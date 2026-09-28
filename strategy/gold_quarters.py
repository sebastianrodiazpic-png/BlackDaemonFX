"""Additional GOLD quarter rejection strategy, closed candles only."""
from datetime import datetime, timezone
import math
import pandas as pd
from strategy.orb.new_york_orb import is_orb_gold_symbol


class GoldQuarterStrategy:
    def __init__(self, provider, increment=25., tolerance=2., min_rr=2.):
        self.provider, self.increment, self.tolerance, self.min_rr = provider, increment, tolerance, min_rr

    def analyze_symbol(self, symbol, now_utc=None):
        now = pd.Timestamp(now_utc or datetime.now(timezone.utc))
        if now.tzinfo is None: now = now.tz_localize('UTC')
        base = {'strategy_name':'GOLD_QUARTERS','strategy_version':'quarters-rejection-v1',
                'valid':False,'action':'WAITING_GOLD_QUARTER','reason':'NO_CONFIRMED_QUARTER_REJECTION'}
        if not is_orb_gold_symbol(symbol): return {**base,'reason':'GOLD_ONLY'}
        def candles(tf, minutes, count):
            data=self.provider.get_candles(symbol,tf,count=count).copy()
            data['time']=pd.to_datetime(data.time,utc=True)
            return data[data.time+pd.Timedelta(minutes=minutes)<=now].sort_values('time').drop_duplicates('time')
        m5=candles('M5',5,40);h1=candles('H1',60,100)
        if len(m5)<16 or len(h1)<20:return {**base,'reason':'QUARTER_CONTEXT_INCOMPLETE'}
        if (now-m5.time.iloc[-1]).total_seconds()>600 or (now-h1.time.iloc[-1]).total_seconds()>7200:
            return {**base,'reason':'QUARTER_CONTEXT_STALE'}
        rejection,confirmation=m5.iloc[-2],m5.iloc[-1]
        if (confirmation.time-rejection.time).total_seconds()!=300:return {**base,'reason':'QUARTER_M5_GAP'}
        span=float(rejection.high-rejection.low)
        if span<=0:return base
        prev=m5.close.shift(1)
        atr=float(pd.concat([m5.high-m5.low,(m5.high-prev).abs(),(m5.low-prev).abs()],axis=1).max(axis=1).iloc[:-1].tail(14).mean())
        if not math.isfinite(atr) or atr<=0:return {**base,'reason':'QUARTER_ATR_INVALID'}
        entry=float(confirmation.close); low=float(h1.low.min()); high=float(h1.high.max());mid=(low+high)/2
        # Compare a bounded ATR tolerance without changing the live tolerance.
        comparisons = []
        shadow_tolerance = min(self.increment * .20, max(self.tolerance, .10 * atr))
        for side, extreme_value in [('BUY', float(rejection.low)), ('SELL', float(rejection.high))]:
            is_buy = side == 'BUY'
            quarter = round(extreme_value/self.increment)*self.increment
            wick_size = min(rejection.open,rejection.close)-rejection.low if is_buy else rejection.high-max(rejection.open,rejection.close)
            favorable_close = (rejection.close>quarter and confirmation.close>rejection.high and confirmation.close>confirmation.open) if is_buy else (rejection.close<quarter and confirmation.close<rejection.low and confirmation.close<confirmation.open)
            zone = low<=entry<mid if is_buy else mid<entry<=high
            candidate_stop = float(rejection.low)-.1*atr if is_buy else float(rejection.high)+.1*atr
            candidate_target = quarter+self.increment if is_buy else quarter-self.increment
            risk_distance = entry-candidate_stop if is_buy else candidate_stop-entry
            reward = candidate_target-entry if is_buy else entry-candidate_target
            candidate_rr = reward/risk_distance if risk_distance>0 else 0
            checks = {'wick': wick_size/span>=.45, 'favorable_close': bool(favorable_close),
                      'h1_location': bool(zone), 'rr': candidate_rr>=self.min_rr}
            comparisons.append({'direction':side, 'level':quarter,
                'distance_price':abs(extreme_value-quarter), 'distance_atr':abs(extreme_value-quarter)/atr,
                'strict_tolerance':self.tolerance, 'atr_tolerance':shadow_tolerance,
                'strict_touch':abs(extreme_value-quarter)<=self.tolerance,
                'atr_touch':abs(extreme_value-quarter)<=shadow_tolerance,
                'other_checks':checks, 'remaining_failures':[k for k,v in checks.items() if not v],
                'candidate_rr':candidate_rr,
                'shadow_conditions_pass': abs(extreme_value-quarter)<=shadow_tolerance and all(checks.values()),
                'entry_authorized':False})
        base['tolerance_shadow'] = {'mode':'SHADOW_ONLY', 'confirmation_time':confirmation.time.isoformat(),
                                    'atr':atr, 'candidates':comparisons}
        for direction,extreme in [('BUY',float(rejection.low)),('SELL',float(rejection.high))]:
            level=round(extreme/self.increment)*self.increment
            if abs(extreme-level)>self.tolerance:continue
            buy=direction=='BUY'
            wick=(min(rejection.open,rejection.close)-rejection.low) if buy else (rejection.high-max(rejection.open,rejection.close))
            favorable=(rejection.close>level and confirmation.close>rejection.high and confirmation.close>confirmation.open) if buy else (rejection.close<level and confirmation.close<rejection.low and confirmation.close<confirmation.open)
            if wick/span<.45 or not favorable:continue
            zone_ok=low<=entry<mid if buy else mid<entry<=high
            if not zone_ok:return {**base,'reason':'QUARTER_H1_LOCATION_BLOCKED'}
            stop=float(rejection.low)-.1*atr if buy else float(rejection.high)+.1*atr
            target=level+self.increment if buy else level-self.increment
            risk=entry-stop if buy else stop-entry
            reward=target-entry if buy else entry-target
            rr=reward/risk if risk>0 else 0
            if rr<self.min_rr:return {**base,'reason':'QUARTER_TARGET_RR_INSUFFICIENT','quarter_level':level,'risk_reward_ratio':rr}
            flags={'quarter_rejection':True,'m5_confirmation':True,'h1_location':True,'target_rr':True}
            signal={'strategy_name':'GOLD_QUARTERS','strategy_version':'quarters-rejection-v1',
                'direction':direction,'entry_price':entry,'entry_time':confirmation.time.isoformat(),
                'stop_loss':stop,'take_profit':target,'quarter_target':target,'quarter_level':level,
                'risk_reward_ratio':rr,'timeframe':'M5','atr':atr,'confirmations':flags,
                'confirmation_percentage':100.,'trade_score':100.,'confirmation_decision':'GOLD_QUARTER_CONFIRMED',
                'entry_location_ranges':{'H1':{'low':low,'high':high}},'passed_confirmations':list(flags)}
            return {**base,'valid':True,'action':'GOLD_QUARTER_CONFIRMED','reason':'QUARTER_REJECTION_AND_M5_CONFIRMATION','signal':signal}
        return base
