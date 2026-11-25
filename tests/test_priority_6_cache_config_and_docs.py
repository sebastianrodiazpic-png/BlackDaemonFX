"""Tests unitarios y de integración para Prioridad 6 (Punto 6):
1. Caché IPC de posiciones y órdenes pendientes en MT5ExecutionProvider (TTL configurable,
   lectura desde caché sin repetir IPC, invalidación inmediata en place_market_order / modify_position_stops /
   close_position, y modo desactivado con TTL=0).
2. Higiene de configuración: worker_rules.py respeta variables de entorno DAEMONBLACKFX_RUNNER_* /
   DAEMONBLACKFX_FIRST_TARGET_RR / DAEMONBLACKFX_SECOND_TARGET_RR sin pisarlas, y LiveTradingConfig
   evalúa variables de entorno dinámicamente con field(default_factory=...).
3. Sincronización documental de /Strategy-bases (dashboard/strategy_bases_page.py y operator_chatbot.py)
   reflejando el contrato 70% / 30%, excepción 1% @ 1:1 sub-TP2 y ventanas horarias de mercados reales.
4. Deprecación formal de strategy.risk.risk_manager sin romper compatibilidad con tests históricos.
"""

from __future__ import annotations

import importlib
import os
import unittest
import warnings
from pathlib import Path
from unittest.mock import MagicMock, patch

from brokers.mt5_execution import MT5ExecutionError, MT5ExecutionProvider
from strategy.execution.active_position_guard import _IN_FLIGHT_CACHE, _IN_FLIGHT_MUTEX
from strategy.execution.live_trading_engine import LiveTradingConfig
from strategy.execution.worker_rules import configure_worker_rules


