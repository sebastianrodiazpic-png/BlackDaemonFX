"""Unified test suite for the 1% risk and dual-leg trade management policy.

Verifies that all 4 strategies (ORB, CUARTOS / GOLD_QUARTERS, SMART MONEY CONCEPTS / SMC,
and MALAYSIAN_SNR) function under the identical unified policy:
1. 1% total available capital risk (Balance/Equity) split into two legs of 0.5% risk each
   (e.g., $10,000 account -> $100 total risk -> two orders of $50 risk each).
2. Leg 1 (TP1) closes upon reaching 1:1 R:R (+ $50 USD profit on $50 risk).
3. The exact moment Leg 1 closes at TP1 (or hits 1.0 R), Leg 2 (RUNNER) moves Stop Loss
   to Break Even protecting broker spread and points buffer to eliminate loss risk.
4. Leg 2 (RUNNER) has a primary objective of TP2 (1:2 R:R = + $100 USD profit).
5. Depending on market continuation, Leg 2 dynamically seeks TP3 (1:3 R:R = + $150 USD)
   or TP4 (1:4 R:R = + $200 USD) with progressive profit locks (+1.0 R, +2.0 R, +3.0 R).
"""

from types import SimpleNamespace
from unittest.mock import Mock
import pytest
import pandas as pd

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from strategy.execution.runner_extension_manager import RunnerExtensionDecision
import strategy.execution.live_trading_engine as live_mod


class MockExecutionRepo:
    def __init__(self):
        self.trades = {}
        self.updates = []
        self._next_id = 1

    def save_trade(self, payload):
        trade_id = self._next_id
        self._next_id += 1
        record = dict(payload, id=trade_id)
        key = record.get("execution_key")
        if key:
            self.trades[key] = record
        return record

    def get_trade_by_execution_key(self, key):
        return self.trades.get(key)

    def update_trade(self, trade_id, updates):
        self.updates.append((trade_id, updates))
        for key, record in self.trades.items():
            if record.get("id") == trade_id:
                record.update(updates)
                return record
        return {"id": trade_id, **updates}

    def open_trades(self, source=None):
        return [t for t in self.trades.values() if t.get("status") == "OPEN"]


class MockPositionExecutor:
    def __init__(self, positions=None):
        self.positions = dict(positions or {})
        self.constraints = {
            "point": 0.01,
            "tick_size": 0.01,
            "digits": 2,
            "volume_min": 0.01,
            "volume_max": 100.0,
            "volume_step": 0.01,
        }

    def get_position(self, ticket):
        return self.positions.get(int(ticket))

    def get_symbol_constraints(self, symbol):
        return dict(self.constraints)

    def calculate_volume(self, symbol, direction, entry, sl, risk_amount):
        risk_dist = abs(entry - sl)
        volume = round(risk_amount / (risk_dist * 10.0), 2)
        actual_risk = volume * risk_dist * 10.0
        return {
            "volume": max(0.01, volume),
            "raw_volume": volume,
            "volume_max": 100.0,
            "volume_min": 0.01,
            "actual_risk_amount": actual_risk,
        }

    def normalize_market_stops(self, symbol, direction, entry, sl, tp, **kwargs):
        return {
            "valid": True,
            "entry_price": float(entry),
            "stop_loss": float(sl),
            "take_profit": float(tp),
            "constraints": self.constraints,
        }


class MockTradeLifecycleExecutor:
    def __init__(self, positions_dict):
        self.positions = positions_dict
        self.moves = []
        self.closes = []

    def move_stop_loss(self, position_ticket, stop_loss, take_profit=None, reason=""):
        ticket = int(position_ticket)
        self.moves.append((ticket, float(stop_loss), float(take_profit) if take_profit else None, reason))
        pos = self.positions.get(ticket)
        if pos:
            pos.sl = float(stop_loss)
            if take_profit is not None:
                pos.tp = float(take_profit)
        return {"modified": True}

    def close_position(self, position_ticket, exit_price=None, reason="manual_close"):
        ticket = int(position_ticket)
        self.closes.append((ticket, reason))
        if ticket in self.positions:
            del self.positions[ticket]
        return {"closed": True, "position_ticket": ticket, "reason": reason}


