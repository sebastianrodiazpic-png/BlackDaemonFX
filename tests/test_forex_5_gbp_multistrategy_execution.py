import unittest
from app.main import BOT_PROFILES
from config.strategy_config import PRUNED_ASSET_UNIVERSE
from config.ict_instrument_policy import resolve_active_pruned_worker_universe
from strategy.execution.worker_rules import configure_worker_rules
from strategy.execution.live_trading_engine import LiveTradingConfig


class TestForex5GbpMultistrategyExecution(unittest.TestCase):
    """Test unitario para la implementación de Worker FOREX (5) MultiStrategia en Pares GBP."""

    EXPECTED_GBP_SYMBOLS = [
        "GBPAUD", "GBPCAD",
        "GBPCHF", "GBPCHFmicro",
        "GBPJPY", "GBPJPYmicro",
        "GBPNZD",
        "GBPUSD", "GBPUSDmicro",
        "GBPNOK", "GBPSEK", "GBPSGD"
    ]

    def test_forex_5_in_bot_profiles(self):
        """Verifica que FOREX_5 exista en BOT_PROFILES con Magic 26082205 y sus 12 instrumentos."""
        self.assertIn("FOREX_5", BOT_PROFILES)
        spec = BOT_PROFILES["FOREX_5"]
        self.assertEqual(spec["magic"], 26082205)
        self.assertEqual(spec["mode"], "forex-5-daemon")
        self.assertEqual(spec["categories"], ["forex"])
        self.assertEqual(sorted(spec["symbols"]), sorted(self.EXPECTED_GBP_SYMBOLS))

    def test_forex_5_in_pruned_asset_universe(self):
        """Verifica que PRUNED_ASSET_UNIVERSE contenga exactamente los 12 instrumentos GBP."""
        self.assertIn("FOREX_5", PRUNED_ASSET_UNIVERSE)
        symbols = PRUNED_ASSET_UNIVERSE["FOREX_5"]
        self.assertEqual(sorted(symbols), sorted(self.EXPECTED_GBP_SYMBOLS))

    def test_resolve_active_pruned_worker_universe(self):
        """Verifica la resolución aislada del universo para FOREX_5."""
        resolved = resolve_active_pruned_worker_universe("FOREX_5")
        self.assertEqual(sorted(resolved), sorted(self.EXPECTED_GBP_SYMBOLS))

    def test_worker_rules_configuration(self):
        """Verifica que configure_worker_rules configure MultiStrategia en M5 con contrato de 2 patas."""
        cfg = LiveTradingConfig(bot_profile="FOREX_5", magic=26082205)
        updated_cfg = configure_worker_rules(cfg)
        self.assertTrue(updated_cfg.malaysian_snr_enabled)
        self.assertEqual(updated_cfg.entry_timeframe, "M5")
        self.assertEqual(updated_cfg.first_target_rr, 1.0)
        self.assertEqual(updated_cfg.second_target_rr, 2.0)
        self.assertTrue(updated_cfg.break_even_enabled)
        self.assertEqual(updated_cfg.break_even_trigger_rr, 1.0)
        self.assertTrue(updated_cfg.forex_rollover_guard_enabled)
        self.assertTrue(updated_cfg.forex_force_flat_friday)
        self.assertFalse(updated_cfg.forex_killzone_only_enabled)

    def test_strategy_bases_and_decisions_contain_gbp(self):
        """Verifica que dashboard/strategy_bases_page.py y decisions_page.py incluyan los registros de GBP."""
        from dashboard.strategy_bases_page import STRATEGY_BASES_HTML
        from dashboard.decisions_page import DECISIONS_HTML

        for sym in self.EXPECTED_GBP_SYMBOLS:
            self.assertIn(f'"{sym}"', STRATEGY_BASES_HTML)
        self.assertIn("FOREX (5)", DECISIONS_HTML)
        self.assertIn("26082205", DECISIONS_HTML)


if __name__ == "__main__":
    unittest.main()
