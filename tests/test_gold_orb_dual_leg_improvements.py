from types import SimpleNamespace
from unittest.mock import Mock
import pytest

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


def mock_build_plan_factory(entry, sl, direction, total_risk_amount):
    risk_distance = abs(entry - sl)
    def build_plan(specs, mode):
        legs = []
        for item in specs:
            name, fraction, logical_rr, broker_rr = item[0], item[1], item[2], item[3]
            leg_risk = total_risk_amount * fraction
            tp = entry + risk_distance * broker_rr if direction == "BUY" else entry - risk_distance * broker_rr
            legs.append({
                "name": name,
                "risk_fraction": fraction,
                "risk_amount": leg_risk,
                "target_rr": broker_rr,
                "take_profit": tp,
            })
        return legs, None
    return build_plan


def test_gold_quarters_splits_into_tp1_and_runner_legs():
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile="GOLD", split_entries_enabled=True)
    engine._is_forex_symbol = lambda s: False
    engine._is_volatility_symbol = lambda s: False
    engine._is_jump_symbol = lambda s: False

    signal = {
        "strategy_name": "GOLD_QUARTERS",
        "direction": "BUY",
        "entry_price": 2700.0,
        "stop_loss": 2690.0,
        "take_profit": 2730.0,
        "quarter_target": 2715.0,
        "quarter_target_2": 2730.0,
        "risk_reward_ratio_tp1": 1.5,
        "risk_reward_ratio_tp2": 3.0,
    }

    build_plan = mock_build_plan_factory(2700.0, 2690.0, "BUY", 10.0)

    legs, split_failure, single_failure, mode = engine._plan_execution_legs(
        exact_symbol="XAUUSD",
        direction="BUY",
        entry=2700.0,
        sl=2690.0,
        rr=3.0,
        strategy_name="GOLD_QUARTERS",
        signal=signal,
        total_risk_amount=10.0,
        risk_fraction=0.5,
        silver_risk_cap=False,
        build_plan=build_plan,
    )

    assert split_failure is None
    assert mode == "SPLIT"
    assert len(legs) == 2
    assert legs[0]["name"] == "TP1"
    assert legs[0]["risk_fraction"] == 0.5
    assert legs[0]["risk_amount"] == 5.0
    assert legs[0]["target_rr"] == 1.5

    assert legs[1]["name"] == "RUNNER"
    assert legs[1]["risk_fraction"] == 0.5
    assert legs[1]["risk_amount"] == 5.0
    assert legs[1]["target_rr"] == 3.0


def test_orb_context_selects_tp2_5_and_tp3_runner_targets():
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile="ORB", split_entries_enabled=True)
    engine._is_forex_symbol = lambda s: False
    engine._is_volatility_symbol = lambda s: False
    engine._is_jump_symbol = lambda s: False

    build_plan = mock_build_plan_factory(40000.0, 39900.0, "BUY", 10.0)

    # Case 1: tight opening range (<= 1.0) -> targets TP3 (3.0R)
    signal_tight = {
        "strategy_name": "ORB_NEW_YORK",
        "opening_range_atr_ratio": 0.9,
        "retest_quality": "HIGH_QUALITY",
    }
    legs_tight, _, _, mode_tight = engine._plan_execution_legs(
        exact_symbol="US30",
        direction="BUY",
        entry=40000.0,
        sl=39900.0,
        rr=2.0,
        strategy_name="ORB_NEW_YORK",
        signal=signal_tight,
        total_risk_amount=10.0,
        risk_fraction=0.5,
        silver_risk_cap=False,
        build_plan=build_plan,
    )
    assert mode_tight == "SPLIT"
    assert legs_tight[1]["target_rr"] == 3.0

    # Case 2: moderate opening range (<= 1.2) -> targets TP2.5 (2.5R)
    signal_mod = {
        "strategy_name": "ORB_NEW_YORK",
        "opening_range_atr_ratio": 1.15,
        "retest_quality": "STANDARD_QUALITY",
    }
    legs_mod, _, _, mode_mod = engine._plan_execution_legs(
        exact_symbol="US30",
        direction="BUY",
        entry=40000.0,
        sl=39900.0,
        rr=2.0,
        strategy_name="ORB_NEW_YORK",
        signal=signal_mod,
        total_risk_amount=10.0,
        risk_fraction=0.5,
        silver_risk_cap=False,
        build_plan=build_plan,
    )
    assert mode_mod == "SPLIT"
    assert legs_mod[1]["target_rr"] == 2.5


