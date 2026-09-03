
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


def _engine():
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(
        jump_strict_filter_enabled=True,
        jump_min_confirmation_ratio=0.90,
        jump_min_trade_score=90,
    )
    return engine


def test_jump_rejects_signal_missing_rejection_even_with_high_score():
    signal = {
        "confirmation_percentage": 92.86,
        "trade_score": 100,
        "confirmations": {
            "rejection": False,
            "micro_structure": True,
            "displacement": True,
            "strong_close": True,
        },
    }
    result = _engine()._jump_quality_gate("Jump 50 Index", signal)
    assert result["action"] == "JUMP_STRICT_FILTER_REJECTED"
    assert "JUMP_REJECTION_REQUIRED" in result["failures"]


def test_jump_passes_only_with_reinforced_confirmation():
    signal = {
        "confirmation_percentage": 92.86,
        "trade_score": 95,
        "confirmations": {
            "rejection": True,
            "micro_structure": True,
            "displacement": True,
            "strong_close": True,
        },
    }
    assert _engine()._jump_quality_gate("Jump 25 Index", signal) is None
    assert signal["jump_strict_gate"]["passed"] is True


def test_non_jump_is_not_affected():
    signal = {"confirmation_percentage": 80, "trade_score": 80, "confirmations": {}}
    assert _engine()._jump_quality_gate("Boom 500 Index", signal) is None
