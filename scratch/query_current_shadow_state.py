"""
scratch/query_current_shadow_state.py
Consulta de solo lectura a storage/runtime/shadow_research.sqlite3
"""
import sqlite3

def main():
    conn = sqlite3.connect('file:storage/runtime/shadow_research.sqlite3?mode=ro', uri=True)
    cur = conn.cursor()
    
    cur.execute("SELECT count(*), min(timestamp), max(timestamp) FROM shadow_signals")
    tot, min_t, max_t = cur.fetchone()
    print(f"Total signals: {tot} | Min timestamp: {min_t} | Max timestamp: {max_t}")
    
    cur.execute("""
        SELECT strategy, variant, market_outcome, count(*), round(sum(market_rr), 4)
        FROM shadow_signals
        WHERE strategy='MSNR'
        GROUP BY strategy, variant, market_outcome
    """)
    rows = cur.fetchall()
    print("\nDesglose MSNR por variante y market_outcome:")
    for r in rows:
        print(f"  Strategy: {r[0]:4s} | Variant: {r[1]:22s} | Outcome: {str(r[2]):26s} | Count: {r[3]:2d} | Sum RR: {r[4]}")

    cur.execute("""
        SELECT id, timestamp, variant, symbol, direction, market_outcome, market_rr
        FROM shadow_signals
        WHERE strategy='MSNR' AND market_outcome IN ('SL_LOSS', 'TP1_WIN')
        ORDER BY timestamp
    """)
    closed = cur.fetchall()
    print(f"\nOperaciones CERRADAS (MSNR) en la base actual: {len(closed)}")
    for c in closed:
        print(f"  ID: {c[0]:2d} | Time: {c[1]} | Var: {c[2]:22s} | Sym: {c[3]:18s} | Dir: {c[4]:4s} | Outcome: {c[5]:10s} | RR: {c[6]:+6.2f}R")

if __name__ == '__main__':
    main()
