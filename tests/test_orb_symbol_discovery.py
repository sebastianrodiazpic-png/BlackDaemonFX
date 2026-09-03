
from strategy.orb.new_york_orb import discover_orb_symbols


class FakeProvider:
    def __init__(self):
        self.info = {
            "XAUUSD": {"trade_mode": 4},
            "XAUUSDmicro": {"trade_mode": 4},
            "Gold BB Pullback Index": {"trade_mode": 0},
            "Gold MACO Long Term Index": {"trade_mode": 0},
            "Wall Street 30": {"trade_mode": 4},
            "US Tech 100": {"trade_mode": 4},
            "US500": {"trade_mode": 4},
            "SPX500": {"trade_mode": 4},
            "US SP 500": {"trade_mode": 4},
        }

    def search_symbols(self, term):
        term = term.lower()
        return [name for name in self.info if term in name.lower()]

    def get_symbol_info(self, symbol):
        return self.info[symbol]


def test_discovery_includes_both_real_gold_contracts_and_not_gold_derived_indices():
    found = discover_orb_symbols(FakeProvider())
    assert "XAUUSD" in found
    assert "XAUUSDmicro" in found
    assert "Gold BB Pullback Index" not in found
    assert "Gold MACO Long Term Index" not in found


def test_discovery_excludes_disabled_orb_contracts():
    provider = FakeProvider()
    provider.info["XAUUSDmicro"]["trade_mode"] = 0
    found = discover_orb_symbols(provider)
    assert "XAUUSD" in found
    assert "XAUUSDmicro" not in found


def test_discovery_includes_sp500_broker_aliases():
    found = discover_orb_symbols(FakeProvider())
    assert "US500" in found
    assert "SPX500" in found
    assert "US SP 500" in found
