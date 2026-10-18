"""Conservative two-leg observation; ambiguous OHLC never receives a win label."""
import math
import pandas as pd


def evaluate(candles, capture, *, point, now, horizon_hours=24, verified_fees_r=None):
    result = {'evidence_type':'OBSERVATION', 'eligible_for_training':False,
              'entry_authorized':False, 'cost_model':'MT5_BID_PLUS_BAR_SPREAD',
              'net_r':None, 'mfe_r':0., 'mae_r':0.}
    try:
        signal, market = capture['signal'], capture['market']
        sign = 1 if signal['direction']=='BUY' else -1
        quote_time = pd.Timestamp(market['spread_quote_time'])
        quote_time = quote_time.tz_localize('UTC') if quote_time.tzinfo is None else quote_time.tz_convert('UTC')
        observed = pd.Timestamp(capture['observed_at'])
        observed = observed.tz_localize('UTC') if observed.tzinfo is None else observed.tz_convert('UTC')
        if market.get('spread_source') != 'MT5_EXECUTION' or not -1 <= (observed-quote_time).total_seconds() <= 30:
            return {**result,'outcome':'MISSING_COSTS'}
        entry = float(market['execution_ask'] if sign==1 else market['execution_bid'])
        stop, tp1, tp2 = (float(signal[k]) for k in ('stop_loss','tp1_price','tp2_price'))
        risk = sign*(entry-stop)
        spread = float(market['execution_ask'])-float(market['execution_bid'])
        if not all(math.isfinite(v) for v in (risk,entry,stop,tp1,tp2,point,spread)) or risk<=0 or point<=0 or spread<0:
            raise ValueError('invalid plan')
        if sign*(tp1-entry)<=0 or sign*(tp2-tp1)<0:
            raise ValueError('invalid targets')
        confirmation = pd.Timestamp(signal['confirmation_closed_at'])
        if observed < confirmation:
            raise ValueError('unclosed confirmation')
    except (KeyError,TypeError,ValueError):
        return {**result,'outcome':'MISSING_CAUSAL_CAPTURE'}
    end = confirmation+pd.Timedelta(hours=horizon_hours)
    data = candles.copy()
    data['time'] = pd.to_datetime(data['time'],utc=True)
    data = data[(data.time>=observed.floor('min')) & (data.time+pd.Timedelta(minutes=1)<=now)
                & (data.time<end)].sort_values('time')
    if data.empty:
        return {**result,'outcome':'PENDING'}
    expected = observed.floor('min')
    first_done = False
    leg1_r = None
    be_stop = None
    for _,bar in data.iterrows():
        if bar.time != expected:
            return {**result,'outcome':'MISSING_HISTORY'}
        expected += pd.Timedelta(minutes=1)
        try:
            bar_spread = float(bar['spread'])*point
            low,high = float(bar.low),float(bar.high)
            if not math.isfinite(low+high+bar_spread) or high<low or bar_spread<0:
                raise ValueError()
        except (KeyError,ValueError,TypeError):
            return {**result,'outcome':'MISSING_COSTS'}
        if sign==-1:
            low,high = low+bar_spread,high+bar_spread
        favorable = high if sign==1 else low
        adverse = low if sign==1 else high
        result['mfe_r'] = max(result['mfe_r'],sign*(favorable-entry)/risk)
        result['mae_r'] = min(result['mae_r'],sign*(adverse-entry)/risk)
        sl = sign*(adverse-(be_stop if first_done else stop))<=0
        first_hit = sign*(favorable-tp1)>=0
        second_hit = sign*(favorable-tp2)>=0
        relevant = sl or (second_hit if first_done else first_hit)
        if relevant and bar.time < observed:
            return {**result,'outcome':'AMBIGUOUS_ENTRY_BAR'}
        if sl and (second_hit if first_done else first_hit):
            return {**result,'outcome':'AMBIGUOUS_BARRIERS'}
        if not first_done:
            if sl:
                leg1_r = leg2_r = -1.
            elif first_hit:
                # Mirror the worker's spread + point offset at TP1. Swap,
                # tick rounding and broker protection delays remain unverified.
                be_stop = entry+sign*(bar_spread+point*int(capture.get('break_even_offset_points',2)))
                if sign*(adverse-be_stop)<=0:
                    return {**result,'outcome':'AMBIGUOUS_TP1_BREAK_EVEN'}
                leg1_r = sign*(tp1-entry)/risk
                first_done = True
                if second_hit:
                    leg2_r = sign*(tp2-entry)/risk
                else:
                    continue
            else:
                continue
        elif sl:
            leg2_r = sign*(be_stop-entry)/risk
        elif second_hit:
            leg2_r = sign*(tp2-entry)/risk
        else:
            continue
        weighted = float(signal.get('leg1_risk_ratio',.5))*leg1_r+float(signal.get('leg2_risk_ratio',.5))*leg2_r
        net = weighted-float(verified_fees_r) if verified_fees_r is not None else None
        return {**result,'outcome':'RESOLVED', 'closed_at':(bar.time+pd.Timedelta(minutes=1)).isoformat(),
                'leg1_r':leg1_r,'leg2_r':leg2_r,'spread_adjusted_r':weighted,
                'net_r':net,'eligible_for_training':net is not None,
                'fees_verified':verified_fees_r is not None}
    return {**result,'outcome':'CENSORED' if now>=end else 'PENDING'}


def refresh(repo, provider, symbol, source='DEMO'):
    rows = repo.msnr_candidates(source=source,symbol=symbol,pending=True,limit=100)
    if not rows:
        return
    # Execution outcomes use broker Bid bars, never Deriv midpoint approximations.
    broker = getattr(provider,'reference',None) or getattr(provider,'metadata_provider',None)
    broker = broker or getattr(provider,'fallback_provider',None)
    if broker is None:
        return
    candles = broker.get_candles(symbol,'M1',count=3000)
    point = float(broker.get_symbol_info(symbol)['point'])
    now = pd.Timestamp.now(tz='UTC')
    for row in rows:
        capture = row['capture']
        result = evaluate(candles,capture,point=point,now=now,
                          horizon_hours=row['settings'].get('candidate_outcome_hours',24))
        repo.save_msnr_candidate_outcome(row['candidate_key'],result)
