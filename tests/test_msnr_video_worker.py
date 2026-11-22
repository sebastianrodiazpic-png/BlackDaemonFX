"""Verificación de remoción de workers redundantes SNR y pestañas de /Instruments."""
import app.main as m
from dashboard import realtime_dashboard as rd
from config.ict_instrument_policy import POLICY_SELECTION_PROFILES
from strategy.execution.live_trading_engine import LiveTradingEngine


def test_snr_workers_and_tabs_removed_consolidated_into_multistrategy():
    # 1. Arquitectura de workers concurrentes: se eliminaron los workers SNR redundantes
    assert "MALAYSIAN_SNR" not in m.FULL_MULTI_BOT_PROFILES
    assert "FOREX_SNR" not in m.FULL_MULTI_BOT_PROFILES
    assert "COMMODITIES_SNR" not in m.FULL_MULTI_BOT_PROFILES
    assert "MSNR" not in m.FULL_MULTI_BOT_PROFILES

    # 2. Selección en /Instruments: removidos de pestañas de políticas
    assert "MALAYSIAN_SNR" not in POLICY_SELECTION_PROFILES
    assert "FOREX_SNR" not in POLICY_SELECTION_PROFILES
    assert "COMMODITIES_SNR" not in POLICY_SELECTION_PROFILES

    # 3. HTML de /Instruments: botones de pestañas eliminados
    html = rd._INSTRUMENTS_HTML
    assert 'data-profile="MALAYSIAN_SNR"' not in html
    assert 'data-profile="FOREX_SNR"' not in html
    assert 'data-profile="COMMODITIES_SNR"' not in html

    # 4. En _WORKER_PROFILE_META están marcados como consolidated_hidden
    for prof in ("MALAYSIAN_SNR", "FOREX_SNR", "COMMODITIES_SNR"):
        meta = rd._WORKER_PROFILE_META.get(prof, {})
        assert meta.get("consolidated_hidden") is True

    # 5. Workers MultiStrategia activos permanecen en FULL_MULTI_BOT_PROFILES
    for expected in ("BOOM", "CRASH", "STEP", "JUMP", "FOREX_1", "FOREX_2", "FOREX_3", "FOREX_4", "FOREX_5", "ICT", "INDICESB_SNR"):
        assert expected in m.FULL_MULTI_BOT_PROFILES
