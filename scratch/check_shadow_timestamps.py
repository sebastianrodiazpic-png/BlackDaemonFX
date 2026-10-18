"""
scratch/check_shadow_timestamps.py
Consulta de solo lectura a storage/runtime/shadow_research.sqlite3 (tabla shadow_signals)
"""
import sqlite3

def main():
    conn = sqlite3.connect('file:storage/runtime/shadow_research.sqlite3?mode=ro', uri=True)
    cur = conn.cursor()
    cur.execute("""
        SELECT id, timestamp, strategy, variant, symbol, direction, simulated_outcome, simulated_rr, market_outcome, market_rr
        FROM shadow_signals 
        WHERE strategy='MSNR' AND market_outcome IS NOT NULL AND market_outcome != ''
        ORDER BY timestamp
    """)
    rows = cur.fetchall()
    print(f"Total registros evaluados de mercado para MSNR: {len(rows)}")
    closed_losses = []
    closed_wins = []
    for r in rows:
        print(f"  ID: {r[0]:2d} | Time: {r[1]} | Var: {r[3]:22s} | Sym: {r[4]:18s} | Dir: {r[5]:4s} | MktOutcome: {r[8]:15s} | MktRR: {r[9]:+6.2f}R")
        if r[8] == 'SL_LOSS':
            closed_losses.append(r)
        elif r[8] == 'TP1_WIN':
            closed_wins.append(r)
            
    print(f"\nResumen MSNR: {len(closed_wins)} Wins, {len(closed_losses)} Losses")
    cur.execute("SELECT MIN(timestamp), MAX(timestamp) FROM shadow_signals")
    min_t, max_t = cur.fetchone()
    print(f"Rango temporal total en shadow_signals: {min_t} a {max_t}")

if __name__ == '__main__':
    main()
