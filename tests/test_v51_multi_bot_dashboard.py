
import inspect
from types import SimpleNamespace

import app.main as main


def test_multi_bot_daemon_accepts_dashboard_flags_via_args():
    params = inspect.signature(main.run_multi_bot_daemon).parameters
    assert "args" in params
    assert "profiles" in params


def test_dashboard_catalog_helper_exists():
    assert callable(main._build_multi_bot_dashboard_catalog)


def test_split_profiles_remain_same():
    assert set(main.SYNTHETIC_SPLIT_PROFILES) == {
        "BOOM", "CRASH", "VOLATILITY", "STEP", "JUMP", "FLIP"
    }


def test_coordinator_source_contains_single_dashboard_start():
    source = inspect.getsource(main.run_multi_bot_daemon)
    assert "RealtimeDashboardService" in source
    assert "dashboard_service.start(live=True)" in source
    assert "dashboard_service.stop()" in source
    assert "dashboard_port" in source
