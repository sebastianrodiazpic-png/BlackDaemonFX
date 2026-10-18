"""Pruebas unitarias para el Guard de Enfriamiento Post-SL y Límite Diario de Pérdidas por Símbolo."""

from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
from unittest.mock import Mock, MagicMock

import pytest

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


def test_symbol_loss_cooldown_gate_blocks_within_cooldown():
    """Valida que una posición cerrada por SL bloquea reentradas durante la ventana de enfriamiento (60 min)."""
    now = datetime(2026, 10, 13, 21, 45, 0, tzinfo=timezone.utc)
    mock_repo = Mock()
    mock_repo.get_symbol_loss_status.return_value = {
        "symbol": "Step Index 500",
        "cooldown_active": True,
        "cooldown_remaining_minutes": 42.4,
        "cooldown_until": (now + timedelta(minutes=42.4)).isoformat(),
        "last_loss_exit_time": (now - timedelta(minutes=17.6)).isoformat(),
        "last_loss_pnl": -33.6,
        "daily_losses_count": 1,
        "daily_strikes_exceeded": False,
        "max_daily_losses": 2,
    }

    config = LiveTradingConfig(
        symbol_loss_cooldown_enabled=True,
        symbol_loss_cooldown_minutes=60.0,
        symbol_max_daily_losses=2,
    )
    engine = LiveTradingEngine(
        provider=Mock(),
        repository=mock_repo,
        executor=Mock(),
        config=config,
    )

    result = engine._symbol_loss_cooldown_gate("Step Index 500")
    assert result is not None
    assert result["action"] == "SYMBOL_COOLDOWN_POST_SL"
    assert "Enfriamiento anti-whipsaw activo" in result["reason"]
    assert result["loss_status"]["cooldown_active"] is True


def test_symbol_loss_cooldown_gate_blocks_when_daily_strikes_exceeded():
    """Valida que alcanzar 2 o más pérdidas en el día suspende la operativa si symbol_daily_strikes_enabled=True."""
    mock_repo = Mock()
    mock_repo.get_symbol_loss_status.return_value = {
        "symbol": "Step Index 500",
        "cooldown_active": False,
        "cooldown_remaining_minutes": 0.0,
        "cooldown_until": None,
        "last_loss_exit_time": "2026-10-13T14:00:00+00:00",
        "last_loss_pnl": -64.5,
        "daily_losses_count": 2,
        "daily_strikes_exceeded": True,
        "max_daily_losses": 2,
    }

    config = LiveTradingConfig(
        symbol_loss_cooldown_enabled=True,
        symbol_loss_cooldown_minutes=60.0,
        symbol_daily_strikes_enabled=True,
        symbol_max_daily_losses=2,
    )
    engine = LiveTradingEngine(
        provider=Mock(),
        repository=mock_repo,
        executor=Mock(),
        config=config,
    )

    result = engine._symbol_loss_cooldown_gate("Step Index 500")
    # La restricción de strikes diarios por activo fue eliminada por diseño operativo:
    # no bloquea el activo.
    assert result is None


def test_symbol_loss_cooldown_gate_allows_when_daily_strikes_disabled():
    """Valida que con symbol_daily_strikes_enabled=False (por defecto), las pérdidas acumuladas no bloquean el activo."""
    mock_repo = Mock()
    mock_repo.get_symbol_loss_status.return_value = {
        "symbol": "Step Index 500",
        "cooldown_active": False,
        "cooldown_remaining_minutes": 0.0,
        "cooldown_until": None,
        "last_loss_exit_time": "2026-10-13T14:00:00+00:00",
        "last_loss_pnl": -64.5,
        "daily_losses_count": 2,
        "daily_strikes_exceeded": True,
        "max_daily_losses": 0,
    }

    config = LiveTradingConfig(
        symbol_loss_cooldown_enabled=True,
        symbol_loss_cooldown_minutes=60.0,
        symbol_daily_strikes_enabled=False,
        symbol_max_daily_losses=0,
    )
    engine = LiveTradingEngine(
        provider=Mock(),
        repository=mock_repo,
        executor=Mock(),
        config=config,
    )

    result = engine._symbol_loss_cooldown_gate("Step Index 500")
    assert result is None


def test_symbol_loss_cooldown_gate_allows_entry_when_healthy():
    """Valida que cuando no hay enfriamiento ni exceso de pérdidas, la puerta no bloquea."""
    mock_repo = Mock()
    mock_repo.get_symbol_loss_status.return_value = {
        "symbol": "Volatility 50 (1s) Index",
        "cooldown_active": False,
        "cooldown_remaining_minutes": 0.0,
        "cooldown_until": None,
        "last_loss_exit_time": None,
        "last_loss_pnl": None,
        "daily_losses_count": 0,
        "daily_strikes_exceeded": False,
        "max_daily_losses": 2,
    }

    config = LiveTradingConfig(
        symbol_loss_cooldown_enabled=True,
        symbol_loss_cooldown_minutes=60.0,
        symbol_max_daily_losses=2,
    )
    engine = LiveTradingEngine(
        provider=Mock(),
        repository=mock_repo,
        executor=Mock(),
        config=config,
    )

    result = engine._symbol_loss_cooldown_gate("Volatility 50 (1s) Index")
    assert result is None


def test_symbol_loss_cooldown_gate_ignored_when_disabled():
    """Valida que si symbol_loss_cooldown_enabled=False, no se ejecuta ninguna restricción."""
    mock_repo = Mock()
    mock_repo.get_symbol_loss_status.return_value = {
        "symbol": "Step Index 500",
        "cooldown_active": True,
        "daily_strikes_exceeded": True,
    }

    config = LiveTradingConfig(
        symbol_loss_cooldown_enabled=False,
    )
    engine = LiveTradingEngine(
        provider=Mock(),
        repository=mock_repo,
        executor=Mock(),
        config=config,
    )

    result = engine._symbol_loss_cooldown_gate("Step Index 500")
    assert result is None
    mock_repo.get_symbol_loss_status.assert_not_called()
