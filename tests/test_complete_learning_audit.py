from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
import json
import pandas as pd
import pytest
from strategy.ai.audit_indicators import audit_indicators
from strategy.ai.feature_extraction import extract_meta_features
from strategy.ai.closed_comparison import closed_comparison
from strategy.execution.live_trading_engine import LiveTradingEngine
from strategy.smc.variant_outcomes import evaluate, refresh
from database.repository import TradingRepository
from dashboard.smc_trial import record, snapshot


def candles(n=50):
    return pd.DataFrame({'time':pd.date_range('2026-09-01',periods=n,freq='5min',tz='UTC'),
        'open':[100+i for i in range(n)], 'high':[102+i for i in range(n)],
        'low':[99+i for i in range(n)], 'close':[101+i for i in range(n)]})


def test_indicators_wilder_warmup_and_no_future_leakage():
    data=candles()
    before=audit_indicators(data)
    assert pd.isna(before.atr.iloc[12])
    assert before.atr.iloc[13]==3
    assert pd.isna(before.adx.iloc[26])
    assert before.adx.iloc[27]==100
    data.loc[40:,'high']=9999
    after=audit_indicators(data)
    pd.testing.assert_frame_equal(before.iloc[:40],after.iloc[:40])


def test_timing_distinguishes_closed_bar_delay_from_processing():
    f=extract_meta_features(signal={'entry_time':'2026-09-01T10:00Z',
        'confirmation_closed_at':'2026-09-01T10:05Z','detected_at':'2026-09-01T10:06Z'}, evaluated_at='2026-09-01T10:06:02Z')
    assert f['signal_open_age_seconds']==362
    assert f['decision_delay_seconds']==62
    assert f['processing_seconds']==2
    assert f['decision_delay_available']==1
    assert 'latency_seconds' not in f
    empty=extract_meta_features(signal={},evaluated_at='2026-09-01T10:06Z')
    assert empty['decision_delay_available']==0


def test_post_fill_update_survives_database_round_trip(tmp_path):
    repo=TradingRepository(tmp_path/'audit.sqlite')
    trade=repo.create_trade({'source':'DEMO','instrument':'EURUSD','direction':'BUY','timeframe':'M5','status':'OPEN',
        'entry_price':100.,'stop_loss':90.,'take_profit':120.,'execution_key':'filled',
        'details':{'metadata':{'monitor_marker':'keep'},'original':'keep'}})
    engine=LiveTradingEngine.__new__(LiveTradingEngine);engine.repository=repo
    lifecycle=SimpleNamespace(metadata={'execution_rr_audit':{'filled_target_rr':1.9},'execution_timing':{'round_trip_seconds':.4}})
    engine._persist_post_fill_audit('filled',lifecycle)
    saved=repo.get_trade(trade)
    assert saved['details']['metadata']['execution_rr_audit']['filled_target_rr']==1.9
    assert saved['details']['metadata']['monitor_marker']=='keep'
    assert saved['details']['original']=='keep'
    assert saved['take_profit']==120.


def trade(i, status='CLOSED', pnl=10, parent='setup'):
    return {'id':i,'source':'DEMO','status':status,'entry_time':'2026-09-01T10:00Z',
        'risk_amount':10,'net_pnl':pnl,'details':{'metadata':{'parent_execution_key':parent,'bot_profile':'FOREX_1','strategy_name':'SMC'}}}


def test_closed_comparison_excludes_partial_setup_and_groups_legs():
    assert closed_comparison([trade(1),trade(2,'OPEN')],'FOREX_2')['closed_setups']==0
    report=closed_comparison([trade(1,pnl=10),trade(2,pnl=-10)],'FOREX_2')
    assert report['closed_setups']==1
    assert report['cohorts']['SMC:BASELINE_EXECUTED']['mean_net_r']==0
    assert report['missing_variant_capture']==1
    assert not report['promotion_allowed']


def candidate(observed='2026-09-01T10:05Z'):
    return {'observed_at':observed,'confirmation_time':'2026-09-01T10:00Z',
        'execution_quote':{'spread_status':'AVAILABLE','spread_source':'MT5_EXECUTION','execution_bid':100.,'execution_ask':100.,'spread_quote_time':observed},
        'plan':{'entry_price':100.,'stop_loss':90.,'take_profit':120.,'direction':'BUY'}}


