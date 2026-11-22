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
    assert "ESTRATEGIA ICT" in _INSTRUMENTS_HTML
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
        "FOREX_SNR": "FOREX_SNR",
        "COMMODITIES_SNR": "COMMODITIES_SNR",
        "INDICESB_SNR": "INDICESB_SNR",
        "ORB": "ORB",
    }
    for worker_prof, tab_prof in expected_mapping.items():
        assert worker_prof in _WORKER_PROFILE_META
        assert _WORKER_PROFILE_META[worker_prof]["selection_profile"] == tab_prof
        if tab_prof in ("SYNTHETICS", "FOREX", "ICT"):
            assert _WORKER_PROFILE_META[worker_prof]["strategy_key"] == "ICT"
        if tab_prof in ("MALAYSIAN_SNR", "FOREX_SNR", "COMMODITIES_SNR", "INDICESB_SNR"):
            assert _WORKER_PROFILE_META[worker_prof]["strategy_key"] == "MALAYSIAN_SNR"

    assert _WORKER_PROFILE_META["MALAYSIAN_SNR"]["label"] == "Malaysian SNR (M15 Fresh/Break)"
    assert _WORKER_PROFILE_META["FOREX_SNR"]["label"] == "FOREX_SNR · Forex & Cripto"


def test_malaysian_snr_and_ict_parallel_worker_progress_reflects_active_and_pruned():
    """Verifica que el progreso de Malaysian SNR (38 sintéticos), Forex SNR (44 Forex/Cripto) e ICT refleje en paralelo los activos."""
    msnr_selected = list(DEFAULT_PRIORITIZED_SYMBOLS["MALAYSIAN_SNR"])
    assert len(msnr_selected) == 38
    assert len(msnr_selected) == len(__import__('config.ict_instrument_policy', fromlist=['x']).MALAYSIAN_SNR_ACTIVE)

    fx_snr_selected = list(DEFAULT_PRIORITIZED_SYMBOLS["FOREX_SNR"])
    assert len(fx_snr_selected) == 44

    state = {
        "selection_profiles": {
            "MALAYSIAN_SNR": msnr_selected,
            "FOREX_SNR": fx_snr_selected,
            "SYNTHETICS": ["Boom 300 Index", "Boom 500 Index", "Boom 900 Index"],
        },
        "selection_profile_versions": {
            "MALAYSIAN_SNR": 2,
            "FOREX_SNR": 2,
            "SYNTHETICS": 2,
        },
    }

    msnr_worker = _enrich_worker_state_with_selection(
        {
            "bot_profile": "MALAYSIAN_SNR",
            "status": "RUNNING",
            "symbols_total": 38,
            "symbols_processed": 12,
            "current_symbol": "Step Index 400",
        },
        state,
    )
    assert msnr_worker["worker_label"] == "Malaysian SNR (M15 Fresh/Break)"
    assert msnr_worker["symbols_total"] == 38
    assert msnr_worker["symbols_processed"] == 12
    assert msnr_worker["active_symbols_count"] == 38
    assert msnr_worker["pruned_symbols_count"] == len(MALAYSIAN_SNR_PRUNED_INFO)
    from config.ict_instrument_policy import MALAYSIAN_SNR_ACTIVE
    assert not set(MALAYSIAN_SNR_ACTIVE) & set(msnr_worker["pruned_symbols"])
    assert "Step Index 400" in msnr_worker["active_symbols"]
    assert "Volatility 10 Index" in msnr_worker["active_symbols"]
    assert "EURUSD" not in msnr_worker["active_symbols"]

    fx_snr_worker = _enrich_worker_state_with_selection(
        {
            "bot_profile": "FOREX_SNR",
            "status": "WAITING_NEW_M1_BAR",
            "symbols_total": 0,
            "symbols_processed": 0,
            "current_symbol": None,
        },
        state,
    )
    assert fx_snr_worker["worker_label"] == "FOREX_SNR · Forex & Cripto"
    assert fx_snr_worker["strategy_label"] == "Malaysian SNR (M15 Fresh/Break · C2)"
    assert fx_snr_worker["symbols_total"] == 44
    assert fx_snr_worker["active_symbols_count"] == 44
    assert fx_snr_worker["pruned_symbols_count"] == 0
    assert "EURUSD" in fx_snr_worker["active_symbols"]
    assert "AUDCAD" in fx_snr_worker["active_symbols"]

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
    # Paso 1.1: ICT (GBDT >= 0.55 + activos ACTIVE)
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
    for sym in ("NZDUSD", "US Small Cap 2000", "US Mid Cap 400"):
        assert sym in ORB_PRUNED_INFO
    for sym in ("Wall Street 30", "EURUSD", "UK Brent Oil", "US Tech 100", "US SP 500"):
        assert sym not in ORB_PRUNED_INFO
        assert sym in DEFAULT_PRIORITIZED_SYMBOLS["ORB"]

    # Paso 2 & 3: No-Colisión y Escalonamiento por Tier S / Tier A
    assert TRI_MOTOR_ORCHESTRATION_CONFIG["cap_per_strategy_symbol"] == 1
    assert TRI_MOTOR_ORCHESTRATION_CONFIG["anti_hedge_opposite_direction_guard"] is True
    assert TRI_MOTOR_ORCHESTRATION_CONFIG["tier_s_risk_percent"] == 1.0
    assert TRI_MOTOR_ORCHESTRATION_CONFIG["tier_a_risk_percent"] == 0.5
    assert "Step Index 400" in TRI_MOTOR_TIER_S_ASSETS["MALAYSIAN_SNR"]
    assert {"XAUUSD", "BTCUSD", "USDCAD", "AUDUSD", "GBPUSD", "XAGUSD", "US Oil", "USDCHF"} <= set(TRI_MOTOR_TIER_S_ASSETS["ORB"])


