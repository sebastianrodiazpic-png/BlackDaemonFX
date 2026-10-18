"""Causal detector, persistence and execution boundaries of SNR alternatives."""
from copy import deepcopy
from dataclasses import replace
from unittest.mock import patch
import urllib.error

import pandas as pd
import pytest

from test_msnr_dynamic_d1_settings import market, dashboard, api
from test_msnr_opportunity_controls import manual_engine
from database.repository import TradingRepository
from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.malaysian_snr.runtime_settings import msnr_default_settings, normalize_msnr_settings
from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy
from strategy.malaysian_snr.validation import av_levels, quasimodo_candidates
from strategy.malaysian_snr.opportunity_rules import (role_flip_candidates, gap_candidate,
    structural_bias, extended_quasimodo_candidates)


NEW_MODES = ('av_entry_mode','role_flip_mode','qm_extended_mode','macro_structure_mode','gap_mode')


def controls(**changes):
    return {**msnr_default_settings(), **dict.fromkeys(NEW_MODES,'off'),
            'continuation_mode':'off','additional_symbols_mode':'off',
            'retest_pinbar_mode':'off','breaker_pair_mode':'off',
            'session_policy':'legacy_utc','obstacle_av_definition':'engulfing',
            'h4_obstacle_mode':'off',**changes}


def test_old_preferences_migrate_without_resetting_custom_values():
    saved = normalize_msnr_settings({'fractal_min_body_ratio':.45,'additional_symbols':[],
        'additional_symbols_mode':'off','continuation_fresh_only':False})
    assert saved['fractal_min_body_ratio']==.45 and saved['additional_symbols']==[]
    assert saved['continuation_fresh_only'] is False
    assert all(saved[key]=='shadow' for key in NEW_MODES)


@pytest.mark.parametrize('change', [
    {'av_entry_definition':'pivots'}, {'av_entry_mode':True}, {'role_flip_mode':'on'},
    {'role_flip_max_changes':0}, {'role_flip_max_changes':1.5}, {'role_flip_max_changes':True},
    {'role_flip_min_displacement_atr':0}, {'role_flip_min_displacement_atr':float('inf')},
    {'qm_extended_swing_window':13}, {'qm_extended_swing_window':True},
    {'qm_extended_min_head_depth_atr':-1}, {'qm_extended_min_head_depth_atr':float('nan')},
    {'macro_bias_method':'last_candle'}, {'macro_pivot_radius':0}, {'gap_timeframe':'M5'},
    {'gap_min_size_atr':True}, {'gap_min_ticks':0}, {'gap_min_spread_multiple':11}])
def test_invalid_alternative_settings_are_atomic(dashboard, change):
    before = api(dashboard)['settings']
    with pytest.raises(urllib.error.HTTPError) as exc:
        api(dashboard,{'fractal_min_body_ratio':.40,**change})
    assert exc.value.code==400
    assert api(dashboard)['settings']==before


def test_all_controls_persist_and_restore_via_api(dashboard):
    changed = controls(av_entry_mode='live',role_flip_mode='live',role_flip_max_changes=2,
        qm_extended_swing_window=10,macro_bias_method='d1_h4_structure',gap_timeframe='H4',gap_min_ticks=4)
    saved = api(dashboard,changed)['settings']
    assert {k:saved[k] for k in changed}==changed
    assert TradingRepository(dashboard.repository.db_path).latest_msnr_runtime_settings()==saved
    assert {k:v for k,v in api(dashboard,msnr_default_settings())['settings'].items()
            if k not in ('version','updated_at')}==msnr_default_settings()


def av_market():
    provider, frames, now = market()
    h1 = frames['H1']
    h1.loc[29,['open','high','low','close']]=[106,107.2,105.9,107]
    h1.loc[30,['open','high','low','close']]=[107,107.1,106.3,106.5]
    h1.loc[38,['open','high','low','close']]=[100,102,98,101]
    h1.loc[39,['open','high','low','close']]=[101,108,101,107.5]
    frames['M15'].loc[60,['open','high','low','close']]=[107,107.6,106.9,107.4]
    return provider,frames,now


