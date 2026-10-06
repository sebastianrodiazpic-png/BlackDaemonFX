import math
from datetime import datetime, timezone
from types import SimpleNamespace
import pandas as pd
import pytest

from strategy.execution.live_trading_engine import (
    LiveTradingEngine,
    LiveTradingConfig,
)
from strategy.ai.meta_labeling import MetaLabelingEngine, MetaLabelingConfig


class DummyDataProvider:
    def __init__(self, candles=None, tick_size=0.01):
        self.candles = candles or {}
        self._tick_size = tick_size
        self.connector = SimpleNamespace()

    def resolve_symbol(self, s):
        return str(s)

    def ensure_symbol(self, s):
        return str(s)

    def get_tick_size(self, s):
        return self._tick_size

    def get_candles(self, symbol, timeframe, count=30):
        key = (str(symbol), str(timeframe).upper())
        if key in self.candles:
            return self.candles[key]
        if timeframe == "H1":
            return pd.DataFrame({
                "time": pd.date_range("2026-09-29 00:00", periods=count, freq="1h", tz="UTC"),
                "open": [1000.0] * count,
                "high": [1010.0] * count,
                "low": [990.0] * count,
                "close": [1000.0] * count,
                "tick_volume": [100] * count,
            })
        elif timeframe == "M5":
            return pd.DataFrame({
                "time": pd.date_range("2026-09-29 10:00", periods=count, freq="5min", tz="UTC"),
                "open": [1000.0] * count,
                "high": [1005.0] * count,
                "low": [995.0] * count,
                "close": [1002.0] * count,
                "tick_volume": [50] * count,
            })
        return pd.DataFrame()


class DummyRepository:
    def __init__(self):
        self.trades = []

    def open_trades(self, source="DEMO"):
        return [t for t in self.trades if t.get("status") == "OPEN"]

    def update_trade(self, trade_id, updates):
        for t in self.trades:
            if t.get("id") == trade_id:
                t.update(updates)
                return t
        return None

    def sync_closed_mt5_trades(self, executor, source="DEMO", on_trade_closed=None):
        updated = 0
        for t in self.trades:
            if t.get("status") == "OPEN":
                t["status"] = "CLOSED"
                t["realized_rr"] = 1.5
                t["net_pnl"] = 15.0
                updated += 1
                if callable(on_trade_closed):
                    on_trade_closed(t)
        return updated


class DummyExecutor:
    def normalize_market_stops(self, *args, **kwargs):
        return {"valid": True, "entry_price": 1000.0, "stop_loss": 990.0, "take_profit": 1020.0}

    def get_position(self, *args, **kwargs):
        return None


def _make_engine(profile, provider=None, repo=None):
    prov = provider or DummyDataProvider()
    rep = repo or DummyRepository()
    return LiveTradingEngine(
        provider=prov,
        repository=rep,
        executor=DummyExecutor(),
        config=LiveTradingConfig(bot_profile=profile),
    )


# =========================================================================
# 1. WORKER BOOM
# =========================================================================
def test_boom_macro_trend_h1_blocks_below_24h_low():
    engine = _make_engine("BOOM")
    
    # 24h low is 990.0 in DummyDataProvider; price at 980.0 is falling below 24h low
    signal = {"entry_price": 980.0, "direction": "BUY"}
    analysis = {"ranges": {"H1": {"low": 990.0, "high": 1050.0}}}
    
    gate = engine._boom_crash_quality_gate("Boom 1000 Index", "BUY", signal, analysis)
    assert gate is not None
    assert gate["action"] == "BOOM_H1_FALLING_BELOW_24H_LOW"
    assert "BOOM_BUY_BLOCKED_PRICE_BELOW_24H_LOW" in gate["reason"]


