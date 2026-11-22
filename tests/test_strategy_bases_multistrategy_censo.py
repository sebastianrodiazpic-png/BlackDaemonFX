# -*- coding: utf-8 -*-
import json
import re
import unittest
from dashboard.strategy_bases_page import STRATEGY_BASES_HTML


class TestStrategyBasesMultiStrategyCenso(unittest.TestCase):
    def setUp(self):
        m_winners = re.search(r'const WINNERS_DATA = (\[.*?\]);', STRATEGY_BASES_HTML, re.DOTALL)
        self.assertIsNotNone(m_winners, "WINNERS_DATA not found in HTML")
        self.winners_data = json.loads(m_winners.group(1))

    def test_multistrategy_tab_in_nav_bar(self):
        self.assertIn("setStrategyTab('multistrategy')", STRATEGY_BASES_HTML)
        self.assertIn("MultiStrategia (Replay 5 Años)", STRATEGY_BASES_HTML)
        self.assertIn("81 Workers MT5", STRATEGY_BASES_HTML)

    def test_multistrategy_filter_in_javascript(self):
        self.assertIn("currentTab === 'multistrategy'", STRATEGY_BASES_HTML)
        self.assertIn("it.strategy !== 'MultiStrategia'", STRATEGY_BASES_HTML)

    def test_no_dummy_2600_or_3750_in_multistrategy(self):
        multi_items = [d for d in self.winners_data if d["strategy"] == "MultiStrategia"]
        self.assertEqual(len(multi_items), 81)
        for it in multi_items:
            self.assertNotEqual(it["trades"], 2600, f"Found placeholder 2600 trades for {it['symbol']}")
            self.assertNotEqual(it["trades"], 3750, f"Found placeholder 3750 trades for {it['symbol']}")
            self.assertNotEqual(it["trades"], 3650, f"Found placeholder 3650 trades for {it['symbol']}")

    def test_jump_family_census_exact_metrics(self):
        jump_map = {d["symbol"]: d for d in self.winners_data if d["strategy"] == "MultiStrategia" and "Jump" in d["symbol"]}
        self.assertEqual(len(jump_map), 5)

        # Jump 10 Index: 1478 trades, 64.4% WR, +$74,800.00 (+748.0R)
        j10 = jump_map["Jump 10 Index"]
        self.assertEqual(j10["trades"], 1478)
        self.assertEqual(j10["win_rate"], 64.4)
        self.assertEqual(j10["pnl"], 74800.0)
        self.assertTrue(j10["is_profitable"])
        self.assertIn("DEJAR ACTIVO", j10["status"])

        # Jump 25 Index: 1465 trades, 63.5% WR, +$65,140.00 (+651.4R)
        j25 = jump_map["Jump 25 Index"]
        self.assertEqual(j25["trades"], 1465)
        self.assertEqual(j25["win_rate"], 63.5)
        self.assertEqual(j25["pnl"], 65140.0)
        self.assertTrue(j25["is_profitable"])

        # Jump 75 Index: 1329 trades, 63.0% WR, +$60,280.00 (+602.8R)
        j75 = jump_map["Jump 75 Index"]
        self.assertEqual(j75["trades"], 1329)
        self.assertEqual(j75["win_rate"], 63.0)
        self.assertEqual(j75["pnl"], 60280.0)
        self.assertTrue(j75["is_profitable"])

        # Jump 50 Index: 1261 trades, 62.7% WR, +$56,360.00 (+563.6R)
        j50 = jump_map["Jump 50 Index"]
        self.assertEqual(j50["trades"], 1261)
        self.assertEqual(j50["win_rate"], 62.7)
        self.assertEqual(j50["pnl"], 56360.0)
        self.assertTrue(j50["is_profitable"])

        # Jump 100 Index: 1198 trades, 61.2% WR, +$50,300.00 (+503.0R)
        j100 = jump_map["Jump 100 Index"]
        self.assertEqual(j100["trades"], 1198)
        self.assertEqual(j100["win_rate"], 61.2)
        self.assertEqual(j100["pnl"], 50300.0)
        self.assertTrue(j100["is_profitable"])
        self.assertIn("DESBLOQUEAR", j100["status"])

    def test_step_family_census_exact_metrics(self):
        step_map = {d["symbol"]: d for d in self.winners_data if d["strategy"] == "MultiStrategia" and "Step" in d["symbol"]}
        self.assertIn("Step Index 200", step_map)
        self.assertIn("Step Index 400", step_map)
        self.assertIn("Step Index 500", step_map)

        s400 = step_map["Step Index 400"]
        self.assertEqual(s400["trades"], 1224)
        self.assertEqual(s400["win_rate"], 62.4)
        self.assertEqual(s400["pnl"], 54620.0)

        s500 = step_map["Step Index 500"]
        self.assertEqual(s500["trades"], 1195)
        self.assertEqual(s500["win_rate"], 61.5)
        self.assertEqual(s500["pnl"], 51020.0)

        # Worker STEP (2) (Large & Base Steps · Magic 26082406)
        for sym, (trades, wr, pnl) in {
            "Step Index": (1239, 62.2, 54490.0),
            "Step Index 300": (1215, 62.8, 53800.0),
            "Step Index 1000": (1180, 63.5, 56000.0),
            "Step Index 1500": (1140, 63.8, 57500.0),
            "Step Index 2000": (1110, 64.2, 59000.0),
        }.items():
            self.assertIn(sym, step_map)
            it = step_map[sym]
            self.assertEqual(it["trades"], trades)
            self.assertEqual(it["win_rate"], wr)
            self.assertEqual(it["pnl"], pnl)
            self.assertTrue(it["is_profitable"])
            self.assertIn("26082406", it["category"])

    def test_real_markets_and_forex_census_exact_metrics(self):
        multi_map = {d["symbol"]: d for d in self.winners_data if d["strategy"] == "MultiStrategia"}
        
        # Wall Street 30: 440 trades, 62.3% WR, +$11,380.00
        ws30 = multi_map["Wall Street 30"]
        self.assertEqual(ws30["trades"], 440)
        self.assertEqual(ws30["win_rate"], 62.3)
        self.assertEqual(ws30["pnl"], 11380.0)

        # XAUUSD: 504 trades, 61.6% WR, +$17,060.00
        xau = multi_map["XAUUSD"]
        self.assertEqual(xau["trades"], 504)
        self.assertEqual(xau["win_rate"], 61.6)
        self.assertEqual(xau["pnl"], 17060.0)

        # BTCUSD: 305 trades, 61.0% WR, +$9,450.00
        btc = multi_map["BTCUSD"]
        self.assertEqual(btc["trades"], 305)
        self.assertEqual(btc["win_rate"], 61.0)
        self.assertEqual(btc["pnl"], 9450.0)

        # GBPUSD: 450 trades, 60.0% WR, +$9,360.00
        gbp = multi_map["GBPUSD"]
        self.assertEqual(gbp["trades"], 450)
        self.assertEqual(gbp["win_rate"], 60.0)
        self.assertEqual(gbp["pnl"], 9360.0)

    def test_volatility_1_hf_and_2_special_exact_metrics(self):
        multi_map = {d["symbol"]: d for d in self.winners_data if d["strategy"] == "MultiStrategia"}

        # Worker VOLATILITY (1) (HF)
        hf100 = multi_map["High Frequency Vol 100 Index"]
        self.assertEqual(hf100["trades"], 1290)
        self.assertEqual(hf100["win_rate"], 68.3)
        self.assertEqual(hf100["pnl"], 73560.0)
        self.assertTrue(hf100["is_profitable"])
        self.assertIn("26082401", hf100["category"])

        hf10 = multi_map["High Frequency Vol 10 Index"]
        self.assertEqual(hf10["trades"], 1180)
        self.assertEqual(hf10["win_rate"], 65.4)
        self.assertEqual(hf10["pnl"], 54280.0)
        self.assertTrue(hf10["is_profitable"])

        # Worker VOLATILITY (2) (Special)
        ldown = multi_map["Ladder Volatility Down Index"]
        self.assertEqual(ldown["trades"], 890)
        self.assertEqual(ldown["win_rate"], 69.8)
        self.assertEqual(ldown["pnl"], 61240.0)
        self.assertTrue(ldown["is_profitable"])
        self.assertIn("VOLATILITY (2)", ldown["category"])

        vlow = multi_map["VolSwitch Low Vol Index"]
        self.assertEqual(vlow["trades"], 940)
        self.assertEqual(vlow["win_rate"], 64.9)
        self.assertEqual(vlow["pnl"], 46820.0)
        self.assertTrue(vlow["is_profitable"])
        self.assertIn("VOLATILITY (2)", vlow["category"])


if __name__ == "__main__":
    unittest.main()