class MockDataProvider:
    def __init__(self, current_price=100.0, spread=0.04):
        self.current_price = current_price
        self.spread = spread

    def get_current_tick(self, symbol):
        bid = self.current_price - self.spread / 2.0
        ask = self.current_price + self.spread / 2.0
        return {"bid": bid, "ask": ask, "time": pd.Timestamp.now(tz="UTC")}

    def get_candles(self, symbol, timeframe, count=80):
        dates = pd.date_range("2026-09-01", periods=count, freq="5min", tz="UTC")
        return pd.DataFrame({
            "time": dates,
            "open": [100.0 + i * 0.1 for i in range(count)],
            "high": [100.2 + i * 0.1 for i in range(count)],
            "low": [99.8 + i * 0.1 for i in range(count)],
            "close": [100.1 + i * 0.1 for i in range(count)],
            "tick_volume": [1000] * count,
        })


def mock_build_plan_factory(entry, sl, direction, total_risk_amount):
    """Produces planned legs with accurate 50/50 sizing for $10,000 capital."""
    risk_dist = abs(entry - sl)

    def build_plan(specs, mode):
        legs = []
        for item in specs:
            name = item[0]
            fraction = item[1]
            target_rr = item[2]
            broker_target_rr = item[3] if len(item) == 4 else target_rr
            leg_risk = total_risk_amount * fraction
            tp_price = entry + risk_dist * broker_target_rr if direction == "BUY" else entry - risk_dist * broker_target_rr
            legs.append({
                "name": name,
                "risk_fraction": fraction,
                "risk_amount": leg_risk,
                "actual_risk_amount": leg_risk,
                "actual_risk_percent": fraction * (total_risk_amount / 10000.0) * 100.0,
                "target_rr": target_rr,
                "logical_target_rr": target_rr,
                "broker_target_rr": broker_target_rr,
                "take_profit": tp_price,
                "execution_key": f"mock_key:{name}",
            })
        return legs, None

    return build_plan


# -------------------------------------------------------------------------
# Test 1: Unified 1% Risk Allocation & Dual 0.5% Legs across All 4 Strategies
# -------------------------------------------------------------------------
@pytest.mark.parametrize("strategy_name,expected_tp1_rr,expected_tp2_rr", [
    ("ORB_NEW_YORK", 1.0, 2.0),
    ("GOLD_QUARTERS", 1.0, 2.0),
    ("SMC", 1.0, 2.0),
    ("MALAYSIAN_SNR", 1.0, 2.0),
])
def test_all_strategies_calculate_1pct_total_risk_and_split_into_two_half_pct_legs(
    strategy_name, expected_tp1_rr, expected_tp2_rr
):
    """Verifies that for an account of $10,000 USD (1% = $100 USD total risk):
    - Each operation executes 2 legs of 50% each ($50 USD risk each = 0.5%).
    - Leg 1 (TP1) targets 1:1 R:R (+ $50 USD gain).
    - Leg 2 (RUNNER) targets TP2 at 1:2 R:R (+ $100 USD gain).
    """
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(
        risk_percent=1.0,
        orb_risk_percent=1.0,
        split_entries_enabled=True,
        split_entry_risk_fraction=0.50,
        first_target_rr=1.0,
        second_target_rr=2.0,
        runner_extension_enabled=True,
        runner_extension_max_target_rr=4.0,
        smc_runner_max_target_rr=4.0,
    )
    engine._is_forex_symbol = lambda s: False
    engine._is_volatility_symbol = lambda s: False
    engine._is_jump_symbol = lambda s: False

    account_balance = 10000.0
    total_risk_percent = engine._risk_percent_for_strategy(strategy_name)
    total_risk_amount = account_balance * total_risk_percent / 100.0

    # Total risk MUST be exactly $100 USD (1% of $10,000 USD)
    assert total_risk_percent == 1.0
    assert total_risk_amount == 100.0

    entry = 100.0
    sl = 90.0  # Risk distance = 10.0
    direction = "BUY"

    build_plan = mock_build_plan_factory(entry, sl, direction, total_risk_amount)

    signal = {
        "strategy_name": strategy_name,
        "direction": direction,
        "entry_price": entry,
        "stop_loss": sl,
        "tp1_rr": 1.0,
        "runner_rr": 2.0,
    }

    legs, split_failure, single_failure, mode = engine._plan_execution_legs(
        exact_symbol="TEST_SYM",
        direction=direction,
        entry=entry,
        sl=sl,
        rr=2.0,
        strategy_name=strategy_name,
        signal=signal,
        total_risk_amount=total_risk_amount,
        risk_fraction=0.50,
        silver_risk_cap=False,
        build_plan=build_plan,
    )

    assert split_failure is None
    assert mode == "SPLIT"
    assert len(legs) == 2

    # Leg 1: TP1
    tp1 = legs[0]
    assert tp1["name"] == "TP1"
    assert tp1["risk_amount"] == 50.0       # Exactly $50 USD (50% of $100)
    assert tp1["actual_risk_percent"] == 0.5 # Exactly 0.5% of $10,000
    assert tp1["target_rr"] == expected_tp1_rr # Exactly 1.0 R:R (+ $50 USD gain)
    assert tp1["take_profit"] == 110.0      # 100 + 10 * 1.0 = 110.0

    # Leg 2: RUNNER (TP2)
    runner = legs[1]
    assert runner["name"] == "RUNNER"
    assert runner["risk_amount"] == 50.0       # Exactly $50 USD (50% of $100)
    assert runner["actual_risk_percent"] == 0.5 # Exactly 0.5% of $10,000
    assert runner["target_rr"] == expected_tp2_rr # Exactly 2.0 R:R (+ $100 USD gain)


