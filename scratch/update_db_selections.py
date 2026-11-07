import json, sqlite3, os

for db_path in ["database/trading_bot.sqlite3", "storage/trading_bot.sqlite3"]:
    if not os.path.exists(db_path):
        continue
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # 1. Actualizar MALAYSIAN_SNR
    row = cur.execute("SELECT selected_symbols_json FROM instrument_selection_profile_preferences WHERE selection_profile = 'MALAYSIAN_SNR' ORDER BY id DESC LIMIT 1").fetchone()
    if row:
        syms = set(json.loads(row[0]))
    else:
        syms = set()
    
    to_add_msnr = [
        "USDCHF", "USDCHFmicro", "AUDCAD", "AUDCADmicro", "AUDUSD", "AUDUSDmicro",
        "Germany 40", "Vol over Boom 550", "Vol over Crash 550",
        "EURUSDmicro", "GBPUSDmicro", "USDJPYmicro", "USDCADmicro", "EURJPYmicro",
        "GBPJPYmicro", "EURAUDmicro", "AUDJPYmicro", "CADJPYmicro", "CHFJPYmicro",
        "CADCHFmicro", "EURGBPmicro", "GBPCHFmicro", "EURCADmicro", "NZDUSDmicro",
        "BTCUSDmicro", "ETHUSDmicro", "XAUUSDmicro", "XAUEUR", "XAUEURmicro"
    ]
    for s in to_add_msnr:
        syms.add(s)
    
    cur.execute(
        "INSERT INTO instrument_selection_profile_preferences (selection_profile, selected_symbols_json, source, version, updated_at) VALUES ('MALAYSIAN_SNR', ?, 'DEMO', 1, datetime('now'))",
        (json.dumps(sorted(syms)),)
    )
    print(f"[{db_path}] MALAYSIAN_SNR updated: total {len(syms)} active symbols")

    # 2. Actualizar ICT
    row_ict = cur.execute("SELECT selected_symbols_json FROM instrument_selection_profile_preferences WHERE selection_profile = 'ICT' ORDER BY id DESC LIMIT 1").fetchone()
    if row_ict:
        syms_ict = set(json.loads(row_ict[0]))
    else:
        syms_ict = set()
    
    to_add_ict = [
        "BTCUSD", "BTCUSDmicro", "XAUUSD", "XAUUSDmicro", "XAUEUR", "XAUEURmicro",
        "US Oil", "Wall Street 30", "US Tech 100"
    ]
    for s in to_add_ict:
        syms_ict.add(s)
    
    cur.execute(
        "INSERT INTO instrument_selection_profile_preferences (selection_profile, selected_symbols_json, source, version, updated_at) VALUES ('ICT', ?, 'DEMO', 1, datetime('now'))",
        (json.dumps(sorted(syms_ict)),)
    )
    print(f"[{db_path}] ICT updated: total {len(syms_ict)} active symbols")

    conn.commit()
    conn.close()
