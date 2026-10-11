import pytest
from dashboard.realtime_dashboard import (
    _build_confluence_matrix,
    DEFAULT_PRIORITIZED_SYMBOLS,
)
from app.main import BOT_PROFILES, _resolve_universe_for_profile_provider


def test_malaysian_snr_sentinel_matrix_contains_all_23_selected_instruments():
    expected_23 = list(DEFAULT_PRIORITIZED_SYMBOLS["MALAYSIAN_SNR"])
    assert len(expected_23) == 23

    # Estado con las selecciones activas tal como en la DB /instruments
    state = {
        "selection_profiles": {
            "MALAYSIAN_SNR": expected_23,
        },
        "worker_candidates": {
            "MALAYSIAN_SNR": {
                "symbol": "Step Index 400",
                "strategy_name": "MALAYSIAN_SNR",
                "action": "WAITING_MALAYSIAN_SNR",
                "reason": "Esperando retest fresh en M15",
            }
        },
        "recent": [
            {
                "symbol": "XAUUSD",
                "strategy_name": "MALAYSIAN_SNR",
                "bot_profile": "MALAYSIAN_SNR",
                "action": "ORDER_OPENED",
                "reason": "Retest M15 Confirmado",
            }
        ],
    }

    matrix = _build_confluence_matrix(state)

    # Filtrar por estrategia Malaysian SNR
    msnr_rows = [m for m in matrix if m["strategy_key"] == "MALAYSIAN_SNR"]
    symbols_in_matrix = [m["symbol"] for m in msnr_rows]

    # Debe contener exactamente los 23 instrumentos seleccionados
    assert len(msnr_rows) == 23
    for sym in expected_23:
        assert sym in symbols_in_matrix, f"Símbolo {sym} ausente de la Matriz Centinela"

    # Verificar que el candidato preservó su estado
    step_row = next(m for m in msnr_rows if m["symbol"] == "Step Index 400")
    assert step_row["final_state"] == "🟡 ESPERANDO RETEST"

    # Verificar que el evento reciente preservó su estado
    xau_row = next(m for m in msnr_rows if m["symbol"] == "XAUUSD")
    assert xau_row["final_state"] == "🟢 SEÑAL LISTA"

    # Verificar que los no procesados están en espera
    boom_row = next(m for m in msnr_rows if m["symbol"] == "Boom 1000 Index")
    assert boom_row["final_state"] == "⚪ EN ESPERA"
    assert boom_row["macro_context"] == "⚪ Rango / Neutral"


def test_malaysian_snr_universe_includes_pruned_catalog():
    class DummyProvider:
        connector = None

    provider = DummyProvider()
    universe = _resolve_universe_for_profile_provider(provider, "MALAYSIAN_SNR")

    # Universo completo debe contener los 23 rentables + los 37 podados = 60
    assert len(universe) == 60
    assert "Step Index 400" in universe
    assert "USDCAD" in universe  # Podado pero configurable
    assert "Boom 1000 Index" in universe


def test_synthetic_workers_allow_all_active_symbols_configured_in_instruments():
    class MockManager:
        def get_active_symbols(self, categories=None):
            cat = categories[0] if categories else ""
            if cat == "boom":
                return [
                    "Boom 100 Index", "Boom 1000 Index", "Boom 150 Index", "Boom 200 Index",
                    "Boom 300 Index", "Boom 50 Index", "Boom 500 Index", "Boom 600 Index",
                    "Boom 900 Index", "Boom 99 Index"
                ]
            elif cat == "crash":
                return [
                    "Crash 100 Index", "Crash 1000 Index", "Crash 150 Index", "Crash 200 Index",
                    "Crash 300 Index", "Crash 50 Index", "Crash 500 Index", "Crash 600 Index",
                    "Crash 900 Index", "Crash 99 Index"
                ]
            elif cat == "step":
                return ["Step Index", "Step Index 100", "Step Index 200", "Step Index 400", "Step Index 500"]
            elif cat == "jump":
                return ["Jump 10 Index", "Jump 25 Index", "Jump 50 Index", "Jump 75 Index", "Jump 100 Index"]
            elif cat == "volatility":
                return ["Volatility 10 Index", "Volatility 25 Index", "Volatility 50 (1s) Index", "Volatility 75 Index"]
            return []

    class DummyProvider:
        def __init__(self):
            self.connector = None

    import app.main as main_mod
    original_manager = main_mod.InstrumentManager
    main_mod.InstrumentManager = lambda conn: MockManager()
    try:
        p = DummyProvider()
        # Boom debe tener los 10 disponibles
        boom_univ = _resolve_universe_for_profile_provider(p, "BOOM")
        assert len(boom_univ) == 10
        assert "Boom 500 Index" in boom_univ
        assert "Boom 600 Index" in boom_univ
        assert "Boom 300 Index" in boom_univ
        assert "Boom 900 Index" in boom_univ

        # Simular selección en /instruments con 4 activos activos
        selected_in_instruments = {"Boom 300 Index", "Boom 500 Index", "Boom 600 Index", "Boom 900 Index"}
        active_for_worker = [s for s in boom_univ if s in selected_in_instruments]
        assert len(active_for_worker) == 4
        assert active_for_worker == ["Boom 300 Index", "Boom 500 Index", "Boom 600 Index", "Boom 900 Index"]

        # Crash debe incluir Crash 600 Index
        crash_univ = _resolve_universe_for_profile_provider(p, "CRASH")
        assert "Crash 600 Index" in crash_univ
        assert "Crash 500 Index" in crash_univ

        # Step debe incluir Step Index 200
        step_univ = _resolve_universe_for_profile_provider(p, "STEP")
        assert "Step Index 200" in step_univ

        # Jump debe incluir Jump 25 Index
        jump_univ = _resolve_universe_for_profile_provider(p, "JUMP")
        assert "Jump 25 Index" in jump_univ
    finally:
        main_mod.InstrumentManager = original_manager


def test_ict_instruments_appear_in_centinela_matrix():
    ict_symbols = ["XAGUSD", "BTCUSD", "Wall Street 30", "US Tech 100", "Volatility 10 Index"]
    state = {
        "selection_profiles": {
            "ICT": ict_symbols,
        },
        "worker_candidates": {
            "ICT": {
                "symbol": "BTCUSD",
                "strategy_name": "ICT_SABRI_MALLE",
                "action": "ICT_SABRI_MALLE_CONFIRMED",
                "reason": "Judas swing confirmed",
            }
        },
        "recent": [],
    }

    matrix = _build_confluence_matrix(state)

    ict_rows = [m for m in matrix if m["strategy_key"] == "ICT"]
    assert len(ict_rows) == len(ict_symbols)
    symbols_found = [m["symbol"] for m in ict_rows]
    for s in ict_symbols:
        assert s in symbols_found

    btcusd_row = next(m for m in ict_rows if m["symbol"] == "BTCUSD")
    assert btcusd_row["final_state"] == "🟢 SEÑAL LISTA"
    assert btcusd_row["strat_badge"] == "strat-cyan"
    assert btcusd_row["strategy"] == "Estrategia ICT"
    assert "MSS" in btcusd_row["structure_level"]

    waiting_row = next(m for m in ict_rows if m["symbol"] == "Wall Street 30")
    assert waiting_row["final_state"] == "⚪ EN ESPERA"
    assert waiting_row["strat_badge"] == "strat-cyan"