def test_runner_step_lock_profit_protection_for_tp3_and_tp2_5():
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile="ORB")
    engine.repository = SimpleNamespace(update_trade=Mock())
    engine.provider = SimpleNamespace(get_current_tick=lambda _: {"bid": 31.90, "ask": 31.92})
    engine.executor = SimpleNamespace(
        get_position=lambda ticket: SimpleNamespace(price_open=30.00, sl=30.05, tp=33.00, price_current=31.90),
        get_symbol_constraints=lambda s: {"digits": 2, "point": 0.01, "tick_size": 0.01},
    )

    trade = {
        "id": 10,
        "instrument": "XAGUSD",
        "direction": "BUY",
        "broker_position_ticket": 888,
        "details": {},
        "planned_rr": 3.0,
    }

    # Position at entry 30.00, initial SL 29.00 (risk = 1.00)
    # BE confirmed at 30.05, current SL is 30.05
    pos = SimpleNamespace(price_open=30.00, sl=30.05, tp=33.00, price_current=31.90)  # +1.90R (above 1.8R)
    metadata = {
        "trade_leg": "RUNNER",
        "break_even_confirmed": True,
        "break_even_price": 30.05,
        "target_rr": 3.0,
        "runner_target_rr": 3.0,
        "initial_stop_loss": 29.00,
        "orb_tp1_target_price": 31.00,
    }

    moved_stops = []
    def mock_move(**kw):
        moved_stops.append(kw)
        pos.sl = kw["stop_loss"]
        return {"modified": True}

    # Call at 1.90R -> should lock +1.0R (SL moves to 31.00)
    res1 = engine.process_orb_break_even_management(trade, pos, metadata, mock_move)
    assert res1["action"] == "ORB_RUNNER_PROFIT_LOCKED_1.0R"
    assert res1["activated"] is True
    assert pos.sl == 31.00
    assert metadata["runner_profit_lock_rr"] == 1.0

    # Advance price to 32.60 (+2.60R, above 2.5R trigger for TP3)
    pos.price_current = 32.60
    engine.provider = SimpleNamespace(get_current_tick=lambda _: {"bid": 32.60, "ask": 32.62})
    res2 = engine.process_orb_break_even_management(trade, pos, metadata, mock_move)
    assert res2["action"] == "ORB_RUNNER_PROFIT_LOCKED_2.0R"
    assert res2["activated"] is True
    assert pos.sl == 32.00
    assert metadata["runner_profit_lock_rr"] == 2.0


def test_gold_quarters_preserves_quarter_levels_and_step_lock_without_smc_closure():
    """Verifies that GOLD_QUARTERS preserves exact quarter levels (TP1, TP2) and
    step-lock profit protection (+1.0R, +2.0R) without being prematurely closed
    or truncated by generic SMC runner continuation evaluations.
    """
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(
        bot_profile="GOLD",
        split_entries_enabled=True,
        runner_extension_enabled=True,
        runner_extension_max_target_rr=4.0,
    )
    engine._is_forex_symbol = lambda s: False
    engine._is_volatility_symbol = lambda s: False
    engine._is_jump_symbol = lambda s: False

    entry = 2700.0
    sl = 2692.0  # Risk = 8.0 USD
    tp1 = 2725.0 # Quarter 1 = +25.0 USD = 3.125 R
    tp2 = 2750.0 # Quarter 2 = +50.0 USD = 6.25 R

    signal = {
        "strategy_name": "GOLD_QUARTERS",
        "direction": "BUY",
        "entry_price": entry,
        "stop_loss": sl,
        "quarter_target": tp1,
        "quarter_target_2": tp2,
        "take_profit": tp2,
        "risk_reward_ratio_tp1": 3.125,
        "risk_reward_ratio_tp2": 6.25,
        "risk_reward_ratio": 6.25,
    }

    build_plan = mock_build_plan_factory(entry, sl, "BUY", 100.0)

    legs, split_failure, single_failure, mode = engine._plan_execution_legs(
        exact_symbol="XAUUSD",
        direction="BUY",
        entry=entry,
        sl=sl,
        rr=6.25,
        strategy_name="GOLD_QUARTERS",
        signal=signal,
        total_risk_amount=100.0,
        risk_fraction=0.5,
        silver_risk_cap=False,
        build_plan=build_plan,
    )

    assert split_failure is None
    assert mode == "SPLIT"
    assert len(legs) == 2

    # Leg 1: TP1 exact quarter target
    assert legs[0]["name"] == "TP1"
    assert legs[0]["target_rr"] == 3.125
    assert legs[0]["take_profit"] == tp1

    # Leg 2: RUNNER exact quarter target 2 (6.25R = 2750.0), NOT capped at 4.0R
    assert legs[1]["name"] == "RUNNER"
    assert legs[1]["target_rr"] == 6.25
    assert legs[1]["take_profit"] == tp2

    engine.repository = SimpleNamespace(update_trade=Mock())
    engine.provider = SimpleNamespace(get_current_tick=lambda _: {"bid": 2736.0, "ask": 2736.5})
    engine.executor = SimpleNamespace(
        get_position=lambda ticket: SimpleNamespace(price_open=entry, sl=entry + 0.30, tp=tp2, price_current=2736.0),
        get_symbol_constraints=lambda s: {"digits": 2, "point": 0.01, "tick_size": 0.01},
    )
    trade = {
        "id": 55,
        "instrument": "XAUUSD",
        "direction": "BUY",
        "broker_position_ticket": 7777,
        "details": {},
        "planned_rr": 6.25,
    }
    pos = SimpleNamespace(price_open=entry, sl=entry + 0.30, tp=tp2, price_current=2736.0)
    metadata = {
        "strategy_name": "GOLD_QUARTERS",
        "trade_leg": "RUNNER",
        "break_even_confirmed": True,
        "break_even_price": entry + 0.30,
        "target_rr": 6.25,
        "runner_target_rr": 6.25,
        "initial_stop_loss": sl,
        "gold_tp1_target_price": tp1,
    }
    engine._break_even_initial_stop = lambda t, m: sl

    def mock_move(**kw):
        pos.sl = kw["stop_loss"]
        return {"modified": True}

    res = engine.process_orb_break_even_management(trade, pos, metadata, mock_move)
    assert res["action"] == "ORB_RUNNER_PROFIT_LOCKED_2.0R"
    assert res["activated"] is True
    assert pos.sl == entry + 16.0  # +2.0R lock = 2716.0

