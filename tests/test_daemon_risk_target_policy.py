from types import SimpleNamespace

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


class Repo:
    def save_signal_once(self, payload):
        return 1, True

    def get_trade_by_execution_key(self, key):
        return None

    def open_trades(self, source=None):
        return []

    def save_account_snapshot(self, account):
        pass


class Provider:
    connector = SimpleNamespace()

    def resolve_symbol(self, symbol):
        return symbol

    def ensure_symbol(self, symbol):
        return True

    def get_current_tick(self, symbol):
        return {"bid": 100.0, "ask": 100.0}


class Executor:
    def assert_demo_account(self):
        return {"balance": 10000.0, "equity": 10000.0, "server": "Deriv-Demo"}

    def normalize_market_stops(self, *args, **kwargs):
        return {
            "valid": True,
            "entry_price": 100.0,
            "stop_loss": 90.0,
            "take_profit": 120.0,
        }

    def calculate_volume(self, *args, **kwargs):
        return {
            "volume": 15.0,
            "raw_volume": 36.8,
            "volume_max": 15.0,
            "actual_risk_amount": 40.0,
        }


class Analyzer:
    def analyze_symbol(self, symbol):
        return {
            "valid": True,
            "signal": {
                "direction": "BUY",
                "entry_time": "2026-08-26T00:00:00+00:00",
                "entry_price": 100.0,
                "stop_loss": 90.0,
                "risk_reward_ratio": 2.0,
            },
        }


def test_rejects_trade_when_broker_max_volume_cannot_reach_risk_target():
    engine = LiveTradingEngine(
        provider=Provider(),
        repository=Repo(),
        config=LiveTradingConfig(
            execution_enabled=False,
            max_entry_drift_r=None,
            min_actual_risk_ratio=0.95,
            validate_order_in_dry_run=False,
        ),
        executor=Executor(),
    )
    engine.multi_timeframe = Analyzer()

    result = engine.process_symbol("Volatility 75 Index")

    assert result["action"] == "REJECTED_RISK_TARGET_UNREACHABLE"
    assert result["reason"] == "BROKER_VOLUME_LIMIT_PREVENTS_TARGET_RISK"
    assert result["actual_risk_amount"] == 40.0
    assert result["min_required_risk"] == 47.5
    assert result["leg"] == "TP1"
