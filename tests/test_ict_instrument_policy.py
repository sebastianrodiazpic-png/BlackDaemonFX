"""Política única de instrumentos ICT en /Instruments (20-oct-2026).



Las pestañas Sintéticos, Forex e ICT muestran como activo exactamente lo que operan los workers

(STEP, JUMP, VOLATILITY_1-4, BOOM, CRASH, FOREX_1-4, ICT) y el resto como PODA PREVENTIVA bloqueada.

"""

from config.ict_instrument_policy import (

    ICT_ACTIVE_BY_PROFILE,

    ICT_FOREX_ACTIVE,

    ICT_PHASE1_EXCLUDED,

    ICT_SYNTHETIC_FAMILIES,

    PREVENTIVE_PRUNE_LABEL,

    ict_active_symbols,

    preventive_prune_reason,

    sanitize_ict_selection,

)

from config.strategy_config import ICT_WR45_PRUNED





def test_synthetics_active_set_is_the_28_ict_synthetics():

    from config.synth_wr45 import REAL_SPREAD_PRUNED

    active = set(ict_active_symbols("SYNTHETICS"))

    assert len(active) == 36  # 05-nov-2026: auditoría 212 pares deja activos los 34 sintéticos base (+ 2 alias = 36) con WR > 50%

    assert not active & set(ICT_PHASE1_EXCLUDED)

    assert not (active & (set(ICT_WR45_PRUNED) - {"Boom 300 Index", "VolSwitch High Vol Index"}))

    assert {"Volatility 10 Index", "Step Index 200", "Boom 600 Index", "Jump 25 Index", "Volatility 25 Index", "Crash 300 Index", "Boom 300 Index", "Step Index", "Volatility 100 Index", "Boom 500 Index", "Crash 900 Index"} <= active





def test_ict_tab_has_no_crypto_silver_synthetics_or_forex():

    active = ict_active_symbols("ICT")

    assert set(active) == {
        "XAUUSD", "XAUUSDmicro", "microXAUUSD",
        "XAUEUR", "XAUEURmicro", "microXAUEUR",
        "BTCUSD", "BTCUSDmicro", "microBTCUSD",
        "US Oil", "US Tech 100", "Wall Street 30",
    }

    for profile in ("SYNTHETICS", "FOREX"):

        assert not set(active) & set(ict_active_symbols(profile))  # un instrumento, una pestaña





def test_engine_family_gates_follow_the_policy():

    from strategy.execution.live_trading_engine import LiveTradingConfig

    cfg = LiveTradingConfig()

    for family in ("STEP", "JUMP", "VOLATILITY", "BOOM", "CRASH"):

        assert tuple(getattr(cfg, f"{family.lower()}_allowed_symbols")) == ICT_SYNTHETIC_FAMILIES[family]

    assert tuple(cfg.forex_allowed_symbols) == ICT_FOREX_ACTIVE == ICT_ACTIVE_BY_PROFILE["FOREX"]





def test_phase1_exclusions_match_ict_strategy():

    from strategy.ict.config import ICTSabriMalleConfig

    assert set(ICT_PHASE1_EXCLUDED) == set(ICTSabriMalleConfig().excluded_symbols)





def test_sanitize_drops_preventive_prune_only_in_ict_tabs():

    assert sanitize_ict_selection("ICT", ["XAUUSD", "ETHUSD", "XAGUSD"]) == ["XAUUSD"]

    assert sanitize_ict_selection("SYNTHETICS", ["Crash 1000 Index", "Boom 600 Index"]) == ["Boom 600 Index"]

    assert sanitize_ict_selection("ORB", ["XAGUSD"]) == ["XAGUSD"]





def test_preventive_prune_reasons():

    assert preventive_prune_reason("XAUUSD", "ICT") == ""

    assert preventive_prune_reason("BTCUSD", "ICT") == ""

    for sym, profile in (("ETHUSD", "ICT"), ("XAGUSD", "ICT"), ("Crash 1000 Index", "SYNTHETICS"),

                         ("Volatility 90 (1s) Index", "SYNTHETICS"), ("EURUSD", "FOREX"), ("Boom 500 Index", "ICT")):

        assert preventive_prune_reason(sym, profile).startswith(PREVENTIVE_PRUNE_LABEL)

    assert "cripto" in preventive_prune_reason("ETHUSD", "ICT")





