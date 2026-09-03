from types import SimpleNamespace

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


class Repo:
    def __init__(self, trades=None):
        self.trades = list(trades or [])
        self.sync_calls = 0

    def open_trades(self, source=None):
        return list(self.trades)

    def sync_closed_mt5_trades(self, executor, source=None):
        self.sync_calls += 1
        return 0


class Reporting:
    def __init__(self, auto_export):
        self.config = SimpleNamespace(auto_export=auto_export)
        self.exports = 0

    def export_now(self):
        self.exports += 1


def engine(repo, reporting):
    value = object.__new__(LiveTradingEngine)
    value.repository = repo
    value.reporting_service = reporting
    value.executor = SimpleNamespace()
    value.config = LiveTradingConfig(
        source="DEMO", bot_profile="BOOM", magic=26082101,
        execution_enabled=True,
    )
    return value


def test_coordinated_worker_sync_never_writes_xlsx():
    repo = Repo()
    reporting = Reporting(auto_export=False)
    value = engine(repo, reporting)
    value.sync_closed_trades()
    assert repo.sync_calls == 1
    assert reporting.exports == 0


def test_standalone_auto_export_remains_compatible():
    repo = Repo()
    reporting = Reporting(auto_export=True)
    value = engine(repo, reporting)
    value.sync_closed_trades()
    assert reporting.exports == 1


def test_pre_execution_sync_skips_mt5_without_owned_positions():
    repo = Repo()
    value = engine(repo, Reporting(auto_export=False))
    result = value._sync_open_trades_before_execution()
    assert result["reason"] == "NO_OWNED_OPEN_POSITIONS"
    assert repo.sync_calls == 0