def test_all_14_signaled_forex_pairs_active_and_free_of_pruning_badge():
    """Valida que los 11 pares Forex rentables con WR > 50.0 % y sus variantes micro estén activos y los 10 podados (incluyendo CHFJPY) en FOREX_PRUNED_INFO."""
    signaled_forex_bases = [
        "GBPUSD",
        "NZDUSD",
        "EURJPY",
        "EURCHF",
        "USDCHF",
        "GBPJPY",
        "CADCHF",
        "EURUSD",
        "USDJPY",
        "AUDUSD",
        "USDCAD",
    ]
    preventive = ["AUDNZD", "EURAUD", "AUDJPY", "GBPCHF", "EURGBP", "EURCAD", "AUDCAD", "GBPAUD", "GBPCAD", "CHFJPY"]
    assert not set(preventive) & set(DEFAULT_PRIORITIZED_SYMBOLS["FOREX"])
    prioritized_forex = set(DEFAULT_PRIORITIZED_SYMBOLS["FOREX"])
    pruned_universe_forex = set(PRUNED_ASSET_UNIVERSE["FOREX"])

    for base in signaled_forex_bases:
        for sym in (base, f"{base}micro"):
            assert sym in prioritized_forex, f"{sym} debe estar en DEFAULT_PRIORITIZED_SYMBOLS['FOREX']"
            assert sym in pruned_universe_forex, f"{sym} debe estar en PRUNED_ASSET_UNIVERSE['FOREX']"
            assert sym not in FOREX_PRUNED_INFO, f"{sym} NO debe aparecer en FOREX_PRUNED_INFO"
            assert sym not in PRUNED_INSTRUMENTS_INFO, f"{sym} NO debe aparecer en PRUNED_INSTRUMENTS_INFO"

    for sym in ("CHFJPY", "CHFJPYmicro"):
        assert sym not in prioritized_forex, f"{sym} NO debe estar activo en FOREX"
        assert sym in FOREX_PRUNED_INFO, f"{sym} debe estar en FOREX_PRUNED_INFO"
        assert sym in PRUNED_INSTRUMENTS_INFO, f"{sym} debe estar en PRUNED_INSTRUMENTS_INFO"


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
    """Fase 1 + Auditoría 5Y: XAGUSD y US SP 500 rehabilitados con WR > 50% en Confluencia Tripartita."""
    assert "US SP 500" not in set(ICT_PHASE1_EXCLUDED)
    assert "XAGUSD" not in set(ICT_PHASE1_EXCLUDED)
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
        assert sym not in ICT_PRUNED_INFO
    for sym in ("Crash 1000 Index", "Volatility 90 (1s) Index", "High Frequency Vol 50 Index"):
        assert sym not in PRUNED_INSTRUMENTS_INFO

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


def test_instruments_parallel_worker_panel_hidden_in_all_tabs():
    """Valida que el panel de control de workers y el banner de estrategia permanezcan ocultos en todas las pestañas de /instruments."""
    assert '<div id="strategyHighlightBanner" style="display:none;"></div>' in _INSTRUMENTS_HTML
    assert '<section id="tabWorkerPanel" style="display:none;"></section>' in _INSTRUMENTS_HTML
    assert "banner.style.display = 'none'" in _INSTRUMENTS_HTML
    assert "panel.style.display = 'none'" in _INSTRUMENTS_HTML


