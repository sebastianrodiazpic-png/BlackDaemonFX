from __future__ import annotations

from config.strategy_config import (
    PRUNED_ASSET_UNIVERSE,
    TRI_MOTOR_ORCHESTRATION_CONFIG,
    TRI_MOTOR_TIER_A_ASSETS,
    TRI_MOTOR_TIER_S_ASSETS,
)
from dashboard.realtime_dashboard import (
    DEFAULT_PRIORITIZED_SYMBOLS,
    FOREX_PRUNED_INFO,
    ICT_PRUNED_INFO,
    MALAYSIAN_SNR_PRUNED_INFO,
    ORB_PRUNED_INFO,
    PRUNED_INSTRUMENTS_INFO,
    RealtimeDashboardService,
    _INSTRUMENTS_HTML,
    _WORKER_PROFILE_META,
    _build_confluence_matrix,
    _enrich_worker_state_with_selection,
)
from strategy.ict.config import ICTSabriMalleConfig
from strategy.malaysian_snr.config import msnr_c2_staging_config
from strategy.malaysian_snr.malaysian_snr_strategy import is_fx_or_metal_symbol
from strategy.orb.asset_rules import ASSET_CONFIG, ORB_PROFITABLE_SWEEP_SYMBOLS, ORB_PRUNED_LOSING_SYMBOLS

ICT_PHASE1_EXCLUDED = set(ICTSabriMalleConfig().excluded_symbols)


def test_instruments_tabs_highlight_ict_and_control_all_target_workers():
    """Verifica que /Instruments destaque Estrategia ICT en Sintéticos, Forex e ICT y controle todos los workers."""
    assert 'data-profile="SYNTHETICS"' in _INSTRUMENTS_HTML
    assert 'data-profile="FOREX"' in _INSTRUMENTS_HTML
    assert 'data-profile="ICT"' in _INSTRUMENTS_HTML
    assert 'data-profile="MALAYSIAN_SNR"' in _INSTRUMENTS_HTML
    assert "ESTRATEGIA ICT (SABRI MALLE" in _INSTRUMENTS_HTML
    assert "Malaysian SNR (M15 Fresh/Break)" in _INSTRUMENTS_HTML
    assert "VOLATILITY (1-4)" in _INSTRUMENTS_HTML
    assert "FOREX (1-4)" in _INSTRUMENTS_HTML

    # Verificar el mapeo exacto de workers a pestañas de /Instruments
    expected_mapping = {
        "CRASH": "SYNTHETICS",
        "BOOM": "SYNTHETICS",
        "STEP": "SYNTHETICS",
        "JUMP": "SYNTHETICS",
        "VOLATILITY_1": "SYNTHETICS",
        "VOLATILITY_2": "SYNTHETICS",
        "VOLATILITY_3": "SYNTHETICS",
        "VOLATILITY_4": "SYNTHETICS",
        "FOREX_1": "FOREX",
        "FOREX_2": "FOREX",
        "FOREX_3": "FOREX",
        "FOREX_4": "FOREX",
        "ICT": "ICT",
        "MALAYSIAN_SNR": "MALAYSIAN_SNR",
        "ORB": "ORB",
    }
    for worker_prof, tab_prof in expected_mapping.items():
        assert worker_prof in _WORKER_PROFILE_META
        assert _WORKER_PROFILE_META[worker_prof]["selection_profile"] == tab_prof
        if tab_prof in ("SYNTHETICS", "FOREX", "ICT"):
            assert _WORKER_PROFILE_META[worker_prof]["strategy_key"] == "ICT"

    assert _WORKER_PROFILE_META["MALAYSIAN_SNR"]["label"] == "Malaysian SNR (M15 Fresh/Break)"


