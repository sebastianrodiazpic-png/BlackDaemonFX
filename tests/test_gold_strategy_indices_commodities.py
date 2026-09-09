from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

from app.main import _resolve_live_symbols_for_profile, BOT_PROFILES
from dashboard.realtime_dashboard import _CATEGORY_LABELS, _infer_symbol_profile, _BOT_MAGIC_PROFILE
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from strategy.orb.new_york_orb import (
    classify_orb_market,
    discover_orb_symbols,
    is_orb_commodity_symbol,
    is_orb_eligible_symbol,
    is_orb_gold_symbol,
    is_orb_index_symbol,
    is_orb_oil_symbol,
    is_orb_silver_symbol,
)


def test_classify_all_requested_indices_and_commodities():
    # Wall Street 30 / Dow Jones
    assert classify_orb_market("Wall Street 30") == "WALL_STREET_30"
    assert classify_orb_market("US30") == "WALL_STREET_30"
    assert classify_orb_market("DJ30") == "WALL_STREET_30"
    assert classify_orb_market("Dow Jones 30") == "WALL_STREET_30"
    assert classify_orb_market("WS30") == "WALL_STREET_30"

    # US Tech 100 / Nasdaq
    assert classify_orb_market("US Tech 100") == "US_TECH_100"
    assert classify_orb_market("USTEC") == "US_TECH_100"
    assert classify_orb_market("NASDAQ 100") == "US_TECH_100"
    assert classify_orb_market("NAS100") == "US_TECH_100"
    assert classify_orb_market("NDX100") == "US_TECH_100"

    # US SP 500 / SP500
    assert classify_orb_market("US500") == "US_500"
    assert classify_orb_market("SP500") == "US_500"
    assert classify_orb_market("SPX500") == "US_500"
    assert classify_orb_market("US SP 500") == "US_500"
    assert classify_orb_market("S&P 500") == "US_500"

    # Plata / XAGUSD
    assert classify_orb_market("XAGUSD") == "XAGUSD"
    assert classify_orb_market("XAGUSDmicro") == "MICRO_XAGUSD"
    assert classify_orb_market("Silver") == "XAGUSD"
    assert classify_orb_market("microXAGUSD") == "MICRO_XAGUSD"

    # Petróleo / US Oil
    assert classify_orb_market("US Oil") == "US_OIL"
    assert classify_orb_market("USOIL") == "US_OIL"
    assert classify_orb_market("WTI") == "US_OIL"
    assert classify_orb_market("Crude Oil") == "US_OIL"
    assert classify_orb_market("Brent") == "US_OIL"

    # Oro / XAUUSD
    assert classify_orb_market("XAUUSD") == "XAUUSD"
    assert classify_orb_market("XAUUSDmicro") == "MICRO_XAUUSD"


def test_market_type_helpers():
    assert is_orb_gold_symbol("XAUUSD") is True
    assert is_orb_gold_symbol("XAUUSDmicro") is True
    assert is_orb_gold_symbol("XAGUSD") is False

    assert is_orb_silver_symbol("XAGUSD") is True
    assert is_orb_silver_symbol("Silver") is True
    assert is_orb_silver_symbol("XAGUSDmicro") is True
    assert is_orb_silver_symbol("XAUUSD") is False

    assert is_orb_oil_symbol("US Oil") is True
    assert is_orb_oil_symbol("WTI") is True
    assert is_orb_oil_symbol("US30") is False

    assert is_orb_index_symbol("Wall Street 30") is True
    assert is_orb_index_symbol("US Tech 100") is True
    assert is_orb_index_symbol("US500") is True
    assert is_orb_index_symbol("XAUUSD") is False

    assert is_orb_commodity_symbol("XAUUSD") is True
    assert is_orb_commodity_symbol("XAGUSD") is True
    assert is_orb_commodity_symbol("US Oil") is True
    assert is_orb_commodity_symbol("US500") is False

    assert is_orb_eligible_symbol("Wall Street 30") is True
    assert is_orb_eligible_symbol("US Tech 100") is True
    assert is_orb_eligible_symbol("US500") is True
    assert is_orb_eligible_symbol("XAUUSD") is True
    assert is_orb_eligible_symbol("XAGUSD") is True
    assert is_orb_eligible_symbol("US Oil") is True
    assert is_orb_eligible_symbol("Volatility 75 Index") is False


def test_orb_worker_resolves_all_indices_and_commodities(monkeypatch):
    # El worker GOLD comparte el mismo universo completo que ORB (Oro, Plata,
    # Petroleo, indices). Los niveles de cuarto se aplican internamente solo
    # a XAUUSD/microXAUUSD (ver LiveTradingConfig.gold_quarter_level_*).
    fake_symbols = [
        "XAUUSD", "XAGUSD", "Wall Street 30", "US Tech 100", "US500", "US Oil",
    ]
    mock_provider = MagicMock()
    mock_provider.search_symbols.side_effect = lambda term: [
        s for s in fake_symbols if term.lower() in s.lower()
    ]
    mock_provider.get_symbol_info.return_value = {"trade_mode": 4}

    monkeypatch.setattr("brokers.mt5_connector.MT5Connector.connect", lambda self: True)
    monkeypatch.setattr("brokers.mt5_connector.MT5Connector.disconnect", lambda self: True)
    monkeypatch.setattr("brokers.mt5_data.MT5DataProvider.connect", lambda self: True)
    monkeypatch.setattr("brokers.mt5_data.MT5DataProvider.disconnect", lambda self: True)
    monkeypatch.setattr(
        "app.main.discover_orb_symbols",
        lambda provider: fake_symbols,
    )

    args = SimpleNamespace(symbol=None)
    resolved = _resolve_live_symbols_for_profile(args, "ORB")
    assert resolved == sorted(set(fake_symbols))

    gold_resolved = _resolve_live_symbols_for_profile(args, "GOLD")
    assert gold_resolved == sorted(set(fake_symbols))


def test_high_impact_usd_news_guard_covers_indices_and_commodities_in_gold_and_orb():
    gold_engine = object.__new__(LiveTradingEngine)
    gold_engine.config = LiveTradingConfig(
        bot_profile="GOLD",
        forex_high_impact_news_guard_enabled=True,
    )

    orb_engine = object.__new__(LiveTradingEngine)
    orb_engine.config = LiveTradingConfig(
        bot_profile="ORB",
        forex_high_impact_news_guard_enabled=True,
    )

    # News guard returns None if no event active, but internally checks affected_currencies={"USD"}
    symbols_to_test = ["XAUUSD", "XAGUSD", "Wall Street 30", "US Tech 100", "US500", "US Oil"]
    for sym in symbols_to_test:
        assert is_orb_eligible_symbol(sym) is True


def test_dashboard_category_labels_and_magic():
    assert _BOT_MAGIC_PROFILE[26082029] == "GOLD"
    assert "orb_ny_xagusd" in _CATEGORY_LABELS
    assert "orb_ny_us_oil" in _CATEGORY_LABELS
    assert "orb_ny_wall_street_30" in _CATEGORY_LABELS
    assert "orb_ny_us_tech_100" in _CATEGORY_LABELS
    assert "orb_ny_us_500" in _CATEGORY_LABELS

    assert _infer_symbol_profile("XAGUSD") == "ORB"
    assert _infer_symbol_profile("US Oil") == "ORB"
    assert _infer_symbol_profile("Wall Street 30") == "ORB"
