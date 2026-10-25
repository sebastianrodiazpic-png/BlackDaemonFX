"""Worker MSNR con la estrategia de los vídeos y su pestaña propia en /Instruments (20-oct-2026)."""
import numpy as np
import pandas as pd
from types import SimpleNamespace

from tests.test_msnr_h4h1_confirmation import _h1, _h4, _now


# ----------------------------------------------------------------------------- arquitectura
def test_msnr_worker_profile_and_architecture():
    import app.main as m
    spec = m.BOT_PROFILES["MSNR"]
    assert spec["mode"] == "msnr-daemon" and spec["magic"] == 26082033 and spec["categories"] == []
    from config.ict_instrument_policy import MSNR_DEMO_TEST_SYMBOLS
    # Mismos instrumentos que Malaysian SNR salvo los sintéticos en prueba demo solo para Malaysian SNR (DEX 1500 UP).
    assert spec["symbols"] == [s for s in m.BOT_PROFILES["MALAYSIAN_SNR"]["symbols"] if s not in MSNR_DEMO_TEST_SYMBOLS]
    assert spec["pruned_symbols"] == m.BOT_PROFILES["MALAYSIAN_SNR"]["pruned_symbols"]
    assert "MSNR" in m.FULL_MULTI_BOT_PROFILES and m._assert_full_multibot_architecture(m.FULL_MULTI_BOT_PROFILES)
    assert m._selection_profile_for_bot("MSNR") == "MSNR" and m._selection_profile_for_bot("MALAYSIAN_SNR") == "MALAYSIAN_SNR"
    src = open(m.__file__, encoding="utf-8").read()
    assert '"msnr-daemon": "MSNR"' in src and '"msnr-daemon",' in src
    magics = [int(v["magic"]) for v in m.BOT_PROFILES.values() if "magic" in v]
    assert magics.count(26082033) == 1


def test_engine_selection_profile_is_msnr_only():
    from strategy.execution.live_trading_engine import LiveTradingEngine
    assert LiveTradingEngine._selection_profile_for_bot("MSNR") == "MSNR"


def test_policy_same_instruments_as_malaysian_snr():
    from config.ict_instrument_policy import ict_active_symbols, preventive_prune_reason, sanitize_ict_selection
    from config.ict_instrument_policy import MSNR_ACTIVE
    assert ict_active_symbols("MSNR") == MSNR_ACTIVE
    assert set(ict_active_symbols("MALAYSIAN_SNR")) - set(MSNR_ACTIVE) <= {"DEX 1500 UP Index"}
    assert sanitize_ict_selection("MSNR", ["AUDNZD", "Boom 1000 Index", "Jump 25 Index"]) == ["Jump 25 Index"]
    assert "solo opera sintéticos" in preventive_prune_reason("EURUSD", "MSNR")


# ----------------------------------------------------------------------------- /Instruments
def test_dashboard_has_independent_msnr_tab():
    from dashboard import realtime_dashboard as rd
    assert "MSNR" in rd._SELECTION_PROFILES and rd._selection_profile_for_category("msnr_jump") == "MSNR"
    assert rd._selection_profile_for_category("malaysian_snr_jump") == "MALAYSIAN_SNR"
    assert set(rd.DEFAULT_PRIORITIZED_SYMBOLS["MSNR"]) <= set(rd.DEFAULT_PRIORITIZED_SYMBOLS["MALAYSIAN_SNR"])
    assert rd._WORKER_PROFILE_META["MSNR"]["selection_profile"] == "MSNR"
    assert rd._WORKER_PROFILE_META["MSNR"]["magic"] == 26082033
    html = rd._INSTRUMENTS_HTML
    assert 'data-profile="MSNR"' in html and "MSNR Vídeos Activo" in html


def test_msnr_tab_selection_only_controls_msnr_and_not_msnr_asset_modes():
    from dashboard.realtime_dashboard import RealtimeDashboardService
    calls = {"modes": 0, "saved": {}}

    class Repo:
        def save_instrument_selection_profile(self, symbols, selection_profile, source):
            calls["saved"][selection_profile] = list(symbols)
            return {"version": 1}

        def latest_instrument_selection_profile(self, profile, source="DEMO"):
            return {"selected_symbols": calls["saved"].get(profile)}

        def save_msnr_runtime_settings(self, **kw):
            calls["modes"] += 1

    svc = RealtimeDashboardService(repository=Repo())
    svc._persist_state_locked = lambda: None
    svc._state["instrument_catalog"] = [{"category": "msnr_jump", "symbols": ["Jump 25 Index", "Jump 50 Index"]},
                                        {"category": "msnr_pruned", "symbols": ["AUDNZD"]}]
    out = svc.update_selected_symbols(["Jump 25 Index", "AUDNZD"], selection_profile="MSNR")
    assert out["ok"] and calls["saved"] == {"MSNR": ["Jump 25 Index"]}
    assert calls["modes"] == 0  # los modos por activo de Malaysian SNR no se tocan


def test_repository_accepts_msnr_profile(tmp_path):
    from database.repository import TradingRepository
    repo = TradingRepository(tmp_path / "s.sqlite")
    repo.save_instrument_selection_profile(["Jump 25 Index"], selection_profile="MSNR", source="DEMO")
    assert repo.latest_instrument_selection_profile("MSNR", source="DEMO")["selected_symbols"] == ["Jump 25 Index"]
    assert "MSNR" in repo.latest_instrument_selection_profiles(source="DEMO")


