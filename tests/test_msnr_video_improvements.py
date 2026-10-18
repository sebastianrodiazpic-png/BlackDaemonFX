from copy import deepcopy
from dataclasses import replace
from unittest.mock import patch
import pandas as pd
import pytest
from test_msnr_dynamic_d1_settings import market, dashboard, api
from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.malaysian_snr.runtime_settings import msnr_default_settings, normalize_msnr_settings, validate_msnr_patch
from strategy.malaysian_snr.video_rules import breaker_pair_candidate, session_allowed, track_session_liquidity
from strategy.malaysian_snr.validation import retest_confirmation, active_av_levels
from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy
from strategy.malaysian_snr.ai_policy import settings_signature
from tools.replay_msnr_two_year_comparison import fast_active_av_levels


def candle_frame(values, frequency='15min'):
    return pd.DataFrame([dict(time=pd.Timestamp('2026-10-01T00:00:00Z')+i*pd.Timedelta(frequency),
                             open=o,high=h,low=l,close=c) for i,(o,h,l,c) in enumerate(values)])


def mirror(frame):
    result=frame.copy()
    result['open'],result['close']=200-frame.open,200-frame.close
    result['high'],result['low']=200-frame.low,200-frame.high
    return result


@pytest.mark.parametrize('direction',['BUY','SELL'])
def test_breaker_pair_does_not_need_a_gap_and_freezes_both_extremes(direction):
    frame=candle_frame([(98,100.2,97.8,100),(100,102.2,99.8,102)],'1h')
    if direction=='SELL':frame=mirror(frame)
    pair=breaker_pair_candidate(frame,2.)
    assert pair['direction']==direction and pair['level']==100
    assert pair['junction_gap_atr']==0 and pair['displacement_atr']==1
    assert pair['bound']==pytest.approx(97.8 if direction=='BUY' else 102.2)
    assert breaker_pair_candidate(frame,2.,min_displacement_atr=1.01) is None
    frame.loc[1,'close']=frame.loc[1,'open']
    assert breaker_pair_candidate(frame,2.) is None


@pytest.mark.parametrize('direction',['BUY','SELL'])
def test_pinbar_recovers_a_closed_sweep_without_lowering_tested_once_requirements(direction):
    frame=candle_frame([(100.02,100.16,99.76,100.10)])
    if direction=='SELL':frame=mirror(frame)
    assert not retest_confirmation(frame,100,direction,1.)['confirmed']
    evidence=retest_confirmation(frame,100,direction,1.,allow_pinbar=True)
    assert evidence['confirmed'] and evidence['pinbar_only']
    assert evidence['trigger']=='SNR_PINBAR_SWEEP_RECLAIM'
    assert evidence['rejection_wick_ratio']==pytest.approx(.65)
    assert not retest_confirmation(frame,100,direction,1.,allow_pinbar=True,require_displacement=True)['confirmed']
    assert not retest_confirmation(frame,100,direction,1.,allow_pinbar=True,max_penetration_atr=.20)['confirmed']


def test_pinbar_does_not_rescue_second_visit_or_bad_reclaim():
    first=(100.02,100.1,99.95,100.03)
    away=(100.4,100.6,100.38,100.41)
    pinbar=(100.02,100.16,99.76,100.10)
    frame=candle_frame([first,away,pinbar])
    assert retest_confirmation(frame,100,'BUY',1.,allow_pinbar=True)['reason']=='RETEST_CONSUMED'
    bad=candle_frame([(99.75,100.0,99.6,99.80)])
    assert not retest_confirmation(bad,100,'BUY',1.,allow_pinbar=True)['confirmed']


