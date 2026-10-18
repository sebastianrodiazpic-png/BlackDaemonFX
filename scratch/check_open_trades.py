import sqlite3
import json

conn = sqlite3.connect(r'C:\Users\sebas\AppData\Local\BlackDaemonFx\trading_bot.sqlite3')
cur = conn.cursor()
cols = [c[1] for c in cur.execute('PRAGMA table_info(trades)').fetchall()]
print('Trades cols:', cols)
open_trades = cur.execute("SELECT * FROM trades WHERE status='OPEN'").fetchall()
print(f'Total OPEN trades: {len(open_trades)}')
for ot in open_trades:
    row_dict = dict(zip(cols, ot))
    details = json.loads(row_dict.get('details_json') or '{}')
    meta = details.get('metadata', {})
    print(f"ID={row_dict.get('id')} Ticket={row_dict.get('broker_position_ticket')} Symbol={row_dict.get('instrument')} Dir={row_dict.get('direction')} Entry={row_dict.get('entry_price')} SL={row_dict.get('stop_loss')} TP={row_dict.get('take_profit')} PlannedRR={row_dict.get('planned_rr')}")
    print(f"   -> Leg={meta.get('trade_leg')} | BE_Trigger={meta.get('break_even_trigger_rr')} | RunnerInitial={meta.get('runner_initial_target_rr')} | RunnerMax={meta.get('runner_max_target_rr')} | RunnerExtEnabled={meta.get('runner_extension_enabled')}")
