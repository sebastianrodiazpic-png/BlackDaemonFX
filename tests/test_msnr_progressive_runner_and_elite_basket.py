import unittest
from types import SimpleNamespace
import os
import pandas as pd

import strategy.execution.live_trading_engine as live_mod
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from strategy.execution.runner_extension_manager import RunnerExtensionDecision
from strategy.malaysian_snr.config import MalaysianSNRConfig
import config.ict_instrument_policy as policy


class MockRepo:
    def __init__(self):
        self.updates = []

    def update_trade(self, trade_id, payload):
        self.updates.append((trade_id, payload))


class MockProvider:
    def get_candles(self, symbol, timeframe, count=80):
        # 20 velas alcistas M5
        return pd.DataFrame([
            {
                "time": pd.Timestamp("2026-10-31T12:00:00Z") + pd.Timedelta(minutes=5 * i),
                "open": 100.0 + i,
                "high": 101.5 + i,
                "low": 99.8 + i,
                "close": 101.0 + i,
            }
            for i in range(20)
        ])


class MockPositionExecutor:
    def __init__(self, position):
        self.position = position

    def get_position(self, ticket):
        return self.position

    def get_symbol_constraints(self, symbol):
        return {"point": 0.01, "tick_size": 0.01, "digits": 2}


class MockTradeExecutor:
    def __init__(self, position):
        self.position = position
        self.moves = []
        self.closes = []

    def move_stop_loss(self, position_ticket, stop_loss, take_profit=None, reason=""):
        self.moves.append((position_ticket, stop_loss, take_profit, reason))
        self.position.sl = float(stop_loss)
        if take_profit is not None:
            self.position.tp = float(take_profit)
        return {"modified": True}

    def close_position(self, position_ticket, exit_price=None, reason="manual_close"):
        self.closes.append((position_ticket, reason))
        return {"closed": True, "position_ticket": position_ticket, "reason": reason}


