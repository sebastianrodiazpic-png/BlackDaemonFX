"""11-nov-2026: choque de ADX en Step (MSNR) y bloqueo de ciclo sin operación virtual.

1. Step en MSNR: el mínimo de ADX de ejecución (25) caía dentro del tramo (25, 40] bloqueado por el filtro de
   régimen, así que solo pasaba ADX > 40. Con la política "regime" (por defecto) el mínimo baja al suelo
   configurado (12) y el tramo (25, 40] lo sigue bloqueando el filtro de régimen. "strict" conserva lo anterior.
2. Un disparo ICT cuyo resultado es BLOCKED_SYMBOL_CYCLE no ocupa el símbolo con una operación virtual.
"""
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from strategy.malaysian_snr.runtime_settings import msnr_default_settings


def _engine(**cfg):
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile="MALAYSIAN_SNR", source="DEMO", **cfg)
    engine.provider = Mock()
    engine.events = []
    engine._persist_audit_event = lambda *a, **k: engine.events.append((a, k))
    engine._msnr_regime_filter_status = lambda force=False: {"verdict": "EN_PRUEBA"}
    settings = {**msnr_default_settings(), "version": 7}
    engine.malaysian_snr_strategy = SimpleNamespace(settings_snapshot=lambda: settings)
    return engine


def _signal(adx):
    return {"strategy_name": "MALAYSIAN_SNR", "adx": adx, "timeframe": "M15", "entry_timeframe": "M15",
            "structure_timeframe": "H1", "entry_confirmation": "M15_ZONE_REJECTION_CLOSE"}


def _passes_both(engine, symbol, adx):
    sig = _signal(adx)
    step = engine._step_quality_gate(symbol, sig)
    regime = engine._msnr_regime_filter_gate(symbol, sig, "MALAYSIAN_SNR")
    return step is None and regime is None, step, regime, sig


def test_defaults():
    cfg = LiveTradingConfig()
    assert cfg.msnr_step_adx_conflict_policy == "regime"
    assert cfg.msnr_step_regime_floor_adx == 12.0
    assert cfg.ict_trigger_lock_skip_actions == ("BLOCKED_SYMBOL_CYCLE",)
    assert msnr_default_settings()["step_min_adx"] == 25.0  # el choque parte de este valor por defecto


@pytest.mark.parametrize("adx, allowed", [(8, False), (11.9, False), (12, True), (18, True), (25, True),
                                         (25.01, False), (33, False), (40, False), (40.5, True), (55, True)])
def test_step_window_with_regime_policy(adx, allowed):
    ok, step, regime, sig = _passes_both(_engine(), "Step Index 200", adx)
    assert ok is allowed
    if allowed:
        quality = sig["step_execution_quality"]
        assert quality["minimum_adx"] == 12.0 and quality["captured_adx"] == float(adx)
        assert quality["adx_conflict_resolution"] == {"policy": "regime", "configured_min_adx": 25.0,
                                                       "effective_min_adx": 12.0, "regime_block_range": [25.0, 40.0]}
    elif adx < 12:
        assert step["reason"] == "MSNR_STEP_EXECUTION_ADX_BELOW_MINIMUM" and step["min_adx"] == 12.0
        assert step["adx_conflict_resolution"]["configured_min_adx"] == 25.0
    else:
        assert step is None and regime["action"] == "MSNR_REGIME_ADX_BLOCKED"  # el tramo perdedor sigue cerrado


@pytest.mark.parametrize("adx, allowed", [(18, False), (24.9, False), (25, True), (33, False), (40.5, True)])
def test_strict_policy_keeps_previous_behaviour(adx, allowed):
    ok, step, _, sig = _passes_both(_engine(msnr_step_adx_conflict_policy="strict"), "Step Index 200", adx)
    assert ok is allowed
    if adx < 25:
        assert step["min_adx"] == 25.0 and "adx_conflict_resolution" not in step
    if allowed:
        assert "adx_conflict_resolution" not in sig["step_execution_quality"]


