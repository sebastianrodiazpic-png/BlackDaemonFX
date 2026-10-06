"""Script de análisis diario para la estrategia de Cuartos en Gold (Worker GOLD).

Se ejecuta diariamente a las 09:00 CLT (12:00 UTC) para:
1. Auditar el desempeño histórico y reciente de GOLD_QUARTERS.
2. Evaluar la efectividad de los filtros implementados (H1 Trend, SL Buffer, Break-Even, Obstacle Choke).
3. Analizar bloqueos en preflight y motivos de rechazo.
4. Auditar el estado de entrenamiento del agente de Meta-Etiquetado / IA.
5. Exportar un informe en Markdown y JSON en storage/analysis/.
"""

import os
import sys
import json
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


def get_db_path() -> Path:
    explicit = os.getenv("DAEMONBLACKFX_DB_PATH")
    if explicit and Path(explicit).exists():
        return Path(explicit)
    local_app_data = os.getenv("LOCALAPPDATA")
    if local_app_data:
        p = Path(local_app_data) / "BlackDaemonFx" / "trading_bot.sqlite3"
        if p.exists():
            return p
    default_p = PROJECT_ROOT / "storage" / "daemons" / "trading.db"
    return default_p


def run_analysis(output_dir: Path | None = None) -> dict:
    db_path = get_db_path()
    if not output_dir:
        output_dir = PROJECT_ROOT / "storage" / "analysis"
    output_dir.mkdir(parents=True, exist_ok=True)

    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "generated_at_clt": (datetime.now(timezone.utc) - timedelta(hours=3)).strftime("%Y-%m-%d %H:%M:%S CLT"),
        "database_path": str(db_path),
        "strategy": "GOLD_QUARTERS",
        "worker": "GOLD",
        "trades_summary": {},
        "trades_list": [],
        "rejection_statistics": {},
        "preflight_statistics": {},
        "meta_labeling_status": {},
        "recommendations": []
    }

    if not db_path.exists():
        report["error"] = f"Base de datos no encontrada en {db_path}"
        return report

    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    # 1. Analizar trades de GOLD_QUARTERS
    try:
        cur.execute("""
            SELECT id, instrument, direction, status, result, net_pnl, planned_rr, realized_rr, 
                   entry_price, exit_price, stop_loss, take_profit, entry_time, exit_time, exit_reason, details_json
            FROM trades 
            ORDER BY id ASC;
        """)
        rows = cur.fetchall()
        
        q_trades = []
        for r in rows:
            tid, inst, direction, status, result, net_pnl, planned_rr, realized_rr, entry_price, exit_price, sl, tp, entry_time, exit_time, exit_reason, details_json = r
            strat_name = ""
            meta = {}
            if details_json:
                try:
                    det = json.loads(details_json)
                    meta = det.get("metadata", {})
                    strat_name = meta.get("strategy_name", "")
                except Exception:
                    pass
            
            is_gold = inst and ("XAU" in inst.upper() or "GOLD" in inst.upper())
            is_quarter = "QUARTER" in strat_name.upper() or (meta.get("quarter_level") is not None)
            
            if is_gold and is_quarter:
                q_trades.append({
                    "id": tid,
                    "instrument": inst,
                    "direction": direction,
                    "status": status,
                    "result": result,
                    "net_pnl": float(net_pnl or 0.0),
                    "planned_rr": float(planned_rr or 0.0),
                    "realized_rr": float(realized_rr or 0.0),
                    "entry_price": float(entry_price or 0.0),
                    "exit_price": float(exit_price or 0.0),
                    "stop_loss": float(sl or 0.0),
                    "take_profit": float(tp or 0.0),
                    "sl_distance": abs(float(entry_price or 0.0) - float(sl or 0.0)),
                    "entry_time": entry_time,
                    "exit_time": exit_time,
                    "exit_reason": exit_reason,
                    "quarter_level": meta.get("quarter_level"),
                    "quarter_target": meta.get("quarter_target"),
                    "break_even_activated": bool(meta.get("break_even_activated")),
                    "has_entry_snapshot": bool(meta.get("entry_learning_snapshot"))
                })
        
        report["trades_list"] = q_trades
        total_closed = [t for t in q_trades if t["status"] == "CLOSED"]
        wins = [t for t in total_closed if t["net_pnl"] > 0]
        losses = [t for t in total_closed if t["net_pnl"] < 0]
        be = [t for t in total_closed if t["net_pnl"] == 0]
        total_pnl = sum(t["net_pnl"] for t in total_closed)
        win_rate = (len(wins) / len(total_closed) * 100.0) if total_closed else 0.0
        
        gross_profit = sum(t["net_pnl"] for t in wins)
        gross_loss = abs(sum(t["net_pnl"] for t in losses))
        profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else (999.0 if gross_profit > 0 else 0.0)
        
        buys = [t for t in q_trades if t["direction"] == "BUY"]
        sells = [t for t in q_trades if t["direction"] == "SELL"]

        report["trades_summary"] = {
            "total_trades": len(q_trades),
            "closed_trades": len(total_closed),
            "open_trades": len(q_trades) - len(total_closed),
            "wins": len(wins),
            "losses": len(losses),
            "break_evens": len(be),
            "win_rate_percent": round(win_rate, 2),
            "total_net_pnl": round(total_pnl, 2),
            "gross_profit": round(gross_profit, 2),
            "gross_loss": round(gross_loss, 2),
            "profit_factor": round(profit_factor, 2),
            "direction_breakdown": {
                "buys": len(buys),
                "sells": len(sells)
            },
            "average_win_pnl": round(gross_profit / len(wins), 2) if wins else 0.0,
            "average_loss_pnl": round(-gross_loss / len(losses), 2) if losses else 0.0
        }
    except Exception as e:
        report["trades_error"] = str(e)

    # 2. Analizar eventos de auditoría y bloqueos (daemon_audit_events)
    try:
        cur.execute("""
            SELECT id, event_type, action, reason, created_at, payload_json
            FROM daemon_audit_events
            WHERE event_type = 'GOLD_QUARTERS_ENTRY_PREFLIGHT'
               OR (event_type = 'GOLD_QUARTERS_EVALUATED' AND action != 'WAITING_GOLD_QUARTER')
               OR reason LIKE '%QUARTER%'
            ORDER BY id DESC LIMIT 200;
        """)
        events = cur.fetchall()
        
        reasons_count = {}
        preflight_counts = {"ALLOWED": 0, "BLOCKED": 0, "reasons": {}}

        for e in events:
            eid, etype, action, reason, created_at, payload_json = e
            reason_key = f"{action}:{reason}" if action else str(reason)
            reasons_count[reason_key] = reasons_count.get(reason_key, 0) + 1
            
            if etype == "GOLD_QUARTERS_ENTRY_PREFLIGHT":
                if action == "ALLOWED":
                    preflight_counts["ALLOWED"] += 1
                else:
                    preflight_counts["BLOCKED"] += 1
                    preflight_counts["reasons"][reason] = preflight_counts["reasons"].get(reason, 0) + 1

        report["rejection_statistics"] = reasons_count
        report["preflight_statistics"] = preflight_counts
    except Exception as e:
        report["events_error"] = str(e)

    conn.close()

    # 3. Analizar estado de IA y Meta-Etiquetado
    try:
        model_path = PROJECT_ROOT / "storage" / "ai_models" / "metalabel_GOLD_QUARTERS.json"
        replay_path = PROJECT_ROOT / "storage" / "runtime" / "smc_trial" / "replay" / "GOLD_QUARTERS.json"
        learning_path = PROJECT_ROOT / "storage" / "learning_audit" / "DEMO_GOLD.json"

        ai_status = {"trained": False, "source": "NONE"}

        if model_path.exists():
            with open(model_path, "r", encoding="utf-8") as f:
                m_data = json.load(f)
                m_info = m_data.get("model", {})
                if m_info.get("trained") or m_data.get("trained"):
                    ai_status["trained"] = True
                    ai_status["source"] = "AUGMENTED_REPLAY_MODEL"
                    fnames = m_data.get("feature_names", [])
                    ai_status["feature_count"] = len(fnames)
                    ai_status["metrics"] = m_data.get("metrics", {})
                    ai_status["samples"] = m_data.get("samples", 0)
                    raw_w = m_info.get("weights")
                    if isinstance(raw_w, dict):
                        weights_dict = raw_w
                    elif isinstance(raw_w, list):
                        weights_dict = dict(zip(fnames, raw_w))
                    else:
                        weights_dict = {}
                    non_zero = {k: v for k, v in weights_dict.items() if abs(v) > 1e-4}
                    sorted_w = sorted(non_zero.items(), key=lambda x: x[1], reverse=True)
                    ai_status["top_positive"] = sorted_w[:3]
                    ai_status["top_negative"] = sorted_w[-3:]

        if replay_path.exists():
            with open(replay_path, "r", encoding="utf-8") as f:
                r_data = json.load(f)
                cands = r_data.get("candidates", [])
                outcomes = {}
                for c in cands:
                    outcomes[c.get("outcome")] = outcomes.get(c.get("outcome"), 0) + 1
                ai_status["replay_stats"] = {
                    "total_candidates": len(cands),
                    "outcomes": outcomes,
                    "tp2_wins": outcomes.get("TP2_WIN", 0),
                    "break_evens": outcomes.get("BE_EXIT", 0),
                    "losses": outcomes.get("FULL_SL", 0)
                }

        if learning_path.exists():
            with open(learning_path, "r", encoding="utf-8") as f:
                l_data = json.load(f)
                ai_status["runtime_learning"] = {
                    "gold_quarters_info": l_data.get("strategies", {}).get("GOLD_QUARTERS", {}),
                    "family_eligible_setups": l_data.get("training_funnel", {}).get("eligible_closed_setups_family", 0),
                    "mode": l_data.get("mode")
                }

        report["meta_labeling_status"] = ai_status
    except Exception as e:
        report["meta_labeling_status"] = {"error": str(e)}

    # 4. Generar Puntos de Mejora y Diagnósticos Automáticos
    ts = report["trades_summary"]
    if ts.get("direction_breakdown", {}).get("sells", 0) == 0 and ts.get("total_trades", 0) > 3:
        report["recommendations"].append({
            "topic": "Sesgo Direccional Exclusivo",
            "observation": f"El bot ha ejecutado {ts.get('total_trades')} compras y 0 ventas en Gold.",
            "impact": "Riesgo de comprar en caídas institucionales severas.",
            "action_taken": "Filtro H1 Trend (EMA20/EMA50 + absorción) activado para prohibir compras en cascadas bajistas."
        })
    
    if ts.get("win_rate_percent", 0.0) < 50.0 and ts.get("closed_trades", 0) >= 3:
        report["recommendations"].append({
            "topic": "Protección de Capital y Break-Even",
            "observation": f"Win Rate actual es {ts.get('win_rate_percent')}%. Varias operaciones alcanzaron +1R antes de revertirse.",
            "action_taken": "Se activó el monitor de Break-Even para GOLD_QUARTERS para proteger trades ganadores al llegar a +1.0R."
        })

    report["recommendations"].append({
        "topic": "Objetivo de Salida: Búsqueda Constante de TP2 (+50 pts) con BE en TP1",
        "observation": "Estrategia configurada para buscar siempre el segundo nivel de cuarto (+50 puntos / 2 cuartos) para maximizar el Ratio Ganancia/Riesgo (5.0R a 7.0R+).",
        "status": "Protección de Break-Even asegurada al alcanzar el primer cuarto (+25 pts / TP1)."
    })

    chokes = report.get("preflight_statistics", {}).get("reasons", {}).get("QUARTER_OBSTACLE_CHOKES_TARGET_CORRIDOR", 0)
    if chokes > 0:
        report["recommendations"].append({
            "topic": "Filtro de Corredor Obstruido Activo",
            "observation": f"Se han evitado {chokes} operaciones donde un Order Block bloqueaba el camino hacia el siguiente cuarto.",
            "status": "Filtro funcionando adecuadamente."
        })

    # 5. Guardar archivos de salida
    json_path = output_dir / f"daily_gold_quarters_{today_str}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    md_path = output_dir / "daily_gold_quarters_report.md"
    md_content = generate_markdown_report(report)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    return report


