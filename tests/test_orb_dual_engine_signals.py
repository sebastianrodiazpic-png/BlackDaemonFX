# -*- coding: utf-8 -*-
import os
import unittest
from datetime import datetime, timezone
from strategy.orb.new_york_orb import NewYorkORBStrategy, ORBConfig

class TestORBDualEngineSignals(unittest.TestCase):
    def test_dual_engine_allows_up_to_two_signals(self):
        os.environ["DAEMONBLACKFX_ORB_DUAL_ENGINE"] = "1"
        try:
            strat = NewYorkORBStrategy(data_provider=None, config=ORBConfig())
            self.assertEqual(strat._max_signals_per_session(), 2)

            symbol = "US500"
            session_date = "2026-11-10"

            # Initially limit not reached
            limit, prev = strat._is_session_signal_limit_reached(symbol, session_date)
            self.assertFalse(limit)

            # First signal recorded
            strat.mark_signal_used(symbol, session_date, "2026-11-10T09:35:00")
            limit, prev = strat._is_session_signal_limit_reached(symbol, session_date)
            # Should NOT be reached because max is 2
            self.assertFalse(limit)

            # Same breakout key cannot be repeated
            limit_same, prev_same = strat._is_session_signal_limit_reached(symbol, session_date, current_key="2026-11-10T09:35:00")
            self.assertTrue(limit_same)

            # Different breakout key is allowed for 2nd trade
            limit_diff, _ = strat._is_session_signal_limit_reached(symbol, session_date, current_key="2026-11-10T10:15:00")
            self.assertFalse(limit_diff)

            # Second signal recorded
            strat.mark_signal_used(symbol, session_date, "2026-11-10T10:15:00")
            # Now limit of 2 is reached
            limit2, prev2 = strat._is_session_signal_limit_reached(symbol, session_date)
            self.assertTrue(limit2)
            self.assertEqual(prev2, "2026-11-10T10:15:00")
        finally:
            os.environ.pop("DAEMONBLACKFX_ORB_DUAL_ENGINE", None)

if __name__ == "__main__":
    unittest.main()
