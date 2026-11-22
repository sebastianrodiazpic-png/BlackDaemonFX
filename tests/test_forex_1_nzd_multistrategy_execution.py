"""
tests/test_forex_1_nzd_multistrategy_execution.py
=================================================
Validación de la integración y ejecución MultiStrategia del Worker FOREX (1)
Magic 26082201 · PID 10776 para los 6 instrumentos de divisas NZD:
NZDCAD, NZDUSD, NZDUSDmicro, NZDCHF, NZDJPY y NZDSGD.
"""

import unittest
import csv
from pathlib import Path
from app.main import BOT_PROFILES
from config.strategy_config import PRUNED_ASSET_UNIVERSE
from config.ict_instrument_policy import (
    resolve_active_pruned_worker_universe,
    ICT_FOREX_ACTIVE_BASES,
    FOREX_SNR_ACTIVE,
)
from strategy.execution.worker_rules import configure_worker_rules
from strategy.execution.live_trading_engine import LiveTradingConfig
from dashboard.strategy_bases_page import STRATEGY_BASES_HTML
from dashboard.decisions_page import DECISIONS_HTML


class TestForex1NzdMultistrategyExecution(unittest.TestCase):
    """Test unitario para la implementación de Worker FOREX (1) MultiStrategia en Pares NZD."""

    EXPECTED_NZD_SYMBOLS = [
        "NZDCAD",
        "NZDUSD", "NZDUSDmicro",
        "NZDCHF",
        "NZDJPY",
        "NZDSGD",
    ]

    def test_forex_1_in_bot_profiles(self):
        """Verifica que FOREX_1 exista en BOT_PROFILES con Magic 26082201 y sus 6 instrumentos."""
        self.assertIn("FOREX_1", BOT_PROFILES)
        spec = BOT_PROFILES["FOREX_1"]
        self.assertEqual(spec["magic"], 26082201)
        self.assertEqual(spec["mode"], "forex-1-daemon")
        self.assertEqual(spec["categories"], ["forex"])
        self.assertEqual(sorted(spec["symbols"]), sorted(self.EXPECTED_NZD_SYMBOLS))

    def test_forex_1_in_pruned_asset_universe(self):
        """Verifica que PRUNED_ASSET_UNIVERSE contenga a FOREX_1 con sus 6 instrumentos."""
        self.assertIn("FOREX_1", PRUNED_ASSET_UNIVERSE)
        self.assertEqual(sorted(PRUNED_ASSET_UNIVERSE["FOREX_1"]), sorted(self.EXPECTED_NZD_SYMBOLS))

    def test_forex_1_universe_resolution_and_active_policy(self):
        """Valida que resolve_active_pruned_worker_universe('FOREX_1') retorne los 6 pares NZD."""
        resolved = resolve_active_pruned_worker_universe("FOREX_1")
        self.assertEqual(sorted(resolved), sorted(self.EXPECTED_NZD_SYMBOLS))

        for sym in ["NZDCAD", "NZDCHF", "NZDJPY", "NZDSGD"]:
            self.assertIn(sym, ICT_FOREX_ACTIVE_BASES)
            self.assertIn(sym, FOREX_SNR_ACTIVE)

    def test_forex_1_multistrategy_worker_rules(self):
        """Valida que configure_worker_rules aplique MultiStrategia M5 y contrato institucional 1.0R/2.0R."""
        cfg = LiveTradingConfig(bot_profile="FOREX_1", magic=26082201)
        opt_cfg = configure_worker_rules(cfg)

        self.assertEqual(opt_cfg.entry_timeframe, "M5")
        self.assertTrue(opt_cfg.dual_m5_m1_trigger_enabled)
        self.assertTrue(opt_cfg.malaysian_snr_enabled)
        self.assertEqual(opt_cfg.first_target_rr, 1.0)
        self.assertEqual(opt_cfg.second_target_rr, 2.0)
        self.assertTrue(opt_cfg.break_even_enabled)
        self.assertEqual(opt_cfg.break_even_trigger_rr, 1.0)
        self.assertTrue(opt_cfg.forex_rollover_guard_enabled)
        self.assertTrue(opt_cfg.forex_force_flat_friday)
        self.assertFalse(opt_cfg.forex_killzone_only_enabled)

    def test_forex_1_strategy_bases_and_decisions_sync(self):
        """Valida que strategy_bases_page, decisions_page y el CSV de bases contengan los 6 pares NZD."""
        for sym in self.EXPECTED_NZD_SYMBOLS:
            self.assertIn(f'"{sym}"', STRATEGY_BASES_HTML)

        self.assertIn("FOREX (1)", DECISIONS_HTML)
        self.assertIn("26082201", DECISIONS_HTML)
        self.assertIn("10776", DECISIONS_HTML)

        csv_path = Path("storage/analysis/replay_5y_perfect_strategy_bases.csv")
        self.assertTrue(csv_path.exists())

        found_in_csv = set()
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                s = row.get("symbol")
                if s in self.EXPECTED_NZD_SYMBOLS and "MultiStrategia" in row.get("strategy", ""):
                    found_in_csv.add(s)

        self.assertEqual(found_in_csv, set(self.EXPECTED_NZD_SYMBOLS))


if __name__ == "__main__":
    unittest.main()
