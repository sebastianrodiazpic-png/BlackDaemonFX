from strategy.execution.live_trading_engine import LiveTradingConfig


def test_all_operational_runner_defaults_end_at_tp2():
    config = LiveTradingConfig()
    assert config.runner_extension_enabled is False
    assert config.runner_extension_max_target_rr == 2.0
    assert config.smc_runner_max_target_rr == 2.0
    assert config.forex_runner_max_target_rr == 2.0
    assert config.forex_runner_broker_safety_target_rr == 2.0


def test_runner_keeps_split_risk_at_half_percent_per_leg():
    config = LiveTradingConfig()
    assert config.split_entries_enabled is True
    assert config.split_entry_risk_fraction == 0.50
    assert config.first_target_rr == 1.0
    assert config.second_target_rr == 2.0
