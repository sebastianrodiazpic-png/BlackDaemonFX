"""Filtro de régimen MSNR en prueba demo (20-oct-2026).

Replay fiel 2 años, 37 sintéticos, tope spread/SL 2 %: sin SNR_FAKEOUT_TRAP_SWEEP y sin ADX en (25, 40]
pasa de -0,003 a +0,029 R/trade. Se prueba en DEMO con criterio fijado: 60 operaciones, R/op > 0 y acierto >= 50 %.
"""
import os
import subprocess
import sys
from datetime import datetime, timezone
from types import SimpleNamespace

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


def _engine(mode="demo_test", source="DEMO", results=None, **cfg):
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile="MALAYSIAN_SNR", source=source, msnr_regime_filter_mode=mode, **cfg)
    engine.events = []
    engine._persist_audit_event = lambda *a, **k: engine.events.append((a, k))
    calls = []

    def reader(instrument, *, strategy_version, source, since=None):
        calls.append((instrument, strategy_version, source, since))
        return list(results or [])

    engine.repository = SimpleNamespace(closed_operations_r=reader)
    engine.malaysian_snr_strategy = SimpleNamespace(config=SimpleNamespace(strategy_version="msnr-v3.1-synthetics"))
    engine._reader_calls = calls
    return engine


def test_defaults_are_demo_test_with_fixed_criterion():
    cfg = LiveTradingConfig()
    assert cfg.msnr_regime_filter_mode == "demo_test"
    assert (cfg.msnr_regime_adx_block_min, cfg.msnr_regime_adx_block_max) == (25.0, 40.0)
    assert (cfg.msnr_regime_review_trades, cfg.msnr_regime_min_r, cfg.msnr_regime_min_win_rate) == (60, 0.0, 0.50)
    assert cfg.msnr_regime_block_fakeout is True


def test_blocks_fakeout_and_adx_band():
    e = _engine()
    out = e._msnr_regime_filter_gate("Jump 75 Index", {"entry_confirmation": "SNR_FAKEOUT_TRAP_SWEEP", "adx": 15}, "MALAYSIAN_SNR")
    assert out["action"] == "MSNR_REGIME_FAKEOUT_BLOCKED"
    for adx in (25.01, 30, 40):
        out = e._msnr_regime_filter_gate("Jump 75 Index", {"entry_confirmation": "M15_ZONE_REJECTION_CLOSE", "adx": adx}, "MALAYSIAN_SNR")
        assert out["action"] == "MSNR_REGIME_ADX_BLOCKED"
    assert any(ev[0][0] == "MSNR_REGIME_FILTER" for ev in e.events)


def test_allows_outside_band_and_annotates_signal():
    e = _engine()
    for adx in (10, 25, 40.5, 60):
        sig = {"entry_confirmation": "CRT_M15_SWEEP_AND_ABSORPTION_CLOSE", "adx": adx}
        assert e._msnr_regime_filter_gate("Jump 75 Index", sig, "MALAYSIAN_SNR") is None
        assert sig["msnr_regime_filter"]["allowed"] is True
    # ADX ausente: no se bloquea por ADX; momentum_adx se usa como respaldo
    assert e._msnr_regime_filter_gate("X", {"entry_confirmation": "M15_ZONE_REJECTION_CLOSE"}, "MALAYSIAN_SNR") is None
    assert e._msnr_regime_filter_gate("X", {"momentum_adx": 33}, "MALAYSIAN_SNR")["action"] == "MSNR_REGIME_ADX_BLOCKED"


def test_scope_mode_source_and_strategy():
    sig = {"entry_confirmation": "SNR_FAKEOUT_TRAP_SWEEP", "adx": 30}
    assert _engine(mode="off")._msnr_regime_filter_gate("X", dict(sig), "MALAYSIAN_SNR") is None
    assert _engine(source="LIVE")._msnr_regime_filter_gate("X", dict(sig), "MALAYSIAN_SNR") is None  # demo_test solo DEMO
    assert _engine(mode="live", source="LIVE")._msnr_regime_filter_gate("X", dict(sig), "MALAYSIAN_SNR") is not None
    assert _engine()._msnr_regime_filter_gate("X", dict(sig), "ICT") is None


