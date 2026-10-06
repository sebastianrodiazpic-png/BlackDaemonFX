"""Read-only ORB replay. Never sends orders or changes live strategy settings.

The requested two-year window is audited, never inferred from an H1 dataset.
Research definitions are explicit approximations until source videos are supplied.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from strategy.orb import new_york_orb as orb
from strategy.orb.asset_rules import audit_volume_confirmation, check_range_amplitude

SYMBOLS = ['XAUUSD', 'XAGUSD', 'US Oil', 'UK Brent Oil', 'US Tech 100',
           'Wall Street 30', 'US SP 500', 'BTCUSD', 'EURUSD']
OUT = ROOT / 'storage/analysis/orb_nunez_2y'
START = pd.Timestamp('2024-10-03', tz='UTC')
END = pd.Timestamp('2026-10-03', tz='UTC')
VARIANTS = ['CURRENT', 'EXPANDED', 'HTF', 'SWEEP', 'HTF_SWEEP']


def filename(symbol):
    return symbol.replace(' ', '_') + '_M5.csv'


def fetch():
    """Fetch bounded intervals, reject MT5 bars outside each requested interval."""
    import MetaTrader5 as mt5
    cache = OUT / 'history'
    cache.mkdir(parents=True, exist_ok=True)
    if not mt5.initialize():
        raise RuntimeError(f'MT5 initialization failed: {mt5.last_error()}')
    audit = {}
    try:
        for symbol in SYMBOLS:
            info = mt5.symbol_info(symbol)
            if info is None:
                audit[symbol] = {'status': 'SYMBOL_UNAVAILABLE'}
                continue
            pieces, rejected, errors = [], 0, []
            for left in pd.date_range(START, END, freq='30D'):
                right = min(left + pd.Timedelta(days=30), END)
                rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_M5,
                                            left.to_pydatetime(), right.to_pydatetime())
                if rates is None:
                    errors.append({'start': str(left), 'error': str(mt5.last_error())})
                    continue
                part = pd.DataFrame(rates)
                part['time'] = pd.to_datetime(part.time, unit='s', utc=True)
                valid = (part.time >= left) & (part.time < right)
                rejected += int((~valid).sum())
                pieces.append(part[valid])
            full = pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame()
            if not full.empty:
                full = full.drop_duplicates('time').sort_values('time')
                full.to_csv(cache / filename(symbol), index=False)
            audit[symbol] = {'point': info.point, 'digits': info.digits,
                             'bars': len(full), 'out_of_interval_rejected': rejected,
                             'errors': errors, 'server_maxbars': mt5.terminal_info().maxbars}
            print('FETCH', symbol, len(full), 'rejected', rejected, flush=True)
    finally:
        mt5.shutdown()
    (OUT / 'fetch_audit.json').write_text(json.dumps(audit, indent=2), encoding='utf-8')


def load(symbol):
    paths = [ROOT / 'data/historical' / filename(symbol),
             ROOT / 'data/forex_historical' / filename(symbol),
             OUT / 'history' / filename(symbol)]
    frames, provenance = [], []
    for path in paths:
        if path.exists():
            frame = pd.read_csv(path)
            frame['time'] = pd.to_datetime(frame.time, utc=True)
            frames.append(frame)
            provenance.append({'file': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    if not frames:
        return pd.DataFrame(), {'status': 'NO_DATA', 'full_two_years': False, 'sources': []}
    df = pd.concat(frames, ignore_index=True).drop_duplicates('time', keep='last').sort_values('time')
    df = df[(df.time >= START - pd.Timedelta(days=30)) & (df.time < END)].reset_index(drop=True)
    bad = (~np.isfinite(df[['open','high','low','close']]).all(axis=1)
           | (df.high < df[['open','close','low']].max(axis=1))
           | (df.low > df[['open','close','high']].min(axis=1)))
    invalid = int(bad.sum())
    df = df[~bad].reset_index(drop=True)
    df['time_ny'] = df.time.dt.tz_convert('America/New_York')
    df['ny_date'] = df.time_ny.dt.date
    df['ny_minute'] = df.time_ny.dt.hour*60 + df.time_ny.dt.minute
    full = bool(len(df) and df.time.iloc[0] <= START + pd.Timedelta(days=1)
                and df.time.iloc[-1] >= END - pd.Timedelta(days=1))
    return df, {'status': 'AVAILABLE' if full else 'PARTIAL', 'full_two_years': full,
                'bars': len(df), 'first': str(df.time.min()), 'last': str(df.time.max()),
                'invalid_ohlc_removed': invalid, 'sources': provenance}


class Provider:
    source_name = 'AUDITED_M5_REPLAY'

    def __init__(self, df, point):
        self.df, self.point, self.index = df, point, 0

    def get_candles(self, symbol, timeframe, count=350):
        return self.df.iloc[max(0, self.index + 1 - count):self.index + 1].copy()

    def get_current_tick(self, symbol):
        bar = self.df.iloc[self.index]
        return {'time': bar.time + pd.Timedelta(minutes=5), 'bid': bar.close,
                'ask': bar.close + float(bar.spread) * self.point}


class ReplayStrategy(orb.NewYorkORBStrategy):
    """Use audited, sorted timestamps already normalized by load().

    This adapter retains the live strategy's closed-candle and window contract,
    without repeatedly parsing and converting the same timestamp columns.
    """
    def _prepare_candles(self, symbol, now_utc):
        frame=self.data_provider.get_candles(symbol,self.config.timeframe,self.config.candle_count)
        return frame[frame.time+pd.Timedelta(minutes=5)<=pd.Timestamp(now_utc)].reset_index(drop=True)


def structural_context(df, minutes):
    """Confirmed 2+2 pivots only; HH+HL bullish, LH+LL bearish, else neutral.

    Aggregate bars are available only at their closing timestamp. A pivot
    becomes usable after the second bar to its right has closed.
    """
    bars = df.set_index('time').resample(f'{minutes}min', label='right', closed='left').agg(
        {'open':'first', 'high':'max', 'low':'min', 'close':'last', 'tick_volume':'count'})
    bars = bars[bars.tick_volume == minutes // 5]
    highs, lows, states, times = [], [], [], []
    for i in range(len(bars)):
        if i >= 4:
            window = bars.iloc[i-4:i+1]
            if window.index[-1] - window.index[0] == pd.Timedelta(minutes=minutes*4):
                center = window.iloc[2]
                if center.high > window.high.drop(window.index[2]).max():
                    highs.append(float(center.high))
                if center.low < window.low.drop(window.index[2]).min():
                    lows.append(float(center.low))
        state = 0
        if len(highs) >= 2 and len(lows) >= 2:
            if highs[-1] > highs[-2] and lows[-1] > lows[-2]:
                state = 1
            elif highs[-1] < highs[-2] and lows[-1] < lows[-2]:
                state = -1
        times.append(bars.index[i])
        states.append(state)
    return pd.Series(states, index=pd.DatetimeIndex(times))


def context_at(series, now):
    i = series.index.searchsorted(now, side='right') - 1
    return int(series.iloc[i]) if i >= 0 else 0


def liquidity(df, first, day):
    known = df.iloc[:first]
    previous = known[known.ny_date < day]
    levels = {}
    if len(previous):
        prior_day = previous.time_ny.iloc[-1].date()
        previous = previous[previous.ny_date == prior_day]
        levels.update(PDH=float(previous.high.max()), PDL=float(previous.low.min()))
    today = known[known.ny_date == day]
    # Explicit NY-clock windows; not asserted to be exact Tokyo/London exchange sessions.
    minute = today.ny_minute
    for name, left, right in [('ASIA', 0, 180), ('LONDON', 180, 570)]:
        part = today[(minute >= left) & (minute < right)]
        if len(part):
            levels[name + '_HIGH'] = float(part.high.max())
            levels[name + '_LOW'] = float(part.low.min())
    return levels


def simulate(df, first, direction, stop, point):
    """Entry at next M5 open; bid OHLC + historical ask spread for short exits.

    Same-bar ordering is unknowable: stop first and TP1 then BE before TP2.
    No arbitrary holding limit or forced session-close exit is introduced.
    """
    if first >= len(df):
        return None
    side = 1 if direction == 'BUY' else -1
    b = df.iloc[first]
    spread = max(0., float(b.spread) * point)
    entry = float(b.open) + (spread if side == 1 else 0.)
    risk = side * (entry - stop)
    if risk <= 0 or not np.isfinite(risk):
        return None
    targets = [entry + side*risk, entry + side*2*risk]
    be = entry + side*spread
    closed = [False, False]
    rr, exits, reasons = [None, None], [None, None], [None, None]
    ambiguous = 0
    future = df.iloc[first:]
    for bar in future.itertuples():
        spread_now = max(0., float(bar.spread)*point)
        hi = float(bar.high) + (spread_now if side == -1 else 0.)
        lo = float(bar.low) + (spread_now if side == -1 else 0.)
        favorable, adverse = (hi, lo) if side == 1 else (lo, hi)
        stop_price = be if closed[0] else stop
        hit_stop = side*(adverse-stop_price) <= 0
        hit_tp1 = side*(favorable-targets[0]) >= 0
        hit_tp2 = side*(favorable-targets[1]) >= 0
        timestamp = str(bar.time + pd.Timedelta(minutes=5))
        if hit_stop:
            be_active = closed[0]
            ambiguous += int(hit_tp2 if closed[0] else hit_tp1)
            for leg in range(2):
                if not closed[leg]:
                    rr[leg] = side*(stop_price-entry)/risk
                    exits[leg], reasons[leg], closed[leg] = timestamp, ('BE' if leg == 1 and be_active else 'SL'), True
            # A gap beyond stop is filled conservatively at open, not guaranteed at SL.
            executable_open = float(bar.open) + (spread_now if side == -1 else 0.)
            if side*(executable_open-stop_price) < 0:
                for leg in range(2):
                    if exits[leg] == timestamp:
                        rr[leg] = side*(executable_open-entry)/risk
            break
        if not closed[0] and hit_tp1:
            rr[0], exits[0], reasons[0], closed[0] = 1., timestamp, 'TP1', True
            if side*(adverse-be) <= 0:
                ambiguous += 1
                rr[1], exits[1], reasons[1], closed[1] = side*(be-entry)/risk, timestamp, 'BE', True
        if not closed[1] and hit_tp2 and closed[0]:
            rr[1], exits[1], reasons[1], closed[1] = 2., timestamp, 'TP2', True
        if all(closed):
            break
    return {'entry_time': str(b.time), 'entry_price': entry, 'stop_loss': stop,
            'tp1_price': targets[0], 'tp2_price': targets[1], 'be_price': be,
            'risk_distance': risk, 'spread_entry': spread, 'ambiguity_bars': ambiguous,
            'leg1_r': rr[0], 'leg2_r': rr[1], 'leg1_exit': exits[0], 'leg2_exit': exits[1],
            'leg1_reason': reasons[0], 'leg2_reason': reasons[1],
            'closed': all(closed), 'net_r': .5*sum(rr) if all(closed) else None}


def sweep_signal(df, indices, offset, opening, cfg, atr):
    """Research B: rejection outside ORB, subsequent closed M5 MSS and midpoint.

    Confirmed in 1..3 following bars; MSS breaks the three lows/highs preceding
    the sweep. SL beyond the sweep extreme (video-3 user summary). Same ATR, volume,
    VWAP/POC checks as A. Reversal can oppose HTF by design.
    """
    if not atr or not check_range_amplitude(opening.high.max(), opening.low.min(), atr,
                                            cfg['max_range_atr_ratio'])['isValid']:
        return None
    idx = indices[offset]
    bar = df.iloc[idx]
    high, low = float(opening.high.max()), float(opening.low.min())
    mid = (high+low)/2
    for earlier in range(max(0, offset-3), offset):
        sweep_idx = indices[earlier]
        sweep = df.iloc[sweep_idx]
        before = df.iloc[max(0, sweep_idx-3):sweep_idx]
        if len(before) != 3 or not low < sweep.close < high:
            continue
        buffer = cfg['atr_buffer']*atr
        sell = sweep.high > high+buffer and bar.close < min(float(before.low.min()), mid)
        buy = sweep.low < low-buffer and bar.close > max(float(before.high.max()), mid)
        if not sell and not buy:
            continue
        direction = 'SELL' if sell else 'BUY'
        side = -1 if sell else 1
        evidence = audit_volume_confirmation(df.iloc[max(0,idx-350):idx+1], sweep.time,
                                            'RETEST', cfg['require_volume'])
        session = df.iloc[opening.index[0]:idx+1]
        vwap = orb.NewYorkORBStrategy._session_vwap(session)
        poc = orb.NewYorkORBStrategy._session_poc(session)
        if not evidence['confirmed'] or not any(level is not None and side*(bar.close-level)>0 for level in (vwap,poc)):
            continue
        structural_stop = float(sweep.high)+buffer if sell else float(sweep.low)-buffer
        return {'direction':direction, 'stop_loss':structural_stop, 'orb_entry_mode':'SWEEP_MSS_RESEARCH',
                'sweep_time':str(sweep.time), 'volume_evidence':evidence}
    return None


def run_symbol(symbol, simulator=None):
    df, coverage = load(symbol)
    if df.empty:
        return symbol, coverage, [], {}
    fetch_audit = json.loads((OUT/'fetch_audit.json').read_text()) if (OUT/'fetch_audit.json').exists() else {}
    point = fetch_audit.get(symbol, {}).get('point')
    if not point:
        coverage.update(status='POINT_METADATA_MISSING', full_two_years=False)
        return symbol, coverage, [], {}
    # Local process only: experimental EURUSD eligibility never changes production files.
    original = orb.classify_orb_market
    orb.classify_orb_market = lambda s: 'EURUSD' if s == 'EURUSD' else original(s)
    provider = Provider(df, point)
    config = orb.ORBConfig(target_rr=2., break_even_enabled=True)
    expanded_config = orb.ORBConfig(target_rr=2., break_even_enabled=True)
    expanded_config.asset_profiles['USOIL']['allowed_modes'] = ['MOMENTUM','RETEST']
    expanded_config.asset_profiles['EURUSD'] = dict(allowed_modes=['MOMENTUM','RETEST'],
        atr_buffer=.05, max_range_atr_ratio=1.5, require_volume=True)
    expanded = ReplayStrategy(provider, expanded_config)
    coverage['point'] = point
    coverage['research_config'] = asdict(expanded_config)
    h1, m15 = structural_context(df,60), structural_context(df,15)
    trades, rejection_counts = [], Counter()
    skipped, eligible = 0, 0
    for day, group in df.groupby(df.ny_date, sort=True):
        if day.weekday() >= 5 or pd.Timestamp(day, tz='UTC') < START:
            continue
        minutes = group.ny_minute
        opening = group[(minutes >= 570)&(minutes < 585)]
        indices = group[(minutes >= 585)&(minutes < 955)].index.to_list()
        if len(opening) != 3 or set(opening.time_ny.dt.minute) != {30,35,40} or not indices:
            skipped += 1
            continue
        eligible += 1
        if eligible % 50 == 0:
            print('PROGRESS',symbol,'sessions',eligible,'date',day,flush=True)
        levels = liquidity(df, indices[0], day)
        used = set()
        session_evidence = None
        for offset, idx in enumerate(indices):
            provider.index = idx
            now = df.time.iloc[idx]+pd.Timedelta(minutes=5)
            hs, ms = context_at(h1,now), context_at(m15,now)
            native_needed = 'EXPANDED' not in used
            htf_needed = ('HTF' not in used or 'HTF_SWEEP' not in used) and hs == ms and hs != 0
            if session_evidence is None or native_needed or htf_needed:
                result = expanded.analyze_symbol(symbol, now)
                rejection_counts[result.get('reason','UNKNOWN')] += 1
                session_evidence = {'atr_frozen_m5':result.get('atr_frozen_m5'),
                                    'asset_profile':result.get('asset_profile')}
            else:
                result = dict(session_evidence)
                rejection_counts['SKIP_CONSUMED_NATIVE_AND_UNALIGNED_HTF'] += 1
            sig = result.get('signal') if result.get('valid') else None
            native_sig = sig if symbol not in ['US Oil','UK Brent Oil','EURUSD'] else None
            cfg_key = result.get('asset_profile')
            cfg = expanded_config.asset_profiles.get(cfg_key, expanded_config.asset_profiles['EURUSD'])
            sweep = (sweep_signal(df,indices,offset,opening,cfg,result.get('atr_frozen_m5'))
                     if 'SWEEP' not in used or 'HTF_SWEEP' not in used else None)
            aligned = sig and hs == ms == (1 if sig['direction']=='BUY' else -1)
            sweep_aligned = sweep and hs == ms == (1 if sweep['direction']=='BUY' else -1)
            choices = {'CURRENT':native_sig, 'EXPANDED':sig, 'SWEEP':sweep,
                       'HTF':sig if aligned else None,
                       'HTF_SWEEP':(sig if aligned else sweep if sweep_aligned else None)}
            for variant, signal in choices.items():
                if variant in used or signal is None:
                    continue
                # If the next opening candle is absent, do not fill after a data gap.
                if idx+1 >= len(df) or df.time.iloc[idx+1] != now:
                    rejection_counts['NEXT_BAR_MISSING'] += 1
                    continue
                simulate_trade = simulator or simulate
                simulated = simulate_trade(df,idx+1,signal['direction'],float(signal['stop_loss']),point)
                if simulated is None:
                    continue
                side = 1 if signal['direction']=='BUY' else -1
                ahead = {k:side*(v-simulated['entry_price'])/simulated['risk_distance']
                         for k,v in levels.items() if side*(v-simulated['entry_price'])>0}
                trades.append({'variant':variant,'symbol':symbol,'session_date':str(day),
                    'signal_time':str(now),'direction':signal['direction'],
                    'entry_mode':signal['orb_entry_mode'],'h1_state':hs,'m15_state':ms,
                    'liquidity_levels':json.dumps(levels),'liquidity_ahead_r':json.dumps(ahead),
                    'nearest_liquidity_r':min(ahead.values()) if ahead else None,
                    'orb_range_high':float(opening.high.max()),'orb_range_low':float(opening.low.min()),
                    **simulated})
                used.add(variant)
            if len(used) == (4 if symbol in ['US Oil','UK Brent Oil','EURUSD'] else 5):
                break
            if result.get('action') in ['ORB_SESSION_CANCELLED','WAITING_ORB_ATR']:
                break
    coverage.update(complete_opening_sessions=eligible, incomplete_sessions_skipped=skipped)
    # Boundary coverage alone cannot certify interior gaps: enumerate every observed session.
    coverage['full_two_years'] = coverage['full_two_years'] and skipped == 0
    print('DONE',symbol,'sessions',eligible,'trades',len(trades),flush=True)
    return symbol, coverage, trades, dict(rejection_counts)


def metrics(frame):
    closed = frame[frame.closed.astype(bool)] if len(frame) else frame
    r = closed.net_r.astype(float) if len(closed) else pd.Series(dtype=float)
    wins, losses = r[r>0].sum(), -r[r<0].sum()
    return {'trades':len(frame), 'closed':len(closed), 'open':len(frame)-len(closed),
            'positive_pct':float((r>0).mean()*100) if len(r) else None,
            'net_r':float(r.sum()), 'expectancy_r':float(r.mean()) if len(r) else None,
            'profit_factor':float(wins/losses) if losses else None,
            'tp1_count':int((closed.leg1_reason=='TP1').sum()) if len(closed) else 0,
            'tp2_count':int((closed.leg2_reason=='TP2').sum()) if len(closed) else 0,
            'ambiguous_trades':int((frame.ambiguity_bars>0).sum()) if len(frame) else 0}


def portfolio(frame, capital=10000.):
    """Risk each leg at 0.5% of realized balance at entry, event chronological.

    No portfolio exposure veto: report peak initial risk of overlapping setups.
    Equal-time entry groups are sized from the same balance; exits occur first.
    Mark-to-market drawdown cannot be inferred from realized event equity.
    """
    events, risks = [], {}
    for key,row in frame.reset_index(drop=True).iterrows():
        events.append((pd.Timestamp(row.entry_time),1,key,'ENTRY',0.))
        for leg in [1,2]:
            if pd.notna(row[f'leg{leg}_exit']):
                events.append((pd.Timestamp(row[f'leg{leg}_exit']),0,key,f'LEG{leg}',float(row[f'leg{leg}_r'])))
    balance, peak, drawdown, maxrisk, openrisk = capital,capital,0.,0.,0.
    records=[]
    for timestamp,_,key,event,r in sorted(events):
        if event=='ENTRY':
            risks[key]=balance*.005
            openrisk+=risks[key]*2
            maxrisk=max(maxrisk,openrisk/balance*100)
            pnl=0.
        else:
            pnl=risks[key]*r
            balance+=pnl
            openrisk-=risks[key]
        peak=max(peak,balance)
        drawdown=max(drawdown,(peak-balance)/peak*100)
        records.append({'time':str(timestamp),'trade_id':key,'event':event,
                        'pnl':pnl,'balance':balance,'initial_open_risk':openrisk})
    return {'initial_capital':capital,'final_realized_balance':balance,
            'return_pct':(balance/capital-1)*100,'realized_drawdown_pct':drawdown,
            'peak_initial_open_risk_pct':maxrisk},records


def report(results, trades):
    status = ('Cobertura de dos años disponible en todos los instrumentos.'
              if results.get('full_two_years_all_symbols') else
              '**Estado: PARCIAL; no se acredita un replay de dos años en todos los instrumentos.**')
    lines=['# Replay ORB: dos piernas y sugerencias de Núñez','',
      f'Intervalo solicitado: {START.date()} a {END.date()} (fin exclusivo).',
      status,'',
      'Entradas: 0,5% de riesgo cada una, total 1% por oportunidad. TP1=1R, TP2=2R. '
      'Runner pasa a BE protegido por spread exclusivamente después de cerrar TP1. '
      'El precio de entrada es la apertura de la siguiente M5, con spread para compras.','',
      '## Cobertura','', '| Instrumento | Primer dato | Último dato | Sesiones ORB | Estado |',
      '|---|---|---|---:|---|']
    for symbol,cov in results['coverage'].items():
        lines.append(f"| {symbol} | {cov.get('first','—')[:10]} | {cov.get('last','—')[:10]} | {cov.get('complete_opening_sessions',0)} | {cov['status']} |")
    lines+=['','## Comparaciones','',
      'CURRENT conserva el universo vigente (petróleo podado; EURUSD no autorizado en vivo). '
      'EXPANDED habilita petróleo y EURUSD solo en este experimento. HTF añade estructura H1 y M15 alineada. '
      'SWEEP prueba barrido/MSS con SL estructural más allá del extremo barrido. '
      'HTF_SWEEP combina rupturas y reversiones alineadas con H1/M15. '
      'Las variantes usan una oportunidad por símbolo y sesión.','',
      '| Variante | Cerradas | Positivas | R neto | PF | Retorno saldo | DD saldo |',
      '|---|---:|---:|---:|---:|---:|---:|']
    for variant,stats in results['variants'].items():
        p=stats['portfolio']
        positive=stats['positive_pct'] or 0
        pf='—' if stats['profit_factor'] is None else f"{stats['profit_factor']:.2f}"
        lines.append(f"| {variant} | {stats['closed']} | {positive:.1f}% | {stats['net_r']:.2f} | {pf} | {p['return_pct']:.2f}% | {p['realized_drawdown_pct']:.2f}% |")
    lines+=['','## Por instrumento (EXPANDED)','',
      '| Instrumento | Cerradas | Positivas | R neto | PF | TP1 | TP2 |',
      '|---|---:|---:|---:|---:|---:|---:|']
    for symbol,stats in results['per_symbol_expanded'].items():
        pf='—' if stats['profit_factor'] is None else f"{stats['profit_factor']:.2f}"
        lines.append(f"| {symbol} | {stats['closed']} | {(stats['positive_pct'] or 0):.1f}% | {stats['net_r']:.2f} | {pf} | {stats['tp1_count']} | {stats['tp2_count']} |")
    lines+=['','## Definiciones y límites','',
      '- H1/M15: pivotes de dos velas a cada lado, conocidos solo tras el cierre de la segunda vela posterior. '
      'Dos máximos y mínimos crecientes = compra; decrecientes = venta; resto = neutral. No se usa contexto futuro.',
      '- Barrido experimental: exceder ORH/ORL con buffer ATR, cerrar dentro; durante las siguientes 1–3 M5 '
      'romper por cierre los tres mínimos/máximos previos al barrido y atravesar el midpoint. '
      'SL más allá del extremo barrido con buffer ATR, '
      'con filtros de amplitud, volumen y VWAP/POC. Es una definición de investigación, pendiente de verificar '
      'con los videos originales; no una reproducción certificada de la enseñanza.',
      '- PDH/PDL usa el último día observado anterior (puede tener datos parciales). Asia=00:00–03:00 NY y Londres=03:00–09:30 NY, '
      'ventanas explícitas para auditoría. Sus niveles quedan registrados como confluencias; no cambian TP1/TP2.',
      '- Velas con SL y TP tocados: SL primero. Tras TP1, si la misma vela también cruza BE, se cierra el runner '
      'en BE antes de conceder TP2. Se registra la ambigüedad; se necesitan ticks/M1 para resolver el orden.',
      '- Spread histórico por vela y point obtenido de MT5. No hay comisión, swap, deslizamiento ni restricciones '
      'de margen/lote mínimo incorporados. Resultados después de spread y antes de los demás costos.',
      '- El volumen de estos CSV es principalmente tick_volume (real_volume suele ser cero). '
      'Se aplica la política del motor para datos ausentes; no se presenta como medición de volumen '
      'institucional negociado. EURUSD usa un perfil experimental genérico, sin habilitarlo en producción.',
      '- No se cierra artificialmente a las 16:00; se mantienen los niveles hasta salida o fin de datos. '
      'Posiciones sin salida se reportan abiertas y no se convierten en ganancias ficticias.',
      '- TP1 y TP2 se proyectan desde el precio ejecutable de la siguiente apertura M5 para conservar '
      '1R/2R con el SL estructural. Esto es una hipótesis del replay: no reproduce exactamente fills '
      'de tick ni los TP precalculados que podría conservar el motor en vivo tras una diferencia de ejecución.',
      '- Se conserva ORB de 15 minutos y sesión Nueva York. No se ensayan ORB de 5/30 minutos, '
      'apertura de Londres ni entradas específicas al retroceso del 50% en rangos cancelados por ATR. '
      'Las mejoras evaluadas son HTF, barrido/MSS y auditoría de liquidez con las reglas descritas.',
      '- Cartera ilustrativa de 10.000 unidades: capitalización por eventos de entrada y cierre; cada pierna '
      'arriesga el 0,5% del saldo realizado al entrar. Puede haber varias oportunidades simultáneas: '
      '1% es por oportunidad, no un techo agregado. DD corresponde al saldo realizado, no a equity flotante.',
      '- Los períodos disponibles difieren entre instrumentos; no es una comparación homogénea de dos años. '
      'Los datos H1 no se convierten en M5 inventadas. La selección vigente puede haber sido ajustada '
      'con estos mismos datos: esto no es validación fuera de muestra.',
      '- Sin órdenes, reinicios, entrenamiento de IA ni modificaciones de las reglas del bot en vivo.','',
      '## Para completar dos años','',
      'MT5 informa maxbars=100000. Se requieren históricos M5 reales que cubran el intervalo solicitado '
      'en cada símbolo (más de 100000 barras; BTC necesita alrededor de 210000). Ampliar la historia '
      'disponible en el terminal o aportar CSV del mismo broker y ejecutar de nuevo este replay. '
      'El archivo fetch_audit.json conserva los datos fuera del intervalo rechazados.']
    (OUT/'INFORME.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--fetch',action='store_true')
    parser.add_argument('--workers',type=int,default=4)
    args=parser.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    if args.fetch:
        fetch()
        return
    results={'requested_start':str(START),'requested_end_exclusive':str(END),
             'coverage':{},'rejections':{},'variants':{},'per_symbol_expanded':{}}
    all_trades=[]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futures={pool.submit(run_symbol,s):s for s in SYMBOLS}
        for future in as_completed(futures):
            symbol,cov,trades,rejections=future.result()
            results['coverage'][symbol]=cov
            results['rejections'][symbol]=rejections
            all_trades.extend(trades)
            (OUT/(symbol.replace(' ','_')+'_checkpoint.json')).write_text(
                json.dumps({'coverage':cov,'trades':trades,'rejections':rejections},default=str),encoding='utf-8')
    frame=pd.DataFrame(all_trades)
    if frame.empty:
        raise RuntimeError('No executable trades; inspect coverage/checkpoints')
    frame=frame.sort_values(['variant','entry_time','symbol']).reset_index(drop=True)
    frame.to_csv(OUT/'trades.csv',index=False)
    for variant in VARIANTS:
        subset=frame[frame.variant==variant]
        stats=metrics(subset)
        stats['portfolio'],events=portfolio(subset)
        results['variants'][variant]=stats
        pd.DataFrame(events).to_csv(OUT/(variant+'_equity_events.csv'),index=False)
    for symbol in SYMBOLS:
        results['per_symbol_expanded'][symbol]=metrics(frame[(frame.variant=='EXPANDED')&(frame.symbol==symbol)])
    results['full_two_years_all_symbols']=all(c['full_two_years'] for c in results['coverage'].values())
    (OUT/'results.json').write_text(json.dumps(results,indent=2,default=str),encoding='utf-8')
    report(results,frame)
    print(json.dumps(results['variants'],indent=2),flush=True)


if __name__=='__main__':
    main()