def test_pinbar_observation_cannot_hide_later_primary_confirmation():
    provider,frames,now=market()
    break_time=frames['H1'].time.iloc[-1]+pd.Timedelta(hours=1)
    frames['M15']=frames['M15'].iloc[:-1].copy()
    pinbar=dict(time=break_time,open=103.02,high=103.16,low=102.76,close=103.10)
    regular=dict(time=break_time+pd.Timedelta(minutes=15),open=103.04,high=103.65,low=102.98,close=103.55)
    frames['M15']=pd.concat([frames['M15'],pd.DataFrame([pinbar,regular])],ignore_index=True)
    cfg=MalaysianSNRConfig(allowed_symbols=(),retest_pinbar_mode='shadow')
    analyzer=MalaysianSNRStrategy(provider,cfg)
    early=analyzer.analyze_symbol('Step Index',break_time+pd.Timedelta(minutes=15))
    assert early['valid'] and early['shadow_only'] and early['signal']['pinbar_observation']
    later=analyzer.analyze_symbol('Step Index',break_time+pd.Timedelta(minutes=30))
    assert later['valid'] and not later['shadow_only']
    assert not later['signal']['retest_evidence']['pinbar_only']
    assert early['signal']['setup_id']==later['signal']['setup_id']


@pytest.mark.parametrize('policy,allowed',[('legacy_utc',False),('market_hours',True)])
def test_crypto_can_scan_outside_forex_hours_without_changing_synthetic_policy(policy,allowed):
    now=pd.Timestamp('2026-10-11T03:00:00Z')
    assert session_allowed('BTCUSDmicro',now,policy)==allowed
    assert session_allowed('Step Index',now,policy,synthetic=True)
    assert not session_allowed('EURUSD',now,policy)


@pytest.mark.parametrize('stamp,allowed',[
    ('2026-07-01T06:30:00Z',True),('2026-01-07T06:30:00Z',False),
    ('2026-03-16T11:30:00Z',True),('2026-01-07T12:15:00Z',True),
    ('2026-07-01T16:00:00Z',False),
])
def test_market_sessions_follow_each_city_clock_across_dst(stamp,allowed):
    assert session_allowed('EURUSD',pd.Timestamp(stamp),'market_hours') is allowed


def test_obstacle_body_turns_include_non_engulfing_level_and_close_invalidates_it():
    frame=candle_frame([(98,101,97,100),(100,100.5,98.5,99),(99,99.9,98.8,99.5)],'1h')
    assert not active_av_levels(frame)
    obstacles=active_av_levels(frame,definition='body_turns')
    assert any(x['type']=='A_RESISTANCE' and x['level']==100 for x in obstacles)
    assert fast_active_av_levels(frame,definition='body_turns')==obstacles
    frame.loc[2,['high','close']]=[102,101]
    assert not any(x['type']=='A_RESISTANCE' and x['level']==100
        for x in active_av_levels(frame,definition='body_turns'))


def test_missing_h4_blocks_only_when_filter_is_live():
    provider,_,now=market()
    cfg=MalaysianSNRConfig(allowed_symbols=(),h4_obstacle_mode='shadow')
    assert MalaysianSNRStrategy(provider,cfg).analyze_symbol('Step Index',now)['valid']
    assert MalaysianSNRStrategy(provider,replace(cfg,h4_obstacle_mode='live')).analyze_symbol('Step Index',now)['reason']=='H4_OBSTACLES_UNAVAILABLE'


def test_h4_observation_records_a_real_obstacle_without_veto_and_live_enforces_it():
    provider,frames,now=market()
    h4=candle_frame([(99,101,97,100)]*40,'4h')
    h4['time']=pd.date_range(end=now.floor('4h')-pd.Timedelta(hours=4),periods=40,freq='4h')
    h4.loc[36,['open','high','low','close']]=[104,110,103,109]
    h4.loc[37,['open','high','low','close']]=[109,111,100,105]
    frames['H4']=h4
    cfg=MalaysianSNRConfig(allowed_symbols=(),h4_obstacle_mode='shadow',obstacle_av_definition='body_turns')
    observed=MalaysianSNRStrategy(provider,cfg).analyze_symbol('Step Index',now)
    assert observed['valid'] and not observed['shadow_only']
    assert observed['signal']['h4_obstacle_evidence']['before_tp1']
    live=MalaysianSNRStrategy(provider,replace(cfg,h4_obstacle_mode='live')).analyze_symbol('Step Index',now)
    assert not live['valid'] and live['reason']=='OBSTACLE_BEFORE_MINIMUM_TP1'