@pytest.mark.parametrize('mode,valid,shadow',[('off',False,False),('shadow',True,True),('live',True,False)])
def test_body_turns_add_real_non_engulfing_candidate_with_closed_retest(mode,valid,shadow):
    provider,frames,now = av_market()
    assert 30 not in [l['idx'] for l in av_levels(frames['H1'])]
    assert 30 in [l['idx'] for l in av_levels(frames['H1'],definition='body_turns')]
    cfg = MalaysianSNRConfig(enable_quasimodo_pattern=False,enable_scenario_3_fractal=False)
    strategy = MalaysianSNRStrategy(provider,cfg,lambda:controls(av_entry_mode=mode))
    result = strategy.analyze_symbol('Step Index',now)
    assert result['valid'] is valid,result
    if valid:
        assert result['signal']['scenario']=='ESC_1_AV_EXTENDED'
        assert result['shadow_only'] is shadow
        assert result['signal']['opportunity']['definition']=='body_turns'
        assert not strategy.analyze_symbol('Step Index',now-pd.Timedelta(minutes=1))['valid']
    assert strategy.config.av_entry_mode=='off'


def test_role_flip_requires_new_closed_break_and_respects_history_limit():
    _,frames,_ = av_market()
    frame=frames['H1'].copy()
    level={'idx':30,'type':'A_RESISTANCE','level':106.,'break_level':106.}
    frame.loc[31:38,'close']=101.
    one=role_flip_candidates(frame,[level],1,.2,4.)
    assert one[0]['direction']=='BUY' and one[0]['role_changes']==1
    frame.loc[34,'close']=107.
    # First flip -> second opposite flip -> newest third flip.
    assert role_flip_candidates(frame,[level],1,.2,4.)==[]
    assert role_flip_candidates(frame,[level],3,.2,4.)[0]['role_changes']==3
    assert role_flip_candidates(frame.iloc[:-1],[level],3,.2,4.)==[]
    frame.loc[39,'close']=106.1
    assert role_flip_candidates(frame,[level],3,.2,4.)==[]


def test_role_flip_recovers_consumed_history_without_duplicating_fresh_continuation():
    _,frames,_ = av_market()
    frame=frames['H1'].copy()
    frame.loc[34,'high']=108.
    level={'idx':30,'type':'A_RESISTANCE','level':106.,'break_level':106.}
    cfg=MalaysianSNRConfig(role_flip_mode='shadow',enable_scenario_1_continuation=True,
        enable_scenario_3_fractal=False,enable_quasimodo_pattern=False)
    strategy=MalaysianSNRStrategy(None,cfg)
    with patch('strategy.malaysian_snr.malaysian_snr_strategy.av_levels',return_value=[level]), \
         patch('strategy.malaysian_snr.malaysian_snr_strategy.compute_adx',return_value=pd.Series([25.])):
        setups=strategy._setups_at_break(frame)
        recovered=next(s for s in setups if s['scenario']=='ESC_1_ROLE_FLIP')
        assert recovered['freshness']['prior_episode']['state']=='CONSUMED'
        assert recovered['freshness']['renewed_by_closed_break'] is True
        frame.loc[34,'high']=102.
        setups=strategy._setups_at_break(frame)
        assert any(s['scenario']=='ESC_1_CONTINUATION' and not s['blocked_reason'] for s in setups)
        assert not any(s['scenario']=='ESC_1_ROLE_FLIP' for s in setups)


def qm_frame():
    frame=pd.DataFrame({'time':pd.date_range('2026-10-08',periods=31,freq='h',tz='UTC'),
                        'open':100.,'high':102.,'low':98.,'close':100.})
    for idx,price in ((20,96.),(24,95.),(28,94.)):
        frame.loc[idx,'low']=price
    for idx,price in ((22,104.),(26,103.)):
        frame.loc[idx,'high']=price
    frame.loc[30,['open','high','low','close']]=[100.,106.,99.,105.]
    return frame


def test_extended_qm_finds_non_adjacent_pattern_without_anticipating_or_repeating_break():
    frame=qm_frame()
    patterns=extended_quasimodo_candidates(frame,1,8,.2,4.)
    target=next(p for p in patterns if p['shoulder']==96. and p['head']==94. and p['neckline']==104.)
    assert target not in quasimodo_candidates(frame,1)
    assert not extended_quasimodo_candidates(frame.iloc[:-1],1,8,.2,4.)
    assert not extended_quasimodo_candidates(frame,1,8,1.,4.)
    extra=frame.iloc[-1:].copy();extra['time']+=pd.Timedelta(hours=1)
    assert not extended_quasimodo_candidates(pd.concat([frame,extra],ignore_index=True),1,8,.2,4.)