def bars(high=121,low=99,time='2026-09-01T10:05Z'):
    return pd.DataFrame({'time':[pd.Timestamp(time)],'high':[high],'low':[low],'spread':[2.]})


@pytest.mark.parametrize('high,low,outcome',[(121,99,'TP'),(101,89,'SL'),(121,89,'AMBIGUOUS_BOTH_BARRIERS'),(101,99,'PENDING_BARRIERS')])
def test_shadow_outcomes_never_become_learning_labels(high,low,outcome):
    result=evaluate(bars(high,low),candidate(),.01,now='2026-09-01T10:10Z')
    assert result['outcome']==outcome
    assert not result['eligible_for_learning'] and not result['entry_authorized']


def test_replay_excludes_unclosed_missing_and_ambiguous_entry_bars():
    assert evaluate(bars(),candidate(),.01,now='2026-09-01T10:09Z')['outcome']=='PENDING_BARS'
    assert evaluate(bars(),candidate('2026-09-01T10:05:10Z'),.01,now='2026-09-01T10:10Z')['outcome']=='AMBIGUOUS_ENTRY_BAR'
    assert evaluate(bars(time='2026-09-01T10:10Z'),candidate(),.01,now='2026-09-01T10:15Z')['outcome']=='INCOMPLETE_BROKER_HISTORY'
    assert evaluate(bars(),{'plan':{}},.01)['outcome']=='MISSING_CAUSAL_PLAN'


def test_unique_setup_preserves_first_ready_and_day_history(tmp_path):
    now=datetime(2026,9,1,10,5,tzinfo=timezone.utc)
    comparison={'setup_time':'2026-09-01T09:00Z','confirmation_time':'2026-09-01T10:00Z','direction':'long','ob_low':90,'ob_high':95,
        'variants':{'test':{'remaining_critical_failures':[],'ob_respected':True}}}
    row={'strategy_name':'SMC','symbol':'EURUSD','action':'NO_M5_CONFIRMATION','setup_sequence_shadow':comparison,'shadow_plan':candidate()['plan'],'shadow_quote':candidate()['execution_quote']}
    record('FOREX_1',row,'H1_PRIMARY','STRICT',tmp_path,now)
    row['shadow_plan']={**row['shadow_plan'],'take_profit':999}
    record('FOREX_1',row,'H1_PRIMARY','STRICT',tmp_path,now+timedelta(seconds=10))
    worker=snapshot(tmp_path)['workers'][0]
    setup=next(iter(worker['unique_setups'].values()))
    assert setup['evaluations']==2 and len(setup['timeline'])==1
    assert setup['first_variant_ready']['test']['plan']['take_profit']==120
    assert list((tmp_path/'history').glob('*.json'))
    broker=SimpleNamespace(get_candles=lambda *a,**k:bars(), get_symbol_info=lambda symbol:{'point':.01})
    report=refresh('FOREX_1',broker,root=tmp_path,output_root=tmp_path/'replay')
    assert report['variants']['test']['unique_setups']==1
    assert report['variants']['test']['closed_replays']==1


def test_closed_replay_is_retained_without_recent_broker_history(tmp_path):
    now=datetime(2026,9,1,10,5,tzinfo=timezone.utc)
    comparison={'setup_time':'2026-09-01T09:00Z','confirmation_time':'2026-09-01T10:00Z','direction':'long','ob_low':90,'ob_high':95,
        'variants':{'test':{'remaining_critical_failures':[],'ob_respected':True}}}
    row={'strategy_name':'SMC','symbol':'EURUSD','action':'NO_M5_CONFIRMATION','setup_sequence_shadow':comparison,
         'shadow_plan':candidate()['plan'],'shadow_quote':candidate()['execution_quote']}
    record('FOREX_1',row,'H1_PRIMARY','STRICT',tmp_path,now)
    broker=SimpleNamespace(get_candles=lambda *a,**k:bars(),get_symbol_info=lambda symbol:{'point':.01})
    first=refresh('FOREX_1',broker,root=tmp_path,output_root=tmp_path/'replay')
    later=refresh('FOREX_1',None,root=tmp_path,output_root=tmp_path/'replay')
    assert first['variants']==later['variants']
    assert later['variants']['test']['closed_replays']==1


def test_shadow_requires_measured_entry_quote():
    c=candidate();c.pop('execution_quote')
    assert evaluate(bars(),c,.01)['outcome']=='MISSING_EXECUTABLE_ENTRY_QUOTE'
