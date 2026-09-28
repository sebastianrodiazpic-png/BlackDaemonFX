import multiprocessing
import time

import pytest

from marketdata.deriv import DerivAPIError, DerivMarketDataProvider
from marketdata.rate_limit import InterprocessRequestRateLimiter


def _issue(path, queue):
    limiter = InterprocessRequestRateLimiter(path, minimum_interval_seconds=0.01)
    try:
        for _ in range(5):
            limiter.wait()
        queue.put(None)
    except Exception as exc:
        queue.put(repr(exc))


def test_empty_file_concurrent_processes(tmp_path):
    ctx = multiprocessing.get_context("spawn")
    queue = ctx.Queue()
    path = str(tmp_path / "shared.lock")
    processes = [ctx.Process(target=_issue, args=(path, queue)) for _ in range(4)]
    try:
        for process in processes:
            process.start()
        assert [queue.get(timeout=20) for _ in processes] == [None] * 4
    finally:
        for process in processes:
            process.join(timeout=5)
            if process.is_alive():
                process.terminate()
                process.join()


def test_cooldown_shared_with_other_instance(tmp_path, monkeypatch):
    clock = [100.0]
    monkeypatch.setattr("marketdata.rate_limit.time.time", lambda: clock[0])
    monkeypatch.setattr("marketdata.rate_limit.time.sleep", lambda delay: clock.__setitem__(0, clock[0] + delay))
    path = tmp_path / "shared.lock"
    first = InterprocessRequestRateLimiter(path, minimum_interval_seconds=0.2)
    second = InterprocessRequestRateLimiter(path, minimum_interval_seconds=0.2)
    first.defer(10)
    second.defer(2)  # A shorter cooldown must not overwrite the longer one.
    assert second.wait() == pytest.approx(10)
    assert first.wait() == pytest.approx(0.2)


def test_final_rate_limit_failure_still_pauses_other_workers(monkeypatch):
    monkeypatch.setenv("DAEMON_DERIV_RATE_LIMIT_RETRIES", "1")
    class Limiter:
        def __init__(self):
            self.delays = []
        def wait(self):
            pass
        def defer(self, delay):
            self.delays.append(delay)
    class Transport:
        def request(self, payload):
            return {"error": {"message": "You have reached the rate limit for ticks_history."}}
    limiter = Limiter()
    provider = DerivMarketDataProvider(transport=Transport(), rate_limiter=limiter)
    with pytest.raises(DerivAPIError, match="rate limit"):
        provider._request({"ticks_history": "test"})
    assert len(limiter.delays) == 2
    assert limiter.delays[1] > limiter.delays[0]
