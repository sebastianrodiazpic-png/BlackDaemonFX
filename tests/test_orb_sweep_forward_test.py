"""ORB SWEEP en prueba hacia delante (BTCUSD, USDCAD): activación y criterio de 40 operaciones con R/op > 0."""
from types import SimpleNamespace

import pytest

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from strategy.orb.asset_rules import ASSET_CONFIG, ORB_SWEEP_FORWARD_TEST_SYMBOLS, ORB_SWEEP_STRATEGY_VERSION
from strategy.orb.new_york_orb import classify_orb_market, is_orb_eligible_symbol


def test_forward_test_profiles_and_market():
    assert set(ORB_SWEEP_FORWARD_TEST_SYMBOLS) == {"BTCUSD", "USDCAD"}
    for key in ("BTCUSD", "USDCAD"):
        assert ASSET_CONFIG[key]["sweep_enabled"] is True and ASSET_CONFIG[key]["allowed_modes"] == []
    # USDCAD replica el perfil del replay ampliado (perfil genérico de investigación)
    assert ASSET_CONFIG["USDCAD"]["max_range_atr_ratio"] == 1.5 and ASSET_CONFIG["USDCAD"]["require_volume"] is True
    assert classify_orb_market("USDCAD") == "USDCAD" and is_orb_eligible_symbol("USDCAD")
    assert classify_orb_market("USDCADmicro") is None  # micro no validado


def make_engine(results, **cfg):
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile="ORB", **cfg)
    engine.calls = []

    def reader(symbol, strategy_version, source):
        engine.calls.append((symbol, strategy_version, source))
        return results

    engine.repository = SimpleNamespace(closed_operations_r=reader)
    engine.audits = []
    engine._persist_audit_event = lambda event, **kw: engine.audits.append((event, kw.get("action")))
    return engine


def test_defaults():
    cfg = LiveTradingConfig()
    assert cfg.orb_sweep_forward_test_enabled is True
    assert cfg.orb_sweep_forward_test_min_trades == 40
    assert cfg.orb_sweep_forward_test_min_r == 0.0


@pytest.mark.parametrize("results,blocked", [
    ([-1.0] * 39, False),                 # aún sin muestra suficiente: sigue operando
    ([1.0] * 20 + [-1.0] * 20, True),     # 40 ops con R/op = 0 -> no supera R > 0
    ([-0.2] * 50, True),
    ([0.5] * 20 + [-0.4] * 20, False),    # R/op +0.05 -> se mantiene
])
def test_forward_test_criterion(results, blocked):
    engine = make_engine(results)
    res = engine._orb_sweep_forward_test_gate("USDCAD", "ORB_NEW_YORK")
    assert (res is not None) is blocked
    assert engine.calls == [("USDCAD", ORB_SWEEP_STRATEGY_VERSION, "DEMO")]
    if blocked:
        assert res["action"] == "ORB_SWEEP_FORWARD_TEST_FAILED"
        assert engine.audits[-1] == ("ORB_SWEEP_FORWARD_TEST", "BLOCKED")


@pytest.mark.parametrize("symbol,strategy,cfg", [
    ("XAUUSD", "ORB_NEW_YORK", {}),                      # validado: no está en prueba
    ("BTCUSD", "ICT_SABRI_MALLE", {}),                   # solo aplica a ORB
    ("BTCUSD", "ORB_NEW_YORK", {"orb_sweep_forward_test_enabled": False}),
])
def test_forward_test_scope(symbol, strategy, cfg):
    engine = make_engine([-1.0] * 60, **cfg)
    assert engine._orb_sweep_forward_test_gate(symbol, strategy) is None
    assert engine.calls == []


def test_configurable_thresholds():
    engine = make_engine([0.1] * 30, orb_sweep_forward_test_min_trades=30, orb_sweep_forward_test_min_r=0.2)
    assert engine._orb_sweep_forward_test_gate("BTCUSD", "ORB_NEW_YORK")["action"] == "ORB_SWEEP_FORWARD_TEST_FAILED"


def test_execution_gate_applies_forward_test():
    engine = make_engine([-0.5] * 40)
    engine.executor = SimpleNamespace(get_current_tick=lambda _s: {"bid": 1.0, "ask": 1.0001})
    res = engine._forex_execution_gate("BTCUSD", "BUY", 0.9, strategy_name="ORB_NEW_YORK")
    assert res is not None and res["action"] == "ORB_SWEEP_FORWARD_TEST_FAILED"


def test_repository_groups_legs_into_operations(tmp_path):
    from database.models import TradeJournal
    from database.repository import TradingRepository
    repo = TradingRepository(tmp_path / "fwd.sqlite")
    rows = [
        ("DEMO:USDCAD:M5:2026-10-20T14:00:00+00:00:BUY:TP1", 50.0, 50.0),
        ("DEMO:USDCAD:M5:2026-10-20T14:00:00+00:00:BUY:RUNNER", 100.0, 50.0),   # op1: +1.5 R
        ("DEMO:USDCAD:M5:2026-10-21T14:00:00+00:00:SELL:TP1", -50.0, 50.0),
        ("DEMO:USDCAD:M5:2026-10-21T14:00:00+00:00:SELL:RUNNER", -50.0, 50.0),  # op2: -1 R
    ]
    with repo.Session() as session:
        for i, (key, pnl, risk) in enumerate(rows):
            session.add(TradeJournal(journal_key=f"k{i}", source="DEMO", instrument="USDCAD", direction="BUY",
                                     status="CLOSED", net_pnl=pnl, risk_amount=risk, execution_key=key,
                                     strategy_version=ORB_SWEEP_STRATEGY_VERSION))
        session.add(TradeJournal(journal_key="other", source="DEMO", instrument="USDCAD", direction="BUY", status="CLOSED",
                                 net_pnl=999.0, risk_amount=1.0, execution_key="x:TP1", strategy_version="orb-ny-v4-asset-rules"))
        session.commit()
    assert sorted(repo.closed_operations_r("USDCAD", strategy_version=ORB_SWEEP_STRATEGY_VERSION)) == [-1.0, 1.5]
