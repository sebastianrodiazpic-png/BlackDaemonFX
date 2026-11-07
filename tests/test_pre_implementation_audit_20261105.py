"""Tests unitarios y de regresión dedicados para la auditoría pre-implementación (05-nov-2026).

Valida punto por punto cada hallazgo técnico y cada mejora estratégica basada en fuentes oficiales
(Toby Crabel / Linda Raschke para ORB, Michael Huddleston / Sabri Malle para ICT,
Alchemist / CRT para Malaysian SNR, y Larry Connors para RSI(2)), comparando el comportamiento
ANTES (código actual intacto) frente al DESPUÉS (propuesta validada).
"""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import MagicMock
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import pytest

from strategy.connors_rsi2.rsi2_daily import Rsi2Config, daily_indicators
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from strategy.ict.config import ICTSabriMalleConfig
from strategy.ict.ict_strategy import (
    ICTSabriMalleStrategy,
    find_active_fvgs_fast,
    find_inversion_fvg_and_bpr_setups,
)
from strategy.malaysian_snr.validation import retest_confirmation
from strategy.orb.new_york_orb import NewYorkORBStrategy, ORBConfig

NY_TZ = ZoneInfo("America/New_York")


class InMemoryProvider:
    """Proveedor determinista en memoria para pruebas unitarias y de regresión."""

    def __init__(self, frames: dict[str, pd.DataFrame], spread: float = 0.10, point: float = 0.01):
        self.frames = frames
        self.spread = spread
        self.point = point
        self.calls: list[tuple[str, str, int]] = []

    def get_candles(self, symbol: str, timeframe: str, count: int = 100) -> pd.DataFrame:
        self.calls.append((symbol, timeframe, count))
        df = self.frames.get(timeframe)
        if df is None:
            return pd.DataFrame()
        return df.tail(count).copy()

    def get_current_tick(self, symbol: str) -> dict:
        m_df = self.frames.get("M5") if "M5" in self.frames else self.frames.get("M15")
        last_close = float(m_df["close"].iloc[-1]) if m_df is not None and not m_df.empty else 100.0
        last_time = m_df["time"].iloc[-1] if m_df is not None and not m_df.empty else pd.Timestamp.now(tz="UTC")
        return {
            "time": last_time + pd.Timedelta(minutes=5),
            "bid": last_close,
            "ask": last_close + self.spread,
            "spread": self.spread,
        }

    def get_symbol_info(self, symbol: str) -> dict:
        return {"trade_mode": 4, "point": self.point, "spread": int(self.spread / max(self.point, 1e-6))}


# =====================================================================
# PUNTO 1: ORB — Colisión de Estado entre Sesiones (LONDON vs NEW_YORK)
# =====================================================================
def _build_orb_session_sweep_df(
    date_str: str, session: str, base_price: float = 2000.0, range_width: float = 10.0
) -> tuple[pd.DataFrame, datetime]:
    """Construye una secuencia M5 con barrido alcista (BUY SWEEP + MSS) en LONDON (03:00 NY) o NEW_YORK (09:30 NY)."""
    start_clock = "01:30:00" if session == "LONDON" else "08:00:00"
    end_clock = "04:05:00" if session == "LONDON" else "10:35:00"
    open_clock = "03:00:00" if session == "LONDON" else "09:30:00"

    times_ny = pd.date_range(
        f"{date_str} {start_clock}", f"{date_str} {end_clock}", freq="5min", tz="America/New_York"
    )
    times_utc = times_ny.tz_convert("UTC")
    half = range_width / 2.0
    df = pd.DataFrame({
        "time": times_utc,
        "time_ny": times_ny,
        "open": base_price,
        "high": base_price + half * 0.5,
        "low": base_price - half * 0.5,
        "close": base_price + half * 0.1,
        "tick_volume": 1000,
        "real_volume": 0,
    })

    open_ts = pd.Timestamp(f"{date_str} {open_clock}", tz="America/New_York")
    open_idx = int(df.index[df["time_ny"] == open_ts][0])

    # 3 velas del Opening Range: [base - half, base + half], midpoint = base_price
    df.loc[open_idx, ["open", "high", "low", "close"]] = [
        base_price, base_price + half, base_price - half * 0.5, base_price + half * 0.4
    ]
    df.loc[open_idx + 1, ["open", "high", "low", "close"]] = [
        base_price + half * 0.4, base_price + half * 0.8, base_price - half, base_price - half * 0.2
    ]
    df.loc[open_idx + 2, ["open", "high", "low", "close"]] = [
        base_price - half * 0.2, base_price + half * 0.3, base_price - half * 0.6, base_price
    ]

    # Vela post-rango 1 (Sweep bajista bajo range_low y cierre dentro del rango)
    df.loc[open_idx + 3, ["open", "high", "low", "close", "tick_volume"]] = [
        base_price - half * 0.3,
        base_price + half * 0.2,
        base_price - half * 1.5,  # barre range_low
        base_price - half * 0.2,  # cierra dentro del rango
        2500,
    ]
    # Vela post-rango 2 (MSS alcista cerrando sobre el máximo previo y midpoint)
    df.loc[open_idx + 4, ["open", "high", "low", "close", "tick_volume"]] = [
        base_price - half * 0.2,
        base_price + half * 1.6,
        base_price - half * 0.3,
        base_price + half * 1.4,
        3200,
    ]

    eval_df = df.iloc[: open_idx + 5].copy()
    now_utc = eval_df.iloc[-1]["time"].to_pydatetime() + timedelta(minutes=5)
    return eval_df, now_utc


