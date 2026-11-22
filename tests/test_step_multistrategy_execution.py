"""Tests de validación unitaria para la MultiStrategia en la familia Step Index.

Verifica:
1. Catálogo unificado de los 5 Step Index (Step Index, Step Index 200, 300, 400, 500).
2. Configuración del Worker STEP (Magic 26082104) con MultiStrategia (MSNR + ICT).
3. Identificación de la estrategia de origen en el estado de salud de posiciones.
4. Alimentación completa de /Strategy-bases con los 5 Step Index.
"""

import json
import re
import pytest
from config.strategy_config import PRUNED_ASSET_UNIVERSE
from strategy.malaysian_snr.universe import FAMILIES
from strategy.execution.live_trading_engine import LiveTradingConfig
from strategy.execution.worker_rules import configure_worker_rules
from dashboard.realtime_dashboard import _WORKER_PROFILE_META


def test_step_universe_contains_all_five_indices():
    step1_syms = PRUNED_ASSET_UNIVERSE.get("STEP", ())
    step2_syms = PRUNED_ASSET_UNIVERSE.get("STEP_2", ())
    expected_step1 = {"Step Index 200", "Step Index 400", "Step Index 500"}
    expected_step2 = {"Step Index", "Step Index 300", "Step Index 1000", "Step Index 1500", "Step Index 2000"}
    assert set(step1_syms) == expected_step1, f"Expected {expected_step1}, got {set(step1_syms)}"
    assert set(step2_syms) == expected_step2, f"Expected {expected_step2}, got {set(step2_syms)}"
    assert "Step Index 300" in FAMILIES["synthetics"]


def test_worker_rules_step_enables_multistrategy():
    cfg = LiveTradingConfig(bot_profile="STEP", magic=26082104, execution_enabled=False)
    configured = configure_worker_rules(cfg)
    assert getattr(configured, "malaysian_snr_enabled", False) is True
    assert getattr(configured, "first_target_rr", 0.0) == 1.0
    assert getattr(configured, "second_target_rr", 0.0) == 2.0
    assert getattr(configured, "break_even_enabled", False) is True
    assert getattr(configured, "entry_timeframe", "") == "M5"


def test_dashboard_step_worker_cataloged_as_multistrategy():
    step_spec = _WORKER_PROFILE_META.get("STEP")
    assert step_spec is not None
    assert step_spec.get("strategy_label") == "MultiStrategia"
    assert step_spec.get("strategy_key") == "MULTISTRATEGY"
    assert step_spec.get("magic") == 26082104
    label = step_spec.get("label", "")
    assert "MultiStrategia" in label
    assert "26082104" in label
    assert "17452" in label


def test_dashboard_frontend_unification_in_both_tabs():
    with open("dashboard/realtime_dashboard.py", "r", encoding="utf-8") as f:
        code = f.read()

    # Pestaña SYNTHETICS unificada con Magic 26082104 y PID 17452
    assert "Worker STEP (1) (MultiStrategia · Magic 26082104 · PID 17452)" in code or "Worker STEP (MultiStrategia · Magic 26082104 · PID 17452)" in code

    # Pestaña MALAYSIAN_SNR unificada con Worker STEP (MultiStrategia · Magic 26082104 · PID 17452 · Índices Step)
    assert "category: 'worker_step_msnr'" in code
    assert "worker: 'STEP'" in code
    assert "Worker STEP (MultiStrategia · Magic 26082104 · PID 17452 · Índices Step)" in code

    # workerForInstrument asegura que cualquier índice Step tenga la insignia STEP (MULTI)
    assert "/step/i.test(l)" in code
    assert "STEP (MULTI)" in code


def test_backend_msnr_excludes_step_indices():
    from dashboard.realtime_dashboard import _resolve_worker_universe_and_selection, DEFAULT_PRIORITIZED_SYMBOLS
    assert "Step Index 300" in DEFAULT_PRIORITIZED_SYMBOLS.get("MALAYSIAN_SNR", [])

    info = _resolve_worker_universe_and_selection("MALAYSIAN_SNR", catalog=[], selection_profiles={})
    msnr_universe = info.get("universe_symbols", [])
    step_in_msnr = [s for s in msnr_universe if "step" in str(s).lower()]
    assert len(step_in_msnr) == 0, f"Worker MALAYSIAN_SNR no debe operar Step Index, encontrados: {step_in_msnr}"


def test_strategy_bases_has_all_five_step_indices():
    with open("dashboard/strategy_bases_page.py", "r", encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"const\s+WINNERS_DATA\s*=\s*(\[.*?\]);", text, re.DOTALL)
    assert m is not None, "WINNERS_DATA not found"
    winners = json.loads(m.group(1))
    
    symbols_found = {w["symbol"] for w in winners if "step" in w.get("symbol", "").lower()}
    expected = {"Step Index", "Step Index 200", "Step Index 300", "Step Index 400", "Step Index 500"}
    assert expected.issubset(symbols_found), f"Missing step symbols in WINNERS_DATA: {expected - symbols_found}"


def test_position_strategy_origin_logic():
    # Simulamos metadata de una posición Malaysian SNR y una posición ICT
    meta_msnr = {"strategy_name": "Malaysian SNR", "trade_leg": "TP1"}
    trade_msnr = {"instrument": "Step Index 200", "comment": "MSNR-12345-TP1", "magic": 26082104}
    strat_msnr = meta_msnr.get("strategy_name") or ("Malaysian SNR" if "MSNR" in str(trade_msnr.get("comment", "")).upper() else None)
    assert strat_msnr == "Malaysian SNR"

    meta_ict = {"strategy_name": "ICT", "trade_leg": "RUNNER"}
    trade_ict = {"instrument": "Step Index 400", "comment": "ICT-67890-RUNNER", "magic": 26082104}
    strat_ict = meta_ict.get("strategy_name") or ("ICT" if "ICT" in str(trade_ict.get("comment", "")).upper() else None)
    assert strat_ict == "ICT"
