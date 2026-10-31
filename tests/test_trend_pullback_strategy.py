"""Tests unitarios y de integración para la estrategia Trend Pullback H1 + M15."""
from __future__ import annotations

from datetime import datetime, timezone
import numpy as np
import pandas as pd
import pytest

from strategy.trend_pullback.config import TrendPullbackConfig
from strategy.trend_pullback.trend_pullback_strategy import TrendPullbackStrategy, closed_candles_only


class MockDataProvider:
    """Proveedor simulado de velas y ticks para testing sin dependencias externas."""

    def __init__(self, h1_df: pd.DataFrame, m15_df: pd.DataFrame, bid: float = 1000.0, ask: float = 1000.2) -> None:
        self.h1_df = h1_df
        self.m15_df = m15_df
        self.bid = bid
        self.ask = ask

    def get_candles(self, symbol: str, timeframe: str, count: int = 100) -> pd.DataFrame:
        if timeframe.upper() == "H1":
            return self.h1_df.tail(count).copy()
        elif timeframe.upper() == "M15":
            return self.m15_df.tail(count).copy()
        raise ValueError(f"Timeframe no soportado en mock: {timeframe}")

    def get_current_tick(self, symbol: str) -> dict[str, float]:
        return {"bid": self.bid, "ask": self.ask}


def _generate_synthetic_candles(
    n: int,
    freq: str,
    end_time: pd.Timestamp | None = None,
    start_price: float = 1000.0,
    trend_slope: float = 1.0,
    seed: int = 42,
) -> pd.DataFrame:
    """Genera serie sintética determinista OHLCV alineada al final."""
    rng = np.random.default_rng(seed)
    if end_time is not None:
        times = pd.date_range(end=end_time, periods=n, freq=freq, tz="UTC")
    else:
        times = pd.date_range("2026-01-01", periods=n, freq=freq, tz="UTC")
    steps = rng.normal(trend_slope, 0.5, n)
    closes = start_price + np.cumsum(steps)
    opens = np.r_[start_price, closes[:-1]]
    highs = np.maximum(opens, closes) + rng.uniform(0.2, 0.8, n)
    lows = np.minimum(opens, closes) - rng.uniform(0.2, 0.8, n)
    return pd.DataFrame({"time": times, "open": opens, "high": highs, "low": lows, "close": closes})


def test_closed_candles_only_filters_future_and_open_bars():
    """Verifica que closed_candles_only excluye la vela en curso y no tiene lookahead."""
    times = pd.date_range("2026-10-27 10:00:00", periods=4, freq="15min", tz="UTC")
    # Velas en 10:00, 10:15, 10:30, 10:45
    df = pd.DataFrame({
        "time": times,
        "open": [10.0, 11.0, 12.0, 13.0],
        "high": [10.5, 11.5, 12.5, 13.5],
        "low": [9.5, 10.5, 11.5, 12.5],
        "close": [10.2, 11.2, 12.2, 13.2],
    })

    # Si now es 10:35, las velas cerradas de 15m son 10:00 (cierra 10:15) y 10:15 (cierra 10:30).
    # La vela 10:30 cierra a las 10:45 (está en curso).
    now = pd.Timestamp("2026-10-27 10:35:00", tz="UTC")
    closed = closed_candles_only(df, now, "M15")
    assert len(closed) == 2
    assert closed["time"].iloc[-1] == pd.Timestamp("2026-10-27 10:15:00", tz="UTC")


