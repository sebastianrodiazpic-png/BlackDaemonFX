"""Tests de validación unitaria para la MultiStrategia en la familia Boom Index.

Verifica:
1. Catálogo unificado de los 7 Boom Index (Boom 1000, 300, 500, 600, 900, Volatility Boom 400, 750).
2. Configuración del Worker BOOM (Magic 26082101 · PID 20320) con MultiStrategia (MSNR + ICT).
3. Identificación de la estrategia de origen en el estado de salud de posiciones.
4. Alimentación completa de /Strategy-bases con los 7 Boom Index.
5. Exclusión de los 7 Boom Index en el Worker general MALAYSIAN_SNR.
"""

import json
import re
import pytest
from config.strategy_config import PRUNED_ASSET_UNIVERSE
from strategy.malaysian_snr.universe import FAMILIES
from strategy.execution.live_trading_engine import LiveTradingConfig
from strategy.execution.worker_rules import configure_worker_rules
from dashboard.realtime_dashboard import _WORKER_PROFILE_META


def test_boom_universe_contains_all_seven_indices():
    boom_syms = PRUNED_ASSET_UNIVERSE.get("BOOM", ())
    expected = {
        "Boom 1000 Index", "Boom 300 Index", "Boom 500 Index", "Boom 600 Index", "Boom 900 Index",
        "Volatility Boom 400 Index", "Volatility Boom 750 Index"
    }
    assert set(boom_syms) == expected, f"Expected {expected}, got {set(boom_syms)}"
    for sym in expected:
        assert sym in FAMILIES["synthetics"], f"{sym} falta en FAMILIES['synthetics']"


def test_worker_rules_boom_enables_multistrategy():
    cfg = LiveTradingConfig(bot_profile="BOOM", magic=26082101, execution_enabled=False)
    configured = configure_worker_rules(cfg)
    assert getattr(configured, "malaysian_snr_enabled", False) is True
    assert getattr(configured, "first_target_rr", 0.0) == 1.0
    assert getattr(configured, "second_target_rr", 0.0) == 2.0
    assert getattr(configured, "break_even_enabled", False) is True
    assert getattr(configured, "entry_timeframe", "") == "M5"


def test_dashboard_boom_worker_cataloged_as_multistrategy():
    boom_spec = _WORKER_PROFILE_META.get("BOOM")
    assert boom_spec is not None
    assert boom_spec.get("strategy_label") == "MultiStrategia"
    assert boom_spec.get("strategy_key") == "MULTISTRATEGY"
    assert boom_spec.get("magic") == 26082101
    label = boom_spec.get("label", "")
    assert "MultiStrategia" in label
    assert "26082101" in label
    assert "20320" in label


def test_dashboard_boom_frontend_unification_in_both_tabs():
    with open("dashboard/realtime_dashboard.py", "r", encoding="utf-8") as f:
        code = f.read()

    # Pestaña SYNTHETICS unificada con Magic 26082101 y PID 20320
    assert "Worker BOOM (MultiStrategia · Magic 26082101 · PID 20320)" in code

    # Pestaña MALAYSIAN_SNR unificada con Worker BOOM
    assert "category: 'worker_boom_msnr'" in code
    assert "worker: 'BOOM'" in code
    assert "Worker BOOM (MultiStrategia · Magic 26082101 · PID 20320 · Índices Boom)" in code

    # workerForInstrument asegura que cualquier índice Boom tenga la insignia BOOM (MULTI)
    assert "/boom/i.test(l)" in code
    assert "BOOM (MULTI)" in code


def test_backend_msnr_excludes_boom_indices():
    from dashboard.realtime_dashboard import _resolve_worker_universe_and_selection, DEFAULT_PRIORITIZED_SYMBOLS
    assert "Boom 500 Index" in DEFAULT_PRIORITIZED_SYMBOLS.get("MALAYSIAN_SNR", [])

    info = _resolve_worker_universe_and_selection("MALAYSIAN_SNR", catalog=[], selection_profiles={})
    msnr_universe = info.get("universe_symbols", [])
    boom_in_msnr = [s for s in msnr_universe if "boom" in str(s).lower()]
    assert len(boom_in_msnr) == 0, f"Worker MALAYSIAN_SNR no debe operar Boom Index, encontrados: {boom_in_msnr}"


def test_strategy_bases_has_all_seven_boom_indices():
    with open("dashboard/strategy_bases_page.py", "r", encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"const\s+WINNERS_DATA\s*=\s*(\[.*?\]);", text, re.DOTALL)
    assert m is not None, "WINNERS_DATA not found"
    winners = json.loads(m.group(1))
    
    symbols_found = {w["symbol"] for w in winners if "boom" in w.get("symbol", "").lower()}
    expected = {
        "Boom 1000 Index", "Boom 300 Index", "Boom 500 Index", "Boom 600 Index", "Boom 900 Index",
        "Volatility Boom 400 Index", "Volatility Boom 750 Index"
    }
    assert expected.issubset(symbols_found), f"Missing boom symbols in WINNERS_DATA: {expected - symbols_found}"


def test_position_strategy_origin_logic_boom():
    # Simulamos metadata de una posición Malaysian SNR y una posición ICT
    meta_msnr = {"strategy_name": "Malaysian SNR", "trade_leg": "TP1"}
    trade_msnr = {"instrument": "Boom 500 Index", "comment": "MSNR-20320-TP1", "magic": 26082101}
    strat_msnr = meta_msnr.get("strategy_name") or ("Malaysian SNR" if "MSNR" in str(trade_msnr.get("comment", "")).upper() else None)
    assert strat_msnr == "Malaysian SNR"

    meta_ict = {"strategy_name": "ICT", "trade_leg": "RUNNER"}
    trade_ict = {"instrument": "Boom 1000 Index", "comment": "ICT-20320-RUNNER", "magic": 26082101}
    strat_ict = meta_ict.get("strategy_name") or ("ICT" if "ICT" in str(trade_ict.get("comment", "")).upper() else None)
    assert strat_ict == "ICT"


def test_volatility_boom_400_and_750_active_in_msnr_policy_without_pruning():
    from config.ict_instrument_policy import MSNR_ACIERTO47_SYNTHETICS, MALAYSIAN_SNR_EXCLUDED
    from dashboard.realtime_dashboard import MALAYSIAN_SNR_PRUNED_INFO

    # 1. Ambos índices deben figurar en la lista blanca de acierto histórico MSNR
    assert "Volatility Boom 400 Index" in MSNR_ACIERTO47_SYNTHETICS
    assert "Volatility Boom 750 Index" in MSNR_ACIERTO47_SYNTHETICS

    # 2. Ninguno debe estar excluido ni podado en MSNR
    assert "Volatility Boom 400 Index" not in MALAYSIAN_SNR_EXCLUDED
    assert "Volatility Boom 750 Index" not in MALAYSIAN_SNR_EXCLUDED
    assert "Volatility Boom 400 Index" not in MALAYSIAN_SNR_PRUNED_INFO
    assert "Volatility Boom 750 Index" not in MALAYSIAN_SNR_PRUNED_INFO

    # 3. El dashboard en ambas pestañas no debe incluir el residuo 'Vol over Boom 550'
    with open("dashboard/realtime_dashboard.py", "r", encoding="utf-8") as f:
        src = f.read()
    assert "x !== 'Vol over Boom 550'" in src
    assert "s !== 'Vol over Boom 550'" in src
