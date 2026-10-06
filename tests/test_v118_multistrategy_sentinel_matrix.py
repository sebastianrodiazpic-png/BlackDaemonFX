from __future__ import annotations

import json
from dashboard.realtime_dashboard import _build_confluence_matrix


def test_build_confluence_matrix_empty_fallback():
    state = {"worker_candidates": {}, "recent": []}
    matrix = _build_confluence_matrix(state)
    assert len(matrix) >= 4
    strats = {m["strategy_key"] for m in matrix}
    assert "SMC" in strats
    assert "MALAYSIAN_SNR" in strats
    assert "ORB" in strats
    assert "GOLD_QUARTERS" in strats


def test_build_confluence_matrix_multistrategy_dedup_and_active():
    state = {
        "worker_candidates": {
            "MALAYSIAN_SNR": {
                "symbol": "Step Index 500",
                "strategy_name": "MALAYSIAN_SNR",
                "action": "BLOCKED_ACTIVE_TRADE",
                "reason": "Posicion activa: esperando cierre TP/SL/BE. Tickets [12345]",
                "direction": "SELL",
            },
            "STEP": {
                "symbol": "Step Index 500",
                "strategy_name": "SMC",
                "action": "NO_M5_CONFIRMATION",
                "reason": "NO_DIRECTIONAL_M5_CONFIRMATION",
                "sequence": {"m15_setups_total": 1, "m5_confirmations_total": 0},
                "h1_context": {"valid": True, "reason": "H1_LOCATION_READY", "trend": "BEARISH"},
            },
            "ORB": {
                "symbol": "US Tech 100",
                "strategy_name": "NEW_YORK_ORB",
                "action": "WAITING_NEW_YORK_OPEN",
                "reason": "WAITING_FOR_0930_NY_OPEN",
            },
            "GOLD": {
                "symbol": "XAUUSD",
                "strategy_name": "GOLD_QUARTERS",
                "action": "ORDER_OPENED",
                "reason": "QUARTER_CONFIRMED",
            },
        },
        "recent": [],
    }

    matrix = _build_confluence_matrix(state)

    # Ambos registros para "Step Index 500" deben coexistir (uno para Malaysian SNR y otro para SMC)
    step_rows = [m for m in matrix if m["symbol"] == "Step Index 500"]
    assert len(step_rows) == 2

    snr_row = next(m for m in step_rows if m["strategy_key"] == "MALAYSIAN_SNR")
    assert snr_row["final_state"] == "🔵 POSICION ACTIVA"
    assert snr_row["badge_class"] == "active"
    assert "Gestión" in snr_row["structure_level"]

    smc_row = next(m for m in step_rows if m["strategy_key"] == "SMC")
    assert smc_row["final_state"] == "⚪ NO CONFIRMO M5"
    assert "Setup M15 OK" in smc_row["structure_level"]
    assert "Falló Filtro M5" in smc_row["trigger_confirmation"]

    orb_row = next(m for m in matrix if m["symbol"] == "US Tech 100")
    assert orb_row["strategy_key"] == "ORB"
    assert "Fuera de Sesión" in orb_row["macro_context"] or "Esperando" in orb_row["final_state"]

    gold_row = next(m for m in matrix if m["symbol"] == "XAUUSD")
    assert gold_row["strategy_key"] == "GOLD_QUARTERS"
    assert gold_row["final_state"] == "🟢 SEÑAL LISTA"


def test_build_confluence_matrix_backward_compatibility():
    state = {
        "worker_candidates": {},
        "recent": [
            {
                "symbol": "Boom 1000 Index",
                "bot_profile": "BOOM",
                "strategy_name": "SMC",
                "action": "DIRECTION_POLICY_BLOCKED",
                "reason": "BOOM_BUY_ONLY_REQUIRES_BUY_H1_CONTEXT",
            }
        ],
    }
    matrix = _build_confluence_matrix(state)
    assert len(matrix) >= 1
    row = matrix[0]
    # Comprobar claves nuevas
    assert "strategy" in row
    assert "macro_context" in row
    assert "structure_level" in row
    assert "trigger_confirmation" in row
    # Comprobar claves heredadas
    assert "h1_context" in row
    assert "m15_structure" in row
    assert "m5_confirmation" in row
    assert "m5_freshness" in row
    assert row["final_state"] == "⚪ FILTRADO H1"
