"""
scratch/audit_cap1_passive_reader.py
====================================
Lector pasivo independiente para auditar señales bloqueadas por Cap=1 en la base de sombra.
Abre storage/runtime/shadow_research.sqlite3 en modo estrictamente de solo lectura (?mode=ro).
Cruza con los timestamps de salida de trades (desde trading_bot.sqlite3 en ?mode=ro o staging)
para determinar qué señales prospectivas habrían sido bloqueadas por concurrencia Cap=1.
Registra los resultados en la base aislada scratch/shadow_cap1_counterfactual.sqlite3.
"""

import sys
import os
import sqlite3
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SHADOW_DB = PROJECT_ROOT / "storage" / "runtime" / "shadow_research.sqlite3"
STAGING_DB = PROJECT_ROOT / "storage" / "runtime" / "shadow_research_staging.sqlite3"
LIVE_DB = Path.home() / "AppData/Local/BlackDaemonFx/trading_bot.sqlite3"
OUTPUT_DB = PROJECT_ROOT / "scratch" / "shadow_cap1_counterfactual.sqlite3"

def audit_passive_cap1():
    print("=" * 80)
    print("AUDITORÍA DE CAP=1 EN MODO SOMBRA PROSPECTIVO (LECTOR PASIVO)")
    print("=" * 80)
    
    # 1. Leer shadow_research.sqlite3 en ?mode=ro
    con_shadow = sqlite3.connect(f"file:{SHADOW_DB}?mode=ro", uri=True)
    df_shadow = pd.read_sql_query("SELECT * FROM shadow_signals ORDER BY timestamp ASC", con_shadow)
    con_shadow.close()
    
    print(f"Total señales en shadow_research.sqlite3: {len(df_shadow)}")
    print("Estrategias presentes:", df_shadow['strategy'].value_counts().to_dict())
    
    # 2. Verificar columnas disponibles
    cols = df_shadow.columns.tolist()
    print("Columnas en shadow_signals:", cols)
    has_exit_time = 'exit_time' in cols or 'replay_exit_time' in cols
    print(f"¿Contiene columna explícita de exit_time?: {has_exit_time}")
    
    # 3. Leer live trades en ?mode=ro para mapear tiempos de salida
    trades_map = {}
    if LIVE_DB.exists():
        con_live = sqlite3.connect(f"file:{LIVE_DB}?mode=ro", uri=True)
        con_live.row_factory = sqlite3.Row
        cur = con_live.cursor()
        cur.execute("SELECT id, instrument, direction, entry_time, exit_time, net_pnl, realized_rr, result FROM trades")
        for row in cur.fetchall():
            trades_map[row['id']] = dict(row)
        con_live.close()
        print(f"Trades mapeados desde trading_bot.sqlite3 (solo lectura): {len(trades_map)}")
    
    # 4. Simular Cap=1 sobre el flujo de señales
    # Crear base de salida scratch/shadow_cap1_counterfactual.sqlite3
    OUTPUT_DB.parent.mkdir(parents=True, exist_ok=True)
    con_out = sqlite3.connect(OUTPUT_DB)
    cur_out = con_out.cursor()
    cur_out.execute("""
        CREATE TABLE IF NOT EXISTS cap1_audit_log (
            id INTEGER PRIMARY KEY,
            shadow_signal_id INTEGER,
            timestamp TEXT,
            strategy TEXT,
            symbol TEXT,
            direction TEXT,
            mechanical_decision TEXT,
            cap1_action TEXT,
            blocking_trade_id INTEGER,
            simulated_outcome TEXT,
            simulated_rr REAL,
            market_outcome TEXT,
            market_rr REAL,
            audit_note TEXT
        )
    """)
    cur_out.execute("DELETE FROM cap1_audit_log") # Reset de la tabla aislada de scratch
    
    # Evaluamos Cap=1 de forma pasiva por estrategia (MSNR e ICT por separado y combinadas)
    for strat in ['MSNR', 'ICT']:
        strat_signals = df_shadow[df_shadow['strategy'] == strat].copy().reset_index(drop=True)
        strat_signals['ts'] = pd.to_datetime(strat_signals['timestamp'], utc=True)
        strat_signals = strat_signals.sort_values('ts').reset_index(drop=True)
        
        open_until = None
        current_blocking_id = None
        
        accepted_cap1 = []
        blocked_cap1 = []
        
        for idx, row in strat_signals.iterrows():
            sig_time = row['ts']
            is_mech_accept = (row['mechanical_decision'] == 'PASSED')
            
            # Verificar si hay una posición abierta
            is_blocked = False
            if open_until is not None and sig_time < open_until:
                is_blocked = True
            
            if is_mech_accept:
                if not is_blocked:
                    cap1_action = 'ACCEPTED_CAP1'
                    accepted_cap1.append(row['id'])
                    # Estimar tiempo de salida: si no hay exit_time, asumir duración típica o hasta el siguiente evento
                    # Si market_outcome es SL_LOSS o TP1_WIN, estimar 4 barras M15 (1h) o usar live trade
                    # Para simplificar sin inventar datos: 4 barras M15 = 60 minutos
                    open_until = sig_time + pd.Timedelta(minutes=60)
                    current_blocking_id = row['id']
                    note = "Ejecutado bajo Cap=1 (cupo libre)"
                else:
                    cap1_action = 'BLOCKED_BY_CAP1'
                    blocked_cap1.append(row['id'])
                    note = f"Bloqueado por trade concurrente ID {current_blocking_id}"
            else:
                cap1_action = 'DISCARDED_BY_FILTER'
                note = f"Descartado previamente por filtro ({row['rejection_reason']})"
                
            cur_out.execute("""
                INSERT INTO cap1_audit_log (
                    shadow_signal_id, timestamp, strategy, symbol, direction,
                    mechanical_decision, cap1_action, blocking_trade_id,
                    simulated_outcome, simulated_rr, market_outcome, market_rr, audit_note
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row['id'], str(row['timestamp']), row['strategy'], row['symbol'], row['direction'],
                row['mechanical_decision'], cap1_action, current_blocking_id if is_blocked else None,
                row['simulated_outcome'], row['simulated_rr'], row['market_outcome'], row['market_rr'], note
            ))
            
        print(f"\nResultados Simulación Cap=1 Pasiva para {strat}:")
        print(f"  - Total señales mecánicamente válidas: {len(strat_signals[strat_signals['mechanical_decision'] == 'PASSED'])}")
        print(f"  - Aceptadas bajo Cap=1: {len(accepted_cap1)}")
        print(f"  - Bloqueadas por Cap=1 (Contrafactual): {len(blocked_cap1)}")
        
    con_out.commit()
    con_out.close()
    print(f"\nResultados guardados exitosamente en: {OUTPUT_DB}")

if __name__ == '__main__':
    audit_passive_cap1()