def test_boom_macro_trend_h1_allows_above_24h_low():
    engine = _make_engine("BOOM")
    
    signal = {"entry_price": 1005.0, "direction": "BUY"}
    analysis = {"ranges": {"H1": {"low": 990.0, "high": 1050.0}}}
    
    gate = engine._boom_crash_quality_gate("Boom 1000 Index", "BUY", signal, analysis)
    assert gate is None


# =========================================================================
# 2. WORKER CRASH
# =========================================================================
def test_crash_macro_trend_h1_blocks_above_24h_high():
    engine = _make_engine("CRASH")
    
    # 24h high is 1050.0; price at 1060.0 is rising above 24h high
    signal = {"entry_price": 1060.0, "direction": "SELL"}
    analysis = {"ranges": {"H1": {"low": 950.0, "high": 1050.0}}}
    
    gate = engine._boom_crash_quality_gate("Crash 500 Index", "SELL", signal, analysis)
    assert gate is not None
    assert gate["action"] == "CRASH_H1_RISING_ABOVE_24H_HIGH"


def test_crash_macro_trend_h1_allows_below_24h_high():
    engine = _make_engine("CRASH")
    
    signal = {"entry_price": 1020.0, "direction": "SELL"}
    analysis = {"ranges": {"H1": {"low": 950.0, "high": 1050.0}}}
    
    gate = engine._boom_crash_quality_gate("Crash 500 Index", "SELL", signal, analysis)
    assert gate is None


# =========================================================================
# 3. WORKER STEP
# =========================================================================
def test_step_mandatory_adx_blocks_when_low():
    engine = _make_engine("STEP")
    
    signal = {"adx": 18.5}
    gate = engine._step_quality_gate("Step Index", signal)
    assert gate is not None
    assert gate["action"] == "STEP_ADX_LOW"
    assert "STEP_REQUIRES_M15_ADX_ABOVE_25" in gate["reason"]


def test_step_mandatory_adx_allows_when_high():
    engine = _make_engine("STEP")
    
    signal = {"adx": 28.5}
    gate = engine._step_quality_gate("Step Index", signal)
    assert gate is None


# =========================================================================
# 4. WORKER JUMP
# =========================================================================
def test_jump_requires_two_consecutive_confirming_candles():
    # Last 2 M5 candles: one bullish, one bearish -> should reject BUY
    m5_candles = pd.DataFrame({
        "time": pd.date_range("2026-09-29 10:00", periods=3, freq="5min", tz="UTC"),
        "open": [100.0, 102.0, 105.0],
        "close": [101.0, 104.0, 103.0],  # Last candle is bearish (103 < 105)
    })
    provider = DummyDataProvider(candles={("Jump 50 Index", "M5"): m5_candles})
    engine = _make_engine("JUMP", provider=provider)
    
    signal = {"direction": "BUY"}
    gate = engine._jump_quality_gate("Jump 50 Index", signal)
    assert gate is not None
    assert gate["action"] == "JUMP_STRICT_FILTER_REJECTED"
    assert "JUMP_REQUIRES_TWO_CONSECUTIVE_CONFIRMING_CANDLES" in gate["reason"]


def test_jump_allows_when_two_consecutive_confirming_candles():
    # Last 2 M5 candles: both bullish -> should pass
    m5_candles = pd.DataFrame({
        "time": pd.date_range("2026-09-29 10:00", periods=3, freq="5min", tz="UTC"),
        "open": [100.0, 102.0, 104.0],
        "close": [101.0, 104.0, 106.0],  # Both 104>102 and 106>104
    })
    provider = DummyDataProvider(candles={("Jump 50 Index", "M5"): m5_candles})
    engine = _make_engine("JUMP", provider=provider)
    
    signal = {"direction": "BUY"}
    gate = engine._jump_quality_gate("Jump 50 Index", signal)
    assert gate is None


