"""
tests/test_commodities_crypto_multistrategy_execution.py
========================================================
Validación de la integración y ejecución MultiStrategia del Worker Materias Primas y Criptomonedas
Magic 26082032 · PID 17144 para los 13 instrumentos:
BTCUSD, ETHUSD, BTCUSDmicro, ETHUSDmicro, XRPUSD, XAUEUR, XAUUSD, XAUUSDmicro,
XAUEURmicro, XAGUSD, XAGUSDmicro, US Oil y UK Brent Oil.
"""

import unittest
import csv
import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import BOT_PROFILES
from config.strategy_config import PRUNED_ASSET_UNIVERSE
from config.ict_instrument_policy import (
    resolve_active_pruned_worker_universe,
    ICT_MARKETS_ACTIVE,
    COMMODITIES_SNR_ACTIVE,
    is_ict_active,
)
from strategy.execution.worker_rules import configure_worker_rules
from strategy.execution.live_trading_engine import LiveTradingConfig
from dashboard.strategy_bases_page import STRATEGY_BASES_HTML
from dashboard.decisions_page import DECISIONS_HTML
from dashboard.realtime_dashboard import _WORKER_PROFILE_META


class TestCommoditiesCryptoMultistrategyExecution(unittest.TestCase):
    """Test unitario para la implementación de Worker Materias Primas y Criptomonedas MultiStrategia."""

    EXPECTED_COMMODITIES_CRYPTO_SYMBOLS = [
        "BTCUSD", "ETHUSD",
        "BTCUSDmicro", "ETHUSDmicro",
        "XRPUSD",
        "XAUEUR", "XAUUSD",
        "XAUUSDmicro", "XAUEURmicro",
        "XAGUSD", "XAGUSDmicro",
        "US Oil", "UK Brent Oil",
    ]

    def test_ict_in_bot_profiles(self):
        """Verifica que ICT exista en BOT_PROFILES con Magic 26082032 y sus 13 instrumentos."""
        self.assertIn("ICT", BOT_PROFILES)
        spec = BOT_PROFILES["ICT"]
        self.assertEqual(spec["magic"], 26082032)
        self.assertEqual(spec["mode"], "ict-daemon")
        self.assertEqual(sorted(spec["symbols"]), sorted(self.EXPECTED_COMMODITIES_CRYPTO_SYMBOLS))

    def test_ict_in_pruned_asset_universe(self):
        """Verifica que PRUNED_ASSET_UNIVERSE contenga a ICT con sus 13 instrumentos."""
        self.assertIn("ICT", PRUNED_ASSET_UNIVERSE)
        self.assertEqual(sorted(PRUNED_ASSET_UNIVERSE["ICT"]), sorted(self.EXPECTED_COMMODITIES_CRYPTO_SYMBOLS))

    def test_ict_universe_resolution_and_active_policy(self):
        """Valida que resolve_active_pruned_worker_universe('ICT') retorne los 13 instrumentos."""
        resolved = resolve_active_pruned_worker_universe("ICT")
        self.assertEqual(sorted(resolved), sorted(self.EXPECTED_COMMODITIES_CRYPTO_SYMBOLS))

        for sym in self.EXPECTED_COMMODITIES_CRYPTO_SYMBOLS:
            self.assertTrue(is_ict_active(sym, "ICT"), f"{sym} should be active in ICT profile")

    def test_ict_multistrategy_worker_rules(self):
        """Valida que configure_worker_rules aplique MultiStrategia M5 y contrato institucional 1.0R/2.0R."""
        cfg = LiveTradingConfig(bot_profile="ICT", magic=26082032)
        opt_cfg = configure_worker_rules(cfg)

        self.assertEqual(opt_cfg.entry_timeframe, "M5")
        self.assertTrue(opt_cfg.dual_m5_m1_trigger_enabled)
        self.assertTrue(opt_cfg.malaysian_snr_enabled)
        self.assertEqual(opt_cfg.first_target_rr, 1.0)
        self.assertEqual(opt_cfg.second_target_rr, 2.0)
        self.assertTrue(opt_cfg.break_even_enabled)
        self.assertEqual(opt_cfg.break_even_trigger_rr, 1.0)
        self.assertTrue(opt_cfg.runner_extension_enabled)
        self.assertTrue(opt_cfg.crypto_rollover_guard_enabled)

    def test_ict_dashboard_metadata_and_strategy_catalog(self):
        """Valida que el dashboard catalogue el worker como MultiStrategia y nombre Materias Primas y Criptomonedas."""
        meta = _WORKER_PROFILE_META.get("ICT")
        self.assertIsNotNone(meta)
        self.assertEqual(meta.get("strategy_key"), "MULTISTRATEGY")
        self.assertEqual(meta.get("strategy_label"), "MultiStrategia")
        self.assertEqual(meta.get("magic"), 26082032)
        self.assertIn("Materias Primas y Criptomonedas", meta.get("label", ""))
        self.assertIn("PID 17144", meta.get("label", ""))

    def test_ict_strategy_bases_and_decisions_sync(self):
        """Valida que strategy_bases_page, decisions_page y el CSV de bases contengan los 13 instrumentos."""
        for sym in self.EXPECTED_COMMODITIES_CRYPTO_SYMBOLS:
            self.assertIn(f'"{sym}"', STRATEGY_BASES_HTML)

        self.assertIn("Materias Primas y Criptomonedas", DECISIONS_HTML)
        self.assertIn("26082032", DECISIONS_HTML)
        self.assertIn("17144", DECISIONS_HTML)

        csv_path = Path("storage/analysis/replay_5y_perfect_strategy_bases.csv")
        self.assertTrue(csv_path.exists())

        found_in_csv = set()
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                s = row.get("symbol")
                if s in self.EXPECTED_COMMODITIES_CRYPTO_SYMBOLS and "MultiStrategia" in row.get("strategy", ""):
                    found_in_csv.add(s)

        self.assertEqual(found_in_csv, set(self.EXPECTED_COMMODITIES_CRYPTO_SYMBOLS))


if __name__ == "__main__":
    unittest.main()
