"""Offline inventory of potential level definitions, without signals or orders."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.malaysian_snr.malaysian_snr_strategy import compute_atr

history = ROOT / 'storage/analysis/msnr_v21_two_years_20261011/history'
rows = []
for symbol in MalaysianSNRConfig().allowed_symbols:
    path = history / f'{symbol.replace(" ", "_")}_H1.pkl'
    if not path.exists():
        rows.append({'symbol': symbol, 'missing': True})
        continue
    frame = pd.read_pickle(path).sort_values('time').reset_index(drop=True)
    stamp = pd.to_datetime(frame.time, utc=True, unit='s' if pd.api.types.is_numeric_dtype(frame.time) else None)
    frame = frame[(stamp >= pd.Timestamp('2024-10-11', tz='UTC')) &
                  (stamp < pd.Timestamp('2026-10-11', tz='UTC'))].reset_index(drop=True)
    o, c = frame.open.to_numpy(), frame.close.to_numpy()
    a = (c[:-1] > o[:-1]) & (c[1:] < o[1:])
    v = (c[:-1] < o[:-1]) & (c[1:] > o[1:])
    strict = (a & (c[1:] <= o[:-1])) | (v & (c[1:] >= o[:-1]))
    same_direction = ((c[:-1] > o[:-1]) & (c[1:] > o[1:]) & (o[1:] > c[:-1])) | (
        (c[:-1] < o[:-1]) & (c[1:] < o[1:]) & (o[1:] < c[:-1]))
    atr_before = compute_atr(frame).to_numpy()[:-1]
    gap_ratio = np.divide(np.abs(o[1:] - c[:-1]), atr_before,
                          out=np.zeros(len(o)-1), where=np.isfinite(atr_before) & (atr_before > 0))
    rows.append({'symbol': symbol, 'h1_bars': len(frame),
                 'body_turns': int((a | v).sum()), 'strict_body_turns': int(strict.sum()),
                 'additional_body_turns': int(((a | v) & ~strict).sum()),
                 'directional_open_close_gaps_ge_001_atr': int((same_direction & (gap_ratio >= .01)).sum()),
                 'directional_open_close_gaps_ge_005_atr': int((same_direction & (gap_ratio >= .05)).sum())})
out = ROOT / 'storage/analysis/msnr_web_review_20261011'
out.mkdir(parents=True, exist_ok=True)
result = {'window_start': '2024-10-11', 'window_end_exclusive': '2026-10-11',
          'warning': 'Level candidates only; not confirmed setups, trades, or WinRate. Thresholds are inventory buckets, not recommended settings.',
          'symbols': rows}
(out / 'structure_inventory.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(result, ensure_ascii=False))
