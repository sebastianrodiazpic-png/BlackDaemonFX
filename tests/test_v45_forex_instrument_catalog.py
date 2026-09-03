
from types import SimpleNamespace

import brokers.symbol_discovery as sd
from config.instruments import InstrumentManager, DEFAULT_CATEGORIES
from dashboard.realtime_dashboard import _CATEGORY_LABELS


class Connected:
    def is_connected(self):
        return True


def _info(name, base="", quote="", visible=True, trade_mode=1):
    return SimpleNamespace(
        name=name,
        currency_base=base,
        currency_profit=quote,
        visible=visible,
        trade_mode=trade_mode,
        volume_min=0.01,
        volume_max=100.0,
        volume_step=0.01,
        point=0.00001,
        digits=5,
    )


def test_forex_is_a_default_operational_category():
    assert "forex" in DEFAULT_CATEGORIES
    assert _CATEGORY_LABELS["forex"] == "Forex"


def test_forex_name_fallback_supports_broker_suffixes():
    assert sd._looks_like_forex_name("EURUSD")
    assert sd._looks_like_forex_name("EURUSDm")
    assert sd._looks_like_forex_name("GBPUSD.a")
    assert sd._looks_like_forex_name("USDJPYmicro")
    assert not sd._looks_like_forex_name("XAUUSD")
    assert not sd._looks_like_forex_name("US500")
    assert not sd._looks_like_forex_name("Volatility 75 Index")


def test_tradeable_forex_is_discovered_from_mt5_metadata(monkeypatch):
    infos = {
        "EURUSD": _info("EURUSD", "EUR", "USD"),
        "GBPUSDm": _info("GBPUSDm", "GBP", "USD"),
        "XAUUSD": _info("XAUUSD", "XAU", "USD"),
        "EURUSD.disabled": _info("EURUSD.disabled", "EUR", "USD", trade_mode=0),
        "Volatility 75 Index": _info("Volatility 75 Index"),
    }

    monkeypatch.setattr(
        sd.mt5, "symbols_get",
        lambda: [SimpleNamespace(name=name) for name in infos],
    )
    monkeypatch.setattr(sd.mt5, "symbol_info", lambda symbol: infos.get(symbol))
    monkeypatch.setattr(sd.mt5, "symbol_select", lambda symbol, selected: True)
    monkeypatch.setattr(sd.mt5, "SYMBOL_TRADE_MODE_DISABLED", 0, raising=False)

    discovery = sd.DerivSymbolDiscovery(Connected())
    assert discovery.get_tradeable_forex() == ["EURUSD", "GBPUSDm"]


def test_instrument_manager_unifies_synthetics_and_forex(monkeypatch):
    manager = object.__new__(InstrumentManager)

    class Discovery:
        def get_tradeable_synthetics(self):
            return ["Volatility 75 Index", "Boom 500 Index"]

        def get_tradeable_forex(self):
            return ["EURUSD", "GBPUSD"]

        def classify_symbol(self, symbol):
            if "Volatility" in symbol:
                return "volatility"
            if "Boom" in symbol:
                return "boom"
            return "other"

    manager.discovery = Discovery()

    assert manager.get_all_instruments() == [
        "Boom 500 Index", "EURUSD", "GBPUSD", "Volatility 75 Index"
    ]
    assert manager.get_active_symbols(categories=["forex"]) == ["EURUSD", "GBPUSD"]
    assert manager.get_active_symbols(categories=["boom", "forex"]) == [
        "Boom 500 Index", "EURUSD", "GBPUSD"
    ]
