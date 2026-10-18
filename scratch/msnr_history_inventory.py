from pathlib import Path
import ast, json, sys
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'storage/analysis/msnr_v21_two_years_20261011'
OUT.mkdir(parents=True, exist_ok=True)
tree = ast.parse((ROOT / 'tools/replay_malaysian_snr_full_universe.py').read_text(encoding='utf-8-sig'))
universe = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'ASSET_UNIVERSE' for t in n.targets))
rows = []
for symbol, meta in universe.items():
    row = {'symbol': symbol, **meta}
    for tf in ('H1', 'M15'):
        path = ROOT / 'data/cache_msnr' / f'{symbol.replace(" ", "_")}_{tf}.pkl'
        if path.exists():
            frame = pd.read_pickle(path)
            times = pd.to_datetime(frame.time, utc=True, unit='s' if pd.api.types.is_numeric_dtype(frame.time) else None)
            row[tf] = {'rows':len(frame), 'start':str(times.min()), 'end':str(times.max()), 'columns':list(frame.columns), 'duplicates':int(times.duplicated().sum()), 'path':str(path), 'mtime_ns':path.stat().st_mtime_ns}
    rows.append(row)
    print(json.dumps(row, ensure_ascii=True), flush=True)
(OUT / 'history_inventory.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
print(f'UNIVERSE={len(universe)}', flush=True)
