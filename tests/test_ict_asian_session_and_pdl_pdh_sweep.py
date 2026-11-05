"""Tests for ICT Institutional Improvements:
1. Sesión Asiática (Tokyo / Sydney Killzone) para pares Forex con JPY y AUD.
2. Barrido de Asian Range (Asia High / Asia Low) como manipulación institucional válida (Judas Swing).
3. Barrido de Previous Day High / Low (PDH / PDL) como manipulación institucional válida.
"""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
import pytest

from strategy.ict.config import ICTSabriMalleConfig
from strategy.ict.ict_strategy import ICTSabriMalleStrategy

NY_TZ = ZoneInfo("America/New_York")


class MockCandleProvider:
    def __init__(self, df_h4=None, df_h1=None, df_m15=None):
        self._df_h4 = df_h4
        self._df_h1 = df_h1
        self._df_m15 = df_m15

    def get_candles(self, symbol, timeframe, count=80):
        if timeframe == "H4":
            return self._df_h4
        elif timeframe == "H1":
            return self._df_h1
        elif timeframe in ("M15", "M5"):
            return self._df_m15
        return None

    def resolve_symbol(self, symbol):
        return symbol

    def ensure_symbol(self, symbol):
        return True

    def get_current_tick(self, symbol):
        return {"bid": 100.0, "ask": 100.0}


def test_asian_session_activation_for_jpy_and_aud_pairs():
    """Pares JPY y AUD activan la sesión asiática en horas de Asia (19:00 a 02:00 NY),

    mientras que otros pares Forex sin JPY/AUD se bloquean fuera de killzone.
    """
    cfg = ICTSabriMalleConfig()
    strat = ICTSabriMalleStrategy(data_provider=MockCandleProvider(), config=cfg)

    # 21:30 NY (01:30 UTC siguiente día): Horario de sesión asiática (Tokyo / Sydney)
    now_ny = datetime(2026, 10, 15, 21, 30, tzinfo=NY_TZ)
    now_utc = now_ny.astimezone(timezone.utc)

    # Crear df_h1 dummy con pocas velas para ver dónde se detiene el análisis
    dates = [now_utc - timedelta(hours=i) for i in range(20, 0, -1)]
    df_dummy = pd.DataFrame({
        "time": dates,
        "open": [100.0] * len(dates),
        "high": [101.0] * len(dates),
        "low": [99.0] * len(dates),
        "close": [100.0] * len(dates),
    })
    strat.provider = MockCandleProvider(df_h1=df_dummy)

    # Pares JPY y AUD deben pasar el filtro de sesión (no fallan por OUTSIDE_INSTITUTIONAL_KILLZONE)
    for sym in ["USDJPY", "GBPJPY", "EURJPY", "AUDUSD", "AUDJPY", "EURAUD"]:
        res = strat.analyze_symbol(sym, now_utc=now_utc)
        assert "OUTSIDE_INSTITUTIONAL_KILLZONE" not in res.get("reason", ""), f"{sym} should be active in Asian Session"

    # Pares que NO tienen JPY ni AUD deben ser bloqueados a las 21:30 NY
    for sym in ["EURUSD", "USDCAD", "GBPUSD", "USDCHF"]:
        res = strat.analyze_symbol(sym, now_utc=now_utc)
        assert "OUTSIDE_INSTITUTIONAL_KILLZONE" in res.get("reason", ""), f"{sym} should be blocked outside killzone"


def test_asian_session_jpy_aud_disabled_by_env(monkeypatch):
    """Si DAEMONBLACKFX_ICT_ASIAN_SESSION_JPY_AUD=0, los pares JPY/AUD quedan bloqueados en horas asiáticas."""
    monkeypatch.setenv("DAEMONBLACKFX_ICT_ASIAN_SESSION_JPY_AUD", "0")
    cfg = ICTSabriMalleConfig()
    strat = ICTSabriMalleStrategy(data_provider=MockCandleProvider(), config=cfg)

    now_ny = datetime(2026, 10, 15, 21, 30, tzinfo=NY_TZ)
    now_utc = now_ny.astimezone(timezone.utc)

    dates = [now_utc - timedelta(hours=i) for i in range(20, 0, -1)]
    df_dummy = pd.DataFrame({
        "time": dates,
        "open": [100.0] * len(dates),
        "high": [101.0] * len(dates),
        "low": [99.0] * len(dates),
        "close": [100.0] * len(dates),
    })
    strat.provider = MockCandleProvider(df_h1=df_dummy)

    res = strat.analyze_symbol("USDJPY", now_utc=now_utc)
    assert "OUTSIDE_INSTITUTIONAL_KILLZONE" in res.get("reason", "")


