from copy import deepcopy
from types import SimpleNamespace
from unittest.mock import Mock, patch
import json
import pandas as pd
import pytest

from database.repository import TradingRepository
from marketdata.router import DerivOnlyMarketDataRouter
from strategy.malaysian_snr.history import useful_history
from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.malaysian_snr.runtime_settings import msnr_default_settings, validate_msnr_patch
from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy
from strategy.malaysian_snr.ai_policy import capture_features, score_candidate, compatibility, FEATURE_SEMANTICS, OBJECTIVE_SCHEMA, settings_signature
from strategy.malaysian_snr.model_training import train_captures
from strategy.malaysian_snr.candidate_outcomes import evaluate
from strategy.ai.meta_labeling import MetaLabelingEngine, MetaLabelingConfig
from strategy.ai.model import CalibratedLogisticModel
from strategy.ai.feature_extraction import FEATURE_SCHEMA
from test_msnr_dynamic_d1_settings import market, dashboard, api


def bars(count=80, timeframe='h'):
    return pd.DataFrame({'time':pd.date_range('2026-10-01',periods=count,freq=timeframe,tz='UTC'),
        'open':100.,'high':102.,'low':99.,'close':101.})


def test_adaptive_history_recovers_weekend_shortfall_and_respects_limit():
    provider = Mock()
    provider.get_candles.side_effect = lambda symbol,tf,count:bars(23 if count==80 else 69)
    frame, audit = useful_history(provider,'Wall Street 30','H1',80,28,pd.Timestamp('2026-10-12',tz='UTC'))
    assert len(frame)==69 and audit['sufficient']
    assert [r['requested'] for r in audit['attempts']]==[80,160]
    provider.get_candles.side_effect = lambda *args,**kwargs:bars(3)
    frame,audit = useful_history(provider,'A','H1',80,28,pd.Timestamp('2026-10-12',tz='UTC'),limit=200)
    assert not audit['sufficient'] and [r['requested'] for r in audit['attempts']]==[80,160,200]


def test_unclosed_and_partial_deriv_bars_are_never_made_complete():
    frame = bars(5)
    frame.loc[0,'time'] += pd.Timedelta(minutes=7)
    frame['complete'] = [True,True,True,False,True]
    frame.attrs['market_data_source']='DERIV_CHARTS_WEBSOCKET'
    provider = Mock(get_candles=Mock(return_value=frame))
    useful,audit = useful_history(provider,'A','H1',80,1,pd.Timestamp('2026-10-01T04:30Z'))
    assert list(useful.time)==list(frame.time.iloc[1:3])
    assert audit['attempts'][0]['partial']==1


def test_mt5_fallback_normalizes_missing_complete_and_leaves_forming_bar_open():
    deriv,mt5 = Mock(),Mock()
    deriv.get_candles.side_effect = RuntimeError('offline')
    now = pd.Timestamp.now(tz='UTC').floor('h')
    frame = bars(2);frame['time']=[now-pd.Timedelta(hours=1),now]
    mt5.get_candles.return_value=frame
    router=DerivOnlyMarketDataRouter(deriv_provider=deriv,metadata_provider=mt5)
    result=router.get_candles('X','H1',2)
    assert list(result.complete)==[True,False]
    assert result.attrs['market_data_source']=='MT5_FALLBACK'
    assert router.diagnostics('X')['latest_closed_candle_time']==frame.time.iloc[0].isoformat()


@pytest.mark.parametrize('bad',[{'history_min_h1':27},{'history_min_d1':True},
    {'history_max_request':float('inf')},{'recovery_window_minutes':7},
    {'ai_mode':'live'},{'ai_incompatible_policy':'ignore'},{'ai_min_probability':float('nan')},
    {'ai_min_probability':10**400},{'recovery_min_body_ratio':0},
    {'ai_min_net_expectancy_r':float('inf')},{'candidate_outcome_hours':0}])
def test_invalid_controls_are_rejected_without_partial_save(dashboard,bad):
    before=api(dashboard)['settings']
    import urllib.error
    with pytest.raises(urllib.error.HTTPError):
        api(dashboard,{'fractal_min_body_ratio':.4,**bad})
    assert api(dashboard)['settings']==before


def test_new_controls_persist_without_resetting_old_geometry(dashboard):
    saved=api(dashboard,{'fractal_min_body_ratio':.45,'m5_confirmation_mode':'live',
        'ai_mode':'shadow','history_min_h1':60})['settings']
    assert saved['fractal_min_body_ratio']==.45 and saved['history_min_h1']==60
    assert TradingRepository(dashboard.repository.db_path).latest_msnr_runtime_settings()==saved


