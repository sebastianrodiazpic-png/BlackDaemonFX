from __future__ import annotations

import pytest
from dashboard.realtime_dashboard import _build_confluence_matrix


def test_synthetic_and_forex_workers_classified_as_ict_in_sentinel_matrix():
    """Verifica que los workers sintéticos y forex se clasifiquen como Estrategia ICT en Centinela."""
    state = {
        "selection_profiles": {
            "ICT": ["BTCUSD", "XAUUSD"],
            "SYNTHETICS": ["Boom 600 Index", "Crash 600 Index", "Step Index 500", "Volatility 75 Index"],
            "FOREX": ["EURUSD", "GBPUSD"],
        },
        "worker_candidates": {
            "BOOM": {
                "symbol": "Boom 600 Index",
                "action": "ANALYZANDO",
                "reason": "NO_JUDAS_SWING_MANIPULATION_CONFIRMED",
            },
            "CRASH": {
                "symbol": "Crash 600 Index",
                "action": "WAITING_ICT",
                "reason": "NO_MACRO_H4_BIAS_ALIGNED",
            },
            "STEP": {
                "symbol": "Step Index 500",
                "action": "EVENT_SCHEDULER_WAIT",
                "reason": "WAITING_NEW_M1_BAR",
            },
            "VOLATILITY_1": {
                "symbol": "Volatility 75 Index",
                "action": "EVENT_SCHEDULER_WAIT",
                "reason": "WAITING_NEW_M1_BAR",
            },
            "FOREX_1": {
                "symbol": "EURUSD",
                "action": "WAITING_ICT",
                "reason": "OUTSIDE_INSTITUTIONAL_KILLZONE",
            },
            "ICT": {
                "symbol": "BTCUSD",
                "action": "WAITING_ICT",
                "reason": "NO_SETUP_CONFIRMED",
            },
        },
        "recent": [],
    }

    matrix = _build_confluence_matrix(state)

    # Filtrar filas de Estrategia ICT
    ict_rows = [m for m in matrix if m["strategy_key"] == "ICT"]
    assert len(ict_rows) >= 8

    # Verificar que todos tienen el nombre unificado "Estrategia ICT" y badge "strat-cyan"
    for row in ict_rows:
        assert row["strategy"] == "Estrategia ICT"
        assert row["strat_badge"] == "strat-cyan"

    # Verificar cada instrumento clave
    symbols_in_ict = {m["symbol"]: m for m in ict_rows}

    # Boom
    assert "Boom 600 Index" in symbols_in_ict
    boom_row = symbols_in_ict["Boom 600 Index"]
    assert "Judas Swing" in boom_row["trigger_confirmation"]
    assert "24/7" in boom_row["macro_context"]

    # Crash
    assert "Crash 600 Index" in symbols_in_ict
    crash_row = symbols_in_ict["Crash 600 Index"]
    assert "EMA 50/200" in crash_row["structure_level"]
    assert "Sin Sesgo H4" in crash_row["trigger_confirmation"]

    # Step
    assert "Step Index 500" in symbols_in_ict

    # Volatility
    assert "Volatility 75 Index" in symbols_in_ict

    # Forex
    assert "EURUSD" in symbols_in_ict
    eur_row = symbols_in_ict["EURUSD"]
    assert "Killzone" in eur_row["macro_context"]

    # ICT nativo
    assert "BTCUSD" in symbols_in_ict


def test_legacy_smc_preserved_only_if_explicit():
    """Verifica que el modo legado SMC solo se active si se pide explícitamente en el test sin indicios ICT."""
    state = {
        "worker_candidates": {
            "STEP": {
                "symbol": "Step Index 500",
                "strategy_name": "SMC",
                "action": "NO_M5_CONFIRMATION",
                "reason": "NO_DIRECTIONAL_M5_CONFIRMATION",
                "sequence": {"m15_setups_total": 1, "m5_confirmations_total": 0},
                "h1_context": {"valid": True, "reason": "H1_LOCATION_READY", "trend": "BEARISH"},
            }
        },
        "recent": [],
    }
    matrix = _build_confluence_matrix(state)
    assert len(matrix) >= 1
    assert matrix[0]["strategy_key"] == "SMC"
    assert matrix[0]["strategy"] == "SMC"
    assert matrix[0]["strat_badge"] == "strat-smc"