def test_malaysian_snr_and_ict_parallel_worker_progress_reflects_active_and_pruned():
    """Verifica que el progreso de Malaysian SNR e ICT refleje en paralelo los activos y deje podados desactivados."""
    msnr_selected = list(DEFAULT_PRIORITIZED_SYMBOLS["MALAYSIAN_SNR"])
    assert len(msnr_selected) == len(__import__('config.ict_instrument_policy', fromlist=['x']).MALAYSIAN_SNR_ACTIVE)  # sintéticos con acierto > 47 % + mercados reales en prueba demo

    state = {
        "selection_profiles": {
            "MALAYSIAN_SNR": msnr_selected,
            "SYNTHETICS": ["Boom 300 Index", "Boom 500 Index", "Boom 900 Index"],
        },
        "selection_profile_versions": {
            "MALAYSIAN_SNR": 2,
            "SYNTHETICS": 2,
        },
    }

    msnr_worker = _enrich_worker_state_with_selection(
        {
            "bot_profile": "MALAYSIAN_SNR",
            "status": "RUNNING",
            "symbols_total": 60,
            "symbols_processed": 12,
            "current_symbol": "Step Index 400",
        },
        state,
    )
    assert msnr_worker["worker_label"] == "Malaysian SNR (M15 Fresh/Break)"
    assert msnr_worker["symbols_total"] == len(__import__('config.ict_instrument_policy', fromlist=['x']).MALAYSIAN_SNR_ACTIVE)
    assert msnr_worker["symbols_processed"] == 12
    assert msnr_worker["active_symbols_count"] == len(__import__('config.ict_instrument_policy', fromlist=['x']).MALAYSIAN_SNR_ACTIVE)
    # Antes 39 podados (mercados reales + 7 sintéticos con acierto <= 45 % + poda por spread real); 4 de los 5 mercados
    # reales en prueba demo del 25-oct-2026 salen de la lista (Germany 40 no estaba).
    real = set(__import__('config.ict_instrument_policy', fromlist=['x']).MSNR_REAL_MARKET_SYMBOLS)
    assert not real & set(msnr_worker["pruned_symbols"])
    # 05-nov-2026 (acierto > 50 % en replay 212 pares): 60 activos y 13 podados en el catálogo MSNR (12 reales <=50% WR + DEX 1500 UP).
    assert msnr_worker["pruned_symbols_count"] == len(MALAYSIAN_SNR_PRUNED_INFO)
    from config.ict_instrument_policy import MALAYSIAN_SNR_ACTIVE, MALAYSIAN_SNR_EXCLUDED
    assert not set(MALAYSIAN_SNR_ACTIVE) & set(msnr_worker["pruned_symbols"])
    assert "Step Index 400" in msnr_worker["active_symbols"]
    assert "Volatility 10 Index" in msnr_worker["active_symbols"]
    assert "XAGUSD" in msnr_worker["pruned_symbols"]
    assert "XAUUSD" in msnr_worker["active_symbols"]

    boom_worker = _enrich_worker_state_with_selection(
        {
            "bot_profile": "BOOM",
            "status": "RUNNING",
            "symbols_total": 10,
            "symbols_processed": 5,
            "current_symbol": "Boom 300 Index",
        },
        state,
    )
    assert boom_worker["selection_profile"] == "SYNTHETICS"
    assert boom_worker["strategy_key"] == "ICT"
    assert boom_worker["symbols_total"] == 3
    assert boom_worker["symbols_processed"] == 3  # acotado a los 3 seleccionados
    assert boom_worker["active_symbols"] == ["Boom 300 Index", "Boom 500 Index", "Boom 900 Index"]
    assert "Boom 50 Index" in boom_worker["pruned_symbols"]


