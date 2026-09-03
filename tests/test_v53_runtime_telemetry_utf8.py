
import inspect
from pathlib import Path

from database.repository import TradingRepository
from app.main import _assert_v53_runtime_compatibility
from dashboard.realtime_dashboard import RealtimeDashboardService
from daemon_version import DAEMONBLACKFX_VERSION


def test_runtime_compatibility_guard_passes_on_clean_v53(tmp_path):
    repo = TradingRepository(db_path=tmp_path/"v53.db")
    _assert_v53_runtime_compatibility(repo)


def test_worker_state_survives_and_dashboard_exposes_version(tmp_path):
    repo = TradingRepository(db_path=tmp_path/"dash.db")
    repo.upsert_worker_runtime_state(
        "FOREX",26082027,source="DEMO",status="RUNNING",pid=777,
        cycle_number=4,symbols_total=6,symbols_processed=3,
        current_symbol="EURUSD",last_action="ANALIZANDO",
    )
    service = RealtimeDashboardService(
        repository=repo, port=0, state_path=tmp_path/"state.json"
    )
    snap=service.snapshot()
    assert snap["daemon_version"] == DAEMONBLACKFX_VERSION
    assert any(x["bot_profile"]=="FOREX" for x in snap["worker_states"])


def test_console_reporter_no_problematic_warning_symbols():
    root=Path(__file__).resolve().parents[1]
    text=(root/"reporting"/"console_reporting_service.py").read_text(encoding="utf-8")
    assert "⚠" not in text
    assert "≥" not in text


def test_runtime_persistence_happens_before_audit_save_in_source():
    from strategy.execution.live_trading_engine import LiveTradingEngine
    source=inspect.getsource(LiveTradingEngine._persist_audit_event)
    assert source.index("upsert_worker_runtime_state") < source.index("save_audit_event")


def test_coordinator_has_worker_console_summary():
    import app.main as main
    source=inspect.getsource(main.run_multi_bot_daemon)
    assert "[WORKERS]" in source
    assert "RUNTIME HEARTBEAT ERROR" in source
