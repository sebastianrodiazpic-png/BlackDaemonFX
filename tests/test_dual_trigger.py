import pandas as pd
import pytest
from strategy.smc.dual_trigger import evaluate_dual_m5_m1_trigger, m5_evidence_before_m1
from strategy.smc.candidate_evaluator import evaluate_candidate_signal_v4

NOW = pd.Timestamp('2026-09-27 12:10', tz='UTC')


def test_m1_early_trigger_requires_m5_sweep_and_time_order():
    m5 = dict(has_sweep=True, sweep_timestamp=NOW-pd.Timedelta(minutes=3))
    m1 = dict(has_choch=True, choch_timestamp=NOW-pd.Timedelta(minutes=1), has_fvg=True, clean_retest=True)
    result = evaluate_dual_m5_m1_trigger(m5, m1, current_time=NOW)
    assert result['approved'] and result['score'] == 35
    assert result['confirmation_timeframe'] == 'M1'
    assert result['diagnostic_tag'] == 'M5_SWEEP_M1_CHOCH_EARLY_TRIGGER'
    assert not evaluate_dual_m5_m1_trigger({}, m1, current_time=NOW)['approved']
    m5['sweep_timestamp'] = NOW
    assert evaluate_dual_m5_m1_trigger(m5, m1, current_time=NOW)['diagnostic_tag'] == 'M1_CHOCH_NOT_AFTER_M5_SWEEP'


@pytest.mark.parametrize('age,approved', [(10,True),(10.01,False),(-1,False)])
def test_selected_m5_clock_cannot_be_masked_by_m1(age, approved):
    result = evaluate_dual_m5_m1_trigger(
        dict(has_sweep=True,has_choch=True,choch_timestamp=NOW-pd.Timedelta(minutes=age)),
        dict(has_choch=True,choch_timestamp=NOW),current_time=NOW)
    assert result['approved'] is approved
    assert result['confirmation_timeframe'] == 'M5'


def test_missing_timestamp_and_wick_without_fvg_fail_closed():
    assert not evaluate_dual_m5_m1_trigger(dict(has_sweep=True,has_choch=True),current_time=NOW)['approved']
    assert not evaluate_dual_m5_m1_trigger(dict(has_sweep=True,has_wick_break_with_fvg=True),current_time=NOW)['approved']


def test_only_completed_prior_directional_sweep_counts():
    frame = pd.DataFrame({'time':pd.date_range('2026-09-27 12:00', periods=3,freq='5min',tz='UTC'),
                          'bullish_sweep':[False,True,False], 'bearish_sweep':[False,False,True]})
    assert not m5_evidence_before_m1(frame,frame.time[0],NOW,'long')['has_sweep']
    assert m5_evidence_before_m1(frame,frame.time[0],NOW+pd.Timedelta(minutes=1),'long')['has_sweep']
    assert not m5_evidence_before_m1(frame,frame.time[0],NOW+pd.Timedelta(minutes=1),'short')['has_sweep']


def test_unified_v4_preserves_modes_and_macro_veto():
    args = dict(signal_type='BUY', current_price=110,
        h1_raw=dict(low=100,high=140,source='PIVOT'), m15_raw=dict(break_quality='BOS'),
        m5_raw=dict(has_sweep=True,sweep_timestamp=NOW-pd.Timedelta(minutes=3)),
        m1_raw=dict(has_choch=True,choch_timestamp=NOW-pd.Timedelta(minutes=1)),current_time=NOW)
    result=evaluate_candidate_signal_v4(**args)
    assert result['status']=='ADAPTIVE_APPROVED' and result['final_score']==75
    args['m1_raw']['has_fvg']=True
    assert evaluate_candidate_signal_v4(**args)['status']=='STRICT_APPROVED'
    args['current_price']=130
    assert not evaluate_candidate_signal_v4(**args)['approved']


