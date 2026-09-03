import app.main as main


def test_legacy_coordinator_aborts_after_releasing_new_guard(monkeypatch):
    events = []

    class Guard:
        def acquire(self):
            events.append("acquire")
            return self

        def release(self):
            events.append("release")

    monkeypatch.setattr(main, "_MultiBotInstanceGuard", lambda _root: Guard())
    monkeypatch.setattr(
        main,
        "_find_other_multibot_coordinators_windows",
        lambda: [{"ProcessId": 22636, "CommandLine": "python -m app.main --mode multi-bot-daemon"}],
    )

    try:
        main._acquire_multibot_instance_guard()
    except SystemExit as exc:
        message = str(exc)
    else:
        raise AssertionError("El coordinador legacy no bloqueó el arranque")

    assert events == ["acquire", "release"]
    assert "MULTIBOT_LEGACY_INSTANCE_DETECTED" in message
    assert "PID=22636" in message
    assert "antes de crear dashboard o workers" in message


def test_without_legacy_coordinator_guard_remains_active(monkeypatch):
    guard = object()

    class Factory:
        def acquire(self):
            return guard

    monkeypatch.setattr(main, "_MultiBotInstanceGuard", lambda _root: Factory())
    monkeypatch.setattr(main, "_find_other_multibot_coordinators_windows", lambda: [])
    assert main._acquire_multibot_instance_guard() is guard
