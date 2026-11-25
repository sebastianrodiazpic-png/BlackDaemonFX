"""Tests de regresión para Prioridades 1 y 2:
- Prioridad 1: Desbloqueo de pata RUNNER (30%) bajo fallback de comentario MT5 (-2 Invalid comment),
  paso explícito de trade_leg en MT5TradeExecutor -> MT5ExecutionProvider, y atomicidad/recuperación
  de splits parciales sin abortar el ciclo del símbolo.
- Prioridad 2: Regla de excepción 1% @ 1:1 cuando el análisis estructural/cuantitativo no proyecta
  recorrido suficiente hasta TP2 (< 2.0R), más corrección de single_entry_target_rr=1.0 y soporte
  70/30 en el selector de contratos ORB Silver.
"""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from brokers.mt5_execution import MT5ExecutionError, MT5ExecutionProvider
from brokers.mt5_trade_executor import MT5TradeExecutor
from strategy.execution.active_position_guard import (
    _IN_FLIGHT_CACHE,
    _IN_FLIGHT_MUTEX,
    is_terminal_in_flight,
)
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from strategy.execution.trade_executor import TradeExecutionRequest


class TestPriority1RunnerUnblockAndAtomicSplit(unittest.TestCase):
    def setUp(self):
        with _IN_FLIGHT_MUTEX:
            _IN_FLIGHT_CACHE.clear()

    @patch("brokers.mt5_execution.mt5")
    def test_order_check_and_send_fallback_preserve_runner_leg_suffix(self, mock_mt5):
        """Cuando MT5 devuelve (-2, 'Invalid \"comment\" argument'), el fallback debe preservar -RUNNER."""
        provider = MT5ExecutionProvider(MagicMock())

        ok_check = MagicMock(retcode=0)
        mock_mt5.order_check.side_effect = [None, ok_check]
        mock_mt5.last_error.side_effect = [(-2, 'Invalid "comment" argument'), (1, "Success")]

        check, used_req, diag = provider._order_check_safe(
            {"symbol": "Volatility 5 Index", "comment": "DEMO:Volatility 5 Index:H1:M15:M5:RUNNER"}
        )
        self.assertIs(check, ok_check)
        self.assertTrue(diag["comment_fallback_used"])
        self.assertEqual(used_req["comment"], "BlackDaemonFx-RUNNER")
        self.assertLessEqual(len(used_req["comment"]), 20)

        # Reversible vía variable de entorno
        mock_mt5.order_check.side_effect = [None, ok_check]
        mock_mt5.last_error.side_effect = [(-2, 'Invalid "comment" argument'), (1, "Success")]
        with patch.dict(os.environ, {"DAEMONBLACKFX_PRESERVE_FALLBACK_COMMENT_LEG": "0"}):
            _, legacy_req, _ = provider._order_check_safe(
                {"symbol": "Volatility 5 Index", "comment": "DEMO:Volatility 5 Index:RUNNER"}
            )
        self.assertEqual(legacy_req["comment"], "BlackDaemonFx")

    @patch("brokers.mt5_trade_executor.mt5", MagicMock())
    @patch("brokers.mt5_execution.mt5")
    def test_end_to_end_tp1_and_runner_70_30_under_mt5_comment_fallback(self, mock_mt5):
        """Reproduce el bug real del 24-25 nov: incluso si MT5 activa fallback de comentario,
        la pata RUNNER (30%) se envía inmediatamente tras TP1 (70%) sin bloqueo in-flight.
        """
        provider = MT5ExecutionProvider(MagicMock())
        provider._ensure = MagicMock()
        provider.assert_demo_account = MagicMock()
        provider._build_market_request_base = MagicMock(
            side_effect=lambda **kw: {
                "symbol": kw["symbol"],
                "volume": kw["volume"],
                "sl": kw["stop_loss"],
                "tp": kw["take_profit"],
                "magic": kw["magic"],
                "comment": kw["comment"],
                "type_filling": 1,
                "price": 100.0,
            }
        )
        provider._current_market_price = MagicMock(return_value=100.0)
        provider._resize_pre_send_risk = MagicMock(return_value=None)
        provider._validate_pre_send_risk = MagicMock()
        provider._validate_executable_rr = MagicMock(return_value={"executable_rr": 2.0})
        provider._is_order_check_success = MagicMock(return_value=True)
        provider._is_order_send_success = MagicMock(return_value=True)
        provider._filling_name = MagicMock(return_value="IOC")
        provider.position_ticket_from_deal = MagicMock(side_effect=lambda deal: int(deal) + 10000)

        # Simulamos que _run_order_check_with_fallback y _order_check_safe activan el fallback -2 de comentario
        ok_check = MagicMock(retcode=0)

        def fake_run_check_with_fallback(sym, req_base):
            _, retry_req, _ = provider._order_check_safe(req_base)
            return {"valid": True, "request": {**retry_req, "type_filling": 1}}

        provider._run_order_check_with_fallback = MagicMock(side_effect=fake_run_check_with_fallback)

        def fake_mt5_order_check(req):
            # Rechaza cualquier comentario con ':' (simulando el rechazo real del binding) y acepta ASCII con '-'
            if ":" in str(req.get("comment") or ""):
                return None
            return ok_check

        mock_mt5.order_check.side_effect = fake_mt5_order_check
        mock_mt5.last_error.return_value = (-2, 'Invalid "comment" argument')

        deals_counter = iter([5001, 5002])

        def fake_mt5_order_send(req):
            d = next(deals_counter)
            return MagicMock(retcode=10009, order=d, deal=d, volume=req["volume"], price=100.0, comment="Placed")

        mock_mt5.order_send.side_effect = fake_mt5_order_send
        provider.get_open_positions = MagicMock(return_value=[])
        provider.get_pending_orders = MagicMock(return_value=[])

        executor = MT5TradeExecutor(execution_provider=provider, magic=26082032, deviation=20)

        # 1. Ejecutar Pata 1: TP1 (70% riesgo = 0.07 lotes)
        req_tp1 = TradeExecutionRequest(
            symbol="Volatility 5 Index",
            timeframe="M5",
            direction="BUY",
            volume=0.07,
            entry_time="2026-11-25T13:15:00+00:00",
            entry_price=100.0,
            stop_loss=95.0,
            take_profit=105.0,
            metadata={
                "execution_key": "DEMO:Volatility 5 Index:H1:M15:M5:2026-11-25T13:15:00+00:00:BUY:TP1",
                "trade_leg": "TP1",
            },
        )
        res_tp1 = executor.execute_trade(req_tp1)
        self.assertEqual(res_tp1.status, "FILLED")
        self.assertEqual(res_tp1.position_ticket, "15001")
        self.assertTrue(is_terminal_in_flight("Volatility 5 Index"))

        # Ahora MT5 reporta TP1 abierta
        pos_tp1 = MagicMock(
            symbol="Volatility 5 Index",
            ticket=15001,
            type=0,
            price_open=100.0,
            sl=95.0,
            magic=26082032,
            comment="BlackDaemonFx-TP1",
        )
        provider.get_open_positions = MagicMock(return_value=[pos_tp1])

        # 2. Ejecutar Pata 2: RUNNER (30% riesgo = 0.03 lotes) -> DEBE EJECUTARSE SIN BLOQUEO
        req_runner = TradeExecutionRequest(
            symbol="Volatility 5 Index",
            timeframe="M5",
            direction="BUY",
            volume=0.03,
            entry_time="2026-11-25T13:15:00+00:00",
            entry_price=100.0,
            stop_loss=95.0,
            take_profit=110.0,
            metadata={
                "execution_key": "DEMO:Volatility 5 Index:H1:M15:M5:2026-11-25T13:15:00+00:00:BUY:RUNNER",
                "trade_leg": "RUNNER",
            },
        )
        res_runner = executor.execute_trade(req_runner)
        self.assertEqual(res_runner.status, "FILLED")
        self.assertEqual(res_runner.position_ticket, "15002")

    @patch("brokers.mt5_execution.mt5")
    def test_explicit_trade_leg_allows_same_worker_runner_but_blocks_cross_worker(self, mock_mt5):
        """Incluso si el comentario no lleva etiqueta, trade_leg='RUNNER' autoriza la 2ª pata del mismo worker."""
        provider = MT5ExecutionProvider(MagicMock())
        provider._ensure = MagicMock()
        mock_check = MagicMock(retcode=0)
        provider._order_check_safe = MagicMock(side_effect=lambda req: (mock_check, req, {}))
        provider._run_order_check_with_fallback = MagicMock(
            side_effect=lambda sym, req_base: {"valid": True, "request": {**dict(req_base), "type_filling": 1}}
        )
        provider._current_market_price = MagicMock(return_value=2600.0)
        provider._resize_pre_send_risk = MagicMock(return_value=None)
        provider._validate_pre_send_risk = MagicMock()
        provider._validate_executable_rr = MagicMock()
        mock_send = MagicMock(retcode=10009, order=901, deal=902, volume=0.03, price=2600.0)
        provider._order_send_safe = MagicMock(side_effect=lambda req: (mock_send, req, {}))
        provider._is_order_send_success = MagicMock(return_value=True)

        sym = "TEST_EXPLICIT_LEG_SYM"
        # Enviar TP1 primero (activa terminal in-flight)
        provider.get_open_positions = MagicMock(return_value=[])
        provider.get_pending_orders = MagicMock(return_value=[])
        provider.place_market_order(sym, "BUY", 0.07, 2590.0, 2610.0, 26082028, "BlackDaemonFx", trade_leg="TP1")

        pos_tp1 = MagicMock(symbol=sym, ticket=7001, type=0, price_open=2600.0, sl=2590.0, magic=26082028)
        provider.get_open_positions = MagicMock(return_value=[pos_tp1])

        # RUNNER del mismo worker con comentario genérico pero trade_leg="RUNNER" -> permitido
        res = provider.place_market_order(
            sym, "BUY", 0.03, 2590.0, 2620.0, 26082028, "BlackDaemonFx", trade_leg="RUNNER"
        )
        self.assertIsNotNone(res)

        # Otro worker (magic distinto) intentando usar trade_leg="RUNNER" -> bloqueado estrictamente
        with self.assertRaises(MT5ExecutionError) as ctx:
            provider.place_market_order(
                sym, "BUY", 0.03, 2590.0, 2620.0, 26082032, "BlackDaemonFx", trade_leg="RUNNER"
            )
        self.assertIn("ORDER_SEND_BLOCKED_CROSS_WORKER_CONFLICT", str(ctx.exception))


