# tests/test_health_audit_and_tripartite_enhancements.py
"""Tests unitarios y de integración para las mejoras del Health Audit:
- Propagación de strategy_name desde analysis/signal
- Calidad de ejecución Step Index sin falsos rechazos en Malaysian SNR
- Normalización canónica de claves de estrategia para workers MultiStrategia
- Clasificación visual y traducción al español de Centinela y Tripartita en Dashboard
- Preservación de probabilidades del modelo entrenado en Gate Tripartita
- Consulta dinámica por source en /api/entry-decisions
"""
import pytest
from unittest.mock import MagicMock
from strategy.confluence.tripartite_confluence_gate import (
    normalize_strategy_key,
    TripartiteConfluenceGate,
    TripartiteConfluenceConfig,
)
from dashboard.realtime_dashboard import (
    _action_label_es,
    _reason_label_es,
    _operational_state,
)


def test_normalize_strategy_key_multistrategy_workers():
    """Valida que los nombres de perfil de los workers sintéticos y forex se normalicen a ICT."""
    assert normalize_strategy_key("STEP") == "ICT"
    assert normalize_strategy_key("BOOM") == "ICT"
    assert normalize_strategy_key("CRASH") == "ICT"
    assert normalize_strategy_key("JUMP") == "ICT"
    assert normalize_strategy_key("VOLATILITY_3") == "ICT"
    assert normalize_strategy_key("FOREX_1") == "ICT"
    assert normalize_strategy_key("MALAYSIAN_SNR") == "MALAYSIAN_SNR"
    assert normalize_strategy_key("ORB") == "ORB"
    assert normalize_strategy_key("TREND_PULLBACK") == "TREND_PULLBACK"


def test_operational_state_sentinel_and_tripartite():
    """Valida que los bloqueos de Régimen y Tripartita tengan etiquetas e insignias warn específicas."""
    # Centinela
    st_centinela = _operational_state("MARKET_REGIME_BLOCKED", "MARKET_REGIME_TOXIC_BLOCKED:ERRATIC_WHIPSAW_VOLATILITY", None)
    assert st_centinela["key"] == "SENTINEL_BLOCKED"
    assert "CENTINELA" in st_centinela["label"]
    assert st_centinela["severity"] == "warn"

    # Tripartita
    st_tripartita = _operational_state("TRIPARTITE_CONFLUENCE_FILTER_REJECTED", "VETO_HUMAN_CRITERIA_ANTI_SPIKE", None)
    assert st_tripartita["key"] == "TRIPARTITE_BLOCKED"
    assert "TRIPARTITA" in st_tripartita["label"]
    assert st_tripartita["severity"] == "warn"

    # Poda estricta
    st_poda = _operational_state("REJECTED", "VETO_STRICT_PRUNING", None)
    assert st_poda["key"] == "TRIPARTITE_BLOCKED"
    assert st_poda["severity"] == "warn"


def test_action_and_reason_labels_translation():
    """Valida las traducciones legibles en español de los nuevos eventos."""
    assert "Centinela" in _action_label_es("MARKET_REGIME_BLOCKED")
    assert "Tripartita" in _action_label_es("TRIPARTITE_CONFLUENCE_FILTER_REJECTED")
    assert "spike" in _reason_label_es("VETO_HUMAN_CRITERIA_ANTI_SPIKE").lower()
    assert "latigazos" in _reason_label_es("ERRATIC_WHIPSAW_VOLATILITY").lower()
    assert "poda estricta" in _reason_label_es("VETO_STRICT_PRUNING").lower()


def test_step_quality_gate_allows_msnr_in_step_worker():
    """Valida que una señal Malaysian SNR sobre Step Index sea evaluada con sus propios controles sin rechazo falso de timeframe."""
    from strategy.execution.live_trading_engine import LiveTradingEngine
    from types import SimpleNamespace

    engine = LiveTradingEngine.__new__(LiveTradingEngine)
    engine.config = SimpleNamespace(
        bot_profile="STEP",
        step_prune_toxic_assets=False,
        step_min_adx=25.0,
    )
    engine._is_step_symbol = lambda s: "Step" in s
    engine._is_h4h1_signal = lambda s: False
    engine._msnr_step_adx_floor = lambda s, m: (m, None)
    
    mock_msnr = MagicMock()
    mock_msnr.settings_snapshot.return_value = {
        "step_min_adx": 20.0,
        "m5_confirmation_mode": "live",
        "version": "v1.0"
    }
    engine.malaysian_snr_strategy = mock_msnr

    # Señal MSNR M5 sobre Step Index en worker STEP
    signal = {
        "strategy_name": "MALAYSIAN_SNR",
        "symbol": "Step Index",
        "adx": 30.0,
        "entry_timeframe": "M5",
        "structure_timeframe": "H1",
        "confirmation_timeframe": "M5",
    }
    analysis = {
        "strategy_name": "MALAYSIAN_SNR",
        "adx": 30.0,
    }

    # No debe ser bloqueado con STEP_TIMEFRAME_TOO_LOW
    res = engine._step_quality_gate("Step Index", signal, analysis)
    assert res is None, f"Esperado None pero devolvió: {res}"


def test_evaluate_tripartite_gate_preserves_trained_ai_probability():
    """Valida que si el modelo de IA está entrenado (trained=True), se respete su probabilidad real."""
    from strategy.execution.live_trading_engine import LiveTradingEngine
    from types import SimpleNamespace

    engine = LiveTradingEngine.__new__(LiveTradingEngine)
    engine.config = SimpleNamespace(bot_profile="ICT")
    
    # Mock del tripartite gate
    mock_gate = MagicMock()
    mock_gate.config.enabled = True
    mock_gate.evaluate_confluence.return_value = MagicMock(allowed=True, veto_reasons=(), metadata={}, to_dict=lambda: {})
    engine.tripartite_confluence_gate = mock_gate

    signal = {
        "strategy_name": "ICT",
        "meta_label": {
            "allowed": True,
            "trained": True,
            "probability": 0.49,
            "net_expectancy_r": 0.12,
        }
    }

    # Llamar al evaluador
    engine._evaluate_tripartite_confluence_gate(
        symbol="EURUSD",
        direction="BUY",
        signal=signal,
        analysis=None,
        key="KEY_TEST",
    )

    # Verificar qué recibió gate.evaluate_confluence
    assert mock_gate.evaluate_confluence.called
    kwargs = mock_gate.evaluate_confluence.call_args[1]
    ai_eval = kwargs.get("ai_evaluation")
    assert ai_eval is not None
    # No debió ser forzado a 0.55 porque trained=True
    assert ai_eval["probability"] == 0.49
    assert ai_eval["net_expectancy_r"] == 0.12