def test_dashboard_prioritized_and_prune_info_never_overlap():

    from dashboard import realtime_dashboard as rd

    catalog = [{"category": "ict_crypto_btcusd", "symbols": ["ETHUSD"]},

               {"category": "ict_metals_xauusd", "symbols": ["XAUUSD", "microXAUUSD"]},

               {"category": "boom", "symbols": ["Crash 1000 Index", "Boom 500 Index", "Boom 50 Index"]},

               {"category": "forex", "symbols": ["EURUSD", "AUDJPY"]}]

    for profile, base in (("SYNTHETICS", rd.PRUNED_INSTRUMENTS_INFO), ("FOREX", rd.FOREX_PRUNED_INFO), ("ICT", rd.ICT_PRUNED_INFO)):

        assert rd.DEFAULT_PRIORITIZED_SYMBOLS[profile] == list(ict_active_symbols(profile))

        info = rd._ict_preventive_prune_info(profile, catalog, base)

        assert not set(info) & set(ict_active_symbols(profile))

        assert all(v.startswith(PREVENTIVE_PRUNE_LABEL) for v in info.values())

    assert "ETHUSD" in rd._ict_preventive_prune_info("ICT", catalog, rd.ICT_PRUNED_INFO)

    syn = rd._ict_preventive_prune_info("SYNTHETICS", catalog, rd.PRUNED_INSTRUMENTS_INFO)

    assert "Crash 1000 Index" in syn and "Boom 50 Index" in syn and "AUDCAD" not in syn





def test_dashboard_save_never_persists_preventive_prune():

    from dashboard.realtime_dashboard import RealtimeDashboardService

    svc = RealtimeDashboardService(repository=None)

    svc._state["instrument_catalog"] = [{"category": "ict_metals_xauusd", "symbols": ["XAUUSD"]},

                                        {"category": "ict_crypto_btcusd", "symbols": ["ETHUSD"]}]

    svc._persist_state_locked = lambda: None

    out = svc.update_selected_symbols(["XAUUSD", "ETHUSD"], selection_profile="ICT")

    assert out["ok"] and out["selected_symbols"] == ["XAUUSD"]

    assert "PODA PREVENTIVA" in out["message"] and "ETHUSD" in out["message"]





def test_instruments_page_labels_and_locks_preventive_prune():

    from dashboard import realtime_dashboard as rd

    html = rd._INSTRUMENTS_HTML

    assert "⚠️ PODA PREVENTIVA" in html and "✓ ICT Activo · " in html

    assert 'disabled data-locked="true"' in html

    for stale in ("ICT Sintético Activo (Sin Poda)", "ICT #1 Boom (+83.1R", "ICT Tier A · Cripto"):

        assert stale not in html





def test_apply_tool_persists_policy(tmp_path):

    from database.repository import TradingRepository

    from tools.apply_ict_instrument_policy import apply_changes, plan_changes

    repo = TradingRepository(tmp_path / "sel.sqlite")

    repo.save_instrument_selection_profile(["XAUUSD", "ETHUSD", "XAGUSD"], selection_profile="ICT", source="DEMO")

    changes = plan_changes(repo)

    ict = next(c for c in changes if c["source"] == "DEMO" and c["profile"] == "ICT")

    assert ict["removed_preventive_prune"] == ["ETHUSD", "XAGUSD"] and "microXAUUSD" in ict["added"]

    apply_changes(repo, changes)

    for profile in ("SYNTHETICS", "FOREX", "ICT"):

        saved = repo.latest_instrument_selection_profile(profile, source="DEMO")["selected_symbols"]

        assert sorted(saved) == sorted(ict_active_symbols(profile))





# ---------------------------------------------------------------- Malaysian SNR (misma política única)

def test_msnr_active_is_synthetics_without_wr45_prune():

    from config.ict_instrument_policy import MSNR_ACTIVE, MSNR_SYNTHETIC_UNIVERSE

    from config.strategy_config import MSNR_WR45_PRUNED

    from config.synth_wr45 import REAL_SPREAD_PRUNED

    assert len(MSNR_SYNTHETIC_UNIVERSE) == 38 and len(MSNR_ACTIVE) == 31 - len(REAL_SPREAD_PRUNED)

    from config.ict_instrument_policy import MSNR_ACIERTO47_SYNTHETICS, MSNR_REAL_MARKET_SYMBOLS

    # Malaysian SNR (05-nov-2026): 38 sintéticos con acierto > 50 % y R > 0 en el replay fiel de 212 pares.

    assert len(MSNR_ACIERTO47_SYNTHETICS) == 38 and set(MSNR_ACIERTO47_SYNTHETICS) <= set(MSNR_SYNTHETIC_UNIVERSE)

    from config.ict_instrument_policy import MALAYSIAN_SNR_ACTIVE

    assert set(ict_active_symbols("MALAYSIAN_SNR")) == set(MALAYSIAN_SNR_ACTIVE)

    assert {"Jump 25 Index", "Boom 300 Index", "Volatility 25 Index"} <= set(MSNR_ACTIVE)  # Fase 1 ICT no aplica a MSNR





