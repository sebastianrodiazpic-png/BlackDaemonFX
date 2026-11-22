# -*- coding: utf-8 -*-
import unittest
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
from unittest.mock import MagicMock

from strategy.ict.ict_strategy import ICTSabriMalleStrategy
from strategy.ict.config import ICTSabriMalleConfig

NEW_YORK = ZoneInfo("America/New_York")

class TestICTRealMarketsSpreadGate(unittest.TestCase):
    def setUp(self):
        self.mock_provider = MagicMock()
        self.config = ICTSabriMalleConfig()
        self.strat = ICTSabriMalleStrategy(data_provider=self.mock_provider, config=self.config)

    def test_sp500_outside_cash_hours_rejected(self):
        # 02:00 AM NY (mercado de contado de NYSE cerrado)
        dt = datetime(2026, 11, 10, 2, 0, tzinfo=NEW_YORK)
        res = self.strat.analyze_symbol("US SP 500", now_utc=dt)
        self.assertFalse(res["valid"])
        self.assertIn("OUTSIDE_INSTITUTIONAL_KILLZONE", res["reason"])

    def test_sp500_in_cash_hours_accepted_session(self):
        # 10:15 AM NY (mercado de contado abierto)
        dt = datetime(2026, 11, 10, 10, 15, tzinfo=NEW_YORK)
        # Mocking provider to fail later after session check
        self.mock_provider.get_candles.return_value = None
        res = self.strat.analyze_symbol("US SP 500", now_utc=dt)
        # Should pass session check and fail on data provider, NOT on killzone
        self.assertNotIn("OUTSIDE_INSTITUTIONAL_KILLZONE", res["reason"])

    def test_gold_rollover_guard_rejected(self):
        # 17:00 NY (horario estricto de rollover de commodities)
        dt = datetime(2026, 11, 10, 17, 0, tzinfo=NEW_YORK)
        res = self.strat.analyze_symbol("XAUUSD", now_utc=dt)
        self.assertFalse(res["valid"])
        self.assertEqual(res["reason"], "MARKET_ROLLOVER_SPREAD_GUARD")

if __name__ == "__main__":
    unittest.main()
