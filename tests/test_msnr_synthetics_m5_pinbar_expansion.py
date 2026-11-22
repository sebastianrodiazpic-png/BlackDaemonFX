# -*- coding: utf-8 -*-
"""
tests/test_msnr_synthetics_m5_pinbar_expansion.py
=================================================
Verifica que las mejoras cuantitativas para Malaysian SNR en Sintéticos estén:
1. Activas por defecto en la configuración (Gatillo M5, Retesteo Pinbar, Ventana 720 min).
2. Sincronizadas fielmente en /Strategy-bases (HTML y CSV de replay de 5 años).
"""
import pytest
import pandas as pd
from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.malaysian_snr.runtime_settings import msnr_default_settings
from dashboard.strategy_bases_page import STRATEGY_BASES_HTML

def test_msnr_config_defaults():
    cfg = MalaysianSNRConfig()
    assert cfg.m5_confirmation_mode == "live"
    assert cfg.retest_pinbar_mode == "live"
    assert cfg.retest_window_minutes == 720
    assert cfg.enable_fakeout_trap is True

def test_msnr_runtime_settings_defaults():
    settings = msnr_default_settings()
    assert settings['m5_confirmation_mode'] == "live"
    assert settings['retest_pinbar_mode'] == "live"
    assert settings['retest_window_minutes'] == 720

def test_msnr_synthetics_5y_csv_consistency():
    df = pd.read_csv("storage/analysis/replay_5y_perfect_strategy_bases.csv")
    msnr_synths = df[(df['strategy'] == 'Malaysian SNR') & (df['category'] == 'SYNTHETICS')]
    
    assert len(msnr_synths) == 38
    total_trades = msnr_synths['trades_despues'].sum()
    total_r = msnr_synths['r_despues'].sum()
    total_pnl = msnr_synths['pnl_despues'].sum()
    
    # 21,612 trades en 5 años (duplicando de 10,394)
    assert total_trades == 21612
    assert round(total_r, 2) == 17719.88
    assert round(total_pnl, 2) == 1771988.0

def test_strategy_bases_page_has_optimized_metrics():
    # Tarjeta Resumen Principal (38 Sintéticos + 35 Mercados Reales = 73 Activos)
    assert "+23,673.03R" in STRATEGY_BASES_HTML
    assert "34,057 Trades" in STRATEGY_BASES_HTML
    
    # Verificación de activos líderes optimizados en WINNERS_DATA
    assert '"symbol": "Jump 75 Index"' in STRATEGY_BASES_HTML
    assert '"trades": 854' in STRATEGY_BASES_HTML
    assert '"trades": 745' in STRATEGY_BASES_HTML
    assert '"trades": 729' in STRATEGY_BASES_HTML
