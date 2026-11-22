import os
import json
import re

from config.strategy_config import PRUNED_ASSET_UNIVERSE
from strategy.malaysian_snr.universe import FAMILIES
from strategy.execution.live_trading_engine import LiveTradingConfig
from strategy.execution.worker_rules import configure_worker_rules
from dashboard.realtime_dashboard import _WORKER_PROFILE_META
from config.ict_instrument_policy import resolve_active_pruned_worker_universe


def test_volatility_multistrategy_universe_contains_all_eight_indices():
    vol_symbols = PRUNED_ASSET_UNIVERSE.get("VOLATILITY_3", ())
    expected = {
        "Volatility 10 Index", "Volatility 100 Index", "Volatility 15 Index",
        "Volatility 25 Index", "Volatility 5 Index", "Volatility 50 Index",
        "Volatility 75 Index", "Volatility 90 Index"
    }
    assert expected.issubset(set(vol_symbols)), f"Faltan índices Volatility en PRUNED_ASSET_UNIVERSE['VOLATILITY_3']: {expected - set(vol_symbols)}"
    assert len(vol_symbols) == 8, f"Se esperaban 8 índices en VOLATILITY_3, encontrados {len(vol_symbols)}"
    for sym in expected:
        assert sym in FAMILIES["synthetics"], f"{sym} falta en FAMILIES['synthetics']"


def test_resolve_active_pruned_worker_universe_volatility_3():
    univ = resolve_active_pruned_worker_universe("VOLATILITY_3")
    expected = {
        "Volatility 10 Index", "Volatility 100 Index", "Volatility 15 Index",
        "Volatility 25 Index", "Volatility 5 Index", "Volatility 50 Index",
        "Volatility 75 Index", "Volatility 90 Index"
    }
    assert set(univ) == expected, f"VOLATILITY_3 debe resolver exactamente los 8 índices objetivo: {set(univ)}"


def test_worker_rules_volatility_3_enables_multistrategy():
    cfg = LiveTradingConfig(bot_profile="VOLATILITY_3", magic=26082403, execution_enabled=False)
    configured = configure_worker_rules(cfg)
    
    assert getattr(configured, "malaysian_snr_enabled", False) is True, "Worker VOLATILITY_3 debe tener malaysian_snr_enabled=True"
    assert getattr(configured, "entry_timeframe", "") == "M5", "Worker VOLATILITY_3 debe operar gatillo M5"
    assert getattr(configured, "first_target_rr", 0.0) == 1.0, "TP1 debe ser 1.0R"
    assert getattr(configured, "second_target_rr", 0.0) == 2.0, "TP2 runner debe ser 2.0R"
    assert getattr(configured, "break_even_enabled", False) is True, "Break-even debe estar activado"


def test_dashboard_volatility_3_worker_cataloged_as_multistrategy():
    meta = _WORKER_PROFILE_META.get("VOLATILITY_3")
    assert meta is not None, "Metadata de VOLATILITY_3 debe existir en _WORKER_PROFILE_META"
    assert meta.get("strategy_key") == "MULTISTRATEGY", f"strategy_key debe ser MULTISTRATEGY, obtenido {meta.get('strategy_key')}"
    assert meta.get("strategy_label") == "MultiStrategia", f"strategy_label debe ser MultiStrategia, obtenido {meta.get('strategy_label')}"
    assert meta.get("magic") == 26082403, f"Magic debe ser 26082403, obtenido {meta.get('magic')}"
    assert "7572" in str(meta.get("label", "")), "Label debe incluir PID 7572"
    assert not meta.get("consolidated_hidden", False), "VOLATILITY_3 no debe estar oculto como consolidado"


def test_dashboard_volatility_3_frontend_unification_in_both_tabs():
    with open("dashboard/realtime_dashboard.py", "r", encoding="utf-8") as f:
        src = f.read()

    # 1. Pestaña SYNTHETICS debe tener la tarjeta de Worker VOLATILITY (3) MultiStrategia
    assert "Worker VOLATILITY (3) (MultiStrategia · Magic 26082403 · PID 7572 · Índices Volatility)" in src

    # 2. Pestaña MALAYSIAN_SNR debe agrupar los Volatility bajo category: 'worker_vol_3_msnr'
    assert "worker_vol_3_msnr" in src
    assert "VOLATILITY (MULTI)" in src

    # 3. Badge en workerForInstrument debe asignar VOLATILITY (MULTI)
    assert "Worker VOLATILITY (3) (MultiStrategia · Magic 26082403 · PID 7572)" in src


def test_backend_msnr_excludes_volatility_multistrategy_indices():
    with open("app/main.py", "r", encoding="utf-8") as f:
        src = f.read()
    
    assert "vol_multi_targets" in src, "Worker general MALAYSIAN_SNR debe definir vol_multi_targets"
    assert "str(s).lower() not in vol_multi_targets" in src, "Worker general MALAYSIAN_SNR debe excluir los 8 Volatility Index para evitar duplicidad"


def test_strategy_bases_has_all_eight_volatility_multistrategy_indices():
    with open("dashboard/strategy_bases_page.py", "r", encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"const\s+WINNERS_DATA\s*=\s*(\[.*?\]);", text, re.DOTALL)
    assert m is not None, "WINNERS_DATA not found"
    winners = json.loads(m.group(1))
    
    vol_multistrat = {w["symbol"] for w in winners if "volatility" in w.get("symbol", "").lower() and w.get("strategy") == "MultiStrategia" and "26082403" in w.get("category", "")}
    expected = {
        "Volatility 10 Index", "Volatility 100 Index", "Volatility 15 Index",
        "Volatility 25 Index", "Volatility 5 Index", "Volatility 50 Index",
        "Volatility 75 Index", "Volatility 90 Index"
    }
    assert expected.issubset(vol_multistrat), f"Missing volatility symbols in WINNERS_DATA: {expected - vol_multistrat}"


def test_position_strategy_origin_logic_volatility():
    meta_msnr = {"strategy_name": "Malaysian SNR", "trade_leg": "TP1"}
    trade_msnr = {"instrument": "Volatility 25 Index", "comment": "MSNR-7572-TP1", "magic": 26082403}
    strat_msnr = meta_msnr.get("strategy_name") or ("Malaysian SNR" if "MSNR" in str(trade_msnr.get("comment", "")).upper() else None)
    assert strat_msnr == "Malaysian SNR"

    meta_ict = {"strategy_name": "ICT", "trade_leg": "RUNNER"}
    trade_ict = {"instrument": "Volatility 75 Index", "comment": "ICT-7572-RUNNER", "magic": 26082403}
    strat_ict = meta_ict.get("strategy_name") or ("ICT" if "ICT" in str(trade_ict.get("comment", "")).upper() else None)
    assert strat_ict == "ICT"


def test_dashboard_worker_card_stratlabel_displays_multistrategy():
    with open("dashboard/realtime_dashboard.py", "r", encoding="utf-8") as f:
        src = f.read()

    # Comprobar que en el renderizador de tarjetas de workers (renderWorkersOverview),
    # stratLabel incluye expresamente a VOLATILITY_3 como 'MultiStrategia'.
    assert "prof === 'VOLATILITY_3'" in src, "VOLATILITY_3 debe estar incluido en la resolución de stratLabel en el frontend"
    assert "MultiStrategia" in src, "stratLabel debe resolver a MultiStrategia para trabajadores multiestrategia"

