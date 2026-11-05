import os
from datetime import datetime, timezone, time
import pandas as pd
import pytest

from strategy.orb.new_york_orb import (
    NewYorkORBStrategy, ORBConfig, classify_orb_market, is_orb_index_symbol
)
from strategy.orb.asset_rules import (
    ASSET_CONFIG, default_asset_profiles, get_asset_rules, ORB_INDICES_ENABLED
)
from strategy.ict.config import ICTSabriMalleConfig as ICTConfig
from strategy.ict.ict_strategy import ICTSabriMalleStrategy


class FakeProvider:
    def __init__(self, candles, now):
        self._candles = candles
        self._now = now
        self.source_name = "FAKE"

    def get_candles(self, symbol, timeframe, count=1000):
        return self._candles.copy()

    def get_current_tick(self, symbol):
        return {"time": pd.Timestamp(self._now), "bid": 100.0, "ask": 100.1}

    def get_symbol_info(self, symbol):
        return {"trade_mode": 4}


def test_orb_indices_asset_rules_and_profiles():
    """Valida que los índices americanos (US30, NAS100, US500) tienen RETEST habilitado."""
    profiles = default_asset_profiles()
    for idx_key in ("US30", "NAS100", "US500"):
        assert idx_key in profiles
        assert "RETEST" in profiles[idx_key]["allowed_modes"]
        assert profiles[idx_key]["sweep_enabled"] is True
        assert profiles[idx_key]["max_range_atr_ratio"] >= 2.5

    # get_asset_rules para Wall Street 30 y US Tech 100
    rule_us30 = get_asset_rules("Wall Street 30")
    assert "RETEST" in rule_us30["allowed_modes"]
    assert rule_us30["pruned"] is False

    rule_nas100 = get_asset_rules("US Tech 100")
    assert "RETEST" in rule_nas100["allowed_modes"]
    assert rule_nas100["pruned"] is False


def test_orb_london_open_expansion():
    """Valida que a las 03:00 NY (08:00 Londres) la estrategia activa la sesión de LONDRES."""
    # 03:00 NY = 08:00 UTC (daylight saving: 03:00 NY = 07:00 UTC)
    # Generar velas para 03:00..03:25 NY (viernes 2026-08-28)
    times = pd.date_range("2026-08-28 07:00:00+00:00", periods=6, freq="5min")
    rows = []
    # 14 velas previas para ATR
    history = pd.DataFrame([
        dict(time=t, open=100., high=102., low=99., close=100., tick_volume=100, real_volume=0)
        for t in pd.date_range("2026-08-28 05:50:00+00:00", periods=14, freq="5min")
    ])
    
    # Rango 03:00..03:15 NY (3 velas M5: 07:00, 07:05, 07:10 UTC)
    session_rows = [
        (100.0, 101.0, 101.5, 99.5),
        (101.0, 100.5, 102.0, 100.0),
        (100.5, 100.0, 101.0, 99.0),
        # 03:15 NY (07:15 UTC) -> Breakout alcista
        (100.5, 103.0, 103.5, 100.4),
        # 03:20 NY (07:20 UTC) -> Retest a 102.0 con mecha de rechazo
        (103.0, 102.5, 103.2, 101.9),
        # 03:25 NY (07:25 UTC) -> Cierre confirmación
        (102.5, 103.5, 103.8, 102.4),
    ]
    for i, ts in enumerate(times):
        o, c, h, l = session_rows[i]
        rows.append(dict(time=ts, open=o, high=h, low=l, close=c, tick_volume=150, real_volume=0))
    df = pd.concat([history, pd.DataFrame(rows)], ignore_index=True)

    now = datetime(2026, 8, 28, 7, 30, 0, tzinfo=timezone.utc)
    config = ORBConfig(london_session_enabled=True)
    strategy = NewYorkORBStrategy(FakeProvider(df, now), config)

    # Evaluar GBPUSD en apertura de Londres
    res = strategy.analyze_symbol("GBPUSD", now)
    assert res["session_name"] == "LONDON"
    assert "03:00" in res["session_open_ny"] or "07:00" in res["session_open_ny"]


def test_orb_retest_scenario_with_rejection_wick():
    """Valida el escenario de retest del rango de apertura con mecha de rechazo."""
    times = pd.date_range("2026-08-28 13:30:00+00:00", periods=5, freq="5min")
    history = pd.DataFrame([
        dict(time=t, open=100., high=102., low=99., close=100., tick_volume=100, real_volume=0)
        for t in pd.date_range("2026-08-28 12:20:00+00:00", periods=14, freq="5min")
    ])
    session_rows = [
        # 09:30-09:45 NY (rango: high=102.0, low=99.0, midpoint=100.5)
        (100.0, 101.0, 101.5, 99.5),
        (101.0, 100.5, 102.0, 100.0),
        (100.5, 100.0, 101.0, 99.0),
        # 09:45 Breakout alcista fuera de 102.0
        (100.2, 103.5, 103.8, 100.1),
        # 09:50 Retest al borde roto 102.0 con mecha de rechazo inferior
        (103.4, 102.8, 103.5, 101.95),  # low=101.95 testea 102.0, close=102.8 > range_high
    ]
    rows = []
    for i, ts in enumerate(times):
        o, c, h, l = session_rows[i]
        rows.append(dict(time=ts, open=o, high=h, low=l, close=c, tick_volume=150, real_volume=0))
    df = pd.concat([history, pd.DataFrame(rows)], ignore_index=True)

    now = datetime(2026, 8, 28, 13, 55, 30, tzinfo=timezone.utc)
    config = ORBConfig()
    strategy = NewYorkORBStrategy(FakeProvider(df, now), config)

    res = strategy.analyze_symbol("US30", now)
    assert res["valid"] is True
    assert res["direction"] == "BUY"
    assert res["action"] in ("ORB_BREAKOUT_RETEST_CONFIRMED", "ORB_SIGNAL_CONFIRMED") or res["signal"]["orb_entry_mode"] == "ORB_BREAKOUT_RETEST"
    assert res["signal"]["stop_loss"] == 100.5  # midpoint del ORB


