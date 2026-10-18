"""
scratch/inspect_source_trading_bot_signals.py
Inspección en modo estrictamente de solo lectura de la base fuente trading_bot.sqlite3
"""
import os
import sqlite3
import json
from pathlib import Path

def main():
    paths_to_check = [
        Path.home() / 'AppData/Local/BlackDaemonFx/trading_bot.sqlite3',
        Path(r"c:\TradingBoot\smc_synthetic_bot\storage\runtime\trading_bot.sqlite3"),
        Path(r"c:\TradingBoot\smc_synthetic_bot\trading_bot.sqlite3"),
    ]
    
    print("=" * 90)
    print("INSPECCIÓN DE SOLO LECTURA: FUENTES DE SEÑALES trading_bot.sqlite3")
    print("=" * 90)
    
    for p in paths_to_check:
        print(f"\nRuta: {p}")
        if not p.exists():
            print("  -> No existe.")
            continue
        print(f"  -> Existe. Tamaño: {p.stat().st_size:,d} bytes")
        
        # Conexión estrictamente read-only
        uri = f"file:{p}?mode=ro"
        try:
            conn = sqlite3.connect(uri, uri=True)
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [r[0] for r in cur.fetchall()]
            print(f"  -> Tablas: {tables}")
            
            if 'signals' in tables:
                cur.execute("SELECT count(*) FROM signals")
                cnt = cur.fetchone()[0]
                print(f"  -> Total filas en 'signals': {cnt}")
                
                cur.execute("SELECT MIN(created_at), MAX(created_at) FROM signals")
                min_ts, max_ts = cur.fetchone()
                print(f"  -> Rango created_at: {min_ts} a {max_ts}")
                
                # Señales desde 2026-10-15 en adelante
                cur.execute("SELECT count(*) FROM signals WHERE created_at >= '2026-10-15'")
                cnt_oct15 = cur.fetchone()[0]
                print(f"  -> Señales con created_at >= '2026-10-15': {cnt_oct15}")
                
                # Señales con created_at >= '2026-10-16'
                cur.execute("SELECT count(*) FROM signals WHERE created_at >= '2026-10-16'")
                cnt_oct16 = cur.fetchone()[0]
                print(f"  -> Señales con created_at >= '2026-10-16': {cnt_oct16}")
                
                # Últimas 10 señales
                cur.execute("""
                    SELECT id, created_at, instrument, direction, strategy_name, execution_status
                    FROM signals
                    ORDER BY id DESC LIMIT 10
                """)
                rows = cur.fetchall()
                print("  -> Últimas 10 señales en signals:")
                for r in rows:
                    print("     ", r)
                    
            if 'trades' in tables:
                cur.execute("SELECT count(*) FROM trades")
                t_cnt = cur.fetchone()[0]
                print(f"  -> Total filas en 'trades': {t_cnt}")
                cur.execute("SELECT MIN(open_time), MAX(open_time) FROM trades")
                min_t, max_t = cur.fetchone()
                print(f"  -> Rango open_time trades: {min_t} a {max_t}")
                cur.execute("""
                    SELECT id, symbol, direction, open_time, close_time, status, profit_loss
                    FROM trades ORDER BY id DESC LIMIT 5
                """)
                t_rows = cur.fetchall()
                print("  -> Últimos 5 trades en trades:")
                for r in t_rows:
                    print("     ", r)
                    
            conn.close()
        except Exception as e:
            print(f"  -> Error consultando DB: {e}")

if __name__ == '__main__':
    main()
