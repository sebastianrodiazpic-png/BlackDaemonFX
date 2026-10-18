"""Compare current CRT with the existing bounded retest on saved candles only."""
import argparse
import json
import sys
import time
from collections import Counter
from dataclasses import asdict, replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import pandas as pd
from tools.audit_msnr_causal import ESTIMATED_SPREADS, load_cached_frames, statistics
from tools.replay_msnr_live_faithful import replay_frames
from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy

parser = argparse.ArgumentParser()
parser.add_argument('--symbol', choices=list(ESTIMATED_SPREADS), required=True)
parser.add_argument('--days', type=int, default=30)
args = parser.parse_args()
if args.days <= 0:
    parser.error('days must be positive')
frames = load_cached_frames(args.symbol)
out = ROOT / 'storage/analysis/msnr_restriction_review_20261011'
out.mkdir(parents=True, exist_ok=True)
prefix = args.symbol.replace(' ', '_')
config = MalaysianSNRConfig()
summary = {
    'symbol': args.symbol, 'days': args.days,
    'm15_start': str(frames['M15'].time.min()), 'm15_end': str(frames['M15'].time.max()),
    'spread_estimate': ESTIMATED_SPREADS[args.symbol],
    'base_configuration': asdict(config),
    'limitations': ['Reused historical data; no independent test.', 'D1 aggregated from H1 in UTC.',
                    'Fixed spread, no commissions or swaps, no portfolio constraints.',
                    'Small samples cannot establish a win-rate improvement.'],
    'variants': [],
}
original = MalaysianSNRStrategy.analyze_symbol
for name, candidate in (
    ('current_crt', config),
    ('bounded_retest_crt_off', replace(config, enable_crt_sweep_rejection=False)),
):
    reasons = Counter()
    def observed(self, symbol, now_utc=None):
        result = original(self, symbol, now_utc)
        reasons[result.get('reason')] += 1
        return result
    MalaysianSNRStrategy.analyze_symbol = observed
    started = time.perf_counter()
    try:
        trades = replay_frames(args.symbol, frames, args.days, candidate,
                               ESTIMATED_SPREADS[args.symbol])
    finally:
        MalaysianSNRStrategy.analyze_symbol = original
    frame = pd.DataFrame(trades)
    metrics = statistics(frame)
    metrics.update(variant=name, evaluation_reasons=dict(reasons), seconds=round(time.perf_counter()-started,2))
    summary['variants'].append(metrics)
    frame.to_csv(out / f'{prefix}_{name}_trades.csv', index=False)
    print(json.dumps({'symbol': args.symbol, **metrics}, ensure_ascii=True), flush=True)
(out / f'{prefix}_comparison.json').write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf-8')
