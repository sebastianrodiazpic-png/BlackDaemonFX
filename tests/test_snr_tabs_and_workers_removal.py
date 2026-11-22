import pytest
from app.main import FULL_MULTI_BOT_PROFILES, BOT_PROFILES
from config.ict_instrument_policy import POLICY_SELECTION_PROFILES, ICT_SELECTION_PROFILES
from dashboard.realtime_dashboard import _SELECTION_PROFILES, _WORKER_PROFILE_META, _INSTRUMENTS_HTML
from strategy.execution.worker_rules import configure_worker_rules
from strategy.execution.live_trading_engine import LiveTradingConfig


def test_removed_snr_workers_not_in_full_multi_bot():
    """Valida que los workers SNR redundantes ya no arranquen en multi-bot-daemon."""
    removed = {"MALAYSIAN_SNR", "FOREX_SNR", "COMMODITIES_SNR"}
    for p in removed:
        assert p not in FULL_MULTI_BOT_PROFILES, f"{p} no debe estar en FULL_MULTI_BOT_PROFILES"

    # Los workers MultiStrategia deben permanecer intactos
    active_multistrat = {
        "BOOM", "CRASH", "STEP", "JUMP",
        "VOLATILITY_1", "VOLATILITY_2", "VOLATILITY_3", "VOLATILITY_4",
        "FOREX_1", "FOREX_2", "FOREX_3", "FOREX_4", "FOREX_5",
        "ICT", "INDICESB_SNR",
    }
    for p in active_multistrat:
        assert p in FULL_MULTI_BOT_PROFILES, f"{p} debe estar en FULL_MULTI_BOT_PROFILES"


def test_removed_snr_tabs_not_in_policy_selection():
    """Valida que las pestañas eliminadas no figuren en POLICY_SELECTION_PROFILES."""
    assert "MALAYSIAN_SNR" not in POLICY_SELECTION_PROFILES
    assert "FOREX_SNR" not in POLICY_SELECTION_PROFILES
    assert "COMMODITIES_SNR" not in POLICY_SELECTION_PROFILES
    assert "TREND_PULLBACK" not in POLICY_SELECTION_PROFILES

    expected_policy = {"SYNTHETICS", "FOREX", "ICT", "INDICESB_SNR"}
    assert set(POLICY_SELECTION_PROFILES) == expected_policy


def test_backend_accepts_selection_profiles_with_removal_from_html():
    """Valida que los botones de pestañas estén eliminados en HTML mientras el backend preserva retrocompatibilidad."""
    assert 'data-profile="MALAYSIAN_SNR"' not in _INSTRUMENTS_HTML
    assert 'data-profile="FOREX_SNR"' not in _INSTRUMENTS_HTML
    assert 'data-profile="COMMODITIES_SNR"' not in _INSTRUMENTS_HTML
    assert 'data-profile="TREND_PULLBACK"' not in _INSTRUMENTS_HTML
    assert "MALAYSIAN_SNR" not in POLICY_SELECTION_PROFILES
    assert "FOREX_SNR" not in POLICY_SELECTION_PROFILES
    assert "COMMODITIES_SNR" not in POLICY_SELECTION_PROFILES
    assert "TREND_PULLBACK" not in POLICY_SELECTION_PROFILES


def test_removed_snr_tabs_not_in_html():
    """Valida que los botones de pestañas hayan sido eliminados del HTML de /Instruments."""
    assert 'data-profile="MALAYSIAN_SNR"' not in _INSTRUMENTS_HTML
    assert 'data-profile="FOREX_SNR"' not in _INSTRUMENTS_HTML
    assert 'data-profile="COMMODITIES_SNR"' not in _INSTRUMENTS_HTML
    assert 'data-profile="TREND_PULLBACK"' not in _INSTRUMENTS_HTML

    # Pestañas activas deben existir
    assert 'data-profile="SYNTHETICS"' in _INSTRUMENTS_HTML
    assert 'data-profile="FOREX"' in _INSTRUMENTS_HTML
    assert 'data-profile="ICT"' in _INSTRUMENTS_HTML
    assert 'data-profile="INDICESB_SNR"' in _INSTRUMENTS_HTML
    assert 'data-profile="ORB"' in _INSTRUMENTS_HTML


def test_consolidated_hidden_metadata():
    """Valida que los perfiles retirados tengan consolidated_hidden=True en _WORKER_PROFILE_META."""
    for prof in ("MALAYSIAN_SNR", "FOREX_SNR", "COMMODITIES_SNR", "TREND_PULLBACK"):
        meta = _WORKER_PROFILE_META.get(prof)
        assert meta is not None, f"{prof} debe existir en _WORKER_PROFILE_META"
        assert meta.get("consolidated_hidden") is True, f"{prof} debe tener consolidated_hidden=True"


def test_active_multistrategy_workers_rules_intact():
    """Valida que las reglas de trades de los workers MultiStrategia activos no hayan sido alteradas."""
    workers_check = {
        "INDICESB_SNR": {"magic": 26082042, "tp1": 1.0, "tp2": 2.0, "be": True, "msnr": True, "tf": "M5"},
        "ICT": {"magic": 26082032, "tp1": 1.0, "tp2": 2.0, "be": True, "msnr": True, "tf": "M5"},
        "FOREX_1": {"magic": 26082201, "tp1": 1.0, "tp2": 2.0, "be": True, "msnr": True, "tf": "M5"},
        "BOOM": {"magic": 26082101, "tp1": 1.0, "tp2": 2.0, "be": True, "msnr": True, "tf": "M5"},
        "VOLATILITY_1": {"magic": 26082401, "tp1": 1.0, "tp2": 2.0, "be": True, "msnr": True, "tf": "M5"},
    }
    for prof, exp in workers_check.items():
        cfg = LiveTradingConfig(bot_profile=prof, magic=exp["magic"], execution_enabled=False)
        rules = configure_worker_rules(cfg)
        assert rules.first_target_rr == exp["tp1"]
        assert rules.second_target_rr == exp["tp2"]
        assert rules.break_even_enabled is exp["be"]
        assert rules.entry_timeframe == exp["tf"]
        assert rules.malaysian_snr_enabled is exp["msnr"]