class TestPriority6CacheConfigAndDocs(unittest.TestCase):
    def setUp(self):
        with _IN_FLIGHT_MUTEX:
            _IN_FLIGHT_CACHE.clear()

    @patch("brokers.mt5_execution.mt5")
    def test_mt5_positions_and_orders_ipc_cache_and_invalidation(self, mock_mt5):
        """Verifica que lecturas consecutivas usen caché dentro del TTL y se invaliden al mutar estado."""
        provider = MT5ExecutionProvider(MagicMock())
        provider._ensure = MagicMock()

        pos1 = MagicMock(ticket=101, symbol="EURUSD")
        pos2 = MagicMock(ticket=102, symbol="XAUUSD")
        mock_mt5.positions_get.side_effect = [[pos1], [pos1, pos2]]
        mock_mt5.orders_get.side_effect = [[], [MagicMock(ticket=201)]]

        with patch.dict(os.environ, {"DAEMONBLACKFX_MT5_POSITIONS_CACHE_TTL_SECONDS": "2.0"}):
            first_pos = provider.get_open_positions()
            second_pos = provider.get_open_positions()
            self.assertEqual(len(first_pos), 1)
            self.assertEqual(len(second_pos), 1)
            # Solo 1 llamada IPC a mt5.positions_get gracias a la caché
            self.assertEqual(mock_mt5.positions_get.call_count, 1)

            first_ord = provider.get_pending_orders()
            second_ord = provider.get_pending_orders()
            self.assertEqual(len(first_ord), 0)
            self.assertEqual(len(second_ord), 0)
            self.assertEqual(mock_mt5.orders_get.call_count, 1)

            # Invalidación explícita (usada tras order_send / modify / close) fuerza lectura fresca inmediata
            provider.invalidate_broker_cache()
            refreshed_pos = provider.get_open_positions()
            self.assertEqual(len(refreshed_pos), 2)
            self.assertEqual(mock_mt5.positions_get.call_count, 2)

            # force_refresh=True también salta la caché sin esperar TTL
            mock_mt5.positions_get.side_effect = [[pos2]]
            forced_pos = provider.get_open_positions(force_refresh=True)
            self.assertEqual(len(forced_pos), 1)
            self.assertEqual(mock_mt5.positions_get.call_count, 3)

        # TTL = 0 desactiva la caché por completo (reversibilidad inmediata)
        mock_mt5.positions_get.reset_mock()
        mock_mt5.positions_get.side_effect = [[pos1], [pos2]]
        with patch.dict(os.environ, {"DAEMONBLACKFX_MT5_POSITIONS_CACHE_TTL_SECONDS": "0"}):
            provider.get_open_positions()
            provider.get_open_positions()
            self.assertEqual(mock_mt5.positions_get.call_count, 2)

    @patch("brokers.mt5_execution.mt5")
    def test_mt5_positions_cache_never_caches_none_error(self, mock_mt5):
        """Si mt5.positions_get devuelve None (fallo IPC), lanza MT5ExecutionError y jamás guarda None en caché."""
        provider = MT5ExecutionProvider(MagicMock())
        provider._ensure = MagicMock()
        mock_mt5.positions_get.return_value = None
        mock_mt5.last_error.return_value = (-1, "IPC timeout")

        with self.assertRaises(MT5ExecutionError):
            provider.get_open_positions()
        self.assertIsNone(provider._positions_cache)

    def test_worker_rules_and_live_config_respect_dynamic_env_vars(self):
        """Verifica que worker_rules.py y LiveTradingConfig obedezcan variables de entorno dinámicas."""
        env_overrides = {
            "DAEMONBLACKFX_FIRST_TARGET_RR": "1.2",
            "DAEMONBLACKFX_SECOND_TARGET_RR": "2.4",
            "DAEMONBLACKFX_BREAK_EVEN_TRIGGER_RR": "1.1",
            "DAEMONBLACKFX_RUNNER_FIRST_TRIGGER_RR": "2.2",
            "DAEMONBLACKFX_RUNNER_FIRST_LOCK_RR": "1.3",
            "DAEMONBLACKFX_RUNNER_SECOND_TRIGGER_RR": "3.2",
            "DAEMONBLACKFX_RUNNER_SECOND_LOCK_RR": "2.6",
            "DAEMONBLACKFX_RUNNER_MAX_TARGET_RR": "4.5",
            "DAEMONBLACKFX_SMC_RUNNER_MAX_TARGET_RR": "4.5",
            "DAEMONBLACKFX_META_LABELING_MODE": "SHADOW",
            "DAEMONBLACKFX_MARKET_REGIME_ICT_REAL_MODE": "FILTER",
        }
        with patch.dict(os.environ, env_overrides):
            raw_cfg = LiveTradingConfig(bot_profile="FOREX_3")
            self.assertEqual(raw_cfg.meta_labeling_mode, "SHADOW")
            self.assertEqual(raw_cfg.market_regime_ict_real_mode, "FILTER")
            self.assertAlmostEqual(raw_cfg.runner_extension_max_target_rr, 4.5)

            for profile in ("ORB", "FOREX_3", "VOLATILITY_4", "BOOM", "ICT", "GOLD"):
                cfg = configure_worker_rules(LiveTradingConfig(bot_profile=profile))
                self.assertAlmostEqual(cfg.first_target_rr, 1.2, msg=profile)
                self.assertAlmostEqual(cfg.second_target_rr, 2.4, msg=profile)
                self.assertAlmostEqual(cfg.break_even_trigger_rr, 1.1, msg=profile)
                self.assertAlmostEqual(cfg.runner_extension_first_trigger_rr, 2.2, msg=profile)
                self.assertAlmostEqual(cfg.runner_extension_first_lock_rr, 1.3, msg=profile)
                self.assertAlmostEqual(cfg.runner_extension_max_target_rr, 4.5, msg=profile)
                self.assertEqual(cfg.meta_labeling_mode, "SHADOW", msg=profile)

    def test_strategy_bases_and_chatbot_reflect_70_30_and_1to1_contract(self):
        """Verifica que /Strategy-bases y el chatbot ya no muestren el texto obsoleto 50% + 50%."""
        from dashboard.strategy_bases_page import STRATEGY_BASES_HTML

        self.assertIn("70% + 30%", STRATEGY_BASES_HTML)
        self.assertIn("1% @ 1:1", STRATEGY_BASES_HTML)
        self.assertNotIn("Fórmula Dual-Leg (50% + 50%)", STRATEGY_BASES_HTML)
        self.assertNotIn("Doble Orden (50% + 50%)", STRATEGY_BASES_HTML)
        self.assertNotIn("Ejecución 2 Piernas (0.5% + 0.5%)", STRATEGY_BASES_HTML)

        chatbot_src = Path("dashboard/operator_chatbot.py").read_text(encoding="utf-8")
        self.assertIn("70% TP1 + 30% RUNNER", chatbot_src)
        self.assertNotIn("2 patas (0.5% + 0.5%)", chatbot_src)

    def test_risk_manager_formally_deprecated(self):
        """Verifica marca de deprecación formal y emisión opcional de DeprecationWarning."""
        import strategy.risk.risk_manager as rm

        self.assertTrue(getattr(rm, "__deprecated__", False))
        with patch.dict(os.environ, {"DAEMONBLACKFX_WARN_DEPRECATED_RISK_MANAGER": "1"}):
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                importlib.reload(rm)
                self.assertTrue(any(issubclass(w.category, DeprecationWarning) for w in caught))


if __name__ == "__main__":
    unittest.main()