def test_instruments_javascript_syntax_valid():
    """Valida que todos los scripts incrustados en /instruments tengan sintaxis JavaScript 100% válida sin errores en Node.js."""
    import re
    import subprocess
    from pathlib import Path

    scripts = re.findall(r"<script>(.*?)</script>", _INSTRUMENTS_HTML, re.DOTALL)
    assert len(scripts) >= 1
    root = Path(__file__).resolve().parents[1]
    for idx, script in enumerate(scripts):
        test_js = root / "storage" / f"test_instruments_syntax_{idx}.js"
        test_js.parent.mkdir(parents=True, exist_ok=True)
        test_js.write_text(script, encoding="utf-8")
        res = subprocess.run(["node", "--check", str(test_js)], capture_output=True, text=True)
        assert res.returncode == 0, f"Script {idx} in /instruments failed JS syntax check: {res.stderr}"


def test_malaysian_snr_audchf_gbpnzd_gbpaud_active_and_pruned_synced_with_strategy_bases():
    """Valida sincronización de Malaysian SNR (38 sintéticos) y Forex SNR (44 Forex/Cripto) con /Strategy-bases."""
    from config.ict_instrument_policy import ict_active_symbols
    from dashboard.realtime_dashboard import FOREX_SNR_PRUNED_INFO
    from strategy.malaysian_snr.config import MalaysianSNRConfig

    msnr_cfg = MalaysianSNRConfig()
    active_msnr = set(ict_active_symbols("MALAYSIAN_SNR"))
    active_fx_snr = set(ict_active_symbols("FOREX_SNR"))

    assert len(active_msnr) == 38
    assert len(active_fx_snr) == 44

    # Activos ganadores Forex deben estar en FOREX_SNR y fuera de MALAYSIAN_SNR (exclusivo sintéticos)
    winners = ["AUDCHF", "AUDCHFmicro", "GBPNZD", "GBPNZDmicro", "GBPAUD", "GBPAUDmicro"]
    for sym in winners:
        assert sym in active_fx_snr, f"{sym} debe estar en ict_active_symbols('FOREX_SNR')"
        assert sym not in active_msnr, f"{sym} NO debe estar en ict_active_symbols('MALAYSIAN_SNR') (exclusivo sintéticos)"
        assert sym not in FOREX_SNR_PRUNED_INFO, f"{sym} NO debe estar en FOREX_SNR_PRUNED_INFO"

    # Activos perdedores Forex en el Replay 5A deben estar excluidos de FOREX_SNR y registrados en FOREX_SNR_PRUNED_INFO
    losers = ["EURCHF", "EURCHFmicro", "GBPCAD", "GBPCADmicro", "AUDNZD", "AUDNZDmicro", "EURNZD", "EURNZDmicro"]
    for sym in losers:
        assert sym not in active_fx_snr, f"{sym} NO debe estar en ict_active_symbols('FOREX_SNR')"
        assert sym in FOREX_SNR_PRUNED_INFO, f"{sym} debe estar registrado en FOREX_SNR_PRUNED_INFO con causa de poda"


def test_instruments_visual_hierarchy_and_clean_badges():
    """Valida la jerarquía visual de /instruments: estilos modernos, badges unificados (✓ ACTIVO / ⛔ PODADO) y etiquetas institucionales."""
    assert ".groupHeader" in _INSTRUMENTS_HTML
    assert ".groupItems" in _INSTRUMENTS_HTML
    assert ".msnrBadge" in _INSTRUMENTS_HTML
    assert ".cardTag" in _INSTRUMENTS_HTML
    assert "✓ ACTIVO" in _INSTRUMENTS_HTML
    assert "⛔ PODADO" in _INSTRUMENTS_HTML
    assert "✓ Seleccionar solo ACTIVOS (excluir PODADOS)" in _INSTRUMENTS_HTML
    assert 'tagIct">ICT</span>' in _INSTRUMENTS_HTML
    assert "Sabri Malle" not in _INSTRUMENTS_HTML


