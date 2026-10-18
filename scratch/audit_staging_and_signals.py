import sqlite3
import json
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path("c:/TradingBoot/smc_synthetic_bot")
LIVE_DB_PATH = Path.home() / "AppData/Local/BlackDaemonFx/trading_bot.sqlite3"
STAGING_DB_PATH = PROJECT_ROOT / "storage" / "runtime" / "shadow_research_staging.sqlite3"
PRIMARY_SHADOW_DB = PROJECT_ROOT / "storage" / "runtime" / "shadow_research.sqlite3"

CUTOFF_ISO = "2026-10-15T17:35:16.304722+00:00"
CUTOFF_DT = pd.to_datetime(CUTOFF_ISO, utc=True)

def audit_all():
    print("===================================================================")
    print("AUDITORIA DE STAGING, SENALES Y TRADES")
    print("===================================================================")

    # 1. Esquema y contenido de STAGING
    print("\n--- 1. AUDITORIA DE SHADOW_RESEARCH_STAGING.SQLITE3 ---")
    if not STAGING_DB_PATH.exists():
        print(f"ERROR: {STAGING_DB_PATH} no existe.")
        return

    conn_stg = sqlite3.connect(STAGING_DB_PATH)
    conn_stg.row_factory = sqlite3.Row
    cur_stg = conn_stg.cursor()

    cur_stg.execute("PRAGMA table_info(shadow_signals)")
    cols = [dict(r) for r in cur_stg.fetchall()]
    print(f"Columnas en shadow_signals ({len(cols)}): {[c['name'] for c in cols]}")

    cur_stg.execute("SELECT count(*) FROM shadow_signals")
    total_stg_rows = cur_stg.fetchone()[0]
    print(f"Total filas en staging: {total_stg_rows}")

    cur_stg.execute("""
        SELECT strategy, variant, count(*) as count,
               sum(CASE WHEN final_action='ACCEPTED_EXECUTION' THEN 1 ELSE 0 END) as accepted,
               sum(CASE WHEN final_action='DISCARDED_BY_FILTER' THEN 1 ELSE 0 END) as discarded
        FROM shadow_signals
        GROUP BY strategy, variant
    """)
    strat_breakdown = [dict(r) for r in cur_stg.fetchall()]
    for sb in strat_breakdown:
        print(f"  {sb['strategy']} | {sb['variant']}: total={sb['count']}, accepted={sb['accepted']}, discarded={sb['discarded']}")

    # Filas detalladas en staging
    cur_stg.execute("""
        SELECT id, timestamp, strategy, variant, symbol, direction, entry_price, 
               final_action, simulated_outcome, simulated_rr, market_outcome, market_rr, 
               contrafactual_note, features_json
        FROM shadow_signals
        ORDER BY id ASC
    """)
    stg_rows = [dict(r) for r in cur_stg.fetchall()]

    events_map = {}
    for r in stg_rows:
        feat = json.loads(r["features_json"]) if r["features_json"] else {}
        src_id = feat.get("source_signal_id")
        ev_uuid = feat.get("event_uuid")
        cohort = feat.get("cohort_tag")
        created_live = feat.get("created_at_live")
        
        if ev_uuid not in events_map:
            events_map[ev_uuid] = {
                "source_signal_id": src_id,
                "strategy": r["strategy"],
                "symbol": r["symbol"],
                "direction": r["direction"],
                "timestamp": r["timestamp"],
                "created_live": created_live,
                "cohort": cohort,
                "variants": [],
                "market_outcome": r["market_outcome"],
                "market_rr": r["market_rr"],
                "contrafactual_note": r["contrafactual_note"],
                "simulated_outcomes": []
            }
        events_map[ev_uuid]["variants"].append(r["variant"])
        events_map[ev_uuid]["simulated_outcomes"].append((r["variant"], r["final_action"], r["simulated_outcome"], r["simulated_rr"]))

    print(f"\nTotal eventos de mercado unicos en staging: {len(events_map)}")
    for ev_id, ev in events_map.items():
        print(f"\nEvento: {ev_id}")
        print(f"  Src ID: {ev['source_signal_id']} | Strat: {ev['strategy']} | Sym: {ev['symbol']} | Dir: {ev['direction']}")
        print(f"  Timestamp (Mercado): {ev['timestamp']} | Created Live: {ev['created_live']} | Cohorte: {ev['cohort']}")
        print(f"  Mercado Real: outcome={ev['market_outcome']}, rr={ev['market_rr']}, note={ev['contrafactual_note']}")
        print(f"  Variantes ({len(ev['variants'])}): {ev['variants']}")
        for v, act, out, rr in ev["simulated_outcomes"]:
            print(f"    - {v}: {act} -> outcome={out}, rr={rr}")

    # Verificar banderas AVOIDED
    cur_stg.execute("SELECT count(*) FROM shadow_signals WHERE final_action='DISCARDED_BY_FILTER' AND (simulated_outcome != 'AVOIDED' OR simulated_rr != 0.0)")
    bad_discarded = cur_stg.fetchone()[0]
    print(f"\nVerificacion AVOIDED: {bad_discarded} senales descartadas incorrectas (debe ser 0).")

    conn_stg.close()

    # 2. AUDITORÍA DE TRADING_BOT.SQLITE3 (SOLO LECTURA)
    print("\n--- 2. AUDITORIA DE TRADING_BOT.SQLITE3 (SOLO LECTURA) ---")
    live_uri = f"file:{LIVE_DB_PATH.resolve()}?mode=ro"
    conn_live = sqlite3.connect(live_uri, uri=True)
    conn_live.row_factory = sqlite3.Row
    cur_live = conn_live.cursor()

    cur_live.execute("""
        SELECT id, instrument, timeframe, signal_time, direction, valid, details_json, created_at
        FROM signals
        WHERE created_at >= '2026-10-15 17:00:00'
        ORDER BY id ASC
    """)
    all_signals_since_17 = [dict(r) for r in cur_live.fetchall()]
    print(f"Total senales desde 17:00 UTC en trading_bot: {len(all_signals_since_17)}")

    cur_live.execute("""
        SELECT id, instrument, timeframe, signal_time, direction, valid, details_json, created_at
        FROM signals
        WHERE created_at >= '2026-10-15 17:35:16'
        ORDER BY id ASC
    """)
    signals_post_created = [dict(r) for r in cur_live.fetchall()]
    print(f"Total senales con created_at >= 17:35:16 UTC: {len(signals_post_created)}")

    cur_live.execute("""
        SELECT id, instrument, timeframe, signal_time, direction, valid, details_json, created_at
        FROM signals
        WHERE signal_time >= '2026-10-15 17:35:16'
        ORDER BY id ASC
    """)
    signals_post_signal_time = [dict(r) for r in cur_live.fetchall()]
    print(f"Total senales con signal_time >= 17:35:16 UTC: {len(signals_post_signal_time)}")

    # Analisis de los 13 IDs de staging
    stg_src_ids = sorted(list(set([ev["source_signal_id"] for ev in events_map.values()])))
    print(f"\nIDs de origen en staging ({len(stg_src_ids)}): {stg_src_ids}")

    for sid in stg_src_ids:
        cur_live.execute("SELECT * FROM signals WHERE id = ?", (sid,))
        s_row = dict(cur_live.fetchone())
        det = json.loads(s_row["details_json"]) if s_row["details_json"] else {}
        s_time = s_row["signal_time"]
        c_time = s_row["created_at"]
        dt_s = pd.to_datetime(s_time, utc=True)
        dt_c = pd.to_datetime(c_time, utc=True)
        diff_sec = (dt_c - dt_s).total_seconds()
        is_sig_prospective = dt_s >= CUTOFF_DT
        is_cre_prospective = dt_c >= CUTOFF_DT
        print(f"ID {sid}: sym={s_row['instrument']}, strat={det.get('strategy_name')}, dir={s_row['direction']}")
        print(f"   signal_time={s_time} (prosp={is_sig_prospective}), created_at={c_time} (prosp={is_cre_prospective}), diff={diff_sec:.1f}s")

    # 3. AUDITORIA DE TRADES EN TRADING_BOT.SQLITE3
    print("\n--- 3. AUDITORIA DE TRADES EN TRADING_BOT.SQLITE3 ---")
    cur_live.execute("""
        SELECT id, instrument, direction, entry_time, exit_time, entry_price, exit_price,
               net_pnl, realized_rr, result, exit_reason
        FROM trades
        WHERE entry_time >= '2026-10-15 17:00:00'
        ORDER BY id ASC
    """)
    trades_since_17 = [dict(r) for r in cur_live.fetchall()]
    print(f"Total trades desde 17:00 UTC en trading_bot: {len(trades_since_17)}")
    for t in trades_since_17:
        print(f"  Trade ID {t['id']}: sym={t['instrument']}, dir={t['direction']}, entry={t['entry_time']}, exit={t['exit_time']}, pnl={t['net_pnl']}, rr={t['realized_rr']}, res={t['result']}, reason={t['exit_reason']}")

    # Investigar los dos eventos asociados a trades
    print("\nInvestigando eventos con market_outcome != PENDING_EVALUATION:")
    for ev_id, ev in events_map.items():
        if ev["market_outcome"] != "PENDING_EVALUATION":
            print(f"\nEvento {ev_id} (Src ID {ev['source_signal_id']}):")
            print(f"  sym={ev['symbol']}, strat={ev['strategy']}, timestamp={ev['timestamp']}, created={ev['created_live']}")
            print(f"  market_outcome={ev['market_outcome']}, market_rr={ev['market_rr']}")
            print(f"  note={ev['contrafactual_note']}")

            # Verificar si existe en trades y como fue el match
            sig_time = pd.to_datetime(ev["timestamp"], utc=True)
            for t in trades_since_17:
                t_entry = pd.to_datetime(t["entry_time"], utc=True)
                diff = (t_entry - sig_time).total_seconds()
                if t["instrument"] == ev["symbol"] and t["direction"] == ev["direction"]:
                    print(f"    Match con Trade ID {t['id']}: entry={t['entry_time']} (diff={diff:.1f}s), exit={t['exit_time']}, pnl={t['net_pnl']}, rr={t['realized_rr']}")

    # 4. AUDITORIA DE SHADOW_RESEARCH.SQLITE3 (BASE ACTIVA DEL RUNNER)
    print("\n--- 4. AUDITORIA DE SHADOW_RESEARCH.SQLITE3 (SOLO LECTURA) ---")
    conn_live_sh = sqlite3.connect(f"file:{PRIMARY_SHADOW_DB.resolve()}?mode=ro", uri=True)
    conn_live_sh.row_factory = sqlite3.Row
    cur_live_sh = conn_live_sh.cursor()
    cur_live_sh.execute("SELECT count(*) FROM shadow_signals")
    live_sh_count = cur_live_sh.fetchone()[0]
    print(f"Total filas en shadow_research.sqlite3 activo: {live_sh_count}")

    # Verificar si el ID 21234 ya esta en shadow_research.sqlite3
    cur_live_sh.execute("""
        SELECT id, timestamp, strategy, variant, symbol, direction, final_action, simulated_outcome, simulated_rr, features_json
        FROM shadow_signals
        WHERE json_extract(features_json, '$.source_signal_id') = 21234
    """)
    rows_21234 = [dict(r) for r in cur_live_sh.fetchall()]
    print(f"Filas de signal_id 21234 en shadow_research.sqlite3: {len(rows_21234)}")
    for r in rows_21234:
        print(f"  ID {r['id']}: variant={r['variant']}, timestamp={r['timestamp']}, action={r['final_action']}, outcome={r['simulated_outcome']}")

    conn_live_sh.close()
    conn_live.close()

if __name__ == "__main__":
    audit_all()