def test_no_conflict_means_no_change():
    # Filtro de régimen apagado: manda el mínimo de Step tal cual.
    engine = _engine(msnr_regime_filter_mode="off")
    assert engine._step_quality_gate("Step Index 200", _signal(18))["min_adx"] == 25.0
    assert engine._step_quality_gate("Step Index 200", _signal(30)) is None
    # Mínimo por encima del tramo (decisión explícita de operar solo tendencia fuerte): se respeta.
    engine = _engine()
    engine.malaysian_snr_strategy = SimpleNamespace(
        settings_snapshot=lambda: {**msnr_default_settings(), "step_min_adx": 45.0, "version": 1})
    assert engine._step_quality_gate("Step Index 200", _signal(42))["min_adx"] == 45.0
    # Mínimo por debajo del tramo: no hay choque.
    engine.malaysian_snr_strategy = SimpleNamespace(
        settings_snapshot=lambda: {**msnr_default_settings(), "step_min_adx": 20.0, "version": 1})
    assert engine._step_quality_gate("Step Index 200", _signal(18))["min_adx"] == 20.0
    # Modo "conservar tramos" del filtro de régimen: no se toca el mínimo de Step.
    engine = _engine(msnr_regime_adx_keep_bands="0-15,40-50")
    assert engine._step_quality_gate("Step Index 200", _signal(14))["min_adx"] == 25.0


def test_floor_never_exceeds_band_start_and_per_symbol_minimum_is_used():
    engine = _engine(msnr_step_regime_floor_adx=30.0)
    assert engine._msnr_step_adx_floor("Step Index 200", 25.0)[0] == 25.0
    engine = _engine()
    engine.malaysian_snr_strategy = SimpleNamespace(settings_snapshot=lambda: {
        **msnr_default_settings(), "step_symbol_min_adx": {"Step Index": 23.0}, "version": 1})
    assert engine._step_quality_gate("Step Index", _signal(22))["min_adx"] == 23.0   # sin choque: 23 < 25
    assert engine._step_quality_gate("Step Index 200", _signal(22)) is None          # choque resuelto: suelo 12


def test_other_step_workers_are_untouched():
    engine = _engine()
    engine.config.bot_profile = "STEP"
    out = engine._step_quality_gate("Step Index", {"strategy_name": "ICT_SABRI_MALLE", "adx": 18, "timeframe": "M15"})
    assert out["reason"] == "STEP_REQUIRES_M15_ADX_ABOVE_25"


# --- Bloqueo de ciclo entre workers: sin operación virtual ---------------------------------------------------------

def _triggered_engine(**cfg):
    from datetime import timedelta
    from tests.test_ict_virtual_limit_entry import BAR, make_engine, signal_analysis
    engine, _ = make_engine([signal_analysis()], [(99.9, 100.0)], BAR + timedelta(minutes=16), **cfg)
    assert engine._ict_analysis_with_virtual_limit("Volatility 75 Index")["valid"] is True
    return engine


def test_symbol_cycle_block_does_not_occupy_symbol():
    engine = _triggered_engine()
    events = []
    engine._persist_audit_event = lambda *a, **k: events.append((a, k))
    assert engine._register_ict_trigger_block_lock("Volatility 75 Index", {"action": "BLOCKED_SYMBOL_CYCLE"}) is None
    assert "Volatility 75 Index" not in engine.__dict__.get("_ict_spread_locks", {})
    assert events[-1][1]["action"] == "SKIPPED"
    assert events[-1][1]["reason"] == "ICT_TRIGGER_LOCK_SKIPPED_INFRASTRUCTURE:BLOCKED_SYMBOL_CYCLE"
    # El disparo se descarta: un resultado posterior sin disparo nuevo tampoco ocupa el símbolo.
    assert engine._register_ict_trigger_block_lock("Volatility 75 Index", {"action": "MAX_TOTAL_OPEN_POSITIONS"}) is None
    assert engine._ict_spread_lock_gate("Volatility 75 Index") is None


def test_process_symbol_cycle_block_leaves_symbol_free():
    engine = _triggered_engine()
    engine._process_symbol_impl = lambda symbol, sync: {"symbol": symbol, "action": "BLOCKED_SYMBOL_CYCLE"}
    engine.process_symbol("Volatility 75 Index")
    assert "Volatility 75 Index" not in engine.__dict__.get("_ict_spread_locks", {})


def test_real_rejections_still_occupy_symbol_and_switch_restores_old_behaviour():
    engine = _triggered_engine()
    lock = engine._register_ict_trigger_block_lock("Volatility 75 Index", {"action": "MAX_TOTAL_OPEN_POSITIONS"})
    assert lock["reason"] == "ICT_SIGNAL_TRIGGERED_NOT_OPENED:MAX_TOTAL_OPEN_POSITIONS"
    engine = _triggered_engine(ict_trigger_lock_skip_actions=())
    lock = engine._register_ict_trigger_block_lock("Volatility 75 Index", {"action": "BLOCKED_SYMBOL_CYCLE"})
    assert lock["reason"] == "ICT_SIGNAL_TRIGGERED_NOT_OPENED:BLOCKED_SYMBOL_CYCLE"
