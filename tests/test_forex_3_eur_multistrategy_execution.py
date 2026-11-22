"""
Test suite de verificación para Worker FOREX (3) (PID 10072, Magic 26082203):
MultiStrategia (Malaysian SNR M5 + ICT M5 + Frankfurt/London/NY Killzones) en pares EUR.
"""
import json
import re

from config.strategy_config import PRUNED_ASSET_UNIVERSE
from strategy.execution.live_trading_engine import LiveTradingConfig
from strategy.execution.worker_rules import configure_worker_rules
from dashboard.realtime_dashboard import _WORKER_PROFILE_META
from config.ict_instrument_policy import (
    resolve_active_pruned_worker_universe,
    FOREX_SNR_ACTIVE,
)
from app.main import BOT_PROFILES, _resolve_symbols_for_profile_shared


EXPECTED_INSTRUMENTS = [
    "EURAUD", "EURAUDmicro",
    "EURCAD", "EURCADmicro",
    "EURCHF", "EURCHFmicro",
    "EURGBP", "EURGBPmicro",
    "EURJPY", "EURJPYmicro",
    "EURNZD", "EURNZDmicro",
    "EURUSD", "EURUSDmicro",
    "EURHKD", "EURMXN", "EURNOK",
    "EURPLN", "EURSEK", "EURSGD", "EURZAR",
]


def test_forex_3_eur_multistrategy_universe_contains_all_instruments():
    forex3_symbols = PRUNED_ASSET_UNIVERSE.get("FOREX_3", ())
    for inst in EXPECTED_INSTRUMENTS:
        assert inst in forex3_symbols, f"Falta {inst} en PRUNED_ASSET_UNIVERSE['FOREX_3']"


def test_resolve_active_pruned_worker_universe_forex_3():
    univ = resolve_active_pruned_worker_universe("FOREX_3")
    for inst in EXPECTED_INSTRUMENTS:
        assert inst in univ, f"FOREX_3 debe resolver {inst}"


def test_bot_profiles_forex_3_spec():
    spec = BOT_PROFILES.get("FOREX_3")
    assert spec is not None, "FOREX_3 debe existir en BOT_PROFILES"
    assert spec.get("magic") == 26082203, f"Magic debe ser 26082203, obtenido {spec.get('magic')}"
    for inst in EXPECTED_INSTRUMENTS:
        assert inst in spec.get("symbols", []), f"Falta {inst} en BOT_PROFILES['FOREX_3']['symbols']"


def test_worker_rules_forex_3_enables_multistrategy():
    cfg = LiveTradingConfig(bot_profile="FOREX_3", magic=26082203, execution_enabled=False)
    configured = configure_worker_rules(cfg)
    
    assert getattr(configured, "malaysian_snr_enabled", False) is True, "Worker FOREX_3 debe tener malaysian_snr_enabled=True"
    assert getattr(configured, "forex_killzone_only_enabled", True) is False, "Worker FOREX_3 debe tener forex_killzone_only_enabled=False para habilitar sesiones europeas"
    assert getattr(configured, "entry_timeframe", "") == "M5", "Worker FOREX_3 debe operar gatillo M5"
    assert getattr(configured, "first_target_rr", 0.0) == 1.0, "TP1 debe ser 1.0R"
    assert getattr(configured, "second_target_rr", 0.0) == 2.0, "TP2 runner debe ser 2.0R"
    assert getattr(configured, "break_even_enabled", False) is True, "Break-even debe estar activado"


def test_dashboard_forex_3_worker_cataloged_as_multistrategy():
    meta = _WORKER_PROFILE_META.get("FOREX_3")
    assert meta is not None, "Metadata de FOREX_3 debe existir en _WORKER_PROFILE_META"
    assert meta.get("strategy_key") == "MULTISTRATEGY", f"strategy_key debe ser MULTISTRATEGY, obtenido {meta.get('strategy_key')}"
    assert meta.get("strategy_label") == "MultiStrategia", f"strategy_label debe ser MultiStrategia, obtenido {meta.get('strategy_label')}"
    assert meta.get("magic") == 26082203, f"Magic debe ser 26082203, obtenido {meta.get('magic')}"
    assert "10072" in str(meta.get("label", "")), "Label debe incluir PID 10072"
    assert not meta.get("consolidated_hidden", False), "FOREX_3 no debe estar oculto como consolidado"


def test_dashboard_forex_3_frontend_unification_in_both_tabs():
    with open("dashboard/realtime_dashboard.py", "r", encoding="utf-8") as f:
        src = f.read()

    # 1. Pestaña FOREX debe tener la tarjeta y agrupación de Worker FOREX (3) MultiStrategia
    assert "Worker FOREX (3) (MultiStrategia · Magic 26082203 · PID 10072 · Pares EUR)" in src

    # 2. Badge en workerForInstrument debe asignar FOREX (EUR MULTI)
    assert "FOREX (EUR MULTI)" in src
    assert "Worker FOREX (3) (MultiStrategia · Magic 26082203 · PID 10072)" in src

    # 3. isMultiStrat y strategy_origin deben reconocer 26082203 y FOREX_3
    assert "26082203" in src
    assert "prof === 'FOREX_3'" in src


def test_strategy_bases_has_all_forex_3_eur_indices():
    with open("dashboard/strategy_bases_page.py", "r", encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"const\s+WINNERS_DATA\s*=\s*(\[.*?\]);", text, re.DOTALL)
    assert m is not None, "WINNERS_DATA not found"
    
    parsed = json.loads(m.group(1))
    forex3_symbols = {d["symbol"] for d in parsed if "FOREX (3)" in d.get("category", "")}
    for expected in EXPECTED_INSTRUMENTS:
        assert expected in forex3_symbols, f"Falta {expected} en WINNERS_DATA de Strategy Bases"


def test_dashboard_instruments_save_forex_3_symbols():
    from dashboard.realtime_dashboard import RealtimeDashboardService
    srv = RealtimeDashboardService()
    res = srv.update_selected_symbols(EXPECTED_INSTRUMENTS, "FOREX")
    assert res.get("ok") is True, f"Fallo al guardar selección de FOREX_3 en FOREX: {res}"


def test_dashboard_forex_snr_tab_has_ordered_forex_3_instruments():
    from dashboard.realtime_dashboard import RealtimeDashboardService
    srv = RealtimeDashboardService()
    res = srv.update_selected_symbols(EXPECTED_INSTRUMENTS, "FOREX_SNR")
    assert res.get("ok") is True, f"Fallo al guardar selección de FOREX_3 en FOREX_SNR: {res}"
