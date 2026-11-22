import glob
import os
import datetime

now = datetime.datetime.now()
print(f"Hora actual local: {now.strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

active_count = 0
total_count = 0

for f in sorted(glob.glob("storage/logs/bots/*.log")):
    total_count += 1
    mtime = datetime.datetime.fromtimestamp(os.path.getmtime(f))
    diff_sec = (now - mtime).total_seconds()
    size_kb = os.path.getsize(f) / 1024.0
    status = "🟢 ACTIVO (escribiendo)" if diff_sec < 60 else ("🟡 RECIENTE" if diff_sec < 180 else "⚪ INACTIVO")
    if diff_sec < 60:
        active_count += 1
    print(f"{os.path.basename(f):25s} | Modificado: {mtime.strftime('%H:%M:%S')} ({diff_sec:5.1f}s atrás) | {size_kb:7.1f} KB | {status}")

print("=" * 80)
print(f"Total workers: {total_count} | Workers escribiendo activamente: {active_count}")