def test_primary_and_pinbar_observations_use_distinct_audit_variants():
    from types import SimpleNamespace
    from unittest.mock import Mock
    from strategy.malaysian_snr.candidate_audit import audit_result
    controls={**msnr_default_settings(),'observe_candidate_outcomes':False}
    signal={'setup_id':'same_episode','strategy_version':MalaysianSNRConfig().strategy_version,
        'entry_timeframe':'M15','entry_price':100.,'confirmation_closed_at':'2026-10-01T12:00:00Z',
        'meta_label':{'market_snapshot':{'planned_rr':2.}},'retest_evidence':{'pinbar_only':False}}
    pinbar={**deepcopy(signal),'retest_evidence':{'pinbar_only':True}}
    analysis={'valid':True,'signal':signal,'runtime_controls':controls,
              'shadow_candidates':[{'valid':True,'signal':pinbar,'shadow_only':True}]}
    repo=SimpleNamespace(save_msnr_candidate=Mock())
    engine=SimpleNamespace(config=SimpleNamespace(source='DEMO',risk_percent=1.),repository=repo)
    result={'analysis':analysis,'action':'TEST_NO_ORDERS'}
    audit_result(engine,'Step Index',result)
    assert not result.get('candidate_audit_error')
    assert [call.kwargs['variant'] for call in repo.save_msnr_candidate.call_args_list]==['M15','M15_PINBAR']


def test_breaker_pair_displacement_cannot_claim_an_unseen_micro_structure_break():
    provider,frames,now=market()
    frames['M15'].loc[57:59,'high']=105.
    cfg=MalaysianSNRConfig(allowed_symbols=())
    analyzer=MalaysianSNRStrategy(provider,cfg)
    setup=next(s for s in analyzer._setups_at_break(frames['H1']) if s['scenario']=='ESC_3_FRACTAL')
    setup={**setup,'scenario':'ESC_1_BREAKER_PAIR','variant_mode':'live'}
    with patch.object(MalaysianSNRStrategy,'_compute_setups_at_break',return_value=[setup]):
        analyzer._structure_cache.clear()
        signal=analyzer.analyze_symbol('Step Index',now)['signal']
    assert not signal['price_action_confirmations']['micro_structure']
    assert signal['micro_structure_evidence']['reference_level']==105.


def test_optional_h4_observation_does_not_fetch_data_without_a_confirmed_setup():
    from unittest.mock import Mock
    provider,_,now=market()
    provider.get_candles=Mock(wraps=provider.get_candles)
    cfg=MalaysianSNRConfig(allowed_symbols=(),h4_obstacle_mode='shadow')
    with patch.object(MalaysianSNRStrategy,'_compute_setups_at_break',return_value=[]):
        result=MalaysianSNRStrategy(provider,cfg).analyze_symbol('Step Index',now)
    assert not result['valid']
    assert not any(call.args[1]=='H4' for call in provider.get_candles.call_args_list)


def test_pinbar_observation_reuses_h1_formations_without_reusing_entry_decisions():
    provider,frames,_=market()
    first=MalaysianSNRStrategy(provider,MalaysianSNRConfig())
    second=deepcopy(first.config)
    second.retest_pinbar_mode='live'
    with patch.object(first,'_compute_setups_at_break',wraps=first._compute_setups_at_break) as compute:
        original=first._setups_at_break(frames['H1'])
        first.config=second
        assert first._setups_at_break(frames['H1'])==original
        assert compute.call_count==1


@pytest.mark.parametrize('bad',[
    {'breaker_pair_min_body_ratio':0},{'breaker_pair_min_body_ratio':True},
    {'breaker_pair_min_displacement_atr':float('nan')},{'breaker_pair_min_displacement_atr':float('inf')},
    {'retest_pinbar_min_wick_ratio':0},{'retest_pinbar_min_close_ratio':.49},
    {'session_policy':'24h'},{'obstacle_av_definition':'wick'},{'h4_obstacle_mode':'apply'},
])
def test_invalid_video_controls_are_rejected(bad):
    with pytest.raises(ValueError):validate_msnr_patch(bad)


def test_new_controls_persist_and_defaults_do_not_reset_operator_choices(dashboard):
    patch={'breaker_pair_mode':'live','retest_pinbar_mode':'live',
        'breaker_pair_min_body_ratio':.6,'session_policy':'legacy_utc',
        'obstacle_av_definition':'engulfing','h4_obstacle_mode':'off'}
    saved=api(dashboard,patch)['settings']
    assert all(saved[k]==v for k,v in patch.items())
    assert api(dashboard)['settings']==saved
    assert normalize_msnr_settings({'fractal_min_body_ratio':.45})['fractal_min_body_ratio']==.45
    assert settings_signature(msnr_default_settings())!=settings_signature({**msnr_default_settings(),**patch})