class TestPriority2SubTp2ExceptionRuleAndSingleRr(unittest.TestCase):
    def _make_engine(self, **cfg_overrides):
        cfg = LiveTradingConfig(**cfg_overrides)
        engine = object.__new__(LiveTradingEngine)
        engine.config = cfg
        engine._is_forex_symbol = lambda s: s in {"EURUSD", "USDCAD", "GBPUSD"}
        engine._is_volatility_symbol = lambda s: "VOLATILITY" in s.upper()
        engine._is_jump_symbol = lambda s: "JUMP" in s.upper()
        return engine

    @staticmethod
    def _mock_build_plan(specs, mode):
        return [
            {
                "name": s[0],
                "risk_fraction": s[1],
                "target_rr": s[2],
                "broker_target_rr": s[3] if len(s) == 4 else s[2],
            }
            for s in specs
        ], None

    def test_msnr_sub_tp2_obstacle_switches_to_single_1pct_1to1_on_boom(self):
        """Cuando MSNR tiene recorrido >= 1.0R pero < 2.0R hasta un obstáculo, ejecuta 1 entrada 1% @ 1:1."""
        engine = self._make_engine(bot_profile="BOOM")
        signal = {
            "tp1_rr": 1.0,
            "runner_rr": 2.0,
            "obstacle_level": 1014.5,
            "tp2_price": 1014.0,  # 1.40R de recorrido desde 1000 con SL 990
        }
        legs, split_err, single_err, mode = engine._plan_execution_legs(
            exact_symbol="Boom 1000 Index",
            direction="BUY",
            entry=1000.0,
            sl=990.0,
            rr=2.0,
            strategy_name="MALAYSIAN_SNR",
            signal=signal,
            total_risk_amount=100.0,
            risk_fraction=0.70,
            runner_risk_fraction=0.30,
            silver_risk_cap=False,
            build_plan=self._mock_build_plan,
        )
        self.assertIsNone(split_err)
        self.assertIsNone(single_err)
        self.assertEqual(mode, "SINGLE")
        self.assertEqual(len(legs), 1)
        self.assertEqual(legs[0]["name"], "SINGLE")
        self.assertAlmostEqual(legs[0]["risk_fraction"], 1.0, places=4)
        self.assertAlmostEqual(legs[0]["target_rr"], 1.0, places=4)
        self.assertTrue(signal["sub_tp2_exception"]["applied"])
        self.assertEqual(signal["sub_tp2_exception"]["reason"], "MSNR_OBSTACLE_BEFORE_MINIMUM_TP2")

        # Si se desactiva por interruptor, vuelve al comportamiento previo
        with patch.dict(os.environ, {"DAEMONBLACKFX_SUB_TP2_SINGLE_1TO1_ENABLED": "0"}):
            engine_off = self._make_engine(bot_profile="BOOM")
            legs_off, _, _, mode_off = engine_off._plan_execution_legs(
                exact_symbol="Boom 1000 Index",
                direction="BUY",
                entry=1000.0,
                sl=990.0,
                rr=2.0,
                strategy_name="MALAYSIAN_SNR",
                signal=dict(signal),
                total_risk_amount=100.0,
                risk_fraction=0.70,
                runner_risk_fraction=0.30,
                silver_risk_cap=False,
                build_plan=self._mock_build_plan,
            )
            self.assertEqual(mode_off, "SPLIT")
            self.assertEqual(len(legs_off), 2)

    def test_smc_m15_obstacle_between_1r_and_2r_switches_to_single_1pct_1to1(self):
        """En SMC/Forex/Volatility, un obstáculo M15 a 1.45R evita abrir runner a 2R y ejecuta 1% @ 1:1."""
        engine = self._make_engine(bot_profile="FOREX_1")
        signal = {
            "m15_obstacles": [
                {"type": "OPPOSING_OB", "low": 1.1045, "high": 1.1055},  # a 1.45R desde 1.1000 con SL 1.0969 -> risk=0.0031 => 1.45R
            ]
        }
        legs, split_err, _, mode = engine._plan_execution_legs(
            exact_symbol="EURUSD",
            direction="BUY",
            entry=1.1000,
            sl=1.0969,
            rr=2.0,
            strategy_name="SMC",
            signal=signal,
            total_risk_amount=100.0,
            risk_fraction=0.70,
            runner_risk_fraction=0.30,
            silver_risk_cap=False,
            build_plan=self._mock_build_plan,
        )
        self.assertIsNone(split_err)
        self.assertEqual(mode, "SINGLE")
        self.assertEqual(len(legs), 1)
        self.assertAlmostEqual(legs[0]["risk_fraction"], 1.0, places=4)
        self.assertAlmostEqual(legs[0]["target_rr"], 1.0, places=4)
        self.assertEqual(signal["sub_tp2_exception"]["reason"], "M15_OBSTACLE_BEFORE_TP2")

    def test_gold_quarters_sub_2r_quarter_target_2_switches_to_single_1to1(self):
        """En GOLD_QUARTERS, si el Cuarto 2 proyecta < 2.0R (ej. 1.35R), aplica excepción 1% @ 1:1."""
        engine = self._make_engine(bot_profile="GOLD")
        signal = {
            "risk_reward_ratio_tp1": 1.0,
            "risk_reward_ratio_tp2": 1.35,
            "quarter_target_2": 2613.5,
        }
        legs, split_err, _, mode = engine._plan_execution_legs(
            exact_symbol="XAUUSD",
            direction="BUY",
            entry=2600.0,
            sl=2590.0,
            rr=1.35,
            strategy_name="GOLD_QUARTERS",
            signal=signal,
            total_risk_amount=100.0,
            risk_fraction=0.70,
            runner_risk_fraction=0.30,
            silver_risk_cap=False,
            build_plan=self._mock_build_plan,
        )
        self.assertIsNone(split_err)
        self.assertEqual(mode, "SINGLE")
        self.assertEqual(len(legs), 1)
        self.assertAlmostEqual(legs[0]["risk_fraction"], 1.0, places=4)
        self.assertAlmostEqual(legs[0]["target_rr"], 1.0, places=4)

    def test_standard_clear_projection_preserves_70_30_split(self):
        """Con proyección limpia >= 2.0R hasta TP2, mantiene estrictamente el split 70% / 30%."""
        engine = self._make_engine(bot_profile="ORB")
        signal = {"opening_range_atr_ratio": 1.4}
        legs, split_err, _, mode = engine._plan_execution_legs(
            exact_symbol="XAUUSD",
            direction="BUY",
            entry=2600.0,
            sl=2590.0,
            rr=2.0,
            strategy_name="ORB_NEW_YORK",
            signal=signal,
            total_risk_amount=100.0,
            risk_fraction=0.70,
            runner_risk_fraction=0.30,
            silver_risk_cap=False,
            build_plan=self._mock_build_plan,
        )
        self.assertIsNone(split_err)
        self.assertEqual(mode, "SPLIT")
        self.assertEqual(len(legs), 2)
        self.assertAlmostEqual(legs[0]["risk_fraction"], 0.70, places=4)
        self.assertAlmostEqual(legs[0]["target_rr"], 1.0, places=4)
        self.assertAlmostEqual(legs[1]["risk_fraction"], 0.30, places=4)
        self.assertGreaterEqual(legs[1]["target_rr"], 2.0)

    def test_app_main_no_longer_hardcodes_single_entry_target_rr_to_2(self):
        """Verifica que app/main.py respete DAEMONBLACKFX_SINGLE_ENTRY_TARGET_RR=1.0 en vez de 2.0 fijo."""
        src = Path("app/main.py").read_text(encoding="utf-8")
        self.assertNotIn("single_entry_target_rr=2.0", src)
        self.assertIn('DAEMONBLACKFX_SINGLE_ENTRY_TARGET_RR", "1.0"', src)

    def test_orb_silver_contract_selector_supports_70_30_split(self):
        """Verifica que _evaluate_orb_silver_contract acepte split 70% / 30% sin rechazar por 2*fraction != 1."""
        import pandas as pd

        engine = self._make_engine(
            bot_profile="ORB",
            split_entries_enabled=True,
            split_entry_risk_fraction=0.70,
            orb_risk_percent=1.0,
        )
        engine.orb_strategy = MagicMock()
        engine.orb_strategy.analyze_symbol.return_value = {
            "valid": True,
            "signal": {"direction": "BUY", "stop_loss": 29.50, "risk_reward_ratio": 2.0},
        }
        engine._meta_execution_spread = MagicMock(
            return_value={
                "spread_status": "AVAILABLE",
                "spread_source": "MT5_EXECUTION",
                "spread_quote_time": pd.Timestamp.now(tz="UTC").isoformat(),
                "execution_bid": 30.00,
                "execution_ask": 30.02,
            }
        )
        engine.executor = MagicMock()
        engine.executor.normalize_market_stops.return_value = {
            "valid": True,
            "entry_price": 30.02,
            "stop_loss": 29.52,
        }
        engine.executor.risk_buffered_entry_price.return_value = 30.02
        engine.executor.calculate_volume.side_effect = lambda sym, d, e, s, r: {
            "volume": round(r / 50.0, 2),
            "actual_risk_amount": r,
        }
        engine.executor.calculate_risk_amount.return_value = {"actual_risk_amount": 1.0}
        engine.executor.calculate_margin_amount.return_value = {"margin_required": 50.0}
        engine.executor.check_market_order.return_value = {"valid": True}

        res = engine._evaluate_orb_silver_contract(
            "XAGUSD", {"equity": 10000.0, "balance": 10000.0, "free_margin": 9000.0}
        )
        self.assertTrue(res["viable"], res)
        self.assertEqual(res["legs"], 2)
        self.assertEqual(len(res["leg_volumes"]), 2)


if __name__ == "__main__":
    unittest.main()
