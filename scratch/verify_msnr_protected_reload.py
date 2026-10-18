"""Read-only exposure/persistence checks for a supervised worker reload."""
import json
import math
import os
from pathlib import Path
import sqlite3
import MetaTrader5 as mt5

if not mt5.initialize():raise SystemExit('Broker verification unavailable')
try:
    positions=mt5.positions_get();orders=mt5.orders_get()
    if positions is None or orders is None:raise SystemExit('Exposure verification failed')
    owned=[p for p in positions if p.magic==26082031]
    if any(o.magic==26082031 for o in orders):raise SystemExit('Pending orders: defer reload')
    path=Path(os.environ['LOCALAPPDATA'])/'BlackDaemonFx/trading_bot.sqlite3'
    with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as connection:
        connection.row_factory=sqlite3.Row
        journal=[dict(row) for row in connection.execute("SELECT id,source,instrument,status,broker_position_ticket,external_ticket FROM trade_journal WHERE source='DEMO' AND status='OPEN'")]
    evidence=[]
    for position in owned:
        sign=1 if position.type==0 else -1
        if (not all(math.isfinite(v) and v>0 for v in (position.sl,position.tp,position.price_open,position.price_current))
                or sign*(position.price_current-position.sl)<=0
                or sign*(position.tp-position.price_current)<=0):
            raise SystemExit('A position lacks verified broker protection; defer reload')
        matches=[row for row in journal if str(position.ticket) in (str(row['broker_position_ticket']),str(row['external_ticket']))]
        if not matches:raise SystemExit('A position is not persisted; defer reload')
        evidence.append({'ticket':position.ticket,'symbol':position.symbol,'sl':position.sl,'tp':position.tp,
            'journal_ids':[row['id'] for row in matches]})
    print(json.dumps({'safe_for_reload':True,'protected_positions':evidence,'pending_orders':0,
        'recovery_path':'persistent journal + broker positions; broker SL/TP remains active'}))
finally:mt5.shutdown()
