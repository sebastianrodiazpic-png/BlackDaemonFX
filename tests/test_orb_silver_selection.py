from types import SimpleNamespace
from unittest.mock import Mock
import pandas as pd
import pytest
from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig

ACCOUNT={'equity':10000.,'balance':12000.,'free_margin':5000.}

def engine(risks=None):
    risks=risks or {'XAGUSD':40.,'XAGUSDmicro':48.}
    e=object.__new__(LiveTradingEngine)
    e.config=LiveTradingConfig(orb_enabled=True)
    e._orb_session_is_active=lambda *args:True
    e._account_and_guard=lambda:ACCOUNT
    e._persist_audit_event=Mock()
    e.orb_strategy=SimpleNamespace(analyze_symbol=lambda symbol:{'valid':True,'signal':{
        'direction':'BUY','stop_loss':90.,'risk_reward_ratio':2.}})
    e._meta_execution_spread=lambda symbol:{'spread_status':'AVAILABLE','spread_source':'MT5_EXECUTION',
        'spread_quote_time':pd.Timestamp.now(tz='UTC').isoformat(),'execution_bid':100.,'execution_ask':100.1}
    def sizing(symbol,direction,entry,stop,budget):
        actual=risks[symbol]
        if actual>budget: raise ValueError('min lot exceeds budget')
        return {'volume':actual/10.,'actual_risk_amount':actual}
    e.executor=SimpleNamespace(normalize_market_stops=lambda *args,**kw:{'valid':True,'entry_price':100.1,'stop_loss':90.},
        risk_buffered_entry_price=lambda symbol,direction,entry,deviation:entry+.02,
        calculate_volume=sizing,calculate_risk_amount=lambda **kw:{'actual_risk_amount':.5},
        calculate_margin_amount=lambda **kw:{'margin_required':100.},
        check_market_order=lambda *args:{'valid':True})
    return e


def test_better_fit_wins_independent_of_iteration_order():
    for symbols in [['XAGUSD','XAGUSDmicro'],['XAGUSDmicro','XAGUSD']]:
        e=engine();report=e._prepare_orb_silver_selection(symbols)
        assert report['selected_symbol']=='XAGUSDmicro'
        best=[r for r in report['evaluations'] if r['symbol']=='XAGUSDmicro'][0]
        assert best['actual_total_risk']==96. and best['actual_risk_percent']==.96
        assert best['legs']==2 and best['risk_budget']==100.
        e._persist_audit_event.assert_called_once()


def test_normal_contract_can_win():
    e=engine({'XAGUSD':48.,'XAGUSDmicro':40.})
    assert e._prepare_orb_silver_selection(['XAGUSDmicro','XAGUSD'])['selected_symbol']=='XAGUSD'


def test_tie_prefers_lower_spread_cost():
    e=engine({'XAGUSD':48.,'XAGUSDmicro':48.})
    e.executor.calculate_risk_amount=lambda **kw:{'actual_risk_amount':1. if kw['symbol']=='XAGUSD' else .1}
    assert e._prepare_orb_silver_selection(['XAGUSD','XAGUSDmicro'])['selected_symbol']=='XAGUSDmicro'


def test_neither_contract_fits_means_no_selection():
    e=engine({'XAGUSD':110.,'XAGUSDmicro':110.})
    report=e._prepare_orb_silver_selection(['XAGUSD','XAGUSDmicro'])
    assert report['selected_symbol'] is None and report['reason']=='NO_VIABLE_SILVER_CONTRACT'


def test_min_lot_can_use_existing_single_fallback_under_cap():
    e=engine({'XAGUSD':60.,'XAGUSDmicro':110.})
    report=e._prepare_orb_silver_selection(['XAGUSD','XAGUSDmicro'])
    assert report['selected_symbol']=='XAGUSD'
    assert report['evaluations'][0]['legs']==1
    assert report['evaluations'][0]['actual_total_risk']==60.


def test_configured_higher_risk_is_capped_and_lower_risk_respected():
    e=engine();e.config.orb_risk_percent=3.
    assert e._evaluate_orb_silver_contract('XAGUSDmicro',ACCOUNT)['risk_budget']==100.
    e.config.orb_risk_percent=.5
    r=e._evaluate_orb_silver_contract('XAGUSD',ACCOUNT)
    assert r['risk_budget']==50. and r['actual_total_risk']<=50.


@pytest.mark.parametrize('failure',['margin','quote','order_check'])
def test_invalid_execution_not_selected(failure):
    e=engine()
    if failure=='margin':e.executor.calculate_margin_amount=lambda **kw:{'margin_required':6000.}
    if failure=='quote':e._meta_execution_spread=lambda symbol:{'spread_status':'UNAVAILABLE'}
    if failure=='order_check':e.executor.check_market_order=lambda *args:{'valid':False}
    assert e._prepare_orb_silver_selection(['XAGUSD','XAGUSDmicro'])['selected_symbol'] is None

def test_live_plan_caps_silver_operation_at_one_percent():
    from test_daemon_risk_target_policy import Provider, Repo, Executor, Analyzer
    repo=Repo();repo.trade_history_dataframe=lambda **kw:pd.DataFrame()
    e=LiveTradingEngine(provider=Provider(),repository=repo,executor=Executor(),
        config=LiveTradingConfig(orb_enabled=True,orb_risk_percent=2.,execution_enabled=False,
            validate_order_in_dry_run=False,max_entry_drift_r=None))
    class Orb:
        config=SimpleNamespace(one_signal_per_session=True)
        def analyze_symbol(self,symbol):
            data=Analyzer().analyze_symbol(symbol)
            data['signal'].update(strategy_name='ORB_NEW_YORK',orb_session_date='2026-09-24')
            return data
    e.orb_strategy=Orb()
    result=e.process_symbol('XAGUSDmicro')
    assert result['action']=='DRY_RUN_VALIDATED',result
    assert result['risk_amount']==100. and result['risk_percent']==1.
    assert sum(leg['risk_amount'] for leg in result['legs'])==100.