# -------------------------------------------------------------------------
# Test 2: Break Even with Spread Protection Activated When TP1 Closes
# -------------------------------------------------------------------------
@pytest.mark.parametrize("strategy_name", ["ORB_NEW_YORK", "GOLD_QUARTERS", "SMC", "MALAYSIAN_SNR"])
def test_all_strategies_move_runner_to_break_even_plus_spread_when_tp1_closes(strategy_name):
    """Verifies that the moment TP1 closes in profit (+ $50 USD), the RUNNER
    moves Stop Loss to Break Even protecting live broker spread and offset points.
    """
    repo = MockExecutionRepo()
    entry = 100.0
    initial_sl = 90.0
    spread = 0.04
    provider = MockDataProvider(current_price=105.0, spread=spread)

    runner_pos = SimpleNamespace(
        ticket=1002,
        price_open=entry,
        price_current=105.0,
        sl=initial_sl,
        tp=140.0,
    )
    positions = {1002: runner_pos}
    pos_executor = MockPositionExecutor(positions)
    lifecycle_executor = MockTradeLifecycleExecutor(positions)

    # 1. Sibling TP1 is CLOSED with WIN (+ $50 USD)
    tp1_record = repo.save_trade({
        "execution_key": "ORDER_1:TP1",
        "instrument": "XAUUSD" if "GOLD" in strategy_name else "US30" if "ORB" in strategy_name else "Jump 25 Index",
        "direction": "BUY",
        "status": "CLOSED",
        "result": "WIN",
        "realized_rr": 1.0,
        "profit": 50.0,
        "entry_price": entry,
        "exit_price": 110.0,
        "stop_loss": initial_sl,
    })

    # 2. RUNNER is currently OPEN at entry
    runner_record = repo.save_trade({
        "execution_key": "ORDER_1:RUNNER",
        "broker_position_ticket": "1002",
        "instrument": tp1_record["instrument"],
        "direction": "BUY",
        "status": "OPEN",
        "entry_price": entry,
        "stop_loss": initial_sl,
        "take_profit": 140.0,
        "planned_rr": 2.0,
        "details": {
            "metadata": {
                "parent_execution_key": "ORDER_1",
                "trade_leg": "RUNNER",
                "strategy_name": strategy_name,
                "initial_stop_loss": initial_sl,
                "break_even_enabled": True,
            }
        },
    })

    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(
        execution_enabled=True,
        break_even_enabled=True,
        break_even_offset_points=2,
        break_even_profit_lock_rr_fraction=0.0,
        runner_extension_enabled=True,
        runner_extension_first_trigger_rr=2.0,
    )
    engine.repository = repo
    engine.executor = pos_executor
    engine.provider = provider
    engine.lifecycle_manager = SimpleNamespace(trade_executor=lifecycle_executor)
    engine._market_availability_cache = None
    engine._trade_owned_by_current_bot = lambda t: True
    engine._trade_metadata = lambda t: dict((t.get("details") or {}).get("metadata") or {})
    engine._break_even_initial_stop = lambda t, m: float(m.get("initial_stop_loss") or t.get("stop_loss"))
    engine._update_excursion_metrics = lambda *args: (args[1], False)
    engine._break_even_price_tolerance = lambda s, e: 0.001
    engine._orb_fixed_exit_policy = lambda m: m.get("strategy_name") == "ORB_NEW_YORK"
    engine._gold_tp1_break_even_guard = lambda *a, **k: {
        "eligible": True,
        "reached": True,
        "observed_price": 105.0,
        "bid": 104.98,
        "ask": 105.02,
        "reason": "TP1_REACHED",
    }
    engine._protect_forex_position_for_high_impact_news = lambda **k: None
    engine._analysis_invalidation_exit = lambda **k: {"managed": False, "closed": False}
    engine._is_crash_symbol = lambda s: False
    engine._persist_live_position_market_snapshots = lambda s: {"errors": []}
    engine.reporting_service = None

    # Execute monitor step
    result = engine._monitor_break_even_positions()

    # The runner must have had its stop loss moved to Break Even protecting the spread
    assert lifecycle_executor.moves, "Expected Stop Loss modification for Break Even"
    last_move = lifecycle_executor.moves[-1]
    ticket, new_sl, new_tp, reason = last_move

    assert ticket == 1002
    # Break Even price MUST be greater than entry (100.0) protecting spread (0.04) + offset (2 pts = 0.02)
    assert new_sl >= entry + spread, f"New SL {new_sl} does not protect spread {spread} above entry {entry}"
    assert runner_pos.sl == new_sl

    # Trade metadata reflects confirmed Break Even
    updated_meta = runner_record["details"]["metadata"]
    assert updated_meta.get("break_even_confirmed") is True or updated_meta.get("break_even_activated") is True


