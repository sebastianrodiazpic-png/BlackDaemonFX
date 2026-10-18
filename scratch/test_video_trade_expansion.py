import sys
from pathlib import Path
import json
import numpy as np
import pandas as pd
from collections import Counter
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.replay_msnr_confirmations import Provider, load_frames, simulate_native, stats
from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy
from strategy.execution.live_trading_engine import LiveTradingEngine
from tools.fetch_msnr_confirmation_history import OUT as HISTORY

manifest_path = HISTORY / 'confirmation_history_manifest.json'
manifest = json.loads(manifest_path.read_text())

# Test symbols
test_symbols = ['Step Index', 'Volatility 50 (1s) Index', 'Crash 1000 Index', 'Boom 1000 Index', 'BTCUSD', 'XAUUSD', 'EURUSD']
symbol_rows = [r for r in manifest['symbols'] if r['symbol'] in test_symbols]

start = pd.Timestamp('2026-09-27T00:00:00Z')
end = pd.Timestamp('2026-10-11T00:00:00Z')

PROFILES = {
    'baseline': {
        'breaker_pair_mode': 'off',
        'retest_pinbar_mode': 'off',
        'retest_window_minutes': 90,
        'recovery_min_body_ratio': 0.35,
        'session_policy': 'legacy_utc',
        'h4_neutral_fallback_mode': 'off',
        'continuation_fresh_only': True,
        'm5_confirmation_mode': 'off',
    },
    'video_expansion': {
        'breaker_pair_mode': 'live',
        'retest_pinbar_mode': 'live',
        'retest_window_minutes': 240,
        'recovery_min_body_ratio': 0.25,
        'session_policy': 'market_hours',
        'h4_neutral_fallback_mode': 'live',
        'continuation_fresh_only': False,
        'm5_confirmation_mode': 'live',
    }
}

all_trades = {p: [] for p in PROFILES}
rejections = {p: Counter() for p in PROFILES}

for row in symbol_rows:
    sym = row['symbol']
    print(f"Loading frames for {sym}...")
    frames = load_frames(row)
    provider = Provider(frames, row)
    m5 = frames['M5']
    indices = np.flatnonzero(((m5.time >= start) & (m5.time < end)).to_numpy())
    
    for p_name, patch in PROFILES.items():
        cfg_dict = dict(
            allowed_symbols=(),
            continuation_mode='live',
            enable_scenario_1_continuation=True,
            enable_scenario_3_fractal=True,
            enable_quasimodo_pattern=True,
            obstacle_av_definition='engulfing',
            h4_obstacle_mode='off',
            **patch
        )
        # remove keys not in config if any
        cfg = MalaysianSNRConfig(**{k: v for k, v in cfg_dict.items() if hasattr(MalaysianSNRConfig, k)})
        controls = dict(
            asset_modes={sym: 'live'},
            m5_symbol_modes={sym: 'live' if patch.get('m5_confirmation_mode') == 'live' else 'off'},
            continuation_symbol_modes={sym: 'live'},
            continuation_mode='live',
            additional_symbols=[],
            additional_symbols_mode='live',
            **patch
        )
        analyzer = MalaysianSNRStrategy(provider, cfg, lambda c=controls: c)
        
        gate_engine = object.__new__(LiveTradingEngine)
        gate_engine.config = SimpleNamespace(bot_profile='MALAYSIAN_SNR', step_min_adx=25.)
        gate_engine.provider = provider
        gate_engine.malaysian_snr_strategy = analyzer
        
        busy = -1
        seen = set()
        trades = []
        
        for i in indices:
            if i < 1 or m5.time.iloc[i-1] + pd.Timedelta(minutes=5) != m5.time.iloc[i]:
                continue
            if i <= busy:
                continue
            provider.now = m5.time.iloc[i]
            quote = provider.get_current_tick(sym)
            spread = quote['ask'] - quote['bid']
            
            reading = analyzer.analyze_symbol(sym, provider.now)
            if not reading.get('valid') or reading.get('shadow_only'):
                rejections[p_name][reading.get('reason', 'SHADOW')] += 1
                continue
            
            sig = dict(reading['signal'])
            if sig['setup_id'] in seen:
                continue
            if provider.now - pd.Timestamp(sig['confirmation_closed_at']) > pd.Timedelta(seconds=60):
                rejections[p_name]['STALE_CONFIRMATION'] += 1
                continue
            
            sign = 1 if sig['direction'] == 'BUY' else -1
            fill = float(m5.open.iloc[i]) + (spread if sign == 1 else 0.)
            stop = float(sig['stop_loss'])
            risk = sign * (fill - stop)
            if risk <= 0:
                rejections[p_name]['INVALID_STOP'] += 1
                continue
            
            distance = sign * (fill - sig['ref_level']) / sig['atr']
            if not (0 <= distance <= sig['max_entry_distance_atr'] and sign * (fill - sig['invalidation_level']) > 0
                    and provider.now <= pd.Timestamp(sig['setup_execution_deadline_at'])):
                rejections[p_name]['CONTEXT_CHANGED'] += 1
                continue
            
            sig['entry_price'] = fill
            gate = gate_engine._step_quality_gate(sym, sig, reading)
            if gate is None:
                gate = gate_engine._boom_crash_quality_gate(sym, sig['direction'], sig, reading)
            if gate:
                rejections[p_name][gate['reason']] += 1
                continue
            
            future = m5.iloc[i:i+601]
            future = future[future.time + pd.Timedelta(minutes=5) <= end]
            runner = float(sig.get('runner_rr', 2.5))
            if sig.get('obstacle_level'):
                room = sign * (sig['tp2_price'] - fill) / risk
                if room < 2:
                    rejections[p_name]['FILL_OBSTACLE_BEFORE_2R'] += 1
                    continue
                runner = min(runner, room)
            seen.add(sig['setup_id'])
            outcome = simulate_native(sig['direction'], fill, stop, fill + sign * 2 * risk,
                                      fill + sign * runner * risk, future, row['point'])
            busy = i + max(0, outcome['bars'] - 1)
            trades.append(outcome)
            all_trades[p_name].append({**outcome, 'symbol': sym, 'profile': p_name, 'scenario': sig['scenario']})
        
        print(f"  [{p_name}] {sym}: {len(trades)} trades", flush=True)

print("\n=== FINAL RESULTS SUMMARY ===", flush=True)
for p_name in PROFILES:
    tr = [t for t in all_trades[p_name] if t.get('rr') is not None]
    wins = [t for t in tr if t.get('rr') > 0]
    total_r = sum(t.get('rr', 0) for t in tr)
    winrate = (len(wins) / len(tr) * 100) if tr else 0.0
    print(f"\nPerfil: {p_name}", flush=True)
    print(f"  Total Trades Resueltos: {len(tr)}", flush=True)
    print(f"  Win Rate: {winrate:.1f}% ({len(wins)}/{len(tr)})", flush=True)
    print(f"  Total R: {total_r:.2f}R", flush=True)
    print(f"  Expectativa por Trade: {(total_r / len(tr)):.2f}R" if tr else "  Expectativa: N/A", flush=True)
    print("  Top Rejections:", dict(rejections[p_name].most_common(5)), flush=True)
