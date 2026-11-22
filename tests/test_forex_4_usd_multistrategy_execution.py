"""
tests/test_forex_4_usd_multistrategy_execution.py
=================================================
Validación de la integración y ejecución del Worker FOREX (4) (Magic 26082204 · PID 12676)
para los 14 instrumentos de la divisa Dólar Estadounidense (USD) bajo arquitectura MultiStrategia (MSNR M5 + ICT M5).
"""

import pytest
from config.strategy_config import PRUNED_ASSET_UNIVERSE
from config.ict_instrument_policy import (
    resolve_active_pruned_worker_universe,
    FOREX_SNR_ACTIVE,
    ICT_FOREX_ACTIVE
)
from app.main import BOT_PROFILES
from strategy.execution.live_trading_engine import LiveTradingConfig
from strategy.execution.worker_rules import configure_worker_rules
from dashboard.realtime_dashboard import _WORKER_PROFILE_META, RealtimeDashboardService

USD_EXPECTED_INSTRUMENTS = [
    "USDCAD", "USDCADmicro",
    "USDCHF", "USDCHFmicro",
    "USDJPY", "USDJPYmicro",
    "USDCNH", "USDHKD", "USDMXN",
    "USDNOK", "USDPLN", "USDSEK",
    "USDSGD", "USDZAR",
]

def test_forex_4_usd_multistrategy_universe_contains_all_instruments():
    """Valida que PRUNED_ASSET_UNIVERSE['FOREX_4'] contenga exactamente los 14 instrumentos USD."""
    forex_4_univ = PRUNED_ASSET_UNIVERSE.get("FOREX_4", ())
    assert len(forex_4_univ) == 14, f"Se esperaban 14 instrumentos en FOREX_4, se encontraron {len(forex_4_univ)}"
    for sym in USD_EXPECTED_INSTRUMENTS:
        assert sym in forex_4_univ, f"Instrumento {sym} no encontrado en PRUNED_ASSET_UNIVERSE['FOREX_4']"

def test_resolve_active_pruned_worker_universe_forex_4():
    """Valida que resolve_active_pruned_worker_universe devuelva los 14 instrumentos para FOREX_4 y los sustraiga de FOREX_1."""
    res_4 = resolve_active_pruned_worker_universe("FOREX_4")
    assert len(res_4) == 14
    for sym in USD_EXPECTED_INSTRUMENTS:
        assert sym in res_4

    res_1 = resolve_active_pruned_worker_universe("FOREX_1")
    # Ningún instrumento de FOREX_4 debe estar en FOREX_1
    overlap = set(res_4).intersection(set(res_1))
    assert not overlap, f"Solapamiento detectado entre FOREX_1 y FOREX_4: {overlap}"

def test_bot_profiles_forex_4_spec():
    """Valida la especificación de BOT_PROFILES para FOREX_4 (Magic 26082204, PID 12676)."""
    spec = BOT_PROFILES.get("FOREX_4")
    assert spec is not None, "FOREX_4 no encontrado en BOT_PROFILES"
    assert spec.get("magic") == 26082204, f"Magic incorrecto: {spec.get('magic')} (esperado 26082204)"
    symbols = spec.get("symbols", [])
    assert len(symbols) == 14
    for sym in USD_EXPECTED_INSTRUMENTS:
        assert sym in symbols

def test_worker_rules_forex_4_enables_multistrategy():
    """Valida que configure_worker_rules para FOREX_4 active MultiStrategia en M5 con contrato 1.0R / 2.0R y BE."""
    cfg = LiveTradingConfig(bot_profile="FOREX_4", magic=26082204, execution_enabled=False)
    rules = configure_worker_rules(cfg)
    
    assert rules.malaysian_snr_enabled is True, "malaysian_snr_enabled no activado en FOREX_4"
    assert rules.entry_timeframe == "M5", f"Timeframe de entrada {rules.entry_timeframe} no es M5"
    assert rules.first_target_rr == 1.0, f"TP1 {rules.first_target_rr} != 1.0R"
    assert rules.second_target_rr == 2.0, f"TP2 {rules.second_target_rr} != 2.0R"
    assert rules.break_even_enabled is True, "break_even_enabled no es True"
    assert rules.forex_rollover_guard_enabled is True, "forex_rollover_guard_enabled no está activo"
    assert rules.forex_force_flat_friday is True, "forex_force_flat_friday no está activo"
    assert rules.forex_killzone_only_enabled is False, "forex_killzone_only_enabled debe ser False para permitir Asian session"

def test_dashboard_forex_4_worker_cataloged_as_multistrategy():
    """Valida que _WORKER_PROFILE_META cataloge a FOREX_4 como MultiStrategia visible."""
    meta = _WORKER_PROFILE_META.get("FOREX_4")
    assert meta is not None, "FOREX_4 no encontrado en _WORKER_PROFILE_META"
    assert meta.get("strategy_key") == "MULTISTRATEGY"
    assert meta.get("strategy_label") == "MultiStrategia"
    assert meta.get("magic") == 26082204
    assert meta.get("consolidated_hidden") is False, "FOREX_4 debe estar visible en el dashboard"
    assert "PID 12676" in str(meta.get("label", ""))

def test_dashboard_forex_4_frontend_unification_in_both_tabs():
    """Valida que en realtime_dashboard.py el frontend unifique FOREX_4 en pestañas FOREX y FOREX_SNR."""
    with open("dashboard/realtime_dashboard.py", "r", encoding="utf-8") as f:
        src = f.read()
    
    assert "Worker FOREX (4) (MultiStrategia · Magic 26082204 · PID 12676 · Pares USD)" in src
    assert "FOREX (USD MULTI)" in src
    assert "26082204" in src

def test_strategy_bases_has_all_forex_4_usd_indices():
    """Valida que dashboard/strategy_bases_page.py tenga los 14 instrumentos USD inyectados en WINNERS_DATA."""
    with open("dashboard/strategy_bases_page.py", "r", encoding="utf-8") as f:
        sb_src = f.read()
    
    for sym in USD_EXPECTED_INSTRUMENTS:
        assert f'"{sym}"' in sb_src, f"Símbolo {sym} no encontrado en strategy_bases_page.py"
        assert f"Forex · Worker FOREX (4) (Magic 26082204 · PID 12676 · Pares USD)" in sb_src

def test_dashboard_instruments_save_forex_4_symbols():
    """Valida que el servicio del dashboard permita guardar los 14 símbolos USD en catálogo FOREX y FOREX_SNR."""
    srv = RealtimeDashboardService()
    res = srv.update_selected_symbols(USD_EXPECTED_INSTRUMENTS, "FOREX")
    assert res.get("ok") is True, f"Error al guardar símbolos FOREX_4: {res}"
    
    res_snr = srv.update_selected_symbols(USD_EXPECTED_INSTRUMENTS, "FOREX_SNR")
    assert res_snr.get("ok") is True, f"Error al guardar símbolos FOREX_4 en FOREX_SNR: {res_snr}"
