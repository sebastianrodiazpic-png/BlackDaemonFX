from types import SimpleNamespace

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from strategy.orb.asset_rules import ASSET_CONFIG, ORB_STRATEGY_VERSION
from strategy.orb.new_york_orb import discover_orb_symbols
from reporting.orb_metrics import summarize_orb_trades


def make_engine(config):
    return LiveTradingEngine(provider=SimpleNamespace(), repository=SimpleNamespace(),
                             executor=SimpleNamespace(), config=config)


def test_worker_engine_loads_new_defaults_and_isolates_profiles():
    config = LiveTradingConfig(bot_profile="ORB", orb_enabled=True, execution_enabled=False)
    engine = make_engine(config)
    assert config.orb_strategy_version == ORB_STRATEGY_VERSION
    assert engine.orb_strategy.config.asset_profiles == ASSET_CONFIG
    assert engine.orb_strategy.config.retest_max_candles == 3
    engine.orb_strategy.config.asset_profiles["XAUUSD"]["allowed_modes"].append("MOMENTUM")
    assert config.orb_asset_profiles["XAUUSD"]["allowed_modes"] == ["MOMENTUM", "RETEST"]
    assert ASSET_CONFIG["XAUUSD"]["allowed_modes"] == ["MOMENTUM", "RETEST"]


def test_worker_engine_forwards_profile_overrides():
    config = LiveTradingConfig(bot_profile="ORB", orb_enabled=True, execution_enabled=False)
    config.orb_asset_profiles["US30"]["max_range_atr_ratio"] = 1.7
    assert make_engine(config).orb_strategy.config.asset_profiles["US30"]["max_range_atr_ratio"] == 1.7
    assert LiveTradingConfig().orb_asset_profiles["US30"]["max_range_atr_ratio"] == 2.0


def test_coordinator_discovery_includes_configured_instruments():
    symbols = ["BTCUSD", "US30", "NAS100", "XAUUSD"]
    provider = SimpleNamespace(search_symbols=lambda term: [s for s in symbols if term.lower() in s.lower()],
                               get_symbol_info=lambda symbol: {"trade_mode": 4})
    assert discover_orb_symbols(provider) == sorted(symbols)


def test_direct_execution_history_recovers_mode_from_signal():
    records = [{"id": 1, "instrument": "US30", "source": "DEMO", "status": "CLOSED", "net_pnl": 5,
                "details": {"metadata": {"trade_leg": "TP1"},
                            "signal": {"orb_entry_mode": "ORB_BREAKOUT_MOMENTUM"}}}]
    metrics = summarize_orb_trades(records)
    assert metrics[0]["strategy"] == "ORB_NY_MOMENTUM"
    assert metrics[0]["expectancy_net_pnl"] == 5
