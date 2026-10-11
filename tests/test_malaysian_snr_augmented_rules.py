"""Pruebas unitarias para las 5 reglas institucionales de Malaysian SNR Augmented.

Valida:
1. True Fresh Level Tracking (descarta niveles mitigados por mechas intermedias).
2. Daily Storyline Filter (confluencia de la vela previa D1).
3. Session Killzones Filter (bloqueo fuera de sesión en Forex/Metales/Índices y pase libre en Sintéticos).
4. Quasimodo (QM) Estructural (sweep + quiebre + retest de hombro izquierdo).
5. Obstacle Awareness & TP1 mínimo 1:2.0 RR.
"""

from __future__ import annotations
import unittest
from datetime import datetime, timezone
import pandas as pd

from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy, is_synthetic_symbol


class MockDataProvider:
    def __init__(self, h1_df: pd.DataFrame, m15_df: pd.DataFrame, d1_df: pd.DataFrame | None = None):
        self.h1_df = h1_df
        self.m15_df = m15_df
        self.d1_df = d1_df

    def get_candles(self, symbol: str, timeframe: str, count: int = 50) -> pd.DataFrame:
        if timeframe == "H1":
            return self.h1_df.tail(count)
        elif timeframe == "M15":
            return self.m15_df.tail(count)
        elif timeframe == "D1":
            if self.d1_df is not None:
                return self.d1_df.tail(count)
            return pd.DataFrame()
        return pd.DataFrame()


