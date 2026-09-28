from datetime import datetime, timezone
from dashboard.smc_trial import record, snapshot


def test_trial_deduplicates_stale_candidates_and_reports_modes(tmp_path):
    now = datetime(2026,9,17,15,tzinfo=timezone.utc)
    row = {"strategy_name":"SMC", "symbol":"XAUUSD", "action":"STALE_M5_SIGNAL", "signal_age":{"signal_time":"2026-09-17T03:00:00Z"}}
    for _ in range(2):
        record("GOLD", row, "H1_PRIMARY", "ATR_BOUNDED", tmp_path, now)
    worker = snapshot(tmp_path)["workers"][0]
    assert worker["evaluations"] == 2
    assert len(worker["stale_signals"]) == 1
    assert worker["policy"] == "H1_PRIMARY"
    assert worker["retest"] == "ATR_BOUNDED"


def test_trial_excludes_orb_and_surfaces_corrupt_files(tmp_path):
    record("ORB", {"strategy_name":"ORB_NEW_YORK"}, "H1_PRIMARY", "ATR_BOUNDED", tmp_path)
    assert snapshot(tmp_path)["workers"] == []
    (tmp_path / "bad.json").write_text("{")
    assert snapshot(tmp_path)["errors"]


def test_gold_groups_and_candidate_expiry(tmp_path):
    now = datetime(2026,9,18,15,tzinfo=timezone.utc)
    for symbol in ("XAUUSDmicro", "XAGUSD", "US SP 500"):
        row = {"strategy_name":"SMC", "symbol":symbol, "direction":"BUY", "action":"NO_M5_CONFIRMATION", "signal_age":{"signal_time":"2026-09-18T14:00:00Z"}}
        record("GOLD", row, "H1_PRIMARY", "ATR_BOUNDED", tmp_path, now)
        row["action"] = "STALE_M5_SIGNAL"
        record("GOLD", row, "H1_PRIMARY", "ATR_BOUNDED", tmp_path, now)
    worker = snapshot(tmp_path)["workers"][0]
    assert set(worker["groups"]) == {"ORO", "PLATA", "INDICES_Y_OTROS"}
    assert len(worker["candidates"]) == 3
    assert all(c["expired"] for c in worker["candidates"].values())
