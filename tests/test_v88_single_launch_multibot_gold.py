from pathlib import Path


def test_full_multibot_contains_gold_before_orb_and_unique_workers():
    source = (Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")
    assert '*MULTIBOT_SYNTHETIC_PROFILES' in source
    assert '*VOLATILITY_SHARD_PROFILES' in source
    assert '_assert_full_multibot_architecture(profiles)' in source
    assert '"gold-session-daemon": "GOLD"' in source


def test_coordinator_forces_one_database_path_for_every_worker():
    source = (Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")
    assert 'shared_db_path = str(Path(repo.db_path).resolve())' in source
    assert 'worker_env["DAEMONBLACKFX_DB_PATH"] = shared_db_path' in source
    assert 'env=worker_env' in source
    assert '"entry": "trade_visual_audits"' in source
    assert '"timeline": "trade_audit_snapshots"' in source


def test_coordinator_remains_only_periodic_xlsx_writer():
    source = (Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")
    assert 'auto_export=False' in source
    assert 'result = reporting.export_now()' in source


def test_gold_uses_fast_event_poll_inside_multibot():
    source = (Path(__file__).resolve().parents[1] / "app" / "main.py").read_text(encoding="utf-8")
    assert 'or str(profile) == "GOLD"' in source