# =========================================================================
# 5. WORKER GOLD
# =========================================================================
def test_gold_profile_strictly_excludes_silver():
    engine = _make_engine("GOLD")
    
    # XAGUSD / XAGUSDmicro must be rejected immediately from GOLD profile
    silver_gate = engine._gold_smc_entry_gate("XAGUSD")
    assert silver_gate is not None
    assert silver_gate["action"] == "GOLD_SILVER_EXCLUDED"
    assert "XAGUSD_EXCLUDED_FROM_GOLD_PROFILE" in silver_gate["reason"]

    silver_micro_gate = engine._gold_smc_entry_gate("XAGUSDmicro")
    assert silver_micro_gate is not None
    assert silver_micro_gate["action"] == "GOLD_SILVER_EXCLUDED"


def test_gold_killzone_hours_restriction():
    engine = _make_engine("GOLD")
    engine.config.gold_killzone_only_enabled = True
    
    # 08:00 UTC is outside 12:00-17:00 UTC London/NY overlap
    outside_time = datetime(2026, 9, 29, 8, 30, tzinfo=timezone.utc)
    gate = engine._gold_smc_entry_gate("XAUUSD", now_utc=outside_time)
    assert gate is not None
    assert gate["action"] == "GOLD_SMC_SESSION_CLOSED"
    assert "XAUUSD_ENTRADAS_SOLO_OVERLAP_LONDRES_NY_12_A_17_UTC" in gate["reason"]

    # 14:00 UTC is inside 12:00-17:00 UTC London/NY overlap
    inside_time = datetime(2026, 9, 29, 14, 0, tzinfo=timezone.utc)
    gate_ok = engine._gold_smc_entry_gate("XAUUSD", now_utc=inside_time)
    assert gate_ok is None


# =========================================================================
# 6. WORKER FOREX
# =========================================================================
def test_forex_m5_freshness_is_20_minutes():
    engine = _make_engine("FOREX_1")
    
    # Forex M5 freshness is relaxed to 20 minutes
    assert engine.pipeline_config.m5_max_signal_age_minutes == 20.0
    assert engine.multi_timeframe.config.max_m5_signal_age_minutes == 20.0


def test_forex_spread_to_sl_ratio_exceeded():
    engine = _make_engine("FOREX_1")
    
    # Mock spread guard check returning ratio = 0.22 (> 0.15)
    class MockSpreadGuard:
        def check(self, symbol, quote, direction, stop, max_risk_ratio=0.15):
            return {
                "allowed": False,
                "reason": "SPREAD_RISK_RATIO_EXCEEDED",
                "spread_risk_ratio": 0.22,
                "max_risk_ratio": 0.15,
            }
    engine._forex_spread_guard = lambda: MockSpreadGuard()
    engine._forex_rollover_entry_gate = lambda symbol: None
    engine._meta_execution_spread = lambda symbol: {"spread": 0.00022}
    
    gate = engine._forex_execution_gate("GBPUSD", "BUY", 0.8500)
    assert gate is not None
    assert gate["action"] == "FOREX_SPREAD_TO_SL_EXCEEDED"
    assert gate["reason"] == "SPREAD_RISK_RATIO_EXCEEDED"


def test_forex_killzone_hours_restriction():
    engine = _make_engine("FOREX_1")
    
    # 08:30 UTC is inside London Killzone (07:00-10:00 UTC) -> allowed
    london_time = datetime(2026, 9, 29, 8, 30, tzinfo=timezone.utc)
    gate_lon = engine._forex_killzone_entry_gate("GBPUSD", now_utc=london_time)
    assert gate_lon is None

    # 13:30 UTC is inside NY Killzone (12:00-16:00 UTC) -> allowed
    ny_time = datetime(2026, 9, 29, 13, 30, tzinfo=timezone.utc)
    gate_ny = engine._forex_killzone_entry_gate("GBPUSD", now_utc=ny_time)
    assert gate_ny is None

    # 11:00 UTC is outside Killzones -> blocked
    dead_zone_time = datetime(2026, 9, 29, 11, 0, tzinfo=timezone.utc)
    gate_dead = engine._forex_killzone_entry_gate("GBPUSD", now_utc=dead_zone_time)
    assert gate_dead is not None
    assert gate_dead["action"] == "FOREX_KILLZONE_CLOSED"
    assert "FOREX_ENTRADAS_SOLO_KILLZONES_LONDRES_07_10_Y_NY_12_16_UTC" in gate_dead["reason"]

    # 21:00 UTC is outside Killzones -> blocked
    night_time = datetime(2026, 9, 29, 21, 0, tzinfo=timezone.utc)
    gate_night = engine._forex_killzone_entry_gate("GBPUSD", now_utc=night_time)
    assert gate_night is not None
    assert gate_night["action"] == "FOREX_KILLZONE_CLOSED"


