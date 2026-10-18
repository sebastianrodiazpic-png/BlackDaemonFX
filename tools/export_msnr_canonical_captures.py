"""Export immutable candidate captures with verified executed two-leg net results."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from database.repository import TradingRepository


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',default='DEMO',choices=['DEMO','REAL'])
    parser.add_argument('--output',default='storage/analysis/msnr_canonical_captures.jsonl')
    parser.add_argument('--db-path')
    args=parser.parse_args()
    repo=TradingRepository(args.db_path)
    rows=repo.msnr_candidates(source=args.source,limit=1000)
    records=[]
    for row in rows:
        capture=row['capture']
        outcome=repo.msnr_closed_execution_result(capture.get('execution_key'),source=args.source)
        if outcome:
            records.append({'candidate_key':row['candidate_key'],'capture':capture,
                            'settings':row['settings'],'outcome':outcome})
    path=Path(args.output);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(''.join(json.dumps(r,default=str,ensure_ascii=False)+'\n' for r in records),encoding='utf-8')
    print(json.dumps({'confirmed_candidates':len(rows),'verified_net_captures':len(records),
                      'output':str(path.resolve()),'active_model_changed':False}))


if __name__=='__main__':
    main()
