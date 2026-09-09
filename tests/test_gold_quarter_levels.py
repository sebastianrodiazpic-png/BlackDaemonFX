from strategy.execution.trade_pipeline import _is_xauusd_contract
from strategy.execution.live_trading_engine import LiveTradingConfig
from strategy.smc.round_number_levels import RoundNumberConfig, detect_round_number_confirmation


def test_gold_quarter_levels_are_spaced_every_25_dollars():
    result = detect_round_number_confirmation(
        2073.5,
        2075.5,
        RoundNumberConfig(enabled=True, increment=25.0, tolerance_price=2.0),
    )

    assert result["round_number_confirmed"] is True
    assert result["round_number_level"] == 2075.0


def test_gold_profile_defaults_to_quarter_level_increment():
    assert LiveTradingConfig().gold_quarter_level_increment == 25.0


def test_quarter_levels_apply_only_to_xauusd_contracts():
    assert _is_xauusd_contract("XAUUSD")
    assert _is_xauusd_contract("XAUUSDmicro")
    assert not _is_xauusd_contract("XAGUSD")
    assert not _is_xauusd_contract("US Oil")
