from types import SimpleNamespace
from unittest.mock import Mock
import pandas as pd
from strategy.execution.live_trading_engine import LiveTradingEngine


def test_observation_refreshes_closed_stages_without_entry_pipeline():
    def stage(symbol, timeframe, count):
        minutes = {"H1": 60, "M15": 15, "M5": 5}[timeframe]
        end = pd.Timestamp.now(tz="UTC").floor(f"{minutes}min") - pd.Timedelta(minutes=minutes)
        data = pd.DataFrame({"time": pd.date_range(end=end, periods=30, freq=f"{minutes}min"),
                             "open": 100., "high": 102., "low": 98., "close": 101.})
        return data, {"data": data}, {}
    engine = object.__new__(LiveTradingEngine)
    engine.multi_timeframe = SimpleNamespace(
        _get_stage_result=Mock(side_effect=stage), config=SimpleNamespace(),
        _get_h1_context=lambda result: {"trend": "NEUTRAL"},
        analyze_symbol=Mock(side_effect=AssertionError("entry forbidden")))
    view = engine._observe_active_strategy("Step Index 200", "SMC")
    assert view["decision"] == "OBSERVACION_ACTUAL"
    assert set(view["timeframes"]) == {"H1", "M15", "M5"}
    assert view["observations"] and view["evaluated_at"]
    assert view["score"] is None and view["audit_only"]
    engine.multi_timeframe.analyze_symbol.assert_not_called()
    engine.multi_timeframe._get_stage_result.side_effect = RuntimeError("feed unavailable")
    failed = engine._observe_active_strategy("Step Index 200", "SMC")
    assert failed["decision"] == "OBSERVACION_NO_DISPONIBLE"
    assert failed["timeframes"] == {}
    assert "feed unavailable" in failed["observations"][0]
