"""Market-independent regression cases for persistent MSNR selection."""
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy
from strategy.malaysian_snr.validation import active_av_levels, level_freshness, retest_confirmation
from tools.replay_msnr_live_faithful import replay_frames


def candles(freq='h', count=40, start='2026-10-08'):
    return pd.DataFrame({'time':pd.date_range(start, periods=count, freq=freq, tz='UTC'),
                         'open':100., 'high':102., 'low':98., 'close':101.})


class Provider:
    def __init__(self, frames):
        self.frames = frames
    def get_candles(self, symbol, timeframe, count=100):
        return self.frames.get(timeframe, pd.DataFrame()).tail(count)


def late_fractal(retest_minutes=75):
    h1 = candles()
    h1.loc[37,['open','high','low','close']] = [100,103,99,101]
    h1.loc[38,['open','high','low','close']] = [100,102,97,100.5]
    h1.loc[39,['open','high','low','close']] = [99,105,98,104]
    closed = h1.time.iloc[-1] + pd.Timedelta(hours=1)
    m15 = candles('15min',60,closed-pd.Timedelta(hours=15))
    post = candles('15min',retest_minutes//15,closed)
    post[['open','high','low','close']] = [105.4,106.,105.2,105.8]
    post.loc[len(post)-1,['open','high','low','close']] = [102.9,103.8,102.8,103.3]
    if retest_minutes >= 60:
        h1 = pd.concat([h1,pd.DataFrame([{'time':closed,'open':105.4,'high':106.,
                                        'low':105.2,'close':105.8}])],ignore_index=True)
    frames = {'H1':h1,'M15':pd.concat([m15,post],ignore_index=True)}
    cfg = MalaysianSNRConfig(allowed_symbols=(), enable_daily_storyline_filter=False)
    return Provider(frames), cfg, closed + pd.Timedelta(minutes=retest_minutes), closed


@pytest.mark.parametrize('minutes',[15,45,60,75,90])
def test_original_break_survives_h1_roll_and_boundary(minutes):
    provider,cfg,now,original = late_fractal(minutes)
    result = MalaysianSNRStrategy(provider,cfg).analyze_symbol('Step Index',now)
    assert result['valid'], result
    assert result['signal']['structure_closed_at'] == original.isoformat()
    assert result['signal']['entry_time'] == now.isoformat()
    assert result['signal']['entry_confirmation'] == 'CRT_M15_SWEEP_AND_ABSORPTION_CLOSE'
    assert result['signal']['stop_loss'] < 98


def test_reconstruction_on_restart_has_same_identity_and_repeated_close():
    provider,cfg,now,_ = late_fractal()
    first = MalaysianSNRStrategy(provider,cfg).analyze_symbol('Step Index',now)
    restarted = MalaysianSNRStrategy(provider,cfg).analyze_symbol('Step Index',now+pd.Timedelta(minutes=1))
    assert first['signal']['setup_id'] == restarted['signal']['setup_id']
    assert first['signal']['entry_time'] == restarted['signal']['entry_time']
    assert first['signal']['stop_loss'] == restarted['signal']['stop_loss']


def test_final_closed_bar_has_bounded_processing_grace():
    provider,cfg,now,_ = late_fractal(90)
    strategy = MalaysianSNRStrategy(provider,cfg)
    assert strategy.analyze_symbol('Step Index',now+pd.Timedelta(seconds=30))['valid']
    assert strategy.analyze_symbol('Step Index',now+pd.Timedelta(seconds=61))['reason']=='SETUP_EXPIRED'


def test_expired_setup_cannot_recover_with_late_retest():
    provider,cfg,now,_ = late_fractal(105)
    result = MalaysianSNRStrategy(provider,cfg).analyze_symbol('Step Index',now)
    assert not result['valid']
    assert result['reason'] == 'SETUP_EXPIRED'


def test_invalidation_is_not_erased_by_later_recovery():
    provider,cfg,now,_ = late_fractal()
    provider.frames['M15'].loc[60,['open','high','low','close']] = [100,105.2,97.9,104.8]
    result = MalaysianSNRStrategy(provider,cfg).analyze_symbol('Step Index',now)
    assert not result['valid']
    assert result['reason'] == 'SETUP_STRUCTURE_INVALIDATED'


def test_missing_post_break_bar_does_not_fabricate_first_retest():
    provider,cfg,now,_ = late_fractal()
    provider.frames['M15'] = provider.frames['M15'].drop(index=60)
    result = MalaysianSNRStrategy(provider,cfg).analyze_symbol('Step Index',now)
    assert result['reason'] == 'RETEST_DATA_GAP'


def test_confirmation_consumes_setup_and_next_bar_cannot_reenter():
    provider,cfg,now,_ = late_fractal(75)
    strategy = MalaysianSNRStrategy(provider,cfg)
    assert strategy.analyze_symbol('Step Index',now)['valid']
    provider.frames['M15'] = pd.concat([provider.frames['M15'],pd.DataFrame([
        {'time':now,'open':102.9,'high':103.8,'low':102.8,'close':103.3}])],ignore_index=True)
    result = strategy.analyze_symbol('Step Index',now+pd.Timedelta(minutes=15))
    assert not result['valid']
    assert result['reason'] == 'SETUP_ALREADY_CONFIRMED'


def retest(prices):
    frame = pd.DataFrame(prices,columns=['open','high','low','close'])
    frame['time'] = pd.date_range('2026-10-08',periods=len(frame),freq='15min',tz='UTC')
    return frame


@pytest.mark.parametrize('direction',['BUY','SELL'])
def test_zone_and_actual_sweep_are_different_valid_triggers(direction):
    def mirror(frame):
        if direction == 'SELL':
            frame = frame.assign(open=200-frame.open,close=200-frame.close,
                                 high=200-frame.low,low=200-frame.high)
        return frame
    zone = mirror(retest([[100.5,101,100.5,100.8]]))
    sweep = mirror(retest([[100,100.8,99.5,100.5]]))
    assert retest_confirmation(zone,100,direction,2)['trigger'] == 'M15_ZONE_REJECTION_CLOSE'
    assert retest_confirmation(sweep,100,direction,2)['trigger'] == 'CRT_M15_SWEEP_AND_ABSORPTION_CLOSE'
    assert not retest_confirmation(zone,100,direction,2,allow_zone=False)['confirmed']
    assert not retest_confirmation(zone,100,direction,2,tolerance_atr=.20)['confirmed']


def test_no_intersection_cannot_link_far_candle_to_recovery():
    frame = retest([[95,96,94,95.5],[100.8,101.2,100.8,101.1]])
    assert not retest_confirmation(frame,100,'BUY',2)['confirmed']


def test_gap_beyond_level_before_first_apparent_touch_cannot_be_repaired():
    frame = retest([[95,96,94,95.5],[100.,100.8,99.9,100.6]])
    assert retest_confirmation(frame,100,'BUY',2)['reason']=='RETEST_PENETRATION_TOO_DEEP'


def test_deep_sweep_is_rejected_even_with_directional_close():
    result = retest_confirmation(retest([[99,101,98.5,100.8]]),100,'BUY',2)
    assert result['reason'] == 'RETEST_PENETRATION_TOO_DEEP'


def test_second_visit_cannot_rescue_failed_first_episode():
    frame = retest([[100.5,100.7,99.8,100.1],[101.1,101.5,101.,101.3],
                    [100.,100.8,99.9,100.6]])
    result = retest_confirmation(frame,100,'BUY',2)
    assert result['reason'] == 'RETEST_CONSUMED'


def test_recovery_deadline_is_counted_from_first_touch():
    frame = retest([[100.5,100.7,99.8,100.1]]*3+[[100.,100.8,99.9,100.6]])
    assert retest_confirmation(frame,100,'BUY',2)['reason'] == 'RETEST_RECOVERY_EXPIRED'


def fresh_frame():
    frame = candles(count=8)
    frame[['open','high','low','close']] = [98.,99.,97.,98.5]
    return frame, {'idx':1,'level':100.,'type':'A_RESISTANCE'}


def test_freshness_counts_visits_not_adjacent_candles_and_body_invalidates():
    frame,level = fresh_frame()
    assert level_freshness(frame,level,2)['state'] == 'FRESH'
    frame.loc[3:4,'high'] = 100.1
    one = level_freshness(frame,level,2)
    assert one['state'] == 'TESTED_ONCE' and one['visits'] == 1
    frame.loc[6,'high'] = 100.1
    assert level_freshness(frame,level,2)['state'] == 'CONSUMED'
    frame,level = fresh_frame()
    frame.loc[3,['open','high','low','close']] = [99,100.4,98,100.2]
    assert level_freshness(frame,level,2)['body_invalidated']


def test_penetration_consumes_level_and_break_candle_does_not_count():
    frame,level = fresh_frame()
    frame.loc[3,'high'] = 100.5
    assert level_freshness(frame,level,2)['state'] == 'CONSUMED'
    frame,level = fresh_frame()
    frame.loc[len(frame)-1,['open','high','low','close']] = [99,103,98,102]
    assert level_freshness(frame,level,2)['state'] == 'FRESH'


def test_tested_level_requires_extra_displacement():
    weak = retest([[100.,100.4,99.9,100.2]])
    strong = retest([[99.9,100.8,99.8,100.5]])
    assert retest_confirmation(weak,100,'BUY',2)['confirmed']
    assert not retest_confirmation(weak,100,'BUY',2,require_displacement=True)['confirmed']
    assert retest_confirmation(strong,100,'BUY',2,require_displacement=True)['confirmed']


def test_broken_obstacle_stays_invalid_and_latest_formation_is_active():
    frame = retest([[98,100.5,97,100],[100,100.4,95,96]])
    active = active_av_levels(frame)
    assert any(level['type']=='A_RESISTANCE' and level['level']==100 for level in active)
    frame = pd.concat([frame,retest([[99,102,98,101],[101,102,96,97]])],ignore_index=True)
    assert not any(level['idx']==1 for level in active_av_levels(frame))


def test_live_execution_identity_does_not_change_with_confirmation_time():
    from strategy.execution.live_trading_engine import LiveTradingEngine
    engine = object.__new__(LiveTradingEngine)
    engine.config = SimpleNamespace(source='DEMO')
    one = engine._execution_key('Step Index','2026-10-09 12:15Z','BUY','MALAYSIAN_SNR',setup_id='abc')
    two = engine._execution_key('Step Index','2026-10-09 12:30Z','BUY','MALAYSIAN_SNR',setup_id='abc')
    assert one == two
    assert one != engine._execution_key('Step Index','2026-10-09 12:15Z','BUY','MALAYSIAN_SNR',setup_id='def')
    assert engine._execution_key('Step Index','2026-10-09 12:15Z','BUY','SMC',setup_id='abc') != one


@pytest.mark.parametrize('reason,expected',[
    ('NO_SETUP_CONFIRMED','BUSCANDO SETUP'),('STALE_CANDLES_H1','DATOS ANTIGUOS'),
    ('D1_BIAS_CONFLICT','CONFLICTO D1'),('WAITING_FIRST_RETEST','ESPERANDO RETEST'),
    ('SETUP_EXPIRED','SETUP EXPIRADO'),('OBSTACLE_D1_BEFORE_2R','SIN ESPACIO TP1'),
    ('RETEST_WEAK_RECOVERY','ESPERANDO RECHAZO'),
])
def test_matrix_displays_real_reason_and_countdown(reason,expected):
    from dashboard.realtime_dashboard import _build_confluence_matrix
    state = {'worker_candidates':{'MALAYSIAN_SNR':{
        'symbol':'Step Index','action':'WAITING_MALAYSIAN_SNR','reason':reason,
        'analysis':{'diagnostics':{'remaining_minutes':15.,'macro_bias':'BUY'}}}}}
    row = next(row for row in _build_confluence_matrix(state) if row['symbol']=='Step Index'
               and row['strategy_key']=='MALAYSIAN_SNR')
    assert expected in row['final_state']
    assert '15 min restantes' in row['metrics_freshness']
    assert 'Alcista' in row['macro_context']
    assert row['ai_score'] == '—'


def test_compacted_live_event_preserves_retest_countdown_and_identity():
    from strategy.execution.live_trading_engine import LiveTradingEngine
    from dashboard.realtime_dashboard import _build_confluence_matrix, _extract_quality
    provider,cfg,now,_ = late_fractal()
    analysis = MalaysianSNRStrategy(provider,cfg).analyze_symbol('Step Index',now)
    raw = {'symbol':'Step Index','action':analysis['action'],'analysis':analysis}
    compact = LiveTradingEngine._compact_symbol_result(raw)
    assert compact['setup_id']==analysis['signal']['setup_id']
    assert compact['entry_confirmation']==analysis['signal']['entry_confirmation']
    state = {'worker_candidates':{'MALAYSIAN_SNR':compact}}
    row = next(row for row in _build_confluence_matrix(state) if row['symbol']=='Step Index'
               and row['strategy_key']=='MALAYSIAN_SNR')
    assert '15 min restantes' in row['metrics_freshness']
    quality = _extract_quality(raw)
    assert quality['setup_id']==compact['setup_id']
    assert quality['diagnostics']['remaining_minutes']==15.


def test_active_daily_obstacle_caps_runner_as_well_as_tp1_room():
    provider,cfg,now,_ = late_fractal()
    daily = candles('D',40,'2026-08-31')
    daily.loc[36,['open','high','low','close']] = [110,117,109,116.5]
    daily.loc[37,['open','high','low','close']] = [116.5,117,109,110]
    daily.loc[38,['open','high','low','close']] = [110,112,109,111]
    provider.frames['D1'] = daily
    result = MalaysianSNRStrategy(provider,cfg).analyze_symbol('Step Index',now)
    assert result['valid'],result
    signal = result['signal']
    assert signal['obstacle_level']==116.5
    assert signal['tp1_price'] <= signal['tp2_price'] < 116.5
    assert signal['runner_rr'] < cfg.tp2_runner_rr


@pytest.mark.parametrize('case',['far','wrong_side','expired','missing'])
def test_live_quote_guard_cannot_be_bypassed_by_single_fallback(case):
    from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(split_entries_enabled=True,single_entry_fallback_enabled=True)
    signal = {'setup_id':'abc','ref_level':100.,'atr':2.,'max_entry_distance_atr':.5,
              'invalidation_level':98.,'setup_expires_at':(pd.Timestamp.now(tz='UTC')+pd.Timedelta(minutes=1)).isoformat()}
    entry = 102. if case=='far' else 99. if case=='wrong_side' else 100.5
    if case=='expired':
        signal['setup_expires_at']=(pd.Timestamp.now(tz='UTC')-pd.Timedelta(minutes=1)).isoformat()
    if case=='missing':
        del signal['atr']
    called = []
    result = engine._plan_execution_legs(exact_symbol='Step Index',direction='BUY',entry=entry,
        sl=97.,rr=3.,strategy_name='MALAYSIAN_SNR',signal=signal,total_risk_amount=100.,
        risk_fraction=.5,silver_risk_cap=False,build_plan=lambda *args:called.append(args))
    assert result[0] is None and result[1]['code']=='MSNR_ENTRY_CONTEXT_CHANGED'
    assert not called


def test_live_quote_within_zone_can_build_dual_legs():
    from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile='MALAYSIAN_SNR',split_entries_enabled=True)
    signal = {'setup_id':'abc','ref_level':100.,'atr':2.,'max_entry_distance_atr':.5,
              'invalidation_level':98.,'tp1_rr':2.,'runner_rr':3.,
              'setup_expires_at':(pd.Timestamp.now(tz='UTC')+pd.Timedelta(minutes=1)).isoformat()}
    result = engine._plan_execution_legs(exact_symbol='Step Index',direction='BUY',entry=100.5,
        sl=97.,rr=3.,strategy_name='MALAYSIAN_SNR',signal=signal,total_risk_amount=100.,
        risk_fraction=.5,silver_risk_cap=False,
        build_plan=lambda specs,mode:([{'name':spec[0],'rr':spec[2]} for spec in specs],None))
    assert [leg['name'] for leg in result[0]]==['TP1','RUNNER']
    assert result[0][0]['rr']==2.


