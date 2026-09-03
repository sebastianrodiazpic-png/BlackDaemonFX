from types import SimpleNamespace

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


class Repo:
    def save_signal_once(self, payload):
        return 11, True

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
            "constraints": {"digits": 2},
        }

    def calculate_volume(self, symbol, direction, entry, stop, risk_amount):
        # El test fuerza sizing exacto para comprobar el reparto 50/50.
        return {"volume": risk_amount / 100.0, "actual_risk_amount": risk_amount}


class Analyzer:
    def analyze_symbol(self, symbol):
        return {
            "valid": True,
            "signal": {
                "direction": "BUY",
                "entry_time": "2026-08-28T12:00:00+00:00",
                "entry_price": 100.0,
                "stop_loss": 90.0,
                "risk_reward_ratio": 2.0,
                "harmonic_confirmed": True,
                "harmonic_pattern": "GARTLEY",
                "harmonic_score": 88.0,
            },
        }


def test_one_percent_operation_is_split_into_two_half_percent_legs():
    engine = LiveTradingEngine(
        provider=Provider(),
        repository=Repo(),
        config=LiveTradingConfig(
            execution_enabled=False,
            validate_order_in_dry_run=False,
            max_entry_drift_r=None,
            risk_percent=1.0,
            split_entries_enabled=True,
            split_entry_risk_fraction=0.50,
            first_target_rr=1.0,
            second_target_rr=2.0,
        ),
        executor=Executor(),
    )
    engine.multi_timeframe = Analyzer()

    result = engine.process_symbol("Volatility 90 Index")

    assert result["action"] == "DRY_RUN_VALIDATED"
    assert result["risk_amount"] == 100.0
    assert result["actual_risk_amount"] == 100.0
    assert result["actual_risk_percent"] == 1.0
    assert len(result["legs"]) == 2

    tp1, runner = result["legs"]
    assert tp1["name"] == "TP1"
    assert tp1["risk_percent"] == 0.5
    assert tp1["risk_amount"] == 50.0
    assert tp1["target_rr"] == 1.0
    assert tp1["take_profit"] == 110.0

    assert runner["name"] == "RUNNER"
    assert runner["risk_percent"] == 0.5
    assert runner["risk_amount"] == 50.0
    assert runner["target_rr"] == 2.0
    assert runner["take_profit"] == 120.0


def test_daemon_pipeline_uses_harmonic_as_bonus_with_adaptive_75_gate_by_default():
    engine = LiveTradingEngine(
        provider=Provider(),
        repository=Repo(),
        config=LiveTradingConfig(),
        executor=Executor(),
    )
    assert engine.pipeline_config.harmonic_enabled is True
    assert engine.pipeline_config.require_harmonic is False
    assert engine.pipeline_config.adaptive_confirmation_enabled is True
    assert engine.pipeline_config.minimum_confirmation_ratio == 0.80
    assert engine.pipeline_config.minimum_viable_trade_score == 75.0
    assert engine.pipeline_config.harmonic_minimum_score == 75.0


def test_smc_runner_extension_uses_4r_broker_target_without_increasing_risk():
    engine = LiveTradingEngine(
        provider=Provider(),
        repository=Repo(),
        config=LiveTradingConfig(
            execution_enabled=False,
            validate_order_in_dry_run=False,
            max_entry_drift_r=None,
            risk_percent=1.0,
            split_entries_enabled=True,
            split_entry_risk_fraction=0.50,
            first_target_rr=1.0,
            second_target_rr=2.0,
            runner_extension_enabled=True,
            runner_extension_max_target_rr=4.0,
        ),
        executor=Executor(),
    )
    engine.multi_timeframe = Analyzer()

    result = engine.process_symbol("Volatility 90 Index")
    assert result["action"] == "DRY_RUN_VALIDATED"
    assert result["actual_risk_percent"] == 1.0
    tp1, runner = result["legs"]
    assert tp1["target_rr"] == 1.0
    assert runner["target_rr"] == 4.0
    assert runner["take_profit"] == 140.0
    assert runner["risk_percent"] == 0.5