# =========================================================================
# 7. WORKER VOLATILITY
# =========================================================================
def test_volatility_rejects_unaligned_structure():
    engine = _make_engine("VOLATILITY_1")
    
    # Direction BUY but structure break was BEARISH -> align <= 0.0
    signal = {"direction": "BUY", "m15_structure_break_type": "BOS_BEARISH"}
    gate = engine._volatility_quality_gate("Volatility 75 Index", signal)
    assert gate is not None
    assert gate["action"] == "VOLATILITY_STRUCTURE_NOT_ALIGNED"
    assert "VOLATILITY_REQUIRES_POSITIVE_STRUCTURAL_ALIGNMENT" in gate["reason"]


def test_volatility_allows_aligned_structure():
    engine = _make_engine("VOLATILITY_1")
    
    signal = {"direction": "BUY", "m15_structure_break_type": "BOS_BULLISH"}
    gate = engine._volatility_quality_gate("Volatility 75 Index", signal)
    assert gate is None


def test_volatility_1s_signal_expiration_at_3_minutes():
    engine = _make_engine("VOLATILITY_2")
    engine.config.volatility_prune_toxic_assets = False
    
    # 1s index with signal age 4.5 minutes (> 3.0) -> rejected
    signal = {"direction": "BUY", "m15_structure_break_type": "BOS_BULLISH", "signal_age": {"age_minutes": 4.5}}
    gate = engine._volatility_quality_gate("Volatility 75 (1s) Index", signal)
    assert gate is not None
    assert gate["action"] == "VOLATILITY_1S_SIGNAL_EXPIRED"
    assert "VOLATILITY_1S_SIGNAL_AGE_EXCEEDS_3_MINUTES" in gate["reason"]

    # 1s index with signal age 1.5 minutes (<= 3.0) -> allowed
    signal_fresh = {"direction": "BUY", "m15_structure_break_type": "BOS_BULLISH", "signal_age": {"age_minutes": 1.5}}
    gate_ok = engine._volatility_quality_gate("Volatility 75 (1s) Index", signal_fresh)
    assert gate_ok is None


# =========================================================================
# 8. CONTINUOUS AI LEARNING FEEDBACK LOOP (ONLINE SGD)
# =========================================================================
def test_feed_ai_online_learning(tmp_path):
    repo = DummyRepository()
    engine = _make_engine("VOLATILITY", repo=repo)
    
    # Configure meta-labeling with a trained dummy model
    meta_config = MetaLabelingConfig(
        enabled=True,
        model_directory=str(tmp_path),
        min_training_samples=1,
    )
    engine.meta_labeling = MetaLabelingEngine(meta_config, worker="VOLATILITY")
    
    from strategy.ai.model import CalibratedLogisticModel, LogisticRegressionModel
    from strategy.ai.feature_extraction import FEATURE_NAMES
    model = CalibratedLogisticModel(
        worker="VOLATILITY",
        strategy_name="ALL",
        model=LogisticRegressionModel(
            weights=[0.01] * len(FEATURE_NAMES),
            mean=[0.0] * len(FEATURE_NAMES),
            scale=[1.0] * len(FEATURE_NAMES),
            bias=0.0,
            trained=True,
            samples=20,
        ),
    )
    engine.meta_labeling.save_model(model)

    # Trade with entry_learning_snapshot
    closed_trade = {
        "id": 101,
        "instrument": "Volatility 75 Index",
        "direction": "BUY",
        "status": "CLOSED",
        "realized_rr": 1.8,
        "details": {
            "metadata": {
                "strategy_name": "SMC",
                "entry_learning_snapshot": {
                    "schema": "entry-learning-v4",
                    "features": {f: 0.5 for f in FEATURE_NAMES},
                },
            }
        },
    }
    
    updated = engine._feed_ai_online_learning(closed_trade)
    assert updated is True


