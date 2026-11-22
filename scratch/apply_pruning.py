import json, sqlite3, os
from datetime import datetime, timezone
from pathlib import Path

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

now_iso = datetime.now(timezone.utc).isoformat()

for db in target_dbs:
    print(f"\nApplying pruning to {db}...")
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, source, selection_profile, version, selected_symbols_json FROM instrument_selection_profile_preferences")
    rows = cur.fetchall()
    updated = 0
    for r in rows:
        row_id = r['id']
        source = r['source']
        profile = r['selection_profile']
        version = (r['version'] or 1) + 1
        syms = json.loads(r['selected_symbols_json'] or "[]")
        prune_set = PRUNE_MAP.get(profile, set())
        to_prune = [s for s in syms if s in prune_set]
        new_syms = [s for s in syms if s not in prune_set]
        if to_prune:
            cur.execute("""
                UPDATE instrument_selection_profile_preferences
                SET selected_symbols_json = ?, version = ?, updated_at = ?
                WHERE id = ?
            """, (json.dumps(new_syms, ensure_ascii=False), version, now_iso, row_id))
            
            # Record audit event
            try:
                cur.execute("""
                    INSERT INTO daemon_audit_events (event_time, source, event_type, instrument, action, reason, details_json)
                    VALUES (?, ?, 'INSTRUMENT_SELECTION_PROFILE_CHANGED', NULL, 'PROFILE_SELECTION_PRUNED_TOXIC_INSTRUMENTS', ?, ?)
                """, (now_iso, source, profile, json.dumps({
                    "pruned_symbols": to_prune,
                    "remaining_count": len(new_syms),
                    "version": version
                })))
            except Exception as e:
                print("Audit event insert error:", e)

            print(f"  [{source}:{profile}] Pruned {len(to_prune)} toxic symbols -> v{version}")
            updated += 1
            
    conn.commit()
    conn.close()
    print(f"Committed {updated} profile updates on {db}.")
