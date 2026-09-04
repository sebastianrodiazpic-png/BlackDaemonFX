
from database.repository import TradingRepository
from dashboard.realtime_dashboard import RealtimeDashboardService


def test_worker_runtime_state_roundtrip(tmp_path):
    repo=TradingRepository(db_path=tmp_path/"worker.db")
    repo.upsert_worker_runtime_state(
        "BOOM",26082101,source="DEMO",status="RUNNING",pid=1234,
        cycle_number=3,symbols_total=8,symbols_processed=4,
        current_symbol="Boom 500 Index",last_action="ANALIZANDO",
        last_reason="M15_SETUP",last_elapsed_seconds=1.25,
        details={"bot_profile":"BOOM","result":{"action":"WAITING_M5"}},
    )
    rows=repo.worker_runtime_states(source="DEMO")
    assert len(rows)==1
    row=rows[0]
    assert row["bot_profile"]=="BOOM"
    assert row["daemon_magic"]==26082101
    assert row["cycle_number"]==3
    assert row["symbols_processed"]==4
    assert row["details"]["result"]["action"]=="WAITING_M5"


def test_dashboard_snapshot_exposes_workers(tmp_path):
    repo=TradingRepository(db_path=tmp_path/"dash.db")
    repo.upsert_worker_runtime_state(
        "VOLATILITY",26082103,source="DEMO",status="RUNNING",
        cycle_number=2,symbols_total=12,symbols_processed=7,
        current_symbol="Volatility 75 Index",
    )
    dashboard=RealtimeDashboardService(repository=repo,port=0,state_path=tmp_path/"state.json")
    snapshot=dashboard.snapshot()
    assert snapshot["multi_bot_mode"] is True
    assert snapshot["worker_states"][0]["bot_profile"]=="VOLATILITY"


def test_dashboard_snapshot_hides_retired_scalping_workers(tmp_path):
    repo=TradingRepository(db_path=tmp_path/"dash.db")
    repo.upsert_worker_runtime_state(
        "BOOM",26082101,source="DEMO",status="RUNNING",
    )
    repo.upsert_worker_runtime_state(
        "SCALP_BOOM",26082107,source="DEMO",status="DISABLED",
    )

    dashboard=RealtimeDashboardService(repository=repo,port=0,state_path=tmp_path/"state.json")
    snapshot=dashboard.snapshot()

    assert [row["bot_profile"] for row in snapshot["worker_states"]] == ["BOOM"]
    assert "SCALP_BOOM" not in snapshot["worker_candidates"]


def test_dashboard_html_contains_family_worker_grid():
    from dashboard import realtime_dashboard as rd
    assert 'id="workerGrid"' in rd._HTML
    for profile in ("BOOM","CRASH","VOLATILITY","STEP","JUMP","FLIP"):
        assert profile in rd._HTML


def test_dashboard_forwards_worker_enablement_to_coordinator(tmp_path):
    calls = []
    dashboard = RealtimeDashboardService(
        repository=None,
        port=0,
        state_path=tmp_path / "state.json",
    )
    dashboard.set_worker_controller(
        lambda profile, enabled: calls.append((profile, enabled)) or {
            "ok": True, "profile": profile, "enabled": enabled,
        }
    )

    result = dashboard.update_worker_enabled("orb", False)

    assert result["ok"] is True
    assert calls == [("ORB", False)]
