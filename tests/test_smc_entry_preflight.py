from types import SimpleNamespace
from unittest.mock import Mock
import pandas as pd
import pytest
from strategy.smc.entry_preflight import confirmation_guard, obstacle_guard
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine

NOW = pd.Timestamp('2026-09-22T15:45:44Z')

def candles():
    return pd.DataFrame([
        {'time': f'2026-09-22T15:{minute}:00Z', 'open': 100., 'high': 102.,
         'low': 98., 'close': 100., 'bos_bearish': False, 'choch_bearish': False,
         'bos_bullish': False, 'choch_bullish': False}
        for minute in ['30', '35', '40', '45']])

def test_gbpcad_obstacle_blocks_before_one_r():
    report = obstacle_guard(1.87555, 1.878, {'SINGLE': 1.87065}, 'SELL',
        [{'type': 'OPPOSING_OB', 'low': 1.87351, 'high': 1.87378}])
    assert not report['valid']
    assert report['nearest_obstacle']['distance_r'] == pytest.approx(.7224489796)

@pytest.mark.parametrize('direction,stop,target,low,high', [
    ('BUY', 90, 120, 109, 111), ('SELL', 110, 80, 89, 91)])
def test_mirrored_obstacles_and_boundary(direction, stop, target, low, high):
    obstacle = {'low': low, 'high': high}
    assert not obstacle_guard(100, stop, {'TP': target}, direction, [obstacle])['valid']
    assert obstacle_guard(100, stop, {'TP': target}, direction, [obstacle], .9)['valid']
    assert obstacle_guard(100, stop, {'TP': target}, direction, [])['valid']

@pytest.mark.parametrize('direction,key,invalid_close', [
    ('BUY', 'choch_bearish', 97), ('SELL', 'bos_bullish', 103)])
def test_opposite_structure_and_extreme_invalidate(direction, key, invalid_close):
    data = candles()
    assert confirmation_guard(data, data.iloc[1].time, direction, NOW)['valid']
    data.loc[2, key] = True
    assert confirmation_guard(data, data.iloc[1].time, direction, NOW)['reason'] == 'SMC_M5_OPPOSITE_STRUCTURE'
    data.loc[2, key] = False
    data.loc[2, 'close'] = invalid_close
    assert confirmation_guard(data, data.iloc[1].time, direction, NOW)['reason'] == 'SMC_M5_CONFIRMATION_EXTREME_BROKEN'

def test_age_feed_and_forming_candle():
    data = candles()
    assert confirmation_guard(data, data.iloc[0].time, 'SELL', NOW)['reason'] == 'SMC_M5_CONFIRMATION_EXPIRED'
    data.loc[3, 'bos_bullish'] = True  # Unclosed candle must never veto.
    assert confirmation_guard(data, data.iloc[2].time, 'SELL', NOW)['valid']
    assert confirmation_guard(data.iloc[:2], data.iloc[1].time, 'SELL', NOW)['reason'] == 'SMC_M5_FEED_STALE'

def test_preflight_fetches_fresh_data_and_persists_rejection(monkeypatch):
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig()
    times = pd.date_range(end=pd.Timestamp.now(tz='UTC').floor('5min'), periods=4, freq='5min')
    data = candles(); data['time'] = times
    engine.provider = SimpleNamespace(get_candles=Mock(return_value=data),
        get_current_tick=Mock(return_value={'bid': 100., 'ask': 100.1}))
    engine.multi_timeframe = SimpleNamespace(_run_pipeline=lambda df, symbol: {'data': df})
    engine._persist_audit_event = Mock()
    engine._market_signal_diagnostics = lambda *a: {}
    signal = {'entry_time': times[2].isoformat(), 'm15_obstacles': [{'low': 95., 'high': 96.}]}
    report = engine._smc_entry_preflight('GBPCAD', signal, 'SELL', 100, 110, [{'name': 'SINGLE', 'take_profit': 80}])
    assert not report['valid'] and report['reason'] == 'SMC_OBSTACLE_BEFORE_MIN_R'
    engine.provider.get_candles.assert_called_once()
    engine._persist_audit_event.assert_called_once()
    assert signal['entry_preflight'] == report

def test_missing_data_fails_closed():
    engine = object.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig()
    engine._persist_audit_event = Mock()
    report = engine._smc_entry_preflight('GBPCAD', {}, 'SELL', 100, 110, [])
    assert not report['valid']
