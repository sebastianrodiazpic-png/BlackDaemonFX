"""Verificación de remoción del worker MSNR y pestaña /Instruments de MSNR, preservando Malaysian SNR."""
import app.main as m
from dashboard import realtime_dashboard as rd
from config.ict_instrument_policy import MALAYSIAN_SNR_ACTIVE, POLICY_SELECTION_PROFILES
from strategy.execution.live_trading_engine import LiveTradingEngine


def test_msnr_worker_and_tab_removed_while_malaysian_snr_preserved():
    # 1. Arquitectura de workers
    assert "MSNR" not in m.BOT_PROFILES
    assert "MSNR" not in m.FULL_MULTI_BOT_PROFILES
    assert "MALAYSIAN_SNR" in m.BOT_PROFILES
    assert "MALAYSIAN_SNR" in m.FULL_MULTI_BOT_PROFILES

    # 2. Selección en /Instruments
    assert "MSNR" not in rd._SELECTION_PROFILES
    assert "MALAYSIAN_SNR" in rd._SELECTION_PROFILES
    assert "MSNR" not in POLICY_SELECTION_PROFILES
    assert "MALAYSIAN_SNR" in POLICY_SELECTION_PROFILES

    # 3. HTML de /Instruments
    html = rd._INSTRUMENTS_HTML
    assert 'data-profile="MSNR"' not in html
    assert 'MSNR Vídeos Activo' not in html
    assert 'data-profile="MALAYSIAN_SNR"' in html
    assert 'MALAYSIAN SNR' in html

    # 4. Engine y resolución de bot profile
    assert LiveTradingEngine._selection_profile_for_bot("MALAYSIAN_SNR") == "MALAYSIAN_SNR"
    assert LiveTradingEngine._selection_profile_for_bot("MSNR") != "MSNR"
    assert m._selection_profile_for_bot("MALAYSIAN_SNR") == "MALAYSIAN_SNR"
    assert m._selection_profile_for_bot("MSNR") != "MSNR"

    # 5. Prioritized symbols
    assert "MSNR" not in rd.DEFAULT_PRIORITIZED_SYMBOLS
    assert rd.DEFAULT_PRIORITIZED_SYMBOLS["MALAYSIAN_SNR"] == list(MALAYSIAN_SNR_ACTIVE)
