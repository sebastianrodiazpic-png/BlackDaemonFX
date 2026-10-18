"""Finalize the current offline replay when all expected checkpoints are present."""
from pathlib import Path
import json, subprocess, sys, time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools.replay_msnr_two_year_comparison import OUT,read_manifest

def main():
    expected=set(read_manifest()['requested_symbols'])
    while True:
        finished=set()
        for path in (OUT/'results').glob('*.json'):
            if path.name.endswith('.superseded.json'):
                continue
            try:
                finished.add(json.loads(path.read_text())['symbol'])
            except (OSError,ValueError):
                continue
        if expected<=finished:
            break
        time.sleep(10)
    subprocess.run([sys.executable,str(ROOT/'tools/summarize_msnr_two_year_comparison.py')],cwd=ROOT,check=True)

if __name__=='__main__':
    main()
