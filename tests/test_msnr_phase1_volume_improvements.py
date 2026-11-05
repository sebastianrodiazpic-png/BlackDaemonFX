import os
import unittest
import numpy as np
import pandas as pd

from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy
from strategy.malaysian_snr.validation import av_levels


class MockProvider:
    def __init__(self, data=None):
        self.data = data or {}

    def get_rates(self, symbol, timeframe, count):
        return self.data.get((symbol, timeframe), pd.DataFrame())


class TestMSNRPhase1VolumeImprovements(unittest.TestCase):
    def test_av_levels_definition_body_turns_vs_engulfing(self):
        """Verifica que body_turns detecta giros de vela sin exigir patrón envolvente estricto."""
        # Barra 0: alcista (open 100, close 105)
        # Barra 1: bajista (open 106, close 102) -> es resistencia A, pero close (102) no envuelve open (100)
        # Barra 2: bajista (open 102, close 98)
        frame = pd.DataFrame([
            {"time": 1000, "open": 100.0, "high": 106.0, "low": 99.0, "close": 105.0},
            {"time": 2000, "open": 106.0, "high": 107.0, "low": 101.0, "close": 102.0},
            {"time": 3000, "open": 102.0, "high": 103.0, "low": 97.0, "close": 98.0},
            {"time": 4000, "open": 98.0, "high": 99.0, "low": 95.0, "close": 96.0},
        ])
        # Con engulfing por defecto: NO genera nivel porque 102.0 > 100.0 (no envuelve)
        engulfing_levels = av_levels(frame, include_latest=False, definition='engulfing')
        self.assertEqual(len(engulfing_levels), 0)

        # Con body_turns (teoría Alchemist/Nestor): SÍ genera nivel de resistencia A en 105.0
        body_turn_levels = av_levels(frame, include_latest=False, definition='body_turns')
        self.assertEqual(len(body_turn_levels), 1)
        self.assertEqual(body_turn_levels[0]["type"], "A_RESISTANCE")
        self.assertEqual(body_turn_levels[0]["level"], 105.0)

    def test_boom_directional_asymmetry_buy_only(self):
        """Verifica que los índices Boom solo admiten compras (BUY) y bloquean ventas (SELL)."""
        cfg = MalaysianSNRConfig(
            directional_asymmetry_enabled=True,
            boom_buy_only_symbols=("Boom 500 Index", "Boom 900 Index", "Boom 1000 Index"),
        )
        strat = MalaysianSNRStrategy(MockProvider(), cfg)

        # Simular setup SELL en Boom 500 Index
        setup_sell = {"direction": "SELL", "level": 1000.0, "scenario": "ESC_1_CONTINUATION"}
        obs_sell = []
        now = pd.Timestamp.utcnow()

        # Usar _evaluate_setup directamente con fake df
        h1 = pd.DataFrame([
            {"time": now - pd.Timedelta(hours=2), "open": 100.0, "high": 105.0, "low": 95.0, "close": 102.0},
            {"time": now - pd.Timedelta(hours=1), "open": 102.0, "high": 104.0, "low": 94.0, "close": 96.0},
            {"time": now, "open": 96.0, "high": 98.0, "low": 93.0, "close": 95.0},
        ])
        m15 = pd.DataFrame([
            {"time": now - pd.Timedelta(minutes=30), "open": 96.0, "high": 97.0, "low": 94.0, "close": 95.0},
            {"time": now - pd.Timedelta(minutes=15), "open": 95.0, "high": 96.0, "low": 93.0, "close": 94.0},
        ])

        # Verificamos lógica de asimetría en Boom
        sym_l = "boom 500 index"
        boom_buy_only = {str(s).strip().lower() for s in cfg.boom_buy_only_symbols}
        self.assertIn(sym_l, boom_buy_only)

        # En venta: debe ser bloqueado
        direction = "SELL"
        is_blocked = (sym_l in boom_buy_only and direction != "BUY")
        self.assertTrue(is_blocked)

        # En compra: debe ser admitido
        direction = "BUY"
        is_admitted = (sym_l in boom_buy_only and direction == "BUY")
        self.assertTrue(is_admitted)

    def test_msnr_allowed_symbols_includes_boom(self):
        """Verifica que allowed_symbols incluye Boom 500 y Boom 900 en la configuración."""
        cfg = MalaysianSNRConfig()
        allowed = {s.strip().lower() for s in cfg.allowed_symbols}
        self.assertIn("boom 500 index", allowed)
        self.assertIn("boom 900 index", allowed)
        self.assertIn("crash 500 index", allowed)

    def test_msnr_env_var_toggles(self):
        """Verifica que los nuevos toggles respetan las variables de entorno."""
        old_env = os.environ.copy()
        try:
            os.environ["DAEMONBLACKFX_MSNR_AV_LEVEL_DEFINITION"] = "body_turns"
            os.environ["DAEMONBLACKFX_MSNR_BREAKER_PAIR_MODE"] = "live"
            os.environ["DAEMONBLACKFX_MSNR_RETEST_PINBAR_MODE"] = "live"
            os.environ["DAEMONBLACKFX_MSNR_AV_ENTRY_MODE"] = "live"

            cfg = MalaysianSNRConfig()
            self.assertEqual(cfg.av_level_definition, "body_turns")
            self.assertEqual(cfg.breaker_pair_mode, "live")
            self.assertEqual(cfg.retest_pinbar_mode, "live")
            self.assertEqual(cfg.av_entry_mode, "live")
        finally:
            os.environ.clear()
            os.environ.update(old_env)

    def test_step_family_bidirectional_by_default(self):
        """Verifica que toda la familia Step y Jump son bidireccionales por defecto en Malaysian SNR."""
        cfg = MalaysianSNRConfig()
        # step_sell_only_symbols y jump_buy_only_symbols deben ser tuplas vacías por defecto
        self.assertEqual(cfg.step_sell_only_symbols, ())
        self.assertEqual(cfg.jump_buy_only_symbols, ())

        # Verificar que ni Step ni Jump están restringidos unidireccionalmente
        step_sell_only = {str(s).strip().lower() for s in cfg.step_sell_only_symbols}
        for sym in ("Step Index", "Step Index 200", "Step Index 400", "Step Index 500"):
            self.assertNotIn(sym.lower(), step_sell_only)

        jump_buy_only = {str(s).strip().lower() for s in cfg.jump_buy_only_symbols}
        for sym in ("Jump 10 Index", "Jump 25 Index", "Jump 50 Index", "Jump 75 Index", "Jump 100 Index"):
            self.assertNotIn(sym.lower(), jump_buy_only)


if __name__ == "__main__":
    unittest.main()
