import sqlite3
import json

conn = sqlite3.connect('storage/runtime/shadow_research_staging.sqlite3')
cur = conn.cursor()
cur.execute('''
    SELECT id, timestamp, strategy, variant, symbol, direction, entry_price, stop_loss, take_profit_1, take_profit_2, final_action, market_outcome, market_rr, features_json
    FROM shadow_signals
    ORDER BY timestamp ASC, id ASC
''')
rows = cur.fetchall()

events = {}
for r in rows:
    feat = json.loads(r[13]) if r[13] else {}
    ev_uuid = feat.get('event_uuid', f"{r[1]}_{r[2]}_{r[4]}_{r[5]}")
    if ev_uuid not in events:
        events[ev_uuid] = {
            'signal_time': r[1],
            'strategy': r[2],
            'symbol': r[4],
            'direction': r[5],
            'entry': r[6],
            'sl': r[7],
            'tp1': r[8],
            'tp2': r[9],
            'source_id': feat.get('source_signal_id'),
            'market_outcome': r[11],
            'market_rr': r[12],
            'variants': []
        }
    events[ev_uuid]['variants'].append({
        'variant': r[3],
        'action': r[10],
        'sim_outcome': feat.get('simulated_outcome'),
        'rejection_reason': feat.get('rejection_reason')
    })

print(f"Total Events found: {len(events)}")
for ev_id, ev in events.items():
    print(f"UUID: {ev_id} | Time: {ev['signal_time']} | Strat: {ev['strategy']} | Sym: {ev['symbol']} | Dir: {ev['direction']} | Entry: {ev['entry']} | SL: {ev['sl']} | TP1: {ev['tp1']} | SourceID: {ev['source_id']} | MktOutcome: {ev['market_outcome']} | MktRR: {ev['market_rr']}")
    for v in ev['variants']:
        print(f"    Variant: {v['variant']} -> Action: {v['action']}")