def test_demo_test_verdicts():
    assert _engine(results=[1.0] * 10)._msnr_regime_filter_status()["verdict"] == "EN_PRUEBA"
    ok = _engine(results=[1.0] * 35 + [-1.0] * 25)._msnr_regime_filter_status()
    assert ok["verdict"] == "SUPERA" and ok["operations"] == 60 and abs(ok["win_rate"] - 35 / 60) < 1e-9
    bad_r = _engine(results=[0.5] * 30 + [-1.0] * 30)._msnr_regime_filter_status()
    assert bad_r["verdict"] == "NO_SUPERA"
    bad_wr = _engine(results=[3.0] * 25 + [-1.0] * 35)._msnr_regime_filter_status()  # R > 0 pero acierto < 50 %
    assert bad_wr["verdict"] == "NO_SUPERA"


def test_status_reads_all_msnr_demo_trades_since_start():
    e = _engine(results=[])
    e._msnr_regime_filter_status()
    instrument, version, source, since = e._reader_calls[0]
    assert instrument is None and version == "msnr-v3.1-synthetics" and source == "DEMO"
    assert since == datetime(2026, 10, 21, tzinfo=timezone.utc)


def test_verdict_change_is_audited_once():
    e = _engine(results=[1.0] * 60)
    e._msnr_regime_status_cache = (0.0, {"verdict": "EN_PRUEBA"})
    e._msnr_regime_filter_status(force=True)
    assert [ev for ev in e.events if ev[0][0] == "MSNR_REGIME_DEMO_TEST"]


def test_repository_all_instruments_and_since(tmp_path):
    from database.models import TradeJournal
    from database.repository import TradingRepository
    repo = TradingRepository(tmp_path / "j.sqlite")
    rows = [("A", "k1:TP1", 10, 10, datetime(2026, 10, 20, tzinfo=timezone.utc)),
            ("B", "k2:TP1", -10, 10, datetime(2026, 10, 22, tzinfo=timezone.utc)),
            ("C", "k3:TP1", 20, 10, datetime(2026, 10, 23, tzinfo=timezone.utc))]
    with repo.Session() as s:
        for i, (sym, key, pnl, risk, t) in enumerate(rows):
            s.add(TradeJournal(journal_key=f"j{i}", source="DEMO", instrument=sym, direction="BUY", status="CLOSED",
                               net_pnl=pnl, risk_amount=risk, execution_key=key, strategy_version="v", entry_time=t))
        s.commit()
    assert sorted(repo.closed_operations_r(None, strategy_version="v", source="DEMO")) == [-1.0, 1.0, 2.0]
    since = datetime(2026, 10, 21, tzinfo=timezone.utc)
    assert sorted(repo.closed_operations_r(None, strategy_version="v", source="DEMO", since=since)) == [-1.0, 2.0]
    assert repo.closed_operations_r("A", strategy_version="v", source="DEMO") == [1.0]


def test_env_switches_mode_off():
    code = ("from strategy.execution.live_trading_engine import LiveTradingConfig as C;"
            "c=C(); print(c.msnr_regime_filter_mode, c.msnr_regime_adx_block_min, c.msnr_regime_review_trades)")
    env = {**os.environ, "DAEMONBLACKFX_MSNR_REGIME_FILTER": "off", "DAEMONBLACKFX_MSNR_REGIME_ADX_MIN": "22",
           "DAEMONBLACKFX_MSNR_REGIME_REVIEW_TRADES": "80"}
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=os.getcwd())
    assert out.stdout.split() == ["off", "22.0", "80"], out.stderr