def test_trend_pullback_bullish_signal_generation():
    """Verifica la generación completa de una señal de compra (BUY) con todos los criterios alineados."""
    # 250 velas H1 alcistas con fuerte pendiente para asegurar EMA50 > EMA200 y ADX > 20
    h1 = _generate_synthetic_candles(250, "1h", start_price=1000.0, trend_slope=2.0, seed=1)
    end_t = h1["time"].iloc[-1]
    
    # 100 velas M15 alcistas alineadas al final de H1
    m15 = _generate_synthetic_candles(100, "15min", end_time=end_t, start_price=1500.0, trend_slope=0.2, seed=2)
    
    # Manipulamos las dos últimas velas para forzar un pullback perfecto a EMA21
    # Penúltima vela: retroceso que toca la EMA21
    m15_ema21 = m15["close"].ewm(span=21, adjust=False).mean()
    target_ema = m15_ema21.iloc[-2]
    
    m15.loc[m15.index[-2], "low"] = target_ema - 1.0
    m15.loc[m15.index[-2], "close"] = target_ema + 0.1
    
    # Última vela: rechazo alcista sobre EMA21 con cierre superior a la apertura
    m15.loc[m15.index[-1], "open"] = target_ema + 0.2
    m15.loc[m15.index[-1], "low"] = target_ema - 0.2
    m15.loc[m15.index[-1], "close"] = target_ema + 1.2
    m15.loc[m15.index[-1], "high"] = target_ema + 1.5

    last_m15_time = m15["time"].iloc[-1]
    # now 16 minutos después para que la última vela esté completamente cerrada
    now = last_m15_time + pd.Timedelta(minutes=16)

    ask_price = float(m15["close"].iloc[-1]) + 0.1
    bid_price = ask_price - 0.02
    provider = MockDataProvider(h1, m15, bid=bid_price, ask=ask_price)

    cfg = TrendPullbackConfig(symbols=("Step Index 200",))
    strategy = TrendPullbackStrategy(provider, cfg)

    res = strategy.analyze_symbol("Step Index 200", now.to_pydatetime())
    assert res["valid"] is True, f"Fallo en validación: {res.get('reason')}"
    assert res["action"] == "TREND_PULLBACK_CONFIRMED"
    
    sig = res["signal"]
    assert sig["direction"] == "BUY"
    assert sig["split_execution"] is True
    assert sig["leg1_risk_ratio"] == 0.5
    assert sig["leg2_risk_ratio"] == 0.5
    assert sig["tp1_rr"] == 1.0
    assert sig["runner_rr"] == 2.0
    assert sig["stop_loss"] < sig["entry_price"]
    assert sig["tp1_price"] > sig["entry_price"]
    assert sig["tp2_price"] > sig["tp1_price"]


def test_trend_pullback_bearish_signal_generation():
    """Verifica la generación completa de una señal de venta (SELL) con tendencia bajista en H1."""
    # 250 velas H1 bajistas con fuerte pendiente negativa
    h1 = _generate_synthetic_candles(250, "1h", start_price=2000.0, trend_slope=-2.0, seed=1)
    end_t = h1["time"].iloc[-1]
    
    # 100 velas M15 bajistas alineadas al final de H1
    m15 = _generate_synthetic_candles(100, "15min", end_time=end_t, start_price=1500.0, trend_slope=-0.2, seed=2)
    
    m15_ema21 = m15["close"].ewm(span=21, adjust=False).mean()
    target_ema = m15_ema21.iloc[-2]
    
    # Penúltima vela: rebote alcista suave y ordenado hacia EMA21
    m15.loc[m15.index[-2], "open"] = target_ema - 0.6
    m15.loc[m15.index[-2], "high"] = target_ema + 1.0
    m15.loc[m15.index[-2], "close"] = target_ema - 0.1
    m15.loc[m15.index[-2], "low"] = target_ema - 0.8
    
    # Última vela: rechazo bajista bajo EMA21 con cierre inferior a la apertura
    m15.loc[m15.index[-1], "open"] = target_ema - 0.2
    m15.loc[m15.index[-1], "high"] = target_ema + 0.2
    m15.loc[m15.index[-1], "close"] = target_ema - 1.2
    m15.loc[m15.index[-1], "low"] = target_ema - 1.5

    last_m15_time = m15["time"].iloc[-1]
    now = last_m15_time + pd.Timedelta(minutes=16)

    bid_price = float(m15["close"].iloc[-1]) - 0.1
    ask_price = bid_price + 0.02
    provider = MockDataProvider(h1, m15, bid=bid_price, ask=ask_price)

    cfg = TrendPullbackConfig(symbols=("Step Index 200",))
    strategy = TrendPullbackStrategy(provider, cfg)

    res = strategy.analyze_symbol("Step Index 200", now.to_pydatetime())
    assert res["valid"] is True, f"Fallo en validación: {res.get('reason')}"
    
    sig = res["signal"]
    assert sig["direction"] == "SELL"
    assert sig["stop_loss"] > sig["entry_price"]
    assert sig["tp1_price"] < sig["entry_price"]
    assert sig["tp2_price"] < sig["tp1_price"]


