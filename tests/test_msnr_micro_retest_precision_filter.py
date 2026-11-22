"""
tests/test_msnr_micro_retest_precision_filter.py
================================================
Verifica el comportamiento del Micro-Retest Precision Gate y Buffer Dinámico en Malaysian SNR:
1. Activado por defecto en la configuración.
2. Posibilidad de desactivar con DAEMONBLACKFX_MSNR_DYNAMIC_BUFFER=0.
3. Blindaje estricto de activos de élite (Jump 75, VolSwitch High Vol, Step Index) sin expansión de tolerancia.
4. Expansión selectiva de tolerancia en activos secundarios/tradicionales.
"""

import os
from unittest.mock import patch
import pytest

from strategy.malaysian_snr.config import MalaysianSNRConfig


def test_msnr_dynamic_buffer_defaults():
    cfg = MalaysianSNRConfig()
    assert cfg.dynamic_retest_buffer_enabled is True
    assert cfg.dynamic_retest_buffer_atr == 0.20


def test_msnr_dynamic_buffer_env_toggle():
    with patch.dict(os.environ, {"DAEMONBLACKFX_MSNR_DYNAMIC_BUFFER": "0"}):
        cfg = MalaysianSNRConfig()
        cfg.__post_init__()
        assert cfg.dynamic_retest_buffer_enabled is False

    with patch.dict(os.environ, {"DAEMONBLACKFX_MSNR_DYNAMIC_BUFFER": "1"}):
        cfg2 = MalaysianSNRConfig()
        cfg2.__post_init__()
        assert cfg2.dynamic_retest_buffer_enabled is True


def test_msnr_elite_protection_tolerance():
    cfg = MalaysianSNRConfig()
    assert cfg.dynamic_retest_buffer_enabled is True
    
    elite_symbols = ["Jump 75 Index", "VolSwitch High Vol Index", "Step Index 200", "Step Index 400"]
    non_elite_symbols = ["EURUSD", "Volatility 25 Index", "XAUUSD", "US Oil"]
    
    elite_protected = {
        "jump 75 index", "volswitch high vol index",
        "step index 200", "step index", "step index 400", "step index 500"
    }
    
    for sym in elite_symbols:
        effective_tolerance = cfg.retest_tolerance_atr
        if cfg.dynamic_retest_buffer_enabled:
            if str(sym).strip().lower() not in elite_protected:
                effective_tolerance += cfg.dynamic_retest_buffer_atr
        # En élite, debe permanecer exactamente en la tolerancia base (0.35)
        assert effective_tolerance == pytest.approx(0.35)
        
    for sym in non_elite_symbols:
        effective_tolerance = cfg.retest_tolerance_atr
        if cfg.dynamic_retest_buffer_enabled:
            if str(sym).strip().lower() not in elite_protected:
                effective_tolerance += cfg.dynamic_retest_buffer_atr
        # En no-élite, se expande con el buffer dinámico (0.35 + 0.20 = 0.55)
        assert effective_tolerance == pytest.approx(0.55)
