"""Run the paired offline audit over every downloaded instrument, with checkpoints."""
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
from pathlib import Path
import json, sys, time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.replay_msnr_two_year_comparison import OUT,read_manifest,run_symbol,baseline_modules

def main():
    baseline_modules(OUT)
    expected=read_manifest()['requested_symbols']
    submitted=set()
    completed=set()
    pending={}
    started=time.monotonic()
    with ProcessPoolExecutor(max_workers=8) as pool:
        while len(completed)<len(expected):
            manifest=read_manifest()
            for row in manifest['symbols']:
                name=row['symbol']
                if name in submitted:
                    continue
                submitted.add(name)
                target=OUT/'results'/f'{name.replace(" ","_")}.json'
                if target.exists():
                    completed.add(name)
                    continue
                pending[pool.submit(run_symbol,row)]=name
            if pending:
                ready,_=wait(list(pending),timeout=10,return_when=FIRST_COMPLETED)
                for future in ready:
                    name=pending.pop(future)
                    try:
                        result=future.result()
                    except Exception as exc:
                        print(json.dumps({'symbol':name,'failure':repr(exc)}),flush=True)
                        raise
                    completed.add(name)
                    print(json.dumps(result,ensure_ascii=True),flush=True)
            else:
                time.sleep(10)
            progress={'completed':len(completed),'expected':len(expected),'downloaded':len(manifest['symbols']),
                      'queued':len(pending),'elapsed_minutes':round((time.monotonic()-started)/60,2)}
            temp=OUT/'replay_progress.json.tmp'
            temp.write_text(json.dumps(progress),encoding='utf-8')
            temp.replace(OUT/'replay_progress.json')
            print(json.dumps(progress),flush=True)
    print(json.dumps({'complete':True,'symbols':len(completed)}),flush=True)

if __name__=='__main__':
    main()
