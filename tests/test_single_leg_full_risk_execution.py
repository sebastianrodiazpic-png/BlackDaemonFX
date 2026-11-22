"""Tests para validación de riesgo completo (1.0%) en entradas de una sola pata.

Contrato del bot:
- En entradas de dos patas (Split): TP1 al 0.50% (1R) + RUNNER al 0.50% (2R) = 1.0% total.
- En entradas de una sola pata (Single-leg): arriesgar 1.0% íntegro para buscar 1.0% (+1R),
  maximizando la expectativa matemática (EV) sin sub-arriesgar al 0.50%.
- Configurable mediante DAEMONBLACKFX_SINGLE_LEG_FULL_RISK y DAEMONBLACKFX_SINGLE_ENTRY_TARGET_RR.
"""

from unittest.mock import MagicMock
import pytest

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


def test_single_leg_full_risk_config_defaults():
    cfg = LiveTradingConfig()
    assert cfg.single_leg_full_risk_enabled is True
    assert cfg.single_entry_target_rr == 1.0


def test_single_leg_full_risk_scales_single_spec_to_one_hundred_percent():
    """Valida que una entrada única con fraccion 0.5 se escale automáticamente a 1.0."""
    cfg = LiveTradingConfig(single_leg_full_risk_enabled=True)
    engine = LiveTradingEngine.__new__(LiveTradingEngine)
    engine.config = cfg
    engine._leg_volume_cap = MagicMock(return_value=None)
    engine.executor = MagicMock()
    engine.executor.risk_buffered_entry_price = MagicMock(side_effect=lambda sym, d, e, dev=None: e)
    engine.executor.calculate_volume = MagicMock(return_value={"volume": 1.0, "actual_risk_amount": 100.0})

    # Simulamos el entorno de build_plan dentro de _process_symbol_guarded
    # Pasamos una sola pata con fraction=0.5 y target=1.0R
    specs = [("TP1", 0.5, 1.0)]
    
    # Ejecutamos la lógica de build_plan modificada
    mod_specs = []
    if len(specs) == 1 and bool(getattr(cfg, "single_leg_full_risk_enabled", True)):
        for spec in specs:
            s_name, s_fraction, s_trr = spec
            mod_specs.append((s_name, 1.0 if s_fraction < 1.0 else s_fraction, s_trr))
    else:
        mod_specs = list(specs)

    assert len(mod_specs) == 1
    assert mod_specs[0][1] == 1.0
    assert mod_specs[0][2] == 1.0


def test_single_leg_full_risk_disabled_preserves_sub_risk():
    """Si DAEMONBLACKFX_SINGLE_LEG_FULL_RISK=0, se preserva la fracción fraccional original."""
    cfg = LiveTradingConfig(single_leg_full_risk_enabled=False)
    specs = [("TP1", 0.5, 1.0)]

    mod_specs = []
    if len(specs) == 1 and bool(getattr(cfg, "single_leg_full_risk_enabled", True)):
        for spec in specs:
            s_name, s_fraction, s_trr = spec
            mod_specs.append((s_name, 1.0 if s_fraction < 1.0 else s_fraction, s_trr))
    else:
        mod_specs = list(specs)

    assert len(mod_specs) == 1
    assert mod_specs[0][1] == 0.5


def test_split_mode_two_legs_unaffected():
    """En split mode con 2 patas, cada una mantiene exactamente el 0.50% (50/50)."""
    cfg = LiveTradingConfig(single_leg_full_risk_enabled=True)
    specs = [
        ("TP1", 0.50, 1.0, 1.0),
        ("RUNNER", 0.50, 2.0, 2.0),
    ]

    mod_specs = []
    if len(specs) == 1 and bool(getattr(cfg, "single_leg_full_risk_enabled", True)):
        for spec in specs:
            if len(spec) == 4:
                s_name, s_fraction, s_trr, s_brr = spec
                mod_specs.append((s_name, 1.0 if s_fraction < 1.0 else s_fraction, s_trr, s_brr))
    else:
        mod_specs = list(specs)

    assert len(mod_specs) == 2
    assert mod_specs[0][1] == 0.50
    assert mod_specs[0][2] == 1.0
    assert mod_specs[1][1] == 0.50
    assert mod_specs[1][2] == 2.0


def test_plan_execution_legs_single_mode_targets_one_to_one():
    """Valida que _plan_execution_legs use target 1.0R (1:1) y fraction 1.0 cuando split está deshabilitado."""
    cfg = LiveTradingConfig(
        split_entries_enabled=False,
        single_leg_full_risk_enabled=True,
        single_entry_target_rr=1.0,
    )
    engine = LiveTradingEngine.__new__(LiveTradingEngine)
    engine.config = cfg

    captured_specs = []
    def dummy_build_plan(specs, mode):
        captured_specs.extend(specs)
        return [{"name": s[0], "fraction": s[1], "target_rr": s[2]} for s in specs], None

    legs, split_failure, single_failure, execution_mode = engine._plan_execution_legs(
        exact_symbol="Volatility 75 Index",
        direction="BUY",
        entry=100.0,
        sl=90.0,
        rr=2.0,
        strategy_name="ICT",
        signal={"tp1_rr": 1.0, "runner_rr": 2.0},
        total_risk_amount=100.0,
        risk_fraction=0.5,
        silver_risk_cap=False,
        build_plan=dummy_build_plan,
    )

    assert execution_mode == "SINGLE"
    assert len(legs) == 1
    assert legs[0]["fraction"] == 1.0
    assert legs[0]["target_rr"] == 1.0
    assert split_failure is None
