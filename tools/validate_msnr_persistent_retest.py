"""Offline evidence for MSNR v2.1, with unique setups and first-touch stages."""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pandas as pd
from strategy.malaysian_snr.config import MalaysianSNRConfig
from tools.audit_msnr_causal import ESTIMATED_SPREADS, load_cached_frames, statistics
from tools.replay_msnr_live_faithful import replay_frames


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--symbol', choices=list(ESTIMATED_SPREADS), required=True)
    parser.add_argument('--days', type=int, default=30)
    parser.add_argument('--output', default='storage/analysis/msnr_v21_validation_20261011')
    args = parser.parse_args()
    if args.days <= 0:
        parser.error('days must be positive')
    out = (ROOT / args.output).resolve()
    if not out.is_relative_to(ROOT):
        parser.error('output must be inside the project')
    out.mkdir(parents=True, exist_ok=True)
    frames = load_cached_frames(args.symbol)
    cfg = MalaysianSNRConfig()
    reasons, unique_by_stage = Counter(), defaultdict(set)
    unique_setups = set()
    def observe(result):
        reason = result.get('reason', 'UNKNOWN')
        reasons[reason] += 1
        diagnostics = result.get('diagnostics') or {}
        evidence = diagnostics.get('candidates') or [diagnostics]
        for item in evidence:
            setup_id = item.get('setup_id')
            if setup_id:
                unique_setups.add(setup_id)
                stage = item.get('reason') or diagnostics.get('stage') or reason
                unique_by_stage[stage].add(setup_id)
    trades = replay_frames(args.symbol, frames, args.days, cfg,
                           ESTIMATED_SPREADS[args.symbol], on_evaluation=observe)
    frame = pd.DataFrame(trades)
    summary = {'symbol':args.symbol, 'days':args.days, 'configuration':asdict(cfg),
               'm15_end':str(frames['M15'].time.max()), 'spread_estimate':ESTIMATED_SPREADS[args.symbol],
               'statistics':statistics(frame), 'evaluations_by_reason':dict(reasons),
               'unique_setups':len(unique_setups),
               'unique_setups_by_stage':{key:len(value) for key,value in unique_by_stage.items()},
               'limitations':['Reused historical data; not an independent performance test.',
                              'D1 aggregated in UTC; fixed spread; no commission, swaps or portfolio constraints.',
                              'Stages overlap; repeated evaluations are not extra trades.']}
    prefix = args.symbol.replace(' ', '_')
    frame.to_csv(out / f'{prefix}_trades.csv',index=False)
    (out / f'{prefix}_metrics.json').write_text(json.dumps(summary,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({key:summary[key] for key in ('symbol','statistics','unique_setups','unique_setups_by_stage')},ensure_ascii=True),flush=True)


if __name__ == '__main__':
    main()
