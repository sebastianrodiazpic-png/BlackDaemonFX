import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from brokers.mt5_connector import MT5Connector
from brokers.mt5_execution import MT5ExecutionError, MT5ExecutionProvider
from config.symbol_policy import get_symbol_direction_policy, is_direction_allowed
from risk.portfolio_accounting import PortfolioAccountingManager, PortfolioLimits
from strategy.execution.active_position_guard import (
    _IN_FLIGHT_CACHE,
    _IN_FLIGHT_MUTEX,
    check_active_position_guard,
)
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from tools.db_maintenance import apply_maintenance, inspect_database


def _make_mock_provider(mock_mt5):
    provider = MT5ExecutionProvider(MagicMock())
    mock_mt5.positions_get.return_value = []
    mock_mt5.orders_get.return_value = []
    mock_mt5.symbol_info_tick.return_value = MagicMock(ask=100.0, bid=100.0)
    provider._ensure = MagicMock()
    mock_check = MagicMock()
    mock_check.retcode = 0
    provider._order_check_safe = MagicMock(side_effect=lambda req: (mock_check, req, {}))
    provider._run_order_check_with_fallback = MagicMock(
        side_effect=lambda sym, req_base: {"valid": True, "request": {**dict(req_base), "type_filling": 1}}
    )
    provider._current_market_price = MagicMock(return_value=100.0)
    provider._resize_pre_send_risk = MagicMock(return_value=None)
    provider._validate_pre_send_risk = MagicMock()
    provider._validate_executable_rr = MagicMock()
    mock_send = MagicMock()
    mock_send.retcode = 10009
    mock_send.order = 1001
    mock_send.deal = 2001
    mock_send.volume = 0.1
    mock_send.price = 100.2
    provider._order_send_safe = MagicMock(side_effect=lambda req: (mock_send, req, {}))
    provider._is_order_send_success = MagicMock(return_value=True)
    return provider


