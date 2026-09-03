from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


class Repo:
    def __init__(self):
        self.updates = []

    def update_trade(self, trade_id, values):
        self.updates.append((trade_id, values))


def engine_with_view(view):
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(
        analysis_invalidation_min_open_minutes=10,
        analysis_invalidation_confirmations=2,
    )
    engine.repository = Repo()
    engine._current_strategy_view_cache = {"Volatility 50 Index": view}
    engine._persist_audit_event = lambda *args, **kwargs: None
    return engine


def old_trade(metadata=None):
    return {
        "id": 4,
        "instrument": "Volatility 50 Index",
        "direction": "BUY",
        "broker_position_ticket": "4714",
        "entry_time": (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat(),
        "details": {"metadata": metadata or {}},
    }


def invalid_view(evaluated_at="2026-09-02T08:00:00+00:00"):
    return {
        "evaluated_at": evaluated_at,
        "valid": False,
        "state": "STALE_M5_SIGNAL",
        "reason": "M5_CONFIRMATION_TOO_OLD_FOR_LIVE_ENTRY",
        "direction": "BUY",
        "diagnostics": {
            "signal_age": {
                "signal_time": "2026-09-02T07:45:00+00:00",
                "latest_closed_candle_time": "2026-09-02T08:00:00+00:00",
            }
        },
    }


def test_same_evaluation_does_not_inflate_confirmation_streak():
    engine = engine_with_view(invalid_view())
    trade = old_trade()
    metadata = trade["details"]["metadata"]
    close = lambda **kwargs: {"closed": True}
    first = engine._analysis_invalidation_exit(
        trade=trade, metadata=metadata, current_rr=-0.50, close_position=close,
    )
    second = engine._analysis_invalidation_exit(
        trade=trade, metadata=metadata, current_rr=-0.50, close_position=close,
    )
    assert first["closed"] is False
    assert second["closed"] is False
    assert metadata.get("analysis_exit_invalid_streak", 0) == 0


def test_stale_signal_does_not_close_even_on_distinct_evaluations():
    engine = engine_with_view(invalid_view("2026-09-02T08:00:00+00:00"))
    trade = old_trade()
    metadata = trade["details"]["metadata"]
    calls = []
    close = lambda **kwargs: calls.append(kwargs) or {"closed": True}
    engine._analysis_invalidation_exit(
        trade=trade, metadata=metadata, current_rr=-0.36, close_position=close,
    )
    engine._current_strategy_view_cache[trade["instrument"]] = invalid_view(
        "2026-09-02T08:00:10+00:00"
    )
    result = engine._analysis_invalidation_exit(
        trade=trade, metadata=metadata, current_rr=-0.36, close_position=close,
    )
    assert result["closed"] is False
    assert not calls


def test_structural_invalidations_count_once_per_closed_m5_candle():
    view = invalid_view()
    view["state"] = "INVALID_DIRECTION"
    view["reason"] = "OPPOSITE_STRUCTURE"
    view["direction"] = "SELL"
    engine = engine_with_view(view)
    trade = old_trade()
    metadata = trade["details"]["metadata"]
    close = lambda **kwargs: {"closed": True}

    engine._analysis_invalidation_exit(
        trade=trade, metadata=metadata, current_rr=-0.20, close_position=close,
    )
    view["evaluated_at"] = "2026-09-02T08:00:10+00:00"
    result = engine._analysis_invalidation_exit(
        trade=trade, metadata=metadata, current_rr=-0.20, close_position=close,
    )

    assert result["closed"] is False
    assert metadata["analysis_exit_invalid_streak"] == 1


def test_recovery_protection_closes_after_positive_mfe_is_lost():
    metadata = {
        "max_favorable_excursion_rr": 0.23,
        "analysis_exit_invalid_streak": 1,
        "analysis_exit_last_evaluated_at": "2026-09-02T08:00:00+00:00",
    }
    view = invalid_view("2026-09-02T08:00:10+00:00")
    view["state"] = "INVALID_DIRECTION"
    view["reason"] = "OPPOSITE_STRUCTURE"
    view["direction"] = "SELL"
    engine = engine_with_view(view)
    trade = old_trade(metadata)
    result = engine._analysis_invalidation_exit(
        trade=trade,
        metadata=metadata,
        current_rr=-0.11,
        close_position=lambda **kwargs: {"closed": True},
    )
    assert result["closed"] is True
    assert result["reason"] == "analysis_invalid_recovery_protection"


def test_valid_current_analysis_resets_streak_and_never_closes():
    view = {
        "evaluated_at": "2026-09-02T08:00:10+00:00",
        "valid": True,
        "state": "ENTRY_CONFIRMED",
        "direction": "BUY",
    }
    engine = engine_with_view(view)
    metadata = {"analysis_exit_invalid_streak": 4}
    trade = old_trade(metadata)
    result = engine._analysis_invalidation_exit(
        trade=trade,
        metadata=metadata,
        current_rr=-0.80,
        close_position=lambda **kwargs: {"closed": True},
    )
    assert result["closed"] is False
    assert metadata["analysis_exit_invalid_streak"] == 0