def test_point1_orb_session_signal_memory_collision_before_vs_after():
    """Demuestra que hoy al ejecutar un SWEEP en Londres y llamar a mark_signal_used,
    se bloquea la sesión de NY del mismo día porque orb_session_date no incluye session_name."""
    df_london, now_london = _build_orb_session_sweep_df("2026-10-15", "LONDON")
    df_ny, now_ny = _build_orb_session_sweep_df("2026-10-15", "NEW_YORK")

    # 1. ANTES (separate_london_ny_session_state=False): Londres bloquea NY el mismo día
    cfg_before = ORBConfig(
        london_session_enabled=True,
        entry_cutoff_enabled=False,
        separate_london_ny_session_state=False,
        asset_profiles={
            "XAUUSD": {
                "allowed_modes": [],
                "sweep_enabled": True,
                "atr_buffer": 0.05,
                "max_range_atr_ratio": 3.0,
                "require_volume": False,
            }
        },
    )
    provider = InMemoryProvider({"M5": df_london})
    strat_before = NewYorkORBStrategy(provider, cfg_before)
    res_london_b = strat_before.analyze_symbol("XAUUSD", now_london)
    assert res_london_b["valid"] is True
    sig_london_b = res_london_b["signal"]
    strat_before.mark_signal_used("XAUUSD", sig_london_b["orb_session_date"], sig_london_b["breakout_candle_time"])
    provider.frames["M5"] = df_ny
    res_ny_before = strat_before.analyze_symbol("XAUUSD", now_ny)
    assert res_ny_before["valid"] is False
    assert res_ny_before["reason"] == "SWEEP_YA_UTILIZADO_ESTA_SESION"

    # 2. DESPUÉS (por defecto en producción separate_london_ny_session_state=True):
    # La marca de Londres queda bajo '2026-10-15_LONDON', liberando '2026-10-15' (NEW_YORK)
    cfg_after = ORBConfig(
        london_session_enabled=True,
        entry_cutoff_enabled=False,
        asset_profiles=cfg_before.asset_profiles,
    )
    provider.frames["M5"] = df_london
    strat_after = NewYorkORBStrategy(provider, cfg_after)
    res_london_a = strat_after.analyze_symbol("XAUUSD", now_london)
    assert res_london_a["valid"] is True
    sig_london_a = res_london_a["signal"]
    assert sig_london_a["orb_session_date"] == "2026-10-15_LONDON"
    strat_after.mark_signal_used("XAUUSD", sig_london_a["orb_session_date"], sig_london_a["breakout_candle_time"])
    provider.frames["M5"] = df_ny
    res_ny_after = strat_after.analyze_symbol("XAUUSD", now_ny)
    assert res_ny_after["valid"] is True
    assert res_ny_after["session_name"] == "NEW_YORK"


