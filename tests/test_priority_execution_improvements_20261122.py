import unittest
from unittest.mock import MagicMock
from datetime import datetime, timezone
import tempfile
import os

from strategy.execution.active_position_guard import (
    terminal_execution_lock,
    is_terminal_in_flight,
    record_terminal_in_flight,
    _IN_FLIGHT_CACHE,
    _IN_FLIGHT_MUTEX,
)
from strategy.execution.live_trading_engine import (
    LiveTradingEngine,
    LiveTradingConfig,
)
from database.repository import TradingRepository
from database.models import Base, Trade
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from strategy.ai.meta_labeling import (
    MetaLabelingConfig,
    MetaLabelingEngine,
)


class TestPriorityExecutionImprovements20261122(unittest.TestCase):
    """Pruebas unitarias de las 4 mejoras prioritarias (Puntos 2, 4, 6 y 7)."""

    def setUp(self):
        # Limpiar cache in-flight
        with _IN_FLIGHT_MUTEX:
            _IN_FLIGHT_CACHE.clear()

    # =========================================================================
    # PUNTO 2: Lock Global Terminal MT5 e In-Flight Barrier
    # =========================================================================
    def test_terminal_in_flight_barrier(self):
        """Verifica que record_terminal_in_flight marque el símbolo como en vuelo."""
        symbol = "EURUSD"
        self.assertFalse(is_terminal_in_flight(symbol))

        # Registrar orden en vuelo con ticket
        record_terminal_in_flight(symbol, 123456)
        self.assertTrue(is_terminal_in_flight(symbol))

        # Otro símbolo debe permanecer libre
        self.assertFalse(is_terminal_in_flight("GBPUSD"))

    def test_terminal_execution_lock_context(self):
        """Verifica que terminal_execution_lock adquiera y libere el context manager."""
        with terminal_execution_lock("EURUSD", timeout_seconds=1.0) as acquired:
            self.assertTrue(acquired)

    # =========================================================================
    # PUNTO 4: Restricción Horaria Centinela en Cruce Londres/NY (13:00-14:59 UTC)
    # =========================================================================
    def test_london_ny_crossover_sentinel_blocks_during_window(self):
        """Verifica bloqueo de Forex entre 13:00 y 14:59 UTC y pase fuera de la ventana."""
        config = LiveTradingConfig(
            london_ny_crossover_filter_enabled=True,
            london_ny_crossover_start_utc_hour=13,
            london_ny_crossover_end_utc_hour=15,
            london_ny_crossover_apply_to_synthetics=False,
            bot_profile="FOREX_1",
        )
        engine = object.__new__(LiveTradingEngine)
        engine.config = config

        # 13:30 UTC: Dentro de la ventana -> Debe ser bloqueado
        t_blocked = datetime(2026, 11, 23, 13, 30, tzinfo=timezone.utc)
        res = engine._london_ny_crossover_sentinel_gate("EURUSD", now_utc=t_blocked)
        self.assertIsNotNone(res)
        self.assertEqual(res["action"], "LONDON_NY_CROSSOVER_FILTER_BLOCKED")

        # 12:59 UTC: Antes de la ventana -> Debe permitirse (None)
        t_allowed_before = datetime(2026, 11, 23, 12, 59, tzinfo=timezone.utc)
        self.assertIsNone(engine._london_ny_crossover_sentinel_gate("EURUSD", now_utc=t_allowed_before))

        # 15:01 UTC: Después de la ventana -> Debe permitirse (None)
        t_allowed_after = datetime(2026, 11, 23, 15, 1, tzinfo=timezone.utc)
        self.assertIsNone(engine._london_ny_crossover_sentinel_gate("EURUSD", now_utc=t_allowed_after))

    def test_london_ny_crossover_sentinel_exemptions(self):
        """Verifica que ORB y Sintéticos queden exentos del bloqueo horario."""
        # Configuración ORB
        config_orb = LiveTradingConfig(
            london_ny_crossover_filter_enabled=True,
            london_ny_crossover_start_utc_hour=13,
            london_ny_crossover_end_utc_hour=15,
            bot_profile="ORB",
        )
        engine_orb = object.__new__(LiveTradingEngine)
        engine_orb.config = config_orb

        t_crossover = datetime(2026, 11, 23, 14, 0, tzinfo=timezone.utc)
        # ORB profile no debe bloquearse en EURUSD o índices
        self.assertIsNone(engine_orb._london_ny_crossover_sentinel_gate("EURUSD", now_utc=t_crossover))

        # Sintéticos no deben bloquearse si london_ny_crossover_apply_to_synthetics=False
        config_forex = LiveTradingConfig(
            london_ny_crossover_filter_enabled=True,
            london_ny_crossover_apply_to_synthetics=False,
            bot_profile="SYNTHETICS_1",
        )
        engine_synth = object.__new__(LiveTradingEngine)
        engine_synth.config = config_forex
        self.assertIsNone(engine_synth._london_ny_crossover_sentinel_gate("Volatility 75 Index", now_utc=t_crossover))

    # =========================================================================
    # PUNTO 6: Deduplicación SQLite y Reconciliación PnL Emergencia
    # =========================================================================
    def test_create_trade_once_deduplicates_by_position_ticket_across_sources(self):
        """Verifica que create_trade_once no cree duplicados del mismo broker ticket bajo distinto source."""
        temp_db = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
        temp_db.close()
        try:
            repo = TradingRepository(f"sqlite:///{temp_db.name}")

            # 1. Insertar posición bajo source='DEMO' (ej. importación previa de MT5)
            t1_id, created1 = repo.create_trade_once({
                "instrument": "EURUSD",
                "direction": "BUY",
                "source": "DEMO",
                "broker_position_ticket": "999888",
                "entry_price": 1.0850,
                "volume": 0.10,
                "status": "OPEN",
            })
            self.assertTrue(created1)

            # 2. Worker intenta insertar la misma posición con source='FOREX_1'
            t2_id, created2 = repo.create_trade_once({
                "instrument": "EURUSD",
                "direction": "BUY",
                "source": "FOREX_1",
                "broker_position_ticket": "999888",
                "entry_price": 1.0850,
                "volume": 0.10,
                "status": "OPEN",
            })
            self.assertFalse(created2)
            self.assertEqual(t1_id, t2_id)

            # Verificar que no existen 2 filas
            with repo.Session() as session:
                count = session.query(Trade).filter(Trade.broker_position_ticket == "999888").count()
                self.assertEqual(count, 1)
        finally:
            if os.path.exists(temp_db.name):
                os.remove(temp_db.name)

    def test_reconcile_emergency_trades(self):
        """Verifica que reconcile_emergency_trades actualice el PnL con deals reales de MT5."""
        temp_db = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
        temp_db.close()
        try:
            repo = TradingRepository(f"sqlite:///{temp_db.name}")

            # Crear trade cerrado de emergencia con PnL en 0.0
            t_id = repo.create_trade({
                "instrument": "EURUSD",
                "direction": "BUY",
                "source": "FOREX_1",
                "broker_position_ticket": "777666",
                "entry_price": 1.0850,
                "volume": 0.10,
                "risk_amount": 50.0,
                "status": "CLOSED",
                "net_pnl": 0.0,
                "exit_reason": "emergency_risk_exit",
            })

            # Mock executor con deals reales
            deal_mock = MagicMock()
            deal_mock.profit = 75.0
            deal_mock.commission = -2.0
            deal_mock.swap = 0.0
            deal_mock.entry = 1  # deal de salida
            deal_mock.price = 1.0880
            deal_mock.time = int(datetime.now(timezone.utc).timestamp())
            deal_mock.ticket = 12345

            mock_executor = MagicMock()
            mock_executor.history_for_position.return_value = [deal_mock]

            reconciled = repo.reconcile_emergency_trades(mock_executor)
            self.assertEqual(reconciled, 1)

            # Verificar datos actualizados
            trade_updated = repo.get_trade(t_id)
            self.assertEqual(trade_updated["net_pnl"], 73.0)  # 75 - 2
            self.assertEqual(trade_updated["result"], "WIN")
            self.assertAlmostEqual(trade_updated["realized_rr"], 73.0 / 50.0, places=2)
        finally:
            if os.path.exists(temp_db.name):
                os.remove(temp_db.name)

    def test_deduplicate_trades(self):
        """Verifica que deduplicate_trades fusione y elimine filas duplicadas por broker_position_ticket."""
        temp_db = tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False)
        temp_db.close()
        try:
            repo = TradingRepository(f"sqlite:///{temp_db.name}")

            # Insertar dos filas para el mismo ticket usando create_trade directo
            t1 = repo.create_trade({
                "instrument": "EURUSD",
                "direction": "BUY",
                "source": "DEMO",
                "broker_position_ticket": "555444",
                "volume": 0.10,
                "status": "OPEN",
                "net_pnl": 0.0,
            })
            t2 = repo.create_trade({
                "instrument": "EURUSD",
                "direction": "BUY",
                "source": "FOREX_1",
                "broker_position_ticket": "555444",
                "volume": 0.10,
                "status": "CLOSED",
                "net_pnl": 45.0,
            })

            removed = repo.deduplicate_trades()
            self.assertEqual(removed, 1)

            # Debe quedar solo 1 fila con el PnL no nulo
            with repo.Session() as session:
                rows = session.query(Trade).filter(Trade.broker_position_ticket == "555444").all()
                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0].net_pnl, 45.0)
        finally:
            if os.path.exists(temp_db.name):
                os.remove(temp_db.name)

    # =========================================================================
    # PUNTO 7: Calibración Meta-Labeling LBDT (1:1 TP1)
    # =========================================================================
    def test_meta_labeling_split_tp1_resolution(self):
        """Verifica que el umbral de meta-labeling se calibre adecuadamente en split TP1."""
        config = MetaLabelingConfig(
            min_probability_forex=0.50,
            min_probability_gold=0.50,
            min_probability_volatility=0.47,
            split_tp1_min_probability=0.46,
            split_tp1_probability_adjustment_enabled=True,
        )
        engine_forex = MetaLabelingEngine(worker="FOREX_1", config=config)
        engine_synth = MetaLabelingEngine(worker="VOLATILITY", config=config)

        # En Forex estándar: 0.50
        self.assertEqual(engine_forex.resolve_min_probability("EURUSD", is_split_tp1=False), 0.50)
        # En Forex con Split TP1 (1:1): se adapta a 0.46
        self.assertEqual(engine_forex.resolve_min_probability("EURUSD", is_split_tp1=True), 0.46)

        # En Volatility estándar: 0.47
        self.assertEqual(engine_synth.resolve_min_probability("Volatility 75 Index", is_split_tp1=False), 0.47)
        # En Volatility Split TP1 (1:1): 0.46
        self.assertEqual(engine_synth.resolve_min_probability("Volatility 75 Index", is_split_tp1=True), 0.46)


if __name__ == "__main__":
    unittest.main()
