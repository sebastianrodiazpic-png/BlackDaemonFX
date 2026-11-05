"""Pruebas unitarias para el búfer circular de velas en memoria (CircularCandleBuffer)."""

import pandas as pd
import pytest
from marketdata.circular_candle_buffer import (
    CircularCandleBuffer,
    BufferedCandleProvider,
)


def _generate_dummy_candles(count: int, symbol: str = "VOLATILITY_75_1S") -> pd.DataFrame:
    """Genera velas sintéticas deterministas para pruebas."""
    times = pd.date_range("2026-10-26 10:00:00", periods=count, freq="5min", tz="UTC")
    data = {
        "time": times,
        "open": [100.0 + i for i in range(count)],
        "high": [105.0 + i for i in range(count)],
        "low": [95.0 + i for i in range(count)],
        "close": [102.0 + i for i in range(count)],
        "tick_volume": [1000 + i for i in range(count)],
    }
    df = pd.DataFrame(data)
    df.attrs["symbol"] = symbol
    return df


def test_circular_candle_buffer_capacity_limit():
    """Verifica que el búfer acote estrictamente las velas a max_candles (e.g. 300)."""
    buffer = CircularCandleBuffer(max_candles=300, ttl_seconds=10.0, enabled=True)
    raw_df = _generate_dummy_candles(500)

    stored = buffer.put("VOLATILITY_75_1S", "M5", raw_df)

    assert len(stored) == 300
    assert stored.iloc[-1]["close"] == raw_df.iloc[-1]["close"]
    assert stored.iloc[0]["time"] == raw_df.iloc[-300]["time"]


def test_circular_candle_buffer_cache_hit_and_miss():
    """Verifica el comportamiento de aciertos (hits) y fallos (misses) de la caché."""
    buffer = CircularCandleBuffer(max_candles=300, ttl_seconds=2.0, enabled=True)
    symbol = "STEP_INDEX"
    timeframe = "M15"

    calls = 0

    def mock_fetch():
        nonlocal calls
        calls += 1
        return _generate_dummy_candles(150, symbol=symbol)

    # Primera llamada: Debe invocar fetch y guardar en búfer (miss)
    df1 = buffer.get_or_fetch(symbol, timeframe, count=50, fetch_callable=mock_fetch)
    assert len(df1) == 50
    assert calls == 1
    assert df1.attrs.get("buffer_hit") is False

    # Segunda llamada inmediata: Debe servirse del búfer en memoria (hit)
    df2 = buffer.get_or_fetch(symbol, timeframe, count=50, fetch_callable=mock_fetch)
    assert len(df2) == 50
    assert calls == 1  # No debe llamar de nuevo
    assert df2.attrs.get("buffer_hit") is True

    diag = buffer.get_diagnostics()
    assert diag["cache_hits"] == 1
    assert diag["cache_misses"] == 1
    assert diag["total_tracked_series"] == 1


def test_buffered_candle_provider_wrapper():
    """Verifica que BufferedCandleProvider delegue transparentemente en el búfer."""
    class FakeProvider:
        def __init__(self):
            self.fetch_count = 0

        def get_candles(self, symbol, timeframe="M5", count=1000):
            self.fetch_count += 1
            return _generate_dummy_candles(min(count, 350), symbol=symbol)

        def get_current_tick(self, symbol):
            return {"symbol": symbol, "bid": 100.0, "ask": 100.1}

    fake_provider = FakeProvider()
    buffered_provider = BufferedCandleProvider(fake_provider)

    candles1 = buffered_provider.get_candles("BOOM_1000_INDEX", "M5", count=100)
    assert len(candles1) == 100
    assert fake_provider.fetch_count == 1

    # Segunda consulta servida por el búfer
    candles2 = buffered_provider.get_candles("BOOM_1000_INDEX", "M5", count=50)
    assert len(candles2) == 50
    assert fake_provider.fetch_count == 1

    # Delegación de otros métodos sin modificar
    tick = buffered_provider.get_current_tick("BOOM_1000_INDEX")
    assert tick["bid"] == 100.0


def test_circular_candle_buffer_timeframe_adaptive_ttl():
    """Verifica que las temporalidades mayores gocen de un TTL adaptativo extendido."""
    buffer = CircularCandleBuffer(max_candles=300, ttl_seconds=2.5, enabled=True)
    assert buffer.get_timeframe_ttl("M5") == 2.5
    assert buffer.get_timeframe_ttl("M1") == 2.5
    assert buffer.get_timeframe_ttl("M15") >= 12.0
    assert buffer.get_timeframe_ttl("H1") >= 45.0
    assert buffer.get_timeframe_ttl("H4") >= 120.0
    assert buffer.get_timeframe_ttl("D1") >= 120.0