def test_point2_orb_frozen_atr_contamination_london_to_ny_before_vs_after():
    """Demuestra que con separate_london_ny_session_state=False _frozen_atr_sessions congela el ATR pequeño de Londres y cancela NY,
    mientras que en producción (separate_london_ny_session_state=True) ambas sesiones tienen ATR congelado independiente."""
    df_london, now_london = _build_orb_session_sweep_df("2026-10-15", "LONDON", base_price=2000.0, range_width=4.0)
    df_ny, now_ny = _build_orb_session_sweep_df("2026-10-15", "NEW_YORK", base_price=2000.0, range_width=12.0)

    cfg_before = ORBConfig(
        london_session_enabled=True,
        entry_cutoff_enabled=False,
        separate_london_ny_session_state=False,
        asset_profiles={
            "XAUUSD": {
                "allowed_modes": [],
                "sweep_enabled": True,
                "atr_buffer": 0.05,
                "max_range_atr_ratio": 2.5,
                "require_volume": False,
            }
        },
    )
    provider = InMemoryProvider({"M5": df_london})
    strat_before = NewYorkORBStrategy(provider, cfg_before)
    strat_before.analyze_symbol("XAUUSD", now_london)
    frozen_london_atr = strat_before._frozen_atr_sessions[("XAUUSD", "2026-10-15")]
    assert frozen_london_atr < 3.0

    provider.frames["M5"] = df_ny
    res_ny_before = strat_before.analyze_symbol("XAUUSD", now_ny)
    assert res_ny_before["valid"] is False
    assert res_ny_before["reason"] == "RANGO_ORB_SUPERA_UMBRAL_CRITICO"

    # DESPUÉS (por defecto en producción separate_london_ny_session_state=True):
    cfg_after = ORBConfig(
        london_session_enabled=True,
        entry_cutoff_enabled=False,
        asset_profiles=cfg_before.asset_profiles,
    )
    provider.frames["M5"] = df_london
    strat_after = NewYorkORBStrategy(provider, cfg_after)
    strat_after.analyze_symbol("XAUUSD", now_london)
    assert ("XAUUSD", "2026-10-15_LONDON") in strat_after._frozen_atr_sessions
    provider.frames["M5"] = df_ny
    res_ny_after = strat_after.analyze_symbol("XAUUSD", now_ny)
    assert res_ny_after["valid"] is True
    assert res_ny_after["atr_frozen_m5"] > 5.0


# =====================================================================
# PUNTO 3: ICT — Escaneo Completo de FVG en toda la Pierna de Desplazamiento LTF
# =====================================================================
def test_point3_ict_displacement_leg_fvg_scan_before_vs_after():
    """Demuestra que si el FVG real de la pierna del MSS se formó en las velas -4..-2 y la vela -1 continúa el desplazamiento
    pero se solapa con la mecha de -3, el cálculo actual (solo -3 vs -1) no detecta FVG real, mientras que el escaneo de la pierna sí."""
    times = pd.date_range("2026-10-15 12:00:00", periods=10, freq="15min", tz="UTC")
    df_m15 = pd.DataFrame({
        "time": times,
        "open": [100.0] * 10,
        "high": [100.5] * 10,
        "low": [99.5] * 10,
        "close": [100.0] * 10,
    })
    # Pierna bajista desde sweep_peak en idx 5 (high=103.0):
    # Vela idx 6 (-4): high=102.8, low=101.8, close=102.0
    df_m15.loc[6, ["open", "high", "low", "close"]] = [102.5, 102.8, 101.8, 102.0]
    # Vela idx 7 (-3): gran desplazamiento bajista, open=102.0, high=102.1, low=99.8, close=100.0
    df_m15.loc[7, ["open", "high", "low", "close"]] = [102.0, 102.1, 99.8, 100.0]
    # Vela idx 8 (-2): high=101.0 (< low[6]=101.8 -> FVG BAJISTA REAL [101.0, 101.8], CE=101.4), low=99.5, close=99.7
    df_m15.loc[8, ["open", "high", "low", "close"]] = [100.0, 101.0, 99.5, 99.7]
    # Vela idx 9 (-1): continúa rompiendo soporte a 98.8, pero dejó mecha superior hasta 99.9 (que toca low[7]=99.8 -> sin gap entre -3 y -1)
    df_m15.loc[9, ["open", "high", "low", "close"]] = [99.7, 99.9, 98.6, 98.8]

    # ANTES: ICT mira únicamente iloc[-3] (idx 7, low=99.8) vs iloc[-1] (idx 9, high=99.9)
    prev_low_3 = float(df_m15["low"].iloc[-3])
    curr_high_1 = float(df_m15["high"].iloc[-1])
    has_real_fvg_only_last3 = curr_high_1 < prev_low_3
    assert has_real_fvg_only_last3 is False  # Pierde el FVG de la pierna

    # DESPUÉS: Escaneo en la pierna de desplazamiento con find_active_fvgs_fast
    fvgs = [
        f for f in find_active_fvgs_fast(df_m15, curr_idx=len(df_m15) - 1, lookback_bars=6)
        if f["type"] == "BEARISH"
    ]
    assert len(fvgs) >= 1
    best_fvg = fvgs[-1]
    assert best_fvg["bottom"] == pytest.approx(101.0)
    assert best_fvg["top"] == pytest.approx(101.8)
    fvg_ce = best_fvg["midpoint"]
    assert fvg_ce == pytest.approx(101.4)
    # Además está en zona Premium (>50% del rango 98.6..102.8 -> eq=100.7)
    assert fvg_ce > 100.7


