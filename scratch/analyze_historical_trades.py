import sys
import sqlite3
import json
from collections import defaultdict
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.database import resolve_db_path

def analyze():
    db_path = resolve_db_path()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, instrument, direction, status, result, net_pnl, realized_rr, setup_reason, exit_reason, details_json, created_at
        FROM trades
    """)
    trades = cur.fetchall()

    stats_by_asset = defaultdict(lambda: {'total': 0, 'wins': 0, 'losses': 0, 'be': 0, 'emergency': 0, 'pnl': 0.0, 'rr_sum': 0.0, 'strategies': defaultdict(lambda: {'total': 0, 'wins': 0, 'losses': 0, 'pnl': 0.0, 'rr_sum': 0.0})})
    stats_by_strategy = defaultdict(lambda: {'total': 0, 'wins': 0, 'losses': 0, 'be': 0, 'pnl': 0.0, 'rr_sum': 0.0, 'assets': defaultdict(int)})

    for t in trades:
        tid, inst, direction, status, result, net_pnl, realized_rr, setup_reason, exit_reason, details_json, created_at = t
        if status != 'CLOSED':
            continue
        
        d = json.loads(details_json) if details_json else {}
        strat = d.get('strategy') or d.get('strategy_name') or d.get('bot_profile') or d.get('profile') or 'UNKNOWN'
        if strat == 'UNKNOWN':
            setup_str = str(setup_reason or '')
            if 'ORB' in setup_str:
                strat = 'ORB_NEW_YORK'
            elif 'MALAYSIAN' in setup_str or 'SnR' in setup_str or 'V_VALLEY' in setup_str or 'A_PEAK' in setup_str:
                strat = 'MALAYSIAN_SNR'
            elif 'QUARTERS' in setup_str or 'MAJOR' in setup_str or 'MINOR' in setup_str:
                strat = 'GOLD_QUARTERS'
            elif 'ICT' in setup_str or 'JUDAS' in setup_str or 'AMD' in setup_str:
                strat = 'ICT'
            else:
                strat = 'SMC'

        pnl = float(net_pnl or 0.0)
        rr = float(realized_rr or 0.0)

        s_a = stats_by_asset[inst]
        s_a['total'] += 1
        s_a['pnl'] += pnl
        s_a['rr_sum'] += rr
        
        st_entry = s_a['strategies'][strat]
        st_entry['total'] += 1
        st_entry['pnl'] += pnl
        st_entry['rr_sum'] += rr

        s_s = stats_by_strategy[strat]
        s_s['total'] += 1
        s_s['pnl'] += pnl
        s_s['rr_sum'] += rr
        s_s['assets'][inst] += 1

        if result == 'WIN':
            s_a['wins'] += 1
            s_s['wins'] += 1
            st_entry['wins'] += 1
        elif result == 'LOSS':
            s_a['losses'] += 1
            s_s['losses'] += 1
            st_entry['losses'] += 1
        elif result == 'BREAKEVEN':
            s_a['be'] += 1
            s_s['be'] += 1
        else:
            s_a['emergency'] += 1
            s_s['losses'] += 1
            st_entry['losses'] += 1

    print('=== STATS BY STRATEGY ===')
    for strat, d in sorted(stats_by_strategy.items(), key=lambda x: x[1]['pnl'], reverse=True):
        wr = (d['wins'] / d['total'] * 100) if d['total'] else 0
        print(f"{strat:22s}: Total={d['total']:3d} | W={d['wins']:3d} L={d['losses']:3d} BE={d['be']:3d} | WR={wr:5.1f}% | NetPnL={d['pnl']:10.2f} | NetRR={d['rr_sum']:6.2f}")

    print('\n=== TOP 20 MOST PROFITABLE ASSETS ===')
    sorted_assets = sorted(stats_by_asset.items(), key=lambda x: x[1]['pnl'], reverse=True)
    for inst, d in sorted_assets[:20]:
        wr = (d['wins'] / d['total'] * 100) if d['total'] else 0
        best_strat = max(d['strategies'].items(), key=lambda x: x[1]['pnl']) if d['strategies'] else ('NONE', {})
        print(f"{inst:28s}: Total={d['total']:3d} | W={d['wins']:3d} L={d['losses']:3d} BE={d['be']:3d} | WR={wr:5.1f}% | NetPnL={d['pnl']:10.2f} | NetRR={d['rr_sum']:6.2f} | Best Strat: {best_strat[0]} (PnL: {best_strat[1]['pnl']:.2f}, WR: {(best_strat[1]['wins']/best_strat[1]['total']*100) if best_strat[1]['total'] else 0:.1f}%)")

    print('\n=== BOTTOM 15 LEAST PROFITABLE / WORST ASSETS (PODADOS/DESACTIVADOS) ===')
    for inst, d in sorted_assets[-15:]:
        wr = (d['wins'] / d['total'] * 100) if d['total'] else 0
        best_strat = max(d['strategies'].items(), key=lambda x: x[1]['pnl']) if d['strategies'] else ('NONE', {})
        print(f"{inst:28s}: Total={d['total']:3d} | W={d['wins']:3d} L={d['losses']:3d} BE={d['be']:3d} | WR={wr:5.1f}% | NetPnL={d['pnl']:10.2f} | NetRR={d['rr_sum']:6.2f} | Best Strat: {best_strat[0]} (PnL: {best_strat[1]['pnl']:.2f})")

    # Audit events check for meta-labeling
    cur.execute("SELECT count(*) FROM daemon_audit_events WHERE event_type LIKE '%META%' OR event_type LIKE '%AI%'")
    ai_events = cur.fetchone()[0]
    print(f"\nTotal AI / Meta-labeling audit events in DB: {ai_events}")

    cur.execute("SELECT event_type, count(*) FROM daemon_audit_events WHERE event_type LIKE '%META%' OR event_type LIKE '%AI%' GROUP BY event_type")
    for row in cur.fetchall():
        print(f"  - {row[0]}: {row[1]}")

    conn.close()

if __name__ == '__main__':
    analyze()
