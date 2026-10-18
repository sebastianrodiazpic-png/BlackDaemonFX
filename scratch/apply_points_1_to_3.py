import urllib.request
import json
import sys

URL = 'http://127.0.0.1:8765/api/strategies/malaysian-snr/settings'

patch = {
    # PUNTO 1: Cartera Ganadora Maximizada (Alta Probabilidad)
    "asset_modes": {
        "Crash 500 Index": "live",       # 86.4% WR, +$1,343.95
        "Step Index 500": "live",        # 66.7% WR, +$568.71
        "Crash 600 Index": "live",       # 81.8% WR, +$72.38
        "Wall Street 30": "live",        # 66.7% WR, +$161.46
        "BTCUSD": "live",                # 58.1% WR, +$125.59
        "XAUUSD": "live",                # 58.8% WR, +$132.64
        "Boom 1000 Index": "live",
        "Boom 500 Index": "live",
        "Boom 600 Index": "live",
        "Boom 300 Index": "live",
        "Crash 1000 Index": "live",
        "Step Index": "live",
        "Step Index 400": "live",
        "Volatility 50 (1s) Index": "live",
        "Volatility 75 (1s) Index": "live",
        "Volatility 10 Index": "live",
        "EURUSD": "live",
        "GBPUSD": "live",
        "USDJPY": "live",
        "GBPJPY": "live",
        "AUDNZD": "live",
        # Filtrado de activos destructores de WinRate a SHADOW para proteger el balance:
        "Volatility 25 Index": "shadow",  # Protege la cuenta de -$446.25 de pérdidas pasadas
        "Volatility 75 Index": "shadow",  # Protege la cuenta de -$330.16 de pérdidas pasadas
        "Step Index 200": "shadow",       # Protege la cuenta de -$309.76 de pérdidas pasadas
        "USDCAD": "shadow",
        "CADCHF": "shadow",
        "CHFJPY": "shadow",
    },
    "continuation_symbol_modes": {
        "Crash 500 Index": "live",
        "Step Index 500": "live",
        "Crash 600 Index": "live",
        "Wall Street 30": "live",
        "BTCUSD": "live",
        "XAUUSD": "live",
        "Boom 1000 Index": "live",
        "Boom 500 Index": "live",
        "Boom 600 Index": "live",
        "Boom 300 Index": "live",
        "Crash 1000 Index": "live",
        "Step Index": "live",
        "Step Index 400": "live",
        "Volatility 50 (1s) Index": "live",
        "Volatility 75 (1s) Index": "live",
        "Volatility 10 Index": "live",
        "EURUSD": "live",
        "GBPUSD": "live",
        "USDJPY": "live",
        "GBPJPY": "live",
        "AUDNZD": "live",
    },
    "m5_symbol_modes": {
        "Crash 500 Index": "live",
        "Step Index 500": "live",
        "Crash 600 Index": "live",
        "Wall Street 30": "live",
        "BTCUSD": "live",
        "XAUUSD": "live",
        "Boom 500 Index": "live",
        "Step Index": "live",
        "Step Index 400": "live",
        "Volatility 50 (1s) Index": "live",
    },

    # PUNTO 2: Seguimiento de Sesiones (Session Tracking & Killzones)
    "session_policy": "market_hours",

    # PUNTO 3: Flexibilización Causal de Malaysian SNR
    "continuation_mode": "live",
    "continuation_fresh_only": False,
    "continuation_direct_trigger": True,
    "continuation_min_body_ratio": 0.50,
    "continuation_min_adx": 20.0,
    "continuation_max_entry_distance_atr": 0.50,
    "retest_window_minutes": 240,
    "recovery_window_minutes": 60,
    "recovery_min_body_ratio": 0.25,
    "breaker_pair_mode": "live",
    "breaker_pair_min_body_ratio": 0.50,
    "breaker_pair_min_displacement_atr": 0.50,
    "retest_pinbar_mode": "live",
    "retest_pinbar_min_wick_ratio": 0.55,
    "retest_pinbar_min_close_ratio": 0.70,
    "h4_neutral_fallback_mode": "live",
    "macro_structure_mode": "live",
    "macro_bias_method": "d1_structure",
    "macro_pivot_radius": 2,
    "fractal_min_body_ratio": 0.45,
    "fractal_max_entry_distance_atr": 0.50,
    "qm_max_entry_distance_atr": 0.50,
    "step_min_adx": 25.0,
    "step_symbol_min_adx": {"Step Index": 23.0},
    "ai_mode": "filter",
    "ai_incompatible_policy": "observe",
}

print(f"Applying patch to {URL}...")
req = urllib.request.Request(
    URL,
    data=json.dumps(patch).encode('utf8'),
    headers={'Content-Type': 'application/json'}
)

try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        res = json.loads(resp.read().decode('utf8'))
        print("SUCCESS! Response status:", res.get('status'))
        settings = res.get('settings', {})
        print("Version:", settings.get('version'))
        print("Breaker Pair Mode:", settings.get('breaker_pair_mode'))
        print("Retest Pinbar Mode:", settings.get('retest_pinbar_mode'))
        print("Retest Window Minutes:", settings.get('retest_window_minutes'))
        print("Recovery Body Ratio:", settings.get('recovery_min_body_ratio'))
        print("Session Policy:", settings.get('session_policy'))
        print("Continuation Mode:", settings.get('continuation_mode'))
        print("Crash 500 Index mode:", settings.get('asset_modes', {}).get('Crash 500 Index'))
        print("Wall Street 30 mode:", settings.get('asset_modes', {}).get('Wall Street 30'))
        print("Volatility 25 Index mode:", settings.get('asset_modes', {}).get('Volatility 25 Index'))
except Exception as e:
    print("FAILED:", e)
    sys.exit(1)
