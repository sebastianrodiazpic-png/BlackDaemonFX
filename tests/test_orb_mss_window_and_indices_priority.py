"""Unit and regression tests for ORB MSS 5-bar confirmation window and American Indices scanning prioritization."""

import os
from datetime import datetime, timezone
import pandas as pd
import numpy as np
import pytest

from strategy.orb.new_york_orb import NewYorkORBStrategy, ORBConfig, is_orb_index_symbol
from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig


def make_orb_ny_candles(count=50, start_time="2026-10-15 08:30:00"):
    """Creates M5 candles with America/New_York timestamps."""
    times_ny = pd.date_range(start_time, periods=count, freq="5min", tz="America/New_York")
    times_utc = times_ny.tz_convert("UTC")
    df = pd.DataFrame({
        "time": times_utc,
        "time_ny": times_ny,
        "open": 2000.0, "high": 2005.0, "low": 1995.0, "close": 2002.0,
        "tick_volume": 1000
    })
    return df


class MockORBProvider:
    def __init__(self, df):
        self.df = df

    def get_candles(self, symbol, timeframe, count=350):
        return self.df.tail(count)

    def search_symbols(self, term):
        return [term]

    def get_symbol_info(self, symbol):
        return {"trade_mode": 4, "spread": 0.1, "point": 0.01}


def test_orb_prioritize_indices_in_engine():
    """Verifies that _prioritize_orb_symbols places American Indices at the front in order: US30, US Tech 100, US SP 500."""
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile="ORB")
    
    symbols = [
        "XAUUSD", "BTCUSD", "US Tech 100", "USDCAD", "Wall Street 30", "GBPUSD", "US SP 500", "US Oil"
    ]
    
    prioritized = engine._prioritize_orb_symbols(symbols)
    
    # First 3 must be the American indices in rank order
    assert prioritized[0] == "Wall Street 30"
    assert prioritized[1] == "US Tech 100"
    assert prioritized[2] == "US SP 500"
    # Remaining symbols follow
    assert set(prioritized[3:]) == {"XAUUSD", "BTCUSD", "USDCAD", "GBPUSD", "US Oil"}


def test_orb_prioritize_indices_disabled_by_env():
    """When DAEMONBLACKFX_ORB_PRIORITIZE_INDICES='0', order is untouched."""
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile="ORB")
    symbols = ["XAUUSD", "US Tech 100", "Wall Street 30"]
    
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("DAEMONBLACKFX_ORB_PRIORITIZE_INDICES", "0")
        res = engine._prioritize_orb_symbols(symbols)
        assert res == symbols


def build_orb_sweep_mss_df(mss_delay_bars=4):
    """
    Constructs an M5 sequence:
    09:30 - 09:45: Opening range (range_high=2010.0, range_low=1990.0, midpoint=2000.0)
    09:45: Sweep candle (earlier): sweeps low to 1985.0 (below range_low - buffer), closes back inside at 1993.0.
    Intermediate bars: remain between 1991.0 and 1998.0 without invalidating sweep low.
    At bar (earlier + mss_delay_bars): confirms MSS by closing above swing high (2010.0) and midpoint (2000.0) at 2014.0.
    """
    # 08:00 to 11:30 NY
    times_ny = pd.date_range("2026-10-15 08:00:00", "2026-10-15 11:00:00", freq="5min", tz="America/New_York")
    times_utc = times_ny.tz_convert("UTC")
    df = pd.DataFrame({
        "time": times_utc,
        "time_ny": times_ny,
        "open": 2000.0, "high": 2005.0, "low": 1995.0, "close": 2001.0,
        "tick_volume": 1000
    })

    # Opening Range: 09:30 (idx 18), 09:35 (idx 19), 09:40 (idx 20)
    # Range: high=2010.0, low=1990.0
    df.loc[18, ["open", "high", "low", "close"]] = [2000.0, 2010.0, 1995.0, 2005.0]
    df.loc[19, ["open", "high", "low", "close"]] = [2005.0, 2008.0, 1990.0, 1998.0]
    df.loc[20, ["open", "high", "low", "close"]] = [1998.0, 2004.0, 1992.0, 2000.0]

    # Post-range starts at idx 21 (09:45 NY).
    # Candle 21: SWEEP candle (sweeps low below 1990 - buffer, closes at 1993.0 inside)
    # before swing was 2010.0 (from idx 18, 19, 20)
    df.loc[21, ["open", "high", "low", "close", "tick_volume"]] = [1995.0, 1998.0, 1985.0, 1993.0, 2500]

    # Intermediate bars between sweep and MSS
    for i in range(1, mss_delay_bars):
        df.loc[21 + i, ["open", "high", "low", "close", "tick_volume"]] = [1994.0, 1999.0, 1991.0, 1996.0, 1500]

    # Confirming MSS bar at idx 21 + mss_delay_bars
    # Breaks previous swing high (2010.0) and midpoint (2000.0) -> close at 2014.0
    target_idx = 21 + mss_delay_bars
    df.loc[target_idx, ["open", "high", "low", "close", "tick_volume"]] = [1996.0, 2018.0, 1995.0, 2014.0, 3000]

    # Slice df up to target_idx
    eval_df = df.iloc[:target_idx + 1].copy()
    # To pass anti-repainting filter, now_utc must be after candle close (+5 min)
    now_utc = eval_df.iloc[-1]["time"].to_pydatetime() + pd.Timedelta(minutes=5)
    return eval_df, now_utc


