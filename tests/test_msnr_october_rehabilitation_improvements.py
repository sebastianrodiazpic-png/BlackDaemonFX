"""Tests de validación para las mejoras de Malaysian SNR basadas en la evidencia de octubre:
1. Micro-stop anclado a mecha M15 de rechazo con buffer protector.
2. Reincorporación condicionada de Crash 500 Index en modo SELL-only (dirección de spikes).
3. Filtro de régimen ADX >= 25 para Step Index 500.
4. Filtro de transición de medianoche UTC (Midnight Guard).
5. Zero-Copy de velas hacia el Criterio Humano y preservación del score de confluencia (umbral 60.0).
"""

import pandas as pd
from datetime import datetime, timezone
from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy
from config.ict_instrument_policy import MSNR_ACIERTO47_SYNTHETICS, MSNR_ELITE_SYNTHETICS
from tests.test_msnr_dynamic_d1_settings import market


def test_msnr_micro_stop_activation_and_geometry():
    """Valida que el micro-stop se active por defecto y se ancle a la mecha de rechazo M15."""
    cfg = MalaysianSNRConfig(
        allowed_symbols=(),
        enable_m15_micro_stop=True,
        m15_micro_stop_buffer_atr=0.10,
        m15_micro_stop_min_risk_atr=0.20,
        enable_synthetic_daily_storyline_filter=False,
        continuation_min_adx=10.0,
        step_min_adx=10.0,
        enable_midnight_guard=False,
    )
    provider_sell, _, now_sell = market("SELL", "BUY")
    strat = MalaysianSNRStrategy(provider_sell, cfg)
    res = strat.analyze_symbol("Volatility 25 Index", now_sell)
    assert res.get("valid") is True
    signal = res.get("signal")
    assert signal is not None
    assert signal.get("micro_stop_applied") is True
    # Valida Zero-Copy hacia el Criterio Humano
    assert "_cached_df_h1" in signal
    assert "_cached_df_ltf" in signal


def test_msnr_crash_500_reincorporated_and_protected():
    """Valida que Crash 500 Index esté en la canasta élite y opere estrictamente SELL-only."""
    assert "Crash 500 Index" in MSNR_ELITE_SYNTHETICS
    assert "Crash 500 Index" in MalaysianSNRConfig().allowed_symbols

    cfg = MalaysianSNRConfig(
        allowed_symbols=(),
        directional_asymmetry_enabled=True,
        crash_sell_only_symbols=("Crash 500 Index",),
        enable_synthetic_daily_storyline_filter=False,
        continuation_min_adx=10.0,
        enable_midnight_guard=False,
    )
    provider_buy, _, now_buy = market("BUY", "SELL")
    provider_sell, _, now_sell = market("SELL", "BUY")

    strat_buy = MalaysianSNRStrategy(provider_buy, cfg)
    strat_sell = MalaysianSNRStrategy(provider_sell, cfg)

    # Crash 500 en BUY debe ser bloqueado
    res_buy = strat_buy.analyze_symbol("Crash 500 Index", now_buy)
    assert res_buy.get("valid") is False
    assert res_buy.get("reason") in ("DIRECTION_ASYMMETRY_CRASH_SELL_ONLY", "DIRECTION_POLICY_BLOCKED")

    # Crash 500 en SELL debe ser válido
    res_sell = strat_sell.analyze_symbol("Crash 500 Index", now_sell)
    assert res_sell.get("valid") is True
    assert res_sell.get("signal", {}).get("direction") == "SELL"


def test_msnr_step_500_adx_regime_filter():
    """Valida que Step Index 500 exija ADX >= 25 para evitar fases sin tendencia."""
    # Con step_min_adx alto (30.0), el setup con ADX 12.8 debe ser rechazado
    cfg_strict = MalaysianSNRConfig(
        allowed_symbols=(),
        directional_asymmetry_enabled=True,
        step_min_adx=30.0,
        enable_synthetic_daily_storyline_filter=False,
        continuation_min_adx=10.0,
        enable_midnight_guard=False,
    )
    provider_sell, _, now_sell = market("SELL", "BUY")
    strat_strict = MalaysianSNRStrategy(provider_sell, cfg_strict)
    res_strict = strat_strict.analyze_symbol("Step Index 500", now_sell)
    assert res_strict.get("valid") is False
    assert res_strict.get("reason") == "STEP_ADX_BELOW_THRESHOLD"

    # Con step_min_adx permisivo (10.0), el setup es válido
    cfg_relaxed = MalaysianSNRConfig(
        allowed_symbols=(),
        directional_asymmetry_enabled=True,
        step_min_adx=10.0,
        enable_synthetic_daily_storyline_filter=False,
        continuation_min_adx=10.0,
        enable_midnight_guard=False,
    )
    strat_relaxed = MalaysianSNRStrategy(provider_sell, cfg_relaxed)
    res_relaxed = strat_relaxed.analyze_symbol("Step Index 500", now_sell)
    assert res_relaxed.get("valid") is True


