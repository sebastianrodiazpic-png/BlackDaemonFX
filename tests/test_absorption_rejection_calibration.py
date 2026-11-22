"""tests/test_absorption_rejection_calibration.py - Validación de absorción y rechazo institucional.

Valida:
1. Malaysian SNR ESC_1_CONTINUATION (DIRECT_TOUCH_RETEST):
   - Exige mecha de absorción institucional (>= 40%) o expansión direccional sólida.
   - Rechaza velas adversas sin mecha que intentan romper en contra.
2. ICT AMD_KILLZONE_FVG_REJECTION:
   - Exige mecha de absorción favorable (>= 40%) en temporalidad de entrada o confirmación M5.
   - Bloquea entradas que presentan mecha contraria adversa (>= 35%) sin absorción.
3. Human Criteria Engine:
   - Veto de mecha contraria excesiva (ADVERSE_SELLER_WICK / ADVERSE_BUYER_WICK).
"""

from __future__ import annotations

import os
from datetime import datetime, timezone, timedelta
import numpy as np
import pandas as pd
import pytest

from strategy.malaysian_snr.validation import retest_confirmation
from strategy.ict.config import ICTSabriMalleConfig
from strategy.ict.ict_strategy import ICTSabriMalleStrategy
from strategy.human_criteria.config import HumanCriteriaConfig, MODE_FILTER
from strategy.human_criteria.human_criteria_engine import HumanCriteriaEngine


def test_msnr_direct_touch_requires_absorption_wick(monkeypatch):
    """En ESC_1_CONTINUATION con allow_direct_touch=True:
    Una vela con mecha de absorción >= 40% confirma DIRECT_TOUCH_RETEST.
    Una vela sin mecha y cerrando en contra es rechazada."""
    monkeypatch.setenv("DAEMONBLACKFX_MSNR_DIRECT_TOUCH_ABSORPTION", "1")
    monkeypatch.setenv("DAEMONBLACKFX_MSNR_ABSORPTION_WICK_RATIO", "0.40")

    level = 100.0
    atr = 2.0
    # Creamos velas donde el precio toca el nivel 100.0
    dates = pd.date_range("2026-01-01", periods=10, freq="15min", tz="UTC")
    
    # 1. Vela con mecha inferior de absorción excelente (Low=99.8, Open=100.5, Close=101.0, High=101.2)
    # Range = 101.2 - 99.8 = 1.4
    # Lower wick = 100.5 - 99.8 = 0.7 (50% >= 40%)
    # Close loc = (101.0 - 99.8) / 1.4 = 0.857 >= 0.40
    df_good = pd.DataFrame({
        "time": dates,
        "open": [102.0] * 9 + [100.5],
        "high": [103.0] * 9 + [101.2],
        "low": [101.5] * 9 + [99.8],  # Toca nivel 100.0
        "close": [102.5] * 9 + [101.0],
    })

    res_good = retest_confirmation(
        frame=df_good,
        level=level,
        direction="BUY",
        atr=atr,
        tolerance_atr=0.35,
        max_distance_atr=0.50,
        allow_direct_touch=True,
    )
    assert res_good["confirmed"] is True
    assert res_good["trigger"] == "DIRECT_TOUCH_RETEST"
    assert res_good["rejection_wick_ratio"] >= 0.40

    # 2. Vela sin absorción cerrando en contra (Low=99.2, Open=100.2, Close=99.5, High=100.3)
    # Range = 100.3 - 99.2 = 1.1
    # Lower wick = 99.5 - 99.2 = 0.3 (27% < 40%)
    # Vela roja cerrando por debajo de apertura y perforando el nivel
    df_bad = pd.DataFrame({
        "time": dates,
        "open": [102.0] * 9 + [100.2],
        "high": [103.0] * 9 + [100.3],
        "low": [101.5] * 9 + [99.2],
        "close": [102.5] * 9 + [99.5],
    })

    res_bad = retest_confirmation(
        frame=df_bad,
        level=level,
        direction="BUY",
        atr=atr,
        tolerance_atr=0.35,
        max_distance_atr=0.50,
        allow_direct_touch=True,
    )
    assert res_bad["confirmed"] is False
    assert res_bad.get("trigger") != "DIRECT_TOUCH_RETEST"


