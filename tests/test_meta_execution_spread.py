from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
import pytest
from strategy.execution.live_trading_engine import LiveTradingEngine
from strategy.ai.feature_extraction import extract_meta_features


def engine(quote):
    obj = LiveTradingEngine.__new__(LiveTradingEngine)
    obj.executor = SimpleNamespace(get_current_tick=lambda symbol: quote)
    obj.provider = SimpleNamespace(get_current_tick=lambda symbol: pytest.fail('Indicative feed must not be queried'))
    return obj


@pytest.mark.parametrize('ask,available', [(100.08, 1), (100., 1), (99., 0), (float('nan'), 0), (float('inf'), 0)])
def test_broker_spread_and_invalid_quotes(ask, available):
    obj = engine(dict(bid=100., ask=ask, time=datetime.now(timezone.utc)))
    market = obj._meta_execution_spread('EURUSD')
    features = extract_meta_features(signal={'entry_price':100., 'spread':42.}, market=market)
    assert features['spread_available'] == available
    assert market['spread_source'] == 'MT5_EXECUTION'
    if available:
        assert market['spread'] == pytest.approx(ask - 100.)
        assert market['spread_quote_time']
    else:
        assert market['spread'] is None
        assert features['spread_ratio'] == 0


@pytest.mark.parametrize('timestamp', [None, datetime.now(timezone.utc)-timedelta(minutes=4), datetime.now(timezone.utc)+timedelta(minutes=2)])
def test_missing_or_stale_timestamp_is_unknown(timestamp):
    market = engine(dict(bid=100., ask=101., time=timestamp))._meta_execution_spread('EURUSD')
    assert market['spread'] is None
    assert extract_meta_features(signal={'spread':5.}, market=market)['spread_available'] == 0


def test_broker_failure_is_unknown():
    obj = engine({})
    def unavailable(symbol):
        raise RuntimeError('offline')
    obj.executor.get_current_tick = unavailable
    assert obj._meta_execution_spread('EURUSD')['spread'] is None
    obj.executor = None
    assert obj._meta_execution_spread('EURUSD')['spread'] is None


def test_gate_persists_quote_provenance_in_audit():
    obj = engine(dict(bid=100., ask=100.08, time=datetime.now(timezone.utc)))
    obj.config = SimpleNamespace(risk_percent=1.)
    def score_signal(**kwargs):
        features = extract_meta_features(signal=kwargs['signal'], market=kwargs['market'])
        return SimpleNamespace(to_dict=lambda:dict(allowed=True, shadow=True, features=features))
    obj.meta_labeling = SimpleNamespace(score_signal=score_signal)
    obj._meta_label_cycle_decisions = []
    events = []
    obj._persist_audit_event = lambda *args, **kwargs: events.append(kwargs)
    decision = obj._meta_label_gate(symbol='EURUSD', signal={'entry_price':100.}, analysis={}, strategy_name='SMC')
    assert decision['features']['spread_ratio'] == pytest.approx(.0008)
    saved = events[0]['payload']['meta_label']['market_snapshot']
    assert saved['execution_ask'] == 100.08
    assert saved['spread_quote_time'] and saved['spread_captured_at']
    assert saved['spread_source'] == 'MT5_EXECUTION'
