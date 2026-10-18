import sqlite3
import json
from pathlib import Path

def inspect_msnr_signals():
    stg_path = Path("storage/runtime/shadow_research_staging.sqlite3")
    conn_stg = sqlite3.connect(f"file:{stg_path.resolve()}?mode=ro", uri=True)
    cur = conn_stg.cursor()
    cur.execute("SELECT id, timestamp, strategy, variant, symbol, direction, entry_price, stop_loss, take_profit_1, take_profit_2, features_json, simulated_outcome, simulated_rr FROM shadow_signals WHERE strategy='MSNR'")
    rows = cur.fetchall()
    print("=== MSNR ROWS IN STAGING ===")
    for r in rows:
        feat = json.loads(r[10]) if r[10] else {}
        print(f"ID: {r[0]} | TS: {r[1]} | Sym: {r[4]} | Dir: {r[5]} | EP: {r[6]} | SL: {r[7]} | TP1: {r[8]} | TP2: {r[9]} | SimOut: {r[11]} | RR: {r[12]}")
        print(f"  source_signal_id: {feat.get('source_signal_id')}, created_at_live: {feat.get('created_at_live')}, raw_action: {feat.get('raw_action')}, score: {feat.get('score')}")
    conn_stg.close()

    # Now inspect production databases to find the source signals 21243 and 21244
    db_candidates = [
        Path.home() / "AppData/Local/BlackDaemonFx/trading_bot.sqlite3",
        Path("trading_bot.sqlite3"),
        Path("data/trading_bot.db"),
    ]
    for db in db_candidates:
        if db.exists() and db.stat().st_size > 0:
            print(f"\n=== INSPECTING PROD DB: {db} ===")
            conn = sqlite3.connect(f"file:{db.resolve()}?mode=ro", uri=True)
            cur = conn.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    if (Path.home() / "AppData/Local/BlackDaemonFx/trading_bot.sqlite3").exists():
        live_db = Path.home() / "AppData/Local/BlackDaemonFx/trading_bot.sqlite3"
        conn = sqlite3.connect(f"file:{live_db.resolve()}?mode=ro", uri=True)
        cur = conn.cursor()
        cur.execute("SELECT id, instrument, timeframe, signal_time, direction, valid, details_json, created_at FROM signals WHERE id IN (21268, 21272, 21279, 21286, 21290) ORDER BY id")
        rows = cur.fetchall()
        print("\n=== REAL MSNR SOURCE SIGNALS IN LIVE DB ===")
        for r in rows:
            det = json.loads(r[6]) if r[6] else {}
            s_name = det.get('strategy_name')
            ep = det.get('entry_price')
            sl = det.get('stop_loss')
            tp = det.get('take_profit')
            print(f"ID {r[0]} | Inst: {r[1]:<16} | Time: {r[3]} | Dir: {r[4]} | Strat: {s_name} | EP: {ep} | SL: {sl} | TP: {tp} | Created: {r[7]}")
        conn.close()

if __name__ == "__main__":
    inspect_msnr_signals()
