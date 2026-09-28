import threading
from concurrent.futures import ThreadPoolExecutor

from dashboard import realtime_dashboard as dashboard


def test_concurrent_account_readers_share_one_build(tmp_path, monkeypatch):
    service = dashboard.RealtimeDashboardService(state_path=tmp_path / 'state.json')
    started, release = threading.Event(), threading.Event()
    calls = []

    def build(*args, **kwargs):
        calls.append(1)
        started.set()
        assert release.wait(5)
        return {'snapshot': None}

    monkeypatch.setattr(dashboard, 'build_account_payload', build)
    service._account_cache = {'at': 0, 'payload': None}
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(service._cached_account_payload)
        assert started.wait(5)
        second = pool.submit(service._cached_account_payload)
        release.set()
        assert first.result() == second.result()
    assert len(calls) == 1
