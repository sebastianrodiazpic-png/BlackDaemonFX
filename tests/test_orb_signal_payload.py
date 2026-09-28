from unittest.mock import Mock
from datetime import datetime, timezone
from strategy.orb.signal_payload import build_signal_payload, log_audit_summary
from strategy.orb.asset_rules import execution_metadata
from strategy.orb.new_york_orb import NewYorkORBStrategy
from test_orb_new_york_strategy import FakeProvider, _session_candles


def test_payload_preserves_precision_and_policy():
    p=build_signal_payload('BUY',1.12345678,1.1,1.15,1.2,'ALTA')
    assert p['entry_price']==1.12345678
    assert p['execution_policy']==dict(fixed_targets=True,be_at_tp1=True,be_protects_spread=True)
    assert not p['audit_metadata']['quality_is_probability']
    assert 'runner_dynamic' not in p and 'tp3_4r' not in p


def test_real_strategy_payload_persists():
    now=datetime(2026,8,28,13,55,1,tzinfo=timezone.utc)
    signal=NewYorkORBStrategy(FakeProvider(_session_candles(),now)).analyze_symbol('US30',now)['signal']
    meta=execution_metadata(signal)
    assert meta['tp1_price']==signal['entry_price']+(signal['entry_price']-signal['stop_loss'])
    assert meta['tp2_price']==signal['take_profit']
    assert meta['audit_metadata']['atr_frozen_m5']==signal['atr_frozen_m5']
    assert meta['execution_policy']['be_at_tp1']


def test_audit_distinguishes_unchecked_risk_from_approval_and_execution():
    p=build_signal_payload('SELL',100,110,90,80,'NO_CLASIFICADA')
    logger=Mock()
    assert log_audit_summary(logger,p)['status']=='PENDIENTE_DE_VALIDACION'
    assert log_audit_summary(logger,p,False)['status']=='RECHAZADA_POR_RIESGO'
    r=log_audit_summary(logger,p,True,execution_status='DRY_RUN_VALIDATED')
    assert r['risk_status']=='APROBADO'
    assert r['execution_status']=='DRY_RUN_VALIDATED'


def test_worker_attaches_structured_audit(monkeypatch):
    from contextlib import nullcontext
    from types import SimpleNamespace
    from strategy.execution.live_trading_engine import LiveTradingEngine
    from strategy.execution import active_position_guard
    monkeypatch.setattr(active_position_guard,'symbol_cycle_lock',lambda _:nullcontext(True))
    engine=object.__new__(LiveTradingEngine)
    engine.provider=SimpleNamespace(resolve_symbol=lambda s:s)
    payload=build_signal_payload('BUY',100,90,110,120,'ALTA')
    payload['strategy_name']='ORB_NEW_YORK'
    engine._process_symbol_guarded=lambda *a:dict(action='OPERACION_RECHAZADA_POR_RIESGO',analysis={'signal':payload})
    result=engine.process_symbol('US30')
    assert result['orb_audit_summary']['risk_status']=='RECHAZADO'
    assert result['orb_audit_summary']['technical_status']=='VALIDA'