def test_m5_native_confirmation_arrives_before_m15_and_shares_execution_episode():
    provider,frames,now=market()
    break_time=frames['H1'].time.iloc[-1]+pd.Timedelta(hours=1)
    m5=bars(181,'5min');m5['time']=pd.date_range(break_time-pd.Timedelta(hours=15),periods=181,freq='5min')
    m5.loc[180,['open','high','low','close']]=[102.9,103.8,102.8,103.3]
    frames['M5']=m5
    settings={**msnr_default_settings(),'additional_symbols':[], 'm5_confirmation_mode':'shadow'}
    strategy=MalaysianSNRStrategy(provider,MalaysianSNRConfig(),lambda:settings)
    early=strategy.analyze_symbol('Step Index',break_time+pd.Timedelta(minutes=5))
    assert early['valid'] and early['shadow_only'],early
    assert early['signal']['entry_timeframe']=='M5'
    later=strategy.analyze_symbol('Step Index',now)
    assert later['signal']['entry_timeframe']=='M15'
    assert later['signal']['setup_id']==early['signal']['setup_id']
    assert not later.get('shadow_only')
    settings['m5_confirmation_mode']='live'
    assert not strategy.analyze_symbol('Step Index',break_time+pd.Timedelta(minutes=5))['shadow_only']


def test_h4_fallback_requires_sufficient_neutral_d1_and_never_overrides_opposition():
    provider,frames,now=market(daily='BUY')
    frames['D1']=bars(31,'D');frames['D1']['time']=pd.date_range('2026-09-07',periods=31,freq='D',tz='UTC')
    frames['H4']=bars(40,'4h');frames['H4']['time']=pd.date_range(now.floor('4h')-pd.Timedelta(hours=160),periods=40,freq='4h')
    controls={**msnr_default_settings(),'macro_structure_mode':'live','h4_neutral_fallback_mode':'shadow',
              'm5_confirmation_mode':'off','additional_symbols':[]}
    strategy=MalaysianSNRStrategy(provider,MalaysianSNRConfig(allowed_symbols=()),lambda:controls)
    def bias(frame,*args):return 'BUY' if len(frame)==40 else None
    with patch('strategy.malaysian_snr.malaysian_snr_strategy.structural_bias',side_effect=bias):
        result=strategy.analyze_symbol('EURUSD',now)
        assert result['valid'] and result['shadow_only'],result
        assert result['signal']['h4_neutral_fallback_used']
        frames['D1']=frames['D1'].iloc[-2:]
        assert not strategy.analyze_symbol('EURUSD',now)['valid']
    with patch('strategy.malaysian_snr.malaysian_snr_strategy.structural_bias',
               side_effect=lambda frame,*args:'BUY' if len(frame)==40 else 'SELL'):
        assert not strategy.analyze_symbol('EURUSD',now)['valid']


def confirmed_capture():
    provider,_,now=market()
    signal=MalaysianSNRStrategy(provider).analyze_symbol('Step Index',now)['signal']
    quote={'planned_rr':signal['risk_reward_ratio'],'risk_percent':1.,'spread':.1,
           'spread_source':'MT5_EXECUTION','spread_quote_time':now.isoformat(),
           'execution_bid':signal['entry_price']-.1,'execution_ask':signal['entry_price']}
    return {'signal':signal,'market':quote,'observed_at':now.isoformat()}


def test_features_are_frozen_and_legacy_model_has_no_compatibility_stamp():
    capture=confirmed_capture()
    original=capture_features(capture['signal'],{},capture['market'])
    capture['signal']['evaluated_at']='2030-01-01T00:00Z'
    assert capture_features(capture['signal'],{},capture['market'])==original
    assert original['signal_open_age_seconds']==0
    assert not compatibility(CalibratedLogisticModel(),capture['signal'],msnr_default_settings())['compatible']


@pytest.mark.parametrize('mode,policy,source,allowed',[
    ('filter','block','DEMO',False),('filter','observe','DEMO',True),
    ('filter','observe','REAL',False),('shadow','block','DEMO',True)])
def test_incompatible_model_policy_is_explicit_and_demo_limited(tmp_path,mode,policy,source,allowed):
    engine=MetaLabelingEngine(MetaLabelingConfig(model_directory=str(tmp_path)),worker='MALAYSIAN_SNR')
    capture=confirmed_capture()
    settings={**msnr_default_settings(),'ai_mode':mode,'ai_incompatible_policy':policy}
    decision=score_candidate(engine,'Step Index',capture['signal'],{},capture['market'],source=source,settings=settings)
    assert decision['allowed'] is allowed
    assert decision['features']['signal_open_age_seconds']==0


