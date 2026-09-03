import json
from pathlib import Path

from database.repository import TradingRepository
from database.models import DaemonAuditEvent


def test_recent_symbol_process_results_keeps_multiple_profiles(tmp_path):
    repo=TradingRepository(db_path=tmp_path/"v70.db")
    with repo.Session() as session:
        session.add_all([
            DaemonAuditEvent(
                event_type="SYMBOL_PROCESS_RESULT", source="DEMO",
                instrument="Boom 1000 Index", action="WAITING",
                payload_json=json.dumps({"bot_profile":"BOOM","daemon_magic":26082101,
                                         "result":{"symbol":"Boom 1000 Index","action":"WAITING_M5"}}),
            ),
            DaemonAuditEvent(
                event_type="SYMBOL_PROCESS_RESULT", source="DEMO",
                instrument="EURUSD", action="WAITING",
                payload_json=json.dumps({"bot_profile":"FOREX_1","daemon_magic":26082201,
                                         "result":{"symbol":"EURUSD","action":"NO_M15_SETUP"}}),
            ),
            DaemonAuditEvent(
                event_type="SYMBOL_PROCESS_RESULT", source="DEMO",
                instrument="XAUUSD", action="WAITING",
                payload_json=json.dumps({"bot_profile":"ORB","daemon_magic":26082028,
                                         "result":{"symbol":"XAUUSD","action":"WAITING_NEW_YORK_OPEN"}}),
            ),
        ])
        session.commit()

    rows=repo.recent_symbol_process_results(source="DEMO",limit=20)
    profiles={r["_bot_profile"] for r in rows}
    assert {"BOOM","FOREX_1","ORB"}.issubset(profiles)


def test_dashboard_hides_superseded_but_keeps_db_history():
    root=Path(__file__).resolve().parents[1]
    text=(root/"dashboard"/"realtime_dashboard.py").read_text(encoding="utf-8")
    assert 'upper() != "SUPERSEDED"' in text
    assert 'recent_symbol_process_results(' in text
    assert 'limit=120' in text
    assert '<th>Bot</th><th>Instrumento</th>' in text


def test_recent_analysis_uses_sqlalchemy_as_authoritative_source():
    root=Path(__file__).resolve().parents[1]
    text=(root/"dashboard"/"realtime_dashboard.py").read_text(encoding="utf-8")
    assert 'state["recent"] = persisted_recent or list(self._recent)' in text
    assert "SQLAlchemy" in text
