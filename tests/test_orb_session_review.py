import unittest
import pandas as pd
import numpy as np
from tools.replay_orb_session_review import Simulator,fx_open,spread_context


def df(rows,start='2026-01-05 15:00Z'):
    frame=pd.DataFrame(rows,columns=['open','high','low','close','spread'])
    frame['time']=pd.date_range(start,periods=len(frame),freq='5min')
    frame['time_ny']=frame.time.dt.tz_convert('America/New_York')
    frame['tick_volume']=100
    return frame


class SessionTests(unittest.TestCase):
    def test_spread_feature_uses_previous_closed_bar(self):
        data=df([(100,101,99,100,1),(100,102,99,101,20)])
        result=Simulator('XAUUSD',.01)(data,1,'BUY',90,.01)
        self.assertAlmostEqual(result['entry_price'],100.01)
        self.assertAlmostEqual(result['spread_entry'],.01)

    def test_tp1_then_spread_protected_be(self):
        data=df([(100,101,99,100,1),(100,111,101,110,2),(110,111,99,100,5)])
        result=Simulator('XAUUSD',.01)(data,1,'BUY',90,.01)
        self.assertEqual(result['leg1_reason'],'TP1')
        self.assertEqual(result['leg2_reason'],'BE_SPREAD')
        self.assertGreater(result['be_price'],result['entry_price'])

    def test_both_legs_sl_without_be(self):
        data=df([(100,101,99,100,0),(100,104,89,90,0)])
        result=Simulator('XAUUSD',.01)(data,1,'BUY',90,.01)
        self.assertEqual((result['leg1_reason'],result['leg2_reason']),('SL','SL'))
        self.assertEqual(result['net_r'],-1)

    def test_sell_tp2(self):
        data=df([(100,101,99,100,0),(100,99,89,90,0),(90,91,79,80,0)])
        result=Simulator('XAUUSD',.01)(data,1,'SELL',110,.01)
        self.assertEqual(result['net_r'],1.5)
        self.assertEqual(result['planned_runner_rr'],2)

    def test_unplaceable_be_not_fictional_profit(self):
        data=df([(100,101,99,100,0),(100,111,99,100,1200)])
        result=Simulator('XAUUSD',.01)(data,1,'BUY',90,.01)
        self.assertEqual(result['leg2_reason'],'BE_UNPLACEABLE_SPREAD_EXIT')
        self.assertIsNone(result['be_price'])
        self.assertGreater(result['ambiguity_bars'],0)

    def test_tp2_caps_profit_if_be_cannot_be_placed(self):
        data=df([(100,101,99,100,0),(100,135,99,130,1200)])
        result=Simulator('XAUUSD',.01)(data,1,'BUY',90,.01)
        self.assertEqual(result['leg2_reason'],'TP2')
        self.assertEqual(result['net_r'],1.5)

    def test_rollover_flat_both_legs(self):
        data=df([(1.1,1.1001,1.0999,1.1,1)]*86,start='2026-01-05 19:00Z')
        # Enter at 13:10 NY after enough stable prior observations.
        data['time']=pd.date_range('2026-01-05 16:00Z',periods=len(data),freq='5min')
        data['time_ny']=data.time.dt.tz_convert('America/New_York')
        result=Simulator('EURUSD',.00001)(data,26,'BUY',1.09,.00001)
        self.assertEqual(result['leg1_reason'],'FOREX_PRE_ROLLOVER_CLOSE')
        self.assertEqual(pd.Timestamp(result['leg1_exit']).tz_convert('America/New_York').strftime('%H:%M'),'16:45')

    def test_fx_cutoff_rejects(self):
        data=df([(1.1,1.1001,1.0999,1.1,1)]*90,start='2026-01-05 16:00Z')
        simulator=Simulator('EURUSD',.00001)
        self.assertIsNone(simulator(data,38,'BUY',1.09,.00001))
        self.assertEqual(simulator.rejections['FOREX_CUTOFF_OR_ROLLOVER'],1)

    def test_missed_friday_close_uses_first_sunday_quote(self):
        data=df([(1.1,1.1001,1.0999,1.1,1)]*28,start='2026-01-09 16:00Z')
        data.loc[27,'time']=pd.Timestamp('2026-01-11 22:00Z')
        data['time_ny']=data.time.dt.tz_convert('America/New_York')
        result=Simulator('EURUSD',.00001)(data,26,'BUY',1.09,.00001)
        self.assertEqual(result['leg1_exit'],'2026-01-11 22:00:00+00:00')
        self.assertEqual(result['leg1_reason'],'FOREX_PRE_ROLLOVER_CLOSE')
        self.assertEqual(result['data_gap_events'],1)

    def test_market_weekend_and_dst(self):
        self.assertFalse(fx_open(pd.Timestamp('2026-01-09 22:00Z')))
        self.assertFalse(fx_open(pd.Timestamp('2026-01-11 21:55Z')))
        self.assertTrue(fx_open(pd.Timestamp('2026-01-11 22:00Z')))
        self.assertTrue(fx_open(pd.Timestamp('2026-07-05 21:00Z')))

    def test_spread_baseline_prefix_invariant(self):
        data=df([(1.1,1.1001,1.0999,1.1,2)]*100)
        full=spread_context(data,.00001)
        prefix=spread_context(data.iloc[:60],.00001)
        pd.testing.assert_frame_equal(full.iloc[:60],prefix)
        self.assertTrue(np.isnan(full.baseline.iloc[19]))
        self.assertAlmostEqual(full.baseline.iloc[20],.00002)

    def test_rollover_spike_excluded_from_baseline(self):
        data=df([(1.1,1.1001,1.0999,1.1,2)]*60,start='2026-01-05 18:00Z')
        data.loc[36:,'spread']=1000
        result=spread_context(data,.00001)
        self.assertAlmostEqual(result.baseline.iloc[-1],.00002)
        self.assertEqual(result.stable.iloc[-1],0)


if __name__=='__main__':unittest.main()