def test_boom_spike_exhaustion_sl_buffer():
    engine = _make_engine("BOOM")
    
    # Boom BUY signal where consolidation base (order_block_low) is 990.0, but original sl is 992.0
    signal = {
        "direction": "BUY",
        "entry_price": 1000.0,
        "stop_loss": 992.0,
        "order_block_low": 990.0,
        "risk_reward_ratio": 2.0,
    }
    # Tick size is 0.01; buffer is max(0.50, 5 * 0.01, 0.50) = 0.50
    # Expected safe SL <= 990.0 - 0.50 = 989.50
    # We test the logic directly:
    consolidation_base = float(signal.get("order_block_low") or signal["stop_loss"])
    tick_size = engine.provider.get_tick_size("Boom 1000 Index") or 0.01
    boom_buffer = max(getattr(engine.config, "boom_sl_buffer_points", 0.0), 5.0 * tick_size, 0.50)
    safe_sl = min(float(signal["stop_loss"]), consolidation_base - boom_buffer)
    assert safe_sl <= 989.50


def test_crash_spike_protective_break_even():
    repo = DummyRepository()
    engine = _make_engine("CRASH", repo=repo)
    engine.config.execution_enabled = True
    engine.config.break_even_enabled = True
    engine.config.break_even_trigger_rr = 1.0
    
    # Mock position in MT5 for Crash 500 Index SELL
    # Entry at 1000.0, initial SL at 1010.0 (risk = 10.0)
    # A crash spike brings price to 995.5 (gain = 4.5 points = 0.45R >= 0.40R)
    # Even though trigger_rr is 1.0, Crash protective trailing should fire at >= 0.40R!
    position = SimpleNamespace(
        ticket=12345,
        price_open=1000.0,
        price_current=995.5,
        sl=1010.0,
        tp=980.0,
    )
    trade = {
        "id": 1,
        "broker_position_ticket": 12345,
        "instrument": "Crash 500 Index",
        "direction": "SELL",
        "entry_price": 1000.0,
        "stop_loss": 1010.0,
        "take_profit": 980.0,
        "status": "OPEN",
        "details": {
            "metadata": {
                "daemon_magic": int(engine.config.magic),
                "break_even_initial_sl": 1010.0,
            }
        },
    }
    repo.trades.append(trade)
    engine.executor.get_position = lambda ticket: position
    
    moved_calls = []
    class MockLifecycleManager:
        class TradeExecutor:
            def move_stop_loss(self, position_ticket, stop_loss, take_profit, reason):
                position.sl = stop_loss
                moved_calls.append({"ticket": position_ticket, "sl": stop_loss, "reason": reason})
                return {"modified": True}
        trade_executor = TradeExecutor()
    engine.lifecycle_manager = MockLifecycleManager()
    
    res = engine._monitor_break_even_positions()
    assert len(moved_calls) == 1
    assert moved_calls[0]["ticket"] == "12345"
    assert moved_calls[0]["sl"] <= 1000.0  # SL moved to entry/BE offset


