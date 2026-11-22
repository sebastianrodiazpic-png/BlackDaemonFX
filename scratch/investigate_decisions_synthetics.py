"""
Script para investigar las decisiones de entrada en índices sintéticos
a través del repositorio y las tablas de auditoría.
"""
import sys
import os
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.repository import TradingRepository
from database.models import DaemonAuditEvent, Trade, Signal

repo = TradingRepository()

print("=" * 80)
print("1. INFORME OFICIAL DE DECISIONES (/api/entry-decisions)")
print("=" * 80)
report = repo.entry_decision_report(days=7, source=None)
print("Keys in report:", list(report.keys()))
events_summary = report.get("events_summary", {})
print("Events summary total:", events_summary.get("total"))
print("By action:", events_summary.get("by_action"))
print("By strategy:", events_summary.get("by_strategy"))
print("Top vetoed symbols:", events_summary.get("top_vetoed_symbols", [])[:10])

recent_vetoes = report.get("recent_vetoes", [])
print(f"\nTotal recent vetoes: {len(recent_vetoes)}")
synth_keywords = ["volatility", "boom", "crash", "jump", "step", "ladder", "volswitch", "dex"]

synth_vetoes = [
    v for v in recent_vetoes 
    if any(k in (v.get("instrument") or "").lower() for k in synth_keywords)
]
print(f"Total recent vetoes en sintéticos: {len(synth_vetoes)}")
for v in synth_vetoes[:20]:
    print(f"  [{v.get('event_time')}] {v.get('instrument')} | Etapa: {v.get('stage')} | Decisión: {v.get('action')} | Estrategia: {v.get('strategy')} | Motivo: {v.get('reason')}")

print("\n" + "=" * 80)
print("2. CONSULTA DIRECTA A DaemonAuditEvent (Últimos 3 días)")
print("=" * 80)
cutoff = datetime.now(timezone.utc) - timedelta(days=3)

with repo.Session() as session:
    from sqlalchemy import select, func
    
    # Ver los tipos de eventos y acciones en la base de datos
    actions_q = (
        select(DaemonAuditEvent.event_type, DaemonAuditEvent.action, func.count())
        .where(DaemonAuditEvent.event_time >= cutoff)
        .group_by(DaemonAuditEvent.event_type, DaemonAuditEvent.action)
    )
    print("Eventos de auditoría por tipo y acción:")
    for etype, act, cnt in session.execute(actions_q).all():
        print(f"  {etype} | {act}: {cnt}")
        
    # Buscar eventos de sintéticos
    synth_events_q = (
        select(DaemonAuditEvent)
        .where(DaemonAuditEvent.event_time >= cutoff)
        .order_by(DaemonAuditEvent.event_time.desc())
        .limit(200)
    )
    rows = session.execute(synth_events_q).scalars().all()
    synth_rows = [
        r for r in rows 
        if any(k in (r.instrument or "").lower() for k in synth_keywords)
    ]
    print(f"\nÚltimos eventos en sintéticos (muestra de {len(synth_rows)}):")
    for r in synth_rows[:25]:
        payload_desc = ""
        if r.payload_json:
            try:
                p = json.loads(r.payload_json)
                payload_desc = f"reason={p.get('reason', p.get('rejection_reason', ''))} score={p.get('score', '')} grade={p.get('grade', '')} prob={p.get('ai_prob', '')}"
            except Exception:
                payload_desc = r.payload_json[:100]
        print(f"  [{r.event_time}] {r.instrument} | Type: {r.event_type} | Action: {r.action} | {payload_desc}")

print("\n" + "=" * 80)
print("3. SEÑALES Y TRADES REGISTRADOS EN SINTÉTICOS (Últimos 3 días)")
print("=" * 80)
with repo.Session() as session:
    from sqlalchemy import select
    sig_q = (
        select(Signal)
        .where(Signal.created_at >= cutoff)
        .order_by(Signal.created_at.desc())
        .limit(50)
    )
    sigs = session.execute(sig_q).scalars().all()
    synth_sigs = [s for s in sigs if any(k in (s.symbol or "").lower() for k in synth_keywords)]
    print(f"Señales generadas en sintéticos: {len(synth_sigs)}")
    for s in synth_sigs[:15]:
        print(f"  [{s.created_at}] {s.symbol} | Dir: {s.direction} | Strategy: {s.strategy} | Status: {s.status} | TF: {s.timeframe}")

    trade_q = (
        select(Trade)
        .where(Trade.created_at >= cutoff)
        .order_by(Trade.created_at.desc())
        .limit(50)
    )
    trades = session.execute(trade_q).scalars().all()
    synth_trades = [t for t in trades if any(k in (t.symbol or "").lower() for k in synth_keywords)]
    print(f"\nTrades generados en sintéticos: {len(synth_trades)}")
    for t in synth_trades[:15]:
        print(f"  [{t.created_at}] {t.symbol} | Dir: {t.direction} | Magic: {t.magic} | Status: {t.status} | Profit: {t.profit}")