# ----------------------------------------------------------------------------- estrategia
class _Provider:
    def __init__(self):
        self.frames = {"H4": _h4(), "H1": _h1()}

    def get_candles(self, symbol, timeframe, count=100):
        return self.frames[timeframe].tail(count).copy()  # sin D1: storyline no disponible

    def get_current_tick(self, symbol):
        return {"bid": 100.5, "ask": 100.55}


def _video(mode="observe"):
    from strategy.malaysian_snr.video_strategy import MSNRVideoConfig, MSNRVideoStrategy
    return MSNRVideoStrategy(_Provider(), MSNRVideoConfig(storyline_mode=mode))


def test_video_strategy_emits_its_own_versioned_signal():
    res = _video().analyze_symbol("Volatility 10 Index", _now(_h1()).to_pydatetime())
    sig = res["signal"]
    assert res["valid"] and res["strategy_name"] == "MSNR_VIDEO" and res["strategy_version"] == "msnr-video-v1"
    assert sig["strategy_name"] == "MSNR_VIDEO" and sig["strategy_version"] == "msnr-video-v1"
    assert sig["scenario"] == "ESC_5_H4H1_CONFIRMATION" and sig["direction"] == "SELL"
    assert sig["storyline"] == "UNAVAILABLE" and sig["storyline_alignment"] == "SIN_STORYLINE"


def test_video_strategy_filter_mode_and_scope():
    res = _video("filter").analyze_symbol("Volatility 10 Index", _now(_h1()).to_pydatetime())
    assert not res["valid"] and res["reason"] == "STORYLINE_SIN_STORYLINE"
    assert _video().analyze_symbol("EURUSD", _now(_h1()).to_pydatetime())["reason"] == "MSNR_VIDEO_SYNTHETICS_ONLY"


def test_live_storyline_matches_replay_tool():
    from strategy.malaysian_snr.storyline import storyline_at as live_at, storyline_events as live_events
    from tools import research_msnr_storyline_h4h1 as tool
    rng = np.random.default_rng(7)

    def frame(n, start, step, scale):
        c = 100 + np.cumsum(rng.normal(0, scale, n))
        o = np.r_[c[0], c[:-1]]
        hi = np.maximum(o, c) + rng.uniform(0, scale, n)
        lo = np.minimum(o, c) - rng.uniform(0, scale, n)
        t = pd.date_range(start, periods=n, freq=step, tz="UTC")
        return pd.DataFrame({"time": t, "open": o, "high": hi, "low": lo, "close": c})

    d1 = frame(160, "2026-01-01", "1D", 1.0)
    h4 = frame(160 * 6, "2026-01-01", "4h", 0.4)
    d1t, h4t = d1.assign(close_time=d1.time + pd.Timedelta(days=1)), h4.assign(close_time=h4.time + pd.Timedelta(hours=4))
    ev_tool, ev_live = tool.storyline_events(d1t, h4t), live_events(d1, h4)
    assert len(ev_tool) == len(ev_live) and len(ev_live) > 0
    for t in pd.date_range("2026-02-01", "2026-06-01", freq="37h", tz="UTC"):
        assert tool.storyline_at(ev_tool, h4t, t) == live_at(ev_live, h4, t)


# ----------------------------------------------------------------------------- motor
def _engine(mode="demo_test", source="DEMO", results=None, profile="MSNR"):
    from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
    e = object.__new__(LiveTradingEngine)
    e.config = LiveTradingConfig(bot_profile=profile, source=source, msnr_video_mode=mode)
    e.events = []
    e._persist_audit_event = lambda *a, **k: e.events.append((a[0], k.get("action")))
    e.repository = SimpleNamespace(closed_operations_r=lambda inst, strategy_version, source, since=None: list(results or []))
    return e


def test_msnr_video_modes_gate_and_criterion():
    from strategy.execution.live_trading_engine import LiveTradingConfig
    cfg = LiveTradingConfig()
    assert (cfg.msnr_video_mode, cfg.msnr_video_storyline_mode, cfg.msnr_video_review_trades) == ("demo_test", "observe", 200)
    assert _engine()._msnr_video_active() and not _engine(source="LIVE")._msnr_video_active()
    sig = {"scenario": "ESC_5_H4H1_CONFIRMATION"}
    assert _engine()._msnr_video_gate("Jump 25 Index", dict(sig), "MSNR_VIDEO") is None
    assert _engine(mode="off")._msnr_video_gate("X", dict(sig), "MSNR_VIDEO")["action"] == "MSNR_VIDEO_DISABLED"
    assert _engine(results=[-0.1] * 200)._msnr_video_gate("X", dict(sig), "MSNR_VIDEO")["action"] == "MSNR_VIDEO_DEMO_TEST_FAILED"
    assert _engine(results=[0.05] * 200)._msnr_video_status()["verdict"] == "SUPERA"
    assert _engine(mode="off")._msnr_video_gate("X", dict(sig), "MALAYSIAN_SNR") is None  # solo su estrategia


def test_msnr_worker_regime_observe_and_family_gates_skipped():
    e = _engine()
    assert e._market_regime_observe_only("Volatility 10 Index") is True
    assert _engine(profile="MALAYSIAN_SNR")._market_regime_observe_only("Volatility 10 Index") is False
    from strategy.execution import live_trading_engine as eng
    src = open(eng.__file__, encoding="utf-8").read()
    assert 'family_gates = str(self.config.bot_profile or "").upper() not in {"MSNR", "DRIFT"}' in src
    assert 'elif str(self.config.bot_profile or "").upper() == "MSNR":' in src
