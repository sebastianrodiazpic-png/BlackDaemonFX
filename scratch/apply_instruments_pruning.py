import sqlite3
import json
import shutil
import os
from datetime import datetime

DB_PATHS = [
    r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3",
    r"C:\TradingBoot\smc_synthetic_bot\storage\trading_bot.sqlite3",
    r"C:\TradingBoot\smc_synthetic_bot\database\trading_bot.sqlite3"
]

# Definición de activos filtrados por rentabilidad demostrada (5A Replay + En Vivo)
ACTIVE_SYNTHETICS = sorted([
    # Jump (Todos los 5 activos, incluyendo rehabilitación de Jump 100)
    "Jump 10 Index", "Jump 25 Index", "Jump 50 Index", "Jump 75 Index", "Jump 100 Index",
    # Boom & Crash (Solo los probados con expectativa positiva)
    "Boom 300 Index", "Boom 500 Index", "Boom 600 Index", "Boom 900 Index", "Boom 1000 Index",
    "Crash 500 Index", "Crash 900 Index", "Crash 1000 Index",
    # Volatility Sólidos
    "Volatility 5 Index", "Volatility 10 Index", "Volatility 50 Index", "Volatility 75 Index",
    "Volatility 90 Index", "Volatility 100 Index",
    "Volatility 5 (1s) Index", "Volatility 10 (1s) Index", "Volatility 15 (1s) Index",
    "Volatility 25 (1s) Index", "Volatility 30 (1s) Index", "Volatility 75 (1s) Index",
    "Volatility 100 (1s) Index", "Volatility 150 (1s) Index", "Volatility 250 (1s) Index",
    # Step Ganadores
    "Step Index 400", "Step Index 500",
    # VolSwitch / Híbridos
    "Vol over Boom 550", "Vol over Crash 550", "VolSwitch High Vol Index"
])

ACTIVE_FOREX = sorted([
    "USDCHF", "USDCHFmicro",
    "USDCAD", "USDCADmicro",
    "EURUSD", "EURUSDmicro",
    "GBPUSD", "GBPUSDmicro",
    "GBPJPY", "GBPJPYmicro",
    "EURJPY", "EURJPYmicro",
    "CADCHF", "CADCHFmicro"
])

ACTIVE_ORB = sorted([
    "Wall Street 30", "US Tech 100", "Germany 40",
    "BTCUSD", "BTCUSDmicro",
    "US Oil", "UK Brent Oil",
    "XAUUSD", "XAUUSDmicro", "microXAUUSD",
    "USDCAD", "USDCADmicro",
    "USDCHF", "USDCHFmicro",
    "GBPUSD", "GBPUSDmicro",
    "EURUSD", "EURUSDmicro"
])

ACTIVE_ICT = sorted([
    "Wall Street 30", "US Tech 100", "Germany 40",
    "BTCUSD", "BTCUSDmicro",
    "US Oil", "UK Brent Oil",
    "XAUUSD", "XAUUSDmicro", "microXAUUSD",
    "Jump 100 Index", "Jump 75 Index", "Jump 25 Index", "Jump 10 Index", "Jump 50 Index",
    "Crash 500 Index", "Boom 500 Index", "Boom 600 Index", "Crash 1000 Index",
    "Volatility 10 Index", "Volatility 90 Index", "Volatility 150 (1s) Index",
    "USDCHF", "USDCAD", "GBPUSD"
])

ACTIVE_COMMODITIES = sorted([
    "US Oil", "UK Brent Oil",
    "XAUUSD", "XAUUSDmicro", "microXAUUSD"
])

ACTIVE_INDICES = sorted([
    "Wall Street 30", "US Tech 100", "Germany 40"
])

ACTIVE_MSNR = sorted([
    "Jump 10 Index", "Jump 25 Index", "Jump 50 Index", "Jump 75 Index", "Jump 100 Index",
    "Crash 500 Index", "Crash 900 Index", "Crash 1000 Index",
    "Boom 300 Index", "Boom 500 Index", "Boom 600 Index", "Boom 900 Index", "Boom 1000 Index",
    "Volatility 10 Index", "Volatility 50 Index", "Volatility 75 Index", "Volatility 90 Index", "Volatility 100 Index",
    "Volatility 10 (1s) Index", "Volatility 15 (1s) Index", "Volatility 75 (1s) Index", "Volatility 100 (1s) Index", "Volatility 150 (1s) Index", "Volatility 250 (1s) Index",
    "Step Index 400", "Step Index 500",
    "Wall Street 30", "US Tech 100", "XAUUSD", "US Oil", "BTCUSD"
])

for db_path in DB_PATHS:
    if not os.path.exists(db_path):
        continue
    print(f"\n--- Actualizando {db_path} ---")
    # Backup
    bak_path = f"{db_path}.bak_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(db_path, bak_path)
    print(f"Backup creado: {bak_path}")
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Check if table exists
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='instrument_selection_profile_preferences'")
    if cur.fetchone():
        updates = [
            ("SYNTHETICS", ACTIVE_SYNTHETICS),
            ("FOREX", ACTIVE_FOREX),
            ("FOREX_SNR", ACTIVE_FOREX),
            ("ORB", ACTIVE_ORB),
            ("ICT", ACTIVE_ICT),
            ("MSNR", ACTIVE_MSNR),
            ("MALAYSIAN_SNR", ACTIVE_MSNR),
            ("COMMODITIES_SNR", ACTIVE_COMMODITIES),
            ("INDICESB_SNR", ACTIVE_INDICES),
            ("FLIP", []) # Podar FLIP completamente
        ]
        
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for prof, syms in updates:
            syms_json = json.dumps(syms)
            cur.execute("""
                UPDATE instrument_selection_profile_preferences 
                SET selected_symbols_json = ?, updated_at = ? 
                WHERE selection_profile = ?
            """, (syms_json, now_str, prof))
            rows_aff = cur.rowcount
            print(f"  Perfil '{prof}': {len(syms)} activos asignados (Filas afectadas: {rows_aff})")
        
        conn.commit()
    conn.close()

print("\n¡Actualización de perfiles en SQLite completada con éxito!")
