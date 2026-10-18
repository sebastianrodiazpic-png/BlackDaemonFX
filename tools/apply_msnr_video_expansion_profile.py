"""Apply the Malaysian SNR video-based expansion profile to maximize trade volume and profitability."""
from datetime import datetime, timezone
import argparse
import json
import os
from pathlib import Path
import sqlite3
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from strategy.malaysian_snr.runtime_settings import validate_msnr_patch

OUT = ROOT / 'storage/analysis/msnr_expansion_trades_20261013'
BASE = 'http://127.0.0.1:8765'
PATH = '/api/strategies/malaysian-snr/settings'

EXPANDED_PROFILE = {
    'breaker_pair_mode': 'live',
    'breaker_pair_min_body_ratio': 0.50,
    'breaker_pair_min_displacement_atr': 0.50,
    'retest_pinbar_mode': 'live',
    'retest_pinbar_min_wick_ratio': 0.55,
    'retest_pinbar_min_close_ratio': 0.70,
    'retest_window_minutes': 240,
    'recovery_window_minutes': 60,
    'recovery_min_body_ratio': 0.25,
    'continuation_fresh_only': False,
    'continuation_mode': 'live',
    'session_policy': 'market_hours',
    'h4_neutral_fallback_mode': 'live',
    'obstacle_av_definition': 'engulfing',
    'h4_obstacle_mode': 'shadow',
    'fractal_min_body_ratio': 0.45,
    'fractal_max_entry_distance_atr': 0.50,
    'continuation_max_entry_distance_atr': 0.50,
    'qm_max_entry_distance_atr': 0.50,
    'continuation_min_body_ratio': 0.50,
    'continuation_min_adx': 20.0,
    'continuation_maximum_breakout_wick_ratio': 0.25,
    'step_min_adx': 25.0,
    'step_symbol_min_adx': {'Step Index': 23.0},
    'macro_structure_mode': 'live',
    'macro_bias_method': 'd1_structure',
    'macro_pivot_radius': 2,
    'research_min_frequency_ratio': 1.05,
    'research_min_resolved_trades': 50,
    'research_min_win_rate_improvement_pp': 1.0,
}

ACTIVE_SYMBOLS = (
    'Step Index', 'Step Index 200', 'Step Index 400', 'Step Index 500',
    'Volatility 10 Index', 'Volatility 25 Index', 'Volatility 50 (1s) Index', 'Volatility 75 (1s) Index',
    'Crash 500 Index', 'Boom 500 Index', 'Boom 600 Index',
    'Crash 1000 Index', 'Boom 1000 Index', 'Boom 300 Index', 'Crash 600 Index',
    'BTCUSD', 'XAUUSD', 'EURUSD', 'GBPUSD', 'USDJPY', 'GBPJPY', 'AUDNZD'
)

M5_SYMBOLS = (
    'Step Index', 'Step Index 200', 'Step Index 400', 'Step Index 500',
    'Volatility 50 (1s) Index', 'Crash 500 Index', 'Boom 500 Index'
)


def request(path=PATH, patch=None):
    req = urllib.request.Request(
        BASE + path,
        data=None if patch is None else json.dumps(patch).encode('utf8'),
        headers={} if patch is None else {'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req, timeout=20) as response:
        data = response.read()
    return json.loads(data) if path == PATH else data


def dump(name, value):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf8')


def worker_snapshot():
    db = Path(os.environ.get('DAEMONBLACKFX_DB_PATH') or
              Path(os.environ['LOCALAPPDATA']) / 'BlackDaemonFx/trading_bot.sqlite3')
    with sqlite3.connect(db.as_uri() + '?mode=ro', uri=True, timeout=15) as con:
        con.row_factory = sqlite3.Row
        row = con.execute(
            "SELECT * FROM worker_runtime_states WHERE bot_profile='MALAYSIAN_SNR' AND source='DEMO' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        return dict(row) if row else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true', help='Persist profile via settings API')
    args = parser.parse_args()

    # Refresh page routes
    request('/strategy-bases')
    before = request()
    if not before.get('ok') or before.get('scope') != 'MALAYSIAN_SNR':
        raise ValueError('SNR settings API unavailable or wrong scope')
    
    dump('settings_before.json', before)
    worker = worker_snapshot()
    dump('worker_before.json', worker)

    current = before['settings']
    patch = dict(EXPANDED_PROFILE)

    # Configure active asset modes
    asset_modes = dict(current.get('asset_modes', {}))
    for s in ACTIVE_SYMBOLS:
        asset_modes[s] = 'live'
    patch['asset_modes'] = asset_modes

    m5_symbol_modes = dict(current.get('m5_symbol_modes', {}))
    for s in M5_SYMBOLS:
        m5_symbol_modes[s] = 'live'
    patch['m5_symbol_modes'] = m5_symbol_modes

    continuation_symbol_modes = dict(current.get('continuation_symbol_modes', {}))
    for s in ACTIVE_SYMBOLS:
        continuation_symbol_modes[s] = 'live'
    patch['continuation_symbol_modes'] = continuation_symbol_modes

    patch = validate_msnr_patch(patch)
    dump('requested_profile.json', patch)

    changes = {
        k: {'before': current.get(k), 'after': v}
        for k, v in patch.items() if current.get(k) != v
    }
    dump('changes.json', changes)

    if not args.apply:
        print(json.dumps({
            'prepared': True,
            'current_version': current.get('version'),
            'total_changes': len(changes),
            'changes': changes,
            'active_symbols': len(ACTIVE_SYMBOLS),
            'm5_symbols': len(M5_SYMBOLS)
        }, ensure_ascii=False, indent=2))
        return

    # Apply changes
    result = request(patch=patch)
    if not result.get('ok'):
        raise ValueError('Profile save was not confirmed by the API')

    after = request()
    dump('settings_after.json', after)

    if not after.get('ok') or any(after['settings'].get(k) != v for k, v in patch.items()):
        raise ValueError('Saved profile does not match authorized settings')

    dump('applied.json', {
        'applied_at_utc': datetime.now(timezone.utc).isoformat(),
        'settings_version': after['settings']['version'],
        'total_verified_controls': len(patch),
        'total_changes_applied': len(changes),
        'source': 'DEMO',
        'orders_sent_by_this_tool': False
    })

    print(json.dumps({
        'saved': True,
        'settings_version': after['settings']['version'],
        'applied_changes': len(changes),
        'breaker_pair_mode': after['settings']['breaker_pair_mode'],
        'retest_pinbar_mode': after['settings']['retest_pinbar_mode'],
        'retest_window_minutes': after['settings']['retest_window_minutes'],
        'session_policy': after['settings']['session_policy'],
        'continuation_fresh_only': after['settings']['continuation_fresh_only']
    }, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
