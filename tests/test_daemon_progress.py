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
