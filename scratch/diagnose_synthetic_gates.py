"""Que gates del engine paran las señales VALIDAS de ICT/MSNR en sinteticos (DB real)."""
import sys, json
from pathlib import Path
from collections import Counter, defaultdict

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from database.repository import TradingRepository, DaemonAuditEvent
from sqlalchemy import select

SYN = ("boom", "crash", "volatility", "step", "jump", "flip", "1hz")
repo = TradingRepository()
with repo.Session() as s:
    cols = [c.name for c in DaemonAuditEvent.__table__.columns]
    print("cols:", cols)
    rows = s.execute(select(DaemonAuditEvent).where(DaemonAuditEvent.event_type == "SYMBOL_PROCESS_RESULT")).scalars().all()

print("total rows", len(rows))
by_action = defaultdict(Counter)
reasons = defaultdict(Counter)
for r in rows:
    p = {}
    try:
        p = json.loads(r.payload_json) if r.payload_json else {}
    except Exception:
        pass
    inst = (getattr(r, "instrument", None) or p.get("symbol") or "").lower()
    if not any(k in inst for k in SYN):
        continue
    prof = str(p.get("bot_profile") or p.get("worker") or "?").upper()
    act = r.action or "?"
    by_action[prof][act] += 1
    if act not in ("WAITING_ICT", "NO_SIGNAL", "WAITING_MSNR", "NO_SETUP", "SYMBOL_NOT_IN_MSNR_ALLOWLIST"):
        reasons[(prof, act)][str(r.reason)[:90]] += 1

for prof, c in sorted(by_action.items()):
    print(f"\n== {prof} ==")
    for a, n in c.most_common(25):
        print(f"  {a}: {n}")
print("\n=== Razones de acciones NO-espera (gates/ejecucion) ===")
for (prof, act), c in sorted(reasons.items()):
    print(f"[{prof}] {act}")
    for rs, n in c.most_common(4):
        print(f"    {n}  {rs}")
