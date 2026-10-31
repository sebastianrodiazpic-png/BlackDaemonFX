import os
import unittest
from dashboard.realtime_dashboard import (
    _is_retired_worker_profile,
    _RETIRED_WORKER_PROFILES,
    _INSTRUMENTS_HTML,
)


class TestDashboardCleanupRetiredWorkers(unittest.TestCase):
    def test_retired_profiles_detection(self):
        """Verifica que los workers retirados sean identificados correctamente."""
        retired_targets = [
            "CARRY",
            "DRIFT",
            "GOLD",
            "GOLD_QUARTERS",
            "MSNR",
            "NIGHT",
            "RSI2",
            "FLIP",
            "IDX_OPEN",
            "SCALP_M1",
        ]
        for p in retired_targets:
            self.assertTrue(
                _is_retired_worker_profile(p),
                f"El perfil {p} debió ser detectado como retirado"
            )

    def test_active_profiles_not_retired(self):
        """Verifica que los workers operativos vigentes NO sean marcados como retirados."""
        active_profiles = [
            "BOOM",
            "CRASH",
            "STEP",
            "JUMP",
            "VOLATILITY",
            "VOLATILITY_1",
            "FOREX_1",
            "ICT",
            "MALAYSIAN_SNR",
            "ORB",
            "TREND_PULLBACK",
        ]
        for p in active_profiles:
            self.assertFalse(
                _is_retired_worker_profile(p),
                f"El perfil activo {p} NO debe ser marcado como retirado"
            )

    def test_retired_worker_profiles_set(self):
        """Verifica que el conjunto de perfiles retirados contenga las 6 familias pedidas."""
        expected = {"CARRY", "DRIFT", "GOLD", "MSNR", "NIGHT", "RSI2"}
        self.assertTrue(expected.issubset(_RETIRED_WORKER_PROFILES))

    def test_configurable_switch(self):
        """Verifica que el filtro sea configurable mediante variable de entorno."""
        os.environ["DAEMONBLACKFX_RETIRED_WORKERS_FILTER"] = "0"
        try:
            self.assertFalse(_is_retired_worker_profile("CARRY"))
        finally:
            os.environ["DAEMONBLACKFX_RETIRED_WORKERS_FILTER"] = "1"
            self.assertTrue(_is_retired_worker_profile("CARRY"))

    def test_confluence_matrix_filter_clean(self):
        """Verifica que la plantilla del dashboard no contenga el botón GOLD QUARTERS."""
        with open("dashboard/realtime_dashboard.py", "r", encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn('data-filter="GOLD_QUARTERS"', content)
        self.assertNotIn('Oro Cuartos (XAUUSD)', content)


if __name__ == "__main__":
    unittest.main()
