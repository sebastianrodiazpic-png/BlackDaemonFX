"""Reconcile historical exit comments; audit-only, never sends broker commands."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from database.repository import TradingRepository
from reporting.target_audit import exit_target_evidence


def reconcile(repo, apply=False):
    changes=[]
    for source in ('DEMO','MT5_EXTERNAL'):
        for row in repo.trade_history_dataframe(source=source).to_dict('records'):
            if row.get('status') != 'CLOSED':
                continue
            details=row.get('details') or row.get('details_json') or {}
            if isinstance(details,str): details=json.loads(details)
            metadata=dict(details.get('metadata') or {})
            broker=metadata.get('broker_exit') or {}
            evidence=exit_target_evidence(row,broker.get('reason'),broker.get('comment'))
            if evidence['status']=='UNAVAILABLE' or metadata.get('target_reconciliation')==evidence:
                continue
            changes.append({'trade_id':row['id'],'instrument':row.get('instrument'),'evidence':evidence})
            if apply:
                metadata['target_reconciliation']=evidence
                repo.update_trade(int(row['id']),{'details':{**details,'metadata':metadata}})
                repo.save_audit_event('TRADE_TARGET_RECONCILIATION',source=source,
                    instrument=row.get('instrument'),execution_key=row.get('execution_key'),
                    action=evidence['status'],payload=changes[-1])
    return changes


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db',required=True)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    repo=TradingRepository(args.db)
    preview=reconcile(repo)
    if args.apply and preview:
        stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        backup=Path('storage/analysis')/('before_target_reconciliation_'+stamp+'.sqlite3')
        with sqlite3.connect('file:'+Path(args.db).resolve().as_posix()+'?mode=ro',uri=True) as src:
            with sqlite3.connect(backup) as dst: src.backup(dst)
        reconcile(repo,apply=True)
    print(json.dumps({'applied':args.apply,'changes':preview},ensure_ascii=False,default=str))
