"""
tests/test_ict_m5_fractal_refinement.py
=======================================
Test suite para el Gatillo de Refinamiento Fractal M5 dentro del FVG M15 de ICT:
1. Interruptor configurable por variable de entorno (DAEMONBLACKFX_ICT_M5_REFINEMENT).
2. Zero Breaking Changes: por defecto desactivado (False).
3. Activación condicional y confirmación temprana en M5 cuando M15 está en consolidación o mecha.
"""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import pandas as pd
import pytest

from strategy.ict.config import ICTSabriMalleConfig
from strategy.ict.ict_strategy import ICTSabriMalleStrategy


class MockProviderWithM5:
    def __init__(self, df_h4=None, df_h1=None, df_m15=None, df_m5=None):
        self._df_h4 = df_h4
        self._df_h1 = df_h1
        self._df_m15 = df_m15
        self._df_m5 = df_m5

    def get_candles(self, symbol, timeframe, count=80):
        if timeframe == "H4":
            return self._df_h4
        elif timeframe == "H1":
            return self._df_h1
        elif timeframe == "M15":
            return self._df_m15
        elif timeframe == "M5":
            return self._df_m5
        return None

    def resolve_symbol(self, symbol):
        return symbol

    def ensure_symbol(self, symbol):
        return True

    def get_current_tick(self, symbol):
        return {"bid": 100.0, "ask": 100.0}


def test_m5_refinement_config_defaults():
    cfg = ICTSabriMalleConfig()
    # Activado oficialmente por autorización del usuario
    assert cfg.m5_fvg_refinement_enabled is True
    assert cfg.m5_refinement_min_wick_ratio == 0.35
    assert cfg.m5_refinement_min_displacement_ratio == 0.45


def test_m5_refinement_env_toggle(monkeypatch):
    monkeypatch.setenv("DAEMONBLACKFX_ICT_M5_REFINEMENT", "0")
    monkeypatch.setenv("DAEMONBLACKFX_ICT_M5_MIN_WICK_RATIO", "0.40")
    cfg = ICTSabriMalleConfig()
    assert cfg.m5_fvg_refinement_enabled is False
    assert cfg.m5_refinement_min_wick_ratio == 0.40


def test_m5_refinement_rescues_signal_when_m15_is_in_absorption():
    now_utc = datetime(2026, 10, 15, 14, 0, tzinfo=timezone.utc)
    dates_h1 = [now_utc - timedelta(hours=i) for i in range(50, 0, -1)]

    # H1 alcista claro
    df_h1 = pd.DataFrame({
        "time": dates_h1,
        "open": [100.0 + i * 0.5 for i in range(50)],
        "high": [102.0 + i * 0.5 for i in range(50)],
        "low": [99.5 + i * 0.5 for i in range(50)],
        "close": [101.5 + i * 0.5 for i in range(50)],
    })

    # M15 con vela última indecisa (cuerpo pequeño 0.20 < 0.45)
    dates_m15 = [now_utc - timedelta(minutes=15 * i) for i in range(30, 0, -1)]
    m15_opens = [120.0] * 29 + [120.0]
    m15_highs = [122.0] * 29 + [122.0]
    m15_lows = [119.0] * 29 + [118.0]
    m15_closes = [121.5] * 29 + [120.2]  # Body = 0.2, Range = 4.0 -> Body ratio = 0.05 (< 0.45)
    df_m15 = pd.DataFrame({
        "time": dates_m15,
        "open": m15_opens,
        "high": m15_highs,
        "low": m15_lows,
        "close": m15_closes,
    })

    # M5 con fuerte mecha de absorción alcista en el soporte (Lower wick = (119.5 - 118.0) / 2.0 = 0.75 >= 0.35)
    dates_m5 = [now_utc - timedelta(minutes=5 * i) for i in range(20, 0, -1)]
    m5_opens = [120.0] * 19 + [119.8]
    m5_highs = [121.0] * 19 + [120.0]
    m5_lows = [119.0] * 19 + [118.0]
    m5_closes = [120.5] * 19 + [119.7]
    df_m5 = pd.DataFrame({
        "time": dates_m5,
        "open": m5_opens,
        "high": m5_highs,
        "low": m5_lows,
        "close": m5_closes,
    })

    dates_h4 = [now_utc - timedelta(hours=4 * i) for i in range(40, 0, -1)]
    df_h4 = pd.DataFrame({
        "time": dates_h4,
        "open": [90.0 + i * 1.0 for i in range(40)],
        "high": [93.0 + i * 1.0 for i in range(40)],
        "low": [89.0 + i * 1.0 for i in range(40)],
        "close": [92.5 + i * 1.0 for i in range(40)],
    })

    provider = MockProviderWithM5(df_h4=df_h4, df_h1=df_h1, df_m15=df_m15, df_m5=df_m5)

    # 1. Con refinamiento M5 desactivado: falla por M15 con cuerpo insuficiente
    cfg_off = ICTSabriMalleConfig()
    cfg_off.m5_fvg_refinement_enabled = False
    strat_off = ICTSabriMalleStrategy(data_provider=provider, config=cfg_off)
    res_off = strat_off.analyze_symbol("Jump 10 Index", now_utc=now_utc)
    assert res_off["valid"] is False
    assert "INSUFFICIENT_DISPLACEMENT_BODY" in res_off["reason"]

    # 2. Con refinamiento M5 activado: M5 valida la absorción fractal
    cfg_on = ICTSabriMalleConfig()
    cfg_on.m5_fvg_refinement_enabled = True
    strat_on = ICTSabriMalleStrategy(data_provider=provider, config=cfg_on)
    res_on = strat_on.analyze_symbol("Jump 10 Index", now_utc=now_utc)
    # Ya no falla por INSUFFICIENT_DISPLACEMENT_BODY
    assert "INSUFFICIENT_DISPLACEMENT_BODY" not in res_on.get("reason", "")
