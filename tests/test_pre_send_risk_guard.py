
import pytest
from brokers.mt5_execution import MT5ExecutionError
import brokers.mt5_execution as module

def provider():
    cls=next(c for c in vars(module).values() if isinstance(c,type) and "_validate_pre_send_risk" in c.__dict__)
    p=object.__new__(cls)
    p.get_symbol_constraints=lambda s:{"point":0.001}
    p.calculate_risk_amount=lambda **k:{"actual_risk_amount":round(abs(k["entry_price"]-k["stop_loss"])*50*k["volume"],2)}
    return p

def test_incident_rejected_before_send():
    with pytest.raises(MT5ExecutionError,match="PRE_SEND_RISK_CAP_BREACH"):
        provider()._validate_pre_send_risk({"symbol":"XAGUSDmicro","price":63.064,
            "sl":62.949,"volume":6.07,"deviation":20},"BUY",33.34992525)

@pytest.mark.parametrize("side,price,sl", [("BUY",63.054,62.949),("SELL",62.949,63.054)])
def test_buffered_risk_within_limit(side,price,sl):
    provider()._validate_pre_send_risk({"symbol":"XAGUSDmicro","price":price,
        "sl":sl,"volume":4.,"deviation":20},side,33.34992525)

def test_invalid_cap_fails_closed():
    with pytest.raises(MT5ExecutionError):
        provider()._validate_pre_send_risk({}, "BUY", float("nan"))


def test_full_order_path_does_not_send_incident():
    from types import SimpleNamespace
    p=provider()
    request={"symbol":"XAGUSDmicro","price":63.054,"sl":62.949,"volume":6.07,"deviation":20,"type_filling":0}
    p._ensure=lambda:None
    p._build_market_request_base=lambda **k:dict(request)
    p._run_order_check_with_fallback=lambda *a:{"valid":True,"request":dict(request)}
    p._current_market_price=lambda *a:63.064
    p._order_check_safe=lambda r:(SimpleNamespace(retcode=0),r,{})
    p._is_order_check_success=lambda r:True
    def no_valid_lot(*args):
        raise MT5ExecutionError("PRE_SEND_RISK_CAP_BREACH: minimum lot too large")
    p.calculate_volume=no_valid_lot
    p._order_send_safe=lambda r:pytest.fail("Order must never be sent")
    with pytest.raises(MT5ExecutionError,match="PRE_SEND_RISK_CAP_BREACH"):
        p.place_market_order("XAGUSDmicro","BUY",6.07,62.949,63.159,1,"test",
                             max_risk_amount=33.34992525)

@pytest.mark.parametrize("updated", [False,True])
def test_reviewed_release_requires_updated_provider_and_keeps_audit(tmp_path, updated):
    import json
    from types import SimpleNamespace
    from strategy.execution.live_trading_engine import LiveTradingEngine,LiveTradingConfig
    e=object.__new__(LiveTradingEngine)
    e.config=LiveTradingConfig(quarantine_path=str(tmp_path/"quarantine.json"))
    e.executor=provider() if updated else SimpleNamespace()
    record={"reason":"POST_FILL_RISK_HARD_CAP_BREACH","recoverable":False,
            "release_after_guard":"PRE_SEND_RISK_CAP_V1"}
    e._save_quarantine({"XAGUSDmicro":record,"OTHER":{"recoverable":False}})
    result=e._quarantine_result("XAGUSDmicro")
    assert (result is None) is updated
    assert "OTHER" in e._load_quarantine()
    if updated:
        assert "XAGUSDmicro" in (tmp_path/"risk_quarantine_releases.jsonl").read_text()