def test_msnr_universe_matches_bot_profile():

    from app.main import BOT_PROFILES

    from config.ict_instrument_policy import MALAYSIAN_SNR_ACTIVE

    assert set(BOT_PROFILES["MALAYSIAN_SNR"]["symbols"]) == set(MALAYSIAN_SNR_ACTIVE)





def test_msnr_prune_reasons_and_sanitize():

    assert preventive_prune_reason("Jump 25 Index", "MALAYSIAN_SNR") == ""

    assert preventive_prune_reason("Boom 1000 Index", "MALAYSIAN_SNR") == ""

    assert preventive_prune_reason("Crash 500 Index", "MALAYSIAN_SNR") == ""

    assert ("acierto <= 51" in preventive_prune_reason("AUDNZD", "MALAYSIAN_SNR") or "acierto <= 47" in preventive_prune_reason("AUDNZD", "MALAYSIAN_SNR"))

    assert sanitize_ict_selection("MALAYSIAN_SNR", ["AUDNZD", "XAGUSD", "Boom 500 Index"]) == ["Boom 500 Index"]





def test_dashboard_msnr_tab_uses_policy():

    from dashboard import realtime_dashboard as rd

    assert rd.DEFAULT_PRIORITIZED_SYMBOLS["MALAYSIAN_SNR"] == list(ict_active_symbols("MALAYSIAN_SNR"))

    info = rd._ict_preventive_prune_info("MALAYSIAN_SNR", [], rd.MALAYSIAN_SNR_PRUNED_INFO)

    assert {"AUDNZD", "XAGUSD", "GBPNZD"} <= set(info)

    assert "EURUSD" not in info  # EURUSD tiene 63.41% WR y +6.06R en el replay fiel 212 pares -> ACTIVO

    assert not set(info) & set(ict_active_symbols("MALAYSIAN_SNR"))

    html = rd._INSTRUMENTS_HTML

    assert "✓ MSNR Activo · " in html and "MSNR Canónico Activo" not in html and "MSNR Tier S" not in html





def test_apply_tool_aligns_msnr_asset_modes(tmp_path):

    from database.repository import TradingRepository

    from tools.apply_ict_instrument_policy import apply_changes, msnr_asset_modes, plan_changes

    assert msnr_asset_modes({"AUDNZD": "live", "Jump 25 Index": "off"}, ["Jump 25 Index", "VolSwitch High Vol Index", "NonCatalogSymbol"],

                            ["Boom 1000 Index", "Volatility 90 (1s) Index"]) == {

        "AUDNZD": "off", "Jump 25 Index": "live", "VolSwitch High Vol Index": "live", "Boom 1000 Index": "off", "Volatility 90 (1s) Index": "off"}  # NonCatalogSymbol fuera del catálogo MSNR: sin modo

    repo = TradingRepository(tmp_path / "msnr.sqlite")

    repo.save_instrument_selection_profile(["AUDNZD", "XAGUSD", "Boom 500 Index"],

                                           selection_profile="MALAYSIAN_SNR", source="DEMO")

    apply_changes(repo, plan_changes(repo))

    saved = repo.latest_instrument_selection_profile("MALAYSIAN_SNR", source="DEMO")["selected_symbols"]

    assert sorted(saved) == sorted(ict_active_symbols("MALAYSIAN_SNR"))

    modes = repo.latest_msnr_runtime_settings(source="DEMO")["asset_modes"]

    assert modes["AUDNZD"] == "off" and modes["XAGUSD"] == "off" and modes["Boom 500 Index"] == "live"





def test_dashboard_msnr_save_syncs_asset_modes_even_with_non_catalog_symbols():

    from dashboard.realtime_dashboard import RealtimeDashboardService

    saved = {}



    class Repo:

        def save_instrument_selection_profile(self, symbols, selection_profile, source):

            saved["sel"] = list(symbols); return {"version": 1}

        def latest_instrument_selection_profile(self, profile, source="DEMO"):

            return {"selected_symbols": saved.get("sel")}

        def latest_msnr_runtime_settings(self, source="DEMO"):

            return {"asset_modes": {"AUDNZD": "live"}}

        def save_msnr_runtime_settings(self, source="DEMO", **kw):

            from strategy.malaysian_snr.runtime_settings import CATALOG_SYMBOLS

            assert set(kw["asset_modes"]) <= set(CATALOG_SYMBOLS)  # si no, la validación real fallaría

            saved["modes"] = kw["asset_modes"]



    svc = RealtimeDashboardService(repository=Repo())

    svc._persist_state_locked = lambda: None

    svc._state["instrument_catalog"] = [{"category": "malaysian_snr_boom", "symbols": ["Boom 500 Index", "VolSwitch High Vol Index"]},

                                        {"category": "malaysian_snr_pruned", "symbols": ["AUDNZD", "Volatility 90 (1s) Index"]}]

    out = svc.update_selected_symbols(["Boom 500 Index", "VolSwitch High Vol Index", "AUDNZD"], selection_profile="MALAYSIAN_SNR")

    assert out["ok"] and out["selected_symbols"] == ["Boom 500 Index", "VolSwitch High Vol Index"]

    assert saved["modes"]["AUDNZD"] == "off" and saved["modes"]["Boom 500 Index"] == "live"





