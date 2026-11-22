"""strategy/smc/warmup.py - Pre-calentamiento JIT Numba y pre-carga de módulos SMC.

Elimina el "Cold Start" de 10+ segundos en el arranque de los daemons compilando
anticipadamente los kernels Numba y cargando los módulos en memoria antes de recibir
el primer tick de mercado.

Configurable mediante:
    DAEMONBLACKFX_SMC_JIT_WARMUP=1 (por defecto '1' activado, '0' desactivado).
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict

import numpy as np
import pandas as pd

logger = logging.getLogger("strategy.smc.warmup")

_WARMED_UP = False


def warmup_smc_kernels(force: bool = False) -> Dict[str, Any]:
    """Compila por anticipado los kernels Numba de SMC usando datos sintéticos mínimos."""
    global _WARMED_UP

    enabled = os.getenv("DAEMONBLACKFX_SMC_JIT_WARMUP", "1").strip().lower() not in (
        "0",
        "false",
        "no",
        "off",
    )
    if (not enabled or _WARMED_UP) and not force:
        return {"warmed_up": _WARMED_UP, "enabled": enabled, "elapsed_ms": 0.0}

    t0 = time.perf_counter()

    try:
        from strategy.smc.vectorized_smc import (
            fast_compute_rolling_atr14,
            vectorized_detect_choch_bos,
        )

        n = 25
        dummy_df = pd.DataFrame(
            {
                "time": pd.date_range("2026-01-01", periods=n, freq="5min", tz="UTC"),
                "open": np.linspace(100.0, 105.0, n, dtype=np.float64),
                "high": np.linspace(101.0, 106.0, n, dtype=np.float64),
                "low": np.linspace(99.0, 104.0, n, dtype=np.float64),
                "close": np.linspace(100.5, 105.5, n, dtype=np.float64),
                "swing_high": np.zeros(n, dtype=bool),
                "swing_low": np.zeros(n, dtype=bool),
            }
        )
        dummy_df.loc[5, "swing_high"] = True
        dummy_df.loc[12, "swing_low"] = True

        # Forzar compilación JIT de CHOCH/BOS
        _ = vectorized_detect_choch_bos(dummy_df)

        # Forzar compilación JIT de ATR continuo
        _ = fast_compute_rolling_atr14(
            np.ascontiguousarray(dummy_df["high"].to_numpy(dtype=np.float64)),
            np.ascontiguousarray(dummy_df["low"].to_numpy(dtype=np.float64)),
            np.ascontiguousarray(dummy_df["close"].to_numpy(dtype=np.float64)),
            period=14,
        )

        _WARMED_UP = True
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        logger.info(
            f"[SMC WARMUP] Precalentamiento JIT completado con éxito en {elapsed_ms:.2f} ms"
        )
        return {"warmed_up": True, "enabled": True, "elapsed_ms": elapsed_ms}

    except Exception as exc:
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        logger.warning(f"[SMC WARMUP ERROR] No se pudo precalentar kernels: {exc}")
        return {
            "warmed_up": False,
            "enabled": True,
            "error": str(exc),
            "elapsed_ms": elapsed_ms,
        }
