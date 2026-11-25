import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timezone
import os
import time

from strategy.execution.live_trading_engine import (
    LiveTradingEngine,
    LiveTradingConfig,
)


class TestPerformanceOptimizationsFase1(unittest.TestCase):
    """Pruebas unitarias de las optimizaciones de rendimiento informático Fase 1:
    1. Preflight Zero-I/O Fast Exit en compuertas determinísticas en memoria.
    2. Deduplicación y throttle adaptativo de eventos de auditoría en compuertas horarias/gates.
    """

    def setUp(self):
        self.config = LiveTradingConfig(
            london_ny_crossover_filter_enabled=True,
            london_ny_crossover_start_utc_hour=13,
            london_ny_crossover_end_utc_hour=15,
            london_ny_crossover_apply_to_synthetics=False,
            bot_profile="FOREX_1",
            source="DEMO",
            magic=26082101,
        )
        self.engine = object.__new__(LiveTradingEngine)
        self.engine.config = self.config
        self.engine.provider = MagicMock()
        self.engine.provider.resolve_symbol = lambda s: str(s)
        self.engine.repository = MagicMock()
        self.engine.repository.get_symbol_loss_status.return_value = {"cooldown_active": False}
        self.engine._is_synthetic_symbol = lambda s: False
        self.engine._is_market_closing_symbol = lambda s: True
        self.engine._gate_audit_cache = {}

    def test_preflight_crossover_blocks_before_calling_mt5_ipc(self):
        """Verifica que el centinela Londres/NY bloquee el símbolo antes de ensure_symbol o pedir ticks."""
        t_blocked = datetime(2026, 11, 23, 13, 30, tzinfo=timezone.utc)

        # Mockear puertas previas para que pasen
        self.engine._active_position_gate = MagicMock(return_value=None)
        self.engine._gold_smc_entry_gate = MagicMock(return_value=None)
        self.engine._forex_killzone_entry_gate = MagicMock(return_value=None)
        self.engine._forex_rollover_entry_gate = MagicMock(return_value=None)
        self.engine._crypto_rollover_entry_gate = MagicMock(return_value=None)
        self.engine._forex_high_impact_news_entry_gate = MagicMock(return_value=None)

        # Mockear las llamadas que representan I/O o IPC a MT5
        self.engine._ict_spread_lock_gate = MagicMock()
        self.engine._market_regime_entry_gate = MagicMock()
        self.engine.provider.ensure_symbol = MagicMock()

        with patch("strategy.execution.live_trading_engine.datetime") as mock_dt:
            mock_dt.now.return_value = t_blocked
            res = self.engine._process_symbol_guarded("EURUSD", sync_before_execution=False)

        # Debe devolver bloqueo de cruce
        self.assertIsNotNone(res)
        self.assertEqual(res.get("action"), "LONDON_NY_CROSSOVER_FILTER_BLOCKED")

        # CERO llamadas a MT5 IPC (ensure_symbol, spread_lock, market_regime)
        self.engine.provider.ensure_symbol.assert_not_called()
        self.engine._ict_spread_lock_gate.assert_not_called()
        self.engine._market_regime_entry_gate.assert_not_called()

    def test_preflight_cooldown_blocks_before_calling_mt5_ipc(self):
        """Verifica que el cooldown de racha bloquee el símbolo antes de ensure_symbol."""
        # Configurar para que crossover gate no bloquee
        t_allowed = datetime(2026, 11, 23, 10, 0, tzinfo=timezone.utc)

        self.engine._active_position_gate = MagicMock(return_value=None)
        self.engine._gold_smc_entry_gate = MagicMock(return_value=None)
        self.engine._forex_killzone_entry_gate = MagicMock(return_value=None)
        self.engine._forex_rollover_entry_gate = MagicMock(return_value=None)
        self.engine._crypto_rollover_entry_gate = MagicMock(return_value=None)
        self.engine._forex_high_impact_news_entry_gate = MagicMock(return_value=None)
        self.engine._london_ny_crossover_sentinel_gate = MagicMock(return_value=None)

        # Cooldown gate activo
        self.engine._symbol_loss_cooldown_gate = MagicMock(return_value={
            "symbol": "EURUSD",
            "action": "SYMBOL_LOSS_COOLDOWN_ACTIVE",
            "reason": "LOSS_STREAK_COOLDOWN",
        })

        self.engine.provider.ensure_symbol = MagicMock()
        self.engine._ict_spread_lock_gate = MagicMock()
        self.engine._market_regime_entry_gate = MagicMock()

        res = self.engine._process_symbol_guarded("EURUSD", sync_before_execution=False)

        self.assertIsNotNone(res)
        self.assertEqual(res.get("action"), "SYMBOL_LOSS_COOLDOWN_ACTIVE")
        self.engine.provider.ensure_symbol.assert_not_called()
        self.engine._ict_spread_lock_gate.assert_not_called()
        self.engine._market_regime_entry_gate.assert_not_called()

    def test_gate_audit_throttle_suppresses_repeated_events(self):
        """Verifica que llamadas repetidas a compuertas (_GATE) dentro de la ventana de throttle sean suprimidas."""
        # Primera llamada: debe persistir en el repositorio
        res1 = self.engine._persist_audit_event(
            "LONDON_NY_CROSSOVER_GATE",
            instrument="EURUSD",
            action="FILTER_BLOCKED",
            reason="LONDON_NY_CROSSOVER_HIGH_VOLATILITY_WINDOW_13:00_UTC",
        )
        self.engine.repository.save_audit_event.assert_called_once()

        # Segunda llamada inmediata: debe ser throttled (sin llamar a save_audit_event de nuevo)
        self.engine.repository.save_audit_event.reset_mock()
        res2 = self.engine._persist_audit_event(
            "LONDON_NY_CROSSOVER_GATE",
            instrument="EURUSD",
            action="FILTER_BLOCKED",
            reason="LONDON_NY_CROSSOVER_HIGH_VOLATILITY_WINDOW_13:00_UTC",
        )
        self.assertIsNotNone(res2)
        self.assertTrue(res2.get("gate_throttled"))
        self.assertTrue(res2.get("sampled_out"))
        self.engine.repository.save_audit_event.assert_not_called()

    def test_gate_audit_throttle_disabled_when_set_to_zero(self):
        """Verifica que si DAEMONBLACKFX_AUDIT_GATE_THROTTLE_SECONDS=0, no haya supresión."""
        with patch.dict(os.environ, {"DAEMONBLACKFX_AUDIT_GATE_THROTTLE_SECONDS": "0"}):
            self.engine._gate_audit_cache.clear()
            self.engine._persist_audit_event(
                "LONDON_NY_CROSSOVER_GATE",
                instrument="EURUSD",
                action="FILTER_BLOCKED",
                reason="WINDOW_13:00_UTC",
            )
            self.assertEqual(self.engine.repository.save_audit_event.call_count, 1)

            self.engine._persist_audit_event(
                "LONDON_NY_CROSSOVER_GATE",
                instrument="EURUSD",
                action="FILTER_BLOCKED",
                reason="WINDOW_13:00_UTC",
            )
            self.assertEqual(self.engine.repository.save_audit_event.call_count, 2)


if __name__ == "__main__":
    unittest.main()
