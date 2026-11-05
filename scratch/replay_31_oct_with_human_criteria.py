import sys
sys.path.insert(0, '.')

import sqlite3
import json
import pandas as pd
from datetime import datetime, timezone

from config.ict_instrument_policy import ict_active_symbols
from strategy.human_criteria.human_criteria_engine import HumanCriteriaEngine
from strategy.human_criteria.config import HumanCriteriaConfig

db_path = r'C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3'
conn = sqlite3.connect(db_path)

cur = conn.cursor()
cur.execute("""
SELECT id, instrument, direction, created_at, exit_time, net_pnl, realized_rr, setup_reason, details_json 
FROM trades 
WHERE created_at LIKE '2026-10-31%' OR exit_time LIKE '2026-10-31%'
ORDER BY id ASC
""")

rows = cur.fetchall()

active_synth = set(ict_active_symbols('SYNTHETICS'))
active_forex = set(ict_active_symbols('FOREX'))
active_ict = set(ict_active_symbols('ICT'))
active_msnr = set(ict_active_symbols('MALAYSIAN_SNR'))
active_tpb = set(ict_active_symbols('TREND_PULLBACK'))

print(f"Total trades on 31-10: {len(rows)}")

pruned_blocked_trades = []
remaining_trades = []

for r in rows:
    t_id, inst, direction, created_at, exit_time, net_pnl, r_rr, setup_reason, details_json = r
    d = json.loads(details_json or '{}')
    strat = d.get('strategy') or d.get('source') or d.get('worker') or setup_reason or ''
    
    is_active = True
    reason_blocked = ""
    
    if 'TREND_PULLBACK' in strat:
        if inst not in active_tpb:
            is_active = False
            reason_blocked = f"Poda Trend Pullback: {inst} no está en universo activo TPB (>51% WR)"
    elif 'MALAYSIAN_SNR' in strat or 'MSNR' in strat:
        if inst not in active_msnr:
            is_active = False
            reason_blocked = f"Poda Malaysian SNR: {inst} no está en universo activo MSNR (>50% WR)"
    elif 'ICT' in strat or 'AMD' in strat:
        if inst in ('XAUUSD', 'US Tech 100', 'Wall Street 30', 'US Oil', 'BTCUSD'):
            if inst not in active_ict:
                is_active = False
                reason_blocked = f"Poda ICT: {inst} no está en activos ICT"
        else:
            if inst not in active_synth:
                is_active = False
                reason_blocked = f"Poda Sintéticos: {inst} no está en universo activo Sintéticos (>50% WR)"
                
    if not is_active:
        pruned_blocked_trades.append({
            "id": t_id,
            "instrument": inst,
            "direction": direction,
            "net_pnl": net_pnl,
            "rr": r_rr,
            "strategy": strat,
            "reason": reason_blocked
        })
    else:
        remaining_trades.append({
            "id": t_id,
            "instrument": inst,
            "direction": direction,
            "net_pnl": net_pnl,
            "rr": r_rr,
            "strategy": strat,
            "details": d
        })

print("\n=== TRADES QUE HABRÍAN SIDO BLOQUEADOS POR LA NUEVA PODA DE ACTIVOS ===")
print(f"Total bloqueados por poda: {len(pruned_blocked_trades)}")
pnl_saved_by_prune = sum(t['net_pnl'] for t in pruned_blocked_trades)
print(f"PnL de estos trades bloqueados: ${pnl_saved_by_prune:.2f}")
for t in pruned_blocked_trades:
    print(f"  ID {t['id']} | {t['instrument']} {t['direction']} | PnL: ${t['net_pnl']} ({t['rr']}R) | {t['reason']}")

print(f"\n=== TRADES RESTANTES TRAS LA PODA ({len(remaining_trades)}) ===")
pnl_remaining = sum(t['net_pnl'] for t in remaining_trades)
print(f"PnL restante antes de Criterio Humano: ${pnl_remaining:.2f}")

conn.close()
