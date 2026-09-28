"""Offline ORB session integration. Run: python tests/test_orb_integration.py -v."""
import copy
from datetime import datetime, timezone
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
from strategy.orb.new_york_orb import NewYorkORBStrategy
from strategy.orb.asset_rules import execution_metadata, check_range_amplitude
from strategy.orb.signal_payload import log_audit_summary
from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig
from test_orb_new_york_strategy import FakeProvider, _session_candles


class TestORBNYv4Integration(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 8, 28, 13, 55, 1, tzinfo=timezone.utc)
        self.frame = FakeProvider(_session_candles(), self.now).get_candles('XAGUSD', 'M5')
        # Transform deterministic prices into a silver-like scale; no live market data.
        for col in ('open', 'high', 'low', 'close'):
            self.frame[col] = self.frame[col] / 10 + 14
        self.frame[['tick_volume', 'real_volume']] = 0
        self.provider = SimpleNamespace(get_candles=lambda *a, **kw:self.frame.copy(),
            get_current_tick=lambda _:dict(time=self.now, bid=24.58, ask=24.60))
        self.strategy = NewYorkORBStrategy(self.provider)

    def create_trade(self, direction='BUY'):
        if direction == 'SELL':
            self.frame = FakeProvider(_session_candles('SELL'),self.now).get_candles('XAGUSD','M5')
            for col in ('open','high','low','close'):
                self.frame[col] = self.frame[col] / 10 + 14
            self.frame[['tick_volume','real_volume']] = 0
        result = self.strategy.analyze_symbol('XAGUSD', self.now)
        self.assertTrue(result['valid'], result)
        signal = result['signal']
        self.metadata = {**execution_metadata(signal), 'strategy_name':'ORB_NEW_YORK',
            'trade_leg':'RUNNER', 'initial_stop_loss':signal['stop_loss'],
            'orb_tp1_target_price':signal['tp1_price']}
        self.trade = dict(id=1,instrument='XAGUSD',direction=direction,broker_position_ticket=100101,
            stop_loss=signal['stop_loss'],take_profit=signal['tp2_price'],details={'metadata':copy.deepcopy(self.metadata)})
        self.position = SimpleNamespace(price_open=signal['entry_price'],sl=signal['stop_loss'],tp=signal['tp2_price'])
        self.quote = {}
        self.moves = Mock(side_effect=self.move_stop)
        self.engine = self.new_engine()
        return signal

    def new_engine(self):
        # External boundaries only are simulated; strategy and management run their real code.
        engine = object.__new__(LiveTradingEngine)
        engine.config = LiveTradingConfig(bot_profile='ORB',break_even_offset_points=0)
        engine.provider = SimpleNamespace(get_current_tick=lambda _:dict(self.quote))
        engine.executor = SimpleNamespace(get_position=lambda _:self.position,
            get_symbol_constraints=lambda _:dict(point=.001,tick_size=.001,digits=3))
        engine.repository = SimpleNamespace(update_trade=self.persist,get_trade_by_execution_key=lambda _:None)
        return engine

    def persist(self, trade_id, changes):
        self.trade.update(copy.deepcopy(changes))

    def move_stop(self, **kwargs):
        self.assertEqual(kwargs['take_profit'],self.position.tp)
        self.position.sl = kwargs['stop_loss']
        return {'modified':True}

    def evaluate(self):
        return self.engine.process_orb_break_even_management(self.trade,self.position,self.metadata,self.moves)

    def test_range_formation_and_frozen_atr_after_restart(self):
        early = datetime(2026,8,28,13,44,59,tzinfo=timezone.utc)
        self.assertEqual(self.strategy.analyze_symbol('XAGUSD',early)['action'],'BUILDING_OPENING_RANGE')
        opening = self.strategy.analyze_symbol('XAGUSD',datetime(2026,8,28,13,45,tzinfo=timezone.utc))
        frozen = opening['atr_frozen_m5']
        expected = self.strategy._average_true_range(self.frame[self.frame.time < pd.Timestamp('2026-08-28 13:45Z')],14)
        self.assertEqual(frozen,expected)
        later = self.strategy.analyze_symbol('XAGUSD',self.now)
        self.assertEqual(later['atr_frozen_m5'],frozen)
        for t in pd.date_range('2026-08-28 13:55Z',periods=12,freq='5min'):
            self.frame.loc[len(self.frame)] = dict(time=t,open=24.58,high=24.581,low=24.579,close=24.58,tick_volume=0,real_volume=0)
        later_time=datetime(2026,8,28,14,55,tzinfo=timezone.utc)
        restarted=NewYorkORBStrategy(self.provider).analyze_symbol('XAGUSD',later_time)
        self.assertEqual(restarted['atr_frozen_m5'],frozen)
        self.assertEqual(restarted['range_amplitude'],opening['range_amplitude'])
        self.assertTrue(check_range_amplitude(24.5,24,.25,1.8)['isValid'])
        self.assertFalse(check_range_amplitude(24.5,24,.25,1.8)['allow_momentum'])

    def test_volume_payload_and_audit_survive_persistence(self):
        signal=self.create_trade()
        self.assertEqual(signal['volume_status'],'VOLUMEN_NO_DISPONIBLE_PASSTHROUGH')
        self.assertEqual(self.metadata['audit_metadata']['volume_status'],signal['volume_status'])
        self.assertTrue(self.metadata['execution_policy']['be_at_tp1'])
        audit=log_audit_summary(Mock(),signal,None,execution_status='SIMULATED_NOT_SENT')
        self.assertEqual(audit['risk_status'],'NO_CONFIRMADO')

    def test_buy_keeps_sl_until_tp1_then_covers_spread_once(self):
        signal=self.create_trade()
        target=signal['tp1_price']
        self.quote.update(bid=target-.001,ask=target+.019)
        self.assertFalse(self.evaluate()['activated'])
        self.moves.assert_not_called()
        self.assertEqual(self.position.sl,signal['stop_loss'])
        self.quote.update(bid=target,ask=target+.02)
        self.assertTrue(self.evaluate()['activated'])
        self.assertAlmostEqual(self.position.sl,signal['entry_price']+.02,places=3)
        self.engine=self.new_engine()
        self.metadata=copy.deepcopy(self.trade['details']['metadata'])
        self.assertEqual(self.evaluate()['action'],'ORB_BE_ALREADY_CONFIRMED')
        self.assertEqual(self.moves.call_count,1)

    def test_sell_uses_ask_not_bid_for_tp1(self):
        signal=self.create_trade('SELL')
        target=signal['tp1_price']
        self.quote.update(bid=target-.01,ask=target+.01)
        self.assertFalse(self.evaluate()['activated'])
        self.moves.assert_not_called()
        self.quote.update(bid=target-.02,ask=target)
        self.assertTrue(self.evaluate()['activated'])
        self.assertAlmostEqual(self.position.sl,signal['entry_price']-.02,places=3)

    def test_failed_modification_can_retry_after_retrace_and_restart(self):
        signal=self.create_trade()
        self.quote.update(bid=signal['tp1_price'],ask=signal['tp1_price']+.02)
        self.moves.side_effect=None
        self.moves.return_value={'modified':False}
        self.assertEqual(self.evaluate()['action'],'ORB_BE_MODIFICATION_FAILED')
        self.assertFalse(self.metadata['break_even_confirmed'])
        self.engine=self.new_engine()
        self.metadata=copy.deepcopy(self.trade['details']['metadata'])
        self.quote.update(bid=signal['tp1_price']-.01,ask=signal['tp1_price']+.01)
        self.moves.side_effect=self.move_stop
        self.assertTrue(self.evaluate()['activated'])

    def test_broker_ack_without_changed_stop_does_not_confirm_be(self):
        signal=self.create_trade()
        self.quote.update(bid=signal['tp1_price'],ask=signal['tp1_price']+.02)
        self.moves.side_effect=None
        self.moves.return_value={'modified':True}
        self.assertEqual(self.evaluate()['action'],'ORB_BE_AWAITING_BROKER_CONFIRMATION')
        self.assertFalse(self.metadata['break_even_confirmed'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