class TestExecutionHardeningAuditFixes(unittest.TestCase):
    def setUp(self):
        with _IN_FLIGHT_MUTEX:
            _IN_FLIGHT_CACHE.clear()

    @patch("brokers.mt5_execution.mt5")
    def test_place_market_order_fail_closed_on_guard_exception(self, mock_mt5):
        provider = _make_mock_provider(mock_mt5)
        provider.get_open_positions = MagicMock(side_effect=RuntimeError("ipc_glitch"))
        with self.assertRaises(MT5ExecutionError) as ctx:
            provider.place_market_order(
                symbol="XAUUSD",
                direction="BUY",
                volume=0.1,
                stop_loss=95.0,
                take_profit=110.0,
                magic=26082032,
                comment="smc:XAUUSD:BUY:TP1",
            )
        self.assertIn("ORDER_SEND_BLOCKED_GUARD_ERROR", str(ctx.exception))
        provider._order_send_safe.assert_not_called()

    @patch("brokers.mt5_execution.mt5")
    def test_split_runner_blocks_cross_worker_or_opposite_direction(self, mock_mt5):
        provider = _make_mock_provider(mock_mt5)
        existing_pos = MagicMock(symbol="XAUUSD", ticket=999, type=0, magic=26082028)  # ORB BUY
        provider.get_open_positions = MagicMock(return_value=[existing_pos])
        provider.get_pending_orders = MagicMock(return_value=[])

        # Otro worker (ICT magic 26082032) intentando enviar :RUNNER -> bloqueado
        with self.assertRaises(MT5ExecutionError) as ctx:
            provider.place_market_order(
                symbol="XAUUSD",
                direction="BUY",
                volume=0.1,
                stop_loss=95.0,
                take_profit=110.0,
                magic=26082032,
                comment="smc:XAUUSD:BUY:RUNNER",
            )
        self.assertIn("ORDER_SEND_BLOCKED_CROSS_WORKER_CONFLICT", str(ctx.exception))

        # Mismo worker pero dirección opuesta (SELL vs BUY) -> bloqueado
        with self.assertRaises(MT5ExecutionError) as ctx2:
            provider.place_market_order(
                symbol="XAUUSD",
                direction="SELL",
                volume=0.1,
                stop_loss=105.0,
                take_profit=90.0,
                magic=26082028,
                comment="ORB-123-RUNNER",
            )
        self.assertIn("ORDER_SEND_BLOCKED_CROSS_WORKER_CONFLICT", str(ctx2.exception))

        # Mismo worker y misma dirección -> permitido y devuelve requested_entry_price
        res = provider.place_market_order(
            symbol="XAUUSD",
            direction="BUY",
            volume=0.1,
            stop_loss=95.0,
            take_profit=110.0,
            magic=26082028,
            comment="ORB-123-RUNNER",
        )
        self.assertEqual(res["requested_entry_price"], 100.0)
        self.assertEqual(res["entry_price"], 100.2)

    @patch("brokers.mt5_connector.mt5")
    def test_mt5_connector_resets_connected_flag_and_retries(self, mock_mt5):
        conn = MT5Connector()
        conn.connected = True
        mock_mt5.terminal_info.return_value = MagicMock(connected=False)
        self.assertFalse(conn.is_connected())
        self.assertFalse(conn.connected)

        # connect() reintenta cuando initialize() falla la primera vez
        mock_mt5.initialize.side_effect = [False, True]
        mock_mt5.account_info.return_value = MagicMock(login=123)
        mock_mt5.last_error.return_value = (-1, "transient")
        with patch.dict(
            os.environ,
            {"DAEMONBLACKFX_MT5_RECONNECT_RETRIES": "2", "DAEMONBLACKFX_MT5_RECONNECT_BACKOFF_SECONDS": "0"},
        ):
            self.assertTrue(conn.connect())
        self.assertTrue(conn.connected)
        self.assertEqual(mock_mt5.initialize.call_count, 2)

    def test_active_position_guard_be_rejects_unknown_position_type(self):
        pos = {"symbol": "XAUUSD", "ticket": 111, "type": "", "sl": 2500.0, "price_open": 2500.0}
        res = check_active_position_guard("XAUUSD", [pos], [], allow_breakeven_positions=True)
        self.assertFalse(res["can_analyze"])
        self.assertEqual(res["status"], "BLOCKED_ACTIVE_TRADE")

    def test_portfolio_accounting_signed_costs_and_dual_currency(self):
        mgr = PortfolioAccountingManager(
            initial_balance=10000.0,
            limits=PortfolioLimits(max_currency_risk_percent=2.0, max_total_concurrent_risk_percent=10.0),
        )
        mgr.register_open_position("t1", "EURUSD", "BUY", 1.10, 1.09, 1.12, 1.0, risk_amount=150.0)
        # EURGBP comparte EUR con EURUSD (150 + 100 = 250 > 200 = 2% de 10,000) -> debe bloquearse
        ok, reason = mgr.can_open_new_trade("EURGBP", planned_risk_amount=100.0)
        self.assertFalse(ok)
        self.assertIn("EUR", reason)

        # Cierre con costes MT5 negativos (-5 commission, -2.5 swap): 10000 + 50 - 5 - 2.5 = 10042.5
        mgr.close_position("t1", gross_pnl=50.0, commission=-5.0, swap=-2.5)
        self.assertAlmostEqual(mgr.realized_balance, 10042.5, places=4)

    def test_ladder_direction_policy(self):
        self.assertEqual(get_symbol_direction_policy("Ladder Volatility Down Index").allowed_direction, "SELL")
        self.assertTrue(is_direction_allowed("Ladder Volatility Down Index", "SELL"))
        self.assertFalse(is_direction_allowed("Ladder Volatility Down Index", "BUY"))
        self.assertEqual(get_symbol_direction_policy("Ladder Volatility Up Index").allowed_direction, "BUY")
        self.assertTrue(is_direction_allowed("Ladder Volatility Up Index", "BUY"))
        self.assertFalse(is_direction_allowed("Ladder Volatility Up Index", "SELL"))
        with patch.dict(os.environ, {"DAEMONBLACKFX_LADDER_DIRECTION_POLICY": "0"}):
            self.assertIsNone(get_symbol_direction_policy("Ladder Volatility Down Index").allowed_direction)

    def test_portfolio_daily_drawdown_gate_blocks_when_exceeded(self):
        engine = object.__new__(LiveTradingEngine)
        engine.config = LiveTradingConfig(source="DEMO", bot_profile="ICT", magic=26082032)
        engine.repository = MagicMock()
        engine.repository.get_daily_closed_trades_summary.return_value = {
            "daily_return_pct": -3.25,
            "today_net_pnl": -325.0,
        }
        engine._persist_audit_event = MagicMock()
        with patch.dict(
            os.environ,
            {"DAEMONBLACKFX_PORTFOLIO_CIRCUIT_BREAKER_ENABLED": "1", "DAEMONBLACKFX_MAX_DAILY_DRAWDOWN_PCT": "3.0"},
        ):
            gate = engine._portfolio_daily_drawdown_gate("XAUUSD")
        self.assertIsNotNone(gate)
        self.assertEqual(gate["action"], "PORTFOLIO_DAILY_DD_CIRCUIT_BREAKER_BLOCKED")
        self.assertIn("-3.25%", gate["reason"])

        # Desactivado por interruptor -> permite paso
        with patch.dict(os.environ, {"DAEMONBLACKFX_PORTFOLIO_CIRCUIT_BREAKER_ENABLED": "0"}):
            self.assertIsNone(engine._portfolio_daily_drawdown_gate("XAUUSD"))

    def test_db_maintenance_dry_run_and_apply(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / "test.sqlite3"
            con = sqlite3.connect(str(db))
            con.execute("CREATE TABLE daemon_audit_events (id INTEGER PRIMARY KEY, event_time TEXT)")
            con.execute("CREATE TABLE trade_audit_snapshots (id INTEGER PRIMARY KEY, snapshot_at TEXT)")
            con.execute("CREATE TABLE trade_visual_audits (id INTEGER PRIMARY KEY, source TEXT, bot_profile TEXT, daemon_magic INTEGER)")
            con.execute("CREATE TABLE worker_runtime_states (id INTEGER PRIMARY KEY, bot_profile TEXT, status TEXT, last_action TEXT)")
            con.execute("INSERT INTO daemon_audit_events (event_time) VALUES ('2025-01-01 00:00:00'), ('2099-01-01 00:00:00')")
            con.execute("INSERT INTO trade_audit_snapshots (snapshot_at) VALUES ('2025-01-01 00:00:00'), ('2099-01-01 00:00:00')")
            con.execute("INSERT INTO trade_visual_audits (source, bot_profile, daemon_magic) VALUES ('MT5_EXTERNAL', 'BOOM', 26082101)")
            con.execute("INSERT INTO worker_runtime_states (bot_profile, status, last_action) VALUES ('MALAYSIAN_SNR', 'RUNNING', 'WAITING')")
            con.commit()
            con.close()

            dry = inspect_database(db, retention_days=30)
            self.assertEqual(dry["targets"]["daemon_audit_events"]["purgeable_rows"], 1)
            self.assertEqual(dry["targets"]["trade_audit_snapshots"]["purgeable_rows"], 1)
            self.assertEqual(dry["stale_audit"]["mt5_external_misattributed_visual_audits"], 1)
            self.assertEqual(dry["stale_audit"]["retired_workers_stuck_running"], 1)

            res = apply_maintenance(db, retention_days=30, run_vacuum=True, clean_stale_audit=True)
            self.assertEqual(res["deleted"]["daemon_audit_events"], 1)
            self.assertEqual(res["deleted"]["trade_audit_snapshots"], 1)
            self.assertEqual(res["cleaned"]["trade_visual_audits_reattributed"], 1)
            self.assertEqual(res["cleaned"]["retired_workers_stopped"], 1)
            self.assertEqual(res["targets"]["daemon_audit_events"]["total_rows"], 1)


if __name__ == "__main__":
    unittest.main()
