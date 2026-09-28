
import json
from datetime import datetime, timezone
from dashboard.quarantine_view import quarantine_snapshot

def test_manual_breach_is_visible_and_file_is_not_modified(tmp_path):
    path=tmp_path/"risk.json"
    raw=json.dumps({"XAGUSDmicro":{"reason":"POST_FILL_RISK_HARD_CAP_BREACH",
        "recoverable":False,"actual_risk_amount":34.9,"hard_risk_cap":33.35}})
    path.write_text(raw)
    result=quarantine_snapshot(path)
    assert result["items"][0]["status"]=="REVISION_MANUAL"
    assert result["items"][0]["actual_risk"]==34.9
    assert result["items"][0]["actions"]
    assert path.read_text()==raw

def test_expired_record_is_pending_not_silently_released(tmp_path):
    path=tmp_path/"risk.json"
    path.write_text(json.dumps({"TEST":{"recoverable":True,"expires_at":"2026-09-14T12:00:00Z"}}))
    result=quarantine_snapshot(path,datetime(2026,9,15,tzinfo=timezone.utc))
    assert result["items"][0]["status"]=="PENDIENTE_REEVALUACION"
    assert "TEST" in json.loads(path.read_text())

def test_read_error_is_not_shown_as_no_quarantine(tmp_path):
    path=tmp_path/"risk.json"
    path.write_text("bad json")
    assert quarantine_snapshot(path)["status"]=="ERROR"