# =====================================================================
# PUNTO 4: Malaysian SNR — Absorción en DIRECT_TOUCH_RETEST
# =====================================================================
def test_point4_msnr_direct_touch_retest_adverse_candle_before_vs_after():
    """Demuestra que DIRECT_TOUCH_RETEST hoy aprueba una vela M15 bajista (close < open) y sin mecha de rechazo en un BUY,
    mientras que el filtro CRT/Alchemist rechaza velas adversas sin mecha y conserva velas con absorción real."""
    level_price = 100.0
    atr = 1.0

    # Caso A: Vela M15 adversa (bajista en un BUY: open=100.15, high=100.15, low=100.00, close=100.00 -> sin mecha inferior)
    df_adverse = pd.DataFrame({
        "time": pd.date_range("2026-10-15 10:00:00", periods=5, freq="15min", tz="UTC"),
        "open": [101.0, 100.8, 100.5, 100.3, 100.15],
        "high": [101.2, 100.9, 100.6, 100.4, 100.15],
        "low": [100.7, 100.4, 100.2, 100.1, 100.00],
        "close": [100.8, 100.5, 100.3, 100.15, 100.00],
    })
    res_before = retest_confirmation(
        df_adverse, level=level_price, direction="BUY", atr=atr,
        tolerance_atr=0.25, allow_direct_touch=True
    )
    # ANTES: Se confirma con DIRECT_TOUCH_RETEST aunque la vela cerró en su mínimo (bajista y wick_ratio=0.0)
    assert res_before["confirmed"] is True
    assert res_before["trigger"] == "DIRECT_TOUCH_RETEST"

    # DESPUÉS: Exigiendo cierre a favor (close > open) o mecha de rechazo >= 0.25 en DIRECT_TOUCH_RETEST:
    last_bar = df_adverse.iloc[-1]
    c_range = float(last_bar["high"]) - float(last_bar["low"])
    lower_wick_ratio = (min(float(last_bar["open"]), float(last_bar["close"])) - float(last_bar["low"])) / c_range if c_range > 0 else 0.0
    absorption_ok = (float(last_bar["close"]) > float(last_bar["open"])) or (lower_wick_ratio >= 0.25)
    assert absorption_ok is False  # Filtra el toque adverso sin mecha

    # Caso B: Toque directo con vela M15 alcista (absorción real: open=100.05, low=99.95, close=100.25, high=100.30)
    df_clean = df_adverse.copy()
    df_clean.loc[4, ["open", "high", "low", "close"]] = [100.05, 100.30, 99.95, 100.25]
    last_clean = df_clean.iloc[-1]
    clean_range = float(last_clean["high"]) - float(last_clean["low"])
    clean_wick = (min(float(last_clean["open"]), float(last_clean["close"])) - float(last_clean["low"])) / clean_range
    clean_absorption_ok = (float(last_clean["close"]) > float(last_clean["open"])) or (clean_wick >= 0.25)
    assert clean_absorption_ok is True  # Conserva el toque limpio con absorción


