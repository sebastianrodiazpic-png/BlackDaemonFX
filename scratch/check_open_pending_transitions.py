"""
scratch/check_open_pending_transitions.py
Consulta de solo lectura para verificar si las 1 OPEN y 6 PENDING de enabled_19_h4_fresh
cerraron en trading_bot.sqlite3
"""
import sqlite3
import pandas as pd
from pathlib import Path

def main():
    sh_path = Path("storage/runtime/shadow_research.sqlite3")
    live_path = Path.home() / "AppData/Local/BlackDaemonFx/trading_bot.sqlite3"
    
    conn_sh = sqlite3.connect(f"file:{sh_path}?mode=ro", uri=True)
    df_p = pd.read_sql("""
        SELECT id, timestamp, strategy, variant, symbol, direction, entry_price, market_outcome, market_rr, features_json
        FROM shadow_signals
        WHERE strategy='MSNR' AND variant='enabled_19_h4_fresh' AND market_outcome IN ('OPEN', 'PENDING_EVALUATION')
        ORDER BY id ASC
    """, conn_sh)
    conn_sh.close()
    
    print("=" * 90)
    print("VERIFICACIÓN DE ESTADO EN MERCADO DE SEÑALES OPEN / PENDING EN SHADOW")
    print("=" * 90)
    print(f"Total señales a verificar: {len(df_p)}")
    
    conn_live = sqlite3.connect(f"file:{live_path}?mode=ro", uri=True)
    conn_live.row_factory = sqlite3.Row
    cur_live = conn_live.cursor()
    
    for _, r in df_p.iterrows():
        sig_id = r['id']
        sym = r['symbol']
        dir_ = r['direction']
        ts = r['timestamp']
        current_mkt = r['market_outcome']
        
        # Buscar trade en live trades dentro de ventana de 2 horas desde ts
        sig_dt = pd.to_datetime(ts, utc=True)
        window_start = (sig_dt - pd.Timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
        window_end = (sig_dt + pd.Timedelta(hours=4)).strftime("%Y-%m-%d %H:%M:%S")
        
        cur_live.execute("""
            SELECT id, instrument, direction, entry_time, exit_time, status, result, realized_rr, net_pnl, exit_reason
            FROM trades
            WHERE instrument = ? AND direction = ? AND entry_time >= ? AND entry_time <= ?
            ORDER BY id ASC
        """, (sym, dir_, window_start, window_end))
        
        matched_trades = [dict(t) for t in cur_live.fetchall()]
        print(f"\nSeñal Shadow #{sig_id}: {sym} {dir_} @ {ts} | Estado Shadow: {current_mkt}")
        if matched_trades:
            for mt in matched_trades:
                print(f"  -> Match Trade #{mt['id']}: entry={mt['entry_time']}, exit={mt['exit_time']}, status={mt['status']}, result={mt['result']}, rr={mt['realized_rr']}, pnl={mt['net_pnl']}, reason={mt['exit_reason']}")
        else:
            print("  -> Sin trade correspondiente en broker/live.")
            
    conn_live.close()

if __name__ == '__main__':
    main()
