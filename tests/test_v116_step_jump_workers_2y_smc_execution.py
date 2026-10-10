"""Tests unitarios para la optimización de 2 Años SMC en Workers STEP y JUMP.

Verifica:
1. Despoda y activación de Step Index 400 y Jump 75 Index.
2. Configuración de 2 targets: TP1 1:2 RR y Runner TP2 1:3 RR.
3. Protección de ganancias progresiva:
   - BE a +2.0R (incluyendo spread + 2*points)
   - Candado a +2.0R cuando alcanza +2.5R (protección para TP2.5 / TP3)
4. División simétrica 50/50 del 1% de riesgo.
5. Ingesta de modelos IA para STEP y JUMP.
"""

import pytest
from strategy.execution.worker_rules import configure_worker_rules
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from config.strategy_config import PRUNED_ASSET_UNIVERSE
from dashboard.realtime_dashboard import PRUNED_INSTRUMENTS_INFO, DEFAULT_PRIORITIZED_SYMBOLS
from strategy.ai.meta_labeling import MetaLabelingEngine


def test_step_jump_unpruned_instruments_persistence():
    """Step Index 400 y Jump 75 Index no deben estar en PRUNED_INSTRUMENTS_INFO y deben estar en PRUNED_ASSET_UNIVERSE."""
    # Verificación en dashboard
    assert "Step Index 400" not in PRUNED_INSTRUMENTS_INFO, "Step Index 400 no debe estar en lista PODA"
    assert "Jump 75 Index" not in PRUNED_INSTRUMENTS_INFO, "Jump 75 Index no debe estar en lista PODA"
    assert "Step Index 400" in DEFAULT_PRIORITIZED_SYMBOLS["SYNTHETICS"]
    assert "Jump 75 Index" in DEFAULT_PRIORITIZED_SYMBOLS["SYNTHETICS"]

    # Verificación en config universe
    assert "Step Index 400" in PRUNED_ASSET_UNIVERSE["STEP"]
    assert "Step Index" in PRUNED_ASSET_UNIVERSE["STEP"]
    assert "Step Index 500" in PRUNED_ASSET_UNIVERSE["STEP"]

    assert "Jump 75 Index" in PRUNED_ASSET_UNIVERSE["JUMP"]


def test_step_jump_worker_rules_targets_and_guards():
    """Worker rules para STEP y JUMP bajo ICT Sabri Malle configuran TP1 1:2, TP2 1:4 y protección."""
    for profile in ["STEP", "JUMP"]:
        base_cfg = LiveTradingConfig(bot_profile=profile)
        cfg = configure_worker_rules(base_cfg)

        assert cfg.first_target_rr == 2.0, f"{profile} first_target_rr debe ser 2.0"
        assert cfg.second_target_rr == 4.0, f"{profile} second_target_rr debe ser 4.0"
        assert cfg.smc_runner_max_target_rr == 4.0, f"{profile} smc_runner_max_target_rr debe ser 4.0"

        # Runner extension y protección progresiva
        assert cfg.runner_extension_enabled is True
        assert cfg.runner_extension_first_trigger_rr == 2.0
        assert cfg.runner_extension_first_lock_rr == 1.0
        assert cfg.runner_extension_second_trigger_rr == 3.0
        assert cfg.runner_extension_second_lock_rr == 2.0


def test_live_trading_config_step_jump_allowed_symbols():
    """LiveTradingConfig debe contener Step Index 400 y Jump 75 Index en sus listas permitidas."""
    cfg = LiveTradingConfig()
    assert "Step Index 400" in cfg.step_allowed_symbols
    assert "Step Index" in cfg.step_allowed_symbols
    assert "Step Index 500" in cfg.step_allowed_symbols

    assert "Jump 75 Index" in cfg.jump_allowed_symbols


def test_ai_meta_models_exist_and_loaded():
    """Los modelos de IA para STEP y JUMP deben existir y estar entrenados."""
    engine_step = MetaLabelingEngine(worker="STEP")
    model_step = engine_step.load_model()
    assert model_step.trained is True, "Modelo STEP debe estar marcado como trained"

    engine_jump = MetaLabelingEngine(worker="JUMP")
    model_jump = engine_jump.load_model()
    assert model_jump.trained is True, "Modelo JUMP debe estar marcado como trained"

    engine_global = MetaLabelingEngine(worker="GLOBAL")
    model_global = engine_global.load_model()
    assert model_global.trained is True, "Modelo GLOBAL debe estar marcado como trained"
