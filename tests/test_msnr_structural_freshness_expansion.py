"""Unit and regression tests for Malaysian SNR Level Freshness Expansion and Structural Freshness Lifecycle."""

import math
import os
import pandas as pd
import numpy as np
import pytest

from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy


def candles(freq="h", count=40, start="2026-10-08"):
    return pd.DataFrame({
        "time": pd.date_range(start, periods=count, freq=freq, tz="UTC"),
        "open": 100.0, "high": 102.0, "low": 98.0, "close": 101.0
    })


class MockProvider:
    def __init__(self, frames):
        self.frames = frames

    def get_candles(self, symbol, timeframe, count=100):
        return self.frames.get(timeframe, pd.DataFrame()).tail(count)


def build_break_and_retest_frames(retest_minutes=240, touch_penetration=0.0):
    """
    Builds an H1 breakout scenario and M15 pullback sequence.
    H1 break closes at index 39.
    M15 bars run from break until retest_minutes.
    At the final M15 bar, price touches the S&R level (103.0) and rejects cleanly.
    """
    h1 = candles("h", 40)
    h1.loc[37, ["open", "high", "low", "close"]] = [100.0, 103.0, 99.0, 101.0]
    h1.loc[38, ["open", "high", "low", "close"]] = [100.0, 102.0, 97.0, 100.5]
    h1.loc[39, ["open", "high", "low", "close"]] = [99.0, 105.0, 98.0, 104.0]
    break_closed_at = h1.time.iloc[-1] + pd.Timedelta(hours=1)

    m15_count = 60
    m15 = candles("15min", m15_count, break_closed_at - pd.Timedelta(hours=15))

    post_bars_count = max(1, retest_minutes // 15)
    post = candles("15min", post_bars_count, break_closed_at)
    post[["open", "high", "low", "close"]] = [105.4, 106.0, 105.2, 105.8]

    # Final bar touches the level 103.0 and forms a strong rejection (CRT sweep & close)
    retest_low = 103.0 - touch_penetration
    # open 103.2, high 104.2, low 102.9 (sweep), close 104.1 (body = 0.9 / 1.3 = 0.69, close location = 1.2/1.3 = 0.92)
    post.loc[len(post) - 1, ["open", "high", "low", "close"]] = [103.2, 104.2, 102.9, 104.1]

    # If retest_minutes >= 60, add synthetic H1 bars
    h1_bars_to_add = retest_minutes // 60
    if h1_bars_to_add > 0:
        extra_h1 = []
        for i in range(h1_bars_to_add):
            t = break_closed_at + pd.Timedelta(hours=i)
            extra_h1.append({"time": t, "open": 105.4, "high": 106.0, "low": 105.0, "close": 105.5})
        h1 = pd.concat([h1, pd.DataFrame(extra_h1)], ignore_index=True)

    frames = {"H1": h1, "M15": pd.concat([m15, post], ignore_index=True)}
    now = break_closed_at + pd.Timedelta(minutes=retest_minutes)
    return MockProvider(frames), now, break_closed_at


def test_structural_freshness_allows_clean_retest_at_4_hours():
    """Retest at 240 min (4h) passes with enable_structural_freshness=True (standard 180 min would expire)."""
    provider, now, break_closed_at = build_break_and_retest_frames(retest_minutes=240)
    cfg = MalaysianSNRConfig(
        allowed_symbols=(),
        enable_daily_storyline_filter=False,
        retest_window_minutes=180,  # Legacy 180 min base window
        enable_structural_freshness=True,
        structural_max_window_minutes=720,
        enable_m15_micro_stop=False,
        step_min_adx=0.0
    )
    strategy = MalaysianSNRStrategy(provider, cfg)
    result = strategy.analyze_symbol("Jump 25 Index", now)
    assert result["valid"], f"Expected valid confirmation, got: {result.get('reason')}"
    assert result["signal"]["entry_confirmation"] == "CRT_M15_SWEEP_AND_ABSORPTION_CLOSE"
    assert result["signal"]["structure_closed_at"] == break_closed_at.isoformat()


def test_legacy_mode_without_structural_freshness_expires_at_240m():
    """When structural freshness is disabled and retest_window=180, 240m retest correctly expires."""
    provider, now, _ = build_break_and_retest_frames(retest_minutes=240)
    cfg = MalaysianSNRConfig(
        allowed_symbols=(),
        enable_daily_storyline_filter=False,
        retest_window_minutes=180,
        enable_structural_freshness=False,  # Disabled
        enable_m15_micro_stop=False,
        step_min_adx=0.0
    )
    strategy = MalaysianSNRStrategy(provider, cfg)
    result = strategy.analyze_symbol("Jump 25 Index", now)
    assert not result["valid"]
    assert result["reason"] == "SETUP_EXPIRED"


def test_structural_freshness_allows_extended_retest_at_6_hours():
    """Retest at 360 min (6h) validates when level remains fresh."""
    provider, now, _ = build_break_and_retest_frames(retest_minutes=360)
    cfg = MalaysianSNRConfig(
        allowed_symbols=(),
        enable_daily_storyline_filter=False,
        retest_window_minutes=360,
        enable_structural_freshness=True,
        structural_max_window_minutes=720,
        enable_m15_micro_stop=False,
        step_min_adx=0.0
    )
    strategy = MalaysianSNRStrategy(provider, cfg)
    result = strategy.analyze_symbol("Jump 25 Index", now)
    assert result["valid"], f"Expected valid at 6h, got: {result.get('reason')}"


def test_structural_invalidation_still_rejects_even_within_structural_window():
    """If price breached invalidation level, structural freshness does NOT rescue the broken setup."""
    provider, now, _ = build_break_and_retest_frames(retest_minutes=240)
    # Breached invalidation level (stop/invalidation level was prev1.close = 97.0)
    provider.frames["M15"].loc[65, ["open", "high", "low", "close"]] = [98.0, 99.0, 95.0, 98.5]
    cfg = MalaysianSNRConfig(
        allowed_symbols=(),
        enable_daily_storyline_filter=False,
        enable_structural_freshness=True,
        structural_max_window_minutes=720,
        step_min_adx=0.0
    )
    strategy = MalaysianSNRStrategy(provider, cfg)
    result = strategy.analyze_symbol("Jump 25 Index", now)
    assert not result["valid"]
    assert result["reason"] == "SETUP_STRUCTURE_INVALIDATED"


def test_retest_past_structural_max_window_expires():
    """If retest occurs at 750 min (exceeding 720 min max window), it correctly expires."""
    provider, now, _ = build_break_and_retest_frames(retest_minutes=750)
    cfg = MalaysianSNRConfig(
        allowed_symbols=(),
        enable_daily_storyline_filter=False,
        enable_structural_freshness=True,
        structural_max_window_minutes=720,
        step_min_adx=0.0
    )
    strategy = MalaysianSNRStrategy(provider, cfg)
    result = strategy.analyze_symbol("Jump 25 Index", now)
    assert not result["valid"]
    assert result["reason"] == "SETUP_EXPIRED"


def test_retest_contact_buffer_atr():
    """Verifies that contact buffer allows touch registration when price reverses within contact buffer."""
    provider, now, _ = build_break_and_retest_frames(retest_minutes=120)
    # Put low at 104.70, close at 104.85
    provider.frames["M15"].loc[len(provider.frames["M15"]) - 1, ["open", "high", "low", "close"]] = [104.8, 105.2, 104.7, 104.85]

    # Case 1: contact buffer 0.0 and dynamic buffer False -> No touch registered -> WAITING_FIRST_RETEST
    cfg_strict = MalaysianSNRConfig(
        allowed_symbols=(),
        enable_daily_storyline_filter=False,
        retest_tolerance_atr=0.35,
        retest_contact_buffer_atr=0.0,
        dynamic_retest_buffer_enabled=False,
        enable_m15_micro_stop=False,
        step_min_adx=0.0
    )
    strat_strict = MalaysianSNRStrategy(provider, cfg_strict)
    res_strict = strat_strict.analyze_symbol("Jump 25 Index", now)
    assert not res_strict["valid"]
    assert res_strict["reason"] == "WAITING_FIRST_RETEST"

    # Case 2: contact buffer 0.15 -> touch registered within buffer
    cfg_buffer = MalaysianSNRConfig(
        allowed_symbols=(),
        enable_daily_storyline_filter=False,
        retest_tolerance_atr=0.35,
        retest_contact_buffer_atr=0.15,
        dynamic_retest_buffer_enabled=False,
        enable_m15_micro_stop=False,
        step_min_adx=0.0
    )
    strat_buffer = MalaysianSNRStrategy(provider, cfg_buffer)
    res_buffer = strat_buffer.analyze_symbol("Jump 25 Index", now)
    # The touch is registered and evaluated (either confirmed or waiting recovery, but NOT missing touch)
    assert res_buffer["reason"] != "WAITING_FIRST_RETEST"
