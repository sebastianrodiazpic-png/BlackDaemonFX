# -*- coding: utf-8 -*-
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
        # 254+ registros evaluados en total
        self.assertGreaterEqual(len(self.winners_data), 254)

    def test_all_strategies_have_evaluated_instruments(self):
        # Malaysian SNR, ICT y Trend Pullback evalúan los instrumentos
        expected_counts = {
            "Malaysian SNR": 65,
            "ICT": 65,
            "Trend Pullback": 60,
            "ORB New York": 21,
        }
        for strat, exp_count in expected_counts.items():
            strat_items = [d for d in self.winners_data if d["strategy"] == strat]
            self.assertEqual(len(strat_items), exp_count, f"{strat} should have exactly {exp_count} evaluated instruments")

    def test_jump_75_and_orb_exact_match(self):
        j75 = {d["strategy"]: d for d in self.winners_data if d["symbol"] == "Jump 75 Index"}
        # Jump 75 Index está presente en las estrategias aplicables a sintéticos
        self.assertGreaterEqual(len(j75), 3, "Jump 75 Index must be present in Malaysian SNR, ICT, and Trend Pullback")

        # Malaysian SNR Optimizado (M5 Fractal & Pinbar): 854 trades, 77.87% WR, +$72,870.00 PnL
        msnr = j75["Malaysian SNR"]
        self.assertEqual(msnr["trades"], 854)
        self.assertEqual(msnr["win_rate"], 77.87)
        self.assertEqual(msnr["pnl"], 72870.0)
        self.assertTrue(msnr["is_profitable"])

        # ICT: 1119 trades, 65.22% WR, +$74,202.00 PnL
        ict = j75["ICT"]
        self.assertEqual(ict["trades"], 1119)
        self.assertEqual(ict["win_rate"], 65.22)
        self.assertEqual(ict["pnl"], 74202.0)
        self.assertTrue(ict["is_profitable"])

        # Trend Pullback: 1070 trades, 60.96% WR, +$59,329.00 PnL
        tp = j75["Trend Pullback"]
        self.assertEqual(tp["trades"], 1070)
        self.assertEqual(tp["win_rate"], 60.96)
        self.assertEqual(tp["pnl"], 59329.0)
        self.assertTrue(tp["is_profitable"])

        # ORB New York: los sintéticos 24/7 sin campana física fueron purgados por incompatibles
        self.assertNotIn("ORB New York", j75)

        # ORB XAUUSD (Dual-Engine 5A): 439 trades, 71.46% WR, +$39,310.00 PnL (+393.10R)
        xau_orb = next(d for d in self.winners_data if d["symbol"] == "XAUUSD" and d["strategy"] == "ORB New York")
        self.assertEqual(xau_orb["trades"], 439)
        self.assertEqual(xau_orb["win_rate"], 71.46)
        self.assertEqual(xau_orb["pnl"], 39310.0)

    def test_no_incompatible_or_zero_trade_records(self):
        # Ningún registro debe tener status incompatible ni 0 trades
        for d in self.winners_data:
            self.assertGreater(d.get("trades", 0), 0, f"Record with 0 trades found: {d}")
            self.assertNotIn("incompatible", d.get("status", "").lower())
        for l in self.losers_data:
            self.assertGreater(l.get("trades", 0), 0, f"Loser record with 0 trades found: {l}")
            self.assertNotIn("incompatible", l.get("status", "").lower())

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

    def test_msnr_real_markets_5y_faithful_replay(self):
        # Activos evaluados de Malaysian SNR rentables
        msnr_items = [d for d in self.winners_data if d["strategy"] == "Malaysian SNR"]
        self.assertGreaterEqual(len(msnr_items), 65)
        self.assertTrue(all(d.get("is_profitable", False) for d in msnr_items))
        self.assertTrue(all("activo" in d.get("status", "").lower() for d in msnr_items))

        # Validar que los activos reales superaron el cuello de botella de la muestra demo (18-40 trades)
        xau = next(d for d in msnr_items if d["symbol"] == "XAUUSD")
        self.assertEqual(xau["trades"], 530)
        self.assertEqual(xau["win_rate"], 67.5)

        audusd = next(d for d in msnr_items if d["symbol"] == "AUDUSD")
        self.assertEqual(audusd["trades"], 410)
        self.assertEqual(audusd["win_rate"], 65.0)

        btcusd = next(d for d in msnr_items if d["symbol"] == "BTCUSD")
        self.assertEqual(btcusd["trades"], 350)
        self.assertEqual(btcusd["win_rate"], 63.8)

        # Validar que todos los PnL sean estrictamente numéricos (float/int) para evitar -$NaN en el frontend
        for d in self.winners_data:
            self.assertIsInstance(d.get("pnl"), (int, float), f"PnL no numérico en {d.get('symbol')}: {d.get('pnl')}")
            self.assertGreater(d.get("sl", 0), 0, f"SL inválido en {d.get('symbol')}")
            self.assertLess(d.get("sl", 0), d.get("trades", 0), f"SL mayor o igual a trades en {d.get('symbol')}")

        self.assertIn("34,057 trades evaluados (73 Activos Rentables / 73 Total · 100% Portafolio)", STRATEGY_BASES_HTML)

        # Validar arquitectura de workers dedicados: FOREX_SNR, COMMODITIES_SNR, INDICESB_SNR
        from app.main import BOT_PROFILES, FULL_MULTI_BOT_PROFILES
        self.assertIn("FOREX_SNR", BOT_PROFILES)
        self.assertIn("INDICESB_SNR", FULL_MULTI_BOT_PROFILES)
        self.assertNotIn("FOREX_SNR", FULL_MULTI_BOT_PROFILES)
        self.assertEqual(BOT_PROFILES["FOREX_SNR"]["mode"], "forex-snr-daemon")
        self.assertEqual(BOT_PROFILES["FOREX_SNR"]["magic"], 26082043)
        self.assertIn("EURUSD", BOT_PROFILES["FOREX_SNR"]["symbols"])

if __name__ == '__main__':
    unittest.main()
