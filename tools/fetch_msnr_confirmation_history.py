"""Freeze native M5/H4 and reuse hashed H1/M15/D1. Read only; no executor."""
from __future__ import annotations
import argparse
import hashlib
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.fetch_msnr_two_year_history import historical_universe
from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.malaysian_snr.validation import closed_candles

OUT = ROOT / 'storage/analysis/msnr_v27_m5_reference_20261012'
SOURCE = ROOT / 'storage/analysis/msnr_v21_two_years_20261011'
TF = {'M5': 5, 'M15': 15, 'H1': 60, 'H4': 240, 'D1': 1440}


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')
    temp.replace(path)


def describe(frame, path, start, end, minutes):
    times = frame.time
    return {'rows': len(frame), 'file': str(path.relative_to(ROOT)),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'start': times.iloc[0].isoformat(), 'last_closed_at': (times.iloc[-1]+pd.Timedelta(minutes=minutes)).isoformat(),
            'full_requested_start': bool(times.iloc[0] <= start),
            'bars_in_window': int(((times >= start) & (times < end)).sum()),
            'max_internal_gap_minutes': float(times.diff().dt.total_seconds().max()/60) if len(frame)>1 else 0.,
            'positive_spread_bars': int((frame.spread>0).sum()) if 'spread' in frame else 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--symbols', default='')
    parser.add_argument('--refresh-native', action='store_true', help='Request M5/H4 again after increasing terminal history')
    args = parser.parse_args()
    import MetaTrader5 as mt5
    if not mt5.initialize():
        raise SystemExit(str(mt5.last_error()))
    start, end = pd.Timestamp('2024-10-11T00:00:00Z'), pd.Timestamp('2026-10-11T00:00:00Z')
    warmup = datetime(2024, 8, 1, tzinfo=timezone.utc)
    now = pd.Timestamp.now(tz='UTC')
    old = json.loads((SOURCE/'history_manifest.json').read_text())
    old_rows = {row['symbol']: row for row in old['symbols']}
    core = set(MalaysianSNRConfig().allowed_symbols)
    universe = historical_universe()
    names = args.symbols.split(',') if args.symbols else sorted(universe)
    out = OUT/'history'
    out.mkdir(parents=True, exist_ok=True)
    report = {'requested_start': start.isoformat(), 'requested_end': end.isoformat(),
              'frozen_at': now.isoformat(), 'maxbars': mt5.terminal_info().maxbars,
              'feed': 'MT5 native candles', 'core_symbols': sorted(core), 'symbols': []}
    try:
        for symbol in names:
            info = mt5.symbol_info(symbol)
            row = {'symbol': symbol, 'cohort': 'core23' if symbol in core else 'historically_pruned37',
                   'category': universe.get(symbol, {}).get('category'), 'frames': {}}
            if info is None or info.trade_mode==0:
                row['error'] = 'SYMBOL_UNAVAILABLE'
            else:
                row.update(point=float(info.point), tick_size=float(info.trade_tick_size or info.point),
                           fallback_spread=float(info.spread*info.point))
                for tf, minutes in TF.items():
                    meta = old_rows.get(symbol, {}).get('frames', {}).get(tf, {})
                    if tf not in ('M5', 'H4') and meta.get('file') and meta.get('rows'):
                        path = SOURCE/meta['file']
                        if hashlib.sha256(path.read_bytes()).hexdigest()!=meta['sha256']:
                            raise ValueError(f'Snapshot changed: {symbol} {tf}')
                        frame = pd.read_pickle(path)
                    else:
                        path = out/f'{symbol.replace(" ", "_")}_{tf}.pkl'
                        cached = pd.read_pickle(path) if path.exists() else pd.DataFrame()
                        frame = cached
                        if frame.empty or args.refresh_native:
                            const = getattr(mt5, f'TIMEFRAME_{tf}')
                            rates = mt5.copy_rates_range(symbol, const, warmup, now.to_pydatetime())
                            request_error = str(mt5.last_error())
                            if rates is None or len(rates)<100:
                                # Never mistake one old edge candle for a two-year snapshot.
                                rates = mt5.copy_rates_from_pos(symbol, const, 0, min(240000, max(1, report['maxbars']-100)))
                                row.setdefault('range_request_errors', {})[tf] = request_error
                            frame = pd.DataFrame(rates) if rates is not None else pd.DataFrame()
                            if not frame.empty:
                                frame['time'] = pd.to_datetime(frame.time, unit='s', utc=True)
                                frame = closed_candles(frame, tf, now)
                                if not cached.empty:
                                    # Retain the oldest native bars when the terminal's rolling
                                    # cache returns a more recent partial window on refresh.
                                    frame = pd.concat([cached, frame]).drop_duplicates('time', keep='last')
                                    frame = closed_candles(frame, tf, now)
                                temporary = path.with_suffix('.pkl.tmp')
                                frame.to_pickle(temporary)
                                temporary.replace(path)
                            elif not cached.empty:
                                frame = cached
                                row.setdefault('refresh_errors', {})[tf] = str(mt5.last_error())
                            elif not path.exists():
                                frame.to_pickle(path)
                    if frame.empty:
                        row['frames'][tf] = {'rows': 0, 'error': str(mt5.last_error())}
                        continue
                    frame = closed_candles(frame, tf, now)
                    row['frames'][tf] = describe(frame, path, start, end, minutes)
                row['complete_two_year_start'] = all(row['frames'].get(tf, {}).get('full_requested_start', False) for tf in TF)
                starts = [pd.Timestamp(m['start']) for m in row['frames'].values() if m.get('rows')]
                row['common_available_start'] = max(starts).isoformat() if len(starts)==len(TF) else None
            report['symbols'].append(row)
            save_json(OUT/'confirmation_history_manifest.json', report)
            print(json.dumps({'symbol': symbol, 'cohort': row['cohort'], 'full_two_years': row.get('complete_two_year_start', False),
                              'm5_start': row['frames'].get('M5', {}).get('start'), 'error': row.get('error')}), flush=True)
    finally:
        mt5.shutdown()


if __name__=='__main__':
    main()
