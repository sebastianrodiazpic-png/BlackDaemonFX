import sqlite3
import pandas as pd
from pathlib import Path

db_path = Path("storage/runtime/shadow_research.sqlite3")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("=====================================================================")
print("CORRECCIÓN ESTRUCTURAL DE SHADOW_RESEARCH.SQLITE3 (AISLAMIENTO CONTRAFACTUAL)")
print("=====================================================================")

# 1. Comprobar si existen las columnas market_outcome, market_rr, contrafactual_note
cur.execute("PRAGMA table_info(shadow_signals)")
cols = [r['name'] for r in cur.fetchall()]
print("Columnas actuales en shadow_signals:", cols)

if "market_outcome" not in cols:
    cur.execute("ALTER TABLE shadow_signals ADD COLUMN market_outcome TEXT")
    print("Columna 'market_outcome' agregada exitosamente.")
if "market_rr" not in cols:
    cur.execute("ALTER TABLE shadow_signals ADD COLUMN market_rr REAL")
    print("Columna 'market_rr' agregada exitosamente.")
if "contrafactual_note" not in cols:
    cur.execute("ALTER TABLE shadow_signals ADD COLUMN contrafactual_note TEXT")
    print("Columna 'contrafactual_note' agregada exitosamente.")

# 2. Consultar todas las filas
cur.execute("SELECT * FROM shadow_signals ORDER BY id ASC")
all_rows = [dict(r) for r in cur.fetchall()]

print(f"Total registros a auditar y normalizar: {len(all_rows)}")

# Identificar por evento de mercado cuál fue el resultado real de mercado
# Agrupamos por (timestamp, symbol, direction)
events_market = {}
for r in all_rows:
    ev_key = (r['timestamp'], r['symbol'], r['direction'])
    out = r['simulated_outcome']
    rr = r['simulated_rr']
    
    # Si esta fila tiene un outcome real registrado, guardarlo como outcome de mercado para el evento
    if out in ['TP1_WIN', 'SL_LOSS', 'BE', 'CLOSED_OTHER']:
        events_market[ev_key] = (out, rr)
    elif out == 'SIMULATED_OPEN' and ev_key not in events_market:
        events_market[ev_key] = ('OPEN', 0.0)

print(f"Total eventos de mercado mapeados con desenlace: {len(events_market)}")

# 3. Aplicar separación rigurosa:
# - market_outcome y market_rr guardan lo que hizo el mercado
# - simulated_outcome y simulated_rr son EXCLUSIVAS de la variante:
#     * Si ACCEPTED_EXECUTION -> simulated_outcome = market_outcome, simulated_rr = market_rr
#     * Si DISCARDED_BY_FILTER -> simulated_outcome = 'AVOIDED', simulated_rr = 0.0, contrafactual_note = ...
corrected_accepted = 0
corrected_discarded = 0

for r in all_rows:
    row_id = r['id']
    ev_key = (r['timestamp'], r['symbol'], r['direction'])
    act = r['final_action']
    
    m_out, m_rr = events_market.get(ev_key, (r['simulated_outcome'] or 'PENDING_EVALUATION', 0.0))
    
    if act == 'ACCEPTED_EXECUTION':
        # La variante tomó el trade: asume el resultado del mercado
        s_out = m_out if m_out not in ['AVOIDED', 'PENDING_EVALUATION'] else (r['simulated_outcome'] or 'PENDING_EVALUATION')
        s_rr = m_rr if m_out in ['TP1_WIN', 'SL_LOSS', 'BE'] else (r['simulated_rr'] or 0.0)
        c_note = None
        cur.execute("""
            UPDATE shadow_signals
            SET market_outcome = ?, market_rr = ?, simulated_outcome = ?, simulated_rr = ?, contrafactual_note = ?
            WHERE id = ?
        """, (m_out, m_rr, s_out, s_rr, c_note, row_id))
        corrected_accepted += 1
        
    elif act == 'DISCARDED_BY_FILTER':
        # La variante NO tomó el trade: su simulated_rr es estrictamente 0.0 y su outcome es AVOIDED
        s_out = 'AVOIDED'
        s_rr = 0.0
        
        # Registrar nota contrafactual
        if m_out == 'SL_LOSS':
            c_note = f"CONTRAFACTUAL_LOSS_AVOIDED ({m_rr:+.2f}R)"
        elif m_out == 'TP1_WIN':
            c_note = f"CONTRAFACTUAL_WIN_MISSED ({m_rr:+.2f}R)"
        elif m_out == 'OPEN':
            c_note = "CONTRAFACTUAL_OPEN_EXPOSURE_AVOIDED"
        else:
            c_note = "CONTRAFACTUAL_FILTERED"
            
        cur.execute("""
            UPDATE shadow_signals
            SET market_outcome = ?, market_rr = ?, simulated_outcome = ?, simulated_rr = ?, contrafactual_note = ?
            WHERE id = ?
        """, (m_out, m_rr, s_out, s_rr, c_note, row_id))
        corrected_discarded += 1

conn.commit()
conn.close()

print(f"Normalización completada:")
print(f"  - Filas Aceptadas procesadas: {corrected_accepted}")
print(f"  - Filas Descartadas limpiadas con R=0.0 y AVOIDED: {corrected_discarded}")
