import os
import psutil

print("=== CHECKING RUNNING PROCESSES (Python, MT5, Terminal) ===")
for p in psutil.process_iter(['pid', 'name', 'cmdline']):
    try:
        name = p.info['name'] or ''
        cmd = " ".join(p.info['cmdline'] or [])
        if any(x in name.lower() or x in cmd.lower() for x in ['terminal64', 'metatrader', 'python', 'daemon', 'blackfx', 'uvicorn']):
            print(f"PID {p.info['pid']}: {name} -> {cmd[:120]}")
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

print("\n=== ENV FILE CHECK ===")
for env_file in [".env", ".env.local", ".env.production", "config/.env"]:
    if os.path.exists(env_file):
        print(f"Found {env_file} ({os.path.getsize(env_file)} bytes)")
