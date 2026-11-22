import pytest
from dashboard.operator_chatbot import (
    build_mt5_symbol_candidates,
    is_symbol_match_faithful,
    resolve_price_profile_and_bounds,
    get_symbol_price_profile,
    fetch_cached_market_candles,
    validate_and_sanitize_chart_data,
    build_chart_data_for_symbol,
    process_operator_chat_message,
)


def test_build_mt5_symbol_candidates_step_family():
    """Verifica que cada variante de Step Index tenga sus candidatos exactos y aislados sin cross-contamination."""
    cands_500 = build_mt5_symbol_candidates("Step Index 500")
    assert "Step Index 500" in cands_500
    assert "Step 500" in cands_500
    # Nunca debe incluir Step 400 ni Step 200
    assert not any("400" in c for c in cands_500)
    assert not any("200" in c for c in cands_500)

    cands_400 = build_mt5_symbol_candidates("Step Index 400")
    assert "Step Index 400" in cands_400
    assert not any("500" in c for c in cands_400)

    cands_200 = build_mt5_symbol_candidates("Step Index 200")
    assert "Step Index 200" in cands_200
    assert not any("500" in c for c in cands_200)

    cands_classic = build_mt5_symbol_candidates("Step Index")
    assert "Step Index" in cands_classic
    assert not any(num in c for c in cands_classic for num in ("200", "300", "400", "500"))


def test_is_symbol_match_faithful():
    """Verifica el guardián de fidelidad estricta para emparejamiento de símbolos de broker."""
    # Coincidencias válidas
    assert is_symbol_match_faithful("Step Index 500", "Step Index 500") is True
    assert is_symbol_match_faithful("Step Index 500", "Step 500") is True
    assert is_symbol_match_faithful("Step Index 500", "StepIndex500") is True
    assert is_symbol_match_faithful("Volatility 75 (1s) Index", "Volatility 75 1s Index") is True
    assert is_symbol_match_faithful("XAUUSD", "XAUUSDmicro") is True

    # Coincidencias inválidas / cruzadas (deben ser rechazadas de inmediato)
    assert is_symbol_match_faithful("Step Index 500", "Step Index 400") is False
    assert is_symbol_match_faithful("Step Index 500", "Step Index 200") is False
    assert is_symbol_match_faithful("Step Index 500", "Step Index") is False
    assert is_symbol_match_faithful("Volatility 75 Index", "Volatility 75 (1s) Index") is False
    assert is_symbol_match_faithful("Volatility 75 (1s) Index", "Volatility 75 Index") is False
    assert is_symbol_match_faithful("Boom 1000 Index", "Crash 1000 Index") is False


def test_step_500_price_profile_and_chart_data():
    """Verifica que Step Index 500 reporte una cotización fiel (~3,745 - 3,790) y nunca ~9,198 ni ~11,200."""
    prof_price, atr, digits, (min_b, max_b) = resolve_price_profile_and_bounds("Step Index 500")
    assert 2000.0 <= prof_price <= 6000.0
    assert 3600.0 <= prof_price <= 3900.0
    assert digits == 1

    chart = build_chart_data_for_symbol("Step Index 500", "BUY")
    assert chart["symbol"] == "Step Index 500"
    # El precio actual DEBE estar en torno a ~3,745 - 3,790
    assert 3500.0 <= chart["current_price"] <= 4100.0
    # Nunca debe mostrar 9,198 ni 11,200
    assert abs(chart["current_price"] - 9198.2) > 3000.0
    assert abs(chart["current_price"] - 11200.0) > 4000.0

    # Las velas también deben estar dentro de la escala real
    for c in chart["candles"]:
        assert 3000.0 <= c["close"] <= 4500.0


def test_all_instruments_price_profile_fidelity():
    """Verifica que el catálogo maestro cubra todas las familias con rangos realistas y sin números ficticios."""
    test_cases = [
        ("Step Index 500", 2500.0, 5000.0),
        ("Step Index 400", 6500.0, 11500.0),
        ("Step Index 200", 8500.0, 12500.0),
        ("Step Index", 5500.0, 9500.0),
        ("Boom 300 Index", 250.0, 800.0),
        ("Boom 1000 Index", 12000.0, 20000.0),
        ("Crash 300 Index", 1800.0, 3500.0),
        ("Crash 1000 Index", 4500.0, 8000.0),
        ("Jump 100 Index", 50.0, 200.0),
        ("Jump 50 Index", 50000.0, 95000.0),
        ("Volatility 75 Index", 30000.0, 55000.0),
        ("Volatility 75 (1s) Index", 3500.0, 6500.0),
        ("EURUSD", 1.00, 1.25),
        ("EURAUD", 1.45, 1.80),
        ("GBPJPY", 180.0, 230.0),
        ("XAUUSD", 2200.0, 3200.0),
        ("XAGUSD", 25.0, 45.0),
        ("US Oil", 60.0, 95.0),
        ("US Tech 100", 18000.0, 25000.0),
        ("Germany 40", 22000.0, 28000.0),
        ("BTCUSD", 70000.0, 110000.0),
    ]

    for sym, min_expected, max_expected in test_cases:
        p, atr, digits, (b_min, b_max) = resolve_price_profile_and_bounds(sym)
        assert min_expected <= p <= max_expected, f"{sym} profile price {p} fuera de [{min_expected}, {max_expected}]"
        assert b_min <= p <= b_max

        chart = build_chart_data_for_symbol(sym, "BUY")
        assert min_expected * 0.85 <= chart["current_price"] <= max_expected * 1.15, (
            f"{sym} chart price {chart['current_price']} fuera de rango realista"
        )


def test_sanity_gate_rejection_of_contaminated_data():
    """Verifica que si se inyecta una cotización errónea / contaminada (ej. 9198 en Step 500), el guardián la corrija."""
    bad_payload = {
        "symbol": "Step Index 500",
        "direction": "BUY",
        "current_price": 9198.2,  # Cotización espuria contaminada
        "atr": 35.0,
        "digits": 1,
        "candles": [{"open": 9190.0, "high": 9205.0, "low": 9185.0, "close": 9198.2}],
    }

    sanitized = validate_and_sanitize_chart_data("Step Index 500", bad_payload)
    # Debe ser sanada a la cotización fiel de Step Index 500
    assert 3600.0 <= sanitized["current_price"] <= 3900.0
    assert abs(sanitized["current_price"] - 9198.2) > 3000.0
    for c in sanitized["candles"]:
        assert 3000.0 <= c["close"] <= 4500.0


def test_operator_chat_message_step_500_response():
    """Verifica la respuesta completa del chatbot al consultar Step 500 Index."""
    res = process_operator_chat_message("¿Cómo ves Step 500 Index?")
    assert res["ok"] is True
    assert res["symbol"] == "Step Index 500"
    assert res["has_chart"] is True
    chart = res["chart_data"]
    assert chart["symbol"] == "Step Index 500"
    # Precio actual fiel en ~3,745 - 3,790
    assert 3500.0 <= chart["current_price"] <= 4100.0
    # Stop loss y Take profits acordes
    assert chart["stop_loss"] < chart["current_price"] or chart["direction"] == "SELL"
    # Jamás mencionar 9198.2
    assert "9198" not in res["reply"]
    assert abs(chart["current_price"] - 9198.2) > 3000.0