def test_orb_mss_confirmation_at_4_bars_delay_succeeds_with_window_5():
    """When MSS confirms 4 bars after sweep, it succeeds with default mss_lookback_bars=5."""
    df, now_utc = build_orb_sweep_mss_df(mss_delay_bars=4)
    provider = MockORBProvider(df)
    cfg = ORBConfig(
        asset_profiles={
            "XAUUSD": {
                "allowed_modes": [],
                "sweep_enabled": True,
                "atr_buffer": 0.05,
                "max_range_atr_ratio": 3.0,
                "require_volume": False,
            }
        },
        mss_lookback_bars=5,
        entry_cutoff_enabled=False
    )
    strategy = NewYorkORBStrategy(provider, cfg)
    res = strategy.analyze_symbol("XAUUSD", now_utc)
    assert res["valid"], f"Expected valid confirmation, got reason: {res.get('reason')}"
    assert res["action"] == "ORB_SIGNAL_CONFIRMED"
    assert res["direction"] == "BUY"


def test_orb_mss_confirmation_at_4_bars_delay_rejected_when_window_is_3():
    """When mss_lookback_bars is set to 3, an MSS 4 bars after sweep is rejected with SIN_BARRIDO_MAS_MSS_CONFIRMADO."""
    df, now_utc = build_orb_sweep_mss_df(mss_delay_bars=4)
    provider = MockORBProvider(df)
    cfg = ORBConfig(
        asset_profiles={
            "XAUUSD": {
                "allowed_modes": [],
                "sweep_enabled": True,
                "atr_buffer": 0.05,
                "max_range_atr_ratio": 3.0,
                "require_volume": False,
            }
        },
        mss_lookback_bars=3,  # Window restricted to 3
        entry_cutoff_enabled=False
    )
    strategy = NewYorkORBStrategy(provider, cfg)
    res = strategy.analyze_symbol("XAUUSD", now_utc)
    assert not res["valid"]
    assert res["reason"] == "SIN_BARRIDO_MAS_MSS_CONFIRMADO"


def test_orb_mss_confirmation_at_5_bars_delay_succeeds_with_window_5():
    """When MSS confirms 5 bars after sweep, it validates under mss_lookback_bars=5."""
    df, now_utc = build_orb_sweep_mss_df(mss_delay_bars=5)
    provider = MockORBProvider(df)
    cfg = ORBConfig(
        asset_profiles={
            "XAUUSD": {
                "allowed_modes": [],
                "sweep_enabled": True,
                "atr_buffer": 0.05,
                "max_range_atr_ratio": 3.0,
                "require_volume": False,
            }
        },
        mss_lookback_bars=5,
        entry_cutoff_enabled=False
    )
    strategy = NewYorkORBStrategy(provider, cfg)
    res = strategy.analyze_symbol("XAUUSD", now_utc)
    assert res["valid"], f"Expected valid confirmation at 5 bars, got reason: {res.get('reason')}"
    assert res["action"] == "ORB_SIGNAL_CONFIRMED"


def test_orb_mss_confirmation_at_6_bars_delay_rejected_when_window_is_5():
    """When MSS confirms 6 bars after sweep, it is rejected under window=5."""
    df, now_utc = build_orb_sweep_mss_df(mss_delay_bars=6)
    provider = MockORBProvider(df)
    cfg = ORBConfig(
        asset_profiles={
            "XAUUSD": {
                "allowed_modes": [],
                "sweep_enabled": True,
                "atr_buffer": 0.05,
                "max_range_atr_ratio": 3.0,
                "require_volume": False,
            }
        },
        mss_lookback_bars=5,
        entry_cutoff_enabled=False
    )
    strategy = NewYorkORBStrategy(provider, cfg)
    res = strategy.analyze_symbol("XAUUSD", now_utc)
    assert not res["valid"]
    assert res["reason"] == "SIN_BARRIDO_MAS_MSS_CONFIRMADO"
