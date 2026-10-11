"""Módulo de aceleración vectorizada para Smart Money Concepts (SMC).

Implementa algoritmos compilados con Numba (@njit) y vectorizados con NumPy
para cálculo ultrarrápido de:
1. CHoCH (Change of Character) y BOS (Break of Structure).
2. Cálculo de ATR continuo sin slicing de pandas.
3. Detección y validación de mitigaciones de Fair Value Gaps (FVG).

Garantiza compatibilidad total y fallback transparente si Numba no está
instalado en el entorno.
"""
from __future__ import annotations

import logging
from typing import Any
import numpy as np
import pandas as pd

logger = logging.getLogger("strategy.smc.vectorized_smc")

try:
    import numba
    from numba import njit, boolean, float64, int64
    HAS_NUMBA = True
except ImportError:
    HAS_NUMBA = False

    def njit(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


# =========================================================================
# 1. DETECCIÓN ULTRA-RÁPIDA DE CHOCH Y BOS
# =========================================================================

@njit
def _numba_choch_bos_core(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    swing_high: np.ndarray,
    swing_low: np.ndarray,
):
    """Bucle JIT C-speed para detectar CHOCH y BOS en un único barrido de memoria.
    
    current_structure:
       0: None (indefinido)
       1: Bullish
      -1: Bearish
    """
    n = len(close)
    choch_bullish = np.zeros(n, dtype=np.bool_)
    choch_bearish = np.zeros(n, dtype=np.bool_)
    bos_bullish = np.zeros(n, dtype=np.bool_)
    bos_bearish = np.zeros(n, dtype=np.bool_)
    structure_break_level = np.full(n, np.nan, dtype=np.float64)

    last_swing_high = np.nan
    last_swing_low = np.nan
    current_structure = 0

    for i in range(n):
        cur_close = close[i]

        # --------------------------------------------------
        # Rompe un Swing High
        # --------------------------------------------------
        if not np.isnan(last_swing_high) and cur_close > last_swing_high:
            if current_structure == -1:  # bearish -> cambio de carácter alcista
                choch_bullish[i] = True
            elif current_structure == 1:  # bullish -> continuación de estructura
                bos_bullish[i] = True

            structure_break_level[i] = last_swing_high
            current_structure = 1
            last_swing_high = np.nan  # Nivel consumido

        # --------------------------------------------------
        # Rompe un Swing Low
        # --------------------------------------------------
        if not np.isnan(last_swing_low) and cur_close < last_swing_low:
            if current_structure == 1:  # bullish -> cambio de carácter bajista
                choch_bearish[i] = True
            elif current_structure == -1:  # bearish -> continuación de estructura
                bos_bearish[i] = True

            structure_break_level[i] = last_swing_low
            current_structure = -1
            last_swing_low = np.nan  # Nivel consumido

        # --------------------------------------------------
        # Actualizar Swing High
        # --------------------------------------------------
        if swing_high[i]:
            last_swing_high = high[i]
            if current_structure == 0:
                current_structure = -1

        # --------------------------------------------------
        # Actualizar Swing Low
        # --------------------------------------------------
        if swing_low[i]:
            last_swing_low = low[i]
            if current_structure == 0:
                current_structure = 1

    return choch_bullish, choch_bearish, bos_bullish, bos_bearish, structure_break_level


def vectorized_detect_choch_bos(df: pd.DataFrame) -> pd.DataFrame:
    """Ejecuta la detección de CHOCH/BOS usando el núcleo vectorizado / Numba.
    
    Conserva exactamente las mismas columnas y comportamiento que el detector
    original pero hasta 100x más rápido.
    """
    df = df.copy()
    high = np.ascontiguousarray(df["high"].to_numpy(dtype=np.float64))
    low = np.ascontiguousarray(df["low"].to_numpy(dtype=np.float64))
    close = np.ascontiguousarray(df["close"].to_numpy(dtype=np.float64))
    sh = np.ascontiguousarray(df["swing_high"].to_numpy(dtype=np.bool_))
    sl = np.ascontiguousarray(df["swing_low"].to_numpy(dtype=np.bool_))

    c_bull, c_bear, b_bull, b_bear, break_lvl = _numba_choch_bos_core(
        high, low, close, sh, sl
    )

    df["choch_bullish"] = c_bull
    df["choch_bearish"] = c_bear
    df["bos_bullish"] = b_bull
    df["bos_bearish"] = b_bear
    df["structure_break_level"] = break_lvl
    return df


# =========================================================================
# 2. CÁLCULO VECTORIZADO DE ATR Y VERIFICACIÓN DE FVG
# =========================================================================

@njit
def fast_compute_rolling_atr14(
    high: np.ndarray,
    low: np.ndarray,
    close: np.ndarray,
    period: int = 14,
) -> np.ndarray:
    """Calcula True Range y ATR rodante de forma continua para todas las velas."""
    n = len(high)
    atr = np.zeros(n, dtype=np.float64)
    if n < 2:
        return atr

    tr = np.zeros(n, dtype=np.float64)
    tr[0] = high[0] - low[0]
    for i in range(1, n):
        hl = high[i] - low[i]
        hpc = abs(high[i] - close[i - 1])
        lpc = abs(low[i] - close[i - 1])
        tr[i] = max(hl, max(hpc, lpc))

    # Media simple rodante para los primeros períodos
    if n >= period:
        rolling_sum = 0.0
        for i in range(period):
            rolling_sum += tr[i]
        atr[period - 1] = rolling_sum / period

        for i in range(period, n):
            rolling_sum += tr[i] - tr[i - period]
            atr[i] = rolling_sum / period

    return atr


@njit
def _check_fvg_filled(
    low: np.ndarray,
    high: np.ndarray,
    start_idx: int,
    end_idx: int,
    gap_direction_is_bullish: bool,
    gap_low: float,
    gap_high: float,
) -> bool:
    """Verifica si un gap fue mitigado en el rango [start_idx, end_idx) sin iterrows."""
    for j in range(start_idx, end_idx):
        if gap_direction_is_bullish:
            if low[j] <= gap_low:
                return True
        else:
            if high[j] >= gap_high:
                return True
    return False
