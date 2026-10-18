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

# 1. Modo IA en FILTER estricto
settings['ai_mode'] = 'filter'
settings['ai_min_probability'] = 0.55
settings['ai_min_probability_forex'] = 0.60
settings['ai_min_probability_gold'] = 0.60
settings['ai_min_probability_volatility'] = 0.52
settings['ai_min_net_expectancy_r'] = 0.10

# 2. Poda de activos tóxicos (desactivados a 'off')
toxic_symbols = [
    'Crash 300 Index',  # WR 27.5%, -$142k en replay, -$71 hoy
    'USDCAD',            # Perdedor estructural en M15, -$79 hoy
    'AUDNZD',            # Negativo en replay
    'EURCHF',            # Spread tóxico / baja volatilidad
    'AUDCHF',            # Negativo en replay
    'CADCHF',            # Negativo en replay
    'EURGBP',            # Whipsaw constante en M15
    'US Oil',            # Gaps / rollover adverso
    'Volatility 25 Index',
    'Volatility 50 Index',
    'Volatility 75 Index',
    'Volatility 100 Index',
    'Volatility 75 (1s) Index',
    'Volatility 250 (1s) Index',
    'USDCHF',
    'AUDUSD',
    'AUDCAD',
    'EURJPY',
    'EURNZD',
    'GBPCHF',
    'GBPNZD'
]

asset_modes = settings.get('asset_modes', {})
continuation_modes = settings.get('continuation_symbol_modes', {})

for sym in toxic_symbols:
    asset_modes[sym] = 'off'
    continuation_modes[sym] = 'off'

# 3. Confirmar activos ganadores núcleo en 'live'
core_winning_symbols = [
    'Jump 50 Index',
    'Jump 10 Index',
    'Jump 25 Index',
    'Step Index',
    'Step Index 200',
    'Step Index 400',
    'Step Index 500',  # Protegido ahora por Cooldown 60m + 2 Strikes
    'Volatility 10 Index',
    'Volatility 50 (1s) Index',
    'Boom 1000 Index',
    'Boom 600 Index',
    'Boom 500 Index',
    'Boom 300 Index',
    'Crash 1000 Index',
    'Crash 600 Index',
    'Crash 500 Index',
    'EURUSD',
    'GBPUSD',
    'USDJPY',
    'GBPJPY',
    'BTCUSD',
    'XAUUSD',
    'US Tech 100',
    'Wall Street 30'
]

for sym in core_winning_symbols:
    asset_modes[sym] = 'live'
    continuation_modes[sym] = 'live'

settings['asset_modes'] = asset_modes
settings['continuation_symbol_modes'] = continuation_modes

new_id = current_id + 1
now_str = datetime.now(timezone.utc).isoformat()
c.execute('''
    INSERT INTO strategy_runtime_preferences (id, source, strategy_name, settings_json, updated_at)
    VALUES (?, 'DEMO', 'MALAYSIAN_SNR', ?, ?)
''', (new_id, json.dumps(settings), now_str))
conn.commit()

print(f"SUCCESS: Inserted strategy_runtime_preferences version/id {new_id}")
print(f"ai_mode: {settings.get('ai_mode')}")
print(f"Crash 300 Index mode: {asset_modes.get('Crash 300 Index')}")
print(f"USDCAD mode: {asset_modes.get('USDCAD')}")
print(f"Step Index 500 mode: {asset_modes.get('Step Index 500')}")
print(f"Active Live Assets Count: {sum(1 for v in asset_modes.values() if v == 'live')}")
print(f"Active Off Assets Count: {sum(1 for v in asset_modes.values() if v == 'off')}")
