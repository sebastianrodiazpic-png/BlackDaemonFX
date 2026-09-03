import sqlite3
from pathlib import Path

import database.database as dbmod
from database.repository import TradingRepository
from dashboard.account_metrics import build_account_payload


def _make_legacy_db(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    conn=sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE trade_journal (id INTEGER PRIMARY KEY)")
        conn.execute("CREATE TABLE trades (id INTEGER PRIMARY KEY)")
        conn.execute("CREATE TABLE account_snapshots (id INTEGER PRIMARY KEY)")
        conn.executemany("INSERT INTO trade_journal(id) VALUES (?)", [(1,), (2,), (3,)])
        conn.executemany("INSERT INTO trades(id) VALUES (?)", [(1,), (2,)])
        conn.execute("INSERT INTO account_snapshots(id) VALUES (1)")
        conn.commit()
    finally:
        conn.close()


def test_stable_db_recovers_nonempty_sibling_legacy_db(tmp_path, monkeypatch):
    current=tmp_path/"v63"
    current.mkdir()
    legacy=tmp_path/"v62"/"database"/"trading_bot.sqlite3"
    _make_legacy_db(legacy)
    stable=tmp_path/"stable"/"trading_bot.sqlite3"

    monkeypatch.setattr(dbmod, "PROJECT_ROOT", current)
    monkeypatch.setattr(dbmod, "LEGACY_PROJECT_DB_PATH", current/"database"/"trading_bot.sqlite3")

    result=dbmod._bootstrap_stable_database(stable)
    assert result["recovered"] is True
    assert Path(result["recovered_from"]) == legacy.resolve()
    assert dbmod._sqlite_activity_score(stable) == (3,2,1,6)


def test_nonempty_stable_db_is_never_overwritten(tmp_path, monkeypatch):
    current=tmp_path/"v63"; current.mkdir()
    stable=tmp_path/"stable"/"trading_bot.sqlite3"
    _make_legacy_db(stable)
    other=tmp_path/"v62"/"database"/"trading_bot.sqlite3"
    _make_legacy_db(other)

    monkeypatch.setattr(dbmod, "PROJECT_ROOT", current)
    result=dbmod._bootstrap_stable_database(stable)
    assert result["recovered"] is False
    assert dbmod._sqlite_activity_score(stable)[-1] == 6


def test_repository_exposes_exact_database_path(tmp_path):
    path=tmp_path/"account.db"
    repo=TradingRepository(db_path=path)
    info=repo.database_diagnostics()
    assert Path(info["path"]) == path.resolve()
    assert info["exists"] is True


def test_account_payload_reports_database_diagnostics(tmp_path):
    repo=TradingRepository(db_path=tmp_path/"account.db")
    payload=build_account_payload(repo)
    assert payload["database"]["path"].endswith("account.db")
    assert "trade_rows" in payload["database"]
    assert "account_snapshot_rows" in payload["database"]


def test_account_page_displays_sqlite_path():
    root=Path(__file__).resolve().parents[1]
    text=(root/"dashboard"/"account_page.py").read_text(encoding="utf-8")
    assert 'id="dbpath"' in text
    assert "SQLite:" in text
    assert "RECUPERADA DESDE" in text
