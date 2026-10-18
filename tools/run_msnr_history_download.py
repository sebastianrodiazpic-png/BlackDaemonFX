"""Parallel isolated read-only MT5 sessions; all subprocess windows stay hidden."""
from pathlib import Path
import json, subprocess, sys, time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'storage/analysis/msnr_v21_two_years_20261011'
def main():
    processes = []
    logs = []
    for shard in range(8):
        log = (OUT / f'download_{shard}.log').open('w',encoding='utf-8')
        logs.append(log)
        processes.append(subprocess.Popen([sys.executable,str(ROOT/'tools/fetch_msnr_two_year_history.py'),'--shards','8','--shard',str(shard)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0)))
    while any(p.poll() is None for p in processes):
        counts = []
        for shard in range(8):
            path = OUT / f'history_manifest_shard_{shard}.json'
            try:
                counts.append(len(json.loads(path.read_text())['symbols']))
            except (OSError,ValueError):
                counts.append(0)
        print(json.dumps({'downloaded_symbols':sum(counts),'by_shard':counts,'running':sum(p.poll() is None for p in processes)}),flush=True)
        time.sleep(10)
    for log in logs:
        log.close()
    failed = [n for n,p in enumerate(processes) if p.returncode != 0]
    if failed:
        raise SystemExit(f'Download shards failed: {failed}; see download logs')
    manifests = [json.loads((OUT/f'history_manifest_shard_{n}.json').read_text()) for n in range(8)]
    merged = {**manifests[0],'symbols':sorted([row for m in manifests for row in m['symbols']],key=lambda r:r['symbol'])}
    merged.pop('shard',None)
    merged['snapshot_times'] = [m['snapshot_at'] for m in manifests]
    (OUT/'history_manifest.json').write_text(json.dumps(merged,indent=2),encoding='utf-8')
    print(json.dumps({'complete':True,'symbols':len(merged['symbols'])}),flush=True)

if __name__ == '__main__':
    main()
