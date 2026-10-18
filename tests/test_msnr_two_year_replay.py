import numpy as np
import pandas as pd
import pytest
from types import SimpleNamespace
from strategy.malaysian_snr.validation import quasimodo_candidates, active_av_levels
from tools.replay_msnr_two_year_comparison import fast_quasimodo, fast_active_av_levels, simulate_buffered, metrics, ClosedProvider, verified_closed, replay, install_acceleration, restore, memoized_indicator
import strategy.malaysian_snr.malaysian_snr_strategy as current
from strategy.malaysian_snr.config import MalaysianSNRConfig


def test_vectorized_qm_preserves_confirmed_pivots_and_first_bos():
    rng=np.random.default_rng(119)
    for radius in (1,2,3):
        for size in (28,78,79,80):
            for _ in range(25):
                close=np.round(np.cumsum(rng.normal(size=size)),2)
                opening=np.r_[close[0],close[:-1]]
                frame=pd.DataFrame({'time':pd.date_range('2024-01-01',periods=size,freq='h',tz='UTC'),
                                    'open':opening,'close':close,
                                    'high':np.maximum(opening,close)+rng.integers(0,3,size=size),
                                    'low':np.minimum(opening,close)-rng.integers(0,3,size=size)})
                assert fast_quasimodo(frame,radius)==quasimodo_candidates(frame,radius)
                assert fast_active_av_levels(frame)==active_av_levels(frame)


@pytest.mark.parametrize('direction',('BUY','SELL'))
def test_intrabar_ambiguity_and_be_spread_buffer_are_adverse(direction):
    sign=1 if direction=='BUY' else -1
    # Sell bid values are shifted so identical executable ask geometry is tested.
    shift=.1 if direction=='SELL' else 0.
    opening=np.array([100.-shift])
    high=np.array([102.1 if sign==1 else 100.2])-shift
    low=np.array([99.8 if sign==1 else 97.9])-shift
    result=simulate_buffered(direction,100.,100.-sign,100.+2*sign,100.+3*sign,opening,high,low,opening,np.array([.1]))
    assert result[1]=='TP1+BE_AMBIGUOUS'
    assert result[0]==pytest.approx(1.075)


def test_right_boundary_is_censored_instead_of_counted_as_win():
    rr,outcome,bars=simulate_buffered('BUY',100.,99.,102.,103.,np.array([100.]),np.array([100.5]),np.array([99.5]),np.array([100.2]),np.array([0.]))
    assert outcome=='RIGHT_CENSORED'
    result=metrics([{'rr':rr,'outcome':outcome,'exit_time':'2026-10-11','time':'2026-10-11','symbol':'Step Index'}])
    assert result['trades']==0 and result['win_pct'] is None and result['censored_trades']==1


@pytest.mark.parametrize('direction',('BUY','SELL'))
def test_equal_targets_close_both_legs_before_be_can_move(direction):
    sign=1 if direction=='BUY' else -1
    high=np.array([102.1 if sign==1 else 100.2])
    low=np.array([99.8 if sign==1 else 97.9])
    reward,outcome,bars=simulate_buffered(direction,100.,100.-sign,100.+2*sign,100.+2*sign,np.array([100.]),high,low,np.array([100.]),np.array([0.]))
    assert outcome=='TP2' and reward==pytest.approx(2.) and bars==1


@pytest.mark.parametrize('direction',('BUY','SELL'))
@pytest.mark.parametrize('invalid',(True,False))
def test_initial_stop_is_checked_against_exit_quote_not_entry_quote(direction,invalid):
    stop=100.05 if invalid else 99.95 if direction=='BUY' else 100.15
    class Signal:
        def __init__(self,provider,cfg):
            pass
        def analyze_symbol(self,symbol,now_utc):
            return {'valid':True,'signal':{'direction':direction,'stop_loss':stop,'runner_rr':2.5,'scenario':'QUOTE_TEST','atr':1.}}
    module=SimpleNamespace(MalaysianSNRStrategy=Signal)
    frame=pd.DataFrame({'time':pd.date_range('2024-01-01',periods=2,freq='15min',tz='UTC'),
                        'open':100.,'high':100.5,'low':99.5,'close':100.})
    cfg=MalaysianSNRConfig(allowed_symbols=())
    trades,details=replay({'symbol':'QUOTE_TEST','fallback_spread':.1},{'M15':frame},module,cfg,
                         pd.Timestamp('2024-01-01T00:15:00Z'),pd.Timestamp('2024-01-01T00:16:00Z'),accelerated=False,screen=False)
    assert len(trades)==(0 if invalid else 1)
    if invalid:
        assert details['counters']['INVALID_INITIAL_SL_QUOTE']==1


