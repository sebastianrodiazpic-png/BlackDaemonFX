# -*- coding: utf-8 -*-
"""Tests de validación unitaria para la MultiStrategia en Worker STEP (2) (Large & Base Steps).

Verifica:
1. Catálogo unificado de los 5 Step Index asignados a Worker STEP (2) (Step Index, 300, 1000, 1500, 2000).
2. Resolución de universo en resolve_active_pruned_worker_universe("STEP_2").
3. Configuración del Worker STEP_2 (Magic 26082406) con MultiStrategia (MSNR + ICT en H1_PRIMARY con M5 trigger).
4. Registro de metadatos de Worker STEP_2 en _WORKER_PROFILE_META.
5. Unificación frontend en /Instruments con card dedicado y badge STEP (LARGE & BASE MULTI).
6. Alimentación en /Strategy-bases de los 5 registros como activos (+280,790.00 USD).
7. Perfil en BOT_PROFILES con Magic 26082406.
"""

import json
import re
import pytest

from app.main import BOT_PROFILES
from config.strategy_config import PRUNED_ASSET_UNIVERSE
from config.ict_instrument_policy import resolve_active_pruned_worker_universe
from strategy.execution.live_trading_engine import LiveTradingConfig
from strategy.execution.worker_rules import configure_worker_rules
from dashboard.realtime_dashboard import _WORKER_PROFILE_META


def test_step_2_universe_contains_all_five_instruments():
    syms = PRUNED_ASSET_UNIVERSE.get("STEP_2", ())
    expected = {
        "Step Index", "Step Index 300", "Step Index 1000",
        "Step Index 1500", "Step Index 2000",
    }
    assert set(syms) == expected, f"Se esperaban {expected}, obtenidos: {set(syms)}"


def test_resolve_active_pruned_worker_universe_step_2():
    resolved = resolve_active_pruned_worker_universe("STEP_2")
    expected = {
        "Step Index", "Step Index 300", "Step Index 1000",
        "Step Index 1500", "Step Index 2000",
    }
    assert set(resolved) == expected, f"resolve_active_pruned_worker_universe falló: {set(resolved)}"


def test_worker_rules_step_2_enables_multistrategy():
    cfg = LiveTradingConfig(bot_profile="STEP_2", magic=26082406, execution_enabled=False)
    configured = configure_worker_rules(cfg)
    assert getattr(configured, "malaysian_snr_enabled", False) is True
    assert getattr(configured, "first_target_rr", 0.0) == 1.0
    assert getattr(configured, "second_target_rr", 0.0) == 2.0
    assert getattr(configured, "break_even_enabled", False) is True
    assert getattr(configured, "entry_timeframe", "") == "M5"
    assert getattr(configured, "dual_m5_m1_trigger_enabled", False) is True


def test_dashboard_step_2_worker_cataloged_as_multistrategy():
    meta = _WORKER_PROFILE_META.get("STEP_2")
    assert meta is not None, "STEP_2 no encontrado en _WORKER_PROFILE_META"
    assert meta.get("strategy_label") == "MultiStrategia"
    assert meta.get("strategy_key") == "MULTISTRATEGY"
    assert meta.get("magic") == 26082406
    label = meta.get("label", "")
    assert "STEP (2)" in label
    assert "26082406" in label


def test_dashboard_frontend_step_2_card_and_badges():
    with open("dashboard/realtime_dashboard.py", "r", encoding="utf-8") as f:
        code = f.read()

    # Tarjeta dedicada en Pestaña SYNTHETICS
    assert "worker_step_2" in code
    assert "Worker STEP (2) (MultiStrategia · Magic 26082406 · Large & Base Steps)" in code

    # Badge asignado en workerForInstrument
    assert "STEP (LARGE & BASE MULTI)" in code


def test_strategy_bases_has_all_five_step_2_indices():
    with open("dashboard/strategy_bases_page.py", "r", encoding="utf-8") as f:
        text = f.read()
    m = re.search(r"const\s+WINNERS_DATA\s*=\s*(\[.*?\]);", text, re.DOTALL)
    assert m is not None, "WINNERS_DATA not found"
    winners = json.loads(m.group(1))

    step2_items = {
        w["symbol"]: w for w in winners
        if w.get("strategy") == "MultiStrategia" and "26082406" in w.get("category", "")
    }
    expected = {
        "Step Index", "Step Index 300", "Step Index 1000",
        "Step Index 1500", "Step Index 2000",
    }
    assert expected.issubset(set(step2_items.keys())), f"Faltan símbolos en STEP_2: {expected - set(step2_items.keys())}"
    for sym in expected:
        assert step2_items[sym]["is_profitable"] is True
        assert step2_items[sym]["trades"] > 1000


def test_bot_profiles_has_step_2():
    spec = BOT_PROFILES.get("STEP_2")
    assert spec is not None
    assert spec.get("magic") == 26082406
    assert spec.get("mode") == "step-2-daemon"
    assert "step" in spec.get("categories", [])
