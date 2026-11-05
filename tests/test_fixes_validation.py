import pytest
from unittest.mock import Mock, MagicMock
from types import SimpleNamespace

from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig
from app.main import _resolve_universe_for_profile_provider, _recover_empty_synthetic_selection
from config.ict_instrument_policy import MSNR_ACIERTO47_SYNTHETICS, ict_active_symbols
from strategy.trend_pullback.config import DEFAULT_PULLBACK_SYMBOLS


class DummyProvider:
    def __init__(self):
        self.connector = SimpleNamespace()
    def get_symbol_info(self, sym):
        return {"name": sym}


def test_trend_pullback_universe_resolution():
    """Verifica que TREND_PULLBACK resuelva correctamente sus 17 instrumentos activos."""
    provider = DummyProvider()
    universe = _resolve_universe_for_profile_provider(provider, "TREND_PULLBACK")
    assert len(universe) == len(DEFAULT_PULLBACK_SYMBOLS)
    for sym in DEFAULT_PULLBACK_SYMBOLS:
        assert sym in universe


def test_malaysian_snr_policy_excludes_unlisted_symbols():
    """Verifica que los activos tóxicos (WR <= 50%) estén excluidos y los rentables (>50%) activos."""
    # Activos rescatados por WR > 50%
    assert "Vol over Boom 550" in MSNR_ACIERTO47_SYNTHETICS
    assert "Vol over Crash 550" not in MSNR_ACIERTO47_SYNTHETICS
    # Activos excluidos por WR <= 50%
    assert "Crash 900 Index" not in MSNR_ACIERTO47_SYNTHETICS
    assert "Jump 50 Index" not in MSNR_ACIERTO47_SYNTHETICS


def test_recover_empty_selections_trend_pullback_and_msnr_cleanup():
    """Verifica la autorecuperación de TREND_PULLBACK y MALAYSIAN_SNR si sus selecciones están vacías."""
    from config.ict_instrument_policy import MALAYSIAN_SNR_ACTIVE
    saved_calls = {}

    def mock_reader(profile, source="DEMO"):
        if profile == "SYNTHETICS":
            return {"selected_symbols": ["Step Index"]}
        if profile == "GOLD":
            return {"selected_symbols": ["XAUUSD"]}
        if profile == "ORB":
            return {"selected_symbols": ["BTCUSD"]}
        if profile == "TREND_PULLBACK":
            return {"selected_symbols": []}  # vacío -> autorecupera
        if profile == "MALAYSIAN_SNR":
            return {"selected_symbols": []}  # vacío -> autorecupera
        return None

    def mock_writer(symbols, selection_profile, source="DEMO"):
        saved_calls[selection_profile] = symbols
        return {"version": 1}

    mock_repo = SimpleNamespace(
        latest_instrument_selection_profile=mock_reader,
        save_instrument_selection_profile=mock_writer,
        save_audit_event=Mock(),
    )

    _recover_empty_synthetic_selection(mock_repo, {}, ["SYNTHETICS", "TREND_PULLBACK", "MALAYSIAN_SNR"])

    assert "TREND_PULLBACK" in saved_calls
    assert len(saved_calls["TREND_PULLBACK"]) == len(DEFAULT_PULLBACK_SYMBOLS)

    assert "MALAYSIAN_SNR" in saved_calls
    assert len(saved_calls["MALAYSIAN_SNR"]) == len(MALAYSIAN_SNR_ACTIVE)
    assert "Vol over Boom 550" in saved_calls["MALAYSIAN_SNR"]
    assert "Vol over Crash 550" not in saved_calls["MALAYSIAN_SNR"]


def test_effective_min_acceptable_fill_rr_tp1_tolerance():
    """Verifica que la pierna TP1 goce de la tolerancia a micro-slippage (0.90R)."""
    config = LiveTradingConfig(
        min_acceptable_fill_rr=1.0,
        min_acceptable_fill_rr_tp1=0.90,
    )
    engine = LiveTradingEngine(
        provider=Mock(),
        repository=Mock(),
        executor=Mock(),
        lifecycle_manager=Mock(),
        config=config,
    )

    # Pierna TP1 (planned_rr=1.0) -> debe permitir hasta 0.90
    thresh_tp1 = engine._effective_min_acceptable_fill_rr(planned_rr=1.0, leg_name="TP1")
    assert thresh_tp1 == 0.90

    # Pierna Runner TP2 (planned_rr=2.0) -> debe exigir 1.0
    thresh_tp2 = engine._effective_min_acceptable_fill_rr(planned_rr=2.0, leg_name="RUNNER")
    assert thresh_tp2 == 1.0


def test_invalidation_exit_allows_minor_tp1_slippage():
    """Verifica que un slippage menor en TP1 (ej. 0.98R) NO dispare salida de emergencia."""
    config = LiveTradingConfig(
        emergency_unfavorable_rr_exit_enabled=True,
        min_acceptable_fill_rr=1.0,
        min_acceptable_fill_rr_tp1=0.90,
    )
    engine = LiveTradingEngine(
        provider=Mock(),
        repository=Mock(),
        executor=Mock(),
        lifecycle_manager=Mock(),
        config=config,
    )

    close_mock = Mock()
    trade = {"instrument": "Step Index", "direction": "SELL"}
    metadata = {
        "trade_leg": "TP1",
        "execution_rr_audit": {
            "filled_target_rr": 0.9868,
            "planned_target_rr": 1.0,
        }
    }

    result = engine._analysis_invalidation_exit(
        trade=trade,
        metadata=metadata,
        current_rr=0.1,
        close_position=close_mock,
    )
    # No debe haber cerrado
    close_mock.assert_not_called()
    assert result["managed"] is False
    assert result["closed"] is False


def test_invalidation_exit_still_aborts_severe_slippage():
    """Verifica que un slippage severo en TP1 (ej. 0.50R < 0.90R) SÍ dispare salida forzada."""
    config = LiveTradingConfig(
        emergency_unfavorable_rr_exit_enabled=True,
        min_acceptable_fill_rr=1.0,
        min_acceptable_fill_rr_tp1=0.90,
    )
    engine = LiveTradingEngine(
        provider=Mock(),
        repository=Mock(),
        executor=Mock(),
        lifecycle_manager=Mock(),
        config=config,
    )

    close_mock = Mock(return_value={"closed": True})
    trade = {"instrument": "Step Index", "direction": "SELL"}
    metadata = {
        "trade_leg": "TP1",
        "execution_rr_audit": {
            "filled_target_rr": 0.50,
            "planned_target_rr": 1.0,
        }
    }

    result = engine._analysis_invalidation_exit(
        trade=trade,
        metadata=metadata,
        current_rr=-0.1,
        close_position=close_mock,
    )
    close_mock.assert_called_once_with("emergency_slippage_unfavorable_rr")
    assert result["managed"] is True
    assert result["closed"] is True
    assert "EMERGENCY_SLIPPAGE_EXIT" in result["reason"]