def test_replay_never_executes_same_setup_twice_after_fast_stop():
    frame = candles('15min',count=112)
    frame['low'] = 89.
    fake = {'valid':True,'signal':{'setup_id':'once','direction':'BUY','stop_loss':90.,
        'runner_rr':3.,'scenario':'ESC_3_FRACTAL','adx':25.,'body_ratio':.7,'atr':2.}}
    with patch.object(MalaysianSNRStrategy,'analyze_symbol',return_value=fake):
        results = replay_frames('Step Index',{'M15':frame},30,MalaysianSNRConfig(),0.)
    assert len(results)==1 and results[0]['rr']==-1.


def test_continuation_tested_policy_and_consumed_level_are_enforced():
    frame = candles()
    frame['open'] = np.linspace(70,95,len(frame))
    frame['high'],frame['low'],frame['close'] = frame.open+1,frame.open-.5,frame.open+.5
    frame.loc[29,['open','high','low','close']] = [96,100.4,95.5,100]
    frame.loc[30,['open','high','low','close']] = [100,100.3,96,96]
    frame.loc[31:38,['open','high','low','close']] = [98.6,99.3,98.2,99]
    frame.loc[34,['open','high','low','close']] = [99,100.1,98.7,99.5]
    frame.loc[39,['open','high','low','close']] = [99.2,102,99,101.8]
    cfg = MalaysianSNRConfig(enable_scenario_1_continuation=True, continuation_fresh_only=False)
    strategy = MalaysianSNRStrategy(None,cfg)
    def reference():
        return next(setup for setup in strategy._setups_at_break(frame)
                    if setup['scenario']=='ESC_1_CONTINUATION' and setup['level']==100)
    with patch('strategy.malaysian_snr.malaysian_snr_strategy.compute_adx',
               return_value=pd.Series(25.,index=frame.index)):
        assert reference()['freshness']['state']=='TESTED_ONCE'
        assert reference()['blocked_reason'] is None
        strategy.config = replace(cfg,enable_tested_level_entries=False)
        assert reference()['blocked_reason']=='TESTED_LEVEL_DISABLED'
        strategy.config = cfg
        frame.loc[36,'high'] = 100.1
        assert reference()['blocked_reason']=='LEVEL_CONSUMED'
