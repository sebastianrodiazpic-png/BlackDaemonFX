import pytest

@pytest.fixture(autouse=True)
def isolated_trial_audit(tmp_path, monkeypatch):
    monkeypatch.setattr("dashboard.smc_trial.ROOT", tmp_path / "trial")

from types import SimpleNamespace

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


class Repo:
    def sync_closed_mt5_trades(self, executor, source=None):
        return 0


class Engine(LiveTradingEngine):
    def process_symbol(self, symbol, sync_before_execution=False):
        return {"symbol": symbol, "action": "NO_SIGNAL"}


def test_process_symbols_reports_each_symbol_immediately():
    engine = Engine(
        provider=SimpleNamespace(),
        repository=Repo(),
        config=LiveTradingConfig(execution_enabled=False),
        executor=SimpleNamespace(),
    )

    events = []
    results = engine.process_symbols(
        ["A", "B"],
        sync_before_execution=False,
        before_symbol=lambda **kw: events.append(("before", kw["symbol"])),
        progress_callback=lambda **kw: events.append(("progress", kw["result"]["symbol"])),
        after_symbol=lambda **kw: events.append(("after", kw["symbol"])),
    )

    assert [row["symbol"] for row in results] == ["A", "B"]
    assert events == [
        ("before", "A"),
        ("progress", "A"),
        ("after", "A"),
        ("before", "B"),
        ("progress", "B"),
        ("after", "B"),
    ]


def test_symbol_permission_error_preserves_diagnostics_and_continues(monkeypatch):
    engine = Engine(
        provider=SimpleNamespace(), repository=Repo(),
        config=LiveTradingConfig(execution_enabled=False), executor=SimpleNamespace(),
    )
    def process(symbol, **kwargs):
        if symbol == "A":
            raise PermissionError(13, "Permission denied", "shared.lock")
        return {"symbol": symbol, "action": "NO_SIGNAL"}
    events = []
    monkeypatch.setattr(engine, "process_symbol", process)
    monkeypatch.setattr(engine, "_persist_audit_event", lambda *args, **kwargs: events.append(kwargs))
    results = engine.process_symbols(["A", "B"], sync_before_execution=False)
    assert results[0]["action"] == "ERROR"
    assert results[1]["action"] == "NO_SIGNAL"
    details = events[0]["payload"]["exception_details"]
    assert details["errno"] == 13
    assert details["filename"] == "shared.lock"
    assert "PermissionError" in details["traceback"]
