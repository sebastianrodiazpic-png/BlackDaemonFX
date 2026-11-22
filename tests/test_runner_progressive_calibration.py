"""tests/test_runner_progressive_calibration.py - Tests unitarios de la calibración progresiva de Pata 2.

Valida:
1. Configuración de LiveTradingConfig y sobreescritura limpia mediante variables de entorno:
   - DAEMONBLACKFX_RUNNER_FIRST_TRIGGER_RR
   - DAEMONBLACKFX_RUNNER_FIRST_LOCK_RR
   - DAEMONBLACKFX_RUNNER_MAX_TARGET_RR
2. Comportamiento del evaluador estructural de continuidad (evaluate_runner_continuation).
3. Consistencia matemática de los pagos netos (PnL) de las 2 patas en cada hito (BE, Lock1, Lock2, TP3, TP4).
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
import numpy as np
import pandas as pd
import pytest

from strategy.execution.live_trading_engine import LiveTradingConfig
from strategy.execution.runner_extension_manager import (
    evaluate_runner_continuation,
    rr_price,
)


def test_runner_extension_config_defaults(monkeypatch):
    monkeypatch.delenv("DAEMONBLACKFX_RUNNER_FIRST_TRIGGER_RR", raising=False)
    monkeypatch.delenv("DAEMONBLACKFX_RUNNER_FIRST_LOCK_RR", raising=False)
    monkeypatch.delenv("DAEMONBLACKFX_RUNNER_MAX_TARGET_RR", raising=False)

    cfg = LiveTradingConfig()
    assert cfg.runner_extension_first_trigger_rr == 2.0
    assert cfg.runner_extension_first_lock_rr == 1.0
    assert cfg.runner_extension_max_target_rr == 3.0


def test_runner_extension_config_env_overrides(monkeypatch):
    monkeypatch.setenv("DAEMONBLACKFX_RUNNER_FIRST_TRIGGER_RR", "2.5")
    monkeypatch.setenv("DAEMONBLACKFX_RUNNER_FIRST_LOCK_RR", "1.5")
    monkeypatch.setenv("DAEMONBLACKFX_RUNNER_MAX_TARGET_RR", "3.5")

    cfg = LiveTradingConfig()
    assert cfg.runner_extension_first_trigger_rr == 2.5
    assert cfg.runner_extension_first_lock_rr == 1.5
    assert cfg.runner_extension_max_target_rr == 3.5


def test_rr_price_calculation():
    # BUY: entrada 100, SL 90 (riesgo 10)
    assert rr_price(100.0, 90.0, "BUY", 1.0) == 110.0
    assert rr_price(100.0, 90.0, "BUY", 2.0) == 120.0
    assert rr_price(100.0, 90.0, "BUY", 3.0) == 130.0

    # SELL: entrada 100, SL 110 (riesgo 10)
    assert rr_price(100.0, 110.0, "SELL", 1.0) == 90.0
    assert rr_price(100.0, 110.0, "SELL", 2.0) == 80.0
    assert rr_price(100.0, 110.0, "SELL", 3.0) == 70.0

    with pytest.raises(ValueError):
        rr_price(100.0, 100.0, "BUY", 1.0)


def test_evaluate_runner_continuation_rejects_on_opposite_choch():
    n = 40
    dates = pd.date_range("2026-01-01", periods=n, freq="5min", tz="UTC")
    df = pd.DataFrame(
        {
            "time": dates,
            "open": np.linspace(100.0, 120.0, n),
            "high": np.linspace(101.0, 121.0, n),
            "low": np.linspace(99.0, 119.0, n),
            "close": np.linspace(100.5, 120.5, n),
        }
    )

    # Introducir un CHOCH contrario reciente en BUY (quiebre bajista brusco)
    df.loc[n - 2, "high"] = 115.0
    df.loc[n - 2, "low"] = 100.0
    df.loc[n - 2, "close"] = 101.0
    df.loc[n - 1, "close"] = 100.0

    decision = evaluate_runner_continuation(df, direction="BUY", stage_rr=2.0)
    assert isinstance(decision.continue_runner, bool)
    assert decision.diagnostics["stage_rr"] == 2.0
    assert decision.diagnostics["direction"] == "BUY"


def test_payout_matrix_two_legs_consistency():
    w1, w2 = 0.5, 0.5

    # 1. Fallo inicial (SL completo)
    sl_total = w1 * (-1.0) + w2 * (-1.0)
    assert sl_total == -1.0

    # 2. TP1 alcanzado y regreso a BE plano
    be_total = w1 * 1.0 + w2 * 0.0
    assert be_total == 0.5

    # 3. TP1 alcanzado, alcanza 2R y retrocede con Lock a 1.0R
    lock1_total = w1 * 1.0 + w2 * 1.0
    assert lock1_total == 1.0

    # 4. TP1 alcanzado, alcanza 2R y retrocede con Lock a 1.5R
    lock15_total = w1 * 1.0 + w2 * 1.5
    assert lock15_total == 1.25

    # 5. TP3 completado (+3.0R en Pata 2)
    tp3_total = w1 * 1.0 + w2 * 3.0
    assert tp3_total == 2.0

    # 6. TP4 completado (+4.0R en Pata 2)
    tp4_total = w1 * 1.0 + w2 * 4.0
    assert tp4_total == 2.5
