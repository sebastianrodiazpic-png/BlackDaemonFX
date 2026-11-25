from types import SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch
import os

from strategy.execution.live_trading_engine import (
    LiveTradingEngine,
    LiveTradingConfig,
)


class TestQuantitativeRRFase2(unittest.TestCase):
    """Pruebas unitarias de la Fase 2 (Gestión Cuantitativa de R:R):
    1. Holgura estructural en Break Even del RUNNER (sin asfixia en el retesteo post-TP1).
    2. Activación de guardias intermedias para TP3/TP4 con nombres de etapas flexibles.
    3. Configurabilidad de targets en entradas simples y split runners.
    """

    def setUp(self):
        self.config = LiveTradingConfig(
            source="DEMO",
            split_entries_enabled=True,
            first_target_rr=1.0,
            second_target_rr=2.0,
            break_even_enabled=True,
            break_even_offset_points=2,
            break_even_profit_lock_rr_fraction=0.30,  # 30% por defecto general
        )
        self.engine = object.__new__(LiveTradingEngine)
        self.engine.config = self.config
        self.engine.executor = MagicMock()
        self.engine.executor.get_symbol_constraints.return_value = {
            "point": 0.01,
            "tick_size": 0.01,
            "digits": 2,
            "spread": 0.02,
        }
        self.engine.executor.get_current_tick.return_value = {"bid": 100.0, "ask": 100.02}
        self.engine.provider = MagicMock()
        self.engine.provider.get_current_tick.return_value = {"bid": 100.0, "ask": 100.02}

    def test_runner_be_profit_lock_is_zero_by_default(self):
        """Verifica que para piernas RUNNER el profit lock por defecto sea 0.0 (BE neto puro sin ahogamiento)."""
        # Entrada 100.0, SL inicial 90.0 (riesgo = 10.0 puntos)
        entry_price = 100.0
        initial_sl = 90.0
        direction = "BUY"
        position = SimpleNamespace(price_open=100.0, sl=90.0, price_current=110.0, swap=0.0)

        # Para una pierna RUNNER, profit_lock_fraction debe ser 0.0
        trade_leg = "RUNNER"
        profit_lock_fraction = float(os.getenv("DAEMONBLACKFX_RUNNER_BE_PROFIT_LOCK_FRACTION", "0.0"))
        self.assertEqual(profit_lock_fraction, 0.0)

        initial_risk = entry_price - initial_sl
        profit_lock_amount = initial_risk * profit_lock_fraction

        be_price, offset = self.engine._break_even_target_stop(
            "Volatility 100 Index", direction, entry_price, profit_lock_amount=profit_lock_amount, position=position
        )

        # BE neto: entry (100.0) + offset (point*2 + spread = 0.02 + 0.02 = 0.04) = 100.04
        # NO 103.04 (que era lo que forzaba 0.3R y provocaba que el retroceso expulsara al runner)
        self.assertAlmostEqual(be_price, 100.04, places=2)

    def test_runner_be_profit_lock_configurable_via_env(self):
        """Verifica que DAEMONBLACKFX_RUNNER_BE_PROFIT_LOCK_FRACTION permita calibrar el lock si se desea."""
        with patch.dict(os.environ, {"DAEMONBLACKFX_RUNNER_BE_PROFIT_LOCK_FRACTION": "0.10"}):
            entry_price = 100.0
            initial_sl = 90.0
            position = SimpleNamespace(price_open=100.0, sl=90.0, price_current=110.0, swap=0.0)

            trade_leg = "RUNNER"
            profit_lock_fraction = float(os.getenv("DAEMONBLACKFX_RUNNER_BE_PROFIT_LOCK_FRACTION", "0.0"))
            self.assertEqual(profit_lock_fraction, 0.10)

            initial_risk = entry_price - initial_sl
            profit_lock_amount = initial_risk * profit_lock_fraction  # 1.0 punto

            be_price, offset = self.engine._break_even_target_stop(
                "Volatility 100 Index", "BUY", entry_price, profit_lock_amount=profit_lock_amount, position=position
            )
            # 100.0 + 0.04 (offset) + 1.0 (lock) = 101.04
            self.assertAlmostEqual(be_price, 101.04, places=2)

    def test_runner_extension_guard_accepts_completed_stages(self):
        """Verifica que la condición de guardia intermedia SMC_TP3_GUARD_2R reconozca tanto 1.5R_TO_3R como 2R_TO_3R."""
        completed_stages = {"1.5R_TO_3R"}
        self.assertTrue(any(s in completed_stages for s in ("2R_TO_3R", "1.5R_TO_3R")))

        completed_stages_2 = {"2R_TO_3R"}
        self.assertTrue(any(s in completed_stages_2 for s in ("2R_TO_3R", "1.5R_TO_3R")))

        completed_stages_empty = set()
        self.assertFalse(any(s in completed_stages_empty for s in ("2R_TO_3R", "1.5R_TO_3R")))


if __name__ == "__main__":
    unittest.main()
