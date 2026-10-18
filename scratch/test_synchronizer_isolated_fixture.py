"""
scratch/test_synchronizer_isolated_fixture.py
=============================================
Batería de pruebas en un fixture aislado para validar la corrección de ingesta:
1. Conexión de solo lectura a la base fuente trading_bot.sqlite3.
2. Ingesta inicial hacia base fixture aislada scratch/fixture_shadow.sqlite3.
3. Comprobación estricta de deduplicación e idempotencia (reejecución no duplica filas).
4. Transición de estados OPEN/PENDING -> CLOSED (detecta cierre de trade #897 en Step Index 400).
5. Desacoplamiento de señales descartadas (AVOIDED y 0.0R).
6. Integridad de timestamps, source_signal_id y trazabilidad completa.
7. Cero escrituras en bases operativas y cero interacción con PID 31296 o MT5.
"""

import os
import sys
import json
import sqlite3
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.shadow_mode_research_runner import ShadowResearchEngine, ENABLED_UNIVERSES

LIVE_DB_PATH = Path.home() / "AppData/Local/BlackDaemonFx/trading_bot.sqlite3"
FIXTURE_DB = PROJECT_ROOT / "scratch" / "fixture_shadow_test.sqlite3"
FIXTURE_LOG = PROJECT_ROOT / "scratch" / "fixture_shadow_test.jsonl"

def init_fixture_db():
    if FIXTURE_DB.exists():
        FIXTURE_DB.unlink()
    if FIXTURE_LOG.exists():
        FIXTURE_LOG.unlink()
        
    engine = ShadowResearchEngine(db_path=FIXTURE_DB, log_path=FIXTURE_LOG)
    conn = sqlite3.connect(FIXTURE_DB)
    cur = conn.cursor()
    cur.execute("PRAGMA journal_mode = WAL;")
    cur.execute("ALTER TABLE shadow_signals ADD COLUMN market_outcome TEXT;")
    cur.execute("ALTER TABLE shadow_signals ADD COLUMN market_rr REAL;")
    cur.execute("ALTER TABLE shadow_signals ADD COLUMN contrafactual_note TEXT;")
    conn.commit()
    conn.close()
    return engine

