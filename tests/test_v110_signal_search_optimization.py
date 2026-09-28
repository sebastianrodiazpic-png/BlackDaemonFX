from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
import threading
import time

import pandas as pd

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from strategy.execution.multi_timeframe import MultiTimeframeAnalyzer, MultiTimeframeConfig


class ConcurrentProvider:
    def __init__(self):
        self.calls = 0
        self.lock = threading.Lock()

    def get_candles(self, symbol, timeframe, count):
        with self.lock:
            self.calls += 1
        time.sleep(0.03)
        return pd.DataFrame(
            {
                "time": pd.date_range("2026-09-11", periods=count, freq="5min", tz="UTC"),
                "open": [100.0] * count,
                "high": [101.0] * count,
                "low": [99.0] * count,
                "close": [100.5] * count,
            }
        )


class ConcurrentAnalyzer(MultiTimeframeAnalyzer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pipeline_calls = 0
        self.pipeline_lock = threading.Lock()

    def _run_pipeline(self, df, symbol):
        with self.pipeline_lock:
            self.pipeline_calls += 1
        time.sleep(0.03)
        return {
            "data": df,
            "setups": pd.DataFrame(),
            "confirmations": pd.DataFrame(),
            "summary": {},
            "diagnostics": {},
        }


def test_stage_cache_single_flight_avoids_duplicate_fetch_and_pipeline():
    provider = ConcurrentProvider()
    analyzer = ConcurrentAnalyzer(
        provider,
        MultiTimeframeConfig(stage_cache_enabled=True),
    )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(
                lambda _: analyzer._get_stage_result("Volatility 100 Index", "M5", 20),
                range(2),
            )
        )

    assert provider.calls == 1
    assert analyzer.pipeline_calls == 1
    assert sorted(result[2]["cache_hit"] for result in results) == [False, True]
    assert any(result[2].get("single_flight_reuse") for result in results)


class SchedulerProvider:
    def __init__(self):
        self.calls = 0
        now = datetime.now(timezone.utc)
        current_open = now.replace(second=0, microsecond=0) - timedelta(
            minutes=now.minute % 5
        )
        self.times = [
            current_open - timedelta(minutes=5),
            current_open,
            current_open + timedelta(minutes=5),
        ]

    def get_candles(self, symbol, timeframe, count=3):
        self.calls += 1
        return pd.DataFrame(
            {
                "time": self.times,
                "open": [1.0, 1.1, 1.2],
                "high": [2.0, 2.0, 2.0],
                "low": [0.5, 0.5, 0.5],
                "close": [1.1, 1.2, 1.3],
            }
        )


def _scheduler_engine():
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(
        bot_profile="FOREX_1",
        forex_event_scheduler_enabled=True,
        forex_event_timeframe="M5",
        event_scheduler_boundary_guard_enabled=True,
    )
    engine.provider = SchedulerProvider()
    engine._forex_last_closed_bar = {}
    return engine


def test_scheduler_does_not_poll_every_symbol_repeatedly_inside_same_m5_bar():
    engine = _scheduler_engine()
    symbols = ["EURUSD", "GBPUSD", "USDJPY"]

    assert engine._forex_due_symbols(symbols) == symbols
    engine._commit_forex_processed_symbols(
        [{"symbol": symbol, "action": "NO_M15_SETUP"} for symbol in symbols]
    )
    first_calls = engine.provider.calls

    assert engine._forex_due_symbols(symbols) == []
    assert engine.provider.calls == first_calls
    assert engine._forex_scheduler_diagnostics["boundary_poll_skipped"] is True


def test_orb_risk_contract_remains_one_percent_independent_of_smc_risk():
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(risk_percent=2.5, orb_risk_percent=1.0)
    assert engine._risk_percent_for_strategy("ORB_NEW_YORK") == 1.0
    assert engine._risk_percent_for_strategy("SMC") == 2.5