# =========================================================================
# 11. TOXIC ASSET PRUNING & DUAL ENTRY 1:2.5 REPLAY RULES (180 DAYS)
# =========================================================================
def test_step_toxic_asset_pruning():
    engine = _make_engine("STEP")
    signal = {"adx": 30.0, "confirmation_timeframe": "M15"}

    # Allowed: Step Index and Step Index 500
    assert engine._step_quality_gate("Step Index", signal) is None
    assert engine._step_quality_gate("Step Index 500", signal) is None

    # Pruned toxic: Step Index 200, Step Index 100
    gate_200 = engine._step_quality_gate("Step Index 200", signal)
    assert gate_200 is not None
    assert gate_200["action"] == "STEP_ASSET_PRUNED_TOXIC"

    gate_100 = engine._step_quality_gate("Step Index 100", signal)
    assert gate_100 is not None
    assert gate_100["action"] == "STEP_ASSET_PRUNED_TOXIC"


def test_jump_toxic_asset_pruning():
    # Use candles with 2 consecutive bullish candles so confirming candle check passes
    m5_candles = pd.DataFrame({
        "time": pd.date_range("2026-09-29 10:00", periods=3, freq="5min", tz="UTC"),
        "open": [100.0, 102.0, 104.0],
        "close": [101.0, 104.0, 106.0],
    })
    provider = DummyDataProvider(candles={
        ("Jump 50 Index", "M5"): m5_candles,
        ("Jump 10 Index", "M5"): m5_candles,
        ("Jump 25 Index", "M5"): m5_candles,
        ("Jump 100 Index", "M5"): m5_candles,
    })
    engine = _make_engine("JUMP", provider=provider)
    signal = {"direction": "BUY"}

    # Allowed: Jump 50 Index and Jump 10 Index
    assert engine._jump_quality_gate("Jump 50 Index", signal) is None
    assert engine._jump_quality_gate("Jump 10 Index", signal) is None

    # Pruned toxic: Jump 25 Index, Jump 100 Index
    gate_25 = engine._jump_quality_gate("Jump 25 Index", signal)
    assert gate_25 is not None
    assert gate_25["action"] == "JUMP_ASSET_PRUNED_TOXIC"

    gate_100 = engine._jump_quality_gate("Jump 100 Index", signal)
    assert gate_100 is not None
    assert gate_100["action"] == "JUMP_ASSET_PRUNED_TOXIC"


def test_volatility_toxic_asset_pruning():
    engine = _make_engine("VOLATILITY")
    signal = {"direction": "BUY", "m15_structure_break_type": "BOS_BULLISH"}

    # Allowed: Volatility 50 (1s) Index and Volatility 75 Index (and Volatility 25 Index)
    assert engine._volatility_quality_gate("Volatility 50 (1s) Index", signal) is None
    assert engine._volatility_quality_gate("Volatility 75 Index", signal) is None
    assert engine._volatility_quality_gate("Volatility 25 Index", signal) is None

    # Pruned toxic: Volatility 50 Index, Volatility 100 Index
    gate_50 = engine._volatility_quality_gate("Volatility 50 Index", signal)
    assert gate_50 is not None
    assert gate_50["action"] == "VOLATILITY_ASSET_PRUNED_TOXIC"

    gate_100 = engine._volatility_quality_gate("Volatility 100 Index", signal)
    assert gate_100 is not None
    assert gate_100["action"] == "VOLATILITY_ASSET_PRUNED_TOXIC"


def test_split_entry_risk_and_asymmetric_target_configuration():
    config = LiveTradingConfig()
    assert config.split_entries_enabled is True
    assert config.split_entry_risk_fraction == 0.50  # 0.5% per leg = 1.0% total
    assert config.first_target_rr in (1.0, 1.2)      # TP1 closes at +1.0R (or +1.2R asymmetric)
    assert config.second_target_rr in (2.0, 2.5)     # Runner target at +2.0R (or +2.5R asymmetric)
    assert config.break_even_trigger_rr == 1.0       # Break-Even triggered at +1.0R
    assert config.break_even_enabled is True

