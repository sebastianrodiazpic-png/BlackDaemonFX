"""Offline candidate learning: no live-model promotion or order side effects."""
from collections import Counter
import hashlib
import json
import os
import re
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd
from strategy.ai.training import _row_metadata, build_training_dataset, _logical_setup_records, _safe_float
from strategy.ai.meta_labeling import MetaLabelingEngine, MetaLabelingConfig

ROOT = Path(__file__).resolve().parents[2] / "storage/learning_audit"


def refresh(trades, worker, source, min_samples=30, root=None):
    root=Path(root or ROOT)
    root.mkdir(parents=True,exist_ok=True)
    if str(source).upper() == "MT5_EXTERNAL":
        worker = "EXTERNAL"
    records=trades.to_dict("records") if isinstance(trades,pd.DataFrame) else list(trades)
    if str(source).upper() == "MT5_EXTERNAL":
        records = [{**r, 'details': {'metadata': {
            **_row_metadata(r), 'bot_profile': 'EXTERNAL'}}} for r in records]
    from strategy.ai.trade_observation import learning_rows, eligibility
    learning_records = learning_rows(records)
    captured=[r for r in learning_records if _row_metadata(r).get("entry_learning_snapshot")]
    # Do not lose an open sibling when filtering incomplete entry evidence.
    incomplete={_row_metadata(r).get("parent_execution_key") for r in learning_records
                if not _row_metadata(r).get("entry_learning_snapshot")}
    captured=[r for r in captured if not _row_metadata(r).get("parent_execution_key")
              or _row_metadata(r).get("parent_execution_key") not in incomplete]
    name=re.sub(r"[^A-Za-z0-9_-]","_",str(source)+"_"+str(worker))
    path=root/(name+".json")
    try: previous=json.loads(path.read_text(encoding="utf-8"))
    except (OSError,ValueError): previous={}

    report={"worker":worker,"source":source,"updated_at":datetime.now(timezone.utc).isoformat(),
            "account_trades":len(records),"with_entry_snapshot":sum(bool(_row_metadata(r).get("entry_learning_snapshot")) for r in records),
            "with_observation":sum(bool(_row_metadata(r).get("mt5_observation")) for r in records),
            "without_entry_snapshot":sum(not bool(_row_metadata(r).get("entry_learning_snapshot")) for r in records),"mode":"CANDIDATE_ONLY", "strategies":{}}
    from strategy.ai.feature_extraction import FEATURE_SCHEMA
    from strategy.ai.closed_comparison import closed_comparison
    from strategy.ai.training import _profiles_match
    exact = [r for r in records if str(_row_metadata(r).get('bot_profile') or '').upper() == str(worker).upper()]
    family = [r for r in records if _profiles_match(worker, _row_metadata(r).get('bot_profile'))]
    def scope_counts(items):
        groups = {}
        for index, row in enumerate(items):
            meta = _row_metadata(row)
            key = (row.get('source'), meta.get('parent_execution_key') or row.get('execution_key') or ('trade:'+str(row.get('id', index))))
            groups.setdefault(key, []).append(row)
        return {'execution_rows':len(items), 'logical_setups':len(groups),
                'closed_setups':sum(all(str(r.get('status')).upper() == 'CLOSED' for r in legs) for legs in groups.values()),
                'entry_captures':sum(bool(_row_metadata(r).get('entry_learning_snapshot')) for r in items),
                'eligibility_reasons_by_execution':dict(Counter(eligibility(r, records).get('reason', 'UNKNOWN') for r in items))}
    report['scopes'] = {'account':scope_counts(records), 'family':scope_counts(family), 'worker':scope_counts(exact)}
    report['training_scope'] = 'FAMILY'
    report['comparison_scope'] = 'FAMILY'
    report['feature_schema'] = FEATURE_SCHEMA
    report["closed_comparison"] = closed_comparison(records, worker)
    report["trade_eligibility"]=[eligibility(r, records) for r in family[-100:]]
    report["instruments"]={}
    for row in _logical_setup_records(records):
        item=report["instruments"].setdefault(str(row.get("instrument") or "UNKNOWN"),
            {"closed_setups":0,"wins":0,"losses":0,"net_pnl":0.0})
        if str(row.get("status")).upper() != "CLOSED": continue
        pnl=_safe_float(row.get("net_pnl"))
        item["closed_setups"]+=1
        if pnl is not None:
            item["net_pnl"]+=pnl
            item["wins"]+=int(pnl>0)
            item["losses"]+=int(pnl<0)
    for strategy in sorted({str(_row_metadata(r).get("strategy_name") or "SMC") for r in captured}):
        dataset=build_training_dataset(captured,worker=worker,strategy_name=strategy)
        eligible=int(dataset["rows"])
        summary={"eligible_closed_setups":eligible,"minimum":min_samples,"trained":False,
                 "reason":"INSUFFICIENT_CLOSED_SETUPS_OR_CLASSES"}
        fingerprint=hashlib.sha256(json.dumps({k:dataset[k] for k in ("features","labels","rr","times","exit_times")},sort_keys=True,default=str).encode()).hexdigest()
        old=previous.get("strategies",{}).get(strategy,{})
        if old.get("fingerprint")==fingerprint and old.get("trained"):
            summary.update(old)
        elif eligible>=min_samples and len(set(dataset["labels"]))==2:
            engine=MetaLabelingEngine(MetaLabelingConfig(mode="SHADOW",min_training_samples=min_samples,
                model_directory=str(root / "candidate_models" / re.sub(r"[^A-Za-z0-9_-]","_",str(source)))),worker=worker)
            summary.update(engine.train(captured,strategy_name=strategy))
        summary["fingerprint"]=fingerprint
        report["strategies"][strategy]=summary
    report['training_funnel'] = {
        'eligible_closed_setups_family':sum(v.get('eligible_closed_setups', 0) for v in report['strategies'].values()),
        'candidate_models_trained':sum(bool(v.get('trained')) for v in report['strategies'].values()),
        'promotion_allowed':False,
        'schema_migration_policy':'REQUIRES_ORIGINAL_CAUSAL_EVIDENCE_NO_IMPUTED_FEATURES',
    }
    name=re.sub(r"[^A-Za-z0-9_-]","_",str(source)+"_"+str(worker))
    path=root/(name+".json");tmp=root/(name+"."+str(os.getpid())+".tmp")
    tmp.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8");tmp.replace(path)
    return report


def snapshot(root=None):
    reports=[]
    for path in Path(root or ROOT).glob("*.json"):
        try:
            item = json.loads(path.read_text(encoding="utf-8"))
            stamp = pd.to_datetime(item.get("updated_at"), utc=True, errors="coerce")
            item["stale"] = bool(pd.isna(stamp) or (pd.Timestamp.now(tz="UTC") - stamp).total_seconds() > 7200)
            from strategy.ai.feature_extraction import FEATURE_SCHEMA
            item["schema_current"] = item.get("feature_schema") == FEATURE_SCHEMA
            reports.append(item)
        except (OSError,ValueError):reports.append({"worker":path.stem,"error":"AUDIT_UNAVAILABLE"})
    if any(r.get("worker") == "EXTERNAL" and r.get("source") == "MT5_EXTERNAL" for r in reports):
        reports = [r for r in reports if r.get("source") != "MT5_EXTERNAL" or r.get("worker") == "EXTERNAL"]
    return reports