def test_session_liquidity_tracking_forex_and_synthetics():
    # 1. Asian range formation in EURUSD (00:00 to 06:45 UTC)
    t0 = pd.Timestamp('2026-10-13 00:00:00Z')
    bars = []
    for i in range(28):
        bars.append({'time': t0 + pd.Timedelta(minutes=15 * i), 'open': 1.0810, 'high': 1.0830, 'low': 1.0800, 'close': 1.0820})
    # London candles (07:15 and 07:30 UTC): sweeping Asian High
    bars.append({'time': pd.Timestamp('2026-10-13 07:15:00Z'), 'open': 1.0820, 'high': 1.0845, 'low': 1.0815, 'close': 1.0825})
    bars.append({'time': pd.Timestamp('2026-10-13 07:30:00Z'), 'open': 1.0825, 'high': 1.0850, 'low': 1.0810, 'close': 1.0815})
    df_forex = pd.DataFrame(bars)

    # Sell signal in London with Asian High sweep
    res_sell = track_session_liquidity(df_forex, 'EURUSD', pd.Timestamp('2026-10-13 07:45:00Z'), direction='SELL')
    assert res_sell['session_name'] == 'LONDON'
    assert not res_sell['is_synthetic']
    assert res_sell['asian_high'] == 1.0830
    assert res_sell['asian_low'] == 1.0800
    assert res_sell['sweep_confirmed'] is True
    assert res_sell['sweep_type'] == 'ASIAN_HIGH_SWEPT'
    assert res_sell['swept_level'] == 1.0830

    # Buy signal in London without Asian Low sweep
    res_buy = track_session_liquidity(df_forex, 'EURUSD', pd.Timestamp('2026-10-13 07:45:00Z'), direction='BUY')
    assert res_buy['sweep_confirmed'] is False
    assert res_buy['sweep_type'] == 'NONE'

    # 2. Synthetic Index 24/7 (Crash 500 Index)
    synth_bars = []
    for i in range(24):
        synth_bars.append({'time': t0 + pd.Timedelta(minutes=15 * i), 'open': 1020, 'high': 1050, 'low': 1000, 'close': 1030})
    # Current bar sweeps prior high to 1060
    synth_bars.append({'time': t0 + pd.Timedelta(minutes=15 * 24), 'open': 1030, 'high': 1060, 'low': 1025, 'close': 1035})
    df_synth = pd.DataFrame(synth_bars)

    res_synth_sell = track_session_liquidity(df_synth, 'Crash 500 Index', t0 + pd.Timedelta(minutes=15 * 25), direction='SELL')
    assert res_synth_sell['is_synthetic'] is True
    assert res_synth_sell['sweep_confirmed'] is True
    assert res_synth_sell['sweep_type'] == 'PRIOR_H4_HIGH_SWEPT'
    assert res_synth_sell['swept_level'] == 1050.0


def test_continuation_direct_touch_confirmation_and_tested_level_unblock():
    # M15 frame with level 100.0 (Support). The most recent closed candle touches 100.1 and closes at 100.2
    frame = candle_frame([(101.0, 102.0, 100.8, 101.5),
                          (101.5, 101.8, 100.1, 100.3),
                          (100.3, 100.5, 99.9, 100.2)], '15min')
    
    # Standard retest requires subsequent recovery bars
    standard = retest_confirmation(frame, 100.0, 'BUY', 1.0, allow_direct_touch=False)
    assert not standard['confirmed']
    
    # Direct touch confirms immediately upon candle close respecting level
    direct = retest_confirmation(frame, 100.0, 'BUY', 1.0, allow_direct_touch=True)
    assert direct['confirmed']
    assert direct['trigger'] == 'DIRECT_TOUCH_RETEST'
    assert direct['confirmation_index'] == len(frame) - 1