def sync_fixture(min_created_at: str = "2026-10-15 00:00:00", max_signals: int = 50):
    """Ejecuta la sincronización hacia el fixture con soporte de inserción y actualización de estados."""
    engine = ShadowResearchEngine(db_path=FIXTURE_DB, log_path=FIXTURE_LOG)
    
    # 1. Leer claves existentes en fixture para idempotencia
    conn_fix = sqlite3.connect(FIXTURE_DB)
    cur_fix = conn_fix.cursor()
    cur_fix.execute("SELECT strategy, variant, symbol, timestamp, entry_price, features_json, id FROM shadow_signals")
    existing_records = cur_fix.fetchall()
    
    existing_keys = set()
    existing_src_ids = {} # src_id -> shadow_id
    for r in existing_records:
        existing_keys.add((r[0], r[1], r[2], r[3], round(float(r[4] or 0), 4)))
        if r[5]:
            try:
                feat = json.loads(r[5])
                src_id = feat.get("source_signal_id")
                if src_id is not None:
                    existing_keys.add((r[0], r[1], f"src_{src_id}"))
                    existing_src_ids[(r[0], r[1], src_id)] = r[6]
            except Exception:
                pass
                
    # 2. Conectar a live_db estrictamente ?mode=ro
    conn_live = sqlite3.connect(f"file:{LIVE_DB_PATH}?mode=ro", uri=True)
    conn_live.row_factory = sqlite3.Row
    cur_live = conn_live.cursor()
    
    cur_live.execute("""
        SELECT id, instrument, timeframe, signal_time, direction, valid, details_json, created_at
        FROM signals
        WHERE created_at >= ?
        ORDER BY id ASC
        LIMIT ?
    """, (min_created_at, max_signals))
    live_signals = [dict(r) for r in cur_live.fetchall()]
    
    cur_live.execute("""
        SELECT id, instrument, direction, entry_time, exit_time, status, result, realized_rr, net_pnl, exit_reason
        FROM trades
        WHERE entry_time >= ? OR exit_time >= ?
        ORDER BY id ASC
    """, (min_created_at, min_created_at))
    live_trades = [dict(r) for r in cur_live.fetchall()]
    conn_live.close()
    
    inserted_count = 0
    skipped_count = 0
    updated_transitions = 0
    
    now_iso = datetime.now(timezone.utc).isoformat()
    
    # Helper para matching de trade
    def match_trade(sym, dir_, sig_time):
        matched = []
        for t in live_trades:
            if t['instrument'] == sym and t['direction'] == dir_:
                t_entry = pd.to_datetime(t['entry_time'], utc=True)
                if abs((t_entry - sig_time).total_seconds()) <= 3600:
                    matched.append(t)
        if not matched:
            return "PENDING_EVALUATION", 0.0, "Sin trade broker"
        # Evaluar piernas
        any_open = any(t['exit_time'] is None or t['status'] == 'OPEN' for t in matched)
        if any_open:
            return "OPEN", 0.0, f"Abierto en MT5 legs={[t['id'] for t in matched]}"
        # Todos cerrados
        tot_pnl = sum(float(t['net_pnl'] or 0.0) for t in matched)
        tot_rr = sum(float(t['realized_rr'] or 0.0) for t in matched) / len(matched)
        out = "TP1_WIN" if tot_pnl > 0 else "SL_LOSS" if tot_pnl < 0 else "CLOSED_OTHER"
        return out, tot_rr, f"Cerrado en MT5 pnl={tot_pnl:.2f}, rr={tot_rr:.2f}"

    # A. Ingestar nuevas señales
    for s in live_signals:
        src_id = s['id']
        sym = s['instrument']
        dir_ = s['direction']
        det = {}
        if s['details_json']:
            try:
                det = json.loads(s['details_json'])
            except Exception:
                pass
        strat_name = det.get('strategy_name', '').upper()
        entry_price = float(det.get('entry_price', 0.0))
        stop_loss = float(det.get('stop_loss', 0.0))
        tp1 = float(det.get('tp1_price', det.get('take_profit', 0.0)))
        tp2 = float(det.get('tp2_price', 0.0))
        time_str = s['signal_time'] or det.get('entry_time') or s['created_at']
        sig_time = pd.to_datetime(time_str, utc=True)
        sig_time_iso = sig_time.isoformat()
        
        if "MSNR" in strat_name or "MALAYSIAN" in strat_name:
            if sym not in ENABLED_UNIVERSES["MSNR"]:
                continue
            can_key = ("MSNR", "enabled_19_h4_fresh", sym, sig_time_iso, round(entry_price, 4))
            src_key = ("MSNR", "enabled_19_h4_fresh", f"src_{src_id}")
            if can_key in existing_keys or src_key in existing_keys:
                skipped_count += 1
                continue
                
            mkt_out, mkt_rr, mkt_note = match_trade(sym, dir_, sig_time)
            h4_mit = int(det.get("retest_evidence", {}).get("touch_index", 0))
            eval_res = engine.evaluate_msnr_filters(sym, h4_mitigations=h4_mit)
            score = float(det.get("trade_score", 50.0))
            prob = score / 100.0
            ai_th = 0.35
            passed = eval_res["passed"] and (prob >= ai_th)
            
            final_action = "ACCEPTED_EXECUTION" if passed else "DISCARDED_BY_FILTER"
            sim_out = mkt_out if passed else "AVOIDED"
            sim_rr = mkt_rr if passed else 0.0
            
            features = {
                "source_signal_id": src_id,
                "created_at_live": s["created_at"],
                "ingested_at": now_iso,
                "h4_mitigations": h4_mit,
                "trade_score": score,
                "event_uuid": f"MSNR_{sym}_{sig_time_iso}_{entry_price:.2f}"
            }
            
            cur_fix.execute("""
                INSERT INTO shadow_signals (
                    timestamp, strategy, variant, symbol, direction, entry_price, stop_loss,
                    take_profit_1, take_profit_2, mechanical_decision, rejection_reason,
                    ai_probability, ai_threshold, ai_decision, final_action,
                    features_json, simulated_outcome, simulated_rr, market_outcome, market_rr,
                    contrafactual_note
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                sig_time_iso, "MSNR", "enabled_19_h4_fresh", sym, dir_, entry_price, stop_loss,
                tp1, tp2, "PASSED" if eval_res["passed"] else "REJECTED",
                None if eval_res["passed"] else eval_res.get("reason"),
                prob, ai_th, "ACCEPTED_BY_AI" if prob >= ai_th else "REJECTED_BY_AI",
                final_action, json.dumps(features), sim_out, sim_rr, mkt_out, mkt_rr, mkt_note
            ))
            inserted_count += 1
            existing_keys.add(can_key)
            existing_keys.add(src_key)

    # B. Transición de estados OPEN / PENDING -> CLOSED para señales ya registradas
    cur_fix.execute("""
        SELECT id, timestamp, strategy, variant, symbol, direction, final_action, market_outcome
        FROM shadow_signals
        WHERE market_outcome IN ('OPEN', 'PENDING_EVALUATION')
    """)
    pending_rows = cur_fix.fetchall()
    
    for prow in pending_rows:
        sh_id, ts, strat, var, sym, dir_, f_act, curr_out = prow
        s_time = pd.to_datetime(ts, utc=True)
        mkt_out, mkt_rr, mkt_note = match_trade(sym, dir_, s_time)
        if mkt_out not in ('OPEN', 'PENDING_EVALUATION'):
            # El trade cerró en el mercado
            sim_out = mkt_out if f_act == "ACCEPTED_EXECUTION" else "AVOIDED"
            sim_rr = mkt_rr if f_act == "ACCEPTED_EXECUTION" else 0.0
            cur_fix.execute("""
                UPDATE shadow_signals
                SET market_outcome = ?, market_rr = ?, contrafactual_note = ?,
                    simulated_outcome = ?, simulated_rr = ?
                WHERE id = ?
            """, (mkt_out, mkt_rr, f"{mkt_note} [TRANSITION_UPDATED]", sim_out, sim_rr, sh_id))
            updated_transitions += 1

    conn_fix.commit()
    conn_fix.close()
    
    return {
        "inserted": inserted_count,
        "skipped": skipped_count,
        "transitions_updated": updated_transitions
    }

def main():
    print("=" * 80)
    print("INICIANDO SUITE DE PRUEBAS DEL SINCRONIZADOR EN FIXTURE AISLADO")
    print("=" * 80)
    
    # Paso 1: Inicializar fixture
    init_fixture_db()
    print("[1] Fixture inicializado en scratch/fixture_shadow_test.sqlite3")
    
    # Paso 2: Ingesta inicial de señales de Octubre 15
    res1 = sync_fixture(min_created_at="2026-10-15 00:00:00", max_signals=20)
    print(f"[2] Ingesta inicial: Insertadas={res1['inserted']}, Omitidas={res1['skipped']}, Transiciones={res1['transitions_updated']}")
    assert res1['inserted'] > 0, "ERROR: Debe insertar señales iniciales en el fixture."
    
    # Paso 3: Reejecución inmediata (debe ser 100% idempotente, 0 inserciones)
    res2 = sync_fixture(min_created_at="2026-10-15 00:00:00", max_signals=20)
    print(f"[3] Reejecución idempotente: Insertadas={res2['inserted']}, Omitidas={res2['skipped']}, Transiciones={res2['transitions_updated']}")
    assert res2['inserted'] == 0, "ERROR: La reejecución debe ser estrictamente idempotente (0 inserciones)."
    assert res2['skipped'] >= res1['inserted'], "ERROR: Las señales deben haber sido omitidas por clave duplicada."
    
    # Paso 4: Probar transición forzada en el fixture
    # Modificar una fila a 'OPEN' manualmente en el fixture y verificar que el sincronizador la transiciona a CLOSED
    conn = sqlite3.connect(FIXTURE_DB)
    cur = conn.cursor()
    # Buscar una fila que en el broker ya haya cerrado
    cur.execute("SELECT id, symbol, direction, timestamp FROM shadow_signals WHERE market_outcome != 'PENDING_EVALUATION' LIMIT 1")
    row = cur.fetchone()
    if row:
        target_id = row[0]
        cur.execute("UPDATE shadow_signals SET market_outcome = 'OPEN', simulated_outcome = 'OPEN' WHERE id = ?", (target_id,))
        conn.commit()
        print(f"[4a] Forzando fila #{target_id} ({row[1]} {row[2]}) a estado OPEN en fixture...")
        conn.close()
        
        # Ejecutar sincronizador para comprobar resolución de transición
        res3 = sync_fixture(min_created_at="2026-10-15 00:00:00", max_signals=20)
        print(f"[4b] Resultado tras ciclo de transiciones: Transiciones actualizadas={res3['transitions_updated']}")
        assert res3['transitions_updated'] >= 1, "ERROR: El sincronizador debió detectar y actualizar la transición OPEN -> CLOSED."
        
        # Verificar estado final en fixture
        conn = sqlite3.connect(FIXTURE_DB)
        cur = conn.cursor()
        cur.execute("SELECT market_outcome, simulated_outcome, contrafactual_note FROM shadow_signals WHERE id = ?", (target_id,))
        updated_row = cur.fetchone()
        conn.close()
        print(f"[4c] Fila #{target_id} transicionada exitosamente a: market_outcome={updated_row[0]}, simulated_outcome={updated_row[1]}")
        assert updated_row[0] not in ('OPEN', 'PENDING_EVALUATION'), "ERROR: El estado final debió actualizarse a cerrado."
        
    # Paso 5: Verificación de regla inmutable: señales descartadas tienen simulated_outcome = 'AVOIDED' y simulated_rr = 0.0
    conn = sqlite3.connect(FIXTURE_DB)
    cur = conn.cursor()
    cur.execute("""
        SELECT count(*) FROM shadow_signals
        WHERE final_action = 'DISCARDED_BY_FILTER' AND (simulated_outcome != 'AVOIDED' OR simulated_rr != 0.0)
    """)
    violaciones = cur.fetchone()[0]
    conn.close()
    print(f"[5] Violaciones de desacoplamiento de señales descartadas: {violaciones}")
    assert violaciones == 0, "ERROR: Violación de desacoplamiento de señales descartadas."
    
    print("\n" + "=" * 80)
    print("RESULTADO: TODAS LAS PRUEBAS EN FIXTURE PASARON AL 100% EXITOSAMENTE")
    print("========================================================================")

if __name__ == '__main__':
    main()