def build_market_data_with_asian_range_and_pdh(sweep_type="ASIAN_HIGH"):
    """Construye dataFrames H4, H1 y M15 con:

    - Día anterior con PDH y PDL claros.
    - Rango Asiático (20:00 a 00:00 NY) bien delimitado.
    - Vela en Londres (03:00 NY) que barre Asian High o PDH con mecha de rechazo.
    - M15 con desplazamiento institucional MSS y FVG mitigado.
    """
    # Fecha de evaluación: 2026-10-15 04:30 NY (en London Killzone 03:00-05:00 NY)
    eval_time_ny = datetime(2026, 10, 15, 4, 30, tzinfo=NY_TZ)
    eval_time_utc = eval_time_ny.astimezone(timezone.utc)

    # 1. H4 Data: 320 velas con tendencia bajista (EMA100 arriba del precio para sesgo BEARISH)
    h4_dates = [eval_time_utc - timedelta(hours=4 * i) for i in range(320, 0, -1)]
    df_h4 = pd.DataFrame({
        "time": h4_dates,
        "open": np.linspace(155.0, 150.0, 320),
        "high": np.linspace(156.0, 151.0, 320),
        "low": np.linspace(154.0, 149.0, 320),
        "close": np.linspace(154.5, 149.5, 320),
    })

    # 2. H1 Data: 70 velas con rango de consolidación base high=150.50, low=149.50
    h1_dates = [eval_time_utc - timedelta(hours=i) for i in range(70, 0, -1)]
    df_h1 = pd.DataFrame({
        "time": h1_dates,
        "open": [150.0] * 70,
        "high": [150.5] * 70,  # Rango de consolidación base (150.50)
        "low": [149.5] * 70,
        "close": [150.0] * 70,
    })

    # Marcamos el día anterior (2026-10-14): PDH = 152.00, PDL = 148.50
    # Velas de 2026-10-14 (hace entre 12 y 36 horas)
    for i in range(len(df_h1)):
        bar_ny = df_h1["time"].iloc[i].astimezone(NY_TZ)
        if bar_ny.date() == datetime(2026, 10, 14).date():
            df_h1.loc[i, "high"] = 151.80
            df_h1.loc[i, "low"] = 148.80
            df_h1.loc[i, "close"] = 150.20
    # Establecer PDH y PDL explícitos en el día previo
    prev_day_indices = [i for i in range(len(df_h1)) if df_h1["time"].iloc[i].astimezone(NY_TZ).date() == datetime(2026, 10, 14).date()]
    if prev_day_indices:
        df_h1.loc[prev_day_indices[5], "high"] = 152.50  # PDH = 152.50
        df_h1.loc[prev_day_indices[10], "low"] = 148.20  # PDL = 148.20

    # Rango Asiático (2026-10-14 20:00 a 2026-10-15 00:00 NY): Asia High = 151.20, Asia Low = 149.70
    asia_indices = [
        i for i in range(len(df_h1))
        if df_h1["time"].iloc[i].astimezone(NY_TZ).date() >= datetime(2026, 10, 14).date()
        and (df_h1["time"].iloc[i].astimezone(NY_TZ).hour in (20, 21, 22, 23, 0))
    ]
    for idx in asia_indices:
        df_h1.loc[idx, "high"] = 150.80
        df_h1.loc[idx, "low"] = 149.90
        df_h1.loc[idx, "close"] = 150.20
    if asia_indices:
        df_h1.loc[asia_indices[1], "high"] = 151.20  # Asia High = 151.20
        df_h1.loc[asia_indices[2], "low"] = 149.70   # Asia Low = 149.70

    # Vela de barrido (Judas Swing) en las últimas 3 velas H1 (ej. vela idx -2 a las 03:00 NY)
    if sweep_type == "ASIAN_HIGH":
        # Barre Asia High (151.20) pero no PDH (152.50): High = 151.60
        df_h1.loc[len(df_h1) - 2, "high"] = 151.60
        df_h1.loc[len(df_h1) - 2, "open"] = 150.30
        df_h1.loc[len(df_h1) - 2, "close"] = 150.40
        df_h1.loc[len(df_h1) - 2, "low"] = 150.10
        # Mecha superior: (151.60 - 150.40) / 1.50 = 1.20 / 1.50 = 0.80 (> 0.35 threshold)
    elif sweep_type == "PDH":
        # Barre PDH (152.50): High = 152.80
        df_h1.loc[len(df_h1) - 2, "high"] = 152.80
        df_h1.loc[len(df_h1) - 2, "open"] = 150.30
        df_h1.loc[len(df_h1) - 2, "close"] = 150.50
        df_h1.loc[len(df_h1) - 2, "low"] = 150.10
        # Mecha superior: (152.80 - 150.50) / 2.70 = 2.30 / 2.70 = 0.85 (> 0.35)

    # Vela actual H1 cerrada (idx -1)
    df_h1.loc[len(df_h1) - 1, "high"] = 150.60
    df_h1.loc[len(df_h1) - 1, "open"] = 150.40
    df_h1.loc[len(df_h1) - 1, "close"] = 149.80
    df_h1.loc[len(df_h1) - 1, "low"] = 149.60

    # 3. M15 Data: 40 velas M15 con desplazamiento y FVG bajista
    m15_dates = [eval_time_utc - timedelta(minutes=15 * i) for i in range(40, 0, -1)]
    df_m15 = pd.DataFrame({
        "time": m15_dates,
        "open": [150.40] * 40,
        "high": [150.60] * 40,
        "low": [150.20] * 40,
        "close": [150.30] * 40,
    })
    # Formar FVG bajista en velas -4, -3, -2
    # Vela -4: vela alcista previa high=151.00, low=150.20
    df_m15.loc[36, ["open", "high", "low", "close"]] = [150.30, 151.00, 150.20, 150.80]
    # Vela -3: gran desplazamiento bajista (MSS) con cuerpo amplio
    df_m15.loc[37, ["open", "high", "low", "close"]] = [150.80, 150.85, 149.50, 149.60]
    # Vela -2: vela baja high=149.90, low=149.40 (Gap entre low(36)=150.20 y high(38)=149.90 -> FVG bajista de 149.90 a 150.20)
    df_m15.loc[38, ["open", "high", "low", "close"]] = [149.60, 149.90, 149.40, 149.50]
    # Vela -1: mitigación hacia 150.05 (dentro del FVG) y fuerte quiebre de soporte a 149.20
    df_m15.loc[39, ["open", "high", "low", "close"]] = [150.00, 150.05, 149.10, 149.20]

    return df_h4, df_h1, df_m15, eval_time_utc


