from types import SimpleNamespace

from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


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


def test_synthetic_runner_cannot_extend_past_tp2_with_manual_configuration():
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(
        bot_profile="BOOM",
        runner_extension_enabled=True,
        runner_extension_max_target_rr=4.0,
    )

    result = engine._manage_runner_extension(
        trade={
            "broker_position_ticket": "1",
            "instrument": "Boom 500 Index",
            "direction": "BUY",
            "details": {"metadata": {"trade_leg": "RUNNER", "strategy_name": "SMC"}},
        },
        position=SimpleNamespace(price_open=100.0, sl=90.0),
        metadata={"trade_leg": "RUNNER", "strategy_name": "SMC"},
        initial_stop_loss=90.0,
        current_rr=2.1,
        move_stop=lambda **_: {"modified": True},
    )

    assert result["reason"] == "SYNTHETICS_FIXED_TP2_TARGET"


def test_synthetic_break_even_adds_live_spread_to_protect_the_runner():
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(break_even_offset_points=2)
    engine.provider = SimpleNamespace(
        get_current_tick=lambda _symbol: {"bid": 100.18, "ask": 100.20}
    )
    engine.executor = SimpleNamespace(
        get_symbol_constraints=lambda _symbol: {"point": 0.01, "digits": 2}
    )

    stop_loss, offset = engine._break_even_target_stop(
        "Boom 500 Index", "BUY", 100.00
    )

    assert stop_loss == 100.04
    assert round(offset, 8) == 0.04
