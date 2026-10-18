"""Recheck only instruments with impossible initial stop quotes; archive prior ledgers."""
from concurrent.futures import ProcessPoolExecutor,as_completed
from pathlib import Path
import json,shutil,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.replay_msnr_two_year_comparison import OUT,run_symbol,read_manifest

def main():
    rows={r['symbol']:r for r in read_manifest()['symbols']}
    affected=[]
    archive=OUT/'results_before_initial_quote_guard'
    archive.mkdir(exist_ok=True)
    for path in (OUT/'results').glob('*.json'):
        if path.name.endswith('.superseded.json'):
            continue
        record=json.loads(path.read_text())
        if any(t['outcome']=='GAP_SL' and t['bars']==1 for v in record.get('versions',{}).values() for t in v['trades']):
            affected.append(rows[record['symbol']])
            shutil.copy2(path,archive/path.name)
    print(json.dumps({'affected_instruments':[r['symbol'] for r in affected]}),flush=True)
    with ProcessPoolExecutor(max_workers=8) as pool:
        jobs={pool.submit(run_symbol,row):row['symbol'] for row in affected}
        for future in as_completed(jobs):
            print(json.dumps(future.result()),flush=True)
    (OUT/'initial_quote_guard_audit.json').write_text(json.dumps({'affected_instruments':[r['symbol'] for r in affected],
        'rule':'BUY SL strictly below opening Bid; SELL SL strictly above opening Ask.',
        'source':'https://www.mql5.com/en/articles/2555',
        'other_instruments':'Their complete ledgers contained no first-bar GAP_SL. Their replay decisions are unaffected by this extra rejection guard.'},indent=2),encoding='utf-8')

if __name__=='__main__':
    main()