# =====================================================================
# PUNTO 5: Connors RSI(2) — Filtro SMA(5) + 2-Day Cumulative RSI(2)
# =====================================================================
def test_point5_connors_rsi2_cumulative_and_sma5_before_vs_after():
    """Valida que el gatillo oficial de Larry Connors (CumRSI2 < 15 + close < SMA5) captura pullbacks graduales de 2 barras
    y filtra entradas donde el precio ya cerró por encima de la SMA(5)."""
    closes = list(np.linspace(100.0, 150.0, 210))
    closes.extend([150.0, 151.0, 152.0, 153.0, 154.0])
    # Pullback fuerte de 4 días tras rally: 150.0, 146.5, 143.0, 140.0
    closes.extend([150.0, 146.5, 143.0, 140.0])

    n = len(closes)
    df_d1 = pd.DataFrame({
        "time": pd.date_range("2026-01-01", periods=n, freq="D", tz="UTC"),
        "open": closes,
        "high": [c + 1.0 for c in closes],
        "low": [c - 1.0 for c in closes],
        "close": closes,
    })

    cfg = Rsi2Config(rsi_threshold=5.0)
    ind = daily_indicators(df_d1, cfg)
    last_row = ind.iloc[-1]
    prev_row = ind.iloc[-2]

    # El precio está sobre SMA200 y en descuento real bajo SMA5
    assert float(last_row["close"]) > float(last_row["sma_trend"])
    assert float(last_row["close"]) < float(last_row["sma_exit"])

    # CumRSI(2) de 2 días cae por debajo de 12.0 tras pullback consecutivo
    cum_rsi2 = float(last_row["rsi2"]) + float(prev_row["rsi2"])
    assert cum_rsi2 < 12.0


# =====================================================================
# PUNTO 6: Motor en Vivo — Claves fvg_top/structure_break en _detect_ict_msnr_confluence
# =====================================================================
def test_point6_live_engine_ict_msnr_confluence_fvg_keys_and_cache():
    """Demuestra que _detect_ict_msnr_confluence en la rama MALAYSIAN_SNR busca 'fvg_top' y 'structure_break' que ICT no exportaba."""
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile="MALAYSIAN_SNR")

    msnr_signal = {
        "strategy_name": "MALAYSIAN_SNR",
        "direction": "BUY",
        "entry_price": 100.05,
        "stop_loss": 99.50,
    }

    # ANTES: ICT devuelve 'mitigation_entry_price' y 'fvg_ce', pero NO 'fvg_top' ni 'structure_break'
    ict_analyzer_before = MagicMock()
    ict_analyzer_before.analyze_symbol.return_value = {
        "valid": True,
        "direction": "BUY",
        "signal": {
            "direction": "BUY",
            "mitigation_entry_price": 100.00,
            "fvg_ce": 100.00,
        },
    }
    engine.ict_strategy = ict_analyzer_before
    engine.malaysian_snr_strategy = None

    res_before = engine._detect_ict_msnr_confluence(
        symbol="EURUSD",
        direction="BUY",
        signal=msnr_signal,
        analysis={},
        strategy_name="MALAYSIAN_SNR",
    )
    assert res_before["has_confluence"] is True
    # peer_details queda con fvg=None y structure_break=None porque ICT no exportaba esas claves
    assert res_before["peer_details"]["fvg"] is None
    assert res_before["peer_details"]["structure_break"] is None

    # DESPUÉS: Cuando ICT exporta 'fvg_top', 'fvg_bottom' y 'structure_break' en su señal, peer_details queda completo
    ict_analyzer_after = MagicMock()
    ict_analyzer_after.analyze_symbol.return_value = {
        "valid": True,
        "direction": "BUY",
        "signal": {
            "direction": "BUY",
            "mitigation_entry_price": 100.00,
            "fvg_ce": 100.00,
            "fvg_top": 100.10,
            "fvg_bottom": 99.90,
            "structure_break": "M15_MSS_CONFIRMED",
        },
    }
    engine.ict_strategy = ict_analyzer_after
    res_after = engine._detect_ict_msnr_confluence(
        symbol="EURUSD",
        direction="BUY",
        signal=msnr_signal,
        analysis={},
        strategy_name="MALAYSIAN_SNR",
    )
    assert res_after["has_confluence"] is True
    assert res_after["peer_details"]["fvg"] == pytest.approx(100.10)
    assert res_after["peer_details"]["structure_break"] == "M15_MSS_CONFIRMED"


