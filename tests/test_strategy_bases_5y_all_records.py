import json
import re
import unittest
from dashboard.strategy_bases_page import STRATEGY_BASES_HTML

class TestStrategyBases5YAllRecords(unittest.TestCase):
    def setUp(self):
        m_winners = re.search(r'const WINNERS_DATA = (\[.*?\]);', STRATEGY_BASES_HTML, re.DOTALL)
        self.assertIsNotNone(m_winners, "WINNERS_DATA not found in HTML")
        self.winners_data = json.loads(m_winners.group(1))

        m_losers = re.search(r'const LOSERS_DATA = (\[.*?\]);', STRATEGY_BASES_HTML, re.DOTALL)
        self.assertIsNotNone(m_losers, "LOSERS_DATA not found in HTML")
        self.losers_data = json.loads(m_losers.group(1))

    def test_total_records_count(self):
        # 73 instruments x 4 strategies = 292 total records
        self.assertEqual(len(self.winners_data), 292)

    def test_all_strategies_have_73_instruments(self):
        strategies = ["Malaysian SNR", "ICT Sabri Malle", "ORB New York", "Trend Pullback"]
        for strat in strategies:
            strat_items = [d for d in self.winners_data if d["strategy"] == strat]
            self.assertEqual(len(strat_items), 73, f"{strat} should have exactly 73 evaluated instruments")

    def test_jump_75_and_orb_exact_match(self):
        j75 = {d["strategy"]: d for d in self.winners_data if d["symbol"] == "Jump 75 Index"}
        self.assertEqual(len(j75), 4, "Jump 75 Index must be present in all 4 strategies")

        # Malaysian SNR: 412 trades, 70.4% WR, +$16,875.00 PnL
        msnr = j75["Malaysian SNR"]
        self.assertEqual(msnr["trades"], 412)
        self.assertEqual(msnr["win_rate"], 70.4)
        self.assertEqual(msnr["pnl"], 16875.0)
        self.assertTrue(msnr["is_profitable"])

        # ICT Sabri Malle: 1218 trades, 54.9% WR, +$11,862.00 PnL
        ict = j75["ICT Sabri Malle"]
        self.assertEqual(ict["trades"], 1218)
        self.assertEqual(ict["win_rate"], 54.9)
        self.assertEqual(ict["pnl"], 11862.0)
        self.assertTrue(ict["is_profitable"])

        # Trend Pullback: 1195 trades, 52.0% WR, +$6,550.00 PnL
        tp = j75["Trend Pullback"]
        self.assertEqual(tp["trades"], 1195)
        self.assertEqual(tp["win_rate"], 52.0)
        self.assertEqual(tp["pnl"], 6550.0)
        self.assertTrue(tp["is_profitable"])

        # ORB New York: 0 trades, Incompatible 24/7
        orb = j75["ORB New York"]
        self.assertEqual(orb["trades"], 0)
        self.assertFalse(orb["is_profitable"])
        self.assertIn("Incompatible", orb["status"])

        # ORB XAUUSD: 242 trades, 62.4% WR, +$7,105.00 PnL
        xau_orb = next(d for d in self.winners_data if d["symbol"] == "XAUUSD" and d["strategy"] == "ORB New York")
        self.assertEqual(xau_orb["trades"], 242)
        self.assertEqual(xau_orb["win_rate"], 62.4)
        self.assertEqual(xau_orb["pnl"], 7105.0)

    def test_status_filters_and_page_loading_dismiss(self):
        # 3-way status filter controls
        self.assertIn('id="statusFilterAll"', STRATEGY_BASES_HTML)
        self.assertIn('id="statusFilterActive"', STRATEGY_BASES_HTML)
        self.assertIn('id="statusFilterPruned"', STRATEGY_BASES_HTML)
        self.assertIn('changeStatusFilter', STRATEGY_BASES_HTML)
        self.assertIn('pageLoading.dismiss()', STRATEGY_BASES_HTML)
        # ORB badge updated to 35 sesión NY
        self.assertIn('35 Sesión NY', STRATEGY_BASES_HTML)

    def test_orb_synthetic_exclusion_in_frontend_logic(self):
        # Check that javascript renderWinnersTable excludes synthetics for orb tab
        self.assertIn("currentTab === 'orb'", STRATEGY_BASES_HTML)
        self.assertIn("it.category.includes('Sintéticos')", STRATEGY_BASES_HTML)
        self.assertIn("currentStatusFilter === 'active'", STRATEGY_BASES_HTML)
        self.assertIn("currentStatusFilter === 'pruned'", STRATEGY_BASES_HTML)

if __name__ == '__main__':
    unittest.main()
