import pytest
import sqlite3
from pathlib import Path
from tools.operator.db_optimizer import get_db_storage_stats, run_passive_checkpoint


def test_db_optimizer_stats(tmp_path: Path):
    db_file = tmp_path / "test_optimizer.sqlite3"
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("CREATE TABLE trades (id INTEGER PRIMARY KEY, symbol TEXT);")
    cur.execute("INSERT INTO trades (symbol) VALUES ('EURUSD'), ('XAUUSD');")
    conn.commit()
    conn.close()

    stats = get_db_storage_stats(db_file)
    assert stats["total_bytes"] > 0
    assert stats["table_counts"]["trades"] == 2
    assert "freelist_pages" in stats
    assert stats["fragmentation_percent"] >= 0.0


def test_db_optimizer_passive_checkpoint(tmp_path: Path):
    db_file = tmp_path / "test_wal_checkpoint.sqlite3"
    conn = sqlite3.connect(str(db_file))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("CREATE TABLE test (val TEXT);")
    conn.execute("INSERT INTO test VALUES ('ok');")
    conn.commit()
    conn.close()

    res = run_passive_checkpoint(db_file)
    assert res["status"] == "OK"
    assert "busy" in res
    assert "wal_pages" in res
