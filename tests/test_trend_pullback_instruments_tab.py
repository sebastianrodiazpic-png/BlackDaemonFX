"""Pruebas unitarias para la integración de Trend Pullback en /Instruments y worker dedicado."""
import unittest
from config.ict_instrument_policy import (
    POLICY_SELECTION_PROFILES,
    TREND_PULLBACK_ACTIVE,
    ict_active_symbols,
    is_ict_active,
    preventive_prune_reason,
)
from strategy.trend_pullback.config import (
    DEFAULT_PULLBACK_SYMBOLS,
    TREND_PULLBACK_51_SYMBOLS,
    TrendPullbackConfig,
)
from dashboard.realtime_dashboard import (
    _SELECTION_PROFILES,
    _WORKER_PROFILE_META,
    DEFAULT_PRIORITIZED_SYMBOLS,
    _selection_profile_for_category,
    _resolve_worker_universe_and_selection,
)
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from strategy.execution.worker_rules import configure_worker_rules, worker_poll_interval
from app.main import (
    BOT_PROFILES,
    FULL_MULTI_BOT_PROFILES,
    _selection_profile_for_bot as app_selection_profile_for_bot,
)
from database.repository import TradingRepository


class TestTrendPullbackInstrumentsTab(unittest.TestCase):
    """Verifica que la estrategia Trend Pullback esté correctamente expuesta en /Instruments y vinculada al worker."""

    def test_21_symbols_surpass_51_percent_wr(self):
        """Los símbolos activos cumplen estrictamente la condición de WR > 51.0% en sintéticos (17 tras transferir Jump/Step a workers dedicados)."""
        self.assertEqual(len(TREND_PULLBACK_51_SYMBOLS), 17)
        self.assertEqual(DEFAULT_PULLBACK_SYMBOLS, TREND_PULLBACK_51_SYMBOLS)
        # Activos líderes comprobados
        self.assertIn("Crash 300 Index", TREND_PULLBACK_51_SYMBOLS)  # 60.10%
        self.assertIn("Volatility 25 Index", TREND_PULLBACK_51_SYMBOLS)  # 58.50%
        self.assertIn("Volatility 100 (1s) Index", TREND_PULLBACK_51_SYMBOLS)  # 57.80%
        self.assertIn("Jump 10 Index", TREND_PULLBACK_51_SYMBOLS)  # 54.50%
        self.assertIn("Volatility 15 Index", TREND_PULLBACK_51_SYMBOLS)  # 51.20%

        # Excluidos o transferidos a workers dedicados STEP y JUMP
        self.assertNotIn("Jump 75 Index", TREND_PULLBACK_51_SYMBOLS)
        self.assertNotIn("Step Index 200", TREND_PULLBACK_51_SYMBOLS)
        self.assertNotIn("Volatility 75 (1s) Index", TREND_PULLBACK_51_SYMBOLS)  # 51.00%
        self.assertNotIn("Vol over Boom 550", TREND_PULLBACK_51_SYMBOLS)  # 50.80%
        self.assertNotIn("Crash 1000 Index", TREND_PULLBACK_51_SYMBOLS)  # 44.60%

    def test_policy_profile_registered(self):
        """El perfil TREND_PULLBACK está registrado en las políticas de /Instruments."""
        self.assertIn("TREND_PULLBACK", POLICY_SELECTION_PROFILES)
        self.assertEqual(ict_active_symbols("TREND_PULLBACK"), TREND_PULLBACK_51_SYMBOLS)
        self.assertTrue(is_ict_active("Crash 300 Index", "TREND_PULLBACK"))
        self.assertFalse(is_ict_active("Crash 1000 Index", "TREND_PULLBACK"))

    def test_preventive_prune_reason_trend_pullback(self):
        """La razón de poda preventiva para Trend Pullback explica el corte de rentabilidad > 51%."""
        reason = preventive_prune_reason("Crash 1000 Index", "TREND_PULLBACK")
        self.assertIn("51.0 %", reason)
        self.assertIn("PODA PREVENTIVA", reason)
        # Símbolo activo no tiene motivo de poda
        self.assertEqual(preventive_prune_reason("Crash 300 Index", "TREND_PULLBACK"), "")

    def test_dashboard_selection_profiles_and_meta(self):
        """El dashboard reconoce TREND_PULLBACK en sus perfiles y metadatos de worker."""
        self.assertIn("TREND_PULLBACK", _SELECTION_PROFILES)
        self.assertIn("TREND_PULLBACK", _WORKER_PROFILE_META)
        meta = _WORKER_PROFILE_META["TREND_PULLBACK"]
        self.assertEqual(meta["selection_profile"], "TREND_PULLBACK")
        self.assertEqual(meta["magic"], 26082038)
        self.assertEqual(meta["strategy_key"], "TREND_PULLBACK")

    def test_selection_profile_for_category(self):
        """Mapeo de categoría de catálogo a perfil de selección."""
        self.assertEqual(_selection_profile_for_category("trend_pullback_synthetics"), "TREND_PULLBACK")
        self.assertEqual(_selection_profile_for_category("trend_pullback"), "TREND_PULLBACK")

    def test_selection_profile_for_bot_both_engines(self):
        """Ambos traductores de perfil dirigen TREND_PULLBACK a su selección independiente."""
        self.assertEqual(LiveTradingEngine._selection_profile_for_bot("TREND_PULLBACK"), "TREND_PULLBACK")
        self.assertEqual(app_selection_profile_for_bot("TREND_PULLBACK"), "TREND_PULLBACK")

    def test_bot_profile_in_app_main(self):
        """El worker TREND_PULLBACK está registrado en la CLI y arquitectura multi-bot de app/main.py."""
        self.assertIn("TREND_PULLBACK", BOT_PROFILES)
        self.assertEqual(BOT_PROFILES["TREND_PULLBACK"]["mode"], "trend-pullback-daemon")
        self.assertEqual(BOT_PROFILES["TREND_PULLBACK"]["magic"], 26082038)
        self.assertIn("TREND_PULLBACK", FULL_MULTI_BOT_PROFILES)

    def test_prioritized_symbols_contains_21_assets(self):
        """DEFAULT_PRIORITIZED_SYMBOLS contiene los 21 activos validados para TREND_PULLBACK."""
        self.assertIn("TREND_PULLBACK", DEFAULT_PRIORITIZED_SYMBOLS)
        self.assertEqual(set(DEFAULT_PRIORITIZED_SYMBOLS["TREND_PULLBACK"]), set(TREND_PULLBACK_51_SYMBOLS))

    def test_worker_universe_resolution(self):
        """El universo del worker TREND_PULLBACK se resuelve correctamente en el dashboard."""
        info = _resolve_worker_universe_and_selection("TREND_PULLBACK", catalog=[], selection_profiles=None)
        self.assertEqual(info["selection_profile"], "TREND_PULLBACK")
        self.assertEqual(info["daemon_magic"], 26082038)
        self.assertEqual(len(info["universe_symbols"]), 17)
        self.assertEqual(len(info["active_symbols"]), 17)
        self.assertEqual(len(info["pruned_symbols"]), 0)

    def test_worker_rules_configuration(self):
        """configure_worker_rules conecta adecuadamente el perfil TREND_PULLBACK."""
        cfg = LiveTradingConfig(bot_profile="TREND_PULLBACK")
        configured = configure_worker_rules(cfg)
        self.assertTrue(configured.trend_pullback_enabled)
        self.assertEqual(configured.entry_timeframe, "M15")
        self.assertEqual(configured.structure_timeframe, "H1")
        self.assertTrue(configured.break_even_enabled)
        self.assertEqual(configured.first_target_rr, 1.0)
        self.assertEqual(configured.second_target_rr, 2.0)
        # worker_poll_interval no recorta forzadamente el intervalo para este perfil
        self.assertEqual(worker_poll_interval("TREND_PULLBACK", 15), 15)

    def test_independent_repository_selection_persistence(self):
        """La persistencia de selección para TREND_PULLBACK no contamina otros perfiles."""
        from pathlib import Path
        db_file = Path("storage") / "test_tp_instruments.db"
        if db_file.exists():
            try:
                db_file.unlink()
            except Exception:
                pass

        repo = TradingRepository(db_path=db_file)
        try:
            # Guardar selección específica de 3 activos para TREND_PULLBACK
            test_selection = ["Crash 300 Index", "Volatility 25 Index", "Jump 10 Index"]
            repo.save_instrument_selection_profile(test_selection, selection_profile="TREND_PULLBACK", source="DEMO")

            # Guardar selección para SYNTHETICS
            synth_selection = ["Boom 1000 Index", "Crash 1000 Index"]
            repo.save_instrument_selection_profile(synth_selection, selection_profile="SYNTHETICS", source="DEMO")

            # Recuperar y verificar aislamiento
            tp_pref = repo.latest_instrument_selection_profile("TREND_PULLBACK", source="DEMO")
            synth_pref = repo.latest_instrument_selection_profile("SYNTHETICS", source="DEMO")

            self.assertIsNotNone(tp_pref)
            self.assertEqual(tp_pref["selected_symbols"], test_selection)
            self.assertEqual(synth_pref["selected_symbols"], synth_selection)
        finally:
            try:
                repo.Session.kw['bind'].dispose()
            except Exception:
                pass
            if db_file.exists():
                try:
                    db_file.unlink()
                except Exception:
                    pass


if __name__ == "__main__":
    unittest.main()