class TestMSNRProgressiveRunnerAndEliteBasket(unittest.TestCase):
    def setUp(self):
        self.position = SimpleNamespace(
            price_open=100.0,
            price_current=115.5,
            sl=100.0,
            tp=120.0,  # Nace buscando 1:2
        )
        self.engine = object.__new__(LiveTradingEngine)
        self.engine.config = LiveTradingConfig(
            execution_enabled=True,
            runner_extension_enabled=True,
            runner_extension_first_trigger_rr=1.5,
            runner_extension_first_lock_rr=1.5,
            runner_extension_second_trigger_rr=2.5,
            runner_extension_second_lock_rr=2.5,
            runner_extension_max_target_rr=4.0,
            second_target_rr=2.0,
        )
        self.engine.provider = MockProvider()
        self.engine.repository = MockRepo()
        self.engine.executor = MockPositionExecutor(self.position)
        self.trade_executor = MockTradeExecutor(self.position)
        self.engine.lifecycle_manager = SimpleNamespace(trade_executor=self.trade_executor)

    def _msnr_trade(self):
        return {
            "id": 999,
            "broker_position_ticket": "7777",
            "instrument": "Boom 1000 Index",
            "direction": "BUY",
            "details": {
                "metadata": {
                    "trade_leg": "RUNNER",
                    "initial_stop_loss": 90.0,  # Riesgo = 10 puntos (1R = 10 puntos)
                    "strategy_name": "MALAYSIAN_SNR",
                    "runner_initial_target_rr": 2.0,
                    "runner_logical_target_rr": 2.0,
                    "runner_max_target_rr": 4.0,
                }
            },
        }

    def test_msnr_elite_basket_composition(self):
        """Verifica que la canasta élite de MSNR incluya a los ganadores probados y excluya a los destructores."""
        elite = policy.MSNR_ELITE_SYNTHETICS
        # Ganadores del replay fiel 1.368 ops:
        self.assertIn("Boom 1000 Index", elite)
        self.assertIn("Crash 1000 Index", elite)
        self.assertIn("Volatility 25 Index", elite)
        self.assertIn("Volatility 10 Index", elite)
        self.assertIn("Step Index", elite)
        # Excluidos por destrucción probada (-43R y -27R):
        self.assertNotIn("Jump 25 Index", elite)
        self.assertNotIn("Volatility 75 Index", elite)

    def test_msnr_config_non_choking_defaults(self):
        """Verifica que los defaults de confirmación de MSNR no asfixien la entrada."""
        cfg = MalaysianSNRConfig()
        self.assertTrue(cfg.enable_scenario_1_continuation)
        self.assertGreaterEqual(cfg.retest_window_minutes, 180)
        self.assertGreaterEqual(cfg.confirmation_tolerance_bars, 1)
        self.assertLessEqual(cfg.recovery_min_body_ratio, 0.30)

    def test_msnr_runner_locks_1_5r_and_extends_to_3r(self):
        """En vivo a 1.5R, el runner de MSNR bloquea 1.5R (+15 pts) y extiende TP a 3.0R (130.0)."""
        original_eval = live_mod.evaluate_runner_continuation
        live_mod.evaluate_runner_continuation = lambda *a, **k: RunnerExtensionDecision(
            True, "CONTINUACION_ESTRUCTURAL_CONFIRMADA", {}
        )
        try:
            trade = self._msnr_trade()
            metadata = dict(trade["details"]["metadata"])
            result = self.engine._manage_runner_extension(
                trade=trade,
                position=self.position,
                metadata=metadata,
                initial_stop_loss=90.0,
                current_rr=1.55,
                move_stop=self.trade_executor.move_stop_loss,
            )
            self.assertTrue(result["managed"])
            self.assertTrue(result["extended"])
            self.assertEqual(result["stage"], "1.5R_TO_3R")
            self.assertEqual(result["profit_lock_rr"], 1.5)
            self.assertEqual(self.position.sl, 115.0)  # 100 + 1.5 * 10
            self.assertEqual(self.position.tp, 130.0)  # 100 + 3.0 * 10
            self.assertEqual(metadata["runner_extension_stage"], "EXTENDED_TO_3R")
        finally:
            live_mod.evaluate_runner_continuation = original_eval

    def test_msnr_runner_locks_2_5r_and_extends_to_4r(self):
        """En vivo a 2.5R, el runner de MSNR bloquea 2.5R (+25 pts) y extiende TP a 4.0R (140.0)."""
        original_eval = live_mod.evaluate_runner_continuation
        live_mod.evaluate_runner_continuation = lambda *a, **k: RunnerExtensionDecision(
            True, "CONTINUACION_ESTRUCTURAL_CONFIRMADA", {}
        )
        try:
            trade = self._msnr_trade()
            metadata = dict(trade["details"]["metadata"])
            metadata["runner_extension_completed_stages"] = ["1.5R_TO_3R"]
            metadata["runner_extension_stage"] = "EXTENDED_TO_3R"

            result = self.engine._manage_runner_extension(
                trade=trade,
                position=self.position,
                metadata=metadata,
                initial_stop_loss=90.0,
                current_rr=2.55,
                move_stop=self.trade_executor.move_stop_loss,
            )
            self.assertTrue(result["managed"])
            self.assertTrue(result["extended"])
            self.assertEqual(result["stage"], "2.5R_TO_4R")
            self.assertEqual(result["profit_lock_rr"], 2.5)
            self.assertEqual(self.position.sl, 125.0)  # 100 + 2.5 * 10
            self.assertEqual(self.position.tp, 140.0)  # 100 + 4.0 * 10
            self.assertEqual(metadata["runner_extension_stage"], "EXTENDED_TO_4R")
        finally:
            live_mod.evaluate_runner_continuation = original_eval


if __name__ == "__main__":
    unittest.main()