def test_ict_all_rehabilitated_assets_active_and_free_of_pruning():
    """Valida que todos los activos rehabilitados con rentabilidad > 50% estén activos y libres de poda bajo Estrategia ICT."""
    from config.ict_instrument_policy import ict_active_symbols

    # Sintéticos
    active_synths = set(ict_active_symbols("SYNTHETICS"))
    for s in ["Jump 100 Index", "Volatility 90 (1s) Index", "Crash 1000 Index", "High Frequency Vol 50 Index"]:
        assert s in active_synths, f"{s} debe estar activo en SYNTHETICS"
        assert s not in PRUNED_INSTRUMENTS_INFO, f"{s} no debe estar en PRUNED_INSTRUMENTS_INFO"
        assert s not in ICT_PRUNED_INFO, f"{s} no debe estar en ICT_PRUNED_INFO"

    # Forex
    active_forex = set(ict_active_symbols("FOREX"))
    for s in ["EURUSD", "EURUSDmicro", "USDJPY", "USDJPYmicro", "AUDUSD", "AUDUSDmicro", "USDCAD", "USDCADmicro"]:
        assert s in active_forex, f"{s} debe estar activo en FOREX"
        assert s not in FOREX_PRUNED_INFO, f"{s} no debe estar en FOREX_PRUNED_INFO"

    # ICT Metales, Cripto & Índices
    active_ict = set(ict_active_symbols("ICT"))
    for s in ["US SP 500", "UK Brent Oil", "XAGUSD", "XAGUSDmicro", "Germany 40", "ETHUSD", "ETHUSDmicro"]:
        assert s in active_ict, f"{s} debe estar activo en ICT"
        assert s not in ICT_PRUNED_INFO, f"{s} no debe estar en ICT_PRUNED_INFO"


def test_orb_instruments_tab_worker_badge_and_snr_workers_separation():
    """Valida que en /Instruments la pestaña ORB muestre la etiqueta ORB y que los workers SNR estén aislados sin errores."""
    from strategy.malaysian_snr.universe import is_synthetic_symbol
    from config.ict_instrument_policy import ict_active_symbols

    # 1. En /Instruments el helper JS workerForInstrument debe priorizar ORB en la pestaña ORB
    assert "if (prof === 'ORB') return { tag: 'ORB', label: 'Worker ORB', badgeClass: 'wpOrb' };" in _INSTRUMENTS_HTML

    # 2. is_synthetic_symbol debe estar exportada en strategy.malaysian_snr.universe
    assert is_synthetic_symbol("Volatility 75 Index") is True
    assert is_synthetic_symbol("Boom 500 Index") is True
    assert is_synthetic_symbol("EURUSD") is False
    assert is_synthetic_symbol("XAUUSD") is False

    # 3. COMMODITIES_SNR (10) e INDICESB_SNR (4) registrados en ict_active_symbols
    assert len(ict_active_symbols("COMMODITIES_SNR")) == 10
    assert len(ict_active_symbols("INDICESB_SNR")) == 4
    assert len(ict_active_symbols("FOREX_SNR")) in (44, 76)
    assert len(ict_active_symbols("MALAYSIAN_SNR")) in (38, 56)


def test_orb_tab_instruments_worker_assignment_in_dashboard():
    """Valida que en /Instruments la pestaña ORB asigne Worker ORB a metales, petróleo, cripto e índices."""
    from dashboard.realtime_dashboard import RealtimeDashboardService, _INSTRUMENTS_HTML
    srv = RealtimeDashboardService()
    cat = srv._cached_instruments_payload(force=True).get("instrument_catalog", [])
    orb_groups = [g for g in cat if str(g.get("selection_profile")).upper() == "ORB"]
    orb_symbols = set()
    for g in orb_groups:
        orb_symbols.update(g.get("symbols") or [])

    target_symbols = ["XAUEUR", "XAUUSD", "XAGUSD", "UK Brent Oil", "US Oil", "BTCUSD", "ETHUSD", "US SP 500", "US Tech 100", "Wall Street 30"]
    for sym in target_symbols:
        assert sym in orb_symbols, f"{sym} debe pertenecer al catálogo ORB"

    # En JS, la guardia de pestaña ORB debe preceder a la lista estática de commodities
    orb_pos = _INSTRUMENTS_HTML.find("if (prof === 'ORB') return { tag: 'ORB', label: 'Worker ORB', badgeClass: 'wpOrb' };")
    comm_pos = _INSTRUMENTS_HTML.find("const commoditiesCryptoTargets = [")
    assert orb_pos != -1, "La regla de pestaña ORB debe existir en el HTML"
    assert comm_pos != -1, "La lista de commodities debe existir en el HTML"
    assert orb_pos < comm_pos, "La regla de pestaña ORB debe evaluarse ANTES de las heurísticas de commodities"

