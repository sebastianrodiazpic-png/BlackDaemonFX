"""Tests de integración y cobertura para la estrategia Malaysian SNR."""

import unittest
from datetime import datetime, timezone
import pandas as pd
import numpy as np

from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from strategy.execution.worker_rules import configure_worker_rules, worker_poll_interval
from database.repository import TradingRepository
from strategy.ai.meta_labeling import MetaLabelingEngine
from app.main import BOT_PROFILES, FULL_MULTI_BOT_PROFILES, _assert_full_multibot_architecture


class TestMalaysianSNRIntegration(unittest.TestCase):

    def test_full_multibot_architecture_includes_malaysian_snr(self):
        self.assertIn("MALAYSIAN_SNR", FULL_MULTI_BOT_PROFILES)
        self.assertIn("MALAYSIAN_SNR", BOT_PROFILES)
        self.assertEqual(BOT_PROFILES["MALAYSIAN_SNR"]["mode"], "malaysian-snr-daemon")
        self.assertEqual(BOT_PROFILES["MALAYSIAN_SNR"]["magic"], 26082031)
        self.assertTrue(_assert_full_multibot_architecture(FULL_MULTI_BOT_PROFILES))

    def test_worker_rules_malaysian_snr_configuration(self):
        config = LiveTradingConfig(bot_profile="MALAYSIAN_SNR", magic=26082031)
        configured = configure_worker_rules(config)
        self.assertTrue(configured.malaysian_snr_enabled)
        self.assertEqual(configured.malaysian_snr_tp1_rr, 2.0)
        self.assertEqual(configured.malaysian_snr_runner_rr, 4.0)
        self.assertEqual(worker_poll_interval("MALAYSIAN_SNR", 5), 5)

    def test_ai_meta_labeling_model_loaded(self):
        ai_engine = MetaLabelingEngine(worker="MALAYSIAN_SNR")
        model = ai_engine.load_model("MALAYSIAN_SNR")
        self.assertTrue(model.trained)
        self.assertGreaterEqual(model.samples, 50)
        self.assertEqual(len(model.model.weights), 44)

    def test_strategy_dual_leg_planning(self):
        config = MalaysianSNRConfig()
        
        class MockDataProvider:
            def get_candles(self, symbol, timeframe, count=80):
                dates = pd.date_range("2026-09-01", periods=count, freq="1h" if timeframe == "H1" else "15min", tz="UTC")
                return pd.DataFrame({
                    "time": dates,
                    "open": np.linspace(100, 110, count),
                    "high": np.linspace(101, 112, count),
                    "low": np.linspace(99, 109, count),
                    "close": np.linspace(100.5, 111.5, count),
                    "tick_volume": [1000] * count,
                })
        
        strategy = MalaysianSNRStrategy(MockDataProvider(), config)
        result = strategy.analyze_symbol("Jump 25 Index")
        self.assertIn("action", result)
        self.assertIn("reason", result)
        self.assertEqual(result["strategy_name"], "MALAYSIAN_SNR")

    def test_repository_profile_persistence(self):
        repo = TradingRepository()
        profiles = repo.latest_instrument_selection_profiles()
        self.assertIn("MALAYSIAN_SNR", profiles)
        self.assertGreaterEqual(len(profiles["MALAYSIAN_SNR"]["selected_symbols"]), 10)

    def test_dashboard_instruments_profile_aware_pruning(self):
        from dashboard.realtime_dashboard import RealtimeDashboardService, DEFAULT_PRIORITIZED_SYMBOLS
        repo = TradingRepository()
        dash = RealtimeDashboardService(repository=repo, host="127.0.0.1", port=8765)
        payload = dash._cached_instruments_payload(force=True)
        
        pruned_by_profile = payload.get("pruned_instruments_by_profile", {})
        self.assertIn("MALAYSIAN_SNR", pruned_by_profile)
        msnr_pruned = pruned_by_profile["MALAYSIAN_SNR"]
        
        # Verify that Malaysian SNR profitable core assets are NOT pruned
        self.assertNotIn("Jump 25 Index", msnr_pruned)
        self.assertNotIn("Step Index 200", msnr_pruned)
        self.assertNotIn("Volatility 10 Index", msnr_pruned)
        self.assertNotIn("Wall Street 30", msnr_pruned)
        self.assertNotIn("Jump 10 Index", msnr_pruned)
        self.assertNotIn("Boom 600 Index", msnr_pruned)
        self.assertNotIn("Crash 600 Index", msnr_pruned)
        self.assertNotIn("Crash 1000 Index", msnr_pruned)
        
        # Verify that actual losing assets ARE pruned
        self.assertIn("Volatility 50 Index", msnr_pruned)
        self.assertIn("CADCHF", msnr_pruned)
        self.assertIn("US Oil", msnr_pruned)
        self.assertIn("Boom 500 Index", msnr_pruned)


if __name__ == "__main__":
    unittest.main()
