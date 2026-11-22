"""
Test suite de verificación para Worker VOLATILITY (2) (PID 36704, Magic 26082402):
MultiStrategia (Malaysian SNR M5 + ICT M5) en Ladder y VolSwitch.
"""
import json
import re

from config.strategy_config import PRUNED_ASSET_UNIVERSE
from strategy.execution.live_trading_engine import LiveTradingConfig
from strategy.execution.worker_rules import configure_worker_rules
from dashboard.realtime_dashboard import _WORKER_PROFILE_META
from config.ict_instrument_policy import (
    ICT_5Y_RESCUED_SYNTHETICS,
    MSNR_ACIERTO47_SYNTHETICS,
    resolve_active_pruned_worker_universe,
)
from app.main import BOT_PROFILES, _resolve_symbols_for_profile_shared


EXPECTED_INSTRUMENTS = [
    "Ladder Volatility Down Index",
    "Ladder Volatility Up Index",
    "VolSwitch Low Vol Index",
    "VolSwitch Medium Vol Index",
]


def test_volatility_2_special_multistrategy_universe_contains_all_indices():
    vol2_symbols = PRUNED_ASSET_UNIVERSE.get("VOLATILITY_2", ())
    for inst in EXPECTED_INSTRUMENTS:
        assert inst in vol2_symbols, f"Falta {inst} en PRUNED_ASSET_UNIVERSE['VOLATILITY_2']"


def test_resolve_active_pruned_worker_universe_volatility_2():
    univ = resolve_active_pruned_worker_universe("VOLATILITY_2")
    for inst in EXPECTED_INSTRUMENTS:
        assert inst in univ, f"VOLATILITY_2 debe resolver {inst}"


def test_worker_rules_volatility_2_enables_multistrategy():
    cfg = LiveTradingConfig(bot_profile="VOLATILITY_2", magic=26082402, execution_enabled=False)
    configured = configure_worker_rules(cfg)
    
    assert getattr(configured, "malaysian_snr_enabled", False) is True, "Worker VOLATILITY_2 debe tener malaysian_snr_enabled=True"
    assert getattr(configured, "entry_timeframe", "") == "M5", "Worker VOLATILITY_2 debe operar gatillo M5"
    assert getattr(configured, "first_target_rr", 0.0) == 1.0, "TP1 debe ser 1.0R"
    assert getattr(configured, "second_target_rr", 0.0) == 2.0, "TP2 runner debe ser 2.0R"
    assert getattr(configured, "break_even_enabled", False) is True, "Break-even debe estar activado"


def test_dashboard_volatility_2_worker_cataloged_as_multistrategy():
    meta = _WORKER_PROFILE_META.get("VOLATILITY_2")
    assert meta is not None, "Metadata de VOLATILITY_2 debe existir en _WORKER_PROFILE_META"
    assert meta.get("strategy_key") == "MULTISTRATEGY", f"strategy_key debe ser MULTISTRATEGY, obtenido {meta.get('strategy_key')}"
    assert meta.get("strategy_label") == "MultiStrategia", f"strategy_label debe ser MultiStrategia, obtenido {meta.get('strategy_label')}"
    assert meta.get("magic") == 26082402, f"Magic debe ser 26082402, obtenido {meta.get('magic')}"
    assert "36704" in str(meta.get("label", "")), "Label debe incluir PID 36704"
    assert not meta.get("consolidated_hidden", False), "VOLATILITY_2 no debe estar oculto como consolidado"


def test_dashboard_volatility_2_frontend_unification_in_both_tabs():
    with open("dashboard/realtime_dashboard.py", "r", encoding="utf-8") as f:
        src = f.read()

    # 1. Pestaña SYNTHETICS debe tener la tarjeta de Worker VOLATILITY (2) MultiStrategia
    assert "Worker VOLATILITY (2) (MultiStrategia · Magic 26082402 · PID 36704 · Ladder & VolSwitch)" in src

    # 2. Pestaña MALAYSIAN_SNR debe agrupar bajo category: 'worker_vol_2_msnr'
    assert "worker_vol_2_msnr" in src
    assert "VOLATILITY (SPECIAL MULTI)" in src

    # 3. Badge en workerForInstrument debe asignar VOLATILITY (SPECIAL MULTI)
    assert "Worker VOLATILITY (2) (MultiStrategia · Magic 26082402 · PID 36704)" in src


def test_backend_msnr_excludes_volatility_special_multistrategy_indices():
    with open("app/main.py", "r", encoding="utf-8") as f:
        src = f.read()
    
    assert "ladder volatility down index" in src.lower(), "Worker general MALAYSIAN_SNR debe excluir Ladder Volatility Down Index"
    assert "volswitch low vol index" in src.lower(), "Worker general MALAYSIAN_SNR debe excluir VolSwitch Low Vol Index"


def test_strategy_bases_has_all_volatility_special_multistrategy_indices():
    with open("dashboard/strategy_bases_page.py", "r", encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"const\s+WINNERS_DATA\s*=\s*(\[.*?\]);", text, re.DOTALL)
    assert m is not None, "WINNERS_DATA not found"
    
    parsed = json.loads(m.group(1))
    special_symbols = {d["symbol"] for d in parsed if "VOLATILITY (2)" in d.get("category", "")}
    for expected in EXPECTED_INSTRUMENTS:
        assert expected in special_symbols, f"Falta {expected} en WINNERS_DATA de Strategy Bases"


def test_dashboard_instruments_save_volatility_2_symbols():
    from dashboard.realtime_dashboard import RealtimeDashboardService
    srv = RealtimeDashboardService()
    res = srv.update_selected_symbols(EXPECTED_INSTRUMENTS, "SYNTHETICS")
    assert res.get("ok") is True, f"Fallo al guardar selección de VOLATILITY_2 en SYNTHETICS: {res}"
    for sym in EXPECTED_INSTRUMENTS:
        assert sym in res.get("selected_symbols", [])


def test_dashboard_instruments_legacy_alias_normalization():
    from dashboard.realtime_dashboard import RealtimeDashboardService
    srv = RealtimeDashboardService()
    legacy_list = ["Ladder Volatility Down Index", "Ladder Volatility Up", "VolSwitch Low Vol Index", "VolSwitch Medium Vol Index"]
    res = srv.update_selected_symbols(legacy_list, "SYNTHETICS")
    assert res.get("ok") is True, f"Fallo al guardar con alias legado: {res}"
    assert "Ladder Volatility Up Index" in res.get("selected_symbols", [])
    assert "Ladder Volatility Up" not in res.get("selected_symbols", [])

