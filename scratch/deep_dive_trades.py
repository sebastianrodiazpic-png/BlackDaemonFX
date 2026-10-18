import sqlite3
import json

db_path = r"C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

trade_ids = [882, 883, 884, 885, 886, 887, 888, 889, 891, 892, 893, 894, 895, 896, 897, 898, 899, 900, 901]

print("=== DEEP DIVE INTO RECENT TRADES ===")
for tid in trade_ids:
    row = cur.execute("SELECT * FROM trades WHERE id = ?", (tid,)).fetchone()
    if not row:
        continue
    det = json.loads(row['details_json']) if row['details_json'] else {}
    print(f"\n" + "="*80)
    print(f"TRADE ID {row['id']} | TICKET {row['broker_position_ticket']} | {row['instrument']} | {row['direction']}")
    print(f"Strategy: {row['strategy_version']} | Setup: {row['setup_reason']}")
    print(f"Entry: {row['entry_price']} | Exit: {row['exit_price']} | SL: {row['stop_loss']} | TP: {row['take_profit']}")
    print(f"Net PnL: ${row['net_pnl']} | Planned RR: {row['planned_rr']} | Realized RR: {row['realized_rr']}")
    print(f"Entry Time (UTC): {row['entry_time']} | Exit Time (UTC): {row['exit_time']}")
    
    # Excursion
    mfe = det.get('max_favorable_excursion_rr') or det.get('metadata', {}).get('max_favorable_excursion_rr')
    mae = det.get('max_adverse_excursion_rr') or det.get('metadata', {}).get('max_adverse_excursion_rr')
    print(f"MFE: {mfe}R | MAE: {mae}R")
    
    # Meta labeling / features
    eval_data = det.get('meta_label_evaluation', {})
    if eval_data:
        feats = eval_data.get('features', {})
        print("Key Features:", {k: v for k, v in feats.items() if k in ['trend_alignment', 'relative_volume', 'confluence_score', 'session_killzone_active', 'spread_to_sl_ratio']})
        print(f"AI Probability: {eval_data.get('probability')}, Net Expectancy: {eval_data.get('net_expectancy_r')}")
    
    # Check trade_audit_snapshots if any
    snaps = cur.execute("SELECT source, bot_profile, visual_context_json, entry_view_json FROM trade_audit_snapshots WHERE broker_position_ticket = ?", (row['broker_position_ticket'],)).fetchall()
    if snaps:
        print(f"Snapshots found: {len(snaps)}")
        for s in snaps:
            print(f"  Source: {s['source']} | Profile: {s['bot_profile']}")
            if s['visual_context_json']:
                try:
                    vc = json.loads(s['visual_context_json'])
                    print(f"  Visual Context: {vc.get('setup_type')} | Reason: {vc.get('reason')} | Confluence: {vc.get('confluence')}")
                except:
                    pass

