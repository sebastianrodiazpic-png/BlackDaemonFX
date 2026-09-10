from pathlib import Path

def test_multi_bot_default_returns_to_multiprocess_coordinator():
    root=Path(__file__).resolve().parents[1]
    text=(root/"app"/"main.py").read_text(encoding="utf-8")
    assert 'if args.mode == "multi-bot-daemon":' in text
    assert 'run_multi_bot_daemon(args, profiles=FULL_MULTI_BOT_PROFILES)' in text

def test_unified_multibot_is_explicit_experimental_mode_only():
    root=Path(__file__).resolve().parents[1]
    text=(root/"app"/"main.py").read_text(encoding="utf-8")
    assert 'if args.mode == "unified-multibot-daemon":' in text
    assert "[EXPERIMENTAL]" in text

def test_dashboard_has_short_full_snapshot_cache():
    root=Path(__file__).resolve().parents[1]
    text=(root/"dashboard"/"realtime_dashboard.py").read_text(encoding="utf-8")
    # v109: TTL subida de 1.5s a 4.0s (optimizacion de memoria del
    # coordinador) para acompanar el polling mas espaciado del navegador.
    assert "self._dashboard_snapshot_cache_ttl_seconds = 4.0" in text
    assert 'self._dashboard_snapshot_cache = {"at": 0.0, "payload": None}' in text

def test_browser_polling_is_reduced():
    root=Path(__file__).resolve().parents[1]
    dash=(root/"dashboard"/"realtime_dashboard.py").read_text(encoding="utf-8")
    account=(root/"dashboard"/"account_page.py").read_text(encoding="utf-8")
    # v109: polling espaciado de 2000/2500ms a 6000ms (optimizacion de
    # memoria del coordinador, ver checkpoint de rendimiento).
    assert "setInterval(refresh,6000)" in dash
    assert "setInterval(load,6000)" in dash
    assert "setInterval(go,2500)" in account

def test_orb_htf_context_is_preserved_after_rollback():
    root=Path(__file__).resolve().parents[1]
    text=(root/"strategy"/"execution"/"live_trading_engine.py").read_text(encoding="utf-8")
    assert "ORB_BREAKOUT_CONTRA_TENDENCIA_H1" in text
    assert "ORB_BREAKOUT_CONTRA_H1_Y_M15" in text
    assert "_orb_higher_timeframe_context" in text

def test_startup_warns_about_parallel_daemon_instances():
    root=Path(__file__).resolve().parents[1]
    text=(root/"app"/"main.py").read_text(encoding="utf-8")
    assert "def _warn_possible_parallel_daemon_instances" in text
    assert "Se detectaron otras instancias Python de DaemonBlackFx" in text