def test_sentinel_and_recent_consistency_with_instruments_selection():
    """Verifica que Modo Centinela y Modo Análisis Recientes sean 100% consistentes con /Instruments."""
    svc = RealtimeDashboardService(repository=None)
    with svc._lock:
        svc._state["selection_profiles"] = {
            "SYNTHETICS": ["Boom 500 Index"],
            "FOREX": ["EURUSD"],
            "ICT": ["XAUUSD"],
            "MALAYSIAN_SNR": ["Step Index 400"],
            "ORB": ["XAUUSD"],
            "GOLD": ["XAUUSD"],
        }
        svc._state["selection_profile_versions"] = {
            "SYNTHETICS": 1,
            "FOREX": 1,
            "ICT": 1,
            "MALAYSIAN_SNR": 1,
            "ORB": 1,
            "GOLD": 1,
        }
        svc._state["selection_version"] = 1
        svc._recent.clear()
        svc._recent.append({
            "symbol": "Boom 500 Index",
            "bot_profile": "BOOM",
            "action": "WAITING_ICT",
            "reason": "JUDAS_SWING_READY",
        })
        svc._recent.append({
            "symbol": "Boom 50 Index",  # Podado y NO seleccionado en SYNTHETICS
            "bot_profile": "BOOM",
            "action": "WAITING_ICT",
            "reason": "PRUNED_SHOULD_NOT_SHOW",
        })

    snap = svc.snapshot(force=True)
    recent_symbols = [r["symbol"] for r in snap["recent"]]
    assert "Boom 500 Index" in recent_symbols
    assert "Boom 50 Index" not in recent_symbols

    matrix_symbols = {(m["strategy_key"], m["symbol"]) for m in snap["confluence_matrix"]}
    assert ("ICT", "Boom 500 Index") in matrix_symbols
    assert ("ICT", "EURUSD") in matrix_symbols
    assert ("ICT", "XAUUSD") in matrix_symbols
    assert ("MALAYSIAN_SNR", "Step Index 400") in matrix_symbols
    assert ("ICT", "Boom 50 Index") not in matrix_symbols


def test_tri_motor_4_optimization_steps_configured():
    """Verifica que los Pasos 1, 2, 3 y 4 del plan Tri-Motor estén configurados en código."""
    # Paso 1.1: ICT Sabri Malle (GBDT >= 0.55 + activos ACTIVE)
    ict_cfg = ICTSabriMalleConfig()
    assert ict_cfg.gbdt_min_probability == 0.55
    assert len(ict_cfg.active_22_symbols) >= 22
    assert "US Oil" in DEFAULT_PRIORITIZED_SYMBOLS["ICT"]

    # Paso 1.2: Malaysian SNR C2 (ADX >= 30, ATR <= 1.2 FX/Metals, ATR <= 1.5 Sintéticos & WS30)
    msnr_c2 = msnr_c2_staging_config()
    assert msnr_c2.enable_c2_fx_metals_atr_cap is True
    assert msnr_c2.min_adx == 30.0
    assert msnr_c2.c2_fx_metals_max_sl_atr == 1.2
    assert msnr_c2.c2_default_max_sl_atr == 1.5
    assert is_fx_or_metal_symbol("EURUSD") is True
    assert is_fx_or_metal_symbol("XAGUSD") is True
    assert is_fx_or_metal_symbol("Wall Street 30") is False
    assert is_fx_or_metal_symbol("Step Index 400") is False

    # Paso 1.3: ORB New York 8 activos en SWEEP validados en Replay 5Y; perdedores podados
    assert "XAUUSD" in set(ORB_PROFITABLE_SWEEP_SYMBOLS)
    assert "BTCUSD" in set(ORB_PROFITABLE_SWEEP_SYMBOLS)
    for sym in ("Wall Street 30", "EURUSD", "UK Brent Oil"):
        assert sym in ORB_PRUNED_LOSING_SYMBOLS
        assert sym in ORB_PRUNED_INFO

    # Paso 2 & 3: No-Colisión y Escalonamiento por Tier S / Tier A
    assert TRI_MOTOR_ORCHESTRATION_CONFIG["cap_per_strategy_symbol"] == 1
    assert TRI_MOTOR_ORCHESTRATION_CONFIG["anti_hedge_opposite_direction_guard"] is True
    assert TRI_MOTOR_ORCHESTRATION_CONFIG["tier_s_risk_percent"] == 1.0
    assert TRI_MOTOR_ORCHESTRATION_CONFIG["tier_a_risk_percent"] == 0.5
    assert "Step Index 400" in TRI_MOTOR_TIER_S_ASSETS["MALAYSIAN_SNR"]
    assert {"XAUUSD", "BTCUSD", "USDCAD", "AUDUSD", "GBPUSD", "XAGUSD", "US Oil", "USDCHF"} <= set(TRI_MOTOR_TIER_S_ASSETS["ORB"])