@pytest.mark.parametrize('factor,expected',[(.05,True),(.6,False)])
def test_gap_uses_material_atr_tick_and_spread_thresholds(factor,expected):
    frame=pd.DataFrame({'open':[100.,106.],'high':[105.,110.],'low':[99.,106.],'close':[104.,110.]})
    result=gap_candidate(frame,4.,factor,.1,.2,2,2.)
    assert bool(result) is expected
    assert gap_candidate(frame,4.,.05,0.,.2,2,2.) is None
    assert gap_candidate(frame,4.,.05,.1,2.,2,2.) is None
    assert gap_candidate(frame,4.,.05,1.1,.2,2,2.) is None


@pytest.mark.parametrize('field,scenario',[
    ('av_entry_mode','ESC_1_AV_EXTENDED'),('role_flip_mode','ESC_1_ROLE_FLIP'),
    ('qm_extended_mode','ESC_3_QM_EXTENDED'),('gap_mode','ESC_4_OPEN_CLOSE')])
@pytest.mark.parametrize('mode',['shadow','live'])
def test_every_alternative_keeps_execution_mode_and_original_live_signal_preference(field,scenario,mode):
    provider,frames,now=market()
    strategy=MalaysianSNRStrategy(provider,MalaysianSNRConfig(),lambda:controls(**{field:mode}))
    baseline=next(s for s in strategy._setups_at_break(frames['H1']) if s['scenario']=='ESC_3_FRACTAL')
    alternate={**deepcopy(baseline),'scenario':scenario,'variant_mode':mode,'opportunity':{'kind':scenario}}
    with patch.object(MalaysianSNRStrategy,'_compute_setups_at_break',return_value=[alternate]):
        strategy._structure_cache.clear()
        result=strategy.analyze_symbol('Step Index',now)
        assert result['valid'] and result['shadow_only'] is (mode=='shadow')
        if mode=='shadow':
            engine=manual_engine(strategy,now,'Step Index')
            assert engine.process_symbol('Step Index')['action']=='MSNR_SHADOW_SIGNAL'
            engine._process_symbol_guarded.assert_not_called()
    with patch.object(MalaysianSNRStrategy,'_compute_setups_at_break',return_value=[{**alternate,'variant_mode':'shadow'},baseline]):
        strategy._structure_cache.clear()
        assert strategy.analyze_symbol('Step Index',now)['signal']['scenario']=='ESC_3_FRACTAL'


def test_macro_structure_shadow_recovers_only_observation_and_live_fails_closed_without_bias():
    provider,frames,now=market()
    cfg=MalaysianSNRConfig(allowed_symbols=())
    settings=controls(macro_structure_mode='shadow')
    strategy=MalaysianSNRStrategy(provider,cfg,lambda:settings)
    with patch('strategy.malaysian_snr.malaysian_snr_strategy.structural_bias',return_value='BUY'):
        result=strategy.analyze_symbol('EURUSD',now)
        assert result['valid'] and result['shadow_only']
        assert result['signal']['macro_structure_observation'] is True
        settings['macro_structure_mode']='live'
        assert strategy.analyze_symbol('EURUSD',now)['shadow_only'] is False
    assert strategy.analyze_symbol('EURUSD',now)['reason']=='MACRO_STRUCTURE_UNAVAILABLE_OR_NEUTRAL'
    # Disabled synthetic veto remains disabled even with neutral structural mode.
    assert strategy.analyze_symbol('Step Index',now)['valid']
    assert structural_bias(frames['D1'],2) is None


def test_h4_macro_alignment_requires_both_confirmed_directions():
    provider,frames,now=market()
    frames['H4']=frames['H1'].copy();frames['H4']['time']=pd.date_range(now-pd.Timedelta(hours=160),periods=40,freq='4h')
    strategy=MalaysianSNRStrategy(provider,MalaysianSNRConfig(allowed_symbols=()),
        lambda:controls(macro_structure_mode='live',macro_bias_method='d1_h4_structure'))
    with patch('strategy.malaysian_snr.malaysian_snr_strategy.structural_bias',side_effect=['BUY','SELL']):
        assert strategy.analyze_symbol('EURUSD',now)['reason']=='MACRO_STRUCTURE_UNAVAILABLE_OR_NEUTRAL'
    with patch('strategy.malaysian_snr.malaysian_snr_strategy.structural_bias',return_value='BUY'):
        assert strategy.analyze_symbol('EURUSD',now)['valid']