def test_fakeout_trap_candidate_and_retest_confirmation():
    from strategy.malaysian_snr.video_rules import fakeout_trap_candidate
    
    # 1. Direct unit test of fakeout_trap_candidate
    # Level = 100.0, Direction = BUY, ATR = 2.0
    # Candle pierces level down to 99.1 (depth = 0.9 / 2.0 = 0.45 ATR <= 0.60 ATR)
    # Candle opens at 100.2, closes at 100.8 (reclaims level). High = 101.0, Low = 99.1
    # Span = 1.9, rejection wick = min(100.2, 100.8) - 99.1 = 1.1 -> wick_ratio = 1.1 / 1.9 = 57.9% (>= 50%)
    class Candle:
        open = 100.2
        high = 101.0
        low = 99.1
        close = 100.8
    
    trap = fakeout_trap_candidate(Candle(), 100.0, 'BUY', 2.0, max_penetration_atr=0.60, min_wick_ratio=0.50)
    assert trap is not None
    assert trap['is_fakeout'] is True
    assert trap['penetration_atr'] == 0.45
    assert trap['wick_ratio'] >= 0.50
    assert trap['reclaimed'] is True

    # 2. Retest confirmation with Fakeout Trap
    # Frame where candle pierces 100.0 by 0.45 ATR and absorbs
    frame = candle_frame([(101.0, 102.0, 100.5, 101.5),
                          (101.5, 101.8, 100.2, 100.4),
                          (100.2, 101.0, 99.1, 100.8)], '15min')
    
    # Without fakeout trap (max_penetration = 0.35 ATR), 0.45 ATR depth is rejected
    no_trap = retest_confirmation(frame, 100.0, 'BUY', 2.0, max_penetration_atr=0.35, allow_fakeout_trap=False)
    assert not no_trap['confirmed']
    assert no_trap['reason'] == 'RETEST_PENETRATION_TOO_DEEP'

    # With fakeout trap enabled, confirms with SNR_FAKEOUT_TRAP_SWEEP trigger!
    with_trap = retest_confirmation(frame, 100.0, 'BUY', 2.0, max_penetration_atr=0.35,
                                    allow_fakeout_trap=True, max_fakeout_penetration_atr=0.60,
                                    fakeout_min_wick_ratio=0.50)
    assert with_trap['confirmed'] is True
    assert with_trap['trigger'] == 'SNR_FAKEOUT_TRAP_SWEEP'
    assert with_trap['fakeout_trap'] is True


def test_quasimodo_continuation_candidates():
    from strategy.malaysian_snr.validation import quasimodo_continuation_candidates
    # Bullish QMC:
    # Swings with radius = 1:
    # i=1: High 105 (S1 Left Shoulder)
    # i=3: Low 98 (S2 Retracement)
    # i=5: High 112 (S3 Head, > S1)
    # i=7: Low 103 (S4 Higher Low, > S2)
    # i=9: Candle closes at 114 (First BOS above S3 Head)
    values = [
        (100, 101, 99, 100),   # 0
        (100, 105, 99, 104),   # 1 High S1 = 105
        (103, 104, 100, 101),  # 2
        (101, 102, 98, 99),    # 3 Low S2 = 98
        (100, 108, 99, 107),   # 4
        (107, 112, 106, 111),  # 5 High S3 (Head) = 112
        (110, 111, 105, 106),  # 6
        (105, 106, 103, 104),  # 7 Low S4 (Higher Low) = 103
        (104, 110, 103, 109),  # 8
        (109, 115, 108, 114),  # 9 BOS close = 114 > 112
    ]
    frame = candle_frame(values, '1h')
    qmc = quasimodo_continuation_candidates(frame, radius=1)
    assert len(qmc) >= 1
    assert qmc[0]['direction'] == 'BUY'
    assert qmc[0]['shoulder'] == 105.0
    assert qmc[0]['head'] == 112.0
    assert qmc[0]['neckline'] == 98.0


def test_h1_ema_dynamic_confluence():
    from strategy.malaysian_snr.video_rules import h1_ema_dynamic_confluence
    # 60 candles around 100.0 -> EMA 50 will be close to 100.0
    frame = candle_frame([(99.5, 100.5, 99.0, 100.0)] * 60, '1h')
    
    # Level at 100.1 is right next to EMA 50 (confluent)
    res_near = h1_ema_dynamic_confluence(frame, 100.1, direction='BUY', period=50, tolerance_atr=0.40)
    assert res_near['confluence'] is True
    assert res_near['distance_atr'] <= 0.40

    # Level at 120.0 is far from EMA 50 (not confluent)
    res_far = h1_ema_dynamic_confluence(frame, 120.0, direction='BUY', period=50, tolerance_atr=0.40)
    assert res_far['confluence'] is False


