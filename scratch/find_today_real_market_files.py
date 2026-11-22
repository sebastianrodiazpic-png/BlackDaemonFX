import os
import json
from pathlib import Path

for root, dirs, files in os.walk("storage/runtime"):
    for f in files:
        if f.endswith(".json") and ("ICT" in f or "ORB" in f or "INDICES" in f or "COMMOD" in f or "FOREX" in f):
            p = Path(root) / f
            mtime = p.stat().st_mtime
            import datetime
            mtime_dt = datetime.datetime.fromtimestamp(mtime, tz=datetime.timezone.utc)
            if mtime_dt.date() == datetime.date(2026, 11, 16):
                print(f"{p} | modified: {mtime_dt}")
                try:
                    with open(p, "r", encoding="utf-8") as jf:
                        d = json.load(jf)
                        if isinstance(d, dict):
                            keys = list(d.keys())
                            print(f"   Keys: {keys[:8]}")
                            if "counts" in d:
                                print(f"   counts: {d['counts']}")
                            if "action" in d or "status" in d:
                                print(f"   status/action: {d.get('status')} / {d.get('action')}")
                            if "last_action" in d or "last_reason" in d:
                                print(f"   last: {d.get('last_action')} -> {d.get('last_reason')}")
                except Exception as e:
                    print(f"   Error: {e}")
