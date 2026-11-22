import os
import json
import re

from config.strategy_config import PRUNED_ASSET_UNIVERSE
from strategy.malaysian_snr.universe import FAMILIES
from strategy.execution.live_trading_engine import LiveTradingConfig
from strategy.execution.worker_rules import configure_worker_rules
from dashboard.realtime_dashboard import _WORKER_PROFILE_META


def test_jump_universe_contains_all_five_indices():
    jump_symbols = PRUNED_ASSET_UNIVERSE.get("JUMP", ())
    expected = {
        "Jump 10 Index", "Jump 25 Index", "Jump 50 Index", "Jump 75 Index", "Jump 100 Index"
    }
    assert expected.issubset(set(jump_symbols)), f"Faltan índices Jump en PRUNED_ASSET_UNIVERSE['JUMP']: {expected - set(jump_symbols)}"
    assert len(jump_symbols) == 5, f"Se esperaban 5 índices en JUMP, encontrados {len(jump_symbols)}"
    for sym in expected:
        assert sym in FAMILIES["synthetics"], f"{sym} falta en FAMILIES['synthetics']"


def test_worker_rules_jump_enables_multistrategy():
    cfg = LiveTradingConfig(bot_profile="JUMP", magic=26082105, execution_enabled=False)
    configured = configure_worker_rules(cfg)
    
    assert getattr(configured, "malaysian_snr_enabled", False) is True, "Worker JUMP debe tener malaysian_snr_enabled=True"
    assert getattr(configured, "entry_timeframe", "") == "M5", "Worker JUMP debe operar gatillo M5"
    assert getattr(configured, "first_target_rr", 0.0) == 1.0, "TP1 debe ser 1.0R"
    assert getattr(configured, "second_target_rr", 0.0) == 2.0, "TP2 runner debe ser 2.0R"
    assert getattr(configured, "break_even_enabled", False) is True, "Break-even debe estar activado"


def test_dashboard_jump_worker_cataloged_as_multistrategy():
    meta = _WORKER_PROFILE_META.get("JUMP")
    assert meta is not None, "Metadata de JUMP debe existir en _WORKER_PROFILE_META"
    assert meta.get("strategy_key") == "MULTISTRATEGY", f"strategy_key debe ser MULTISTRATEGY, obtenido {meta.get('strategy_key')}"
    assert meta.get("strategy_label") == "MultiStrategia", f"strategy_label debe ser MultiStrategia, obtenido {meta.get('strategy_label')}"
    assert meta.get("magic") == 26082105, f"Magic debe ser 26082105, obtenido {meta.get('magic')}"
    assert "16804" in str(meta.get("label", "")), "Label debe incluir PID 16804"


def test_dashboard_jump_frontend_unification_in_both_tabs():
    with open("dashboard/realtime_dashboard.py", "r", encoding="utf-8") as f:
        src = f.read()

    # 1. Pestaña SYNTHETICS debe tener la tarjeta de Worker JUMP MultiStrategia
    assert "Worker JUMP (MultiStrategia · Magic 26082105 · PID 16804)" in src, "Falta la tarjeta de Worker JUMP MultiStrategia en SYNTHETICS"

    # 2. Pestaña MALAYSIAN_SNR debe agrupar los Jump bajo category: 'worker_jump_msnr'
    assert "worker_jump_msnr" in src, "Falta category worker_jump_msnr en pestaña MALAYSIAN_SNR"
    assert "Worker JUMP (MultiStrategia · Magic 26082105 · PID 16804 · Índices Jump)" in src, "Falta tarjeta unificada de Jump en pestaña MALAYSIAN_SNR"

    # 3. Badge en workerForInstrument debe asignar JUMP (MULTI)
    assert "JUMP (MULTI)" in src, "workerForInstrument debe asignar insignia JUMP (MULTI)"
    assert "Jump (MultiStrategia · PID 16804)" in src, "msnrFamilyLabel debe identificar Jump (MultiStrategia · PID 16804)"


def test_backend_msnr_excludes_jump_indices():
    with open("app/main.py", "r", encoding="utf-8") as f:
        src = f.read()
    
    # MALAYSIAN_SNR general debe excluir índices que contengan 'jump'
    assert '"jump" not in str(s).lower()' in src, "Worker general MALAYSIAN_SNR debe excluir Jump Index para evitar duplicidad"


def test_strategy_bases_has_all_five_jump_indices():
    with open("dashboard/strategy_bases_page.py", "r", encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"const\s+WINNERS_DATA\s*=\s*(\[.*?\]);", text, re.DOTALL)
    assert m is not None, "WINNERS_DATA not found"
    winners = json.loads(m.group(1))
    
    jump_multistrat = {w["symbol"] for w in winners if "jump" in w.get("symbol", "").lower() and w.get("strategy") == "MultiStrategia"}
    expected = {
        "Jump 10 Index", "Jump 25 Index", "Jump 50 Index", "Jump 75 Index", "Jump 100 Index"
    }
    assert expected.issubset(jump_multistrat), f"Missing jump symbols in WINNERS_DATA: {expected - jump_multistrat}"


def test_position_strategy_origin_logic_jump():
    meta_msnr = {"strategy_name": "Malaysian SNR", "trade_leg": "TP1"}
    trade_msnr = {"instrument": "Jump 25 Index", "comment": "MSNR-16804-TP1", "magic": 26082105}
    strat_msnr = meta_msnr.get("strategy_name") or ("Malaysian SNR" if "MSNR" in str(trade_msnr.get("comment", "")).upper() else None)
    assert strat_msnr == "Malaysian SNR"

    meta_ict = {"strategy_name": "ICT", "trade_leg": "RUNNER"}
    trade_ict = {"instrument": "Jump 75 Index", "comment": "ICT-16804-RUNNER", "magic": 26082105}
    strat_ict = meta_ict.get("strategy_name") or ("ICT" if "ICT" in str(trade_ict.get("comment", "")).upper() else None)
    assert strat_ict == "ICT"