def test_asian_range_high_sweep_manipulation_confirmed():
    """Un barrido de Asian High durante Londres con mecha de rechazo es reconocido

    como manipulación institucional válida y confirma la señal de venta en ICT.
    """
    df_h4, df_h1, df_m15, eval_time_utc = build_market_data_with_asian_range_and_pdh(sweep_type="ASIAN_HIGH")
    provider = MockCandleProvider(df_h4=df_h4, df_h1=df_h1, df_m15=df_m15)
    cfg = ICTSabriMalleConfig(
        asian_range_sweep_enabled=True,
        pdh_pdl_sweep_enabled=True,
    )
    strat = ICTSabriMalleStrategy(data_provider=provider, config=cfg)

    res = strat.analyze_symbol("GBPJPY", now_utc=eval_time_utc)
    assert res["valid"] is True, f"Expected valid confirmation, got reason: {res.get('reason')}"
    assert res["action"] == "ICT_SABRI_MALLE_CONFIRMED"
    signal = res["signal"]
    assert signal["direction"] == "SELL"
    assert "ASIAN_RANGE_HIGH" in signal["swept_liquidity_source"]
    assert signal["asian_range_swept"] is True


def test_previous_day_high_pdh_sweep_manipulation_confirmed():
    """Un barrido de Previous Day High (PDH) con mecha de rechazo es reconocido

    como manipulación institucional válida (BSL sweep) y confirma la señal de venta en ICT.
    """
    df_h4, df_h1, df_m15, eval_time_utc = build_market_data_with_asian_range_and_pdh(sweep_type="PDH")
    provider = MockCandleProvider(df_h4=df_h4, df_h1=df_h1, df_m15=df_m15)
    cfg = ICTSabriMalleConfig(
        asian_range_sweep_enabled=True,
        pdh_pdl_sweep_enabled=True,
    )
    strat = ICTSabriMalleStrategy(data_provider=provider, config=cfg)

    res = strat.analyze_symbol("USDJPY", now_utc=eval_time_utc)
    assert res["valid"] is True, f"Expected valid confirmation, got reason: {res.get('reason')}"
    assert res["action"] == "ICT_SABRI_MALLE_CONFIRMED"
    signal = res["signal"]
    assert signal["direction"] == "SELL"
    assert "PREVIOUS_DAY_HIGH" in signal["swept_liquidity_source"]
    assert signal["pdh_pdl_swept"] is True