def test_all_14_signaled_forex_pairs_active_and_free_of_pruning_badge():
    """Valida que los 8 pares Forex rentables con WR > 50.0 % y R > 0 (auditoría 212 pares) y sus variantes micro estén activos y los 13 podados en FOREX_PRUNED_INFO."""
    signaled_forex_bases = [
        "GBPUSD",
        "NZDUSD",
        "CHFJPY",
        "EURJPY",
        "EURCHF",
        "USDCHF",
        "GBPJPY",
        "CADCHF",
    ]
    preventive = ["AUDNZD", "USDJPY", "EURAUD", "AUDJPY", "AUDUSD", "USDCAD", "GBPCHF", "EURGBP", "EURUSD", "EURCAD", "AUDCAD", "GBPAUD", "GBPCAD"]
    assert not set(preventive) & set(DEFAULT_PRIORITIZED_SYMBOLS["FOREX"])
    prioritized_forex = set(DEFAULT_PRIORITIZED_SYMBOLS["FOREX"])
    pruned_universe_forex = set(PRUNED_ASSET_UNIVERSE["FOREX"])

    for base in signaled_forex_bases:
        for sym in (base, f"{base}micro"):
            assert sym in prioritized_forex, f"{sym} debe estar en DEFAULT_PRIORITIZED_SYMBOLS['FOREX']"
            assert sym in pruned_universe_forex, f"{sym} debe estar en PRUNED_ASSET_UNIVERSE['FOREX']"
            assert sym not in FOREX_PRUNED_INFO, f"{sym} NO debe aparecer en FOREX_PRUNED_INFO"
            assert sym not in PRUNED_INSTRUMENTS_INFO, f"{sym} NO debe aparecer en PRUNED_INSTRUMENTS_INFO"


def test_all_signaled_synthetics_and_ict_active_and_free_of_pruning_badge():
    """Valida que todos los activos de Sintéticos e ICT señalados estén activos y sin comentario Descartado por Poda."""
    signaled_synthetics = (
        set(PRUNED_ASSET_UNIVERSE["STEP"])
        | set(PRUNED_ASSET_UNIVERSE["JUMP"])
        | set(PRUNED_ASSET_UNIVERSE["VOLATILITY"])
        | set(PRUNED_ASSET_UNIVERSE["BOOM"])
        | set(PRUNED_ASSET_UNIVERSE["CRASH"])
    )
    prioritized_synthetics = set(DEFAULT_PRIORITIZED_SYMBOLS["SYNTHETICS"])
    for sym in signaled_synthetics:
        assert sym in prioritized_synthetics, f"{sym} debe estar en DEFAULT_PRIORITIZED_SYMBOLS['SYNTHETICS']"
        assert sym not in PRUNED_INSTRUMENTS_INFO, f"{sym} NO debe aparecer en PRUNED_INSTRUMENTS_INFO"

    signaled_ict = set(PRUNED_ASSET_UNIVERSE["ICT"])
    prioritized_ict = set(DEFAULT_PRIORITIZED_SYMBOLS["ICT"])
    for sym in signaled_ict:
        assert sym in prioritized_ict, f"{sym} debe estar en DEFAULT_PRIORITIZED_SYMBOLS['ICT']"
        assert sym not in ICT_PRUNED_INFO, f"{sym} NO debe aparecer en ICT_PRUNED_INFO"
        assert sym not in PRUNED_INSTRUMENTS_INFO, f"{sym} NO debe aparecer en PRUNED_INSTRUMENTS_INFO"


