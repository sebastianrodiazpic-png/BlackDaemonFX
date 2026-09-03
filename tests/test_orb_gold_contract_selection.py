
from types import SimpleNamespace

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


class Repo:
    def open_trades(self, source=None):
        return []


def _engine():
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(
        risk_percent=1.0,
        split_entries_enabled=True,
        split_entry_risk_fraction=0.50,
        min_actual_risk_ratio=0.99,
        max_actual_risk_tolerance=0.01,
        orb_enabled=True,
    )
    engine.repository = Repo()
    engine._orb_gold_cycle_selection = None
    engine._orb_gold_cycle_diagnostics = {}
    engine._orb_session_is_active = lambda symbol=None, now_utc=None: True
    return engine


def test_gold_selector_chooses_lower_execution_quality_score():
    engine = _engine()
    engine._account_and_guard = lambda: {"equity": 10000.0, "balance": 10000.0, "free_margin": 9000.0}
    evaluations = {
        "XAUUSD": {
            "symbol": "XAUUSD", "viable": True,
            "quality": {"score": 2.5, "spread_risk_ratio": 0.010, "margin_free_ratio": 0.020},
        },
        "XAUUSDmicro": {
            "symbol": "XAUUSDmicro", "viable": True,
            "quality": {"score": 0.8, "spread_risk_ratio": 0.004, "margin_free_ratio": 0.005},
        },
    }
    engine._evaluate_orb_gold_contract = lambda symbol, account: evaluations[symbol]

    result = engine._prepare_orb_gold_selection(["XAUUSD", "XAUUSDmicro", "US500"])

    assert result["selected_symbol"] == "XAUUSDmicro"
    assert engine._orb_gold_cycle_selection == "XAUUSDmicro"
    assert result["reason"] == "BEST_RISK_SPREAD_MARGIN_EXECUTION"


def test_gold_selector_uses_xauusd_when_micro_is_not_viable():
    engine = _engine()
    engine._account_and_guard = lambda: {"equity": 10000.0, "balance": 10000.0, "free_margin": 9000.0}
    evaluations = {
        "XAUUSD": {
            "symbol": "XAUUSD", "viable": True,
            "quality": {"score": 1.0, "spread_risk_ratio": 0.01, "margin_free_ratio": 0.02},
        },
        "XAUUSDmicro": {
            "symbol": "XAUUSDmicro", "viable": False, "reason": "RISK_TARGET_UNREACHABLE",
        },
    }
    engine._evaluate_orb_gold_contract = lambda symbol, account: evaluations[symbol]

    result = engine._prepare_orb_gold_selection(["XAUUSDmicro", "XAUUSD"])

    assert result["selected_symbol"] == "XAUUSD"


def test_gold_selector_does_not_duplicate_gold_exposure():
    engine = _engine()
    engine.repository = SimpleNamespace(
        open_trades=lambda source=None: [
            {"id": 9, "instrument": "XAUUSD", "broker_position_ticket": "777"}
        ]
    )

    counterpart = engine._orb_gold_counterpart_open("XAUUSDmicro")

    assert counterpart["instrument"] == "XAUUSD"
    assert counterpart["broker_position_ticket"] == "777"


def test_gold_selector_skips_expensive_comparison_outside_orb_session():
    engine = _engine()
    engine._orb_session_is_active = lambda symbol=None, now_utc=None: False

    def fail_account():
        raise AssertionError("No debe calcular cuenta/sizing fuera de la sesión ORB")

    engine._account_and_guard = fail_account
    result = engine._prepare_orb_gold_selection(["XAUUSD", "XAUUSDmicro"])

    assert result["selected_symbol"] is None
    assert result["reason"] == "OUTSIDE_ORB_NEW_YORK_SESSION"
