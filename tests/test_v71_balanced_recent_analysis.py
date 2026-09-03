import json
from pathlib import Path

from database.repository import TradingRepository
from database.models import DaemonAuditEvent


def _event(session, profile, symbol, action, magic):
    payload={"bot_profile":profile,"daemon_magic":magic,
             "result":{"symbol":symbol,"action":action}}
    session.add(DaemonAuditEvent(
        event_type="SYMBOL_PROCESS_RESULT",
        source="DEMO",
        instrument=symbol,
        action=action,
        payload_json=json.dumps(payload),
    ))


def test_orb_flood_does_not_hide_forex_or_synthetics(tmp_path):
    repo=TradingRepository(db_path=tmp_path/"v71.db")
    with repo.Session() as session:
        for i in range(80):
            _event(session,"ORB",f"XAUUSD{i%4}","WAITING_NEW_YORK_OPEN",26082028)
        _event(session,"FOREX_1","EURUSD","NO_M15_SETUP",26082201)
        _event(session,"BOOM","Boom 1000 Index","WAITING_M5",26082101)
        session.commit()

    rows=repo.recent_symbol_process_results(
        source="DEMO",limit=120,per_profile=12,scan_limit=2500
    )
    profiles={r["_bot_profile"] for r in rows}
    assert "ORB" in profiles
    assert "FOREX_1" in profiles
    assert "BOOM" in profiles


def test_profile_is_inferred_from_magic_when_payload_profile_missing():
    profile=TradingRepository._infer_audit_profile(
        {"daemon_magic":26082203},
        {"symbol":"EURCHF","action":"STALE_M5_SIGNAL"},
        "EURCHF",
    )
    assert profile=="FOREX_3"


def test_profile_is_inferred_from_symbol_for_old_synthetic_event():
    assert TradingRepository._infer_audit_profile({}, {"symbol":"Jump 75 Index"}, "Jump 75 Index")=="JUMP"


def test_recent_results_are_deduped_by_profile_symbol_action(tmp_path):
    repo=TradingRepository(db_path=tmp_path/"v71.db")
    with repo.Session() as session:
        for _ in range(10):
            _event(session,"ORB","XAUUSD","WAITING_NEW_YORK_OPEN",26082028)
        session.commit()
    rows=repo.recent_symbol_process_results(source="DEMO",limit=20,per_profile=12,scan_limit=100)
    orb=[r for r in rows if r["_bot_profile"]=="ORB" and r["symbol"]=="XAUUSD"]
    assert len(orb)==1


def test_dashboard_calls_balanced_repository():
    root=Path(__file__).resolve().parents[1]
    text=(root/"dashboard"/"realtime_dashboard.py").read_text(encoding="utf-8")
    assert "per_profile=12" in text
    assert "scan_limit=2500" in text
    assert "La vista se equilibra por worker" in text
