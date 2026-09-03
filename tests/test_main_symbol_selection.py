from app.main import (
    _normalize_categories,
    _require_symbol_for_offline_mode,
    _resolve_symbols,
)
from config.strategy_config import TIMEFRAMES


class FakeConnector:
    pass


class FakeProvider:
    def __init__(self):
        self.connector = FakeConnector()
        self.ensure_calls = []

    def ensure_symbol(self, symbol):
        self.ensure_calls.append(symbol)
        return f"EXACT::{symbol}"


class FakeInstrumentManager:
    def __init__(self, connector):
        self.connector = connector
        self.calls = []

    def get_active_symbols(self, categories=None):
        self.calls.append(categories)

        if categories == ["boom", "crash"]:
            return [
                "Boom 100 Index",
                "Crash 500 Index",
            ]

        return [
            "Boom 100 Index",
            "Crash 500 Index",
            "Volatility 75 Index",
        ]


def test_explicit_symbol_has_priority():
    print("\nTEST 1 - SIMBOLO EXPLICITO TIENE PRIORIDAD")

    provider = FakeProvider()

    result = _resolve_symbols(
        provider,
        symbol="Boom 100 Index",
    )

    assert result == ["EXACT::Boom 100 Index"]
    assert provider.ensure_calls == [
        "Boom 100 Index"
    ]

    print("SIMBOLO EXPLICITO: OK")


def test_dynamic_symbols_are_discovered(monkeypatch):
    print("\nTEST 2 - DESCUBRIMIENTO DINAMICO")

    provider = FakeProvider()

    monkeypatch.setattr(
        "app.main.InstrumentManager",
        FakeInstrumentManager,
    )

    result = _resolve_symbols(provider)

    assert result == [
        "Boom 100 Index",
        "Crash 500 Index",
        "Volatility 75 Index",
    ]

    print("DESCUBRIMIENTO DINAMICO: OK")


def test_categories_are_normalized(monkeypatch):
    print("\nTEST 3 - CATEGORIAS NORMALIZADAS")

    provider = FakeProvider()

    monkeypatch.setattr(
        "app.main.InstrumentManager",
        FakeInstrumentManager,
    )

    categories = _normalize_categories(
        "BOOM, crash "
    )

    result = _resolve_symbols(
        provider,
        categories=categories,
    )

    assert categories == [
        "boom",
        "crash",
    ]

    assert result == [
        "Boom 100 Index",
        "Crash 500 Index",
    ]

    print("CATEGORIAS: OK")


def test_offline_modes_require_symbol():
    print("\nTEST 4 - MODO OFFLINE REQUIERE SIMBOLO")

    try:
        _require_symbol_for_offline_mode(
            None,
            "backtest",
        )
    except ValueError as error:
        assert "--symbol" in str(error)
    else:
        raise AssertionError(
            "Debía requerir --symbol"
        )

    print("VALIDACION OFFLINE: OK")


def test_strategy_timeframes_are_used_outside_instruments():
    print("\nTEST 5 - TIMEFRAMES FUERA DE INSTRUMENTS")

    assert TIMEFRAMES["structure"] == "H1"
    assert TIMEFRAMES["confirmation"] == "M15"
    assert TIMEFRAMES["entry"] == "M5"

    print("TIMEFRAMES: H1 -> M15 -> M5")
    print("OK")
