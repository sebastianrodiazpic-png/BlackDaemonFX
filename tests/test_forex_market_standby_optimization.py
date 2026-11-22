import os
import unittest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


class TestForexMarketStandbyOptimization(unittest.TestCase):
    """Suite de validación de la optimización de Standby de Mercado Cerrado para Work Forex (1-4)."""

    def setUp(self):
        self.mock_repo = MagicMock()
        self.mock_provider = MagicMock()

    def test_forex_standby_weekend_detection(self):
        """Verifica detección matemática y por zonas horarias del fin de semana Forex."""
        cfg = LiveTradingConfig(bot_profile="FOREX_4", magic=26082204)
        engine = LiveTradingEngine(self.mock_provider, repository=self.mock_repo, config=cfg)

        # 1. Viernes noche: 13 de Noviembre 2026, 23:00 UTC (18:00 NY EST, tras cierre 17:00 NY)
        friday_night = datetime(2026, 11, 13, 23, 0, tzinfo=timezone.utc)
        status_friday = engine._forex_market_standby_status(now_utc=friday_night)
        self.assertTrue(status_friday["in_standby"])
        self.assertTrue(status_friday["is_closed"])
        self.assertIn("Fin de semana Forex", status_friday["reason"])
        self.assertEqual(status_friday["reopen_time_utc"], "2026-11-15T22:00:00+00:00")
        self.assertAlmostEqual(status_friday["seconds_until_reopen"], 169200.0, delta=5.0)

        # 2. Sábado: 14 de Noviembre 2026, 15:00 UTC (10:00 NY EST)
        saturday = datetime(2026, 11, 14, 15, 0, tzinfo=timezone.utc)
        status_sat = engine._forex_market_standby_status(now_utc=saturday)
        self.assertTrue(status_sat["in_standby"])
        self.assertTrue(status_sat["is_closed"])
        self.assertEqual(status_sat["reopen_time_utc"], "2026-11-15T22:00:00+00:00")

        # 3. Domingo antes de apertura: 15 de Noviembre 2026, 21:50 UTC (16:50 NY EST, 10 min antes de 17:00)
        sunday_before_open = datetime(2026, 11, 15, 21, 50, tzinfo=timezone.utc)
        status_sun_early = engine._forex_market_standby_status(now_utc=sunday_before_open)
        self.assertTrue(status_sun_early["in_standby"])
        self.assertTrue(status_sun_early["is_closed"])
        self.assertAlmostEqual(status_sun_early["seconds_until_reopen"], 600.0, delta=2.0)

        # 4. Domingo tras apertura: 15 de Noviembre 2026, 22:05 UTC (17:05 NY EST, mercado reabierto)
        sunday_after_open = datetime(2026, 11, 15, 22, 5, tzinfo=timezone.utc)
        status_sun_open = engine._forex_market_standby_status(now_utc=sunday_after_open)
        self.assertFalse(status_sun_open["in_standby"])
        self.assertFalse(status_sun_open["is_closed"])

        # 5. Martes en plena sesión: 17 de Noviembre 2026, 14:00 UTC
        tuesday = datetime(2026, 11, 17, 14, 0, tzinfo=timezone.utc)
        status_tuesday = engine._forex_market_standby_status(now_utc=tuesday)
        self.assertFalse(status_tuesday["in_standby"])
        self.assertFalse(status_tuesday["is_closed"])

    def test_non_forex_synthetics_never_enter_standby(self):
        """Los índices sintéticos operan 24/7 y jamás deben pausarse por fin de semana."""
        synthetic_profiles = ["SYNTHETICS", "BOOM", "CRASH", "VOLATILITY_1", "STEP", "JUMP"]
        saturday = datetime(2026, 11, 14, 15, 0, tzinfo=timezone.utc)

        for prof in synthetic_profiles:
            cfg = LiveTradingConfig(bot_profile=prof, magic=1001)
            engine = LiveTradingEngine(self.mock_provider, repository=self.mock_repo, config=cfg)
            status = engine._forex_market_standby_status(now_utc=saturday)
            self.assertFalse(
                status["in_standby"],
                f"El perfil sintético {prof} no debe entrar en standby de fin de semana.",
            )

    def test_all_forex_workers_recognized(self):
        """Verifica que todos los workers de Forex (1-5 y SNR) sean cubiertos por la optimización."""
        forex_profiles = ["FOREX", "FOREX_1", "FOREX_2", "FOREX_3", "FOREX_4", "FOREX_5", "FOREX_SNR"]
        saturday = datetime(2026, 11, 14, 15, 0, tzinfo=timezone.utc)

        for prof in forex_profiles:
            cfg = LiveTradingConfig(bot_profile=prof, magic=26082200)
            engine = LiveTradingEngine(self.mock_provider, repository=self.mock_repo, config=cfg)
            status = engine._forex_market_standby_status(now_utc=saturday)
            self.assertTrue(
                status["in_standby"],
                f"El worker {prof} debe entrar en standby durante fin de semana.",
            )

    def test_traditional_indices_and_commodities_workers_recognized(self):
        """Verifica que Índices Bursátiles y Materias Primas entren en standby en fin de semana."""
        traditional_profiles = ["INDICESB_SNR", "ORB", "IDX_OPEN", "COMMODITIES_SNR", "COMMODITIES"]
        saturday = datetime(2026, 11, 14, 15, 0, tzinfo=timezone.utc)

        for prof in traditional_profiles:
            cfg = LiveTradingConfig(bot_profile=prof, magic=26082042)
            engine = LiveTradingEngine(self.mock_provider, repository=self.mock_repo, config=cfg)
            status = engine._forex_market_standby_status(now_utc=saturday)
            self.assertTrue(
                status["in_standby"],
                f"El worker tradicional {prof} debe entrar en standby durante fin de semana.",
            )
            self.assertTrue(status["is_closed"])
            self.assertIn("Fin de semana", status["reason"])

    def test_configurable_kill_switch(self):
        """Si forex_market_standby_enabled está en False, no entra en standby."""
        saturday = datetime(2026, 11, 14, 15, 0, tzinfo=timezone.utc)
        cfg = LiveTradingConfig(bot_profile="FOREX_4", magic=26082204, forex_market_standby_enabled=False)
        engine = LiveTradingEngine(self.mock_provider, repository=self.mock_repo, config=cfg)
        status = engine._forex_market_standby_status(now_utc=saturday)
        self.assertFalse(status["in_standby"])

    def test_standby_updates_worker_runtime_state_and_resumes(self):
        """Valida que en modo standby se actualice el estado del worker a STANDBY_MARKET_CLOSED y se reanude."""
        cfg = LiveTradingConfig(
            bot_profile="FOREX_3",
            magic=26082203,
            forex_market_standby_enabled=True,
            forex_market_standby_poll_seconds=1.0,
            background_position_monitor_enabled=False,
        )
        engine = LiveTradingEngine(self.mock_provider, repository=self.mock_repo, config=cfg)

        # Simular sábado sin posiciones abiertas
        saturday = datetime(2026, 11, 14, 12, 0, tzinfo=timezone.utc)
        self.mock_repo.open_trades.return_value = []

        with patch.object(engine, "_forex_market_standby_status") as mock_status:
            mock_status.return_value = {
                "in_standby": True,
                "is_closed": True,
                "reason": "Fin de semana Forex",
                "reopen_time_utc": "2026-11-15T22:00:00+00:00",
                "reopen_display": "Sunday 2026-11-15 22:00 UTC",
                "seconds_until_reopen": 1000.0,
            }

            # Ejecutar 1 ciclo determinista en modo test
            engine.run_daemon(symbols=["EURUSD"], max_cycles=1)

            # Verificar que se actualizó el estado a STANDBY_MARKET_CLOSED
            self.mock_repo.upsert_worker_runtime_state.assert_called()
            call_kwargs = self.mock_repo.upsert_worker_runtime_state.call_args[1]
            self.assertEqual(call_kwargs.get("status"), "STANDBY_MARKET_CLOSED")
            self.assertIn("Mercado cerrado", call_kwargs.get("last_reason"))


if __name__ == "__main__":
    unittest.main()