def test_previous_day_low_pdl_sweep_manipulation_confirmed():
    """Un barrido de Previous Day Low (PDL) con mecha de rechazo inferior es reconocido

    como manipulación institucional válida (SSL sweep) y confirma la señal de compra en ICT.
    """
    eval_time_ny = datetime(2026, 10, 15, 4, 30, tzinfo=NY_TZ)
    eval_time_utc = eval_time_ny.astimezone(timezone.utc)

    # H4: Tendencia alcista (EMA100 bajo el precio para sesgo BULLISH)
    h4_dates = [eval_time_utc - timedelta(hours=4 * i) for i in range(320, 0, -1)]
    df_h4 = pd.DataFrame({
        "time": h4_dates,
        "open": np.linspace(140.0, 150.0, 320),
        "high": np.linspace(141.0, 151.0, 320),
        "low": np.linspace(139.0, 149.0, 320),
        "close": np.linspace(140.5, 150.5, 320),
    })

    # H1: 70 velas con PDL en el día previo = 149.00
    h1_dates = [eval_time_utc - timedelta(hours=i) for i in range(70, 0, -1)]
    df_h1 = pd.DataFrame({
        "time": h1_dates,
        "open": [150.0] * 70,
        "high": [150.5] * 70,
        "low": [149.5] * 70,
        "close": [150.0] * 70,
    })
    prev_day_indices = [i for i in range(len(df_h1)) if df_h1["time"].iloc[i].astimezone(NY_TZ).date() == datetime(2026, 10, 14).date()]
    if prev_day_indices:
        df_h1.loc[prev_day_indices[5], "high"] = 151.00
        df_h1.loc[prev_day_indices[10], "low"] = 149.00  # PDL = 149.00

    # Barrido de PDL a 148.40 en vela -2 con mecha inferior larga
    df_h1.loc[len(df_h1) - 2, "low"] = 148.40
    df_h1.loc[len(df_h1) - 2, "open"] = 149.80
    df_h1.loc[len(df_h1) - 2, "close"] = 149.70
    df_h1.loc[len(df_h1) - 2, "high"] = 150.00
    # Mecha inferior: (149.70 - 148.40) / 1.60 = 1.30 / 1.60 = 0.81 (> 0.35)

    df_h1.loc[len(df_h1) - 1, "high"] = 150.40
    df_h1.loc[len(df_h1) - 1, "open"] = 149.70
    df_h1.loc[len(df_h1) - 1, "close"] = 150.20
    df_h1.loc[len(df_h1) - 1, "low"] = 149.60

    # M15: Desplazamiento alcista y FVG alcista
    m15_dates = [eval_time_utc - timedelta(minutes=15 * i) for i in range(40, 0, -1)]
    df_m15 = pd.DataFrame({
        "time": m15_dates,
        "open": [150.0] * 40,
        "high": [150.3] * 40,
        "low": [149.8] * 40,
        "close": [150.1] * 40,
    })
    # FVG alcista: vela 36 high=149.50, vela 37 cuerpo alcista 149.50->150.20, vela 38 low=149.80 (gap 149.50 - 149.80)
    df_m15.loc[36, ["open", "high", "low", "close"]] = [149.30, 149.50, 149.10, 149.40]
    df_m15.loc[37, ["open", "high", "low", "close"]] = [149.40, 150.20, 149.30, 150.10]
    df_m15.loc[38, ["open", "high", "low", "close"]] = [150.00, 150.10, 149.80, 150.05]
    # Mitigación y fuerte quiebre de resistencia (150.10) a 150.40 con cuerpo >= 45%
    df_m15.loc[39, ["open", "high", "low", "close"]] = [149.90, 150.45, 149.80, 150.40]

    provider = MockCandleProvider(df_h4=df_h4, df_h1=df_h1, df_m15=df_m15)
    cfg = ICTSabriMalleConfig(
        asian_range_sweep_enabled=True,
        pdh_pdl_sweep_enabled=True,
    )
    strat = ICTSabriMalleStrategy(data_provider=provider, config=cfg)

    res = strat.analyze_symbol("AUDUSD", now_utc=eval_time_utc)
    assert res["valid"] is True, f"Expected valid confirmation, got reason: {res.get('reason')}"
    assert res["action"] == "ICT_SABRI_MALLE_CONFIRMED"
    signal = res["signal"]
    assert signal["direction"] == "BUY"
    assert "PREVIOUS_DAY_LOW" in signal["swept_liquidity_source"]
    assert signal["pdh_pdl_swept"] is True