# -------------------------------------------------------------------------
# Test 3: Runner Behavior at TP2 (No Continuation -> Closes with + $100 Profit)
# -------------------------------------------------------------------------
@pytest.mark.parametrize("strategy_name", ["ORB_NEW_YORK", "GOLD_QUARTERS", "SMC", "MALAYSIAN_SNR"])
def test_all_strategies_runner_closes_at_tp2_when_no_continuation(monkeypatch, strategy_name):
    """Verifies that at TP2 (2.0 R:R = + $100 USD profit):
    - First locks +1.0 R profit in broker.
    - Evaluates continuation.
    - If NO continuation exists, closes position to secure ~2.0 R (+$100 USD profit).
    """
    repo = MockExecutionRepo()
    entry = 100.0
    initial_sl = 90.0  # Risk = 10.0
    current_price = 120.5  # At > 2.0 R (TP2)

    runner_pos = SimpleNamespace(
        ticket=2001,
        price_open=entry,
        price_current=current_price,
        sl=100.06,  # Currently in Break Even
        tp=140.0,
    )
    positions = {2001: runner_pos}
    pos_executor = MockPositionExecutor(positions)
    lifecycle_executor = MockTradeLifecycleExecutor(positions)

    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(
        execution_enabled=True,
        runner_extension_enabled=True,
        runner_extension_first_trigger_rr=2.0,
        runner_extension_first_lock_rr=1.0,
        runner_extension_max_target_rr=4.0,
        smc_runner_max_target_rr=4.0,
    )
    engine.repository = repo
    engine.executor = pos_executor
    engine.provider = MockDataProvider(current_price=current_price)
    engine.lifecycle_manager = SimpleNamespace(trade_executor=lifecycle_executor)

    # Mock NO continuation: trade momentum faded or opposing structure formed
    monkeypatch.setattr(
        live_mod,
        "evaluate_runner_continuation",
        lambda *args, **kwargs: RunnerExtensionDecision(
            continue_runner=False,
            reason="MOMENTUM_EXHAUSTED_NO_CONTINUATION",
            diagnostics={"trend": "WEAK"}
        ),
    )

    trade = {
        "id": 99,
        "broker_position_ticket": "2001",
        "instrument": "Volatility 75 Index",
        "direction": "BUY",
        "details": {
            "metadata": {
                "trade_leg": "RUNNER",
                "strategy_name": strategy_name,
                "initial_stop_loss": initial_sl,
            }
        },
    }
    metadata = dict(trade["details"]["metadata"])

    result = engine._manage_runner_extension(
        trade=trade,
        position=runner_pos,
        metadata=metadata,
        initial_stop_loss=initial_sl,
        current_rr=2.05,
        move_stop=lifecycle_executor.move_stop_loss,
    )

    # 1. Profit must be locked at 1.0 R (+ $50 USD)
    assert result["profit_lock_rr"] == 1.0
    assert runner_pos.sl == 110.0  # entry 100 + 1.0 * 10 = 110.0

    # 2. Position MUST be closed to capture ~2.0 R gain (+ $100 USD)
    assert result["closed"] is True
    assert lifecycle_executor.closes, "Expected close_position to be called"
    closed_ticket, close_reason = lifecycle_executor.closes[-1]
    assert closed_ticket == 2001
    assert "no_continuation" in close_reason


