
import inspect
from pathlib import Path
import app.main as main

def test_synthetics_split_launcher_enables_dashboard():
    root=Path(__file__).resolve().parents[1]
    text=(root/"run_synthetics_split.bat").read_text(encoding="utf-8")
    assert "--mode synthetics-split-daemon" in text
    assert "--dashboard" in text
    assert "--dashboard-port 8765" in text

def test_coordinator_dashboard_is_not_conditional_on_dashboard_flag():
    source=inspect.getsource(main.run_multi_bot_daemon)
    assert "coordinator_dashboard_enabled = True" in source
    assert "if coordinator_dashboard_enabled:" in source

def test_workers_still_do_not_start_individual_dashboards():
    source=inspect.getsource(main.run_multi_bot_daemon)
    assert '"--coordinated-worker"' in source
    run_source=inspect.getsource(main.main)
    assert "dashboard=(args.dashboard and not args.coordinated_worker)" in run_source

def test_split_profiles_are_exactly_six():
    assert tuple(main.SYNTHETIC_SPLIT_PROFILES)==(
        "BOOM","CRASH","VOLATILITY","STEP","JUMP","FLIP"
    )

def test_coordinator_starts_and_stops_one_central_dashboard():
    source=inspect.getsource(main.run_multi_bot_daemon)
    assert source.count("dashboard_service.start(live=True)") == 1
    assert "dashboard_service.stop()" in source
