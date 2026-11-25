import datetime
import os
import sqlite3
import tempfile
import unittest

from tools.maintenance.archive_heavy_tables import run_maintenance, PROTECTED_TABLES


class TestArchiveHeavyTables(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.live_db = os.path.join(self.temp_dir.name, "test_live.sqlite3")
        self.archive_db = os.path.join(self.temp_dir.name, "test_archive.sqlite3")

        conn = sqlite3.connect(self.live_db)
        cur = conn.cursor()

        # Tabla protegida: trades
        cur.execute("""
            CREATE TABLE trades (
                id INTEGER PRIMARY KEY,
                instrument TEXT,
                created_at TEXT
            )
        """)

        # Tablas pesadas: daemon_audit_events, account_snapshots
        cur.execute("""
            CREATE TABLE daemon_audit_events (
                id INTEGER PRIMARY KEY,
                event_type TEXT,
                created_at TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE account_snapshots (
                id INTEGER PRIMARY KEY,
                balance REAL,
                snapshot_time TEXT
            )
        """)

        now = datetime.datetime.now(datetime.timezone.utc)
        old_date = (now - datetime.timedelta(days=20)).isoformat()
        recent_date = (now - datetime.timedelta(days=2)).isoformat()

        # Insertar trades (no deben borrarse nunca)
        cur.execute("INSERT INTO trades VALUES (1, 'EURUSD', ?)", (old_date,))
        cur.execute("INSERT INTO trades VALUES (2, 'GBPUSD', ?)", (recent_date,))

        # Insertar daemon_audit_events: 10 antiguos, 5 recientes
        for i in range(1, 11):
            cur.execute("INSERT INTO daemon_audit_events VALUES (?, 'OLD_EVENT', ?)", (i, old_date))
        for i in range(11, 16):
            cur.execute("INSERT INTO daemon_audit_events VALUES (?, 'RECENT_EVENT', ?)", (i, recent_date))

        # Insertar account_snapshots: 5 antiguos, 5 recientes
        for i in range(1, 6):
            cur.execute("INSERT INTO account_snapshots VALUES (?, 1000.0, ?)", (i, old_date))
        for i in range(6, 11):
            cur.execute("INSERT INTO account_snapshots VALUES (?, 1050.0, ?)", (i, recent_date))

        conn.commit()
        conn.close()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_protected_tables_are_never_purged(self):
        """Verifica que las tablas protegidas nunca sean tocadas."""
        summary = run_maintenance(
            live_db_path=self.live_db,
            archive_db_path=self.archive_db,
            retention_overrides={"trades": 1},  # intentar forzar
            batch_size=10,
            do_vacuum=False,
        )

        conn = sqlite3.connect(self.live_db)
        trades_count = conn.execute("SELECT count(*) FROM trades").fetchone()[0]
        conn.close()

        self.assertEqual(trades_count, 2)  # Ambas operaciones permanecen intactas

    def test_heavy_tables_are_archived_and_purged(self):
        """Verifica que registros de más de 7 días se archiven y se purguen de la base viva."""
        summary = run_maintenance(
            live_db_path=self.live_db,
            archive_db_path=self.archive_db,
            retention_overrides={"daemon_audit_events": 7, "account_snapshots": 7},
            batch_size=5,
            do_vacuum=False,
        )

        live_conn = sqlite3.connect(self.live_db)
        live_events = live_conn.execute("SELECT count(*) FROM daemon_audit_events").fetchone()[0]
        live_snapshots = live_conn.execute("SELECT count(*) FROM account_snapshots").fetchone()[0]
        live_conn.close()

        # En la base viva solo deben quedar los 5 recientes de cada una
        self.assertEqual(live_events, 5)
        self.assertEqual(live_snapshots, 5)

        # En la base de archivo deben estar los 10 antiguos de eventos y 5 antiguos de snapshots
        archive_conn = sqlite3.connect(self.archive_db)
        archived_events = archive_conn.execute("SELECT count(*) FROM daemon_audit_events").fetchone()[0]
        archived_snapshots = archive_conn.execute("SELECT count(*) FROM account_snapshots").fetchone()[0]
        archive_conn.close()

        self.assertEqual(archived_events, 10)
        self.assertEqual(archived_snapshots, 5)

        # Resumen correcto
        self.assertEqual(summary["total_purged_rows"], 15)


if __name__ == "__main__":
    unittest.main()
