
from types import SimpleNamespace

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from trade_lifecycle_manager import TradeLifecycle, STATE_EXECUTION
from reporting.trade_reporting_service import TradeReportingService


def test_reporting_prefers_explicit_execution_key():
    lifecycle = SimpleNamespace(
        metadata={"execution_key": "DEMO:UNIQUE:KEY"},
        execution_id="999",
        position_ticket="888",
        symbol="Boom 100 Index",
        timeframe="M5",
        direction="BUY",
        entry_time="2026-08-26T00:00:00+00:00",
    )
    assert TradeReportingService._execution_key(lifecycle) == "DEMO:UNIQUE:KEY"


class FakeRepository:
    def __init__(self):
        self.sync_calls = 0

    def sync_closed_mt5_trades(self, executor, source=None):
        self.sync_calls += 1
        return 2


class FakeReporting:
    def __init__(self):
        self.exports = 0

    def export_now(self):
        self.exports += 1


class FakeEngine(LiveTradingEngine):
    def process_symbols(self, symbols):
        return [{"symbol": symbol, "action": "NO_SIGNAL"} for symbol in symbols]


def test_run_once_processes_and_syncs_and_exports():
    repo = FakeRepository()
    reporting = FakeReporting()
    engine = FakeEngine(
        provider=SimpleNamespace(),
        repository=repo,
        config=LiveTradingConfig(execution_enabled=False),
        executor=SimpleNamespace(),
        reporting_service=reporting,
    )

    result = engine.run_once(["Boom 100 Index"])

    assert result["results"][0]["action"] == "NO_SIGNAL"
    assert result["sync"] == 2
    assert repo.sync_calls == 1
    assert reporting.exports == 1


class FakeLifecycleManager:
    def create_from_signal(self, signal):
        return TradeLifecycle(
            symbol=signal["symbol"],
            timeframe=signal["timeframe"],
            direction=signal["direction"],
            entry_time=signal["entry_time"],
            entry_price=signal["entry_price"],
            stop_loss=signal["stop_loss"],
            take_profit=signal["take_profit"],
            risk_reward_ratio=signal["risk_reward_ratio"],
        )

    def execute_with_executor(self, lifecycle, volume):
        lifecycle.state = STATE_EXECUTION
        lifecycle.execution_status = "FILLED"
        lifecycle.execution_id = "12345"
        lifecycle.position_ticket = "67890"
        lifecycle.execution_time = "2026-08-26T00:00:00+00:00"
        return lifecycle


class ExecutionRepo:
    def __init__(self):
        self.saved_signals = []
        self.saved_accounts = []
        self.rows = {}

    def save_signal_once(self, payload):
        self.saved_signals.append(payload)
        return 77, True

    def get_trade_by_execution_key(self, key):
        return self.rows.get(key)

    def create_trade_once(self, payload):
        row = {"id": len(self.rows) + 1, **payload}
        self.rows[payload["execution_key"]] = row
        return row["id"], True

    def get_trade(self, trade_id):
        return next((r for r in self.rows.values() if r["id"] == trade_id), None)

    def open_trades(self, source=None):
        return []

    def save_account_snapshot(self, account):
        self.saved_accounts.append(account)

    def sync_closed_mt5_trades(self, executor, source=None):
        return 0


class Provider:
    connector = SimpleNamespace()

    def resolve_symbol(self, symbol):
        return symbol

    def ensure_symbol(self, symbol):
        return True

    def get_current_tick(self, symbol):
        return {"bid": 100.0, "ask": 101.0}


class Executor:
    def assert_demo_account(self):
        return {"balance": 10000.0, "equity": 10000.0, "server": "Deriv-Demo"}

    def normalize_market_stops(self, *args, **kwargs):
        return {
            "valid": True,
            "entry_price": 101.0,
            "stop_loss": 95.0,
            "take_profit": 113.0,
        }

    def calculate_volume(self, *args, **kwargs):
        return {"volume": 0.1, "actual_risk_amount": 10.0}

    def check_market_order(self, *args, **kwargs):
        return {"valid": True}

    def get_position(self, ticket):
        return SimpleNamespace(
            ticket=ticket, volume=0.1, price_open=101.0, sl=95.0, tp=113.0
        )

    def calculate_risk_amount(self, **kwargs):
        return {"actual_risk_amount": 10.0, "risk_engine": "TEST"}


class Analyzer:
    def analyze_symbol(self, symbol):
        return {
            "valid": True,
            "diagnostics": {"m5": {"last_candle_time": "2026-08-26T00:00:00+00:00"}},
            "signal": {
                "direction": "BUY",
                "chart_pattern_supporting_strength": 0.78,
                "chart_pattern_conflicting_strength": 0.65,
                "entry_location_ranges": {"H1": {"low": 90., "high": 120.}},
                "entry_time": "2026-08-26T00:00:00+00:00",
                "entry_price": 100.0,
                "stop_loss": 95.0,
                "risk_reward_ratio": 2.0,
            },
        }


def test_execution_path_uses_lifecycle_manager_when_configured():
    repo = ExecutionRepo()
    lifecycle = FakeLifecycleManager()
    engine = LiveTradingEngine(
        provider=Provider(),
        repository=repo,
        config=LiveTradingConfig(execution_enabled=True, max_entry_drift_r=None),
        executor=Executor(),
        lifecycle_manager=lifecycle,
    )
    engine.multi_timeframe = Analyzer()

    result = engine.process_symbol("Volatility 90 Index")

    assert result["action"] == "SPLIT_ORDER_OPENED"
    assert result["opened_legs"][0]["lifecycle"]["metadata"]["stage_data"]["m5"]["last_candle_time"] == "2026-08-26T00:00:00+00:00"
    assert len(repo.rows) == 2
    metadata=result["opened_legs"][0]["lifecycle"]["metadata"]
    assert metadata["entry_learning_snapshot"]["schema"] == "entry-learning-v1"
    assert metadata["entry_learning_snapshot"]["features"]
    assert metadata["chart_pattern_supporting_strength"] == .78
    assert metadata["chart_pattern_conflicting_strength"] == .65
    assert metadata["target_path_audit"]["TP1"]["mode"] == "INFORMATION_ONLY"
    assert len(result["opened_legs"]) == 2
    assert [leg["leg"] for leg in result["opened_legs"]] == ["TP1", "RUNNER"]
    assert all(leg["position_ticket"] == "67890" for leg in result["opened_legs"])
    assert all(leg["execution_id"] == "12345" for leg in result["opened_legs"])
    assert all(leg["lifecycle"]["state"] == STATE_EXECUTION for leg in result["opened_legs"])
    assert result["opened_legs"][0]["lifecycle"]["metadata"]["execution_key"].endswith(":TP1")
    assert result["opened_legs"][1]["lifecycle"]["metadata"]["execution_key"].endswith(":RUNNER")