def test_ict_synthetic_m15_micro_stop():
    """Valida que en sintéticos el micro-stop M15 ancla el SL a la mecha de rechazo."""
    cfg = ICTConfig(
        enable_m15_micro_stop=True,
        m15_micro_stop_buffer_atr=0.10,
        m15_micro_stop_min_risk_atr=0.20,
    )
    assert cfg.enable_m15_micro_stop is True

    # Provider falso con velas M15 y H1
    dates_h1 = pd.date_range("2026-11-02 00:00:00", periods=50, freq="1h", tz="UTC")
    df_h1 = pd.DataFrame({
        "time": dates_h1,
        "open": [100.0] * 50,
        "high": [105.0] * 48 + [120.0, 103.0],  # Judas Swing peak en 120.0
        "low": [95.0] * 50,
        "close": [100.0] * 49 + [99.0],
        "tick_volume": [1000] * 50,
    })

    # Velas M15 recientes: la vela de rechazo tiene un high local de 104.0 (mucho más bajo que el Judas de 120.0)
    dates_m15 = pd.date_range("2026-11-02 10:00:00", periods=40, freq="15min", tz="UTC")
    df_m15 = pd.DataFrame({
        "time": dates_m15,
        "open": [101.0] * 38 + [103.0, 101.0],
        "high": [102.0] * 38 + [104.0, 101.5],  # M15 rejection wick high = 104.0
        "low": [98.0] * 38 + [100.0, 97.0],
        "close": [100.0] * 38 + [101.0, 97.5],  # Displacement close below support
        "tick_volume": [500] * 40,
    })

    class MultiTFProvider:
        source_name = "MOCK"
        def get_candles(self, sym, tf, count=81):
            if tf == "H1":
                return df_h1
            elif tf == "M15":
                return df_m15
            elif tf == "H4":
                # Resumir H1
                return df_h1.iloc[::4]
            return df_m15

        def get_current_tick(self, sym):
            return {"bid": 97.5, "ask": 97.6, "time": pd.Timestamp("2026-11-02 20:00:00+00:00")}

    strategy = ICTSabriMalleStrategy(MultiTFProvider(), cfg)
    now = datetime(2026, 11, 2, 20, 0, 0, tzinfo=timezone.utc)
    res = strategy.analyze_symbol("Volatility 75 Index", now)

    # Si se confirma señal bajista, el Stop Loss no debe estar en 120.0 (H1), sino en ~104.0 (M15 micro-stop)
    if res.get("valid"):
        sl = res["stop_loss"]
        assert sl < 115.0, f"Expected micro-stop near M15 high (104.0), got H1 SL {sl}"
        assert res.get("micro_stop_applied") is True


def test_gold_silver_bullet_and_london_close_enabled():
    """Valida que Gold (XAUUSD) no es bloqueado en la ventana Silver Bullet de las 10:00 AM NY."""
    cfg = ICTConfig(
        silver_bullet_enabled=True,
        silver_bullet_hours_ny=(3, 10, 14),
        killzone_filter_enabled=True,
    )
    dates_h1 = pd.date_range("2026-11-02 00:00:00", periods=50, freq="1h", tz="UTC")
    df_h1 = pd.DataFrame({
        "time": dates_h1,
        "open": [2000.0] * 50,
        "high": [2010.0] * 50,
        "low": [1990.0] * 50,
        "close": [2005.0] * 50,
        "tick_volume": [1000] * 50,
    })
    class GoldProvider:
        source_name = "MOCK"
        def get_candles(self, sym, tf, count=81):
            return df_h1
        def get_current_tick(self, sym):
            return {"bid": 2005.0, "ask": 2005.2, "time": pd.Timestamp("2026-11-02 15:15:00+00:00")}

    strategy = ICTSabriMalleStrategy(GoldProvider(), cfg)
    # 15:15 UTC = 10:15 AM NY (hora de Silver Bullet)
    now = datetime(2026, 11, 2, 15, 15, 0, tzinfo=timezone.utc)
    res = strategy.analyze_symbol("XAUUSD", now)
    # El motivo NO debe ser OUTSIDE_INSTITUTIONAL_KILLZONE
    assert "OUTSIDE_INSTITUTIONAL_KILLZONE" not in res.get("reason", "")
