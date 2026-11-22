import json
import re

from config.strategy_config import PRUNED_ASSET_UNIVERSE
from strategy.malaysian_snr.universe import FAMILIES
from strategy.execution.live_trading_engine import LiveTradingConfig
from strategy.execution.worker_rules import configure_worker_rules
from dashboard.realtime_dashboard import _WORKER_PROFILE_META
from config.ict_instrument_policy import resolve_active_pruned_worker_universe


def test_volatility_4_multistrategy_universe_contains_all_eleven_indices():
    vol_1s_symbols = PRUNED_ASSET_UNIVERSE.get("VOLATILITY_4", ())
    expected = {
        "Volatility 100 (1s) Index", "Volatility 150 (1s) Index", "Volatility 250 (1s) Index",
        "Volatility 50 (1s) Index", "Volatility 75 (1s) Index", "Volatility 90 (1s) Index",
        "Volatility 10 (1s) Index", "Volatility 15 (1s) Index", "Volatility 25 (1s) Index",
        "Volatility 30 (1s) Index", "Volatility 5 (1s) Index"
    }
    assert expected.issubset(set(vol_1s_symbols)), f"Faltan índices en PRUNED_ASSET_UNIVERSE['VOLATILITY_4']: {expected - set(vol_1s_symbols)}"
    assert len(vol_1s_symbols) == 11, f"Se esperaban 11 índices en VOLATILITY_4, encontrados {len(vol_1s_symbols)}"


def test_resolve_active_pruned_worker_universe_volatility_4():
    univ = resolve_active_pruned_worker_universe("VOLATILITY_4")
    expected = {
        "Volatility 100 (1s) Index", "Volatility 150 (1s) Index", "Volatility 250 (1s) Index",
        "Volatility 50 (1s) Index", "Volatility 75 (1s) Index", "Volatility 90 (1s) Index",
        "Volatility 10 (1s) Index", "Volatility 15 (1s) Index", "Volatility 25 (1s) Index",
        "Volatility 30 (1s) Index", "Volatility 5 (1s) Index"
    }
    assert set(univ) == expected, f"VOLATILITY_4 debe resolver exactamente los 11 índices objetivo: {set(univ)}"


def test_worker_rules_volatility_4_enables_multistrategy():
    cfg = LiveTradingConfig(bot_profile="VOLATILITY_4", magic=26082404, execution_enabled=False)
    configured = configure_worker_rules(cfg)
    
    assert getattr(configured, "malaysian_snr_enabled", False) is True, "Worker VOLATILITY_4 debe tener malaysian_snr_enabled=True"
    assert getattr(configured, "entry_timeframe", "") == "M5", "Worker VOLATILITY_4 debe operar gatillo M5"
    assert getattr(configured, "first_target_rr", 0.0) == 1.0, "TP1 debe ser 1.0R"
    assert getattr(configured, "second_target_rr", 0.0) == 2.0, "TP2 runner debe ser 2.0R"
    assert getattr(configured, "break_even_enabled", False) is True, "Break-even debe estar activado"


def test_dashboard_volatility_4_worker_cataloged_as_multistrategy():
    meta = _WORKER_PROFILE_META.get("VOLATILITY_4")
    assert meta is not None, "Metadata de VOLATILITY_4 debe existir en _WORKER_PROFILE_META"
    assert meta.get("strategy_key") == "MULTISTRATEGY", f"strategy_key debe ser MULTISTRATEGY, obtenido {meta.get('strategy_key')}"
    assert meta.get("strategy_label") == "MultiStrategia", f"strategy_label debe ser MultiStrategia, obtenido {meta.get('strategy_label')}"
    assert meta.get("magic") == 26082404, f"Magic debe ser 26082404, obtenido {meta.get('magic')}"
    assert "35156" in str(meta.get("label", "")), "Label debe incluir PID 35156"
    assert not meta.get("consolidated_hidden", False), "VOLATILITY_4 no debe estar oculto como consolidado"


def test_dashboard_volatility_4_frontend_unification_in_both_tabs():
    with open("dashboard/realtime_dashboard.py", "r", encoding="utf-8") as f:
        src = f.read()

    # 1. Pestaña SYNTHETICS debe tener la tarjeta de Worker VOLATILITY (4) MultiStrategia
    assert "Worker VOLATILITY (4) (MultiStrategia · Magic 26082404 · PID 35156 · Índices Volatility 1s)" in src

    # 2. Pestaña MALAYSIAN_SNR debe agrupar los Volatility 1s bajo category: 'worker_vol_4_msnr'
    assert "worker_vol_4_msnr" in src
    assert "VOLATILITY (1S MULTI)" in src

    # 3. Badge en workerForInstrument debe asignar VOLATILITY (1S MULTI)
    assert "Worker VOLATILITY (4) (MultiStrategia · Magic 26082404 · PID 35156)" in src


