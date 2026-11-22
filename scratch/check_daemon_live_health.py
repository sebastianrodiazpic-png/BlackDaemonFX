import json
import urllib.request
import sqlite3
from pathlib import Path
from datetime import datetime

print("=== 1. VERIFICANDO API HTTP DEL DASHBOARD (http://127.0.0.1:8765) ===")
endpoints = [
    "/api/state",
    "/api/health",
    "/api/positions"
]

for ep in endpoints:
    url = f"http://127.0.0.1:8765{ep}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "HealthCheck/1.0"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = resp.read()
            parsed = json.loads(data.decode("utf-8"))
            print(f"[OK] {url} respondió con código 200 (tamaño: {len(data)} bytes)")
            if ep == "/api/state":
                workers = parsed.get("workers", [])
                print(f"     Workers activos reportados: {len(workers)}")
                for w in workers:
                    prof = w.get("bot_profile") or w.get("profile")
                    magic = w.get("daemon_magic") or w.get("magic")
                    strat = w.get("strategy_label") or w.get("strategy_key")
                    status = w.get("status") or w.get("state")
                    syms_count = len(w.get("symbols") or [])
                    print(f"     -> Worker {prof} (Magic {magic}): {strat} | Estado: {status} | Símbolos: {syms_count}")
    except Exception as e:
        print(f"[ERROR/WARN] {url}: {e}")

print("\n=== 2. VERIFICANDO BASE DE DATOS OPERACIONAL (storage/trading.db) ===")
db_path = Path("storage/trading.db")
if not db_path.exists():
    # buscar db en storage
    dbs = list(Path("storage").glob("*.db"))
    print(f"DBs encontrados en storage: {dbs}")
    db_path = dbs[0] if dbs else None

if db_path and db_path.exists():
    print(f"Conectando a {db_path}...")
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    cursor = conn.cursor()
    
    # Ver tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [r[0] for r in cursor.fetchall()]
    print(f"Tablas: {tables}")
    
    # Ver últimos eventos de auditoría
    if "audit_events" in tables:
        cursor.execute("SELECT event_type, action, created_at, payload FROM audit_events ORDER BY id DESC LIMIT 5")
        rows = cursor.fetchall()
        print("\nÚltimos 5 audit events:")
        for r in rows:
            print(f"  [{r[2]}] {r[0]} - {r[1]}")
            
    # Ver posiciones abiertas
    if "trades" in tables:
        cursor.execute("SELECT id, symbol, direction, magic, entry_price, status, created_at, comment FROM trades WHERE status='OPEN' LIMIT 10")
        open_trades = cursor.fetchall()
        print(f"\nTrades en estado OPEN: {len(open_trades)}")
        for t in open_trades:
            print(f"  ID {t[0]} | {t[1]} {t[2]} | Magic {t[3]} | Entry {t[4]} | Comment {t[7]}")
            
    conn.close()
else:
    print("No se encontró base de datos en storage/")
