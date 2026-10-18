import sqlite3
import json
from pathlib import Path
import pandas as pd

# 1. Leer trades completados de hoy de la DB en vivo (Read-Only)
live_db = Path.home() / 'AppData/Local/BlackDaemonFx/trading_bot.sqlite3'
conn_live = sqlite3.connect(f'file:{live_db}?mode=ro', uri=True)
conn_live.row_factory = sqlite3.Row
cur_live = conn_live.cursor()

cur_live.execute("""
    SELECT id, instrument, direction, status, result, entry_time, exit_time,
           entry_price, exit_price, realized_rr, net_pnl, exit_reason, setup_reason
    FROM trades
    WHERE (entry_time >= '2026-10-15' OR exit_time >= '2026-10-15')
    ORDER BY id ASC
""")
live_trades = [dict(r) for r in cur_live.fetchall()]
conn_live.close()

print(f"Total trades en live bot hoy: {len(live_trades)}")

# 2. Conectar a shadow_research.sqlite3
shadow_db = Path("storage/runtime/shadow_research.sqlite3")
conn_shadow = sqlite3.connect(shadow_db)
conn_shadow.row_factory = sqlite3.Row
cur_shadow = conn_shadow.cursor()

cur_shadow.execute("SELECT * FROM shadow_signals ORDER BY id ASC")
shadow_signals = [dict(r) for r in cur_shadow.fetchall()]

print(f"Total shadow signals: {len(shadow_signals)}")

# Comprobar cuántas señales coinciden en activo, dirección y ventana de tiempo (+/- 5 minutos)
matches = []
for ss in shadow_signals:
    s_sym = ss['symbol']
    s_dir = ss['direction']
    s_time = pd.to_datetime(ss['timestamp'], utc=True)
    
    matched_trade = None
    for lt in live_trades:
        if lt['instrument'] == s_sym and lt['direction'] == s_dir:
            t_time = pd.to_datetime(lt['entry_time'], utc=True)
            diff_sec = abs((s_time - t_time).total_seconds())
            if diff_sec <= 300: # 5 min tolerance
                matched_trade = lt
                break
    
    if matched_trade:
        matches.append({
            'shadow_id': ss['id'],
            'strategy': ss['strategy'],
            'variant': ss['variant'],
            'symbol': s_sym,
            'direction': s_dir,
            'final_action': ss['final_action'],
            'rejection_reason': ss['rejection_reason'],
            'live_status': matched_trade['status'],
            'live_result': matched_trade['result'],
            'live_rr': matched_trade['realized_rr'],
            'live_exit_reason': matched_trade['exit_reason'],
            'time_diff_sec': diff_sec
        })

print(f"Total coincidencias exactas entre señales shadow y operaciones en vivo: {len(matches)}")
df_matches = pd.DataFrame(matches)
if not df_matches.empty:
    print(df_matches.to_string())

conn_shadow.close()
