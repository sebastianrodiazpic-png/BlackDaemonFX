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
row = pd.read_sql_query('SELECT * FROM shadow_signals WHERE id = 17', conn).iloc[0]
conn.close()

sig_t = pd.to_datetime(row['timestamp'], utc=True)
cre_t = pd.to_datetime(json.loads(row['features_json'])['created_at_live'], utc=True)
ep = row['entry_price']; sl = row['stop_loss']; tp1 = row['take_profit_1']; tp2 = row['take_profit_2']
print(f'ID 17 | Sig: {sig_t} | Cre: {cre_t} | EP={ep}, SL={sl}, TP1={tp1}, TP2={tp2}')

sub_bars = bars[(bars['time'] >= sig_t) & (bars['time'] <= pd.to_datetime('2026-10-15 19:20:00+00:00', utc=True))]
for _, b in sub_bars.iterrows():
    is_cre = " <-- CREATED_AT" if b['time'] == pd.to_datetime('2026-10-15 19:09:00+00:00', utc=True) else ""
    hit_sl = " [TOUCHED SL!]" if b['low'] <= sl else ""
    hit_tp1 = " [TOUCHED TP1!]" if b['high'] >= tp1 else ""
    hit_tp2 = " [TOUCHED TP2!]" if b['high'] >= tp2 else ""
    print(f"  {b['time']} | O={b['open']:.3f} H={b['high']:.3f} L={b['low']:.3f} C={b['close']:.3f}{hit_sl}{hit_tp1}{hit_tp2}{is_cre}")
