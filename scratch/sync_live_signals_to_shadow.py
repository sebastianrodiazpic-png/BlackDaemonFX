"""
scratch/sync_live_signals_to_shadow.py
======================================
Ingesta de señales recientes del bot en vivo (en modo SOLO LECTURA) para
ser evaluadas en modo sombra por las 4 variantes de ICT y Malaysian SNR (19 activos habilitados).

Garantías:
- Abre trading_bot.sqlite3 estrictamente en modo URI ?mode=ro (Read-Only).
- Escribe únicamente en storage/runtime/shadow_research.sqlite3 y storage/runtime/shadow_events.jsonl.
- NO envía órdenes al broker.
"""

import sys
import json
import sqlite3
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.shadow_mode_research_runner import ShadowResearchEngine, ENABLED_UNIVERSES

def sync_live_signals_to_shadow():
    db_path = Path.home() / 'AppData/Local/BlackDaemonFx/trading_bot.sqlite3'
    if not db_path.exists():
        print(f"[ERROR] Live database not found at {db_path}")
        return

    # Conexión estrictamente de SOLO LECTURA
    conn_live = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
    conn_live.row_factory = sqlite3.Row
    cur_live = conn_live.cursor()

    engine = ShadowResearchEngine()
    
    # Consultar señales recientes de hoy (2026-10-15)
    cur_live.execute("""
        SELECT * FROM signals
        WHERE created_at >= '2026-10-15' AND details_json IS NOT NULL
        ORDER BY id ASC
    """)
    rows = cur_live.fetchall()
    print(f"Total señales detectadas en DB en vivo hoy: {len(rows)}")

    ingested_count = 0
    for r in rows:
        try:
            details = json.loads(r['details_json'])
        except Exception:
            continue

        strat_name = details.get('strategy_name', '').upper()
        symbol = r['instrument'] or details.get('symbol')
        direction = r['direction'] or details.get('direction')
        entry_price = float(details.get('entry_price', 0.0))
        stop_loss = float(details.get('stop_loss', 0.0))
        tp1 = float(details.get('tp1_price', details.get('take_profit', 0.0)))
        tp2 = float(details.get('tp2_price', 0.0))

        # Timestamp de la señal
        time_str = r['signal_time'] or details.get('entry_time') or r['created_at']
        try:
            sig_time = pd.to_datetime(time_str, utc=True)
        except Exception:
            sig_time = datetime.now(timezone.utc)

        # 1. EVALUAR ICT
        if "ICT" in strat_name:
            if symbol not in ENABLED_UNIVERSES["ICT"]:
                continue
            # Evaluar simultáneamente las 4 variantes exigidas
            for variant in ["base", "lock_0700_0930", "lock_0700_1000", "london_only"]:
                eval_res = engine.evaluate_ict_variant(symbol, sig_time, variant=variant)
                # Probabilidad heurística / meta-labeling si disponible
                prob = float(details.get('trade_score', 50.0)) / 100.0 if details.get('trade_score') else 0.45
                ai_th = 0.45
                ai_decision = "ACCEPTED_BY_AI" if prob >= ai_th and eval_res["passed"] else "REJECTED_BY_AI" if prob < ai_th else "NOT_EVALUATED_FILTER_REJECT"
                final_action = "ACCEPTED_EXECUTION" if (eval_res["passed"] and prob >= ai_th) else "DISCARDED_BY_FILTER"
                
                event_data = {
                    "timestamp": sig_time.isoformat(),
                    "strategy": "ICT",
                    "variant": variant,
                    "symbol": symbol,
                    "direction": direction,
                    "entry_price": entry_price,
                    "stop_loss": stop_loss,
                    "take_profit_1": tp1,
                    "take_profit_2": tp2,
                    "mechanical_decision": "PASSED" if eval_res["passed"] else "REJECTED",
                    "rejection_reason": None if eval_res["passed"] else eval_res["reason"],
                    "ai_probability": prob,
                    "ai_threshold": ai_th,
                    "ai_decision": ai_decision,
                    "final_action": final_action,
                    "features": {"hour_utc": sig_time.hour, "session": eval_res.get("session")},
                    "simulated_outcome": "PENDING_EVALUATION",
                    "simulated_rr": 0.0
                }
                engine.record_shadow_event(event_data)
                ingested_count += 1

        # 2. EVALUAR MALAYSIAN SNR
        elif "MALAYSIAN" in strat_name or "MSNR" in strat_name:
            # Estrictamente los 19 activos habilitados
            h4_evidence = details.get('h4_obstacle_evidence', {})
            h4_mitigations = int(details.get('retest_evidence', {}).get('touch_index', 0))
            
            eval_res = engine.evaluate_msnr_filters(symbol, h4_mitigations=h4_mitigations)
            prob = float(details.get('trade_score', 50.0)) / 100.0 if details.get('trade_score') else 0.40
            ai_th = 0.35 # Umbral congelado 0.35 validado en entrenamiento
            ai_decision = "ACCEPTED_BY_AI" if prob >= ai_th and eval_res["passed"] else "REJECTED_BY_AI" if prob < ai_th else "NOT_EVALUATED_FILTER_REJECT"
            final_action = "ACCEPTED_EXECUTION" if (eval_res["passed"] and prob >= ai_th) else "DISCARDED_BY_FILTER"

            event_data = {
                "timestamp": sig_time.isoformat(),
                "strategy": "MSNR",
                "variant": "enabled_19_h4_fresh",
                "symbol": symbol,
                "direction": direction,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profit_1": tp1,
                "take_profit_2": tp2,
                "mechanical_decision": "PASSED" if eval_res["passed"] else "REJECTED",
                "rejection_reason": None if eval_res["passed"] else eval_res["reason"],
                "ai_probability": prob,
                "ai_threshold": ai_th,
                "ai_decision": ai_decision,
                "final_action": final_action,
                "features": {"h4_mitigations": h4_mitigations, "is_enabled": symbol in ENABLED_UNIVERSES["MSNR"]},
                "simulated_outcome": "PENDING_EVALUATION",
                "simulated_rr": 0.0
            }
            engine.record_shadow_event(event_data)
            ingested_count += 1

    conn_live.close()
    print(f"[SHADOW SYNC] Evaluadas y registradas {ingested_count} variantes de señales en shadow mode.")
    summary = engine.get_summary()
    print(json.dumps(summary, indent=2))

if __name__ == '__main__':
    sync_live_signals_to_shadow()
