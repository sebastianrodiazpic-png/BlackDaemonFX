import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pandas as pd, json, sqlite3
from tools.prospective_m1_replay_runner import ProspectiveM1ReplayRunner

db_path = Path('storage/runtime/shadow_research_staging.sqlite3')
arch_dir = Path('storage/runtime/m1_prospective_cache')
runner = ProspectiveM1ReplayRunner(db_path=db_path, dry_run=True, archive_dir=arch_dir)
runner.fetch_market_data(['Boom 500 Index'])
bars = runner.cache_m1['Boom 500 Index']

conn = sqlite3.connect(f'file:{db_path.resolve()}?mode=ro', uri=True)
row = pd.read_sql_query('SELECT * FROM shadow_signals WHERE id = 5', conn).iloc[0]
conn.close()

sig_t = pd.to_datetime(row['timestamp'], utc=True)
cre_t = pd.to_datetime(json.loads(row['features_json'])['created_at_live'], utc=True)
ep = row['entry_price']; sl = row['stop_loss']; tp1 = row['take_profit_1']; tp2 = row['take_profit_2']
print(f'ID 5 | Sig: {sig_t} | Cre: {cre_t} | EP={ep}, SL={sl}, TP1={tp1}, TP2={tp2}')

fut_sig = bars[bars['time'] >= sig_t].copy().reset_index(drop=True)
print(f'Total bars after sig_t: {len(fut_sig)}')

# Let us check when SL or TP1 was hit from sig_t
hit_sl_at = None
hit_tp1_at = None
for idx, b in fut_sig.iterrows():
    if b['low'] <= sl and hit_sl_at is None:
        hit_sl_at = (idx, b['time'], b['low'])
    if b['high'] >= tp1 and hit_tp1_at is None:
        hit_tp1_at = (idx, b['time'], b['high'])

print(f'From sig_t: hit_sl_at = {hit_sl_at}')
print(f'From sig_t: hit_tp1_at = {hit_tp1_at}')

fut_cre = bars[bars['time'] >= cre_t].copy().reset_index(drop=True)
hit_sl_at_cre = None
hit_tp1_at_cre = None
for idx, b in fut_cre.iterrows():
    if b['low'] <= sl and hit_sl_at_cre is None:
        hit_sl_at_cre = (idx, b['time'], b['low'])
    if b['high'] >= tp1 and hit_tp1_at_cre is None:
        hit_tp1_at_cre = (idx, b['time'], b['high'])

print(f'From cre_t: hit_sl_at = {hit_sl_at_cre}')
print(f'From cre_t: hit_tp1_at = {hit_tp1_at_cre}')
