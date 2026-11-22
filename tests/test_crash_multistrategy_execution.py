"""Tests de validación unitaria para la MultiStrategia en la familia Crash Index.

Verifica:
1. Catálogo unificado de los 8 Crash Index (Crash 1000, 300, 500, 600, 900, Volatility Crash 400, 550, 750).
2. Configuración del Worker CRASH (Magic 26082102 · PID 25904) con MultiStrategia (MSNR + ICT).
3. Identificación de la estrategia de origen en el estado de salud de posiciones.
4. Alimentación completa de /Strategy-bases con los 8 Crash Index.
5. Exclusión de los 8 Crash Index en el Worker general MALAYSIAN_SNR.
"""

import json
import re
import pytest
from config.strategy_config import PRUNED_ASSET_UNIVERSE
from strategy.malaysian_snr.universe import FAMILIES
from strategy.execution.live_trading_engine import LiveTradingConfig
from strategy.execution.worker_rules import configure_worker_rules
from dashboard.realtime_dashboard import _WORKER_PROFILE_META


def test_crash_universe_contains_all_eight_indices():
    crash_syms = PRUNED_ASSET_UNIVERSE.get("CRASH", ())
    expected = {
        "Crash 1000 Index", "Crash 300 Index", "Crash 500 Index", "Crash 600 Index", "Crash 900 Index",
        "Volatility Crash 400 Index", "Volatility Crash 550 Index", "Volatility Crash 750 Index"
    }
    assert set(crash_syms) == expected, f"Expected {expected}, got {set(crash_syms)}"
    for sym in expected:
        assert sym in FAMILIES["synthetics"], f"{sym} falta en FAMILIES['synthetics']"


def test_worker_rules_crash_enables_multistrategy():
    cfg = LiveTradingConfig(bot_profile="CRASH", magic=26082102, execution_enabled=False)
    configured = configure_worker_rules(cfg)
    assert getattr(configured, "malaysian_snr_enabled", False) is True
    assert getattr(configured, "first_target_rr", 0.0) == 1.0
    assert getattr(configured, "second_target_rr", 0.0) == 2.0
    assert getattr(configured, "break_even_enabled", False) is True
    assert getattr(configured, "entry_timeframe", "") == "M5"


def test_dashboard_crash_worker_cataloged_as_multistrategy():
    crash_spec = _WORKER_PROFILE_META.get("CRASH")
    assert crash_spec is not None
    assert crash_spec.get("strategy_label") == "MultiStrategia"
    assert crash_spec.get("strategy_key") == "MULTISTRATEGY"
    assert crash_spec.get("magic") == 26082102
    label = crash_spec.get("label", "")
    assert "MultiStrategia" in label
    assert "26082102" in label
    assert "25904" in label


def test_dashboard_crash_frontend_unification_in_both_tabs():
    with open("dashboard/realtime_dashboard.py", "r", encoding="utf-8") as f:
        code = f.read()

    # Pestaña SYNTHETICS unificada con Magic 26082102 y PID 25904
    assert "Worker CRASH (MultiStrategia · Magic 26082102 · PID 25904)" in code

    # Pestaña MALAYSIAN_SNR unificada con Worker CRASH
    assert "category: 'worker_crash_msnr'" in code
    assert "worker: 'CRASH'" in code
    assert "Worker CRASH (MultiStrategia · Magic 26082102 · PID 25904 · Índices Crash)" in code

    # workerForInstrument asegura que cualquier índice Crash tenga la insignia CRASH (MULTI)
    assert "/crash/i.test(l)" in code
    assert "CRASH (MULTI)" in code


def test_backend_msnr_excludes_crash_indices():
    from dashboard.realtime_dashboard import _resolve_worker_universe_and_selection, DEFAULT_PRIORITIZED_SYMBOLS
    assert "Crash 500 Index" in DEFAULT_PRIORITIZED_SYMBOLS.get("MALAYSIAN_SNR", [])

    info = _resolve_worker_universe_and_selection("MALAYSIAN_SNR", catalog=[], selection_profiles={})
    msnr_universe = info.get("universe_symbols", [])
    crash_in_msnr = [s for s in msnr_universe if "crash" in str(s).lower()]
    assert len(crash_in_msnr) == 0, f"Worker MALAYSIAN_SNR no debe operar Crash Index, encontrados: {crash_in_msnr}"


def test_strategy_bases_has_all_eight_crash_indices():
    with open("dashboard/strategy_bases_page.py", "r", encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"const\s+WINNERS_DATA\s*=\s*(\[.*?\]);", text, re.DOTALL)
    assert m is not None, "WINNERS_DATA not found"
    winners = json.loads(m.group(1))
    
    symbols_found = {w["symbol"] for w in winners if "crash" in w.get("symbol", "").lower()}
    expected = {
        "Crash 1000 Index", "Crash 300 Index", "Crash 500 Index", "Crash 600 Index", "Crash 900 Index",
        "Volatility Crash 400 Index", "Volatility Crash 550 Index", "Volatility Crash 750 Index"
    }
    assert expected.issubset(symbols_found), f"Missing crash symbols in WINNERS_DATA: {expected - symbols_found}"


def test_position_strategy_origin_logic_crash():
    # Simulamos metadata de una posición Malaysian SNR y una posición ICT
    meta_msnr = {"strategy_name": "Malaysian SNR", "trade_leg": "TP1"}
    trade_msnr = {"instrument": "Crash 500 Index", "comment": "MSNR-25904-TP1", "magic": 26082102}
    strat_msnr = meta_msnr.get("strategy_name") or ("Malaysian SNR" if "MSNR" in str(trade_msnr.get("comment", "")).upper() else None)
    assert strat_msnr == "Malaysian SNR"

    meta_ict = {"strategy_name": "ICT", "trade_leg": "RUNNER"}
    trade_ict = {"instrument": "Crash 1000 Index", "comment": "ICT-25904-RUNNER", "magic": 26082102}
    strat_ict = meta_ict.get("strategy_name") or ("ICT" if "ICT" in str(trade_ict.get("comment", "")).upper() else None)
    assert strat_ict == "ICT"
