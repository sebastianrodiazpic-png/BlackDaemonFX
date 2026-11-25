import os
import unittest
from unittest.mock import patch

from config.ict_instrument_policy import (
    HF_VOL_SYMBOLS,
    ICT_SYNTHETIC_FAMILIES,
    resolve_active_pruned_worker_universe,
)
from config.symbol_policy import get_symbol_direction_policy, is_direction_allowed
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from strategy.execution.worker_rules import configure_worker_rules


class TestOla3FiveYearBlockA(unittest.TestCase):
    def test_split_70_30_default_and_override(self):
        cfg = LiveTradingConfig()
        self.assertAlmostEqual(cfg.split_entry_risk_fraction, 0.70, places=4)
        self.assertIsNone(cfg.split_runner_risk_fraction)

        engine = object.__new__(LiveTradingEngine)
        engine.config = cfg
        captured = {}

        def fake_build_plan(specs, mode):
            captured["specs"] = specs
            captured["mode"] = mode
            return [{"name": s[0], "fraction": s[1]} for s in specs], None

        legs, split_err, _, mode = engine._plan_execution_legs(
            exact_symbol="Volatility 10 Index",
            direction="BUY",
            entry=100.0,
            sl=95.0,
            rr=2.0,
            strategy_name="ICT",
            signal={"tp1_rr": 1.0, "runner_rr": 2.0},
            total_risk_amount=100.0,
            risk_fraction=0.70,
            runner_risk_fraction=0.30,
            silver_risk_cap=False,
            build_plan=fake_build_plan,
        )
        self.assertIsNone(split_err)
        self.assertEqual(mode, "SPLIT")
        self.assertEqual(captured["specs"][0][0], "TP1")
        self.assertAlmostEqual(captured["specs"][0][1], 0.70, places=4)
        self.assertEqual(captured["specs"][1][0], "RUNNER")
        self.assertAlmostEqual(captured["specs"][1][1], 0.30, places=4)

        with patch.dict(os.environ, {"DAEMONBLACKFX_SPLIT_LEG1_RATIO": "0.50", "DAEMONBLACKFX_SPLIT_LEG2_RATIO": "0.50"}):
            cfg50 = LiveTradingConfig()
            self.assertAlmostEqual(cfg50.split_entry_risk_fraction, 0.50, places=4)
            self.assertAlmostEqual(cfg50.split_runner_risk_fraction, 0.50, places=4)

    def test_jump_buy_only_policy_and_toggle(self):
        pol = get_symbol_direction_policy("Jump 25 Index")
        self.assertEqual(pol.allowed_direction, "BUY")
        self.assertEqual(pol.reason, "JUMP_BUY_ONLY")
        self.assertTrue(is_direction_allowed("Jump 25 Index", "BUY"))
        self.assertFalse(is_direction_allowed("Jump 25 Index", "SELL"))

        with patch.dict(os.environ, {"DAEMONBLACKFX_JUMP_BUY_ONLY": "0"}):
            pol_off = get_symbol_direction_policy("Jump 25 Index")
            self.assertIsNone(pol_off.allowed_direction)
            self.assertTrue(is_direction_allowed("Jump 25 Index", "SELL"))

    def test_msnr_disabled_by_default_in_real_market_workers(self):
        for prof in ("FOREX_1", "FOREX_2", "FOREX_3", "FOREX_4", "FOREX_5", "ICT"):
            cfg = configure_worker_rules(LiveTradingConfig(bot_profile=prof))
            self.assertFalse(cfg.malaysian_snr_enabled, f"{prof} debe tener MSNR desactivado por defecto")

        # Reversible vía env var
        with patch.dict(os.environ, {"DAEMONBLACKFX_ICT_MULTISTRATEGY": "1", "DAEMONBLACKFX_FOREX_4_MULTISTRATEGY": "1"}):
            self.assertTrue(configure_worker_rules(LiveTradingConfig(bot_profile="ICT")).malaysian_snr_enabled)
            self.assertTrue(configure_worker_rules(LiveTradingConfig(bot_profile="FOREX_4")).malaysian_snr_enabled)

        # Sintéticos mantienen MSNR activo por defecto
        self.assertTrue(configure_worker_rules(LiveTradingConfig(bot_profile="BOOM")).malaysian_snr_enabled)
        self.assertTrue(configure_worker_rules(LiveTradingConfig(bot_profile="CRASH")).malaysian_snr_enabled)

    def test_hf_vol_pruned_by_default_and_reversible(self):
        for sym in HF_VOL_SYMBOLS:
            self.assertNotIn(sym, ICT_SYNTHETIC_FAMILIES["VOLATILITY"])
        self.assertEqual(resolve_active_pruned_worker_universe("VOLATILITY_1", HF_VOL_SYMBOLS), [])

        with patch.dict(os.environ, {"DAEMONBLACKFX_PRUNE_HF_VOL": "0"}):
            restored = resolve_active_pruned_worker_universe("VOLATILITY_1", HF_VOL_SYMBOLS)
            self.assertEqual(len(restored), len(HF_VOL_SYMBOLS))

    def test_skip_empty_workers_and_exclude_vol_over(self):
        from app.main import _should_skip_disabled_worker_process
        from config.ict_instrument_policy import UNAVAILABLE_VOL_OVER_SYMBOLS, _malaysian_snr_synthetics

        # VOLATILITY_1 tiene 0 símbolos tras poda HF_VOL -> debe omitirse si no tiene posiciones abiertas
        skip, reason = _should_skip_disabled_worker_process("VOLATILITY_1", repo=None)
        self.assertTrue(skip)
        self.assertEqual(reason, "EMPTY_WORKER_UNIVERSE")

        # Desactivable por interruptor
        with patch.dict(os.environ, {"DAEMONBLACKFX_SKIP_EMPTY_WORKERS": "0"}):
            skip_off, _ = _should_skip_disabled_worker_process("VOLATILITY_1", repo=None)
            self.assertFalse(skip_off)

        # Vol over Boom/Crash 550 excluidos por defecto en MSNR
        msnr_syms = _malaysian_snr_synthetics()
        for sym in UNAVAILABLE_VOL_OVER_SYMBOLS:
            self.assertNotIn(sym, msnr_syms)
        with patch.dict(os.environ, {"DAEMONBLACKFX_EXCLUDE_UNAVAILABLE_VOL_OVER": "0"}):
            msnr_all = _malaysian_snr_synthetics()
            for sym in UNAVAILABLE_VOL_OVER_SYMBOLS:
                self.assertIn(sym, msnr_all)

    def test_indicesb_snr_and_volatility_2_symbol_selection_and_be_reentry(self):
        from unittest.mock import MagicMock

        # 1. INDICESB_SNR mapea a INDICESB_SNR (no a SYNTHETICS)
        self.assertEqual(LiveTradingEngine._selection_profile_for_bot("INDICESB_SNR"), "INDICESB_SNR")
        self.assertEqual(LiveTradingEngine._selection_profile_for_bot("INDICES"), "INDICESB_SNR")

        # 2. VOLATILITY_2 no borra sus propios símbolos activos
        engine = object.__new__(LiveTradingEngine)
        engine.config = LiveTradingConfig(bot_profile="VOLATILITY_2", source="DEMO")
        engine.daily_profit_target_manager = None
        engine.dashboard_service = None
        engine.repository = MagicMock()
        v2_syms = [
            "Ladder Volatility Down Index",
            "Ladder Volatility Up Index",
            "VolSwitch Low Vol Index",
            "VolSwitch Medium Vol Index",
        ]
        engine.repository.latest_instrument_selection_profile.return_value = {"selected_symbols": v2_syms}
        selected = engine._selected_base_cycle_symbols(v2_syms)
        self.assertEqual(selected, v2_syms)

        # 3. _active_position_gate permite re-entrada si la posición abierta está en BE (riesgo $0)
        engine.executor = MagicMock()
        engine.executor.get_open_positions.return_value = [
            {"symbol": "Boom 1000 Index", "ticket": 123, "type": "BUY", "price_open": 10000.0, "sl": 10005.0}
        ]
        engine.executor.get_pending_orders.return_value = []
        with patch.dict(os.environ, {"DAEMONBLACKFX_ALLOW_REENTRY_ON_BE": "1"}):
            self.assertIsNone(engine._active_position_gate("Boom 1000 Index"))
        with patch.dict(os.environ, {"DAEMONBLACKFX_ALLOW_REENTRY_ON_BE": "0"}):
            engine._persist_audit_event = MagicMock()
            blocked = engine._active_position_gate("Boom 1000 Index")
            self.assertIsNotNone(blocked)
            self.assertEqual(blocked["status"], "BLOCKED_ACTIVE_TRADE")


if __name__ == "__main__":
    unittest.main()