def test_repeated_candidates_have_one_episode_and_immutable_first_capture(tmp_path):
    repo=TradingRepository(tmp_path/'audit.sqlite3')
    capture=confirmed_capture()
    values=dict(source='DEMO',symbol='Step Index',version=MalaysianSNRConfig().strategy_version,
        settings=msnr_default_settings(),setup_id=capture['signal']['setup_id'],variant='M15',
        state='META_LABEL_FILTER_REJECTED',reason='MSNR_AI_MODEL_INCOMPATIBLE',
        capture=capture,confirmed_at=capture['signal']['confirmation_closed_at'])
    first=repo.save_msnr_candidate(**values)
    capture2=deepcopy(capture);capture2['signal']['entry_price']=500.
    assert repo.save_msnr_candidate(**{**values,'capture':capture2})==first
    assert repo.msnr_candidates()[0]['capture']['signal']['entry_price']!=500.
    repo.save_msnr_candidate(**{**values,'variant':'M5'})
    funnel=repo.msnr_candidate_funnel()
    assert funnel['unique_setups']==1 and funnel['variants']==2 and funnel['evaluations']==3
    assert funnel['confirmed']==1 and funnel['executed']==0 and funnel['win_rate'] is None


def test_ambiguous_outcomes_and_missing_costs_are_not_training_labels():
    capture=confirmed_capture();sig=capture['signal'];entry=sig['entry_price']
    candle=bars(1,'min');candle['time']=[pd.Timestamp(capture['observed_at'])]
    candle['spread']=1.;candle['high']=sig['tp2_price']+1;candle['low']=sig['stop_loss']-1
    now=candle.time.iloc[0]+pd.Timedelta(minutes=1)
    result=evaluate(candle,capture,point=.1,now=now)
    assert result['outcome']=='AMBIGUOUS_BARRIERS' and not result['eligible_for_training']
    candle['high']=entry+.1
    result=evaluate(candle,capture,point=.1,now=now)
    assert result['outcome']=='RESOLVED' and result['spread_adjusted_r']==-1
    assert result['net_r'] is None and not result['eligible_for_training']
    verified=evaluate(candle,capture,point=.1,now=now,verified_fees_r=.02)
    assert verified['net_r']==-1.02 and verified['eligible_for_training']


def test_canonical_training_keeps_calibration_and_test_separate_and_purges_exits():
    capture=confirmed_capture();records=[]
    for i in range(150):
        c=deepcopy(capture);stamp=pd.Timestamp('2026-01-01',tz='UTC')+pd.Timedelta(hours=i)
        c['signal'].update(setup_id=str(i),confirmation_closed_at=stamp.isoformat(),entry_time=stamp.isoformat())
        outcome={'eligible_for_training':True,'net_r':2. if i%2 else -1.,
                 'closed_at':(stamp+pd.Timedelta(minutes=90 if i in (89,119) else 5)).isoformat()}
        records.append({'capture':c,'outcome':outcome,'settings':msnr_default_settings()})
    model,metrics=train_captures(records,msnr_default_settings(),strategy_version=MalaysianSNRConfig().strategy_version)
    assert model.provenance['independent_test_verified']
    assert metrics['train_samples']==89 and metrics['calibration_samples']==29 and metrics['test_samples']==30
    assert metrics['purged_samples']==2 and metrics['promotion_allowed'] is False
    assert compatibility(model,capture['signal'],msnr_default_settings())['compatible']
    assert CalibratedLogisticModel.from_dict(model.to_dict()).provenance==model.provenance
    with pytest.raises(ValueError,match='INSUFFICIENT'):
        train_captures([],msnr_default_settings(),strategy_version='old')


def test_execution_result_uses_net_money_over_actual_total_risk(tmp_path):
    repo=TradingRepository(tmp_path/'net.sqlite3')
    for leg,risk,profit in [('TP1',25.,50.),('RUNNER',25.,-2.)]:
        repo.create_trade({'instrument':'Step Index','direction':'BUY','source':'DEMO',
            'broker':'MT5','execution_key':'parent:'+leg,'status':'CLOSED',
            'entry_time':'2026-10-01T00:00:00Z','exit_time':'2026-10-01T01:00:00Z',
            'risk_amount':risk,'net_pnl':profit,'strategy_version':MalaysianSNRConfig().strategy_version})
    result=repo.msnr_closed_execution_result('parent')
    assert result['net_r']==.96 and result['eligible_for_training']
    assert result['evidence_type']=='EXECUTED_JOURNAL_NET_TWO_LEGS'
    assert repo.msnr_closed_execution_result('missing') is None


