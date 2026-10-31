from types import SimpleNamespace
import unittest
import pandas as pd

import strategy.execution.live_trading_engine as live_mod
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from strategy.execution.runner_extension_manager import RunnerExtensionDecision


class MockRepo:
    def __init__(self):
        self.updates = []

    def update_trade(self, trade_id, payload):
        self.updates.append((trade_id, payload))


class MockProvider:
    def get_candles(self, symbol, timeframe, count=80):
        return pd.DataFrame([
            {
                "time": pd.Timestamp("2026-08-30T12:00:00Z") + pd.Timedelta(minutes=5 * i),
                "open": 100 + i,
                "high": 101 + i,
                "low": 99 + i,
                "close": 100.8 + i,
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


class TestDynamicProgressiveRunner(unittest.TestCase):
    def setUp(self):
        self.position = SimpleNamespace(
            price_open=100.0,
            price_current=115.5,
            sl=100.02,
            tp=120.0,  # Nace en 1:2 (120.0 con entrada 100 y SL 90, riesgo = 10)
        )
        self.engine = object.__new__(LiveTradingEngine)
        self.engine.config = LiveTradingConfig(
            execution_enabled=True,
            runner_extension_enabled=True,
            first_target_rr=1.0,
            second_target_rr=2.0,
            volatility_first_target_rr=1.0,
            volatility_second_target_rr=2.0,
            runner_extension_first_trigger_rr=1.5,
            runner_extension_first_lock_rr=1.5,
            runner_extension_second_trigger_rr=2.5,
            runner_extension_second_lock_rr=2.5,
            runner_extension_max_target_rr=4.0,
        )
        self.engine.provider = MockProvider()
        self.engine.repository = MockRepo()
        self.engine.executor = MockPositionExecutor(self.position)
        self.trade_executor = MockTradeExecutor(self.position)
        self.engine.lifecycle_manager = SimpleNamespace(trade_executor=self.trade_executor)

    def _trade(self):
        return {
            "id": 99,
            "broker_position_ticket": "5555",
            "instrument": "Volatility 100 Index",
            "direction": "BUY",
            "details": {
                "metadata": {
                    "trade_leg": "RUNNER",
                    "initial_stop_loss": 90.0,
                    "strategy_name": "ICT_SABRI_MALLE",
                }
            },
        }

    def test_default_config_values(self):
        """Verifica que la configuración por defecto adopte 1.5R y 2.5R como hitos."""
        cfg = LiveTradingConfig()
        self.assertEqual(cfg.runner_extension_first_trigger_rr, 1.5)
        self.assertEqual(cfg.runner_extension_first_lock_rr, 1.5)
        self.assertEqual(cfg.runner_extension_second_trigger_rr, 2.5)
        self.assertEqual(cfg.runner_extension_second_lock_rr, 2.5)
        self.assertEqual(cfg.second_target_rr, 2.0)

    def test_at_1_5r_locks_1_5r_and_extends_to_3r(self):
        """Al alcanzar 1.5R con continuación, bloquea 1.5R (+15 puntos) y extiende a 3R (130.0)."""
        original_eval = live_mod.evaluate_runner_continuation
        live_mod.evaluate_runner_continuation = lambda *a, **k: RunnerExtensionDecision(
            True, "CONTINUACION_ESTRUCTURAL_CONFIRMADA", {}
        )
        try:
            metadata = dict(self._trade()["details"]["metadata"])
            result = self.engine._manage_runner_extension(
                trade=self._trade(),
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
            # Entrada 100, riesgo 10 -> SL a 115.0 (+1.5R protegido)
            self.assertEqual(self.position.sl, 115.0)
            # TP ampliado a 3R (o max_target_rr fail-safe)
            self.assertGreaterEqual(self.position.tp, 130.0)
            self.assertEqual(metadata["runner_profit_lock_rr"], 1.5)
            self.assertEqual(metadata["runner_extension_stage"], "EXTENDED_TO_3R")
        finally:
            live_mod.evaluate_runner_continuation = original_eval

    def test_at_2_5r_locks_2_5r_and_extends_to_4r(self):
        """Al alcanzar 2.5R con continuación, bloquea 2.5R (+25 puntos) y extiende a 4R (140.0)."""
        original_eval = live_mod.evaluate_runner_continuation
        live_mod.evaluate_runner_continuation = lambda *a, **k: RunnerExtensionDecision(
            True, "CONTINUACION_ESTRUCTURAL_CONFIRMADA", {}
        )
        try:
            metadata = dict(self._trade()["details"]["metadata"])
            # Simulamos que ya completó la primera etapa 1.5R_TO_3R
            metadata["runner_extension_completed_stages"] = ["1.5R_TO_3R"]
            metadata["runner_extension_stage"] = "EXTENDED_TO_3R"

            result = self.engine._manage_runner_extension(
                trade=self._trade(),
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
            # Entrada 100, riesgo 10 -> SL a 125.0 (+2.5R protegido)
            self.assertEqual(self.position.sl, 125.0)
            self.assertEqual(self.position.tp, 140.0)
            self.assertEqual(metadata["runner_profit_lock_rr"], 2.5)
            self.assertEqual(metadata["runner_extension_stage"], "EXTENDED_TO_4R")
        finally:
            live_mod.evaluate_runner_continuation = original_eval


if __name__ == "__main__":
    unittest.main()
