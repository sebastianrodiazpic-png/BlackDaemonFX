from pathlib import Path

import pytest

from app.main import _MultiBotInstanceGuard


def test_second_coordinator_is_rejected_before_workers(tmp_path: Path):
    first = _MultiBotInstanceGuard(tmp_path).acquire()
    try:
        with pytest.raises(SystemExit) as exc:
            _MultiBotInstanceGuard(tmp_path).acquire()
        message = str(exc.value)
        assert "MULTIBOT_ALREADY_RUNNING" in message
        assert f"PID={first._owner()['pid']}" in message
        assert "antes de crear workers" in message
    finally:
        first.release()


def test_lock_can_be_acquired_after_clean_release(tmp_path: Path):
    first = _MultiBotInstanceGuard(tmp_path).acquire()
    first.release()

    second = _MultiBotInstanceGuard(tmp_path).acquire()
    try:
        assert second._owner()["active"] is True
    finally:
        second.release()
