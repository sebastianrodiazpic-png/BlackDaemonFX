import sys, os
sys.path.insert(0, os.path.abspath('.'))
import pandas as pd, json, sqlite3
from marketdata.factory import build_market_data_provider
from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy

db = os.path.expanduser('~') + r'\AppData\Local\BlackDaemonFx\trading_bot.sqlite3'
con = sqlite3.connect(db)
pref = con.execute('SELECT settings_json, id FROM strategy_runtime_preferences WHERE strategy_name="MALAYSIAN_SNR" ORDER BY id DESC LIMIT 1').fetchone()
settings = json.loads(pref[0])
settings['version'] = pref[1]
print('Live version in DB:', settings.get('version'))
print('Crash 500 mode:', settings.get('asset_modes', {}).get('Crash 500 Index'))
print('Wall Street 30 mode:', settings.get('asset_modes', {}).get('Wall Street 30'))
print('Volatility 25 mode:', settings.get('asset_modes', {}).get('Volatility 25 Index'))

p = build_market_data_provider('MT5')
strat = MalaysianSNRStrategy(p, runtime_settings_loader=lambda: settings)
now = pd.Timestamp.now(tz='UTC')

for s in ['Crash 500 Index', 'Wall Street 30', 'EURUSD', 'Step Index']:
    res = strat.analyze_symbol(s, now)
    stage = res.get('diagnostics', {}).get('stage') or res.get('reason')
    print(f"{s} -> valid: {res.get('valid')}, shadow_only: {res.get('shadow_only')}, stage/reason: {stage}")
