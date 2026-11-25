"""Tests unitarios e integración para Prioridad 4 (Punto 4):
1. Franja 10:00–11:59 Chile (13:00–14:59 UTC): bloquea mercados reales (Forex, Oro, Índices, Petróleo, Cripto),
   PERO permite entradas bajo la estrategia ORB (y bloquea estrategias no-ORB incluso si el perfil fuera mixto).
2. Franja 15:00–16:59 Chile (18:00–19:59 UTC): bloquea TODOS los mercados reales (incluido ORB).
3. Franja 23:00–00:59 Chile (02:00–03:59 UTC): bloquea TODOS los mercados reales.
4. TODOS los instrumentos sintéticos (Volatility, Boom, Crash, Step, Jump, Flip, VolSwitch, Ladder, Range Break, DEX)
   quedan 100% excluidos de los bloqueos horarios y direccionales.
5. Confluencia direccional reforzada en mercados reales (XAUUSD BUY contra tendencia H1 o con ADX débil < 20),
   eximiendo a ORB y excluyendo por completo a los sintéticos.
"""

from __future__ import annotations

import os
import unittest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


class TestPriority4RealMarketHoursAndConfluence(unittest.TestCase):
    def _make_engine(self, bot_profile="FOREX_1", **overrides):
        cfg = LiveTradingConfig(bot_profile=bot_profile, **overrides)
        engine = object.__new__(LiveTradingEngine)
        engine.config = cfg
        engine._gate_audit_cache = {}
        engine.repository = MagicMock()
        return engine

    def test_window_10_to_12_chile_blocks_real_markets_except_orb(self):
        """10:00–11:59 AM Chile (13:00–14:59 UTC): bloquea Forex/Oro/Petróleo/Índices salvo estrategia ORB."""
        t_1030_cl = datetime(2026, 11, 25, 13, 30, tzinfo=timezone.utc)  # 10:30 AM Chile (UTC-3)
        t_1145_cl = datetime(2026, 11, 25, 14, 45, tzinfo=timezone.utc)  # 11:45 AM Chile (UTC-3)
        t_1205_cl = datetime(2026, 11, 25, 15, 5, tzinfo=timezone.utc)   # 12:05 PM Chile (UTC-3)

        # Workers no-ORB en mercados reales -> BLOQUEADOS (incluyendo Petróleo USOIL y Oro XAUUSD)
        for profile, sym in [
            ("FOREX_1", "EURUSD"),
            ("ICT", "XAUUSD"),
            ("ICT", "USOIL"),
            ("GOLD", "XAUUSD"),
            ("INDICESB_SNR", "Wall Street 30"),
            ("ICT", "BTCUSD"),
        ]:
            eng = self._make_engine(bot_profile=profile)
            res1 = eng._london_ny_crossover_sentinel_gate(sym, now_utc=t_1030_cl)
            res2 = eng._london_ny_crossover_sentinel_gate(sym, now_utc=t_1145_cl)
            self.assertIsNotNone(res1, f"{profile}/{sym} debe bloquearse a las 10:30 CL")
            self.assertIsNotNone(res2, f"{profile}/{sym} debe bloquearse a las 11:45 CL")
            self.assertEqual(res1["action"], "LONDON_NY_CROSSOVER_FILTER_BLOCKED")
            # A las 12:05 PM Chile (15:05 UTC) ya está permitido
            self.assertIsNone(eng._london_ny_crossover_sentinel_gate(sym, now_utc=t_1205_cl))
            self.assertIsNone(eng._real_market_toxic_hours_sentinel_gate(sym, now_utc=t_1205_cl))

        # Worker ORB con estrategia ORB_NEW_YORK -> PERMITIDO en 10:00–11:59 AM Chile
        eng_orb = self._make_engine(bot_profile="ORB", orb_enabled=True)
        for sym in ("XAUUSD", "Wall Street 30", "US Tech 100", "USDCAD", "USOIL"):
            self.assertIsNone(eng_orb._london_ny_crossover_sentinel_gate(sym, now_utc=t_1030_cl))
            self.assertIsNone(eng_orb._real_market_toxic_hours_sentinel_gate(sym, now_utc=t_1030_cl))
            self.assertIsNone(
                eng_orb._strategy_toxic_hour_gate(sym, "ORB_NEW_YORK", now_utc=t_1030_cl),
                f"ORB_NEW_YORK debe permitirse en {sym} a las 10:30 CL",
            )

        # Defensa por estrategia: si dentro de 13:00–14:59 UTC llegara una señal NO-ORB (ej. ICT o SMC), se bloquea
        non_orb_block = eng_orb._strategy_toxic_hour_gate("XAUUSD", "ICT", now_utc=t_1030_cl)
        self.assertIsNotNone(non_orb_block)
        self.assertEqual(non_orb_block["action"], "LONDON_NY_CROSSOVER_NON_ORB_STRATEGY_BLOCKED")

    def test_windows_15_to_17_and_23_to_01_chile_block_all_real_markets_including_orb(self):
        """15:00–16:59 CL (18:00–19:59 UTC) y 23:00–00:59 CL (02:00–03:59 UTC) bloquean mercados reales (incluido ORB)."""
        t_1530_cl = datetime(2026, 11, 25, 18, 30, tzinfo=timezone.utc)  # 03:30 PM Chile
        t_1659_cl = datetime(2026, 11, 25, 19, 59, tzinfo=timezone.utc)  # 04:59 PM Chile
        t_1701_cl = datetime(2026, 11, 25, 20, 1, tzinfo=timezone.utc)   # 05:01 PM Chile (libre)

        t_2315_cl = datetime(2026, 11, 26, 2, 15, tzinfo=timezone.utc)   # 11:15 PM Chile
        t_0045_cl = datetime(2026, 11, 26, 3, 45, tzinfo=timezone.utc)   # 12:45 AM Chile
        t_0105_cl = datetime(2026, 11, 26, 4, 5, tzinfo=timezone.utc)    # 01:05 AM Chile (libre)

        for profile in ("FOREX_1", "ICT", "GOLD", "INDICESB_SNR", "ORB"):
            eng = self._make_engine(bot_profile=profile, orb_enabled=(profile == "ORB"))
            for sym in ("EURUSD", "XAUUSD", "Wall Street 30", "USOIL", "BTCUSD"):
                # Bloqueo 15:00–16:59 CL
                b_aft_1 = eng._real_market_toxic_hours_sentinel_gate(sym, now_utc=t_1530_cl)
                b_aft_2 = eng._real_market_toxic_hours_sentinel_gate(sym, now_utc=t_1659_cl)
                self.assertIsNotNone(b_aft_1, f"{profile}/{sym} debe bloquearse a las 15:30 CL")
                self.assertIsNotNone(b_aft_2, f"{profile}/{sym} debe bloquearse a las 16:59 CL")
                self.assertEqual(b_aft_1["action"], "NY_AFTERNOON_TOXIC_WINDOW_BLOCKED")
                self.assertIsNone(eng._real_market_toxic_hours_sentinel_gate(sym, now_utc=t_1701_cl))

                # Bloqueo 23:00–00:59 CL
                b_night_1 = eng._real_market_toxic_hours_sentinel_gate(sym, now_utc=t_2315_cl)
                b_night_2 = eng._real_market_toxic_hours_sentinel_gate(sym, now_utc=t_0045_cl)
                self.assertIsNotNone(b_night_1, f"{profile}/{sym} debe bloquearse a las 23:15 CL")
                self.assertIsNotNone(b_night_2, f"{profile}/{sym} debe bloquearse a las 00:45 CL")
                self.assertEqual(b_night_1["action"], "ASIA_DEAD_ZONE_TOXIC_WINDOW_BLOCKED")
                self.assertIsNone(eng._real_market_toxic_hours_sentinel_gate(sym, now_utc=t_0105_cl))

    def test_all_synthetic_instruments_strictly_excluded_from_all_blocks(self):
        """Ningún instrumento sintético de Deriv puede ser bloqueado en ninguna de las 3 franjas ni por confluencia real."""
        synthetics = [
            "Volatility 10 Index",
            "Volatility 75 Index",
            "Volatility 100 (1s) Index",
            "Boom 1000 Index",
            "Boom 500 Index",
            "Crash 1000 Index",
            "Crash 500 Index",
            "Step Index",
            "Step Index 500",
            "Multi Step 2 Index",
            "Skew Step Index 4 Up",
            "Jump 25 Index",
            "Jump 75 Index",
            "VolSwitch Low Vol Index",
            "Ladder Volatility Down Index",
            "Ladder Volatility Up Index",
            "Range Break 100 Index",
            "DEX 900 UP Index",
            "Drift Switch Index 10",
        ]
        toxic_times = [
            datetime(2026, 11, 25, 2, 30, tzinfo=timezone.utc),   # 23:30 CL
            datetime(2026, 11, 25, 13, 30, tzinfo=timezone.utc),  # 10:30 CL
            datetime(2026, 11, 25, 18, 30, tzinfo=timezone.utc),  # 15:30 CL
        ]
        for profile in ("VOLATILITY_3", "VOLATILITY_4", "BOOM", "CRASH", "STEP", "JUMP", "ICT"):
            eng = self._make_engine(bot_profile=profile)
            for sym in synthetics:
                self.assertTrue(eng._is_synthetic_symbol(sym), f"{sym} debe detectarse como sintético")
                for t in toxic_times:
                    self.assertIsNone(
                        eng._london_ny_crossover_sentinel_gate(sym, now_utc=t),
                        f"Sintético {sym} NO debe bloquearse en 10-12 CL",
                    )
                    self.assertIsNone(
                        eng._real_market_toxic_hours_sentinel_gate(sym, now_utc=t),
                        f"Sintético {sym} NO debe bloquearse en 15-17 / 23-01 CL",
                    )
                    self.assertIsNone(
                        eng._strategy_toxic_hour_gate(sym, "ICT", now_utc=t),
                        f"Sintético {sym} NO debe bloquearse por estrategia en horas tóxicas",
                    )
                # Tampoco debe aplicársele el bloqueo direccional de mercados reales
                self.assertIsNone(
                    eng._real_market_directional_confluence_gate(
                        sym, "SELL", {"adx": 10.0}, {"h1_trend": "BULLISH"}, "ICT"
                    )
                )

    def test_real_market_directional_confluence_blocks_weak_or_counter_xau_buy_only(self):
        """En XAUUSD (mercado real), bloquea BUY contra tendencia H1 bajista o con ADX < 20 (salvo ORB)."""
        eng = self._make_engine(bot_profile="ICT")

        # 1. XAUUSD BUY contra H1 BEARISH -> bloqueado
        res_counter = eng._real_market_directional_confluence_gate(
            "XAUUSD", "BUY", {"adx": 28.0}, {"h1_trend": "BEARISH"}, "ICT"
        )
        self.assertIsNotNone(res_counter)
        self.assertEqual(res_counter["action"], "REAL_MARKET_DIRECTIONAL_CONFLUENCE_BLOCKED")
        self.assertIn("COUNTER_HTF", res_counter["reason"])

        # 2. XAUUSD BUY con ADX débil (14.5 < 20.0) -> bloqueado
        res_weak_adx = eng._real_market_directional_confluence_gate(
            "XAUUSD", "BUY", {"adx": 14.5}, {"h1_trend": "BULLISH"}, "ICT"
        )
        self.assertIsNotNone(res_weak_adx)
        self.assertEqual(res_weak_adx["action"], "REAL_MARKET_DIRECTIONAL_CONFLUENCE_BLOCKED")
        self.assertIn("WEAK_ADX", res_weak_adx["reason"])

        # 3. XAUUSD BUY con H1 BULLISH y ADX 25.0 -> permitido
        self.assertIsNone(
            eng._real_market_directional_confluence_gate(
                "XAUUSD", "BUY", {"adx": 25.0}, {"h1_trend": "BULLISH"}, "ICT"
            )
        )

        # 4. ORB_NEW_YORK en XAUUSD BUY -> exento por diseño
        self.assertIsNone(
            eng._real_market_directional_confluence_gate(
                "XAUUSD", "BUY", {"adx": 12.0}, {"h1_trend": "BEARISH"}, "ORB_NEW_YORK"
            )
        )

    def test_env_switches_cleanly_disable_filters(self):
        """Todos los nuevos filtros de Prioridad 4 se desactivan limpiamente con sus variables de entorno."""
        t_aft = datetime(2026, 11, 25, 18, 30, tzinfo=timezone.utc)
        t_night = datetime(2026, 11, 25, 2, 30, tzinfo=timezone.utc)
        with patch.dict(
            os.environ,
            {
                "DAEMONBLACKFX_NY_AFTERNOON_FILTER_ENABLED": "0",
                "DAEMONBLACKFX_ASIA_DEAD_ZONE_FILTER_ENABLED": "0",
                "DAEMONBLACKFX_REAL_DIRECTIONAL_CONFLUENCE_ENABLED": "0",
            },
        ):
            eng = self._make_engine(bot_profile="FOREX_1")
            self.assertIsNone(eng._real_market_toxic_hours_sentinel_gate("EURUSD", now_utc=t_aft))
            self.assertIsNone(eng._real_market_toxic_hours_sentinel_gate("EURUSD", now_utc=t_night))
            self.assertIsNone(
                eng._real_market_directional_confluence_gate(
                    "XAUUSD", "BUY", {"adx": 10.0}, {"h1_trend": "BEARISH"}, "ICT"
                )
            )


if __name__ == "__main__":
    unittest.main()
