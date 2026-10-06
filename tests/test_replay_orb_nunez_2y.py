"""Replay correctness: execution ordering, partial exits and historical causality."""
import unittest
import pandas as pd
from tools.replay_orb_nunez_2y import simulate, portfolio, structural_context, context_at, Provider, ReplayStrategy
from strategy.orb.new_york_orb import NewYorkORBStrategy, ORBConfig


def candles(rows):
    df = pd.DataFrame(rows, columns=['open','high','low','close','spread'])
    df['time'] = pd.date_range('2026-01-05 15:00', periods=len(df), freq='5min', tz='UTC')
    df['tick_volume'] = 10
    return df


class ReplayTests(unittest.TestCase):
    def test_both_legs_stop_no_premature_be(self):
        result=simulate(candles([(100,105,89,91,0)]),0,'BUY',90,.01)
        self.assertEqual((result['leg1_reason'],result['leg2_reason']),('SL','SL'))
        self.assertEqual(result['net_r'],-1)

    def test_tp1_then_tp2_weighted_r(self):
        result=simulate(candles([(100,111,100.5,110,0),(110,121,109,120,0)]),0,'BUY',90,.01)
        self.assertEqual((result['leg1_reason'],result['leg2_reason']),('TP1','TP2'))
        self.assertEqual(result['net_r'],1.5)

    def test_tp1_then_be(self):
        result=simulate(candles([(100,111,100.5,110,0),(110,111,99,100,0)]),0,'BUY',90,.01)
        self.assertEqual(result['net_r'],.5)
        self.assertEqual(result['leg2_reason'],'BE')

    def test_ambiguous_stop_first(self):
        result=simulate(candles([(100,121,89,100,0)]),0,'BUY',90,.01)
        self.assertEqual(result['net_r'],-1)
        self.assertEqual(result['ambiguity_bars'],1)

    def test_ambiguous_be_before_tp2(self):
        result=simulate(candles([(100,121,99,120,0)]),0,'BUY',90,.01)
        self.assertEqual(result['net_r'],.5)
        self.assertEqual(result['ambiguity_bars'],1)

    def test_sell_ask_spread_prevents_false_target(self):
        result=simulate(candles([(100,100,89,90,200)]),0,'SELL',110,.01)
        self.assertFalse(result['closed'])
        self.assertIsNone(result['leg1_reason'])

    def test_sell_tp1_tp2(self):
        result=simulate(candles([(100,99.5,89,90,0),(90,91,79,80,0)]),0,'SELL',110,.01)
        self.assertEqual(result['net_r'],1.5)

    def test_gap_loss_exceeds_planned_risk(self):
        result=simulate(candles([(100,105,99,104,0),(80,85,79,82,0)]),0,'BUY',90,.01)
        self.assertEqual(result['net_r'],-2)

    def test_open_runner_is_not_fake_closed_win(self):
        result=simulate(candles([(100,111,101,110,0)]),0,'BUY',90,.01)
        self.assertFalse(result['closed'])
        self.assertIsNone(result['net_r'])
        self.assertEqual(result['leg1_r'],1)

    def test_event_sizing_and_partial_pnl(self):
        a=simulate(candles([(100,111,101,110,0),(110,121,109,120,0)]),0,'BUY',90,.01)
        b=simulate(candles([(100,104,89,91,0)]),0,'BUY',90,.01)
        stats,events=portfolio(pd.DataFrame([a,b]))
        self.assertAlmostEqual(stats['final_realized_balance'],10050)
        self.assertAlmostEqual(stats['peak_initial_open_risk_pct'],2)

    def test_structure_is_prefix_invariant(self):
        rows=[(100+i%4,103+i%4,97+i%4,101+i%4,0) for i in range(160)]
        df=candles(rows)
        cutoff=df.time.iloc[100]
        full=structural_context(df,15)
        truncated=structural_context(df[df.time<cutoff],15)
        self.assertEqual(context_at(full,cutoff),context_at(truncated,cutoff))

    def test_prepared_adapter_matches_live_closed_candles(self):
        df=candles([(100,105,95,101,0)]*400)
        df['time_ny']=df.time.dt.tz_convert('America/New_York')
        provider=Provider(df,.01)
        provider.index=380
        now=df.time.iloc[380]+pd.Timedelta(minutes=5)
        cfg=ORBConfig()
        actual=ReplayStrategy(provider,cfg)._prepare_candles('XAUUSD',now)
        expected=NewYorkORBStrategy(provider,cfg)._prepare_candles('XAUUSD',now)
        pd.testing.assert_frame_equal(actual,expected)


if __name__=='__main__':
    unittest.main()
