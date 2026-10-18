import sqlite3
import pandas as pd
from pathlib import Path

# 1. Leer trades completados de hoy de la DB en vivo en modo SOLO LECTURA
live_db = Path.home() / 'AppData/Local/BlackDaemonFx/trading_bot.sqlite3'
conn_live = sqlite3.connect(f'file:{live_db}?mode=ro', uri=True)
conn_live.row_factory = sqlite3.Row
cur_live = conn_live.cursor()

cur_live.execute("""
    SELECT id, instrument, direction, status, result, entry_time, exit_time,
           entry_price, exit_price, realized_rr, net_pnl, exit_reason
    FROM trades
    WHERE (entry_time >= '2026-10-15' OR exit_time >= '2026-10-15')
    ORDER BY id ASC
""")
live_trades = [dict(r) for r in cur_live.fetchall()]
conn_live.close()

# 2. Conectar a shadow_research.sqlite3
shadow_db = Path("storage/runtime/shadow_research.sqlite3")
conn_shadow = sqlite3.connect(shadow_db)
conn_shadow.row_factory = sqlite3.Row
cur_shadow = conn_shadow.cursor()

cur_shadow.execute("SELECT * FROM shadow_signals WHERE simulated_outcome = 'PENDING_EVALUATION' OR simulated_outcome IS NULL")
pending_signals = [dict(r) for r in cur_shadow.fetchall()]

updated_count = 0
for ss in pending_signals:
    s_sym = ss['symbol']
    s_dir = ss['direction']
    s_time = pd.to_datetime(ss['timestamp'], utc=True)
    
    # Buscar trade coincidente
    matched = None
    for lt in live_trades:
        if lt['instrument'] == s_sym and lt['direction'] == s_dir:
            t_time = pd.to_datetime(lt['entry_time'], utc=True)
            if abs((s_time - t_time).total_seconds()) <= 300: # 5 min
                matched = lt
                break
                
    if matched and matched['status'] == 'CLOSED':
        # Determinar outcome y rr
        res = matched['result']
        realized_rr = matched['realized_rr']
        if res == 'WIN':
            outcome = 'TP1_WIN'
            rr = round(float(realized_rr or 1.0), 4)
        elif res == 'LOSS':
            outcome = 'SL_LOSS'
            rr = round(float(realized_rr or -1.0), 4)
        elif res == 'BE' or (realized_rr is not None and abs(float(realized_rr)) < 0.1):
            outcome = 'BE'
            rr = 0.0
        else:
            outcome = 'CLOSED_OTHER'
            rr = round(float(realized_rr or 0.0), 4)
            
        cur_shadow.execute("""
            UPDATE shadow_signals
            SET simulated_outcome = ?, simulated_rr = ?
            WHERE id = ?
        """, (outcome, rr, ss['id']))
        updated_count += 1
    elif matched and matched['status'] == 'OPEN':
        # Marcar como OPEN_POSITION
        cur_shadow.execute("""
            UPDATE shadow_signals
            SET simulated_outcome = 'SIMULATED_OPEN'
            WHERE id = ?
        """, (ss['id'],))

conn_shadow.commit()
conn_shadow.close()
print(f"Actualizadas {updated_count} señales en shadow_research.sqlite3 con resultados reales cerrados.")
