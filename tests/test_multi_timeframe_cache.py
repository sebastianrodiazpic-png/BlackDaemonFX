import pandas as pd

from strategy.execution.multi_timeframe import MultiTimeframeAnalyzer, MultiTimeframeConfig


class CountingProvider:
    def __init__(self):
        self.calls = 0

    def get_candles(self, symbol, timeframe, count):
        self.calls += 1
        times = pd.date_range("2026-08-26 00:00:00+00:00", periods=count, freq="5min")
        return pd.DataFrame({
            "time": times,
            "open": [100.0] * count,
            "high": [101.0] * count,
            "low": [99.0] * count,
            "close": [100.5] * count,
        })


class CountingAnalyzer(MultiTimeframeAnalyzer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pipeline_calls = 0

    def _run_pipeline(self, df, symbol):
        self.pipeline_calls += 1
        return {
            "data": df.copy(),
            "setups": pd.DataFrame(),
            "confirmations": pd.DataFrame(),
            "summary": {},
            "diagnostics": {},
        }


def test_stage_cache_reuses_data_and_pipeline_before_next_candle():
    provider = CountingProvider()
    analyzer = CountingAnalyzer(
        provider,
        MultiTimeframeConfig(stage_cache_enabled=True),
    )

    _, _, first = analyzer._get_stage_result("Boom 100 Index", "M5", 10)
    _, _, second = analyzer._get_stage_result("Boom 100 Index", "M5", 10)

    assert provider.calls == 1
    assert analyzer.pipeline_calls == 1
    assert first["cache_hit"] is False
    assert second["cache_hit"] is True


def test_clear_stage_cache_forces_new_fetch_and_pipeline():
    provider = CountingProvider()
    analyzer = CountingAnalyzer(provider, MultiTimeframeConfig(stage_cache_enabled=True))

    analyzer._get_stage_result("Boom 100 Index", "M15", 10)
    analyzer.clear_stage_cache(symbol="Boom 100 Index", timeframe="M15")
    _, _, timing = analyzer._get_stage_result("Boom 100 Index", "M15", 10)

    assert provider.calls == 2
    assert analyzer.pipeline_calls == 2
    assert timing["cache_hit"] is False