# -------------------------------------------------------------------------
# Test 4: Runner Dynamic Extension to TP3 (+ $150 USD) and TP4 (+ $200 USD)
# -------------------------------------------------------------------------
@pytest.mark.parametrize("strategy_name", ["ORB_NEW_YORK", "GOLD_QUARTERS", "SMC", "MALAYSIAN_SNR"])
def test_all_strategies_runner_extends_to_tp3_and_tp4_with_continuation(monkeypatch, strategy_name):
    """Verifies that when market continuation is confirmed:
    - At 2.0 R: locks 1.0 R (+ $50 USD) and extends target to 3.0 R (TP3 = + $150 USD).
    - At 3.0 R: locks 2.0 R (+ $100 USD) and extends target to 4.0 R (TP4 = + $200 USD).
    """
    repo = MockExecutionRepo()
    entry = 100.0
    initial_sl = 90.0  # Risk = 10.0

    runner_pos = SimpleNamespace(
        ticket=3001,
        price_open=entry,
        price_current=120.5,
        sl=100.06,  # In BE
        tp=120.0,
    )
    positions = {3001: runner_pos}
    pos_executor = MockPositionExecutor(positions)
    lifecycle_executor = MockTradeLifecycleExecutor(positions)

    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(
        execution_enabled=True,
        runner_extension_enabled=True,
        runner_extension_first_trigger_rr=2.0,
        runner_extension_first_lock_rr=1.0,
        runner_extension_second_trigger_rr=3.0,
        runner_extension_second_lock_rr=2.0,
        runner_extension_max_target_rr=4.0,
        smc_runner_max_target_rr=4.0,
    )
    engine.repository = repo
    engine.executor = pos_executor
    engine.provider = MockDataProvider(current_price=120.5)
    engine.lifecycle_manager = SimpleNamespace(trade_executor=lifecycle_executor)

    # Mock continuation CONFIRMED
    monkeypatch.setattr(
        live_mod,
        "evaluate_runner_continuation",
        lambda *args, **kwargs: RunnerExtensionDecision(
            continue_runner=True,
            reason="STRONG_TREND_CONTINUATION",
            diagnostics={"adx": 35.0}
        ),
    )

    trade = {
        "id": 105,
        "broker_position_ticket": "3001",
        "instrument": "Volatility 75 Index",
        "direction": "BUY",
        "details": {
            "metadata": {
                "trade_leg": "RUNNER",
                "strategy_name": strategy_name,
                "initial_stop_loss": initial_sl,
            }
        },
    }
    metadata = dict(trade["details"]["metadata"])

    # --- STAGE 1: Price reaches 2.0 R -> Extends to 3.0 R ---
    res_2r = engine._manage_runner_extension(
        trade=trade,
        position=runner_pos,
        metadata=metadata,
        initial_stop_loss=initial_sl,
        current_rr=2.05,
        move_stop=lifecycle_executor.move_stop_loss,
    )

    assert res_2r["extended"] is True
    assert res_2r["stage"] == "2R_TO_3R"
    assert res_2r["profit_lock_rr"] == 1.0
    assert runner_pos.sl == 110.0  # +1.0 R profit locked (+ $50 USD)
    assert metadata["runner_extension_stage"] == "EXTENDED_TO_3R"

    # --- STAGE 2: Price reaches 3.0 R -> Extends to 4.0 R ---
    runner_pos.price_current = 130.5
    res_3r = engine._manage_runner_extension(
        trade=trade,
        position=runner_pos,
        metadata=metadata,
        initial_stop_loss=initial_sl,
        current_rr=3.05,
        move_stop=lifecycle_executor.move_stop_loss,
    )

    assert res_3r["extended"] is True
    assert res_3r["stage"] == "3R_TO_4R"
    assert res_3r["profit_lock_rr"] == 2.0
    assert runner_pos.sl == 120.0  # +2.0 R profit locked (+ $100 USD)
    assert metadata["runner_extension_stage"] == "EXTENDED_TO_4R"
    assert res_3r["target_rr"] == 4.0  # Seeking TP4 (+ $200 USD)