def test_full_process_audits_candidate_even_when_result_hides_analysis(tmp_path):
    from strategy.execution.live_trading_engine import LiveTradingEngine
    engine=object.__new__(LiveTradingEngine)
    controls={**msnr_default_settings(),'observe_candidate_outcomes':False}
    capture=confirmed_capture()
    analysis={'valid':True,'signal':capture['signal'],'runtime_controls':controls}
    engine.config=SimpleNamespace(bot_profile='MALAYSIAN_SNR',source='DEMO',risk_percent=1.)
    engine.repository=TradingRepository(tmp_path/'pipeline.sqlite3')
    engine.malaysian_snr_strategy=SimpleNamespace(settings_snapshot=lambda:controls)
    engine.meta_labeling=MetaLabelingEngine(MetaLabelingConfig(model_directory=str(tmp_path)),worker='MALAYSIAN_SNR')
    engine._persist_audit_event=Mock()
    engine._meta_execution_spread=Mock(return_value=capture['market'])
    def process(*args):
        engine._msnr_audit_local.analysis=analysis
        return {'action':'REJECTED_RISK','reason':'RISK_LIMIT','execution_key':'parent'}
    engine._process_symbol_impl=process
    result=engine.process_symbol('Step Index')
    assert not result.get('candidate_audit_error'),result
    rows=engine.repository.msnr_candidates()
    assert len(rows)==1 and rows[0]['last_reason']=='RISK_LIMIT'
    assert rows[0]['capture']['execution_key']=='parent'
    assert rows[0]['capture']['decision']['feature_semantics']==FEATURE_SEMANTICS
    assert engine._msnr_audit_local.analysis is None


def test_snr_generic_training_and_online_learning_never_overwrite_active_artifact(tmp_path):
    path=tmp_path/'metalabel_MALAYSIAN_SNR_MALAYSIAN_SNR.json'
    path.write_text('{"legacy":true}',encoding='utf-8')
    engine=MetaLabelingEngine(MetaLabelingConfig(model_directory=str(tmp_path)),worker='MALAYSIAN_SNR')
    assert engine.train([],strategy_name='MALAYSIAN_SNR')['active_model_changed'] is False
    assert not engine.update_online_trade({},1,strategy_name='MALAYSIAN_SNR')
    assert path.read_text(encoding='utf-8')=='{"legacy":true}'


def test_returned_provider_errors_are_counted_in_cycle_summary(capsys):
    from reporting.console_reporting_service import ConsoleReportingService
    ConsoleReportingService().summarize([{'action':'WAITING_MALAYSIAN_SNR','reason':"PROVIDER_ERROR: 'complete'"}],sync=0)
    assert 'Errores: 1' in capsys.readouterr().out


def test_observed_runner_break_even_uses_tp1_spread_plus_worker_point_offset():
    capture=confirmed_capture();sig=capture['signal'];entry=sig['entry_price']
    capture['break_even_offset_points']=2
    candles=bars(3,'min');start=pd.Timestamp(capture['observed_at'])
    candles['time']=pd.date_range(start,periods=3,freq='min')
    candles['spread']=1.
    candles['high']=[entry+.2,sig['tp1_price']+.2,entry+.6]
    candles['low']=[entry-.2,sig['tp1_price']-.3,entry+.25]
    result=evaluate(candles,capture,point=.1,now=start+pd.Timedelta(minutes=3))
    assert result['outcome']=='RESOLVED'
    assert result['leg2_r']==pytest.approx(.3/(entry-sig['stop_loss']))
    assert not result['eligible_for_training']


def test_dashboard_distinguishes_confirmed_retest_from_incompatible_ai_veto():
    from dashboard.realtime_dashboard import _build_confluence_matrix
    state={'worker_candidates':{'MALAYSIAN_SNR':{'symbol':'Step Index',
        'strategy_name':'MALAYSIAN_SNR','action':'META_LABEL_FILTER_REJECTED',
        'reason':'MSNR_AI_MODEL_INCOMPATIBLE'}}}
    row=next(r for r in _build_confluence_matrix(state) if r['symbol']=='Step Index')
    assert row['final_state']=='🟡 MODELO IA INCOMPATIBLE'
    assert 'confirmado' in row['trigger_confirmation']


def test_ai_veto_is_counted_as_rejection_in_logs(capsys):
    from reporting.console_reporting_service import ConsoleReportingService
    ConsoleReportingService().summarize([{'action':'META_LABEL_FILTER_REJECTED','reason':'MSNR_AI_MODEL_INCOMPATIBLE'}],sync=0)
    text=capsys.readouterr().out
    assert 'Señales rechazadas: 1' in text and 'Esperando/otros: 0' in text
