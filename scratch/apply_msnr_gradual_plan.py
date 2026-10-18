import sqlite3
import json
from datetime import datetime, timezone

DB_PATH = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"

# 1. LISTA DE ACTIVOS TIER 1 Y ALTA CONSISTENCIA (ACTIVADOS)
ACTIVE_SYMBOLS = [
    # Sintéticos Líderes Jump & Step
    "Jump 25 Index",
    "Jump 50 Index",
    "Jump 10 Index",
    "Step Index 400",
    "Step Index 500",
    "Step Index 200",
    "Step Index",
    # Boom & Crash (Dirección Institucional Única)
    "Boom 1000 Index",
    "Crash 1000 Index",
    "Boom 600 Index",
    "Crash 600 Index",
    "Boom 500 Index",
    "Crash 500 Index",
    "Boom 300 Index",
    "Crash 300 Index",
    # Macro, Cripto, Oro e Índices
    "BTCUSD",
    "XAUUSD",
    "Wall Street 30",
    "US Tech 100",
    # Forex Líderes con sesión / filtros A/V
    "USDJPY",
    "EURUSD",
    "GBPUSD",
    "GBPJPY",
    "AUDNZD",
    "GBPAUD"
]

# 2. ACTIVOS TÓXICOS EXCLUIDOS / PODADOS
TOXIC_SYMBOLS = [
    "Volatility 50 Index",
    "Volatility 100 Index",
    "Volatility 250 (1s) Index",
    "Volatility 75 (1s) Index",
    "US Oil",
    "CADCHF",
    "EURGBP",
    "AUDCHF",
    "EURCHF",
    "AUDCAD",
    "GBPCHF",
    "GBPNZD",
    "AUDUSD",
    "USDCAD",
    "USDCHF",
    "EURJPY",
    "EURNZD",
    "Volatility 25 Index",
    "Volatility 75 Index"
]

now_iso = datetime.now(timezone.utc).isoformat()

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Actualizar instrument_selection_profile_preferences para MALAYSIAN_SNR
for source in ["DEMO", "LIVE"]:
    row = cur.execute(
        "SELECT id, version FROM instrument_selection_profile_preferences WHERE source=? AND selection_profile='MALAYSIAN_SNR'",
        (source,)
    ).fetchone()
    
    if row:
        row_id, ver = row
        new_ver = (ver or 0) + 1
        cur.execute(
            "UPDATE instrument_selection_profile_preferences SET selected_symbols_json=?, version=?, updated_at=? WHERE id=?",
            (json.dumps(ACTIVE_SYMBOLS, ensure_ascii=False), new_ver, now_iso, row_id)
        )
        print(f"Actualizado instrument_selection_profile_preferences {source}: ID {row_id}, Nueva versión {new_ver}, Total {len(ACTIVE_SYMBOLS)} activos")
    else:
        cur.execute(
            "INSERT INTO instrument_selection_profile_preferences (source, selection_profile, selected_symbols_json, version, updated_at) VALUES (?, 'MALAYSIAN_SNR', ?, 1, ?)",
            (source, json.dumps(ACTIVE_SYMBOLS, ensure_ascii=False), now_iso)
        )
        print(f"Insertado instrument_selection_profile_preferences {source} con {len(ACTIVE_SYMBOLS)} activos")

# Actualizar strategy_runtime_preferences para MALAYSIAN_SNR
row_pref = cur.execute(
    "SELECT id, settings_json FROM strategy_runtime_preferences WHERE source='DEMO' AND strategy_name='MALAYSIAN_SNR' ORDER BY id DESC LIMIT 1"
).fetchone()

if row_pref:
    pref_id, current_json = row_pref
    settings = json.loads(current_json)
    
    # Configurar asset_modes y continuation_symbol_modes
    asset_modes = settings.get("asset_modes", {})
    continuation_symbol_modes = settings.get("continuation_symbol_modes", {})
    
    # Activar los líderes en live
    for sym in ACTIVE_SYMBOLS:
        asset_modes[sym] = "live"
        continuation_symbol_modes[sym] = "live"
        
    # Poner explícitamente en off a los tóxicos
    for sym in TOXIC_SYMBOLS:
        asset_modes[sym] = "off"
        continuation_symbol_modes[sym] = "off"
        
    settings["asset_modes"] = asset_modes
    settings["continuation_symbol_modes"] = continuation_symbol_modes
    settings["version"] = 19
    
    cur.execute(
        "INSERT INTO strategy_runtime_preferences (source, strategy_name, settings_json, updated_at) VALUES ('DEMO', 'MALAYSIAN_SNR', ?, ?)",
        (json.dumps(settings, ensure_ascii=False), now_iso)
    )
    print(f"Insertada Versión 19 en strategy_runtime_preferences para MALAYSIAN_SNR con {len(ACTIVE_SYMBOLS)} activos live y {len(TOXIC_SYMBOLS)} activos tóxicos en off.")

conn.commit()
conn.close()
print("Sincronización completa en SQLite.")
