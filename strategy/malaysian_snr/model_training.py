"""Reproducible canonical SNR training with purged chronological partitions."""
import hashlib
import json
import math
import numpy as np
import pandas as pd
from datetime import datetime, timezone

from strategy.ai.feature_extraction import FEATURE_NAMES, FEATURE_SCHEMA, feature_vector
from strategy.ai.model import CalibratedLogisticModel, LogisticRegressionModel, ProbabilityCalibrator
from .ai_policy import capture_features, FEATURE_SEMANTICS, OBJECTIVE_SCHEMA, settings_signature


def train_captures(records, settings, *, strategy_version, min_samples=120):
    rows, seen = [], set()
    for record in records:
        capture = record.get('capture') or record
        result = record.get('outcome') or {}
        if not result.get('eligible_for_training') or result.get('net_r') is None:
            continue
        signal, market = capture.get('signal',{}), capture.get('market',{})
        if signal.get('strategy_version') != strategy_version:
            continue
        if settings_signature(record.get('settings') or settings) != settings_signature(settings):
            continue
        if not signal.get('setup_id') or market.get('spread_source') != 'MT5_EXECUTION':
            continue
        key = (signal['symbol'],signal['setup_id'])
        if key in seen:
            continue
        seen.add(key)
        features = capture_features(signal,capture.get('analysis') or {},market)
        # Captured enrichments are immutable and carry the canonical semantics.
        decision = capture.get('decision') or {}
        if decision.get('feature_semantics') == FEATURE_SEMANTICS and decision.get('features'):
            features = decision['features']
        entry = pd.to_datetime(signal['confirmation_closed_at'],utc=True)
        exit_time = pd.to_datetime(result['closed_at'],utc=True)
        net_r = float(result['net_r'])
        if not math.isfinite(net_r) or exit_time <= entry:
            continue
        vector = feature_vector(features)
        if not all(math.isfinite(v) for v in vector):
            continue
        rows.append(dict(entry=entry,exit=exit_time,features=vector,label=int(net_r>0),rr=net_r,key=key))
    rows.sort(key=lambda r:r['entry'])
    if len(rows)<min_samples:
        raise ValueError(f'INSUFFICIENT_VERIFIED_CANONICAL_CAPTURES:{len(rows)}/{min_samples}')
    cal_start, test_start = rows[int(len(rows)*.6)]['entry'], rows[int(len(rows)*.8)]['entry']
    train = [r for r in rows if r['entry']<cal_start and r['exit']<cal_start]
    cal = [r for r in rows if cal_start<=r['entry']<test_start and r['exit']<test_start]
    test = [r for r in rows if r['entry']>=test_start]
    if any(len(part)<10 or len({r['label'] for r in part})<2 for part in (train,cal,test)):
        raise ValueError('INSUFFICIENT_PURGED_PARTITIONS_OR_CLASSES')
    model = CalibratedLogisticModel(worker='MALAYSIAN_SNR',strategy_name='MALAYSIAN_SNR')
    x = lambda part:np.array([r['features'] for r in part],dtype=float)
    y = lambda part:np.array([r['label'] for r in part],dtype=int)
    model.model = LogisticRegressionModel().fit(x(train),y(train))
    model.calibrator = ProbabilityCalibrator().fit(model.model.predict_proba(x(cal)),y(cal))
    probabilities = np.array([model.probability(r['features']) for r in test])
    targets = y(test)
    clipped = np.clip(probabilities,1e-9,1-1e-9)
    wins = [r['rr'] for r in train if r['rr']>0]
    losses = [-r['rr'] for r in train if r['rr']<=0]
    model.average_win_rr = float(np.mean(wins))
    model.average_loss_rr = float(np.mean(losses))
    model.trained_at = datetime.now(timezone.utc).isoformat()
    threshold = settings['ai_min_probability']
    accepted = probabilities>=threshold
    metrics = {'test_samples':len(test),'train_samples':len(train),'calibration_samples':len(cal),
        'purged_samples':len(rows)-len(train)-len(cal)-len(test),
        'base_win_rate':float(targets.mean()),
        'brier_score':float(np.mean((probabilities-targets)**2)),
        'log_loss':float(-np.mean(targets*np.log(clipped)+(1-targets)*np.log(1-clipped))),
        'selected_samples':int(accepted.sum()),
        'selected_win_rate':float(targets[accepted].mean()) if accepted.any() else None,
        'selected_expectancy_r':float(np.array([r['rr'] for r in test])[accepted].mean()) if accepted.any() else None,
        'promotion_allowed':False}
    reliability = []
    for low in np.arange(0,1,.1):
        mask = (probabilities>=low)&(probabilities<low+.1 if low<.9 else probabilities<=1)
        reliability.append({'lower':float(low),'samples':int(mask.sum()),
            'predicted':float(probabilities[mask].mean()) if mask.any() else None,
            'observed':float(targets[mask].mean()) if mask.any() else None})
    metrics['reliability'] = reliability
    digest = hashlib.sha256(json.dumps(rows,sort_keys=True,default=str).encode()).hexdigest()
    model.provenance = {'feature_semantics':FEATURE_SEMANTICS,'feature_schema':FEATURE_SCHEMA,
        'objective_schema':OBJECTIVE_SCHEMA,'strategy_version':strategy_version,
        'settings_signature':settings_signature(settings),'data_sha256':digest,
        'independent_test_verified':True,'split':'chronological_60_20_20_exit_purged',
        'windows':{name:{'first':part[0]['entry'].isoformat(),'last':part[-1]['entry'].isoformat()}
                   for name,part in [('train',train),('calibration',cal),('test',test)]},
        'metrics':metrics}
    return model,metrics
