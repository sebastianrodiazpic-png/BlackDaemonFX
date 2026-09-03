from types import SimpleNamespace

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


class FakeProvider:
    connector = SimpleNamespace()

    def resolve_symbol(self, symbol):
        return symbol

    def ensure_symbol(self, symbol):
        return True

    def get_current_tick(self, symbol):
        return {"bid": 100.8, "ask": 101.0}


class FakeRepository:
    def __init__(self):
        self.saved_signals = []
        self.saved_accounts = []

    def save_signal_once(self, payload):
        self.saved_signals.append(payload)
        return 77, True

    def get_trade_by_execution_key(self, key):
        return None

    def open_trades(self, source=None):
        return []

    def save_account_snapshot(self, account):
        self.saved_accounts.append(account)


class FakeExecutor:
    def __init__(self):
        self.placed = False
        self.order_check_calls = []

    def assert_demo_account(self):
        return {"balance": 10_000.0, "equity": 10_000.0, "server": "DEMO"}

    def normalize_market_stops(self, symbol, direction, entry, original_sl, rr, safety_points=0):
        return {
            "valid": True,
            "reason": "STOPS_VALID",
            "entry_price": float(entry),
            "stop_loss": float(original_sl),
            "take_profit": float(entry + (entry - original_sl) * rr),
            "adjusted": False,
            "constraints": {"point": 0.1, "stops_level_points": 0},
        }

    def calculate_volume(self, symbol, direction, entry, sl, risk_amount):
        actual = float(risk_amount) * 0.995
        return {
            "volume": 0.25,
            "raw_volume": 0.25,
            "risk_per_lot": 199.0,
            "actual_risk_amount": actual,
            "tick_size": 0.1,
            "tick_value": 1.0,
            "volume_min": 0.01,
            "volume_max": 100.0,
            "volume_step": 0.01,
        }

    def check_market_order(self, symbol, direction, volume, sl, tp, magic, comment, deviation):
        self.order_check_calls.append({
            "symbol": symbol,
            "direction": direction,
            "volume": volume,
            "stop_loss": sl,
            "take_profit": tp,
            "magic": magic,
            "comment": comment,
            "deviation": deviation,
        })
        return {"valid": True, "retcode": 0, "comment": "Done", "diagnostic": "ORDER_CHECK_OK"}

    def place_market_order(self, *args, **kwargs):
        self.placed = True
        raise AssertionError("DRY_RUN nunca debe llamar place_market_order")


class FakeAnalyzer:
    def analyze_symbol(self, symbol):
        signal = {
            "direction": "BUY",
            "entry_time": "2026-08-25T12:00:00+00:00",
            "entry_price": 100.0,
            "stop_loss": 95.0,
            "take_profit": 110.0,
            "risk_reward_ratio": 2.0,
            "confirmation_ok": True,
        }
        return {
            "symbol": symbol,
            "valid": True,
            "action": "MULTI_TIMEFRAME_SIGNAL",
            "direction": "BUY",
            "signal": signal,
            "diagnostics": {
                "sequence_status": "VALID_SEQUENCE",
                "sequence": {
                    "selected_setup_time": "2026-08-25T11:45:00+00:00",
                    "selected_confirmation_time": "2026-08-25T12:00:00+00:00",
                    "eligible_confirmations": 1,
                },
                "signal_age": {
                    "valid": True,
                    "reason": "M5_SIGNAL_FRESH",
                    "age_candles": 1,
                    "max_age_candles": 3,
                    "is_stale": False,
                },
            },
        }


def test_live_engine_reaches_full_dry_run_validated_path_without_sending_order():
    provider = FakeProvider()
    repository = FakeRepository()
    executor = FakeExecutor()
    engine = LiveTradingEngine(
        provider,
        repository,
        LiveTradingConfig(
            execution_enabled=False,
            validate_order_in_dry_run=True,
            diagnostic_mode=True,
            risk_percent=1.0,
            max_entry_drift_r=0.50,
        ),
        executor=executor,
    )
    engine.multi_timeframe = FakeAnalyzer()

    result = engine.process_symbol("Volatility 90 Index")

    assert result["action"] == "DRY_RUN_VALIDATED"
    assert result["direction"] == "BUY"
    assert result["entry_price"] == 101.0
    assert result["stop_loss"] == 95.0
    assert result["take_profit"] == 113.0
    assert result["planned_rr"] == 2.0
    assert result["risk_amount"] == 100.0
    assert result["actual_risk_amount"] == 99.5
    assert len(result["legs"]) == 2
    assert result["legs"][0]["risk_amount"] == 50.0
    assert result["legs"][0]["take_profit"] == 107.0
    assert result["legs"][1]["risk_amount"] == 50.0
    assert result["legs"][1]["take_profit"] == 113.0
    assert all(leg["order_check"]["valid"] is True for leg in result["legs"])
    assert all(leg["order_check"]["retcode"] == 0 for leg in result["legs"])
    assert result["market_signal_diagnostics"]["market_invalidated_signal"] is False
    assert result["market_signal_diagnostics"]["entry_drift_exceeded"] is False
    assert len(executor.order_check_calls) == 2
    assert executor.placed is False
    assert len(repository.saved_signals) == 1
    assert len(repository.saved_accounts) == 1