# -------------------------------------------------------------------------
# Test 5: TP1 Closes Immediately When Crossing 1.0R / 2.0R (No Persisting Open)
# -------------------------------------------------------------------------
@pytest.mark.parametrize("strategy_name,target_rr", [
    ("MALAYSIAN_SNR", 1.0),
    ("ORB_NEW_YORK", 1.0),
    ("GOLD_QUARTERS", 1.0),
    ("ICT", 2.0),
])
def test_tp1_closes_immediately_when_crossing_target_rr_and_never_persists_open(strategy_name, target_rr):
    """Verifies that trades aiming for TP1 (Leg 1) close immediately at market
    as soon as price crosses the target R:R barrier (1.0 R for MSNR/ORB/GQ, 2.0 R for ICT),
    and NEVER persist open searching for more than TP1."""
    repo = MockExecutionRepo()
    entry = 100.0
    initial_sl = 90.0  # Risk = 10.0 points
    target_price = entry + target_rr * (entry - initial_sl)

    # 1. Price has NOT reached TP1 (e.g., at 0.5 R) -> Must stay open
    below_target_price = entry + 0.5 * (entry - initial_sl)
    tp1_pos = SimpleNamespace(
        ticket=5001,
        price_open=entry,
        price_current=below_target_price,
        sl=initial_sl,
        tp=target_price,
    )
    positions = {5001: tp1_pos}
    pos_executor = MockPositionExecutor(positions)
    lifecycle_executor = MockTradeLifecycleExecutor(positions)

    tp1_record = repo.save_trade({
        "id": 888,
        "execution_key": "ORDER_TEST:TP1",
        "broker_position_ticket": "5001",
        "instrument": "Volatility 75 Index",
        "direction": "BUY",
        "status": "OPEN",
        "entry_price": entry,
        "stop_loss": initial_sl,
        "take_profit": target_price,
        "planned_rr": target_rr,
        "details": {
            "metadata": {
                "parent_execution_key": "ORDER_TEST",
                "trade_leg": "TP1",
                "strategy_name": strategy_name,
                "initial_stop_loss": initial_sl,
                "target_rr": target_rr,
                "logical_target_rr": target_rr,
            }
        },
    })

    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(
        execution_enabled=True,
        break_even_enabled=True,
        split_entries_enabled=True,
    )
    engine.repository = repo
    engine.executor = pos_executor
    engine.lifecycle_manager = SimpleNamespace(trade_executor=lifecycle_executor)
    engine._trade_owned_by_current_bot = lambda t: True
    engine._trade_metadata = lambda t: dict((t.get("details") or {}).get("metadata") or {})
    engine._break_even_initial_stop = lambda t, m: float(m.get("initial_stop_loss") or t.get("stop_loss"))
    engine._update_excursion_metrics = lambda *args: (args[1], False)
    engine._break_even_price_tolerance = lambda s, e: 0.001
    engine._orb_fixed_exit_policy = lambda m: False
    engine._gold_tp1_break_even_guard = lambda *a, **k: {"eligible": False}
    engine._protect_forex_position_for_high_impact_news = lambda **k: None
    engine._analysis_invalidation_exit = lambda **k: {"managed": False, "closed": False}
    engine.sync_closed_trades = Mock(return_value=1)
    engine._persist_audit_event = Mock()

    # Pass 1: Price at 0.5R -> No close
    engine._monitor_break_even_positions()
    assert len(lifecycle_executor.closes) == 0, "TP1 should NOT close before crossing target R:R"

    # Pass 2: Price reaches or crosses TP1 target barrier (e.g. +1.05 R or +2.05 R for ICT)
    crossing_price = target_price + 0.5  # crossed barrier
    tp1_pos.price_current = crossing_price
    engine._monitor_break_even_positions()

    # Must close IMMEDIATELY at market without persisting open
    assert len(lifecycle_executor.closes) == 1, "TP1 MUST close immediately upon crossing target R:R"
    closed_ticket, close_reason = lifecycle_executor.closes[0]
    assert closed_ticket == 5001
    assert "tp1_target_reached" in close_reason
    assert engine.sync_closed_trades.called