def test_selection_lists_aligned_with_phase1_exclusions():
    """Fase 1 + Auditoría 5Y: ninguna lista de selección ICT/ORB contiene activos que la estrategia rechaza en vivo."""
    assert {"XAGUSD", "US SP 500"} <= set(ICT_PHASE1_EXCLUDED)
    ict_lists = {
        **{f"PRUNED_ASSET_UNIVERSE[{k}]": PRUNED_ASSET_UNIVERSE[k]
           for k in ("STEP", "JUMP", "VOLATILITY", "BOOM", "CRASH", "FOREX", "ICT")},
        "TIER_S[ICT]": TRI_MOTOR_TIER_S_ASSETS["ICT"],
        "TIER_A[ICT]": TRI_MOTOR_TIER_A_ASSETS["ICT"],
        "DEFAULT[ICT]": DEFAULT_PRIORITIZED_SYMBOLS["ICT"],
        "DEFAULT[SYNTHETICS]": DEFAULT_PRIORITIZED_SYMBOLS["SYNTHETICS"],
        "DEFAULT[FOREX]": DEFAULT_PRIORITIZED_SYMBOLS["FOREX"],
        "active_22_symbols": ICTSabriMalleConfig().active_22_symbols,
    }
    for name, symbols in ict_lists.items():
        assert not ICT_PHASE1_EXCLUDED & set(symbols), f"{name} contiene excluidos de Fase 1"
    for sym in ("XAGUSD", "US SP 500"):
        assert sym in ICT_PRUNED_INFO
    for sym in ("Crash 1000 Index", "Volatility 90 (1s) Index", "High Frequency Vol 50 Index"):
        assert sym in PRUNED_INSTRUMENTS_INFO

    # MSNR y Sintéticos ICT operan Jump 25 y Volatility 25 rescatados por la auditoría 5Y
    assert {"Jump 25 Index", "Volatility 25 Index"} <= set(DEFAULT_PRIORITIZED_SYMBOLS["SYNTHETICS"])
    assert {"Jump 25 Index", "Volatility 25 Index"} <= set(DEFAULT_PRIORITIZED_SYMBOLS["MALAYSIAN_SNR"])
    assert "XAGUSD" not in DEFAULT_PRIORITIZED_SYMBOLS["MALAYSIAN_SNR"]

    # ORB: 11 activos operan SWEEP/HTF_SWEEP (WR > 50% y R > 0 en Replay 212 pares); selección y tiers coinciden
    tradable = {k for k, v in ASSET_CONFIG.items() if v.get("allowed_modes") or v.get("sweep_enabled")}
    assert tradable == {"XAUUSD", "XAUEUR", "BTCUSD", "ETHUSD", "USDCAD", "AUDUSD", "GBPUSD", "XAGUSD", "USOIL", "USDCHF", "USDJPY"}
    assert {"XAUUSD", "XAUEUR", "BTCUSD", "ETHUSD", "USDCAD", "AUDUSD", "GBPUSD", "XAGUSD", "US Oil", "USDCHF", "USDJPY"} <= set(PRUNED_ASSET_UNIVERSE["ORB"])
    assert {"XAUUSD", "XAUEUR", "BTCUSD", "ETHUSD", "USDCAD", "AUDUSD", "GBPUSD", "XAGUSD", "US Oil", "USDCHF", "USDJPY"} <= set(DEFAULT_PRIORITIZED_SYMBOLS["ORB"])
    assert not set(DEFAULT_PRIORITIZED_SYMBOLS["ORB"]) & set(ORB_PRUNED_INFO)