def test_trend_pullback_rejects_when_spread_ratio_exceeded():
    """Verifica que se aborta la señal si el spread supera el tope del 2.0% del SL."""
    h1 = _generate_synthetic_candles(250, "1h", start_price=1000.0, trend_slope=2.0, seed=1)
    end_t = h1["time"].iloc[-1]
    m15 = _generate_synthetic_candles(100, "15min", end_time=end_t, start_price=1500.0, trend_slope=0.2, seed=2)
    
    m15_ema21 = m15["close"].ewm(span=21, adjust=False).mean()
    target_ema = m15_ema21.iloc[-2]
    m15.loc[m15.index[-2], "low"] = target_ema - 1.0
    m15.loc[m15.index[-2], "close"] = target_ema + 0.1
    m15.loc[m15.index[-1], "open"] = target_ema + 0.2
    m15.loc[m15.index[-1], "low"] = target_ema - 0.2
    m15.loc[m15.index[-1], "close"] = target_ema + 1.2
    m15.loc[m15.index[-1], "high"] = target_ema + 1.5

    last_m15_time = m15["time"].iloc[-1]
    now = last_m15_time + pd.Timedelta(minutes=16)

    # Spread intencionadamente gigante (ej. 20.0 pts cuando SL ~ 5 pts => spread/SL > 200%)
    ask_price = float(m15["close"].iloc[-1]) + 20.0
    bid_price = float(m15["close"].iloc[-1])
    provider = MockDataProvider(h1, m15, bid=bid_price, ask=ask_price)

    cfg = TrendPullbackConfig(symbols=("Step Index 200",), max_spread_sl_ratio=0.02)
    strategy = TrendPullbackStrategy(provider, cfg)

    res = strategy.analyze_symbol("Step Index 200", now.to_pydatetime())
    assert res["valid"] is False
    assert "SPREAD_SL_RATIO_EXCEEDED" in res["reason"]


def test_trend_pullback_rejects_when_disabled_or_disallowed_symbol():
    """Verifica interruptor maestro y lista blanca de instrumentos."""
    h1 = _generate_synthetic_candles(250, "1h")
    m15 = _generate_synthetic_candles(100, "15min")
    provider = MockDataProvider(h1, m15)

    # Desactivada
    strategy_off = TrendPullbackStrategy(provider, TrendPullbackConfig(enabled=False))
    res_off = strategy_off.analyze_symbol("Step Index 200")
    assert res_off["valid"] is False
    assert res_off["reason"] == "STRATEGY_DISABLED"

    # Símbolo no permitido
    strategy_sym = TrendPullbackStrategy(provider, TrendPullbackConfig(symbols=("Step Index 200",)))
    res_sym = strategy_sym.analyze_symbol("EURUSD")
    assert res_sym["valid"] is False
    assert res_sym["reason"] == "SYMBOL_NOT_IN_PULLBACK_UNIVERSE"


def test_trend_pullback_rejects_when_h1_adx_is_low():
    """Verifica el filtro de régimen direccional: aborta si ADX en H1 < 20."""
    h1 = _generate_synthetic_candles(250, "1h", start_price=1000.0, trend_slope=0.1, seed=10)
    end_t = h1["time"].iloc[-1]
    m15 = _generate_synthetic_candles(100, "15min", end_time=end_t, start_price=1000.0, trend_slope=0.1, seed=11)
    provider = MockDataProvider(h1, m15)

    # Exigimos adx_min muy alto (ej. 60.0) para garantizar que la serie sintética no lo alcance
    strategy = TrendPullbackStrategy(provider, TrendPullbackConfig(symbols=("Step Index 200",), adx_min=60.0))
    res = strategy.analyze_symbol("Step Index 200")
    assert res["valid"] is False
    assert "H1_ADX_LOW" in res["reason"]


def test_trend_pullback_rejects_when_no_ema21_touch():
    """Verifica que si el precio está lejos de la EMA21 en M15 (sin retroceso), no dispara orden."""
    h1 = _generate_synthetic_candles(250, "1h", start_price=1000.0, trend_slope=2.0, seed=1)
    end_t = h1["time"].iloc[-1]
    m15 = _generate_synthetic_candles(100, "15min", end_time=end_t, start_price=1500.0, trend_slope=0.2, seed=2)
    
    # Aseguramos que la vela esté muy por encima de la EMA21 (sin tocar)
    m15_ema21 = m15["close"].ewm(span=21, adjust=False).mean()
    m15.loc[m15.index[-2], "low"] = m15_ema21.iloc[-2] + 5.0
    m15.loc[m15.index[-1], "low"] = m15_ema21.iloc[-1] + 5.0
    m15.loc[m15.index[-1], "close"] = m15_ema21.iloc[-1] + 8.0

    last_m15_time = m15["time"].iloc[-1]
    now = last_m15_time + pd.Timedelta(minutes=16)

    provider = MockDataProvider(h1, m15, bid=2000.0, ask=2000.02)
    strategy = TrendPullbackStrategy(provider, TrendPullbackConfig(symbols=("Step Index 200",)))

    res = strategy.analyze_symbol("Step Index 200", now.to_pydatetime())
    assert res["valid"] is False
    assert "M15_NO_PULLBACK_TOUCH_EMA21" in res["reason"]


