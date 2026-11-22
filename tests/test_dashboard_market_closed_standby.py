import unittest
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

from dashboard.realtime_dashboard import (
    _is_traditional_market_closed,
    RealtimeDashboardService,
)


class TestDashboardMarketClosedStandby(unittest.TestCase):
    """Valida el enriquecimiento y visualización de workers tradicionales en modo reposo por mercado inoperativo."""

    def test_is_traditional_market_closed_schedule(self):
        # Sábado: 14 de Noviembre 2026, 15:00 UTC (mercado tradicional cerrado)
        sat = datetime(2026, 11, 14, 15, 0, tzinfo=timezone.utc)
        is_closed, reason = _is_traditional_market_closed(now_utc=sat)
        self.assertTrue(is_closed)
        self.assertIn("Mercado cerrado", reason)

        # Domingo antes de 17:00 NY: 15 de Noviembre 2026, 21:00 UTC (16:00 NY)
        sun_before = datetime(2026, 11, 15, 21, 0, tzinfo=timezone.utc)
        is_closed, _ = _is_traditional_market_closed(now_utc=sun_before)
        self.assertTrue(is_closed)

        # Domingo tras 17:00 NY: 15 de Noviembre 2026, 22:30 UTC (17:30 NY)
        sun_after = datetime(2026, 11, 15, 22, 30, tzinfo=timezone.utc)
        is_closed, _ = _is_traditional_market_closed(now_utc=sun_after)
        self.assertFalse(is_closed)

        # Martes sesión regular: 17 de Noviembre 2026, 14:00 UTC
        tue = datetime(2026, 11, 17, 14, 0, tzinfo=timezone.utc)
        is_closed, _ = _is_traditional_market_closed(now_utc=tue)
        self.assertFalse(is_closed)

    def test_dashboard_enriches_traditional_workers_during_weekend(self):
        """Durante el fin de semana, Forex 1, 3, 4, 5, Índices y ORB entran en STANDBY_MARKET_CLOSED y FOREX_2 en DISABLED."""
        mock_repo = MagicMock()
        mock_repo.worker_runtime_states.return_value = []
        mock_repo.get_selection_profiles.return_value = {}

        dash = RealtimeDashboardService(repository=mock_repo)

        with patch("dashboard.realtime_dashboard._is_traditional_market_closed") as mock_closed:
            mock_closed.return_value = (True, "Mercado cerrado (Fin de semana) · reposo automático")

            data = dash._cached_instruments_payload(force=True)
            workers = {w.get("bot_profile"): w for w in data.get("worker_states", [])}

            # Validar que Forex 2 está DISABLED
            self.assertIn("FOREX_2", workers)
            self.assertEqual(workers["FOREX_2"].get("status"), "DISABLED")
            self.assertEqual(workers["FOREX_2"].get("last_action"), "STANDBY_MARKET_CLOSED")

            # Validar que Forex 1, 3, 4, 5 están en STANDBY_MARKET_CLOSED
            for wp in ("FOREX_1", "FOREX_3", "FOREX_4", "FOREX_5"):
                self.assertIn(wp, workers)
                self.assertEqual(
                    workers[wp].get("status"),
                    "STANDBY_MARKET_CLOSED",
                    f"{wp} debe estar en STANDBY_MARKET_CLOSED durante fin de semana",
                )
                self.assertIn("reposo", str(workers[wp].get("last_reason")).lower())

            # Validar que Índices Bursátiles y ORB están en STANDBY_MARKET_CLOSED
            for wp in ("INDICESB_SNR", "ORB"):
                self.assertIn(wp, workers)
                self.assertEqual(
                    workers[wp].get("status"),
                    "STANDBY_MARKET_CLOSED",
                    f"{wp} debe estar en STANDBY_MARKET_CLOSED durante fin de semana",
                )

            # Validar que los sintéticos (24/7) NO están en STANDBY_MARKET_CLOSED
            for wp in ("CRASH", "BOOM", "STEP", "JUMP", "VOLATILITY_1"):
                self.assertIn(wp, workers)
                self.assertNotEqual(
                    workers[wp].get("status"),
                    "STANDBY_MARKET_CLOSED",
                    f"{wp} es sintético y jamás debe pausarse",
                )


if __name__ == "__main__":
    unittest.main()