def test_volswitch_high_vol_pruned_by_real_spread_in_ict_and_msnr():

    """23-oct-2026: spread real ~4,3× el de las velas; supera siempre el tope 2 % (0 operaciones posibles)."""

    from config.ict_instrument_policy import MSNR_ACTIVE, ict_active_symbols, preventive_prune_reason

    from config.synth_wr45 import ICT_WR45_PRUNED, MSNR_WR45_PRUNED, REAL_SPREAD_PRUNED

    sym = "VolSwitch High Vol Index"

    assert REAL_SPREAD_PRUNED == (sym,) and sym in ICT_WR45_PRUNED and sym in MSNR_WR45_PRUNED

    # Rescatado en SYNTHETICS y MALAYSIAN_SNR por decisión del usuario (WR = 61.1 % con Criterio Humano):

    for profile in ("SYNTHETICS", "MALAYSIAN_SNR"):

        assert sym in ict_active_symbols(profile), f"{sym} debe estar activo en {profile}"

        assert preventive_prune_reason(sym, profile) == "", f"{sym} no debe tener poda en {profile}"

    assert sym not in MSNR_ACTIVE





def test_real_spread_prune_switch_by_env():

    import os, subprocess, sys

    code = "from config.synth_wr45 import REAL_SPREAD_PRUNED; print(REAL_SPREAD_PRUNED)"

    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,

                         env={**os.environ, "DAEMONBLACKFX_REAL_SPREAD_PRUNE": "0"}, cwd=os.getcwd())

    assert out.stdout.strip() == "()", out.stderr





def test_worker_consolidation_active_vs_pruned_and_selective_activation():

    from config.ict_instrument_policy import (

        ICT_FOREX_ACTIVE,

        ICT_FOREX_PRUNED_SYMBOLS,

        ICT_VOLATILITY_ACTIVE_SYMBOLS,

        ICT_VOLATILITY_PRUNED_SYMBOLS,

        resolve_active_pruned_worker_universe,

    )

    assert len(ICT_VOLATILITY_ACTIVE_SYMBOLS) == 19

    assert len(ICT_VOLATILITY_PRUNED_SYMBOLS) == 2

    assert set(resolve_active_pruned_worker_universe("VOLATILITY_1")) == set(ICT_VOLATILITY_ACTIVE_SYMBOLS)

    assert set(resolve_active_pruned_worker_universe("VOLATILITY_2")) == set(ICT_VOLATILITY_PRUNED_SYMBOLS)

    assert resolve_active_pruned_worker_universe("VOLATILITY_3") == []

    assert resolve_active_pruned_worker_universe("VOLATILITY_4") == []



    assert len(ICT_FOREX_ACTIVE) == 16

    assert len(ICT_FOREX_PRUNED_SYMBOLS) == 26

    assert set(resolve_active_pruned_worker_universe("FOREX_1")) == set(ICT_FOREX_ACTIVE)

    assert set(resolve_active_pruned_worker_universe("FOREX_2")) == set(ICT_FOREX_PRUNED_SYMBOLS)

    assert resolve_active_pruned_worker_universe("FOREX_3") == []

    assert resolve_active_pruned_worker_universe("FOREX_4") == []



    assert sanitize_ict_selection("FOREX", ["GBPUSD", "EURUSD"], allow_selective=False) == ["GBPUSD"]

    assert sanitize_ict_selection("FOREX", ["GBPUSD", "EURUSD"], allow_selective=True) == ["GBPUSD", "EURUSD"]

    assert sanitize_ict_selection("SYNTHETICS", ["Volatility 10 Index", "Crash 300 Index"], allow_selective=True) == [

        "Volatility 10 Index",

        "Crash 300 Index",

    ]

    assert sanitize_ict_selection("ICT", ["XAUUSD", "US SP 500"], allow_selective=True) == ["XAUUSD", "US SP 500"]



