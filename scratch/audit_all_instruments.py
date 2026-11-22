import sqlite3
import json
import pandas as pd

p = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(f"file:{p}?mode=ro", uri=True)

# 1. Check all profiles in instrument_selection_profile_preferences
print("=== PERFILES DE INSTRUMENTOS EN /Instruments ===")
df_profiles = pd.read_sql_query("SELECT source, selection_profile, selected_symbols_json, updated_at FROM instrument_selection_profile_preferences WHERE source='DEMO'", conn)
active_instruments_by_profile = {}
all_active_symbols = set()

for idx, row in df_profiles.iterrows():
    prof = row['selection_profile']
    try:
        syms = json.loads(row['selected_symbols_json'])
        active_instruments_by_profile[prof] = syms
        all_active_symbols.update(syms)
        print(f"Profile: {prof} -> {len(syms)} instrumentos seleccionados")
    except Exception as e:
        print(f"Profile {prof} error: {e}")

print(f"\nTotal instrumentos únicos activos en /Instruments: {len(all_active_symbols)}")

# 2. Check trades count in DB for all these active symbols
df_trades = pd.read_sql_query("SELECT instrument, count(id) as trade_count, sum(case when result='WIN' or net_pnl > 0 then 1 else 0 end) as wins, sum(net_pnl) as total_pnl, min(entry_time) as first_trade, max(entry_time) as last_trade FROM trades GROUP BY instrument", conn)

# Merge
summary_list = []
trades_dict = {row['instrument']: row for _, row in df_trades.iterrows()}

for sym in sorted(all_active_symbols):
    t_info = trades_dict.get(sym)
    cnt = t_info['trade_count'] if t_info is not None else 0
    wins = t_info['wins'] if t_info is not None else 0
    wr = round((wins / cnt) * 100.0, 1) if cnt > 0 else 0.0
    pnl = round(t_info['total_pnl'], 2) if t_info is not None and pd.notnull(t_info['total_pnl']) else 0.0
    last_t = str(t_info['last_trade'])[:16] if t_info is not None and pd.notnull(t_info['last_trade']) else "NUNCA"
    
    summary_list.append({
        "symbol": sym,
        "live_trades": cnt,
        "win_rate": wr,
        "net_pnl": pnl,
        "last_trade": last_t
    })

df_summary = pd.DataFrame(summary_list)
print("\n=== RESUMEN DE ACTIVIDAD EN VIVO (TODOS LOS ACTIVOS DE /Instruments) ===")
print(df_summary.sort_values(by="live_trades", ascending=False).to_string())

conn.close()
