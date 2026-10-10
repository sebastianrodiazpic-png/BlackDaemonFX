import sqlite3
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict, Counter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def run_audit():
    print("="*80)
    print("BLACKDAEMONFX · AUDITORIA PROFUNDA DE SISTEMA, ESTRATEGIAS Y CAPITAL")
    print(f"Timestamp Local: {datetime.now().isoformat()}")
    print("="*80)

    from database.repository import TradingRepository
    repo = TradingRepository()
    db_path = repo.db_path
    print(f"Ruta autoritativa DB: {db_path} (Existe: {db_path.exists()}, Tam: {db_path.stat().st_size / (1024*1024):.2f} MB)")

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1. AUDITORÍA DE TRADES REGISTRADOS
    print("\n" + "="*80)
    print("[1] ANÁLISIS DE TRADES REGISTRADOS EN TABLA 'trades'")
    print("="*80)

    cur.execute("SELECT COUNT(*) FROM trades")
    total_trades = cur.fetchone()[0]
    print(f"Total trades en tabla 'trades': {total_trades}")

    # Desglose por estrategia / version
    cur.execute("""
        SELECT strategy_version, status, COUNT(*) as cnt,
               SUM(CASE WHEN net_pnl > 0 THEN 1 ELSE 0 END) as wins,
               SUM(CASE WHEN net_pnl < 0 THEN 1 ELSE 0 END) as losses,
               AVG(risk_percent) as avg_risk_pct,
               SUM(net_pnl) as total_pnl
        FROM trades 
        GROUP BY strategy_version, status
    """)
    for r in cur.fetchall():
        print(f"  - Estrategia: {str(r['strategy_version']):<25} | Status: {r['status']:<10} | Trades: {r['cnt']:<5} | Wins: {r['wins']:<4} | Losses: {r['losses']:<4} | AvgRisk%: {r['avg_risk_pct']} | PnL: ${r['total_pnl'] or 0:.2f}")

    # Desglose por instrumento
    cur.execute("""
        SELECT instrument, strategy_version, COUNT(*) as cnt,
               AVG(volume) as avg_vol,
               AVG(risk_percent) as avg_risk_pct,
               AVG(risk_amount) as avg_risk_usd,
               SUM(net_pnl) as total_pnl
        FROM trades
        GROUP BY instrument, strategy_version
        ORDER BY cnt DESC
    """)
    print("\nDesglose de trades por instrumento y estrategia:")
    for r in cur.fetchall():
        print(f"  - {r['instrument']:<22} | Strat: {str(r['strategy_version']):<20} | Trades: {r['cnt']:<4} | AvgVol: {r['avg_vol']:.4f} | Risk%: {r['avg_risk_pct']} | RiskUSD: ${r['avg_risk_usd'] or 0:.2f} | PnL: ${r['total_pnl'] or 0:.2f}")

    # Muestra de los últimos 20 trades con todos los detalles de tamaño, 2 piernas, etc.
    cur.execute("""
        SELECT id, external_ticket, broker_position_ticket, instrument, direction, volume,
               entry_price, stop_loss, take_profit, planned_rr, realized_rr,
               risk_percent, risk_amount, net_pnl, status, setup_reason, details_json,
               strategy_version, created_at
        FROM trades 
        ORDER BY id DESC LIMIT 20
    """)
    recent_trades = cur.fetchall()
    print(f"\nÚltimos {len(recent_trades)} trades registrados:")
    for t in recent_trades:
        details = {}
        if t['details_json']:
            try: details = json.loads(t['details_json'])
            except: pass
        leg = details.get('split_order_leg', details.get('leg', details.get('order_leg', 'N/A')))
        magic = details.get('magic', details.get('daemon_magic', 'N/A'))
        print(f"  ID:{t['id']:<4} Ticket:{t['broker_position_ticket'] or t['external_ticket']} Strat:{str(t['strategy_version']):<18} Sym:{t['instrument']:<16} Dir:{t['direction']:<5} Vol:{t['volume']:<5} Risk%:{t['risk_percent']} Risk$:{t['risk_amount']} Leg:{leg} Magic:{magic} PnL:${t['net_pnl'] or 0:.2f} Status:{t['status']}")

    # 2. AUDITORÍA DE TRADES EN TRADE_JOURNAL
    print("\n" + "="*80)
    print("[2] ANÁLISIS DE TRADES EN 'trade_journal'")
    print("="*80)
    cur.execute("SELECT COUNT(*) FROM trade_journal")
    print(f"Total en trade_journal: {cur.fetchone()[0]}")
    cur.execute("SELECT strategy_version, status, COUNT(*), SUM(net_pnl) FROM trade_journal GROUP BY strategy_version, status")
    for r in cur.fetchall():
        print(f"  - Journal Strat: {str(r[0]):<25} Status: {r[1]:<10} Count: {r[2]} PnL: ${r[3] or 0:.2f}")

    # 3. WORKER RUNTIME STATES (¿Cuáles workers han estado vivos y qué han hecho?)
    print("\n" + "="*80)
    print("[3] ESTADOS DE RUNTIME DE LOS WORKERS (worker_runtime_states)")
    print("="*80)
    cur.execute("""
        SELECT bot_profile, daemon_magic, status, pid, cycle_number, symbols_total, 
               symbols_processed, current_symbol, last_action, last_reason, updated_at, details_json
        FROM worker_runtime_states 
        ORDER BY updated_at DESC
    """)
    workers = cur.fetchall()
    print(f"Workers registrados: {len(workers)}")
    for w in workers:
        dt = {}
        if w['details_json']:
            try: dt = json.loads(w['details_json'])
            except: pass
        print(f"  - Profile:{w['bot_profile']:<15} Magic:{w['daemon_magic']:<10} Status:{w['status']:<10} PID:{w['pid']:<6} Cycle:{w['cycle_number']:<4} Syms:{w['symbols_processed']}/{w['symbols_total']} Action:{w['last_action']:<25} Reason:{w['last_reason']} Upd:{w['updated_at']}")

    # 4. EVENTOS DE AUDITORÍA Y FILTROS/RECHAZOS (daemon_audit_events)
    print("\n" + "="*80)
    print("[4] EVENTOS DE AUDITORÍA, RECHAZOS Y BARRERAS (daemon_audit_events)")
    print("="*80)
    cur.execute("""
        SELECT event_type, action, COUNT(*) as cnt 
        FROM daemon_audit_events 
        GROUP BY event_type, action 
        ORDER BY cnt DESC LIMIT 25
    """)
    for ev in cur.fetchall():
        print(f"  - EventType:{ev['event_type']:<40} Action:{str(ev['action']):<30} Total:{ev['cnt']}")

    # Razones de rechazo o no-entrada en daemon_audit_events
    cur.execute("""
        SELECT reason, COUNT(*) as cnt 
        FROM daemon_audit_events 
        WHERE reason IS NOT NULL AND reason != ''
        GROUP BY reason 
        ORDER BY cnt DESC LIMIT 25
    """)
    print("\nTop 25 Motivos/Razones registradas en eventos de auditoría:")
    for r in cur.fetchall():
        print(f"  - {r['reason'][:70]:<72} ({r['cnt']} veces)")

    # 5. SEÑALES EN LA TABLA SIGNALS (¿Cuántas señales SMC e ICT se intentaron evaluar?)
    print("\n" + "="*80)
    print("[5] EVALUACIÓN DE SEÑALES (tabla signals)")
    print("="*80)
    cur.execute("SELECT COUNT(*) FROM signals")
    total_sig = cur.fetchone()[0]
    print(f"Total señales generadas históricamente: {total_sig}")
    cur.execute("SELECT valid, COUNT(*) FROM signals GROUP BY valid")
    for r in cur.fetchall():
        print(f"  - Valid={r[0]}: {r[1]} señales")

    # Muestra de señales recientes
    cur.execute("""
        SELECT id, instrument, timeframe, direction, valid, signal_time, 
               trend_ok, swing_ok, liquidity_ok, sweep_ok, structure_break_ok, 
               order_block_ok, retest_ok, premium_discount_ok, confirmation_ok, details_json
        FROM signals 
        ORDER BY id DESC LIMIT 15
    """)
    print("\nÚltimas 15 señales registradas:")
    for s in cur.fetchall():
        dt = {}
        if s['details_json']:
            try: dt = json.loads(s['details_json'])
            except: pass
        score = dt.get('smc_score', dt.get('score', 'N/A'))
        print(f"  ID:{s['id']} {s['instrument']:<16} TF:{s['timeframe']} Dir:{s['direction']} Valid:{s['valid']} Trend:{s['trend_ok']} Swg:{s['swing_ok']} Liq:{s['liquidity_ok']} Swp:{s['sweep_ok']} BoS:{s['structure_break_ok']} OB:{s['order_block_ok']} Ret:{s['retest_ok']} Disc:{s['premium_discount_ok']} Score:{score}")

    conn.close()

if __name__ == "__main__":
    run_audit()