def test_live_trading_engine_integration_and_contract():
    """Verifica la integración de Trend Pullback en LiveTradingConfig y LiveTradingEngine."""
    from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
    cfg = LiveTradingConfig()
    assert hasattr(cfg, "trend_pullback_mode")
    assert hasattr(cfg, "trend_pullback_split")
    assert cfg.trend_pullback_split is True

    engine = LiveTradingEngine.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(source="DEMO", trend_pullback_mode="demo_test")
    assert engine._trend_pullback_active() is True

    engine_live = LiveTradingEngine.__new__(LiveTradingEngine)
    engine_live.config = LiveTradingConfig(source="LIVE", trend_pullback_mode="demo_test")
    assert engine_live._trend_pullback_active() is False

    engine_off = LiveTradingEngine.__new__(LiveTradingEngine)
    engine_off.config = LiveTradingConfig(source="DEMO", trend_pullback_mode="off")
    assert engine_off._trend_pullback_active() is False


def test_trend_pullback_directional_asymmetry_and_pruned_symbols():
    """Verifica la poda de activos tóxicos y la asimetría direccional en Trend Pullback."""
    from strategy.trend_pullback.config import TREND_PULLBACK_PRUNED_SYMBOLS, _env_symbols

    # Poda garantizada en la lista por defecto
    active_syms = _env_symbols()
    for pruned in TREND_PULLBACK_PRUNED_SYMBOLS:
        assert pruned not in active_syms, f"{pruned} debe estar excluido del universo activo"

    # Simular intento de señal BUY en Step Index 500 (solo SELL permitido)
    h1 = _generate_synthetic_candles(250, "1h", start_price=1000.0, trend_slope=2.0, seed=1)
    end_t = h1["time"].iloc[-1]
    m15 = _generate_synthetic_candles(100, "15min", end_time=end_t, start_price=1200.0, trend_slope=0.2, seed=2)
    m15_ema21 = m15["close"].ewm(span=21, adjust=False).mean()
    target_ema = m15_ema21.iloc[-2]
    m15.loc[m15.index[-2], "open"] = target_ema + 0.6
    m15.loc[m15.index[-2], "low"] = target_ema - 0.2
    m15.loc[m15.index[-2], "close"] = target_ema + 0.1
    m15.loc[m15.index[-1], "open"] = target_ema + 0.1
    m15.loc[m15.index[-1], "close"] = target_ema + 0.8
    m15.loc[m15.index[-1], "high"] = target_ema + 1.2
    m15.loc[m15.index[-1], "low"] = target_ema

    provider = MockDataProvider(h1, m15, bid=2000.0, ask=2000.02)
    cfg = TrendPullbackConfig(symbols=("Step Index 500",))
    strategy = TrendPullbackStrategy(provider, cfg)
    now = m15["time"].iloc[-1] + pd.Timedelta(minutes=16)

    res = strategy.analyze_symbol("Step Index 500", now.to_pydatetime())
    assert res["valid"] is False
    assert "DIRECTION_ASYMMETRY_STEP_SELL_ONLY" in res["reason"]


def test_trend_pullback_anti_impulsive_pullback_rejected():
    """Verifica que un retroceso con vela impulsiva gigante contra la tendencia es rechazado (anti-falling knife)."""
    h1 = _generate_synthetic_candles(250, "1h", start_price=1000.0, trend_slope=2.0, seed=1)
    end_t = h1["time"].iloc[-1]
    m15 = _generate_synthetic_candles(100, "15min", end_time=end_t, start_price=1200.0, trend_slope=0.2, seed=2)
    m15_ema21 = m15["close"].ewm(span=21, adjust=False).mean()
    target_ema = m15_ema21.iloc[-2]

    # Penúltima vela: caída gigante con cuerpo > 2.0 ATR (falling knife)
    m15.loc[m15.index[-2], "open"] = target_ema + 5.0
    m15.loc[m15.index[-2], "close"] = target_ema - 0.2
    m15.loc[m15.index[-2], "high"] = target_ema + 5.2
    m15.loc[m15.index[-2], "low"] = target_ema - 0.5

    # Última vela: intento de rebote pequeño
    m15.loc[m15.index[-1], "open"] = target_ema - 0.1
    m15.loc[m15.index[-1], "close"] = target_ema + 0.5
    m15.loc[m15.index[-1], "high"] = target_ema + 0.8
    m15.loc[m15.index[-1], "low"] = target_ema - 0.2

    provider = MockDataProvider(h1, m15, bid=2000.0, ask=2000.02)
    cfg = TrendPullbackConfig(symbols=("Volatility 25 Index",), max_pullback_bar_body_atr=1.25)
    strategy = TrendPullbackStrategy(provider, cfg)
    now = m15["time"].iloc[-1] + pd.Timedelta(minutes=16)

    res = strategy.analyze_symbol("Volatility 25 Index", now.to_pydatetime())
    assert res["valid"] is False
    assert "M15_IMPULSIVE_PULLBACK_REJECTED" in res["reason"]