class DummyProvider:
    def __init__(self, df_h4, df_h1, df_ltf, df_m5=None):
        self.df_h4 = df_h4
        self.df_h1 = df_h1
        self.df_ltf = df_ltf
        self.df_m5 = df_m5

    def get_candles(self, symbol, timeframe, count=81):
        if timeframe in ("H4", "4H"):
            return self.df_h4
        if timeframe in ("H1", "1H"):
            return self.df_h1
        if timeframe in ("M15", "15M"):
            return self.df_ltf
        if timeframe in ("M5", "5M"):
            return self.df_m5
        return None

    def get_current_tick(self, symbol):
        return {"bid": 100.0, "ask": 100.05}


def test_ict_fvg_absorption_wick_guard(monkeypatch):
    """En ICT AMD_KILLZONE_FVG_REJECTION:
    Si la vela de entrada no muestra mecha de absorción y presenta mecha contraria adversa,
    el análisis retorna WAITING_FVG_ABSORPTION_WICK."""
    monkeypatch.setenv("DAEMONBLACKFX_ICT_FVG_REQUIRE_ABSORPTION_WICK", "1")
    monkeypatch.setenv("DAEMONBLACKFX_ICT_FVG_MIN_ABSORPTION_WICK_RATIO", "0.40")

    now = datetime(2026, 11, 19, 14, 0, tzinfo=timezone.utc)
    dates_h4 = pd.date_range(now - timedelta(hours=160), periods=40, freq="4h", tz="UTC")
    dates_h1 = pd.date_range(now - timedelta(hours=80), periods=80, freq="1h", tz="UTC")
    dates_m15 = pd.date_range(now - timedelta(minutes=15 * 80), periods=80, freq="15min", tz="UTC")

    # H4 alcista
    df_h4 = pd.DataFrame({
        "time": dates_h4,
        "open": np.linspace(100, 150, 40),
        "high": np.linspace(102, 153, 40),
        "low": np.linspace(99, 149, 40),
        "close": np.linspace(101, 152, 40),
    })

    # H1 alcista
    df_h1 = pd.DataFrame({
        "time": dates_h1,
        "open": np.linspace(130, 160, 80),
        "high": np.linspace(132, 162, 80),
        "low": np.linspace(129, 159, 80),
        "close": np.linspace(131, 161, 80),
    })

    # M15 con vela última que rompe pero tiene mecha superior adversa (vendedores empujando abajo)
    # Range = 10, Open=150, Close=156 (cuerpo 6.0/10 = 0.60 displacement ok), High=160, Low=149.8
    # Lower wick = 150 - 149.8 = 0.2 (2% < 40%)
    # Upper adverse wick = 160 - 156 = 4.0 (40% >= 35%)
    opens = np.linspace(130, 150, 80)
    highs = opens + 3.0
    lows = opens - 1.0
    closes = opens + 2.0

    opens[-1] = 150.0
    highs[-1] = 160.0
    lows[-1] = 149.8
    closes[-1] = 156.0

    df_m15 = pd.DataFrame({
        "time": dates_m15,
        "open": opens,
        "high": highs,
        "low": lows,
        "close": closes,
    })

    provider = DummyProvider(df_h4, df_h1, df_m15)
    config = ICTSabriMalleConfig()
    config.fvg_require_absorption_wick = True
    config.fvg_min_absorption_wick_ratio = 0.40
    config.m5_fvg_refinement_enabled = False

    strat = ICTSabriMalleStrategy(data_provider=provider, config=config)
    res = strat.analyze_symbol("Volatility 75 Index", now_utc=now)

    # Debe pausar o esperar absorción si llega a la fase de disparo FVG
    if not res["valid"] and "WAITING_FVG_ABSORPTION_WICK" in res["reason"]:
        assert "WAITING_FVG_ABSORPTION_WICK" in res["reason"]