def test_m15_micro_structural_stop_loss():
    provider, frames, now = market()
    # Test Malaysian SNR with micro stop enabled
    cfg = MalaysianSNRConfig(allowed_symbols=(), enable_m15_micro_stop=True,
                             m15_micro_stop_buffer_atr=0.10, m15_micro_stop_min_risk_atr=0.20)
    strat = MalaysianSNRStrategy(provider, cfg)
    res = strat.analyze_symbol('Step Index', now)
    assert res['valid'] is True
    sig = res['signal']
    assert sig['micro_stop_applied'] is True
    # Micro stop is tighter than the baseline H1 bound, yielding lower risk distance
    risk = abs(sig['entry_price'] - sig['stop_loss'])
    assert sig['tp1_price'] == pytest.approx(sig['entry_price'] + 2.0 * risk if sig['direction'] == 'BUY' else sig['entry_price'] - 2.0 * risk)


def test_msnr_runner_tiered_trailing_lock():
    from unittest.mock import Mock
    from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig

    config = LiveTradingConfig(runner_extension_enabled=True)
    engine = LiveTradingEngine(provider=Mock(), repository=Mock(), executor=Mock(), config=config)

    trade = {
        'id': 101,
        'instrument': 'Crash 1000 Index',
        'direction': 'BUY',
        'broker_position_ticket': '777888',
        'details': {}
    }
    metadata = {
        'strategy_name': 'MALAYSIAN_SNR',
        'trade_leg': 'RUNNER',
        'runner_rr': 4.0,
        'runner_extension_completed_stages': []
    }
    position = Mock()
    position.price_open = 1000.0
    position.sl = 990.0   # initial SL at 990 -> 1R risk = 10.0

    position.sl = 990.0
    def fake_move(position_ticket, stop_loss, take_profit, reason):
        position.sl = float(stop_loss)
        return {'modified': True}

    move_stop_mock = Mock(side_effect=fake_move)
    engine.executor.get_position = Mock(return_value=position)
    engine.lifecycle_manager = Mock()
    engine.lifecycle_manager.trade_executor = Mock()

    # At current_rr = 2.5: should trigger stage MSNR_LOCK_1_5R and lock +1.5R (SL = 1015.0)
    res_1 = engine._manage_runner_extension(
        trade=trade,
        position=position,
        metadata=metadata,
        initial_stop_loss=990.0,
        current_rr=2.5,
        move_stop=move_stop_mock
    )
    assert res_1['managed'] is True
    assert res_1['stage'] == 'MSNR_LOCK_1_5R'
    # Lock 1.5R -> entry 1000 + 1.5 * 10 = 1015.0
    move_stop_mock.assert_called_with(
        position_ticket='777888',
        stop_loss=1015.0,
        take_profit=1040.0,
        reason='runner_profit_lock_msnr_lock_1_5r'
    )
    assert 'MSNR_LOCK_1_5R' in metadata['runner_extension_completed_stages']

    # At current_rr = 3.5: should trigger stage MSNR_LOCK_2_5R and lock +2.5R (SL = 1025.0)
    move_stop_mock.reset_mock()
    res_2 = engine._manage_runner_extension(
        trade=trade,
        position=position,
        metadata=metadata,
        initial_stop_loss=990.0,
        current_rr=3.5,
        move_stop=move_stop_mock
    )
    assert res_2['managed'] is True
    assert res_2['stage'] == 'MSNR_LOCK_TP3'
    # Lock TP3 (3.0R) -> entry 1000 + 3.0 * 10 = 1030.0
    move_stop_mock.assert_called_with(
        position_ticket='777888',
        stop_loss=1030.0,
        take_profit=1040.0,
        reason='runner_profit_lock_msnr_lock_tp3'
    )
    assert 'MSNR_LOCK_TP3' in metadata['runner_extension_completed_stages']