def test_confirmation_engine_uses_external_m5_sweep_for_m1():
    from test_confirmation_engine import _data, _setup
    from strategy.smc.confirmation_engine import evaluate_m5_confirmation, M5ConfirmationConfig
    frame=_data()
    frame['time']=pd.to_datetime(['2026-01-01 00:05','2026-01-01 00:06','2026-01-01 00:10','2026-01-01 00:11'],utc=True)
    frame['choch_bullish']=[False,False,False,True]
    setup=_setup(frame)
    setup['setup_time']=pd.Timestamp('2026-01-01 00:00',tz='UTC')
    setup['h1_adaptive_bounds']=dict(low=90,high=130,source='PIVOT')
    setup['m15_structure']=dict(break_quality='BOS')
    context=pd.DataFrame(dict(time=pd.to_datetime(['2026-01-01 00:05'],utc=True),bullish_sweep=[True]))
    config=M5ConfirmationConfig(adaptive_smc_score_enabled=True,dual_trigger_enabled=True,
        confirmation_timeframe_minutes=1,require_fvg=False,require_chart_pattern=False)
    kwargs=dict(data=frame,setup=setup,retest_index=2,confirmation_index=3,direction='long',config=config)
    result=evaluate_m5_confirmation(**kwargs,m5_trigger_data=context)
    assert result['confirmation_valid']
    assert result['m5_detailed_confirmation']['diagnostic_tag']=='M5_SWEEP_M1_CHOCH_EARLY_TRIGGER'
    assert result['confirmation_timeframe']=='M1'
    assert not evaluate_m5_confirmation(**kwargs)['confirmation_valid']


def test_m1_preflight_does_not_wait_for_m5_close():
    from strategy.smc.entry_preflight import confirmation_guard
    data=pd.DataFrame(dict(time=pd.to_datetime(['2026-09-27 12:08','2026-09-27 12:09'],utc=True),
        low=[100,100],high=[110,110],close=[105,106],bos_bearish=[False,False],choch_bearish=[False,False]))
    assert confirmation_guard(data,data.time.iloc[-1],'BUY',NOW,timeframe_minutes=1)['valid']
    assert not confirmation_guard(data,data.time.iloc[-1],'BUY',NOW)['valid']


def test_coordinator_fetches_m1_and_passes_m5_evidence(monkeypatch):
    import strategy.execution.multi_timeframe as module
    analyzer=module.MultiTimeframeAnalyzer(None,module.MultiTimeframeConfig(
        h1_location_only=True,dual_m5_m1_trigger_enabled=True))
    frame=pd.DataFrame(dict(time=pd.date_range('2026-09-10',periods=100,freq='h',tz='UTC'),
        open=125.,high=190.,low=110.,close=125.))
    frame.loc[20,'high']=200.;frame.loc[40,'low']=100.
    setup=pd.DataFrame([dict(time=frame.time.iloc[-3],setup_time=frame.time.iloc[-3],
        ob_low=120.,ob_high=130.,setup_type='long',direction='BUY')])
    fetched=[]
    def stage(symbol,tf,count):
        fetched.append(tf)
        return frame,dict(data=frame,setups=setup,confirmations=pd.DataFrame(),summary={}),{}
    monkeypatch.setattr(analyzer,'_get_stage_result',stage)
    monkeypatch.setattr(analyzer,'_get_h1_context',lambda *a:dict(trend='NEUTRAL',valid=True,reason='TEST',context_time=None))
    monkeypatch.setattr(analyzer,'_m15_setups',lambda *a:setup)
    captured={}
    def pipeline(**kwargs):
        cfg=kwargs['config']
        confirmations=pd.DataFrame()
        if cfg.confirmation_timeframe_minutes==1:
            captured.update(kwargs)
            confirmations=pd.DataFrame([dict(entry_time=frame.time.iloc[-1],direction='BUY',valid=True,
                confirmation_timeframe='M1')])
        return dict(data=frame,confirmations=confirmations,summary={})
    monkeypatch.setattr(module,'run_trade_pipeline',pipeline)
    class Selected(Exception): pass
    def select(setups,confirmations):
        assert confirmations.iloc[-1].confirmation_timeframe=='M1'
        raise Selected()
    monkeypatch.setattr(analyzer,'_select_ordered_pair',select)
    with pytest.raises(Selected): analyzer.analyze_symbol('EURUSD')
    assert 'M1' in fetched
    assert captured['m5_trigger_data'] is frame
    assert captured['config'].dual_trigger_enabled