def test_provider_excludes_forming_candle_at_exact_close_boundary():
    frame=pd.DataFrame({'time':pd.date_range('2024-01-01',periods=3,freq='15min',tz='UTC'),'open':[1,2,3],'high':[1,2,3],'low':[1,2,3],'close':[1,2,3]})
    provider=ClosedProvider({'M15':frame})
    provider.now=pd.Timestamp('2024-01-01T00:30:00Z')
    closed=provider.get_candles('test','M15',60)
    assert closed.close.tolist()==[1,2]
    assert verified_closed(closed,'M15',provider.now) is closed
    with pytest.raises(AssertionError):
        verified_closed(frame,'M15',provider.now)


def test_shared_indicator_cache_keeps_distinct_causal_prefixes_separate():
    frame=pd.DataFrame({'time':pd.date_range('2024-01-01',periods=80,freq='h',tz='UTC'),
                        'open':np.arange(80.),'high':np.arange(80.)+3,'low':np.arange(80.)-2,'close':np.arange(80.)+1})
    frame.loc[0,['high','low']]=[100.,-100.]
    cache={}
    wrapped=memoized_indicator(current.compute_adx,'adx',cache)
    full=wrapped(frame).iloc[-1]
    shortened=wrapped(frame.iloc[1:].reset_index(drop=True)).iloc[-1]
    assert full==current.compute_adx(frame).iloc[-1]
    assert shortened==current.compute_adx(frame.iloc[1:].reset_index(drop=True)).iloc[-1]
    assert len(cache)==2


@pytest.mark.parametrize('minutes',(15,45,60,75,90))
@pytest.mark.parametrize('direction',('BUY','SELL'))
def test_screened_replay_preserves_actual_signal_through_h1_rollover(minutes,direction):
    h1=pd.DataFrame({'time':pd.date_range('2026-10-08',periods=40,freq='h',tz='UTC'),
                     'open':100.,'high':102.,'low':98.,'close':101.})
    h1.loc[37,['open','high','low','close']]=[100,103,99,101]
    h1.loc[38,['open','high','low','close']]=[100,102,97,100.5]
    h1.loc[39,['open','high','low','close']]=[99,105,98,104]
    broke=h1.time.iloc[-1]+pd.Timedelta(hours=1)
    before=pd.DataFrame({'time':pd.date_range(broke-pd.Timedelta(hours=15),periods=60,freq='15min'),
                         'open':100.,'high':102.,'low':98.,'close':101.})
    after=pd.DataFrame({'time':pd.date_range(broke,periods=minutes//15,freq='15min'),
                        'open':105.4,'high':106.,'low':105.2,'close':105.8})
    after.loc[len(after)-1,['open','high','low','close']]=[102.9,103.8,102.8,103.3]
    if minutes>=60:
        h1=pd.concat([h1,pd.DataFrame([{'time':broke,'open':105.4,'high':106.,'low':105.2,'close':105.8}])],ignore_index=True)
    confirmed=broke+pd.Timedelta(minutes=minutes)
    future=pd.DataFrame({'time':pd.date_range(confirmed,periods=4,freq='15min'),
                         'open':103.3,'high':104.,'low':96.,'close':100.})
    m15=pd.concat([before,after,future],ignore_index=True)
    if direction=='SELL':
        def mirror(frame):
            return frame.assign(open=200-frame.open,close=200-frame.close,high=200-frame.low,low=200-frame.high)
        h1,m15=mirror(h1),mirror(m15)
    frames={'H1':h1,'M15':m15}
    cfg=MalaysianSNRConfig(allowed_symbols=(),enable_daily_storyline_filter=False,enable_d1_storyline_levels=False)
    row={'symbol':'Step Index','point':0.,'fallback_spread':0.}
    end=confirmed+pd.Timedelta(minutes=15)
    reference,_=replay(row,frames,current,cfg,broke,end,accelerated=False,screen=False)
    original=install_acceleration(current)
    try:
        optimized,_=replay(row,frames,current,cfg,broke,end)
    finally:
        restore(current,original)
    assert len(reference)==1
    assert reference[0]['direction']==direction
    assert reference[0]['time']==str(confirmed)
    assert optimized==reference
