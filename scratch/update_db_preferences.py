import sqlite3
import os
import json
from datetime import datetime, timezone

db_path = os.path.expanduser('~') + r'\AppData\Local\BlackDaemonFx\trading_bot.sqlite3'
conn = sqlite3.connect(db_path)
c = conn.cursor()

row = c.execute('SELECT id, settings_json FROM strategy_runtime_preferences WHERE strategy_name="MALAYSIAN_SNR" ORDER BY id DESC LIMIT 1').fetchone()
current_id = row[0]
settings = json.loads(row[1])

# Apply new direct trigger and ensure all winning assets are live
settings['continuation_direct_trigger'] = True
settings['continuation_mode'] = 'live'
settings['continuation_fresh_only'] = False
settings['retest_window_minutes'] = 240
settings['recovery_window_minutes'] = 60
settings['recovery_min_body_ratio'] = 0.25
settings['breaker_pair_mode'] = 'live'
settings['retest_pinbar_mode'] = 'live'
settings['session_policy'] = 'market_hours'

# Winning assets in live
for s in ['Crash 500 Index', 'Step Index 500', 'Crash 600 Index', 'Wall Street 30', 'BTCUSD', 'XAUUSD',
          'Boom 1000 Index', 'Boom 500 Index', 'Boom 600 Index', 'Boom 300 Index', 'Crash 1000 Index',
          'Step Index', 'Step Index 400', 'Volatility 50 (1s) Index', 'Volatility 75 (1s) Index',
          'Volatility 10 Index', 'EURUSD', 'GBPUSD', 'USDJPY', 'GBPJPY', 'AUDNZD']:
    settings['asset_modes'][s] = 'live'
    settings['continuation_symbol_modes'][s] = 'live'

# Losing assets in shadow
for s in ['Volatility 25 Index', 'Volatility 75 Index', 'Step Index 200', 'USDCAD', 'CADCHF', 'CHFJPY']:
    settings['asset_modes'][s] = 'shadow'

new_id = current_id + 1
now_str = datetime.now(timezone.utc).isoformat()
c.execute('''
INSERT INTO strategy_runtime_preferences (id, source, strategy_name, settings_json, updated_at)
VALUES (?, 'DEMO', 'MALAYSIAN_SNR', ?, ?)
''', (new_id, json.dumps(settings), now_str))
conn.commit()
print(f"SUCCESS: Inserted strategy_runtime_preferences version/id {new_id}")
print(f"Continuation direct trigger: {settings.get('continuation_direct_trigger')}")
print(f"Crash 500 mode: {settings['asset_modes'].get('Crash 500 Index')}")
