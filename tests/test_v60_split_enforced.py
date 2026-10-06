import inspect
import app.main as main

def test_legacy_synthetic_daemon_is_not_individual_worker():
    source=inspect.getsource(main.main)
    block=source[source.index("strategy_worker_modes"):source.index("if args.mode in strategy_worker_modes")]
    assert '"synthetic-daemon": "SYNTHETICS"' not in block

def test_historical_daemon_aliases_route_to_split():
    source=inspect.getsource(main.main)
    assert '"synthetics-split-daemon"' in source
    assert '"synthetic-daemon"' in source
    assert '"demo-daemon"' in source
    assert "SYNTHETIC_SPLIT_PROFILES" in source

def test_split_still_exact_six():
    assert tuple(main.SYNTHETIC_SPLIT_PROFILES)==(
        "BOOM","CRASH","VOLATILITY","STEP","JUMP","FLIP"
    )

def test_legacy_runtime_is_superseded_by_coordinator():
    source=inspect.getsource(main.run_multi_bot_daemon)
    assert '"SYNTHETICS"' in source
    assert 'status="SUPERSEDED"' in source
    assert 'last_action="REPLACED_BY_FAMILY_WORKERS"' in source

def test_family_architecture_guard_still_passes():
    assert main._assert_synthetic_split_architecture() is True
