import sqlite3
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from database.database import resolve_db_path

db_path = resolve_db_path()
conn = sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True)
cur = conn.cursor()

cur.execute("""
    SELECT id, instrument, direction, status, entry_time, exit_time, net_pnl, realized_rr, strategy_version, details_json
    FROM trade_journal
    WHERE entry_time >= '2026-10-04' AND entry_time <= '2026-10-10'
      AND (details_json LIKE '%MALAYSIAN_SNR%' OR strategy_version LIKE 'msnr%')
    ORDER BY id ASC
""")

rows = cur.fetchall()
print(f"Total rows found: {len(rows)}")

symbols = Counter()
scenarios = Counter()
versions = Counter()
symbol_pnl = defaultdict(float)
symbol_trades = defaultdict(int)
symbol_wins = defaultdict(int)
scenario_pnl = defaultdict(float)
scenario_wins = defaultdict(int)

wins = 0
losses = 0
total_pnl = 0.0

for r in rows:
    inst = r[1]
    pnl = r[6] or 0.0
    ver = r[8] or 'UNKNOWN'
    det = json.loads(r[9] or '{}')
    meta = det.get('metadata') or {}
    sc = meta.get('scenario') or meta.get('msnr_scenario') or 'UNKNOWN'
    
    symbols[inst] += 1
    scenarios[sc] += 1
    versions[ver] += 1
    total_pnl += pnl
    symbol_pnl[inst] += pnl
    symbol_trades[inst] += 1
    scenario_pnl[sc] += pnl
    
    if pnl > 0:
        wins += 1
        symbol_wins[inst] += 1
        scenario_wins[sc] += 1
    elif pnl < 0:
        losses += 1

print(f"\nResumen Global Oct 4 al 10:")
print(f"  Total Trades (piernas): {len(rows)}")
print(f"  Ganadoras: {wins}, Perdedoras: {losses}")
print(f"  WinRate global: {(wins/len(rows)*100 if rows else 0):.1f}%")
print(f"  Net PnL total: ${total_pnl:.2f}")

print(f"\nVersiones de Estrategia registradas:")
for v, count in versions.most_common():
    print(f"  - {v}: {count} trades")

print(f"\nEscenarios operados:")
for sc, count in scenarios.most_common():
    w = scenario_wins[sc]
    p = scenario_pnl[sc]
    wr = (w/count*100) if count else 0
    print(f"  - {sc}: {count} trades | WinRate: {wr:.1f}% | PnL: ${p:.2f}")

print(f"\nTop 15 Activos por volumen:")
for inst, count in symbols.most_common(15):
    w = symbol_wins[inst]
    p = symbol_pnl[inst]
    wr = (w/count*100) if count else 0
    print(f"  - {inst:25}: {count:3} trades | WR: {wr:5.1f}% | PnL: ${p:8.2f}")

# Sample 3 trades to see what entry metadata looked like in v1.0
print("\nEjemplo de metadatos de entrada antigua:")
for r in rows[:2]:
    det = json.loads(r[9] or '{}')
    meta = det.get('metadata') or {}
    print(f"ID #{r[0]} ({r[1]} {r[2]}):")
    print(f"  TF: {meta.get('timeframe')}, entry_tf: {meta.get('entry_timeframe')}, scenario: {meta.get('scenario')}")
    print(f"  confirmations: {meta.get('confirmations') or meta.get('confirmation_details')}")
    print(f"  entry_reason: {meta.get('entry_reason') or det.get('setup_reason')}")
