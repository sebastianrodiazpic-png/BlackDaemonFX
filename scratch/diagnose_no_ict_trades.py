"""Diagnostic script: Analyze why no ICT trades have been triggered.
Examines database DaemonAuditEvent rows and bot logs.
"""
import sys
import json
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from database.repository import TradingRepository, DaemonAuditEvent
from sqlalchemy import select, func

def analyze_db_audit():
    repo = TradingRepository()
    with repo.Session() as session:
        # Check total SYMBOL_PROCESS_RESULT events
        total_evals = session.query(func.count(DaemonAuditEvent.id)).filter(
            DaemonAuditEvent.event_type == "SYMBOL_PROCESS_RESULT"
        ).scalar()
        
        # Check last 1000 events
        rows = session.execute(
            select(DaemonAuditEvent)
            .where(DaemonAuditEvent.event_type == "SYMBOL_PROCESS_RESULT")
            .order_by(DaemonAuditEvent.id.desc())
            .limit(1000)
        ).scalars().all()
        
        reasons_counter = Counter()
        actions_counter = Counter()
        profiles_counter = Counter()
        reasons_by_profile = {}
        
        for r in rows:
            act = r.action or "UNKNOWN"
            actions_counter[act] += 1
            rsn = r.reason or "NO_REASON"
            reasons_counter[rsn] += 1
            
            payload = {}
            if r.payload_json:
                try: payload = json.loads(r.payload_json)
                except Exception: pass
            
            prof = payload.get("bot_profile") or "UNKNOWN"
            profiles_counter[prof] += 1
            if prof not in reasons_by_profile:
                reasons_by_profile[prof] = Counter()
            reasons_by_profile[prof][rsn] += 1

        print("=== RECENT 1000 SYMBOL EVALUATIONS IN DB ===")
        print(f"Total symbol process evaluations recorded in DB: {total_evals}")
        print("\nTop Actions:")
        for act, cnt in actions_counter.most_common(10):
            print(f"  {act}: {cnt}")
            
        print("\nTop Rejection Reasons Overall:")
        for rsn, cnt in reasons_counter.most_common(15):
            print(f"  {rsn}: {cnt}")
            
        print("\nRejection Reasons By Worker Profile:")
        for prof, counter in sorted(reasons_by_profile.items()):
            print(f"  Worker [{prof}]:")
            for rsn, cnt in counter.most_common(5):
                print(f"    - {rsn}: {cnt}")

def analyze_bot_logs():
    logs_dir = PROJECT_ROOT / "storage" / "logs" / "bots"
    print("\n=== LOG ANALYSIS (REASONS IN RECENT CYCLES) ===")
    for log_file in sorted(logs_dir.glob("*.log")):
        if log_file.stat().st_size == 0:
            continue
        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()[-300:]
            
            reasons = []
            for line in lines:
                if "Motivo:" in line:
                    reasons.append(line.split("Motivo:")[-1].strip())
            
            if reasons:
                c = Counter(reasons)
                print(f"\nLog: {log_file.name} (últimas evaluaciones):")
                for r, cnt in c.most_common(3):
                    print(f"  - {r}: {cnt} veces")
        except Exception as e:
            print(f"Error reading {log_file.name}: {e}")

if __name__ == "__main__":
    analyze_db_audit()
    analyze_bot_logs()
