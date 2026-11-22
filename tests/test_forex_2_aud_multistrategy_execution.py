"""
Test suite de verificación para Worker FOREX (2) (PID 30880, Magic 26082202):
MultiStrategia (Malaysian SNR M5 + ICT M5 + Asian Killzone) en pares AUD.
"""
import json
import re

from config.strategy_config import PRUNED_ASSET_UNIVERSE
from strategy.execution.live_trading_engine import LiveTradingConfig
from strategy.execution.worker_rules import configure_worker_rules
from dashboard.realtime_dashboard import _WORKER_PROFILE_META
from config.ict_instrument_policy import (
    resolve_active_pruned_worker_universe,
)
from app.main import BOT_PROFILES, _resolve_symbols_for_profile_shared


EXPECTED_INSTRUMENTS = [
    "AUDCAD",
    "AUDCADmicro",
    "AUDCHF",
    "AUDCHFmicro",
    "AUDJPY",
    "AUDJPYmicro",
    "AUDNZD",
    "AUDNZDmicro",
    "AUDSGD",
    "AUDUSD",
    "AUDUSDmicro",
]


def test_forex_2_aud_multistrategy_universe_contains_all_instruments():
    forex2_symbols = PRUNED_ASSET_UNIVERSE.get("FOREX_2", ())
    for inst in EXPECTED_INSTRUMENTS:
        assert inst in forex2_symbols, f"Falta {inst} en PRUNED_ASSET_UNIVERSE['FOREX_2']"


def test_resolve_active_pruned_worker_universe_forex_2():
    univ = resolve_active_pruned_worker_universe("FOREX_2")
    for inst in EXPECTED_INSTRUMENTS:
        assert inst in univ, f"FOREX_2 debe resolver {inst}"


def test_worker_rules_forex_2_enables_multistrategy_and_asian_killzone():
    cfg = LiveTradingConfig(bot_profile="FOREX_2", magic=26082202, execution_enabled=False)
    configured = configure_worker_rules(cfg)
    
    assert getattr(configured, "malaysian_snr_enabled", False) is True, "Worker FOREX_2 debe tener malaysian_snr_enabled=True"
    assert getattr(configured, "forex_killzone_only_enabled", True) is False, "Worker FOREX_2 debe tener forex_killzone_only_enabled=False para habilitar Asian Killzone"
    assert getattr(configured, "entry_timeframe", "") == "M5", "Worker FOREX_2 debe operar gatillo M5"
    assert getattr(configured, "first_target_rr", 0.0) == 1.0, "TP1 debe ser 1.0R"
    assert getattr(configured, "second_target_rr", 0.0) == 2.0, "TP2 runner debe ser 2.0R"
    assert getattr(configured, "break_even_enabled", False) is True, "Break-even debe estar activado"


def test_dashboard_forex_2_worker_cataloged_as_multistrategy():
    meta = _WORKER_PROFILE_META.get("FOREX_2")
    assert meta is not None, "Metadata de FOREX_2 debe existir en _WORKER_PROFILE_META"
    assert meta.get("strategy_key") == "MULTISTRATEGY", f"strategy_key debe ser MULTISTRATEGY, obtenido {meta.get('strategy_key')}"
    assert meta.get("strategy_label") == "MultiStrategia", f"strategy_label debe ser MultiStrategia, obtenido {meta.get('strategy_label')}"
    assert meta.get("magic") == 26082202, f"Magic debe ser 26082202, obtenido {meta.get('magic')}"
    assert "30880" in str(meta.get("label", "")), "Label debe incluir PID 30880"
    assert not meta.get("consolidated_hidden", False), "FOREX_2 no debe estar oculto como consolidado"


def test_dashboard_forex_2_frontend_unification_in_both_tabs():
    with open("dashboard/realtime_dashboard.py", "r", encoding="utf-8") as f:
        src = f.read()

    # 1. Pestaña FOREX debe tener la tarjeta y agrupación de Worker FOREX (2) MultiStrategia
    assert "Worker FOREX (2) (MultiStrategia · Magic 26082202 · PID 30880 · Pares AUD)" in src

    # 2. Badge en workerForInstrument debe asignar FOREX (AUD MULTI)
    assert "FOREX (AUD MULTI)" in src
    assert "Worker FOREX (2) (MultiStrategia · Magic 26082202 · PID 30880)" in src

    # 3. isMultiStrat y strategy_origin deben reconocer 26082202 y FOREX_2
    assert "26082202" in src
    assert "prof === 'FOREX_2'" in src


def test_strategy_bases_has_all_forex_2_aud_indices():
    with open("dashboard/strategy_bases_page.py", "r", encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"const\s+WINNERS_DATA\s*=\s*(\[.*?\]);", text, re.DOTALL)
    assert m is not None, "WINNERS_DATA not found"
    
    parsed = json.loads(m.group(1))
    forex2_symbols = {d["symbol"] for d in parsed if "FOREX (2)" in d.get("category", "")}
    for expected in EXPECTED_INSTRUMENTS:
        assert expected in forex2_symbols, f"Falta {expected} en WINNERS_DATA de Strategy Bases"


def test_dashboard_instruments_save_forex_2_symbols():
    from dashboard.realtime_dashboard import RealtimeDashboardService
    srv = RealtimeDashboardService()
    res = srv.update_selected_symbols(EXPECTED_INSTRUMENTS, "FOREX")
    assert res.get("ok") is True, f"Fallo al guardar selección de FOREX_2 en FOREX: {res}"


def test_dashboard_forex_snr_tab_has_ordered_work_2_instruments():
    from dashboard.realtime_dashboard import FOREX_SNR_PRUNED_INFO
    from config.ict_instrument_policy import FOREX_SNR_ACTIVE

    with open("dashboard/realtime_dashboard.py", "r", encoding="utf-8") as f:
        src = f.read()

    # 1. Pestaña FOREX_SNR debe tener el grupo ordenado para Worker FOREX (2)
    assert "activeProfile === 'FOREX_SNR'" in src
    assert "worker_forex_2_snr" in src
    assert "Worker FOREX (2) (MultiStrategia · Magic 26082202 · PID 30880 · Pares AUD)" in src

    # 2. Ninguno de los 11 pares AUD debe estar en FOREX_SNR_PRUNED_INFO
    for inst in EXPECTED_INSTRUMENTS:
        assert inst not in FOREX_SNR_PRUNED_INFO, f"{inst} de Work 2 no debe estar en FOREX_SNR_PRUNED_INFO"

    # 3. Todos los 11 pares AUD deben estar en FOREX_SNR_ACTIVE
    for inst in EXPECTED_INSTRUMENTS:
        assert inst in FOREX_SNR_ACTIVE, f"{inst} de Work 2 debe estar en FOREX_SNR_ACTIVE"


def test_dashboard_instruments_save_forex_snr_symbols():
    from dashboard.realtime_dashboard import RealtimeDashboardService
    srv = RealtimeDashboardService()
    res = srv.update_selected_symbols(EXPECTED_INSTRUMENTS, "FOREX_SNR")
    assert res.get("ok") is True, f"Fallo al guardar selección de FOREX_2 en FOREX_SNR: {res}"

