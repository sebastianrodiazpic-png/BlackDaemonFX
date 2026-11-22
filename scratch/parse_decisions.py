import json
from collections import Counter

with open("scratch/entry_decisions_raw.json", "r", encoding="utf-8-sig") as f:
    data = json.load(f)

print("=== KEYS EN EL REPORTE ===")
print(list(data.keys()))

events_summary = data.get("events_summary", {})
print("\n=== RESUMEN DE EVENTOS ===")
print(f"Total eventos: {events_summary.get('total')}")
print(f"Por acción: {events_summary.get('by_action')}")
print(f"Por estrategia: {events_summary.get('by_strategy')}")
print(f"Por etapa: {events_summary.get('by_stage')}")
print(f"Top símbolos vetados: {events_summary.get('top_vetoed_symbols')}")

recent_vetoes = data.get("recent_vetoes", [])
print(f"\n=== ÚLTIMOS VETOS (Total: {len(recent_vetoes)}) ===")

synth_keywords = ["volatility", "boom", "crash", "jump", "step", "ladder", "volswitch", "dex", "1s"]

synth_vetoes = [
    v for v in recent_vetoes 
    if any(k in (v.get("instrument") or "").lower() for k in synth_keywords)
]

print(f"Total vetos en índices sintéticos: {len(synth_vetoes)}")

# Agrupar por instrumento y motivo
reasons_by_sym = {}
reasons_counter = Counter()
stages_counter = Counter()

for v in synth_vetoes:
    sym = v.get("instrument")
    stage = v.get("stage")
    action = v.get("action")
    strat = v.get("strategy")
    reason = v.get("reason")
    reasons_counter[f"[{stage}:{action}] {reason}"] += 1
    stages_counter[stage] += 1
    if sym not in reasons_by_sym:
        reasons_by_sym[sym] = []
    reasons_by_sym[sym].append({
        "time": v.get("event_time"),
        "stage": stage,
        "action": action,
        "strategy": strat,
        "reason": reason
    })

print("\n=== MOTIVOS DE VETO EN SINTÉTICOS ===")
for r, count in reasons_counter.most_common(15):
    print(f"  ({count} veces) {r}")

print("\n=== DESGLOSE POR INSTRUMENTO (Primeros 10) ===")
for sym, vlist in list(reasons_by_sym.items())[:10]:
    print(f"\nInstrumento: {sym} ({len(vlist)} vetos)")
    for v in vlist[:5]:
        print(f"    {v['time']} | Etapa: {v['stage']} | Acción: {v['action']} | Strat: {v['strategy']} | Motivo: {v['reason']}")

print("\n=== TRADES CON DECISIÓN REGISTRADA ===")
recent_trades = data.get("recent_trades", [])
print(f"Total recent trades en reporte: {len(recent_trades)}")
synth_trades = [
    t for t in recent_trades 
    if any(k in (t.get("instrument") or "").lower() for k in synth_keywords)
]
print(f"Trades en sintéticos: {len(synth_trades)}")
for t in synth_trades[:10]:
    print(f"  {t.get('entry_time')} | {t.get('instrument')} | Dir: {t.get('direction')} | Strat: {t.get('strategy')} | HC: {t.get('human_score')} | Tri: {t.get('tripartite_action')} | AI: {t.get('ai_prob')} | Outcome: {t.get('status')} | R: {t.get('realized_r')}")
