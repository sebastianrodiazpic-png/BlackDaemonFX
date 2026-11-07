import sys, json, sqlite3
conn = sqlite3.connect("database/trading_bot.sqlite3")
row = conn.execute("SELECT selected_symbols_json FROM instrument_selection_profile_preferences WHERE selection_profile = 'SYNTHETICS' ORDER BY id DESC LIMIT 1").fetchone()
if row:
    syms = json.loads(row[0])
    print(f"Total SYNTHETICS: {len(syms)}")
    print("Volatility 15 Index:", "Volatility 15 Index" in syms)
    print("Volatility 15 (1s) Index:", "Volatility 15 (1s) Index" in syms)
    print("Volatility 100 Index:", "Volatility 100 Index" in syms)
    print("Volatility 100 (1s) Index:", "Volatility 100 (1s) Index" in syms)
    
    # Asegurar que Volatility 100 Index y Volatility 15 Index esten activados
    updated = False
    if "Volatility 100 Index" not in syms:
        syms.append("Volatility 100 Index")
        updated = True
    if "Volatility 15 Index" not in syms:
        syms.append("Volatility 15 Index")
        updated = True
    if updated:
        syms.sort()
        conn.execute("INSERT INTO instrument_selection_profile_preferences (selection_profile, selected_symbols_json, source, version, updated_at) VALUES ('SYNTHETICS', ?, 'DEMO', 1, datetime('now'))", (json.dumps(syms),))
        conn.commit()
        print("Updated SYNTHETICS selection in DB to ensure both V15 and V100 are active.")
    else:
        print("Both V15 and V100 are already ACTIVE in DB.")
