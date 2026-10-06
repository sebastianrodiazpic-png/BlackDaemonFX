"""Herramienta de auditoría y estadística de comportamiento post-despliegue.

Analiza el desempeño de las operaciones, el filtro del meta-etiquetador IA,
los parámetros de bloqueo por familia y oportunidades de mejora para el Win Rate.

Uso:
    python tools/audit_worker_ai_behavior.py [--db-path storage/trading_bot.sqlite3]
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

# Ajuste de encoding UTF-8
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def canonical_family(worker_or_symbol: str) -> str:
    text = str(worker_or_symbol or "").upper().strip()
    if text.startswith("SCALP_"):
        text = text[len("SCALP_"):]
    if "BOOM" in text:
        return "BOOM"
    if "CRASH" in text:
        return "CRASH"
    if "STEP" in text:
        return "STEP"
    if "JUMP" in text:
        return "JUMP"
    if "VOL" in text or "1HZ" in text or "V10" in text or "V25" in text or "V50" in text or "V75" in text or "V100" in text:
        return "VOLATILITY"
    if "XAU" in text or "XAG" in text or "GOLD" in text or "SILVER" in text:
        return "GOLD"
    if any(c in text for c in ("EUR", "USD", "GBP", "JPY", "AUD", "CAD", "CHF", "NZD")):
        return "FOREX"
    if any(idx in text for idx in ("WALL STREET", "US TECH", "US SP", "OIL", "BRENT")):
        return "ORB_INDICES"
    return text or "OTHER"


from database.database import resolve_db_path


def run_audit(db_path: str | None = None, models_dir: str = "storage/ai_models") -> dict:
    if db_path:
        db = Path(db_path)
    else:
        db = resolve_db_path()
    if not db.exists():
        print(f"[!] No se encontró base de datos en {db}")
        return {}

    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Cargar operaciones
    cursor.execute("""
        SELECT id, source, instrument, direction, status, entry_time, exit_time,
               entry_price, exit_price, stop_loss, take_profit, realized_rr,
               net_pnl, exit_reason, details_json
        FROM trades
        ORDER BY id ASC
    """)
    rows = cursor.fetchall()

    # Cargar eventos de auditoría (bloqueos y decisiones)
    audit_events = []
    try:
        cursor.execute("""
            SELECT id, event_type, instrument, action, reason, payload_json, event_time
            FROM daemon_audit_events
            ORDER BY id DESC LIMIT 5000
        """)
        audit_events = cursor.fetchall()
    except Exception as e:
        print(f"Error cargando daemon_audit_events: {e}")

    # 1. Estadísticas de Trades por Familia (Diferenciando Bot Nativo vs Manual MT5)
    def new_stat_dict():
        return {
            "total": 0, "wins": 0, "losses": 0, "break_even": 0, "open": 0,
            "sum_rr": 0.0, "sum_pnl": 0.0, "win_rr": [], "loss_rr": [],
        }

    family_stats = defaultdict(new_stat_dict)
    external_stats = defaultdict(new_stat_dict)

    ai_scored_count = 0
    ai_vetoed_count = 0
    ai_allowed_count = 0

    for r in rows:
        fam = canonical_family(r["instrument"])
        src = str(r["source"] or "").upper()
        status = str(r["status"] or "").upper()
        rr = r["realized_rr"]
        pnl = r["net_pnl"]

        try:
            rr = float(rr) if rr is not None else 0.0
        except (ValueError, TypeError):
            rr = 0.0

        try:
            pnl = float(pnl) if pnl is not None else 0.0
        except (ValueError, TypeError):
            pnl = 0.0

        target_dict = external_stats if src == "MT5_EXTERNAL" else family_stats
        stats = target_dict[fam]
        stats["total"] += 1
        stats["sum_rr"] += rr
        stats["sum_pnl"] += pnl

        if status == "OPEN":
            stats["open"] += 1
        elif abs(rr) < 1e-6:
            stats["break_even"] += 1
        elif rr > 0:
            stats["wins"] += 1
            stats["win_rr"].append(rr)
        else:
            stats["losses"] += 1
            stats["loss_rr"].append(rr)

        # Revisar si contenía decisión de Meta-Etiquetado IA
        raw_det = r["details_json"]
        if raw_det:
            try:
                det = json.loads(raw_det) if isinstance(raw_det, str) else raw_det
                meta = det.get("metadata") or {}
                if "meta_label" in meta or "meta_label_decision" in meta:
                    ai_scored_count += 1
                    dec = meta.get("meta_label") or meta.get("meta_label_decision") or {}
                    if dec.get("allowed") is False:
                        ai_vetoed_count += 1
                    else:
                        ai_allowed_count += 1
            except Exception:
                pass

    # 2. Análisis de Bloqueos en Auditoría
    block_reasons = Counter()
    for ev in audit_events:
        action = str(ev["action"] or "").upper()
        reason = str(ev["reason"] or "").strip()
        if any(tok in action for tok in ("BLOCKED", "CLOSED", "EXCLUDED", "REJECTED", "LOW", "EXPIRED")):
            block_reasons[f"{action}: {reason}"] += 1

    # 3. Estado de Modelos de IA
    models_summary = {}
    m_dir = Path(models_dir)
    if m_dir.exists():
        for mf in sorted(m_dir.glob("metalabel_*.json")):
            try:
                dat = json.loads(mf.read_text(encoding="utf-8"))
                models_summary[mf.name] = {
                    "worker": dat.get("worker"),
                    "trained": dat.get("model", {}).get("trained", False),
                    "samples": dat.get("model", {}).get("samples", 0),
                    "positive_rate": round(float(dat.get("model", {}).get("positive_rate", 0.0)), 3),
                    "avg_win_rr": round(float(dat.get("average_win_rr", 1.0)), 2),
                    "avg_loss_rr": round(float(dat.get("average_loss_rr", 1.0)), 2),
                    "trained_at": dat.get("trained_at"),
                }
            except Exception:
                pass

    # Imprimir Reporte
    print("=" * 80)
    print("   REPORTE DE AUDITORÍA Y COMPORTAMIENTO: WORKERS & META-ETIQUETADO IA")
    print(f"   Generado: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print("=" * 80)

    print("\n1. DESEMPEÑO DE WORKERS (TRADES NATIVOS SMC BOT - DEMO/LIVE):")
    print("-" * 80)
    print(f"{'Familia':<15} | {'Total':<6} | {'Wins':<5} | {'Loss':<5} | {'WinRate':<8} | {'Sum R':<8} | {'Avg Win R':<10} | {'Avg Loss R':<10}")
    print("-" * 80)
    total_trades = 0
    total_wins = 0
    total_losses = 0
    total_r = 0.0

    for fam, st in sorted(family_stats.items()):
        closed = st["wins"] + st["losses"]
        wr = (st["wins"] / closed * 100.0) if closed > 0 else 0.0
        avg_w = (sum(st["win_rr"]) / len(st["win_rr"])) if st["win_rr"] else 0.0
        avg_l = (sum(st["loss_rr"]) / len(st["loss_rr"])) if st["loss_rr"] else 0.0
        print(f"{fam:<15} | {st['total']:<6} | {st['wins']:<5} | {st['losses']:<5} | {wr:6.1f}% | {st['sum_rr']:+7.2f}R | {avg_w:8.2f}R | {avg_l:8.2f}R")
        total_trades += st["total"]
        total_wins += st["wins"]
        total_losses += st["losses"]
        total_r += st["sum_rr"]

    closed_all = total_wins + total_losses
    overall_wr = (total_wins / closed_all * 100.0) if closed_all > 0 else 0.0
    print("-" * 80)
    print(f"{'SUBTOTAL BOT':<15} | {total_trades:<6} | {total_wins:<5} | {total_losses:<5} | {overall_wr:6.1f}% | {total_r:+7.2f}R |")

    if external_stats:
        ext_tot = sum(s["total"] for s in external_stats.values())
        ext_w = sum(s["wins"] for s in external_stats.values())
        ext_l = sum(s["losses"] for s in external_stats.values())
        ext_r = sum(s["sum_rr"] for s in external_stats.values())
        ext_wr = (ext_w / (ext_w + ext_l) * 100.0) if (ext_w + ext_l) > 0 else 0.0
        print(f"{'MANUAL MT5':<15} | {ext_tot:<6} | {ext_w:<5} | {ext_l:<5} | {ext_wr:6.1f}% | {ext_r:+7.2f}R | (Observadas, no gestionadas)")

    print("\n2. ESTADO DE MODELOS DE META-ETIQUETADO IA (storage/ai_models):")
    print("-" * 80)
    for name, info in models_summary.items():
        status_str = f"ENTRENADO ({info['samples']} muestras, WinRate Base: {info['positive_rate']*100:.1f}%)" if info['trained'] else "NO ENTRENADO"
        print(f" • {name:<30} -> {status_str} | Win/Loss RR: +{info['avg_win_rr']}R / -{info['avg_loss_rr']}R")

    print("\n3. PRINCIPALES PARÁMETROS Y VETOS DE BLOQUEO REGISTRADOS:")
    print("-" * 80)
    if block_reasons:
        for reason, count in block_reasons.most_common(12):
            print(f" • [{count:3d} veces] {reason}")
    else:
        print(" • No se registraron bloqueos explícitos en audit_events (esperando ciclo en vivo).")

    print("\n4. DIAGNÓSTICO DE OPORTUNIDADES PARA MAXIMIZAR EL WIN RATE:")
    print("-" * 80)
    suggestions = []
    for fam, st in family_stats.items():
        closed = st["wins"] + st["losses"]
        wr = (st["wins"] / closed * 100.0) if closed > 0 else 0.0
        if closed >= 3 and wr < 35.0:
            suggestions.append(f"Familia {fam}: Win Rate bajo ({wr:.1f}% en {closed} trades). Recomienda activar umbral de probabilidad IA >= 0.60 para filtrar falsos rompimientos.")
        if fam == "STEP" and st["losses"] > st["wins"]:
            suggestions.append("Familia STEP: Alta tasa de pérdida confirmada por la micro-dinámica discreta. Mantener filtro ADX > 25 estricto o aislar a temporalidad M15.")
        if fam == "GOLD" and any("XAG" in (r["instrument"] or "") for r in rows):
            suggestions.append("Familia GOLD: Asegurar que XAGUSD siga completamente aislado del perfil de Oro.")

    if not suggestions:
        suggestions.append("El sistema está operando con los filtros optimizados. Revisar tras la acumulación de más ciclos a las 9:00 AM.")

    for s in suggestions:
        print(f" • {s}")
    print("=" * 80)

    conn.close()
    return {
        "family_stats": dict(family_stats),
        "overall_win_rate": overall_wr,
        "total_r": total_r,
        "models_summary": models_summary,
        "block_reasons": dict(block_reasons),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auditoría de Comportamiento de Workers e IA")
    parser.add_argument("--db-path", default=None, help="Ruta a trading_bot.sqlite3 (por defecto base activa)")
    parser.add_argument("--models-dir", default="storage/ai_models", help="Ruta a storage/ai_models")
    args = parser.parse_args()
    run_audit(args.db_path, args.models_dir)
