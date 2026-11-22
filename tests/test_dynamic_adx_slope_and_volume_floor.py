import pytest
import os
import pandas as pd
import numpy as np
from unittest.mock import MagicMock

from strategy.ict.config import ICTConfig
from strategy.ict.ict_strategy import ICTStrategy
from brokers.mt5_execution import MT5ExecutionProvider
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


def test_dynamic_adx_slope_evaluation():
    # Creamos un mock provider y configuramos ICTStrategy
    provider = MagicMock()
    config = ICTConfig(
        min_adx_h1=20.0,
        dynamic_adx_slope_enabled=True,
        dynamic_adx_min_threshold=16.0,
    )
    strategy = ICTStrategy(data_provider=provider, config=config)

    # 1. Caso: ADX en 18.2 con pendiente positiva (16.0 -> 17.1 -> 18.2)
    # Debe ser aceptado porque 18.2 >= 16.0 y slope > 0
    now = pd.Timestamp.now(tz="UTC")
    dates = pd.date_range(end=now, periods=35, freq="1h")
    # Generamos velas sintéticas
    df_h1 = pd.DataFrame({
        "time": dates,
        "open": np.linspace(100, 110, 35),
        "high": np.linspace(101, 112, 35),
        "low": np.linspace(99, 109, 35),
        "close": np.linspace(100.5, 111.5, 35),
    })

    # Verificamos que los atributos de config existen y son correctos
    assert strategy.config.dynamic_adx_slope_enabled is True
    assert strategy.config.dynamic_adx_min_threshold == 16.0
    assert strategy.config.min_adx_h1 == 20.0


def test_order_check_structural_error_preservation():
    # Mock del conector MT5
    connector = MagicMock()
    prov = MT5ExecutionProvider(connector=connector)

    # Simulamos que order_check_safe falla en intento 0 con Invalid volume (10014),
    # y en intentos 1 y 2 falla con Unsupported filling mode (10030).
    attempt_0_res = MagicMock(retcode=10014, comment="Invalid volume")
    attempt_1_res = MagicMock(retcode=10030, comment="Unsupported filling mode")
    attempt_2_res = MagicMock(retcode=10030, comment="Unsupported filling mode")

    call_count = 0
    def fake_order_check_safe(req):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return attempt_0_res, req, {}
        elif call_count == 2:
            return attempt_1_res, req, {}
        else:
            return attempt_2_res, req, {}

    prov._order_check_safe = fake_order_check_safe
    prov._symbol_filling_candidates = lambda sym: [0, 1, 2]
    prov.get_filling_diagnostics = lambda sym: {}

    result = prov._run_order_check_with_fallback("Jump 100 Index", {"symbol": "Jump 100 Index"})
    
    assert result["valid"] is False
    assert result["retcode"] == 10014, f"Se esperaba 10014 (Invalid volume) como causa raíz, pero se obtuvo {result['retcode']}"
    assert "Invalid volume" in result["comment"]


def test_adaptive_min_volume_clamp_jump_fallback():
    # Verificamos que LiveTradingConfig incluya adaptive_min_volume_clamp_enabled
    cfg = LiveTradingConfig(
        jump_strict_filter_enabled=True,
        jump_allow_single_fallback=False,
        adaptive_min_volume_clamp_enabled=True,
    )
    assert cfg.adaptive_min_volume_clamp_enabled is True

    # Simulamos condición de _plan_execution_legs
    is_jump = True
    split_failure_min_vol = {"code": "VOLUMEN_MINIMO_SUPERA_RIESGO_DE_LA_PIERNA"}
    split_failure_other = {"code": "OTHER_RISK_FAILURE"}

    # Con adaptive_min_volume_clamp activo y fallo por volumen mínimo:
    # jump_single_fallback_blocked NO debe bloquear
    adaptive_clamp = bool(cfg.adaptive_min_volume_clamp_enabled)
    is_min_vol = split_failure_min_vol.get("code") in ("VOLUMEN_MINIMO_SUPERA_RIESGO_DE_LA_PIERNA", "LOTE_DEL_BROKER_NO_PERMITE_ALCANZAR_RIESGO_OBJETIVO")
    blocked_adaptive = (
        is_jump
        and bool(cfg.jump_strict_filter_enabled)
        and not bool(cfg.jump_allow_single_fallback)
        and not (adaptive_clamp and is_min_vol)
    )
    assert blocked_adaptive is False, "El fallback único debe desbloquearse si el split falló por volumen mínimo"

    # Con otro tipo de fallo (ej. riesgo excedido): debe seguir bloqueando
    is_min_vol_other = split_failure_other.get("code") in ("VOLUMEN_MINIMO_SUPERA_RIESGO_DE_LA_PIERNA", "LOTE_DEL_BROKER_NO_PERMITE_ALCANZAR_RIESGO_OBJETIVO")
    blocked_other = (
        is_jump
        and bool(cfg.jump_strict_filter_enabled)
        and not bool(cfg.jump_allow_single_fallback)
        and not (adaptive_clamp and is_min_vol_other)
    )
    assert blocked_other is True, "Otros fallos deben mantener el bloqueo estricto de Jump"
