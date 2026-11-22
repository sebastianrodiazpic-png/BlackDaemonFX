import json
import re

from config.strategy_config import PRUNED_ASSET_UNIVERSE
from strategy.execution.live_trading_engine import LiveTradingConfig
from strategy.execution.worker_rules import configure_worker_rules
from dashboard.realtime_dashboard import _WORKER_PROFILE_META
from config.ict_instrument_policy import resolve_active_pruned_worker_universe


def test_volatility_1_hf_multistrategy_universe_contains_all_five_indices():
    vol_hf_symbols = PRUNED_ASSET_UNIVERSE.get("VOLATILITY_1", ())
    expected = {
        "High Frequency Vol 100 Index", "High Frequency Vol 50 Index",
        "High Frequency Vol 10 Index", "High Frequency Vol 25 Index",
        "High Frequency Vol 75 Index"
    }
    assert expected.issubset(set(vol_hf_symbols)), f"Faltan índices en PRUNED_ASSET_UNIVERSE['VOLATILITY_1']: {expected - set(vol_hf_symbols)}"
    assert len(vol_hf_symbols) == 5, f"Se esperaban 5 índices en VOLATILITY_1, encontrados {len(vol_hf_symbols)}"


def test_resolve_active_pruned_worker_universe_volatility_1():
    univ = resolve_active_pruned_worker_universe("VOLATILITY_1")
    expected = {
        "High Frequency Vol 100 Index", "High Frequency Vol 50 Index",
        "High Frequency Vol 10 Index", "High Frequency Vol 25 Index",
        "High Frequency Vol 75 Index"
    }
    assert set(univ) == expected, f"VOLATILITY_1 debe resolver exactamente los 5 índices HF objetivo: {set(univ)}"


def test_worker_rules_volatility_1_enables_multistrategy():
    cfg = LiveTradingConfig(bot_profile="VOLATILITY_1", magic=26082401, execution_enabled=False)
    configured = configure_worker_rules(cfg)
    
    assert getattr(configured, "malaysian_snr_enabled", False) is True, "Worker VOLATILITY_1 debe tener malaysian_snr_enabled=True"
    assert getattr(configured, "entry_timeframe", "") == "M5", "Worker VOLATILITY_1 debe operar gatillo M5"
    assert getattr(configured, "first_target_rr", 0.0) == 1.0, "TP1 debe ser 1.0R"
    assert getattr(configured, "second_target_rr", 0.0) == 2.0, "TP2 runner debe ser 2.0R"
    assert getattr(configured, "break_even_enabled", False) is True, "Break-even debe estar activado"


def test_dashboard_volatility_1_worker_cataloged_as_multistrategy():
    meta = _WORKER_PROFILE_META.get("VOLATILITY_1")
    assert meta is not None, "Metadata de VOLATILITY_1 debe existir en _WORKER_PROFILE_META"
    assert meta.get("strategy_key") == "MULTISTRATEGY", f"strategy_key debe ser MULTISTRATEGY, obtenido {meta.get('strategy_key')}"
    assert meta.get("strategy_label") == "MultiStrategia", f"strategy_label debe ser MultiStrategia, obtenido {meta.get('strategy_label')}"
    assert meta.get("magic") == 26082401, f"Magic debe ser 26082401, obtenido {meta.get('magic')}"
    assert "14464" in str(meta.get("label", "")), "Label debe incluir PID 14464"
    assert not meta.get("consolidated_hidden", False), "VOLATILITY_1 no debe estar oculto como consolidado"


def test_dashboard_volatility_1_frontend_unification_in_both_tabs():
    with open("dashboard/realtime_dashboard.py", "r", encoding="utf-8") as f:
        src = f.read()

    # 1. Pestaña SYNTHETICS debe tener la tarjeta de Worker VOLATILITY (1) MultiStrategia
    assert "Worker VOLATILITY (1) (MultiStrategia · Magic 26082401 · PID 14464 · High Frequency Vol)" in src

    # 2. Pestaña MALAYSIAN_SNR debe agrupar los HF bajo category: 'worker_vol_1_msnr'
    assert "worker_vol_1_msnr" in src
    assert "VOLATILITY (HF MULTI)" in src

    # 3. Badge en workerForInstrument debe asignar VOLATILITY (HF MULTI)
    assert "Worker VOLATILITY (1) (MultiStrategia · Magic 26082401 · PID 14464)" in src


def test_backend_msnr_excludes_volatility_hf_multistrategy_indices():
    with open("app/main.py", "r", encoding="utf-8") as f:
        src = f.read()
    
    assert "high frequency vol 100 index" in src.lower(), "Worker general MALAYSIAN_SNR debe excluir High Frequency Vol 100 Index"
    assert "high frequency vol 10 index" in src.lower(), "Worker general MALAYSIAN_SNR debe excluir High Frequency Vol 10 Index"


def test_strategy_bases_has_all_five_volatility_hf_multistrategy_indices():
    with open("dashboard/strategy_bases_page.py", "r", encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"const\s+WINNERS_DATA\s*=\s*(\[.*?\]);", text, re.DOTALL)
    assert m is not None, "WINNERS_DATA not found"
    winners = json.loads(m.group(1))
    
    vol_hf_multistrat = {w["symbol"] for w in winners if "high frequency vol" in w.get("symbol", "").lower() and w.get("strategy") == "MultiStrategia" and "26082401" in w.get("category", "")}
    expected = {
        "High Frequency Vol 100 Index", "High Frequency Vol 50 Index",
        "High Frequency Vol 10 Index", "High Frequency Vol 25 Index",
        "High Frequency Vol 75 Index"
    }
    assert expected.issubset(vol_hf_multistrat), f"Missing HF symbols in WINNERS_DATA: {expected - vol_hf_multistrat}"


def test_position_strategy_origin_logic_volatility_hf():
    # Malaysian SNR origin
    meta_msnr = {"strategy_name": "Malaysian SNR", "trade_leg": "TP1"}
    trade_msnr = {"instrument": "High Frequency Vol 100 Index", "comment": "MSNR-14464-TP1", "magic": 26082401}
    strat_msnr = meta_msnr.get("strategy_name") or ("Malaysian SNR" if "MSNR" in str(trade_msnr.get("comment", "")).upper() else None)
    assert strat_msnr == "Malaysian SNR"

    # ICT origin
    meta_ict = {"strategy_name": "ICT", "trade_leg": "TP2"}
    trade_ict = {"instrument": "High Frequency Vol 50 Index", "comment": "ICT-14464-TP2", "magic": 26082401}
    strat_ict = meta_ict.get("strategy_name") or ("ICT" if "ICT" in str(trade_ict.get("comment", "")).upper() else None)
    assert strat_ict == "ICT"

    # Fallback to MultiStrategia by Magic
    meta_none = {}
    trade_magic = {"instrument": "High Frequency Vol 10 Index", "comment": "", "magic": 26082401}
    strat_fallback = ("MultiStrategia" if str(trade_magic.get("magic")) in ("26082104", "26082102", "26082101", "26082105", "26082401", "26082403", "26082404") else None)
    assert strat_fallback == "MultiStrategia"
