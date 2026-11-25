import unittest
from unittest.mock import MagicMock, patch
from strategy.execution.active_position_guard import (
    _IN_FLIGHT_CACHE,
    _IN_FLIGHT_MUTEX,
    record_terminal_in_flight,
    is_terminal_in_flight,
)
from brokers.mt5_execution import MT5ExecutionProvider, MT5ExecutionError


class TestSplitRunnerBarrierFix(unittest.TestCase):
    """Verifica que la barrera terminal in-flight y active position guard permitan

    la ejecución inmediata de la pierna RUNNER en entradas divididas (TP1 + RUNNER),
    sin bloquear la segunda pata ni desarmar el contrato de 2 patas (1% total).
    """

    def setUp(self):
        with _IN_FLIGHT_MUTEX:
            _IN_FLIGHT_CACHE.clear()

    @patch("brokers.mt5_execution.mt5")
    def test_split_runner_not_blocked_by_tp1_in_flight_or_active_position(self, mock_mt5):
        """La pata TP1 se envía, queda in-flight y como posición activa.

        La pata RUNNER inmediata DEBE permitirse y enviarse sin error.
        Una tercera pata o nueva orden debe ser bloqueada.
        """
        provider = MT5ExecutionProvider(MagicMock())
        symbol = "Boom 1000 Index"

        # Mock básico de mt5
        mock_mt5.positions_get.return_value = []
        mock_mt5.orders_get.return_value = []
        mock_mt5.symbol_info_tick.return_value = MagicMock(ask=15000.0, bid=15000.0)

        # Mock de order_check y ordenes
        provider._ensure = MagicMock()
        mock_check = MagicMock()
        mock_check.retcode = 0
        provider._order_check_safe = MagicMock(side_effect=lambda req: (mock_check, req, {}))
        provider._run_order_check_with_fallback = MagicMock(side_effect=lambda sym, req_base: {
            "valid": True,
            "request": {**dict(req_base), "type_filling": 1},
        })
        provider._current_market_price = MagicMock(return_value=15000.0)
        provider._resize_pre_send_risk = MagicMock(return_value=None)
        provider._validate_pre_send_risk = MagicMock()
        provider._validate_executable_rr = MagicMock()

        # Mock de order_send exitoso
        mock_send_result = MagicMock()
        mock_send_result.retcode = 10009
        mock_send_result.order = 1001
        mock_send_result.deal = 2001
        mock_send_result.volume = 0.5
        mock_send_result.price = 15000.0
        provider._order_send_safe = MagicMock(side_effect=lambda req: (mock_send_result, req, {}))
        provider._is_order_send_success = MagicMock(return_value=True)

        # 1. Enviar TP1
        res1 = provider.place_market_order(
            symbol=symbol,
            direction="BUY",
            volume=0.5,
            stop_loss=14950.0,
            take_profit=15050.0,
            magic=26082101,
            comment="smc:B1000:BUY:TP1",
        )
        self.assertIsNotNone(res1)
        self.assertTrue(is_terminal_in_flight(symbol))

        # Ahora MT5 tiene 1 posición abierta (el TP1 recién llenado)
        pos_tp1 = MagicMock()
        pos_tp1.symbol = symbol
        pos_tp1.ticket = 4796921802
        pos_tp1.type = 0
        pos_tp1.price_open = 15000.0
        pos_tp1.sl = 14950.0
        pos_tp1.magic = 26082101
        pos_tp1.comment = "smc:B1000:BUY:TP1"
        provider.get_open_positions = MagicMock(return_value=[pos_tp1])
        provider.get_pending_orders = MagicMock(return_value=[])

        # 2. El RUNNER NO debe lanzar MT5ExecutionError (debe ejecutarse exitosamente)
        res2 = provider.place_market_order(
            symbol=symbol,
            direction="BUY",
            volume=0.5,
            stop_loss=14950.0,
            take_profit=15100.0,
            magic=26082101,
            comment="smc:B1000:BUY:RUNNER",
        )
        self.assertIsNotNone(res2)

        # 3. Verificar que una orden NO-RUNNER (ej. nueva señal TP1 o duplicado)
        # SÍ sea bloqueada por estar in-flight o por tener ya posición activa
        with self.assertRaises(MT5ExecutionError) as ctx:
            provider.place_market_order(
                symbol=symbol,
                direction="BUY",
                volume=0.5,
                stop_loss=14950.0,
                take_profit=15050.0,
                magic=26082101,
                comment="smc:B1000:BUY:TP1",
            )
        self.assertIn("ORDER_SEND_BLOCKED", str(ctx.exception))

        # 4. Si ya existen 2 posiciones abiertas, incluso un intento extra de RUNNER debe ser bloqueado
        pos_runner = MagicMock()
        pos_runner.symbol = symbol
        pos_runner.ticket = 4796921803
        pos_runner.type = 0
        pos_runner.price_open = 15000.0
        pos_runner.sl = 14950.0
        pos_runner.magic = 26082101
        pos_runner.comment = "smc:B1000:BUY:RUNNER"
        provider.get_open_positions = MagicMock(return_value=[pos_tp1, pos_runner])

        with self.assertRaises(MT5ExecutionError) as ctx2:
            provider.place_market_order(
                symbol=symbol,
                direction="BUY",
                volume=0.5,
                stop_loss=14950.0,
                take_profit=15100.0,
                magic=26082101,
                comment="smc:B1000:BUY:RUNNER",
            )
        self.assertIn("ORDER_SEND_BLOCKED_ACTIVE_POSITION", str(ctx2.exception))

    @patch("brokers.mt5_execution.mt5")
    def test_orb_hyphen_runner_not_blocked_by_in_flight_barrier(self, mock_mt5):
        """Verifica que comentarios con guiones propios de ORB (-RUNNER, -TP2)

        sean reconocidos correctamente como patas split runner y no sean bloqueados
        por ORDER_SEND_BLOCKED_TERMINAL_DUPLICATE.
        """
        provider = MT5ExecutionProvider(MagicMock())
        symbol = "US Tech 100"

        mock_mt5.positions_get.return_value = []
        mock_mt5.orders_get.return_value = []
        mock_mt5.symbol_info_tick.return_value = MagicMock(ask=26000.0, bid=26000.0)

        provider._ensure = MagicMock()
        mock_check = MagicMock()
        mock_check.retcode = 0
        provider._order_check_safe = MagicMock(side_effect=lambda req: (mock_check, req, {}))
        provider._run_order_check_with_fallback = MagicMock(side_effect=lambda sym, req_base: {
            "valid": True,
            "request": {**dict(req_base), "type_filling": 1},
        })
        provider._current_market_price = MagicMock(return_value=26000.0)
        provider._resize_pre_send_risk = MagicMock(return_value=None)
        provider._validate_pre_send_risk = MagicMock()
        provider._validate_executable_rr = MagicMock()

        mock_send_result = MagicMock()
        mock_send_result.retcode = 10009
        mock_send_result.order = 1002
        mock_send_result.deal = 2002
        mock_send_result.volume = 0.1
        mock_send_result.price = 26000.0
        provider._order_send_safe = MagicMock(side_effect=lambda req: (mock_send_result, req, {}))
        provider._is_order_send_success = MagicMock(return_value=True)

        # 1. Enviar TP1 con formato ORB (guión)
        res1 = provider.place_market_order(
            symbol=symbol,
            direction="SELL",
            volume=0.1,
            stop_loss=26100.0,
            take_profit=25900.0,
            magic=26082028,
            comment="ORB-20261124-152000-TP1",
        )
        self.assertIsNotNone(res1)
        self.assertTrue(is_terminal_in_flight(symbol))

        # MT5 ahora tiene 1 posición abierta (el TP1 recién ejecutado)
        pos_tp1 = MagicMock()
        pos_tp1.symbol = symbol
        pos_tp1.ticket = 4797630821
        pos_tp1.type = 1
        pos_tp1.price_open = 26000.0
        pos_tp1.sl = 26100.0
        pos_tp1.magic = 26082028
        pos_tp1.comment = "ORB-20261124-152000-TP1"
        provider.get_open_positions = MagicMock(return_value=[pos_tp1])
        provider.get_pending_orders = MagicMock(return_value=[])

        # 2. El RUNNER con guión (-RUNNER) NO debe ser bloqueado por terminal in-flight
        res2 = provider.place_market_order(
            symbol=symbol,
            direction="SELL",
            volume=0.1,
            stop_loss=26100.0,
            take_profit=25800.0,
            magic=26082028,
            comment="ORB-20261124-152000-RUNNER",
        )
        self.assertIsNotNone(res2)


if __name__ == "__main__":
    unittest.main()
