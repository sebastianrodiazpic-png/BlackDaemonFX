import json, sqlite3, os
from pathlib import Path

# Flop instruments to prune per profile:
PRUNE_MAP = {
    "MALAYSIAN_SNR": {
        "Volatility 25 Index", "Crash 600 Index", "Crash 300 Index", 
        "Volatility 15 Index", "Volatility 50 (1s) Index", "Boom 900 Index"
    },
    "MSNR": {
        "Volatility 25 Index", "Crash 600 Index", "Crash 300 Index", 
        "Volatility 15 Index", "Volatility 50 (1s) Index", "Boom 900 Index"
    },
    "SYNTHETICS": {
        "Volatility 25 Index", "Crash 600 Index"
    },
    "ICT": {
        "Crash 300 Index", "Jump 10 Index", "Step Index", "US SP 500"
    },
    "ORB": {
        "EURUSD", "EURUSDmicro", "US SP 500"
    },
    "FOREX": {
        "EURUSD", "EURUSDmicro"
    },
    "FOREX_SNR": {
        "EURUSD", "EURUSDmicro"
    }
}

target_dbs = []
appdata_db = Path(os.environ.get('LOCALAPPDATA', '')) / 'BlackDaemonFx' / 'trading_bot.sqlite3'
if appdata_db.exists():
    target_dbs.append(appdata_db)
workspace_db = Path("storage/trading_bot.sqlite3")
if workspace_db.exists():
    target_dbs.append(workspace_db)

print("Targets:", target_dbs)

for db in target_dbs:
    print(f"\n--- Checking {db} ---")
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, source, selection_profile, version, selected_symbols_json FROM instrument_selection_profile_preferences")
    rows = cur.fetchall()
    for r in rows:
        profile = r['selection_profile']
        syms = json.loads(r['selected_symbols_json'] or "[]")
        prune_set = PRUNE_MAP.get(profile, set())
        to_prune = [s for s in syms if s in prune_set]
        new_syms = [s for s in syms if s not in prune_set]
        if to_prune:
            print(f"[{r['source']}:{profile}] Pruning {len(to_prune)} symbols: {to_prune} (remaining: {len(new_syms)})")
        else:
            print(f"[{r['source']}:{profile}] Clean ({len(syms)} symbols)")
    conn.close()
