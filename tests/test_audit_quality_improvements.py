from types import SimpleNamespace
from datetime import datetime, timezone
import pandas as pd
import pytest
from strategy.ai.feature_extraction import extract_meta_features, FEATURE_NAMES
from strategy.smc.shadow_replay import replay
from reporting.trade_report_exporter import TradeReportExporter
from database.repository import TradingRepository


def test_native_pattern_scale_and_missingness():
    f=extract_meta_features(signal={'chart_pattern_strength':.72,'chart_pattern_conflict_strength_delta':.1})
    assert f['chart_pattern_strength']==.72
    assert f['chart_pattern_strength_delta']==.1
    assert f['spread_available']==0
    assert f['adx_available']==0
    g=extract_meta_features(signal={'entry_price':100.,'adx':0.,'atr':2.},market={'spread':0.})
    assert g['spread_available']==1 and g['adx_available']==1
    assert g['atr_ratio']==.02
    assert set(g)==set(FEATURE_NAMES)


def test_report_bounded_reader_and_original_survives_format_error(tmp_path):
    calls=[]
    def read(source,limit=None):
        calls.append(limit);return pd.DataFrame({'id':range(limit)})
    assert len(TradeReportExporter._bounded_read(read,'DEMO',7))==7
    assert calls==[7]
    repo=TradingRepository(tmp_path/'empty.sqlite')
    target=tmp_path/'existing.xlsx';target.write_bytes(b'original')
    exporter=TradeReportExporter(repo,target)
    def fail(**kwargs):raise RuntimeError('format failed')
    exporter._format_workbook=fail
    with pytest.raises(RuntimeError):exporter.export()
    assert target.read_bytes()==b'original'
    assert not list(tmp_path.glob('*.tmp.xlsx'))


def test_broker_close_reason_preserved(tmp_path):
    repo=TradingRepository(tmp_path/'deals.sqlite')
    trade_id=repo.create_trade({'source':'DEMO','instrument':'EURUSD','timeframe':'M5','direction':'BUY',
        'status':'OPEN','entry_price':1.1,'stop_loss':1.09,'take_profit':1.12,'risk_amount':10.,
        'broker_position_ticket':'123','details':{'metadata':{'existing':'keep'}}})
    exit_deal=SimpleNamespace(entry=1,reason=5,time=1760000000,time_msc=1760000000000,ticket=2,
        price=1.12,profit=20.,commission=0.,swap=0.,comment='tp',magic=42)
    # A later list item can be the entry deal: order cannot determine exit provenance.
    entry_deal=SimpleNamespace(entry=0,reason=3,time=1759999999,ticket=1,price=1.1,profit=0.,commission=0.,swap=0.)
    executor=SimpleNamespace(get_position=lambda ticket:None,history_for_position=lambda *a:[exit_deal,entry_deal])
    repo.sync_closed_mt5_trades(executor,source='DEMO')
    row=repo.get_trade(trade_id)
    assert row['exit_reason']=='mt5_tp'
    assert row['details']['metadata']['broker_exit']['reason']=='TP'
    assert row['details']['metadata']['existing']=='keep'


def test_shadow_replay_excludes_confirmation_and_marks_ambiguity():
    df=pd.DataFrame({'time':pd.to_datetime(['2026-09-22T10:00Z','2026-09-22T10:05Z']),
        'low':[80,89],'high':[130,121]})
    result=replay(df,confirmation_time=df.time.iloc[0],direction='BUY',entry=100,stop=90,target=120)
    assert result['outcome']=='AMBIGUOUS_BOTH_BARRIERS'
    assert not result['entry_authorized']
    assert replay(df.iloc[:1],confirmation_time=df.time.iloc[0],direction='BUY',entry=100,stop=90,target=120)['outcome']=='PENDING_BARRIERS'


def test_quarters_tolerance_comparison_never_authorizes():
    from test_external_observation_quarters import QuarterProvider, NOW
    from strategy.gold_quarters import GoldQuarterStrategy
    result=GoldQuarterStrategy(QuarterProvider()).analyze_symbol('XAUUSD',NOW)
    assert result['valid']
    shadow=result['tolerance_shadow']
    assert shadow['mode']=='SHADOW_ONLY'
    assert all(not c['entry_authorized'] for c in shadow['candidates'])
    assert all(c['atr_tolerance']<=5. for c in shadow['candidates'])
    assert result['signal']['quarter_target']==125.


def test_nan_is_missing_and_legacy_percent_normalizes():
    f=extract_meta_features(signal={'adx':float('nan'),'chart_pattern_strength':72.},market={'spread':float('nan')})
    assert f['adx_available']==0 and f['spread_available']==0
    assert f['chart_pattern_strength']==.72


def test_sell_replay_uses_ask_and_keeps_barriers():
    df=pd.DataFrame({'time':pd.to_datetime(['2026-09-22T10:05Z']), 'low':[89.], 'high':[99.]})
    result=replay(df,confirmation_time='2026-09-22T10:00Z',direction='SELL',entry=100,stop=105,target=90,spread=2.)
    assert result['outcome']=='PENDING_BARRIERS'  # Bid touched TP; ask did not.
    assert result['target']==90 and result['stop']==105