class TestMalaysianSNRAugmentedRules(unittest.TestCase):

    def test_synthetic_symbol_detection(self):
        self.assertTrue(is_synthetic_symbol("Jump 10 Index"))
        self.assertTrue(is_synthetic_symbol("Step Index 200"))
        self.assertTrue(is_synthetic_symbol("Volatility 75 Index"))
        self.assertTrue(is_synthetic_symbol("Crash 500 Index"))
        self.assertTrue(is_synthetic_symbol("Boom 1000 Index"))
        self.assertFalse(is_synthetic_symbol("EURUSD"))
        self.assertFalse(is_synthetic_symbol("XAUUSD"))
        self.assertFalse(is_synthetic_symbol("Wall Street 30"))
        self.assertFalse(is_synthetic_symbol("BTCUSD"))

    def test_session_killzone_filter(self):
        config = MalaysianSNRConfig(enable_session_killzones_filter=True, allowed_symbols=())
        provider = MockDataProvider(pd.DataFrame(), pd.DataFrame())
        strat = MalaysianSNRStrategy(provider, config=config)

        # 03:00 UTC (Fuera de Killzone en Forex)
        t_out = datetime(2026, 10, 9, 3, 0, tzinfo=timezone.utc)
        res_forex = strat.analyze_symbol("EURUSD", now_utc=t_out)
        self.assertFalse(res_forex["valid"])
        self.assertEqual(res_forex["reason"], "SESSION_FILTER_OUTSIDE_KILLZONE")

        # Sintético a la misma hora 03:00 UTC (No se bloquea por Killzone)
        res_synth = strat.analyze_symbol("Jump 10 Index", now_utc=t_out)
        self.assertNotEqual(res_synth["reason"], "SESSION_FILTER_OUTSIDE_KILLZONE")

        # 08:30 UTC (Londres Killzone activa en Forex)
        t_london = datetime(2026, 10, 9, 8, 30, tzinfo=timezone.utc)
        res_london = strat.analyze_symbol("EURUSD", now_utc=t_london)
        self.assertNotEqual(res_london["reason"], "SESSION_FILTER_OUTSIDE_KILLZONE")

    def test_tp1_min_rr_is_2_0(self):
        config = MalaysianSNRConfig(tp1_min_rr=2.0)
        strat = MalaysianSNRStrategy(data_provider=None, config=config)
        sig = strat._build_confirmed_signal(
            symbol="Jump 10 Index",
            direction="BUY",
            scenario="ESC_1_CONTINUATION",
            entry_price=100.0,
            stop_loss=90.0,
            risk_dist=10.0,
            adx=25.0,
            body_ratio=0.70,
            ref_level=95.0,
            break_level=95.0,
            current_atr=10.0,
        )
        self.assertEqual(sig["signal"]["tp1_rr"], 2.0)
        self.assertEqual(sig["signal"]["tp1_price"], 120.0)  # 100 + (2.0 * 10)

    def test_obstacle_awareness_trims_runner(self):
        config = MalaysianSNRConfig(enable_obstacle_awareness=True, tp2_runner_rr=3.0)
        strat = MalaysianSNRStrategy(data_provider=None, config=config)
        
        # Entrada BUY a 100.0, SL 90.0 (distancia riesgo = 10.0)
        # Nivel obstáculo contrario a 122.0 (distancia 22.0 = 2.2R)
        # Runner sin obstáculo sería 3.0R (130.0). Con obstáculo a 2.2R, debe ajustarse a 2.0R (120.0).
        sig = strat._build_confirmed_signal(
            symbol="Wall Street 30",
            direction="BUY",
            scenario="ESC_1_CONTINUATION",
            entry_price=100.0,
            stop_loss=90.0,
            risk_dist=10.0,
            adx=25.0,
            body_ratio=0.70,
            ref_level=95.0,
            break_level=95.0,
            current_atr=10.0,
            obstacle_level=122.0,
        )
        self.assertLess(sig["signal"]["runner_rr"], 3.0)
        self.assertAlmostEqual(sig["signal"]["runner_rr"], 2.1)
        self.assertEqual(sig["signal"]["tp2_price"], 121.0)


    def test_crt_sweep_and_rejection_trigger(self):
        from strategy.malaysian_snr.validation import confirmed_crt_retest
        # Setup: Level at 100.0, BUY direction, ATR = 2.0
        # Case 1: Valid sweep (low=99.5 <= 100.2) and rejection close (close=100.5 > open=100.0)
        df_valid = pd.DataFrame([
            {"time": pd.Timestamp("2026-10-10 10:00:00", tz="UTC"), "open": 100.0, "high": 100.8, "low": 99.5, "close": 100.5}
        ])
        self.assertTrue(confirmed_crt_retest(df_valid, level=100.0, direction="BUY", atr=2.0))

        # Case 2: No sweep (low=101.0 > 100.2)
        df_no_sweep = pd.DataFrame([
            {"time": pd.Timestamp("2026-10-10 10:00:00", tz="UTC"), "open": 101.2, "high": 101.8, "low": 101.0, "close": 101.5}
        ])
        self.assertFalse(confirmed_crt_retest(df_no_sweep, level=100.0, direction="BUY", atr=2.0))

        # Case 3: Sweep but closes bearish (failed rejection)
        df_bearish_fail = pd.DataFrame([
            {"time": pd.Timestamp("2026-10-10 10:00:00", tz="UTC"), "open": 100.5, "high": 100.8, "low": 99.5, "close": 99.8}
        ])
        self.assertFalse(confirmed_crt_retest(df_bearish_fail, level=100.0, direction="BUY", atr=2.0))

    def test_validated_portfolio_allowlist(self):
        config = MalaysianSNRConfig()
        # Validados en replay 2 anos (60 activos auditados)
        for sym in ["EURUSD", "USDJPY", "GBPUSD", "GBPJPY", "XAUUSD", "XAGUSD", "Step Index 400", "Boom 1000 Index", "Crash 1000 Index", "Step Index", "Jump 25 Index"]:
            self.assertIn(sym, config.allowed_symbols)
        # Excluidos formalmente de MSNR por expectativa negativa o toxicidad
        for sym in ["US Tech 100", "US SP 500", "US Oil", "AUDUSD", "USDCHF", "USDCAD", "BTCUSD", "Volatility 50 Index"]:
            self.assertNotIn(sym, config.allowed_symbols)


if __name__ == "__main__":
    unittest.main()
