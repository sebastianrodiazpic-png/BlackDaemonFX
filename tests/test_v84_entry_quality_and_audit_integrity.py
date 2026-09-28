from types import SimpleNamespace

from database.repository import TradingRepository
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


def test_orb_unknown_htf_context_is_not_required():
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(
        bot_profile="ORB", orb_require_known_htf_context=True,
        orb_require_h1_alignment=True, orb_use_m15_context=True,
    )
    engine.multi_timeframe = SimpleNamespace(
        analyze_symbol=lambda symbol: {"h1": {}, "m15": {}, "action": "NO_SETUP"}
    )
    result = engine._orb_higher_timeframe_context("XAUUSDmicro", "BUY")
    assert result["blocked"] is False
    assert result["reason"] == "ORB_HTF_NOT_REQUIRED"


def test_orb_non_correlated_markets_do_not_share_a_global_one_percent_cap():
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(
        source="DEMO", bot_profile="ORB", orb_risk_percent=1.0,
    )
    engine.repository = SimpleNamespace(open_trades=lambda source: [{
        "id": 1, "instrument": "XAUUSDmicro", "risk_percent": 1.0,
        "details": {"metadata": {"strategy_name": "ORB_NEW_YORK",
                                   "operation_risk_percent": 1.0,
                                   "parent_execution_key": "ORB-1"}},
    }])
    result = engine._orb_exposure_guard("Wall Street 30", "ORB-2", "ORB_NEW_YORK")
    assert result is None


def test_reused_trade_id_resets_frozen_identity(tmp_path):
    repo = TradingRepository(db_path=tmp_path / "audit.db")
    repo.upsert_trade_visual_audit(
        2, instrument="VolSwitch Medium Vol Index", broker_position_ticket="OLD",
        entry_context={"instrument": "VolSwitch Medium Vol Index"},
    )
    repo.upsert_trade_visual_audit(
        2, instrument="EURUSD", broker_position_ticket="NEW",
        entry_context={"instrument": "EURUSD"},
    )
    row = repo.trade_visual_audits()[0]
    assert row["instrument"] == "EURUSD"
    assert row["broker_position_ticket"] == "NEW"
    assert row["entry_context"]["instrument"] == "EURUSD"