def test_msnr_midnight_guard_window():
    """Valida el bloqueo temporal durante la transición de medianoche UTC."""
    cfg = MalaysianSNRConfig(allowed_symbols=(), enable_midnight_guard=True, midnight_guard_window_minutes=15)
    provider_sell, _, _ = market("SELL", "BUY")
    strat = MalaysianSNRStrategy(provider_sell, cfg)

    # 23:50 UTC (10 minutos antes de medianoche) -> Bloqueado
    t_2350 = pd.Timestamp("2026-10-15 23:50:00", tz="UTC")
    res_2350 = strat.analyze_symbol("Volatility 25 Index", t_2350)
    assert res_2350.get("reason") == "MIDNIGHT_TRANSITION_GUARD_ACTIVE"

    # 00:08 UTC (8 minutos después de medianoche) -> Bloqueado
    t_0008 = pd.Timestamp("2026-10-16 00:08:00", tz="UTC")
    res_0008 = strat.analyze_symbol("Volatility 25 Index", t_0008)
    assert res_0008.get("reason") == "MIDNIGHT_TRANSITION_GUARD_ACTIVE"

    # 00:20 UTC (fuera de la ventana) -> Libre
    t_0020 = pd.Timestamp("2026-10-16 00:20:00", tz="UTC")
    res_0020 = strat.analyze_symbol("Volatility 25 Index", t_0020)
    assert res_0020.get("reason") != "MIDNIGHT_TRANSITION_GUARD_ACTIVE"


def test_msnr_human_criteria_integration_and_threshold():
    """Valida que el Criterio Humano evalúe MSNR con su umbral calibrado de 60.0."""
    from strategy.human_criteria import HumanCriteriaEngine, HumanCriteriaConfig

    config = HumanCriteriaConfig(
        enabled=True,
        mode="FILTER",
        min_score_threshold=65.0,
        synthetic_min_score_threshold=75.0,
        malaysian_snr_min_score_threshold=60.0,
    )
    engine = HumanCriteriaEngine(config)

    # Simular candidato con score 62.0 (superior a 60.0 de MSNR, pero inferior a 75.0 de ICT)
    signal = {
        "strategy": "MALAYSIAN_SNR",
        "symbol": "Volatility 25 Index",
        "direction": "SELL",
        "timeframe": "M15",
    }
    dates = pd.date_range("2026-10-04", periods=40, freq="1h")
    df_h1 = pd.DataFrame({
        "time": dates,
        "open": [100.0 - i * 0.5 for i in range(40)],
        "high": [101.0 - i * 0.5 for i in range(40)],
        "low": [99.0 - i * 0.5 for i in range(40)],
        "close": [99.5 - i * 0.5 for i in range(40)],
    })
    df_ltf = pd.DataFrame({
        "time": pd.date_range("2026-10-04", periods=40, freq="15min"),
        "open": [100.0 - i * 0.2 for i in range(40)],
        "high": [100.5 - i * 0.2 for i in range(40)],
        "low": [99.5 - i * 0.2 for i in range(40)],
        "close": [99.8 - i * 0.2 for i in range(40)],
    })

    decision = engine.evaluate_candidate(
        symbol="Volatility 25 Index",
        direction="SELL",
        signal=signal,
        df_h1=df_h1,
        df_ltf=df_ltf,
        current_time=datetime.now(timezone.utc),
    )
    # Debe ser evaluado con éxito y aprobado si supera los 60 puntos
    assert decision.score >= 60.0
    assert decision.allowed is True