def test_asian_range_and_pdh_sweeps_disabled_by_env(monkeypatch):
    """Si los flags están desactivados por entorno, un barrido de Asian High durante la sesión

    de Nueva York (donde el rango de sesión es Londres) es rechazado al no superar el rango de Londres.
    """
    monkeypatch.setenv("DAEMONBLACKFX_ICT_ASIAN_RANGE_SWEEP", "0")
    monkeypatch.setenv("DAEMONBLACKFX_ICT_PDH_PDL_SWEEP", "0")
    monkeypatch.setenv("DAEMONBLACKFX_ICT_SB_HOURS_NY", "10")

    eval_time_ny = datetime(2026, 10, 15, 10, 15, tzinfo=NY_TZ)
    eval_time_utc = eval_time_ny.astimezone(timezone.utc)

    # H4: 320 velas bajistas
    h4_dates = [eval_time_utc - timedelta(hours=4 * i) for i in range(320, 0, -1)]
    df_h4 = pd.DataFrame({
        "time": h4_dates,
        "open": np.linspace(155.0, 150.0, 320),
        "high": np.linspace(156.0, 151.0, 320),
        "low": np.linspace(154.0, 149.0, 320),
        "close": np.linspace(154.5, 149.5, 320),
    })

    # H1: 70 velas hasta las 10:15 NY
    h1_dates = [eval_time_utc - timedelta(hours=i) for i in range(70, 0, -1)]
    df_h1 = pd.DataFrame({
        "time": h1_dates,
        "open": [150.0] * 70,
        "high": [150.5] * 70,
        "low": [149.5] * 70,
        "close": [150.0] * 70,
    })

    # Rango de Londres (02:00 a 05:00 NY): High = 153.00, Low = 149.00
    # Asian Range (20:00 a 00:00 NY): Asia High = 151.00
    for i in range(len(df_h1)):
        bar_ny = df_h1["time"].iloc[i].astimezone(NY_TZ)
        if bar_ny.date() == eval_time_ny.date() and 2 <= bar_ny.hour <= 5:
            df_h1.loc[i, "high"] = 153.00
            df_h1.loc[i, "low"] = 149.00
        elif (bar_ny.hour in (20, 21, 22, 23)) and bar_ny.date() >= eval_time_ny.date() - timedelta(days=1):
            df_h1.loc[i, "high"] = 151.00
            df_h1.loc[i, "low"] = 149.80

    # Vela en NY (idx -2) barre Asian High (151.40) pero NO barre el rango de Londres (153.00)
    df_h1.loc[len(df_h1) - 2, "high"] = 151.40
    df_h1.loc[len(df_h1) - 2, "open"] = 150.20
    df_h1.loc[len(df_h1) - 2, "close"] = 150.30
    df_h1.loc[len(df_h1) - 2, "low"] = 150.00

    # M15: datos básicos
    m15_dates = [eval_time_utc - timedelta(minutes=15 * i) for i in range(40, 0, -1)]
    df_m15 = pd.DataFrame({
        "time": m15_dates,
        "open": [150.0] * 40,
        "high": [150.3] * 40,
        "low": [149.8] * 40,
        "close": [150.1] * 40,
    })

    provider = MockCandleProvider(df_h4=df_h4, df_h1=df_h1, df_m15=df_m15)
    cfg = ICTSabriMalleConfig()
    strat = ICTSabriMalleStrategy(data_provider=provider, config=cfg)

    res = strat.analyze_symbol("GBPJPY", now_utc=eval_time_utc)
    # Al estar desactivado asian_range_sweep, el barrido de Asian High (151.40) no se toma
    # y como no superó el rango de Londres (153.00), no hay manipulación confirmada
    assert res["valid"] is False
    assert res["reason"] == "NO_JUDAS_SWING_MANIPULATION_CONFIRMED"
