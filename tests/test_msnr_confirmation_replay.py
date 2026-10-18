import numpy as np
import pandas as pd
import pytest
from tools.replay_msnr_confirmations import Provider, accelerated, config_for, simulate_native, stats
from strategy.malaysian_snr.runtime_settings import msnr_default_settings
import strategy.malaysian_snr.malaysian_snr_strategy as module


def bars(values):
    return pd.DataFrame([dict(time=pd.Timestamp('2026-01-01T00:00:00Z')+pd.Timedelta(minutes=5*i),
                             open=o, high=h, low=l, close=c, spread=s) for i,(o,h,l,c,s) in enumerate(values)])


def test_native_m5_is_closed_and_quote_uses_previous_closed_spread():
    frame = bars([(100, 101, 99, 100, 2), (100, 101, 99, 100, 999)])
    provider = Provider({'M5': frame}, {'point': .01, 'tick_size': .01})
    provider.now = frame.time.iloc[1]
    assert len(provider.get_candles('Step', 'M5'))==1
    assert provider.get_current_tick('Step')['ask']==pytest.approx(100.02)


@pytest.mark.parametrize('direction', ['BUY', 'SELL'])
def test_stop_target_collision_marked_and_conservative(direction):
    frame = bars([(100, 102.5, 97.5, 100, 0)])
    sign = 1 if direction=='BUY' else -1
    result = simulate_native(direction, 100, 100-sign, 100+2*sign, 100+4*sign, frame, .01)
    assert result['rr']==-1 and result['ambiguous']


def test_equal_targets_fill_resting_legs_before_be():
    result = simulate_native('BUY',100,99,102,102,bars([(100,102.2,99.5,102,2)]),.01)
    assert result['rr']==2 and not result['ambiguous'] and result['outcome']=='TP2'


def test_break_even_uses_tp1_spread_plus_two_points():
    frame=bars([(100.5,102.1,100.4,102,10),(101,101.5,100.1,100.5,2)])
    result=simulate_native('BUY',100,99,102,104,frame,.01)
    assert result['rr']==pytest.approx(1.06) and result['outcome']=='BE'


def test_missing_outcome_bars_censor_instead_of_fabricating_execution():
    frame=bars([(100,100.5,99.5,100,0),(100,105,98,100,0)])
    frame.loc[1,'time']+=pd.Timedelta(minutes=5)
    result=simulate_native('BUY',100,99,102,104,frame,.01)
    assert result['rr'] is None and result['outcome']=='HISTORY_GAP_CENSORED'
    assert stats([result])['conservative_ohlc']['win_pct'] is None


def test_dataset_end_does_not_become_timeout_win():
    result=simulate_native('BUY',100,99,102,104,bars([(100,101,99.5,100.8,0)]),.01)
    assert result['rr'] is None and result['outcome']=='RIGHT_CENSORED'


def test_live_preferences_not_reset_and_each_variant_changes_only_experiments():
    settings=msnr_default_settings()
    settings.update(fractal_min_body_ratio=.45, continuation_mode='live', continuation_fresh_only=False)
    base=config_for(settings,'M15')
    m5=config_for(settings,'M15_M5')
    h4=config_for(settings,'M15_H4')
    assert base.fractal_min_body_ratio==m5.fractal_min_body_ratio==.45
    assert base.enable_scenario_1_continuation and not base.continuation_fresh_only
    assert base.tp2_runner_rr==4
    assert m5.m5_confirmation_mode=='live' and m5.h4_neutral_fallback_mode=='off'
    assert h4.m5_confirmation_mode=='off' and h4.h4_neutral_fallback_mode=='live'
    assert settings['m5_confirmation_mode']=='shadow'


def test_acceleration_matches_original_indicators_and_restores_globals():
    rng=np.random.default_rng(20261012)
    close=np.cumsum(rng.normal(size=80))+100
    opening=np.r_[close[0],close[:-1]]
    frame=pd.DataFrame({'time':pd.date_range('2026-01-01',periods=80,freq='h',tz='UTC'),
        'open':opening,'close':close,'high':np.maximum(opening,close)+1,'low':np.minimum(opening,close)-1})
    original=module.compute_adx
    reference=original(frame)
    with accelerated():
        pd.testing.assert_series_equal(module.compute_adx(frame),reference)
        assert module.compute_atr(frame.iloc[:-1]).iloc[-1]!=module.compute_atr(frame).iloc[-1]
    assert module.compute_adx is original
