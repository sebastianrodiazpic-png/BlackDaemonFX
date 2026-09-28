import pandas as pd
from strategy.execution.trade_pipeline import PipelineConfig
from strategy.smc.m15_setup import build_m15_setups
from strategy.execution.live_trading_engine import LiveTradingEngine


def candles():
    d = pd.DataFrame({'time': pd.date_range('2026-09-23', periods=24, freq='15min', tz='UTC'),
                      'open': [100.0]*24, 'high': [101.0]*24,
                      'low': [99.0]*24, 'close': [99.5]*24, 'zone': ['discount']*24})
    d.loc[10, 'high'] = 103.0
    d.loc[22, ['open','high','low','close']] = [100,106,99.5,105.5]
    d.loc[23, ['open','high','low','close']] = [105,106,100,104]
    return d


def test_m15_accepts_displacement_ob_with_confirmed_pivot_break():
    d = candles()
    setups, audit = build_m15_setups(d, PipelineConfig())
    assert len(setups) == 1
    assert setups.iloc[0].setup_type == 'long'
    assert setups.iloc[0].setup_time == d.iloc[22].time + pd.Timedelta(minutes=15)
    assert audit[-1]['accepted']


def test_wrong_zone_and_invalidated_blocks_are_audited():
    d = candles(); d['zone'] = 'premium'; d.loc[23, 'close'] = 98
    setups, audit = build_m15_setups(d, PipelineConfig())
    assert setups.empty or not (setups.setup_type == 'long').any()
    assert any('M15_OB_INVALIDATED_BY_CLOSE' in x['reasons'] for x in audit)


def test_old_block_expires():
    setups, audit = build_m15_setups(candles(), PipelineConfig(max_retest_candles=0))
    assert setups.empty
    assert any('M15_OB_EXPIRED' in x['reasons'] for x in audit)


def test_sell_is_symmetric():
    d = candles(); original=d.copy()
    for a,b in [('open','open'),('close','close'),('high','low'),('low','high')]:
        d[a] = 200-original[b]
    d['zone']='premium'
    setups,_ = build_m15_setups(d,PipelineConfig())
    assert len(setups)==1 and setups.iloc[0].setup_type=='short'


def test_historical_rejection_does_not_override_current_buy():
    rejected={'direction':'SELL','trade_score':100}
    result=LiveTradingEngine._compact_symbol_result({'analysis':{'direction':'BUY',
        'diagnostics':{'m5':{'latest_rejected_candidate':rejected},
                       'm15':{'m15_block_audit':[{'accepted':False,'reasons':['M15_OB_EXPIRED']}]}}}})
    assert result['direction']=='BUY'
    assert result.get('trade_score') is None
    assert result['historical_m5_rejection']==rejected
    assert result['m15_block_audit'][0]['reasons']==['M15_OB_EXPIRED']


def test_separated_setup_keeps_m5_structure_sweep_and_location_gates():
    from test_confirmation_engine import _data, _setup
    from strategy.smc.confirmation_engine import evaluate_m5_confirmation, M5ConfirmationConfig
    d=_data(); setup=_setup(d).to_dict()
    setup.update(setup_origin='M15_DISPLACEMENT_OB', h1_location_direction='BUY',
                 zone='discount', premium_discount_ok=True, structure_break_ok=True)
    d['bos_bullish']=False; d.loc[3,'bos_bullish']=True
    d['bullish_sweep']=False; d.loc[2,'bullish_sweep']=True
    cfg=M5ConfirmationConfig(require_m5_structure_event=True, require_chart_pattern=False,
                             require_fvg=False, minimum_trade_score=70)
    def evaluate():
        return evaluate_m5_confirmation(data=d, setup=setup, retest_index=2,
                                        confirmation_index=3, direction='long', config=cfg)
    assert evaluate()['confirmation_valid']
    d.loc[3,'bos_bullish']=False
    assert 'M5_BOS_CHOCH_REQUIRED' in evaluate()['critical_confirmation_failures']
    d.loc[3,'bos_bullish']=True; d.loc[2,'bullish_sweep']=False
    assert 'liquidity_sweep' in evaluate()['critical_confirmation_failures']
    d.loc[2,'bullish_sweep']=True; setup['zone']='premium'
    assert 'premium_discount' in evaluate()['critical_confirmation_failures']


def test_pipeline_uses_supplied_m15_block_for_confirmation(monkeypatch):
    import strategy.execution.trade_pipeline as pipeline
    supplied=pd.DataFrame([dict(time=pd.Timestamp('2026-09-23T05:45Z'),
        setup_time=pd.Timestamp('2026-09-23T05:45Z'), setup_type='long',
        ob_low=99., ob_high=101., setup_origin='M15_DISPLACEMENT_OB')])
    captured={}
    def confirm(data,setups,**kwargs):
        captured['setups']=setups.copy()
        captured['config']=kwargs['confirmation_config']
        return pd.DataFrame()
    monkeypatch.setattr(pipeline,'detect_entry_confirmations',confirm)
    pipeline.run_trade_pipeline(candles(),
        PipelineConfig(require_m5_structure_event=True,require_favorable_confirmation=True),
        symbol='Step Index 200',confirmation_setups=supplied)
    pd.testing.assert_frame_equal(captured['setups'],supplied)
    assert captured['config'].require_m5_structure_event
    assert captured['config'].require_favorable_confirmation