def test_scheduler_uses_m1_only_for_enabled_adaptive_smc():
    from strategy.execution.live_trading_engine import LiveTradingEngine,LiveTradingConfig
    engine=object.__new__(LiveTradingEngine)
    engine.config=LiveTradingConfig(h1_location_only=True,bot_profile='BOOM')
    assert engine._smc_event_timeframe()=='M1'
    engine.config.dual_m5_m1_trigger_enabled=False
    assert engine._smc_event_timeframe()=='M5'
    engine.config.dual_m5_m1_trigger_enabled=True
    engine.config.bot_profile='ORB'
    assert engine._smc_event_timeframe()=='M5'


def test_early_preflight_rechecks_m1_and_supporting_m5(monkeypatch):
    from types import SimpleNamespace
    from unittest.mock import Mock
    from strategy.execution.live_trading_engine import LiveTradingEngine,LiveTradingConfig
    engine=object.__new__(LiveTradingEngine)
    engine.config=LiveTradingConfig()
    now=pd.Timestamp.now(tz='UTC')
    def candles(tf):
        freq='1min' if tf=='M1' else '5min'
        return pd.DataFrame(dict(time=pd.date_range(end=now.floor(freq),periods=4,freq=freq),
            open=100.,high=102.,low=98.,close=100.,bos_bearish=False,choch_bearish=False,
            bos_bullish=False,choch_bullish=False))
    m1,m5=candles('M1'),candles('M5')
    engine.provider=SimpleNamespace(get_candles=Mock(side_effect=lambda symbol,tf,count: m1 if tf=='M1' else m5),
        get_current_tick=lambda symbol:dict(ask=100.1,bid=100.))
    engine.multi_timeframe=SimpleNamespace(_run_pipeline=lambda data,symbol:dict(data=data),
        pipeline_config=SimpleNamespace(m5_max_signal_age_minutes=10))
    engine._market_signal_diagnostics=lambda *args:{}
    engine._persist_audit_event=Mock()
    signal=dict(entry_time=m1.time.iloc[-2],confirmation_timeframe='M1',m15_obstacles=[],
        m5_detailed_confirmation=dict(confirmation_timestamp=m1.time.iloc[-2]+pd.Timedelta(minutes=1),
            sweep_timestamp=m5.time.iloc[-3]+pd.Timedelta(minutes=5)))
    result=engine._smc_entry_preflight('Test',signal,'BUY',100.,90.,[dict(name='TP',take_profit=120.)])
    assert result['valid'],result
    assert result['m5_sweep']['valid']
    assert [call.args[1] for call in engine.provider.get_candles.call_args_list]==['M1','M5']
    m5.loc[2,'choch_bearish']=True
    assert not engine._smc_entry_preflight('Test',signal,'BUY',100.,90.,[dict(name='TP',take_profit=120.)])['valid']


def test_m1_chooses_latest_candidate_after_retest(monkeypatch):
    import strategy.smc.entry_confirmation as module
    from strategy.smc.confirmation_engine import M5ConfirmationConfig
    data=pd.DataFrame(dict(time=pd.date_range('2026-09-27 12:00',periods=5,freq='min',tz='UTC'),
        open=[100,100,100,101,102],high=[101,101,102,103,104],
        low=[99,99,99,100,101],close=[100,100,101.5,102.5,103.5]))
    setup=pd.DataFrame([dict(time=data.time.iloc[0],setup_time=data.time.iloc[0],setup_type='long',ob_low=99,ob_high=101)])
    seen=[]
    def evaluate(**kwargs):
        seen.append(kwargs['confirmation_index'])
        return dict(confirmation_valid=True)
    monkeypatch.setattr(module,'evaluate_m5_confirmation',evaluate)
    result=module.detect_entry_confirmations(data,setup,
        confirmation_config=M5ConfirmationConfig(dual_trigger_enabled=True,confirmation_timeframe_minutes=1))
    assert result.iloc[0].entry_time==data.time.iloc[-1]
    assert seen==[4]