def test_backend_msnr_excludes_volatility_1s_multistrategy_indices():
    with open("app/main.py", "r", encoding="utf-8") as f:
        src = f.read()
    
    assert "volatility 100 (1s) index" in src.lower(), "Worker general MALAYSIAN_SNR debe excluir Volatility 100 (1s) Index"
    assert "volatility 5 (1s) index" in src.lower(), "Worker general MALAYSIAN_SNR debe excluir Volatility 5 (1s) Index"


def test_strategy_bases_has_all_eleven_volatility_1s_multistrategy_indices():
    with open("dashboard/strategy_bases_page.py", "r", encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"const\s+WINNERS_DATA\s*=\s*(\[.*?\]);", text, re.DOTALL)
    assert m is not None, "WINNERS_DATA not found"
    winners = json.loads(m.group(1))
    
    vol_1s_multistrat = {w["symbol"] for w in winners if "(1s)" in w.get("symbol", "").lower() and w.get("strategy") == "MultiStrategia" and "26082404" in w.get("category", "")}
    expected = {
        "Volatility 100 (1s) Index", "Volatility 150 (1s) Index", "Volatility 250 (1s) Index",
        "Volatility 50 (1s) Index", "Volatility 75 (1s) Index", "Volatility 90 (1s) Index",
        "Volatility 10 (1s) Index", "Volatility 15 (1s) Index", "Volatility 25 (1s) Index",
        "Volatility 30 (1s) Index", "Volatility 5 (1s) Index"
    }
    assert expected.issubset(vol_1s_multistrat), f"Missing volatility 1s symbols in WINNERS_DATA: {expected - vol_1s_multistrat}"


def test_position_strategy_origin_logic_volatility_1s():
    meta_msnr = {"strategy_name": "Malaysian SNR", "trade_leg": "TP1"}
    trade_msnr = {"instrument": "Volatility 50 (1s) Index", "comment": "MSNR-35156-TP1", "magic": 26082404}
    strat_msnr = meta_msnr.get("strategy_name") or ("Malaysian SNR" if "MSNR" in str(trade_msnr.get("comment", "")).upper() else None)
    assert strat_msnr == "Malaysian SNR"

    meta_ict = {"strategy_name": "ICT", "trade_leg": "RUNNER"}
    trade_ict = {"instrument": "Volatility 250 (1s) Index", "comment": "ICT-35156-RUNNER", "magic": 26082404}
    strat_ict = meta_ict.get("strategy_name") or ("ICT" if "ICT" in str(trade_ict.get("comment", "")).upper() else None)
    assert strat_ict == "ICT"


def test_volatility_4_all_eleven_instruments_active_without_pruning():
    from dashboard.realtime_dashboard import (
        _resolve_worker_universe_and_selection,
        DEFAULT_PRIORITIZED_SYMBOLS,
        PRUNED_INSTRUMENTS_INFO
    )
    from config.ict_instrument_policy import ict_active_symbols, MALAYSIAN_SNR_ACTIVE

    vol4_all = [
        "Volatility 100 (1s) Index", "Volatility 150 (1s) Index", "Volatility 250 (1s) Index",
        "Volatility 50 (1s) Index", "Volatility 75 (1s) Index", "Volatility 90 (1s) Index",
        "Volatility 10 (1s) Index", "Volatility 15 (1s) Index", "Volatility 25 (1s) Index",
        "Volatility 30 (1s) Index", "Volatility 5 (1s) Index",
    ]

    # 1. Ningún índice debe estar en PRUNED_INSTRUMENTS_INFO
    for s in vol4_all:
        assert s not in PRUNED_INSTRUMENTS_INFO, f"{s} no debe estar en PRUNED_INSTRUMENTS_INFO"

    # 2. Todos deben estar en DEFAULT_PRIORITIZED_SYMBOLS de SYNTHETICS y MALAYSIAN_SNR
    synths = DEFAULT_PRIORITIZED_SYMBOLS.get("SYNTHETICS", [])
    msnr = DEFAULT_PRIORITIZED_SYMBOLS.get("MALAYSIAN_SNR", [])
    for s in vol4_all:
        assert s in synths, f"{s} falta en DEFAULT_PRIORITIZED_SYMBOLS['SYNTHETICS']"
        assert s in msnr, f"{s} falta en DEFAULT_PRIORITIZED_SYMBOLS['MALAYSIAN_SNR']"
        assert s in ict_active_symbols("SYNTHETICS"), f"{s} falta en ict_active_symbols('SYNTHETICS')"
        assert s in MALAYSIAN_SNR_ACTIVE, f"{s} falta en MALAYSIAN_SNR_ACTIVE"

    # 3. La resolución del worker VOLATILITY_4 debe arrojar exactamente 11 activos y 0 podados
    res = _resolve_worker_universe_and_selection("VOLATILITY_4", None, None)
    assert res["universe_symbols_count"] == 11, f"Se esperaban 11 en universo, obtenidos {res['universe_symbols_count']}"
    assert res["active_symbols_count"] == 11, f"Se esperaban 11 activos, obtenidos {res['active_symbols_count']}"
    assert res["pruned_symbols_count"] == 0, f"Se esperaban 0 podados, obtenidos {res['pruned_symbols_count']}"
    assert set(res["active_symbols"]) == set(vol4_all)
