import copy
from test_orb_momentum import evaluate
from dashboard.orb_audit import record,snapshot
from strategy.execution.live_trading_engine import LiveTradingEngine


def test_missing_volume_shadow_does_not_authorize_live_entry():
    result=evaluate(change={'tick_volume':0})
    audit=result['orb_audit']['momentum']
    assert not result['valid']
    assert audit['volume_status']=='UNAVAILABLE_OR_ZERO'
    assert result['reason'].startswith('ORB_MOMENTUM_REJECTED:')
    assert audit['variants']['EXT_0.50_MISSING_VOLUME_SHADOW']['momentum_checks_pass']
    assert all(not x['entry_authorized'] for x in audit['variants'].values())


def test_volume_exception_never_removes_body_requirement():
    r=evaluate(change={'tick_volume':0,'open':106.1})
    assert all('MOMENTUM_BODY_TOO_SMALL' in x['remaining_failures'] for x in r['orb_audit']['momentum']['variants'].values())


def test_compact_audit_preserves_range_and_unique_candidate(tmp_path):
    result=evaluate(change={'tick_volume':0})
    compact=LiveTradingEngine._compact_symbol_result({'symbol':'US500','analysis':result,'action':result['action'],'reason':result['reason']})
    assert len(compact['orb_audit']['opening_candles'])==3
    assert compact['orb_audit']['range_start'].endswith('-04:00')
    record(compact,tmp_path);record(compact,tmp_path)
    saved=snapshot(tmp_path)
    assert len(saved['candidates'])==1
    first=copy.deepcopy(next(iter(saved['candidates'].values())))
    compact['orb_audit']['momentum']['body_ratio']=0
    record(compact,tmp_path)
    assert next(iter(snapshot(tmp_path)['candidates'].values()))==first
