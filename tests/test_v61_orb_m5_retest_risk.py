import inspect
from strategy.orb.new_york_orb import ORBConfig
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


def test_orb_v61_defaults_are_m5_midpoint_and_2r():
    cfg=ORBConfig()
    assert cfg.timeframe == "M5"
    assert cfg.stop_mode == "MIDPOINT"
    assert cfg.stop_buffer_fraction == 0.0
    assert cfg.target_rr == 2.0


def test_live_orb_risk_is_fixed_to_one_percent_total():
    cfg=LiveTradingConfig()
    assert cfg.orb_risk_percent == 1.0
    assert cfg.split_entries_enabled is True
    assert cfg.split_entry_risk_fraction == 0.50
    assert cfg.first_target_rr == 1.0
    assert cfg.second_target_rr == 2.0


def test_runner_can_extend_2r_to_3r_and_4r_with_profit_locks():
    cfg=LiveTradingConfig(
        runner_extension_enabled=True,
        runner_extension_first_trigger_rr=2.0,
        runner_extension_first_lock_rr=1.0,
        runner_extension_second_trigger_rr=3.0,
        runner_extension_second_lock_rr=2.0,
        runner_extension_max_target_rr=4.0,
    )
    assert cfg.runner_extension_first_trigger_rr == 2.0
    assert cfg.runner_extension_first_lock_rr == 1.0
    assert cfg.runner_extension_second_trigger_rr == 3.0
    assert cfg.runner_extension_second_lock_rr == 2.0
    assert cfg.runner_extension_max_target_rr == 4.0


def test_execute_signal_uses_orb_specific_risk_percent():
    source=inspect.getsource(LiveTradingEngine.process_symbol)
    assert 'self.config.orb_risk_percent' in source
    assert 'strategy_name == "ORB_NEW_YORK"' in source


def test_orb_signal_source_requires_retest():
    from strategy.orb.new_york_orb import NewYorkORBStrategy
    source=inspect.getsource(NewYorkORBStrategy.analyze_symbol)
    assert 'retest_buy_ok' in source
    assert 'retest_sell_ok' in source
    assert 'BREAKOUT_M5_SIN_RETEST_CONFIRMADO_AL_ORB' in source
