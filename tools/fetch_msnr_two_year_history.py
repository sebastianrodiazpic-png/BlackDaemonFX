"""Read-only MT5 historical snapshot for the MSNR paired audit. Never sends orders."""
from __future__ import annotations
import argparse, ast, hashlib, json, sys, time
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from config.strategy_config import PRUNED_ASSET_UNIVERSE
from strategy.malaysian_snr.config import MalaysianSNRConfig

def historical_universe():
    tree = ast.parse((ROOT / 'tools/replay_malaysian_snr_full_universe.py').read_text(encoding='utf-8-sig'))
    return next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'ASSET_UNIVERSE' for t in n.targets))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='storage/analysis/msnr_v21_two_years_20261011')
    parser.add_argument('--shard', type=int, default=0)
    parser.add_argument('--shards', type=int, default=1)
    args = parser.parse_args()
    out = (ROOT / args.output).resolve()
    if not out.is_relative_to(ROOT):
        parser.error('Output must be inside the workspace')
    (out / 'history').mkdir(parents=True, exist_ok=True)
    import MetaTrader5 as mt5
    if not mt5.initialize():
        raise SystemExit(f'MT5 historical connection failed: {mt5.last_error()}')
    try:
        catalog = mt5.symbols_get() or ()
        lookup = {s.name:s for s in catalog}
        configured = set(MalaysianSNRConfig().allowed_symbols)
        configured.update(s for group in PRUNED_ASSET_UNIVERSE.values() for s in group)
        legacy = historical_universe()
        all_names = sorted({s.name for s in catalog if s.visible and s.trade_mode != 0} | configured | set(legacy))
        names = all_names[args.shard::args.shards]
        start = datetime(2024, 8, 1, tzinfo=timezone.utc)
        end = datetime.now(timezone.utc)
        audit_start = pd.Timestamp('2024-10-11T00:00:00Z')
        audit_end = pd.Timestamp('2026-10-11T00:00:00Z')
        manifest = {'audit_start':str(audit_start),'audit_end':str(audit_end),'snapshot_at':str(end),
                    'catalog_total':len(catalog),'visible_total':sum(s.visible for s in catalog),
                    'universe_rule':'Visible tradable instruments UNION configured worker/MSNR instruments UNION previous 60-asset replay',
                    'requested_symbols':all_names, 'shard':args.shard, 'symbols':[]}
        for n, name in enumerate(names, 1):
            started = time.monotonic()
            info = lookup.get(name)
            row = {'symbol':name,'visible':bool(info and info.visible),'configured':name in configured,
                   'legacy_universe':name in legacy, 'path':info.path if info else None,
                   'point':float(info.point) if info else None,
                   'fallback_spread':float(info.spread * info.point) if info else None,
                   'legacy_spread':legacy.get(name,{}).get('base_spread'), 'frames':{}}
            if info is None or info.trade_mode == 0:
                row['error'] = 'NOT_AVAILABLE_OR_DISABLED_IN_TERMINAL'
            else:
                for tf, const, minutes in (('H1',mt5.TIMEFRAME_H1,60),('M15',mt5.TIMEFRAME_M15,15),('D1',mt5.TIMEFRAME_D1,1440)):
                    path = out / 'history' / f'{name.replace(" ", "_")}_{tf}.pkl'
                    if path.exists():
                        frame = pd.read_pickle(path)
                    else:
                        rates = mt5.copy_rates_range(name, const, start, end)
                        frame = pd.DataFrame(rates) if rates is not None else pd.DataFrame()
                        if len(frame):
                            frame['time'] = pd.to_datetime(frame.time, unit='s', utc=True)
                            # Some MT5 calls return one bar outside requested range.
                            frame = frame[(frame.time >= start) & (frame.time + pd.Timedelta(minutes=minutes) <= end)].sort_values('time').reset_index(drop=True)
                        frame.to_pickle(path)
                    if frame.empty:
                        row['frames'][tf] = {'rows':0,'error':str(mt5.last_error())}
                        continue
                    prices = frame[['open','high','low','close']].to_numpy(float)
                    invalid = ~np.isfinite(prices).all(axis=1) | (prices[:,1] < prices.max(axis=1)) | (prices[:,2] > prices.min(axis=1))
                    metadata = {'rows':len(frame),'start':str(frame.time.min()),'last_open':str(frame.time.max()),
                                'duplicates':int(frame.time.duplicated().sum()),'invalid_ohlc':int(invalid.sum()),
                                'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'file':str(path.relative_to(out)),
                                'bars_before_audit':int((frame.time + pd.Timedelta(minutes=minutes) <= audit_start).sum()),
                                'bars_during_audit':int(((frame.time >= audit_start) & (frame.time < audit_end)).sum())}
                    if tf == 'M15':
                        metadata['internal_missing_slots'] = int(np.maximum(0, frame.time.diff().dropna().dt.total_seconds().to_numpy()/900 - 1).sum())
                        metadata['positive_spread_bars'] = int((frame.spread > 0).sum()) if 'spread' in frame else 0
                        metadata['full_two_year_start'] = bool(frame.time.min() <= audit_start)
                    row['frames'][tf] = metadata
            manifest['symbols'].append(row)
            manifest_path=out / f'history_manifest_shard_{args.shard}.json'
            manifest_temp=manifest_path.with_suffix('.json.tmp')
            manifest_temp.write_text(json.dumps(manifest,indent=2),encoding='utf-8')
            manifest_temp.replace(manifest_path)
            print(json.dumps({'index':n,'total':len(names),'symbol':name,'rows':{tf:x.get('rows') for tf,x in row['frames'].items()},'error':row.get('error'),'seconds':round(time.monotonic()-started,2)}),flush=True)
    finally:
        mt5.shutdown()

if __name__ == '__main__':
    main()
