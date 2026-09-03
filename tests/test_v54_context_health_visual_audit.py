
from database.repository import TradingRepository
from dashboard.realtime_dashboard import (
    RealtimeDashboardService,
    _infer_symbol_profile,
    _position_owner,
)


def test_symbol_owner_inference_by_family():
    assert _infer_symbol_profile("Boom 500 Index") == "BOOM"
    assert _infer_symbol_profile("Crash 150 Index") == "CRASH"
    assert _infer_symbol_profile("Volatility 75 Index") == "VOLATILITY"
    assert _infer_symbol_profile("Step Index 200") == "STEP"
    assert _infer_symbol_profile("Jump 100 Index") == "JUMP"
    assert _infer_symbol_profile("Crash Boom Flip 500 Index") == "FLIP"
    assert _infer_symbol_profile("GBPAUD") == "FOREX"
    assert _infer_symbol_profile("XAUUSDmicro") == "ORB"


def test_legacy_daemon_magic_infers_correct_owner():
    trade={"source":"DEMO","instrument":"Crash 150 Index"}
    metadata={"daemon_magic":26082026}
    owner=_position_owner(trade,metadata)
    assert owner["managed_by_daemon"] is True
    assert owner["owner_profile"]=="CRASH"
    assert owner["ownership_status"]=="LEGACY_INFERIDA"


def test_external_with_known_daemon_magic_is_flagged_for_reconciliation():
    trade={"source":"MT5_EXTERNAL","instrument":"Jump 100 Index"}
    metadata={"daemon_magic":26082105}
    owner=_position_owner(trade,metadata)
    assert owner["managed_by_daemon"] is False
    assert owner["owner_profile"]=="JUMP"
    assert owner["ownership_status"]=="MAGIC_DAEMON_PERO_SOURCE_EXTERNA"


def test_visual_audit_roundtrip(tmp_path):
    repo=TradingRepository(db_path=tmp_path/"visual.db")
    repo.upsert_position_visual_audit(
        "Boom 500 Index",
        {"timeframes":{"M5":{"candles":[{"time":"2026-08-31T12:00:00Z","open":1,"high":2,"low":0,"close":1.5}]}}},
        market={"trade_id":12,"current_price":1.5,"current_rr":0.75},
        bot_profile="BOOM",
        daemon_magic=26082101,
        source="DEMO",
    )
    rows=repo.position_visual_audits("DEMO")
    assert len(rows)==1
    assert rows[0]["bot_profile"]=="BOOM"
    assert rows[0]["market"]["current_rr"]==0.75
    assert rows[0]["chart"]["timeframes"]["M5"]["candles"]


def test_latest_worker_candidate_is_read_from_append_only_audit(tmp_path):
    repo=TradingRepository(db_path=tmp_path/"candidate.db")
    repo.save_audit_event(
        "SYMBOL_PROCESS_RESULT",
        source="DEMO",
        instrument="EURUSD",
        action="NO_SIGNAL",
        cycle_number=7,
        payload={
            "bot_profile":"FOREX",
            "daemon_magic":26082027,
            "result":{
                "symbol":"EURUSD",
                "score":87,
                "confirmation_percentage":0.86,
                "direction":"BUY",
                "reason":"WAITING_M5",
            },
        },
    )
    rows=repo.latest_worker_process_results("DEMO")
    assert rows["FOREX"]["symbol"]=="EURUSD"
    assert rows["FOREX"]["score"]==87
    assert rows["FOREX"]["_cycle_number"]==7


def test_dashboard_snapshot_exposes_worker_candidates_and_visual_health(tmp_path):
    repo=TradingRepository(db_path=tmp_path/"dash.db")
    repo.save_audit_event(
        "SYMBOL_PROCESS_RESULT",
        source="DEMO",
        instrument="Jump 100 Index",
        action="WAITING",
        payload={
            "bot_profile":"JUMP",
            "daemon_magic":26082105,
            "result":{"symbol":"Jump 100 Index","score":90},
        },
    )
    repo.upsert_worker_runtime_state(
        "JUMP",26082105,source="DEMO",status="RUNNING",pid=999,
        cycle_number=2,symbols_total=5,symbols_processed=2,current_symbol="Jump 100 Index"
    )
    service=RealtimeDashboardService(repository=repo,port=0,state_path=tmp_path/"state.json")
    snap=service.snapshot()
    assert snap["worker_candidates"]["JUMP"]["symbol"]=="Jump 100 Index"


def test_dashboard_html_has_context_tabs_and_owner_column():
    from dashboard import realtime_dashboard as rd
    assert "Último candidato analizado · contexto por bot" in rd._HTML
    assert 'id="candidateBotTabs"' in rd._HTML
    assert "Bot / Owner" in rd._HTML
    assert "telemetría por owner/worker" in rd._HTML