@pytest.mark.parametrize('tf',['H1','H4'])
@pytest.mark.parametrize('mode',['shadow','live'])
def test_real_gap_scenario_confirms_m15_for_h1_and_h4_and_rejects_formation_touch(tf,mode):
    provider,frames,now=market()
    frame=frames['H1'].copy()
    frame.loc[38,['open','high','low','close']]=[100.,104.5,99.,104.]
    frame.loc[39,['open','high','low','close']]=[106.,110.,106.,110.]
    if tf=='H4':
        frame['time']=pd.date_range(now-pd.Timedelta(hours=160,minutes=15),periods=40,freq='4h')
    frames[tf]=frame
    frames['M15'].loc[60,['open','high','low','close']]=[105.,105.7,104.9,105.5]
    provider.get_symbol_info=lambda s:{'point':.1,'trade_tick_size':.1}
    provider.get_current_tick=lambda s:{'bid':105.5,'ask':105.7}
    cfg=MalaysianSNRConfig(enable_scenario_3_fractal=False,enable_quasimodo_pattern=False)
    strategy=MalaysianSNRStrategy(provider,cfg,lambda:controls(gap_mode=mode,gap_timeframe=tf,continuation_min_adx=0.))
    result=strategy.analyze_symbol('Step Index',now)
    assert result['valid'],result
    assert result['signal']['scenario']=='ESC_4_OPEN_CLOSE'
    assert result['signal']['structure_timeframe']==tf
    assert result['shadow_only'] is (mode=='shadow')
    frames[tf].loc[39,'low']=105.9
    assert not strategy.analyze_symbol('Step Index',now)['valid']


def test_structural_bias_uses_confirmed_close_swings_and_closed_bos():
    frame=qm_frame().iloc[:11].copy()
    frame['close']=[100,103,99,104,100,105,101,106,102,107,108]
    assert structural_bias(frame,1)=='BUY'
    inverted=frame.copy();inverted['close']=200-frame.close
    assert structural_bias(inverted,1)=='SELL'


def test_primary_live_candidate_collects_later_shadow_without_losing_live_entry():
    provider,frames,now=market()
    strategy=MalaysianSNRStrategy(provider,MalaysianSNRConfig(),lambda:controls(qm_extended_mode='shadow'))
    baseline=next(s for s in strategy._setups_at_break(frames['H1']) if s['scenario']=='ESC_3_FRACTAL')
    shadow={**deepcopy(baseline),'scenario':'ESC_3_QM_EXTENDED','variant_mode':'shadow'}
    with patch.object(MalaysianSNRStrategy,'_compute_setups_at_break',return_value=[baseline,shadow]):
        strategy._structure_cache.clear()
        result=strategy.analyze_symbol('Step Index',now)
    assert result['signal']['scenario']=='ESC_3_FRACTAL'
    assert result['shadow_candidates'][0]['signal']['scenario']=='ESC_3_QM_EXTENDED'


def test_gap_avoids_quote_requests_when_no_material_separation_exists():
    provider,_,now=market()
    provider.get_symbol_info=lambda s:pytest.fail('No gap requires no additional market metadata')
    provider.get_current_tick=lambda s:pytest.fail('No gap requires no additional quote')
    strategy=MalaysianSNRStrategy(provider,MalaysianSNRConfig(),lambda:controls(gap_mode='shadow'))
    result=strategy.analyze_symbol('Step Index',now)
    assert result['valid'] and result['gap_data_reason']=='GAP_NO_MATERIAL_SEPARATION'


def test_structural_observations_are_preserved_by_compact_audit():
    from strategy.execution.live_trading_engine import LiveTradingEngine
    result={'strategy_name':'MALAYSIAN_SNR','signal':{'strategy_name':'MALAYSIAN_SNR'},
        'shadow_candidates':[{'shadow_only':True,'signal':{
            'setup_id':'new-observation','scenario':'ESC_3_QM_EXTENDED','direction':'BUY',
            'opportunity':{'kind':'QM_EXTENDED'},'entry_price':100.,'stop_loss':98.,
            'tp1_price':104.,'tp2_price':106.}}]}
    compact=LiveTradingEngine._compact_symbol_result({'analysis':result})
    assert compact['shadow_candidates'][0]['setup_id']=='new-observation'
    assert compact['shadow_candidates'][0]['execution_mode']=='SHADOW'
    assert compact['shadow_candidates'][0]['tp1_price']==104.
