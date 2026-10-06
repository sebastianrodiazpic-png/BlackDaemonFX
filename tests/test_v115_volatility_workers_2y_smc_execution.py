from types import SimpleNamespace
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from config.strategy_config import PRUNED_ASSET_UNIVERSE
from dashboard.realtime_dashboard import DEFAULT_PRIORITIZED_SYMBOLS, PRUNED_INSTRUMENTS_INFO


class Repo:
    def save_signal_once(self, payload):
        return 11, True

    def get_trade_by_execution_key(self, key):
        return None

    def open_trades(self, source=None):
        return []

    def save_account_snapshot(self, account):
        pass

    def update_trade(self, trade_id, data):
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
    def get_open_positions(self):
        return []

    def get_pending_orders(self):
        return []

    def assert_demo_account(self):
        return {"balance": 10000.0, "equity": 10000.0, "server": "Deriv-Demo"}

    def normalize_market_stops(self, *args, **kwargs):
        return {
            "valid": True,
            "entry_price": 100.0,
            "stop_loss": 90.0,
            "take_profit": 130.0,
            "constraints": {"digits": 2},
        }

    def calculate_volume(self, symbol, direction, entry, stop, risk_amount):
        return {"volume": risk_amount / 100.0, "actual_risk_amount": risk_amount}


class Analyzer:
    def analyze_symbol(self, symbol):
        return {
            "valid": True,
            "signal": {
                "direction": "BUY",
                "entry_location_ranges": {tf: {"low": 90.0, "high": 130.0} for tf in ("H1", "M15", "M5")},
                "entry_time": "2026-10-02T12:00:00+00:00",
                "entry_price": 100.0,
                "stop_loss": 90.0,
                "risk_reward_ratio": 2.0,
                "harmonic_confirmed": True,
                "harmonic_pattern": "GARTLEY",
                "harmonic_score": 88.0,
            },
        }


def test_volatility_worker_splits_entry_into_tp1_2r_and_runner_3r():
    engine = LiveTradingEngine(
        provider=Provider(),
        repository=Repo(),
        config=LiveTradingConfig(
            execution_enabled=False,
            validate_order_in_dry_run=False,
            max_entry_drift_r=None,
            risk_percent=1.0,
            bot_profile="VOLATILITY_1",
            split_entries_enabled=True,
            split_entry_risk_fraction=0.50,
            volatility_first_target_rr=2.0,
            volatility_second_target_rr=3.0,
            smc_runner_max_target_rr=3.0,
        ),
        executor=Executor(),
    )
    engine.multi_timeframe = Analyzer()
    engine._smc_entry_preflight = lambda *args: {"valid": True}

    result = engine.process_symbol("Volatility 75 Index")

    assert result["action"] == "DRY_RUN_VALIDATED"
    assert result["risk_amount"] == 100.0
    assert result["actual_risk_amount"] == 100.0
    assert result["actual_risk_percent"] == 1.0
    assert len(result["legs"]) == 2

    tp1, runner = result["legs"]
    assert tp1["name"] == "TP1"
    assert tp1["risk_percent"] == 0.5
    assert tp1["risk_amount"] == 50.0
    assert tp1["target_rr"] == 2.0
    assert tp1["take_profit"] == 120.0

    assert runner["name"] == "RUNNER"
    assert runner["risk_percent"] == 0.5
    assert runner["risk_amount"] == 50.0
    assert runner["target_rr"] == 3.0
    assert runner["take_profit"] == 130.0

    assert result["break_even_trigger_rr"] == 2.0


def test_volatility_runner_progressive_profit_lock_at_2_5r():
    engine = LiveTradingEngine(
        provider=Provider(),
        repository=Repo(),
        config=LiveTradingConfig(
            bot_profile="VOLATILITY_2",
            runner_extension_enabled=True,
            smc_runner_max_target_rr=3.0,
            smc_runner_tp3_guard_trigger_rr=2.5,
            smc_runner_tp3_guard_lock_rr=2.0,
        ),
        executor=Executor(),
    )
    engine.lifecycle_manager = SimpleNamespace(
        trade_executor=SimpleNamespace(close_position=lambda *a, **k: {"closed": True})
    )

    trade = {
        "id": 999,
        "instrument": "Volatility 50 (1s) Index",
        "direction": "BUY",
        "broker_position_ticket": "123456",
        "details": {
            "metadata": {
                "bot_profile": "VOLATILITY_2",
                "trade_leg": "RUNNER",
                "strategy_name": "SMC",
                "runner_extension_completed_stages": ["2R_TO_3R"],
            }
        },
    }

    position = SimpleNamespace(
        price_open=1000.0,
        sl=1000.0,
        tp=1300.0,
    )

    moved_sl = []
    def fake_move_stop(position_ticket, stop_loss, take_profit, reason):
        moved_sl.append((stop_loss, take_profit, reason))
        return {"modified": True}

    res = engine._manage_runner_extension(
        trade=trade,
        position=position,
        metadata=dict(trade["details"]["metadata"]),
        initial_stop_loss=900.0,  # 1R = 100.0 points
        current_rr=2.52,          # At 2.52R, profit guard triggers!
        move_stop=fake_move_stop,
    )

    assert res.get("managed") is True
    assert res.get("stage") == "SMC_TP3_GUARD_2R"
    assert res.get("profit_lock_rr") == 2.0
    # Stop loss moved to entry (1000) + 2.0 * 100 = 1200.0
    assert len(moved_sl) == 1
    assert moved_sl[0][0] == 1200.0
    assert moved_sl[0][2] == "smc_runner_tp3_guard_lock_2r"


def test_top_volatility_instruments_unpruned_and_prioritized():
    expected_top_15 = [
        "Volatility 50 (1s) Index",
        "Volatility 75 Index",
        "Volatility 75 (1s) Index",
        "VolSwitch High Vol Index",
        "High Frequency Vol 50 Index",
        "Vol over Crash 550",
        "Volatility 15 Index",
        "Volatility 150 (1s) Index",
        "Volatility 250 (1s) Index",
        "Volatility 90 Index",
        "Volatility 5 Index",
        "High Frequency Vol 100 Index",
        "Vol over Boom 550",
        "Volatility 90 (1s) Index",
        "Volatility 25 Index",
    ]

    pruned_vol_universe = PRUNED_ASSET_UNIVERSE["VOLATILITY"]
    prioritized_synthetics = DEFAULT_PRIORITIZED_SYMBOLS["SYNTHETICS"]

    for sym in expected_top_15:
        # Must be in strategy universe
        assert sym in pruned_vol_universe, f"{sym} missing from PRUNED_ASSET_UNIVERSE"
        # Must be in dashboard prioritized symbols
        assert sym in prioritized_synthetics, f"{sym} missing from DEFAULT_PRIORITIZED_SYMBOLS"
        # Must NOT be in pruned instruments info (no PODA comments)
        assert sym not in PRUNED_INSTRUMENTS_INFO, f"{sym} still marked as PRUNED in PRUNED_INSTRUMENTS_INFO"