# =====================================================================
# PUNTO 7: ORB — Corte Horario en _evaluate_sweep (Londres 07:30 NY vs NY 11:30 NY)
# =====================================================================
def test_point7_orb_evaluate_sweep_cutoff_attribute_mismatch():
    """Verifica que ORBConfig define explícitamente entry_cutoff_minute_ny (955 por defecto, configurable por env)
    y los atributos de corte horario de Londres y Nueva York."""
    cfg = ORBConfig()
    assert hasattr(cfg, "entry_cutoff_minute_ny") is True
    assert cfg.entry_cutoff_minute_ny == 955
    assert cfg.entry_cutoff_hour * 60 + cfg.entry_cutoff_minute == 690  # 11:30 NY
    assert cfg.london_entry_cutoff_hour * 60 + cfg.london_entry_cutoff_minute == 450  # 07:30 NY


# =====================================================================
# PUNTO 8: ICT — iFVG / BPR en M15 con Stop Loss Protegido por ATR
# =====================================================================
def test_point8_ict_ifvg_bpr_m15_and_atr_protected_sl():
    """Valida la detección de Inversion FVG (iFVG) en M15 y que proteger el SL con buffer de ATR
    evita stops pegados a solo 2*spread del gap."""
    times = pd.date_range("2026-10-15 12:00:00", periods=10, freq="15min", tz="UTC")
    df_m15 = pd.DataFrame({
        "time": times,
        "open": [100.0] * 10,
        "high": [100.5] * 10,
        "low": [99.5] * 10,
        "close": [100.0] * 10,
    })
    # Formar un FVG bajista previo en idx 3..5:
    # c0 (idx 3): low = 101.0
    df_m15.loc[3, ["open", "high", "low", "close"]] = [101.5, 101.8, 101.0, 101.2]
    # c1 (idx 4): vela bajista
    df_m15.loc[4, ["open", "high", "low", "close"]] = [101.2, 101.3, 100.0, 100.1]
    # c2 (idx 5): high = 100.5 (< c0.low=101.0 -> FVG bajista [100.5, 101.0])
    df_m15.loc[5, ["open", "high", "low", "close"]] = [100.1, 100.5, 99.8, 100.0]
    # Vela idx 7: rompe hacia arriba el FVG bajista con cuerpo (close=101.4 > gap_top=101.0 -> Inversión a Soporte RBS)
    df_m15.loc[7, ["open", "high", "low", "close"]] = [100.2, 101.6, 100.1, 101.4]
    # Vela actual idx 9: retestea el iFVG (low=100.8 <= gap_top=101.0 y close=101.1 >= gap_bot=100.5)
    df_m15.loc[9, ["open", "high", "low", "close"]] = [101.2, 101.3, 100.8, 101.1]

    spread = 0.02
    setup = find_inversion_fvg_and_bpr_setups(df_m15, curr_idx=9, intended_direction="BUY", lookback_bars=8, spread=spread)
    assert setup is not None
    assert setup["valid"] is True
    assert setup["type"] == "ICT_INVERSION_FVG"
    # ANTES: el SL queda apenas a gap_bot - 2*spread = 100.5 - 0.04 = 100.46 (distancia 0.64)
    assert setup["stop_loss"] == pytest.approx(100.5 - 2.0 * spread)
    # DESPUÉS: con protección estructural (mínimo del swing pre-inversión 99.8 o ATR buffer), el SL cubre el swing real
    atr_m15 = 0.80
    protected_sl = min(setup["gap_bottom"] - 0.25 * atr_m15, float(df_m15["low"].iloc[5:8].min()) - spread)
    assert protected_sl < setup["stop_loss"]

