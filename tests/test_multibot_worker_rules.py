import pytest
from types import SimpleNamespace
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from strategy.execution.worker_rules import (configure_worker_rules, worker_poll_interval,
    worker_rules_manifest, stamp_confirmation_times, RULESET)


@pytest.mark.parametrize('profile',['BOOM','CRASH','STEP','JUMP','VOLATILITY_1','VOLATILITY_2',
    'VOLATILITY_3','VOLATILITY_4','FOREX_1','FOREX_2','FOREX_3','FOREX_4','GOLD'])
def test_all_smc_profiles_receive_same_integration_without_enabling_execution(profile):
    original=LiveTradingConfig(bot_profile=profile,execution_enabled=False,magic=123,risk_percent=.5,
        dual_m5_m1_trigger_enabled=False,h1_location_only=False)
    config=configure_worker_rules(original)
    assert config.dual_m5_m1_trigger_enabled and config.h1_location_only
    assert config.entry_timeframe=='M5' and config.smc_entry_location_policy=='H1_PRIMARY'
    assert config.risk_percent==.5 and config.magic==123 and not config.execution_enabled
    assert config.strategy_version==RULESET
    assert not original.dual_m5_m1_trigger_enabled
    engine=object.__new__(LiveTradingEngine);engine.config=config
    assert engine._smc_event_timeframe()=='M1'
    assert worker_poll_interval(profile,300)==10


@pytest.mark.parametrize('profile',['ORB','IDX_OPEN'])
def test_independent_strategies_keep_their_rules(profile):
    original=LiveTradingConfig(bot_profile=profile,orb_enabled=profile=='ORB',idx_open_enabled=False)
    config=configure_worker_rules(original)
    assert not config.dual_m5_m1_trigger_enabled and not config.h1_location_only
    assert config.orb_enabled==original.orb_enabled and not config.idx_open_enabled
    assert config.strategy_version==original.strategy_version
    assert worker_poll_interval(profile,60)==60


@pytest.mark.parametrize('frame,close',[('M1','2026-09-28T12:01:00+00:00'),('M5','2026-09-28T12:05:00+00:00')])
def test_timestamp_uses_selected_confirmation_timeframe(frame,close):
    signal=dict(entry_time='2026-09-28T12:00Z',confirmation_timeframe=frame,timeframe='M5')
    stamp_confirmation_times(signal)
    assert signal['confirmation_closed_at']==close


def test_jump_consumes_real_price_action_evidence_and_still_rejects_missing_requirement():
    from test_confirmation_engine import _data,_setup
    from strategy.smc.confirmation_engine import evaluate_m5_confirmation,M5ConfirmationConfig
    data=_data()
    signal=evaluate_m5_confirmation(data=data,setup=_setup(data),retest_index=2,
        confirmation_index=3,direction='long',config=M5ConfirmationConfig(require_fvg=False,require_chart_pattern=False))
    assert all(signal['price_action_confirmations'].values())
    # Isolate the Jump gate contract from the separate adaptive points/ratio rules.
    signal.update(trade_score=95,confirmation_percentage=100,confirmations={'m5_choch':True})
    engine=object.__new__(LiveTradingEngine)
    engine.config=LiveTradingConfig(jump_strict_filter_enabled=True)
    assert engine._jump_quality_gate('Jump 100 Index',signal) is None
    signal['price_action_confirmations']['displacement']=False
    blocked=engine._jump_quality_gate('Jump 100 Index',signal)
    assert blocked is not None and blocked['action']=='JUMP_STRICT_FILTER_REJECTED'


def test_manifest_reflects_real_engine_configuration():
    from test_daemon_split_risk_management import Provider,Repo,Executor
    engine=LiveTradingEngine(Provider(),Repo(),configure_worker_rules(LiveTradingConfig(bot_profile='STEP')),
        executor=Executor())
    result=worker_rules_manifest(engine)
    assert result['profile']=='STEP' and result['telemetry_worker']=='STEP'
    assert result['dual_m5_m1'] and result['event_timeframe']=='M1'
    assert result['h1_fractal_left']==3 and result['h1_fractal_right']==1
    assert result['m5_max_signal_age_minutes']==10 and not result['execution_enabled']
