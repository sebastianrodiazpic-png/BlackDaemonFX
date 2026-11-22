"""Congelación de reinicios del coordinador durante la sesión (app/restart_freeze.py, 11-nov-2026)."""
import json
import os
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.restart_freeze import HISTORY_FILE, check_and_record, evaluate, in_windows, parse_windows

SESSION = datetime(2026, 11, 11, 13, 0, tzinfo=timezone.utc)       # killzone de NY: fuera de mantenimiento
MAINTENANCE = datetime(2026, 11, 11, 21, 30, tzinfo=timezone.utc)   # dentro de 21:00-23:00 UTC
WINDOWS = parse_windows("21:00-23:00")


def _eval(now, *, mode="warn", idle=5.0, history=(), override=False, max_per_day=1):
    last = None if idle is None else now - timedelta(minutes=idle)
    return evaluate(now, mode=mode, windows=WINDOWS, last_activity=last, history=list(history),
                    lookback_minutes=30, max_per_day=max_per_day, override=override)


def test_parse_and_window_membership():
    assert parse_windows("21:00-23:00, 05:30-06:00") == [(1260, 1380), (330, 360)]
    assert parse_windows("basura,25:00-26:00,10:00-10:00,") == []
    assert in_windows(MAINTENANCE, WINDOWS) and not in_windows(SESSION, WINDOWS)
    assert not in_windows(MAINTENANCE.replace(hour=23, minute=0), WINDOWS)          # fin exclusivo
    night = parse_windows("22:00-01:00")                                            # cruza medianoche
    assert in_windows(SESSION.replace(hour=23), night) and in_windows(SESSION.replace(hour=0, minute=30), night)
    assert not in_windows(SESSION.replace(hour=1), night)


def test_cold_start_is_always_allowed():
    for mode in ("warn", "enforce"):
        assert _eval(SESSION, mode=mode, idle=None)["decision"] == "ALLOW"          # sin logs previos
        out = _eval(SESSION, mode=mode, idle=45.0)                                   # bot parado > 30 min
        assert out["decision"] == "ALLOW" and out["reason"] == "COLD_START" and out["is_restart"] is False


def test_restart_in_session_warns_by_default_and_blocks_in_enforce():
    warn = _eval(SESSION)
    assert warn["decision"] == "WARN" and warn["reason"] == "RESTART_OUTSIDE_MAINTENANCE_WINDOW"
    block = _eval(SESSION, mode="enforce")
    assert block["decision"] == "BLOCK" and block["is_restart"] is True
    allowed = _eval(SESSION, mode="enforce", override=True)
    assert allowed["decision"] == "WARN" and allowed["reason"].endswith("_OVERRIDDEN")
    assert _eval(SESSION, mode="off")["decision"] == "ALLOW"
    assert _eval(SESSION, mode="valor-raro")["mode"] == "warn"


def test_restart_in_maintenance_window_is_allowed_until_daily_limit():
    assert _eval(MAINTENANCE, mode="enforce")["reason"] == "RESTART_IN_MAINTENANCE_WINDOW"
    previous = [{"at": (MAINTENANCE - timedelta(hours=1)).isoformat(), "is_restart": True, "decision": "ALLOW"}]
    out = _eval(MAINTENANCE, mode="enforce", history=previous)
    assert out["decision"] == "BLOCK" and out["reason"] == "RESTART_LIMIT_PER_DAY_REACHED"
    # Los intentos bloqueados y los arranques en frío no cuentan; 0 = sin límite diario.
    ignored = [{"at": "x", "is_restart": True, "decision": "BLOCK"}, {"at": "x", "is_restart": False, "decision": "ALLOW"}]
    assert _eval(MAINTENANCE, mode="enforce", history=ignored)["decision"] == "ALLOW"
    assert _eval(MAINTENANCE, mode="enforce", history=previous, max_per_day=0)["decision"] == "ALLOW"


def _project(idle_minutes, now):
    root = Path(tempfile.mkdtemp(prefix="restart_freeze_"))
    logs = root / "storage" / "logs" / "bots"
    logs.mkdir(parents=True)
    if idle_minutes is not None:
        log = logs / "ict.log"
        log.write_text("x", encoding="utf-8")
        stamp = (now - timedelta(minutes=idle_minutes)).timestamp()
        os.utime(log, (stamp, stamp))
    return root


def test_check_and_record_writes_history_and_counts_previous_restarts():
    root = _project(3, SESSION)
    first = check_and_record(root, now_utc=SESSION, env={})
    assert first["decision"] == "WARN" and first["restarts_last_24h"] == 0 and "AVISO" in first["message"]
    second = check_and_record(root, now_utc=SESSION + timedelta(minutes=10), env={})
    assert second["restarts_last_24h"] == 1
    rows = [json.loads(line) for line in (root / "storage" / "runtime" / HISTORY_FILE).read_text("utf-8").splitlines()]
    assert len(rows) == 2 and "message" not in rows[0] and rows[0]["maintenance_utc"] == "21:00-23:00"


def test_check_and_record_enforce_override_and_off():
    env = {"DAEMONBLACKFX_RESTART_FREEZE": "enforce"}
    root = _project(3, SESSION)
    blocked = check_and_record(root, now_utc=SESSION, env=env)
    assert blocked["decision"] == "BLOCK" and "ARRANQUE CANCELADO" in blocked["message"]
    allowed = check_and_record(root, now_utc=SESSION, env={**env, "DAEMONBLACKFX_RESTART_FREEZE_OVERRIDE": "1"})
    assert allowed["decision"] == "WARN" and allowed["restarts_last_24h"] == 0    # el intento bloqueado no cuenta
    custom = check_and_record(root, now_utc=SESSION, env={**env, "DAEMONBLACKFX_RESTART_MAINTENANCE_UTC": "12:00-14:00",
                                                          "DAEMONBLACKFX_RESTART_MAX_PER_DAY": "5"})
    assert custom["decision"] == "ALLOW"
    off_root = _project(3, SESSION)
    assert check_and_record(off_root, now_utc=SESSION, env={"DAEMONBLACKFX_RESTART_FREEZE": "off"})["decision"] == "ALLOW"
    assert not (off_root / "storage" / "runtime" / HISTORY_FILE).exists()
    cold = _project(None, SESSION)
    assert check_and_record(cold, now_utc=SESSION, env=env)["reason"] == "COLD_START"


def test_main_cancels_start_only_on_block(monkeypatch):
    import app.main as main
    import app.restart_freeze as freeze

    released = []
    guard = type("Guard", (), {"release": lambda self: released.append(True)})()
    monkeypatch.setattr(freeze, "check_and_record", lambda root: {"decision": "WARN", "is_restart": True, "message": "m"})
    assert main._apply_restart_freeze(guard)["decision"] == "WARN" and not released
    monkeypatch.setattr(freeze, "check_and_record", lambda root: {"decision": "BLOCK", "is_restart": True, "message": "m"})
    with pytest.raises(SystemExit):
        main._apply_restart_freeze(guard)
    assert released == [True]

    def broken(root):
        raise RuntimeError("fallo interno")
    monkeypatch.setattr(freeze, "check_and_record", broken)
    assert main._apply_restart_freeze(guard) is None                               # nunca impide arrancar
