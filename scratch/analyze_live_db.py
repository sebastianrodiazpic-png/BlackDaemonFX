import os
import sqlite3
from pathlib import Path
from collections import defaultdict
import json

db_path = Path(os.environ.get('LOCALAPPDATA', '')) / 'BlackDaemonFx' / 'trading_bot.sqlite3'
con = sqlite3.connect(f'file:{db_path.as_posix()}?mode=ro', uri=True)
cur = con.cursor()

print("==================================================")
print("1. ANÁLISIS DE TRADES EJECUTADOS (HISTÓRICO LIVE)")
print("==================================================")
cur.execute("""
    SELECT 
        source,
        COUNT(*) as total,
        SUM(CASE WHEN net_pnl > 0 THEN 1 ELSE 0 END) as wins,
        SUM(CASE WHEN net_pnl < 0 THEN 1 ELSE 0 END) as losses,
        SUM(CASE WHEN net_pnl == 0 THEN 1 ELSE 0 END) as be,
        ROUND(SUM(net_pnl), 2) as total_pnl,
        ROUND(AVG(realized_rr), 3) as avg_rr,
        ROUND(AVG(planned_rr), 3) as avg_plan_rr
    FROM trades
    GROUP BY source
    ORDER BY total DESC
""")
print(f"{'Estrategia/Source':<20} | {'Total':<6} | {'Wins':<5} | {'Loss':<5} | {'BE':<4} | {'WR%':<6} | {'Net PnL':<10} | {'Avg RR':<7} | {'Plan RR':<7}")
print("-" * 80)
for r in cur.fetchall():
    total, wins, losses = r[1], r[2], r[3]
    decided = wins + losses
    wr = (wins / decided * 100) if decided > 0 else 0.0
    print(f"{str(r[0])[:20]:<20} | {r[1]:<6} | {r[2]:<5} | {r[3]:<5} | {r[4]:<4} | {wr:5.1f}% | ${r[5]:<9} | {r[6]:<7} | {r[7]:<7}")

print("\n--- TOP 15 ACTIVOS POR RENDIMIENTO REALIZADO ---")
cur.execute("""
    SELECT 
        instrument,
        COUNT(*) as total,
        SUM(CASE WHEN net_pnl > 0 THEN 1 ELSE 0 END) as wins,
        SUM(CASE WHEN net_pnl < 0 THEN 1 ELSE 0 END) as losses,
        ROUND(SUM(net_pnl), 2) as total_pnl,
        ROUND(AVG(realized_rr), 3) as avg_rr
    FROM trades
    GROUP BY instrument
    HAVING total >= 15
    ORDER BY total_pnl DESC
    LIMIT 15
""")
print(f"{'Instrumento':<25} | {'Total':<6} | {'Wins':<5} | {'Loss':<5} | {'WR%':<6} | {'Net PnL':<10} | {'Avg RR':<7}")
print("-" * 75)
for r in cur.fetchall():
    decided = r[2] + r[3]
    wr = (r[2] / decided * 100) if decided > 0 else 0.0
    print(f"{str(r[0])[:25]:<25} | {r[1]:<6} | {r[2]:<5} | {r[3]:<5} | {wr:5.1f}% | ${r[4]:<9} | {r[5]:<7}")

print("\n--- TOP 10 ACTIVOS CON PEOR RENDIMIENTO (CANDIDATOS A PODA O CALIBRACIÓN) ---")
cur.execute("""
    SELECT 
        instrument,
        COUNT(*) as total,
        SUM(CASE WHEN net_pnl > 0 THEN 1 ELSE 0 END) as wins,
        SUM(CASE WHEN net_pnl < 0 THEN 1 ELSE 0 END) as losses,
        ROUND(SUM(net_pnl), 2) as total_pnl,
        ROUND(AVG(realized_rr), 3) as avg_rr
    FROM trades
    GROUP BY instrument
    HAVING total >= 10
    ORDER BY total_pnl ASC
    LIMIT 10
""")
for r in cur.fetchall():
    decided = r[2] + r[3]
    wr = (r[2] / decided * 100) if decided > 0 else 0.0
    print(f"{str(r[0])[:25]:<25} | {r[1]:<6} | {r[2]:<5} | {r[3]:<5} | {wr:5.1f}% | ${r[4]:<9} | {r[5]:<7}")

print("\n==================================================")
print("2. ANÁLISIS DE MOTIVOS DE CIERRE (EXIT REASONS)")
print("==================================================")
cur.execute("""
    SELECT exit_reason, COUNT(*), ROUND(SUM(net_pnl), 2), ROUND(AVG(realized_rr), 3)
    FROM trades
    GROUP BY exit_reason
    ORDER BY COUNT(*) DESC
""")
for r in cur.fetchall():
    print(f"Razón: {str(r[0])[:30]:<30} | Trades: {r[1]:<6} | PnL: ${r[2]:<9} | Avg RR: {r[3]}")

print("\n==================================================")
print("3. ANÁLISIS DE EVENTOS DE AUDITORÍA (ÚLTIMAS 72H Y HISTÓRICO)")
print("==================================================")
cur.execute("SELECT MIN(event_time), MAX(event_time) FROM daemon_audit_events")
min_t, max_t = cur.fetchone()
print(f"Rango temporal auditoría: {min_t} hasta {max_t}")

cur.execute("""
    SELECT reason, count(*) as cnt 
    FROM daemon_audit_events 
    GROUP BY reason 
    ORDER BY cnt DESC 
    LIMIT 25
""")
print(f"{'Razón de Descarte / Evento':<55} | {'Conteo':<8}")
print("-" * 65)
for r in cur.fetchall():
    print(f"{str(r[0])[:55]:<55} | {r[1]:<8}")

print("\n==================================================")
print("4. MODO CENTINELA: TOXIC REGIME BLOCKS POR ACTIVO")
print("==================================================")
cur.execute("""
    SELECT instrument, count(*) as cnt 
    FROM daemon_audit_events 
    WHERE reason LIKE '%TOXIC%' OR reason LIKE '%CENTINELA%' OR reason LIKE '%REGIME%'
    GROUP BY instrument 
    ORDER BY cnt DESC 
    LIMIT 15
""")
for r in cur.fetchall():
    print(f"{str(r[0])[:30]:<30} | {r[1]:<8} bloqueos de régimen")

print("\n==================================================")
print("5. ANÁLISIS DE MSNR CANDIDATES (PIPELINE)")
print("==================================================")
cur.execute("""
    SELECT stage, COUNT(*) 
    FROM msnr_candidates 
    GROUP BY stage 
    ORDER BY COUNT(*) DESC
""")
for r in cur.fetchall():
    print(f"Stage: {str(r[0])[:30]:<30} | Candidatos: {r[1]}")

con.close()
