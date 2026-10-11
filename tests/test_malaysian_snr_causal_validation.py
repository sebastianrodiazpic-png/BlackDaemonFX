"""Regression coverage for causal MSNR entries and conservative replay exits."""
import unittest
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy
from strategy.malaysian_snr.validation import closed_candles, av_levels, level_is_fresh, confirmed_retest, quasimodo_candidates
from tools.replay_msnr_live_faithful import HistoricalProvider, simulate


def candles(freq="h", count=40, start="2026-10-08"):
    return pd.DataFrame({"time": pd.date_range(start, periods=count, freq=freq, tz="UTC"),
                         "open": 100., "high": 102., "low": 98., "close": 101.})


class Provider:
    def __init__(self, frames):
        self.frames = frames
    def get_candles(self, symbol, timeframe, count=100):
        return self.frames.get(timeframe, pd.DataFrame()).tail(count)


class TestCausalMSNR(unittest.TestCase):
    def test_closure_boundary_and_epoch_timestamps(self):
        frame = candles(count=4)
        now = frame.time.iloc[-1] + pd.Timedelta(minutes=30)
        closed = closed_candles(frame, "H1", now)
        self.assertEqual(len(closed), 3)
        self.assertEqual(len(closed_candles(frame, "H1", now + pd.Timedelta(minutes=30))), 4)
        epochs = frame.copy()
        epochs["time"] = epochs.time.map(lambda timestamp: int(timestamp.timestamp()))
        epoch_closed = closed_candles(epochs, "H1", now)
        self.assertEqual(closed.time.tolist(), epoch_closed.time.tolist())
        pd.testing.assert_frame_equal(closed.drop(columns="time"), epoch_closed.drop(columns="time"))

    def test_corrupt_and_duplicate_data_rejected(self):
        for issue in ("duplicate", "nan", "range", "time"):
            frame = candles(count=4)
            if issue == "duplicate":
                frame.loc[1, "time"] = frame.time.iloc[0]
            elif issue == "nan":
                frame.loc[1, "close"] = np.nan
            elif issue == "range":
                frame.loc[1, "close"] = 105
            else:
                frame.loc[1, "time"] = pd.NaT
            with self.subTest(issue=issue), self.assertRaises(ValueError):
                closed_candles(frame, "H1", pd.Timestamp("2026-10-10", tz="UTC"))

    def test_fresh_uses_body_price_and_actual_intersection(self):
        frame = candles(count=5)
        frame.loc[0, ["open", "high", "low", "close"]] = [98, 110, 97, 100]
        frame.loc[1, ["open", "high", "low", "close"]] = [100, 108, 95, 96]
        frame.loc[2:3, ["open", "high", "low", "close"]] = [96, 99, 95, 97]
        level = av_levels(frame)[0]
        self.assertEqual(level["level"], 100)
        self.assertEqual(level["wick_bound"], 110)
        self.assertTrue(level_is_fresh(frame, level))
        frame.loc[2, "high"] = 100
        self.assertFalse(level_is_fresh(frame, level))
        frame.loc[2, ["open", "high", "low", "close"]] = [102, 104, 101, 103]
        self.assertTrue(level_is_fresh(frame, level))

    def test_retest_needs_intersection_recovery_and_no_chase(self):
        frame = candles(count=1)
        frame.loc[0, ["open", "high", "low", "close"]] = [99, 101, 98, 100.5]
        self.assertTrue(confirmed_retest(frame, 100, "BUY", 2))
        for prices in ([90, 92, 89, 91], [101, 101.5, 99, 100.5], [100, 104, 99, 103]):
            frame.loc[0, ["open", "high", "low", "close"]] = prices
            self.assertFalse(confirmed_retest(frame, 100, "BUY", 2))

    def test_timezone_conversion_and_session_endpoint(self):
        strategy = MalaysianSNRStrategy(Provider({}), MalaysianSNRConfig(allowed_symbols=()))
        instant = datetime(2026, 10, 9, 3, tzinfo=timezone.utc)
        shifted = pd.Timestamp(instant).tz_convert("America/Santiago").to_pydatetime()
        self.assertEqual(strategy.analyze_symbol("EURUSD", instant), strategy.analyze_symbol("EURUSD", shifted))
        self.assertEqual(strategy.analyze_symbol("EURUSD", datetime(2026, 10, 9, 11, tzinfo=timezone.utc))["reason"], "SESSION_FILTER_OUTSIDE_KILLZONE")

    def test_disabled_and_missing_daily_fail_closed(self):
        now = pd.Timestamp("2026-10-09 16:15", tz="UTC")
        h1 = candles(count=40)
        m15 = candles("15min", count=60, start="2026-10-09 01:15")
        strategy = MalaysianSNRStrategy(Provider({"H1": h1, "M15": m15}), MalaysianSNRConfig(allowed_symbols=(), enable_session_killzones_filter=False))
        self.assertEqual(strategy.analyze_symbol("Step Index", now)["reason"], "MISSING_CLOSED_D1")
        strategy.config.enabled = False
        self.assertEqual(strategy.analyze_symbol("Step Index", now)["reason"], "STRATEGY_DISABLED")

    def test_open_candle_changes_cannot_change_signal(self):
        h1 = candles(count=40)
        now = h1.time.iloc[-1] + pd.Timedelta(minutes=30)
        m15 = candles("15min", count=60, start=now - pd.Timedelta(hours=14, minutes=45))
        cfg = MalaysianSNRConfig(allowed_symbols=(), enable_daily_storyline_filter=False)
        provider = Provider({"H1": h1, "M15": m15})
        strategy = MalaysianSNRStrategy(provider, cfg)
        before = strategy.analyze_symbol("Step Index", now)
        provider.frames["H1"].loc[39, ["high", "close"]] = [999, 998]
        provider.frames["M15"].loc[59, ["high", "close"]] = [999, 998]
        self.assertEqual(before, strategy.analyze_symbol("Step Index", now))

    def test_real_fractal_signal_waits_for_post_break_confirmation(self):
        h1 = candles(count=40)
        h1.loc[37, ["open", "high", "low", "close"]] = [100, 103, 99, 101]
        h1.loc[38, ["open", "high", "low", "close"]] = [100, 102, 97, 100.5]
        h1.loc[39, ["open", "high", "low", "close"]] = [99, 105, 98, 104]
        break_close = h1.time.iloc[-1] + pd.Timedelta(hours=1)
        m15 = candles("15min", count=60, start=break_close - pd.Timedelta(hours=14, minutes=45))
        m15.loc[59, ["open", "high", "low", "close"]] = [102.9, 103.8, 102.8, 103.3]
        cfg = MalaysianSNRConfig(allowed_symbols=(), enable_daily_storyline_filter=False)
        provider = Provider({"H1": h1, "M15": m15})
        strategy = MalaysianSNRStrategy(provider, cfg)
        self.assertEqual(strategy.analyze_symbol("Step Index", break_close)["reason"], "WAITING_POST_BREAK_RETEST")
        now = break_close + pd.Timedelta(minutes=15)
        result = strategy.analyze_symbol("Step Index", now)
        self.assertTrue(result["valid"], result)
        self.assertEqual(result["signal"]["scenario"], "ESC_3_FRACTAL")
        self.assertEqual(result["signal"]["entry_time"], now.isoformat())
        repeated = strategy.analyze_symbol("Step Index", now + pd.Timedelta(minutes=1))
        self.assertEqual(repeated["signal"]["entry_time"], result["signal"]["entry_time"])
        provider.frames["M15"].loc[59, "open"] = 103.5
        self.assertFalse(strategy.analyze_symbol("Step Index", now)["valid"])

    def test_stop_obstacle_geometry_and_time(self):
        strategy = MalaysianSNRStrategy(None)
        args = dict(symbol="Step Index", direction="BUY", scenario="ESC_3_FRACTAL", entry_price=100,
                    stop_loss=90, risk_dist=10, adx=25, body_ratio=.7, ref_level=95, break_level=95, current_atr=10)
        self.assertFalse(strategy._build_confirmed_signal(**{**args, "stop_loss":110})["valid"])
        self.assertFalse(strategy._build_confirmed_signal(**args, obstacle_level=115)["valid"])
        self.assertFalse(strategy._build_confirmed_signal(**args, obstacle_level=119.5)["valid"])
        now = datetime(2026, 10, 9, 15, tzinfo=timezone.utc)
        result = strategy._build_confirmed_signal(**args, obstacle_level=122, now_utc=now)
        self.assertTrue(result["valid"])
        signal = result["signal"]
        self.assertGreaterEqual(signal["tp2_price"], signal["tp1_price"])
        self.assertLess(signal["tp2_price"], 122)
        self.assertIsNone(signal["success_probability"])
        self.assertEqual(signal["entry_time"], now.isoformat())

    def test_qm_requires_confirmed_alternating_swings(self):
        frame = candles(count=16)
        frame["high"] = [102,103,105,110,106,103,101,103,105,111,115,110,107,102,100,98]
        frame["low"] = [98,99,101,105,101,98,95,98,101,105,109,104,100,97,94,90]
        frame["open"] = (frame.high + frame.low) / 2
        frame["close"] = frame.open + .1
        patterns = quasimodo_candidates(frame)
        self.assertEqual(len(patterns), 1)
        self.assertEqual(patterns[0]["direction"], "SELL")
        self.assertEqual(patterns[0]["shoulder"], 110)
        self.assertFalse(quasimodo_candidates(frame.iloc[:12]))

    def test_historical_provider_uses_only_closed_data(self):
        frame = candles(count=5)
        provider = HistoricalProvider({"H1": frame})
        provider.now = frame.time.iloc[-1] + pd.Timedelta(minutes=15)
        self.assertEqual(len(provider.get_candles("Step Index", "H1")), 4)

    def test_ambiguous_runner_bar_prioritizes_be(self):
        rr, outcome, bars = simulate("BUY", 100, 90, 120, 130, [121, 131], [101, 99], [120, 125])
        self.assertEqual((rr, outcome, bars), (1., "TP1+BE", 2))

    def test_ambiguous_tp1_activation_and_gap_loss(self):
        self.assertEqual(simulate("BUY", 100, 90, 120, 130, [131], [99], [125])[0], 1.)
        self.assertEqual(simulate("BUY", 100, 90, 120, 130, [120], [80], [100], opens=[80])[0], -2.)

    def test_short_exits_on_ask_and_custom_tp1(self):
        self.assertEqual(simulate("SELL", 100, 110, 80, 70, [109], [90], [95], spreads=[2])[0], -1.)
        rr, outcome, _ = simulate("BUY", 100, 90, 115, 125, [126], [101], [125])
        self.assertEqual((rr, outcome), (2., "TP2"))

    def test_live_plan_preserves_obstacle_ceiling_after_quote_moves(self):
        from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
        engine = object.__new__(LiveTradingEngine)
        engine.config = LiveTradingConfig(bot_profile="MALAYSIAN_SNR", split_entries_enabled=True,
                                          runner_extension_enabled=True, runner_extension_max_target_rr=4,
                                          single_entry_fallback_enabled=True)
        engine._is_forex_symbol = lambda s: True
        engine._is_volatility_symbol = lambda s: False
        engine._is_jump_symbol = lambda s: False
        captured = []
        def build_plan(specs, mode):
            captured.append(specs)
            return [{"name":row[0]} for row in specs], None
        args = dict(exact_symbol="EURUSD", direction="BUY", entry=100.1, sl=90., rr=2.1,
                    strategy_name="MALAYSIAN_SNR", signal={"tp1_rr":2., "runner_rr":2.1,
                    "tp2_price":121., "obstacle_level":122.}, total_risk_amount=100.,
                    risk_fraction=.5, silver_risk_cap=False, build_plan=build_plan)
        self.assertIsNotNone(engine._plan_execution_legs(**args)[0])
        self.assertAlmostEqual(captured[0][1][3], (121.-100.1)/(100.1-90.))
        args["entry"] = 101.
        captured.clear()
        legs, failure, _, _ = engine._plan_execution_legs(**args)
        self.assertIsNone(legs)
        self.assertEqual(failure["code"], "MSNR_OBSTACLE_BEFORE_MINIMUM_TP1")
        self.assertFalse(captured)  # A single-entry fallback cannot bypass this guard.


if __name__ == "__main__":
    unittest.main()