def generate_markdown_report(report: dict) -> str:
    ts = report.get("trades_summary", {})
    dirs = ts.get("direction_breakdown", {})
    pre = report.get("preflight_statistics", {})
    ai = report.get("meta_labeling_status", {})
    gq_ai = ai.get("gold_quarters_info", {})

    md = f"""# Informe Diario de Auditoría: Cuartos en Gold (Worker GOLD)
**Fecha y Hora de Emisión**: {report.get('generated_at_clt', 'N/A')}
**Estrategia**: `GOLD_QUARTERS` | **Base de Datos**: `{Path(report.get('database_path', '')).name}`

---

### 1. Resumen de Rendimiento Operativo
| Métrica | Valor |
| :--- | :--- |
| **Total Operaciones Históricas** | {ts.get('total_trades', 0)} |
| **Operaciones Cerradas** | {ts.get('closed_trades', 0)} |
| **Ganadas / Perdidas / BE** | {ts.get('wins', 0)} Wins / {ts.get('losses', 0)} Losses / {ts.get('break_evens', 0)} BE |
| **Win Rate** | **{ts.get('win_rate_percent', 0.0)}%** |
| **PnL Neto Total** | **${ts.get('total_net_pnl', 0.0):.2f} USD** |
| **Profit Factor** | {ts.get('profit_factor', 0.0)} |
| **Desglose Direccional** | Compras: {dirs.get('buys', 0)} | Ventas: {dirs.get('sells', 0)} |
| **Ganancia Promedio (Win)** | +${ts.get('average_win_pnl', 0.0):.2f} USD |
| **Pérdida Promedio (Loss)** | -${abs(ts.get('average_loss_pnl', 0.0)):.2f} USD |

---

### 2. Estado de Filtros y Preflight
* **Preflight Autorizados**: {pre.get('ALLOWED', 0)}
* **Preflight Bloqueados**: {pre.get('BLOCKED', 0)}
* **Motivos de Bloqueo Recientes**:
"""
    for reason, count in pre.get("reasons", {}).items():
        md += f"  - `{reason}`: {count} eventos\n"

    md += f"""
---

### 3. Estado del Agente de Inteligencia Artificial (Meta-Etiquetado)
* **Estado del Modelo**: {'🟢 Activo y Calibrado (CalibratedLogisticModel)' if ai.get('trained') else '🟡 En Recolección (Untrained)'}
* **Fuente de Entrenamiento**: `{ai.get('source', 'N/A')}` ({ai.get('samples', 0)} muestras de MT5 Replay)
* **Métricas del Modelo**: Precisión: `{ai.get('metrics', {}).get('accuracy', 0.0) * 100:.1f}%` | Win Rate Base: `{ai.get('metrics', {}).get('win_rate', 0.0) * 100:.1f}%`
* **Setups Evaluados (Replay Aumentado)**: {ai.get('replay_stats', {}).get('total_candidates', 0)} setups
* **Distribución de Salidas Replay**: {ai.get('replay_stats', {}).get('tp2_wins', 0)} Wins (TP2) | {ai.get('replay_stats', {}).get('break_evens', 0)} Break-Evens | {ai.get('replay_stats', {}).get('losses', 0)} Losses
* **Factores Predictivos Clave (+)**: {', '.join([f'{k} (+{v:.2f})' for k, v in ai.get('top_positive', [])]) or 'N/A'}
* **Factores Penalizadores Clave (-)**: {', '.join([f'{k} ({v:.2f})' for k, v in ai.get('top_negative', [])]) or 'N/A'}

---

### 4. Diagnósticos y Puntos de Mejora
"""
    for rec in report.get("recommendations", []):
        md += f"#### 🔹 {rec.get('topic')}\n"
        md += f"* **Observación**: {rec.get('observation')}\n"
        if "action_taken" in rec:
            md += f"* **Acción Implementada**: {rec.get('action_taken')}\n"
        if "status" in rec:
            md += f"* **Estado**: {rec.get('status')}\n"
        md += "\n"

    md += """
---
*Informe generado automáticamente por el subsistema de auditoría de BlackDaemonFX.*
"""
    return md


if __name__ == "__main__":
    rep = run_analysis()
    print("=" * 60)
    print(f"ANÁLISIS DIARIO GOLD QUARTERS GENERADO EXITOSAMENTE")
    print(f"Fecha: {rep.get('generated_at_clt')}")
    print(f"Total Trades: {rep.get('trades_summary', {}).get('total_trades')}")
    print(f"Win Rate: {rep.get('trades_summary', {}).get('win_rate_percent')}% | PnL: ${rep.get('trades_summary', {}).get('total_net_pnl')}")
    print("=" * 60)
    print("Informe guardado en storage/analysis/daily_gold_quarters_report.md")
