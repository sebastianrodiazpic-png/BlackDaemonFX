"""Closed logical setups and pre-entry variant evidence; no model promotion."""
from collections import defaultdict
import math
import pandas as pd
from strategy.ai.training import _row_metadata, _profiles_match, externally_closed


def closed_comparison(records, worker):
    groups = defaultdict(list)
    for row in records:
        meta = _row_metadata(row)
        if not _profiles_match(worker, meta.get('bot_profile')):
            continue
        identity = meta.get('parent_execution_key') or row.get('execution_key') or ('trade:' + str(row.get('id')))
        groups[(row.get('source'), identity)].append(row)
    report = {'unit':'LOGICAL_SETUP', 'mode':'OBSERVED_COHORTS_ONLY', 'promotion_allowed':False,
              'manual_exit_setups':0, 'manual_exit_net_pnl':0.0, 'closed_setups':0, 'pending_setups':0, 'target_review_pending':0, 'by_version':{}, 'missing_outcome':0, 'missing_variant_capture':0,
              'cohorts':{}, 'counterfactual_status':'REQUIRES_CLOSED_REPLAY_FOR_UNEXECUTED_CANDIDATES'}
    values = defaultdict(list)
    for legs in groups.values():
        if any((_row_metadata(r).get('target_reconciliation') or {}).get('requires_review') for r in legs):
            report['target_review_pending'] += 1
            continue
        if any(str(r.get('status')).upper() != 'CLOSED' for r in legs):
            report['pending_setups'] += 1
            continue
        if any(externally_closed(r) for r in legs):
            report['manual_exit_setups'] += 1
            for row in legs:
                try:
                    pnl = float(row.get('net_pnl'))
                    if math.isfinite(pnl):
                        report['manual_exit_net_pnl'] += pnl
                except (TypeError, ValueError):
                    pass
            continue
        try:
            risks = [float((_row_metadata(r).get('post_fill_risk') or {}).get('actual_risk_amount') or r['risk_amount']) for r in legs]
            pnls = [float(r['net_pnl']) for r in legs]
            if not all(math.isfinite(x) for x in risks+pnls) or min(risks) <= 0:
                raise ValueError('invalid outcome')
            rr = sum(pnls) / sum(risks)
        except (ValueError, TypeError, KeyError):
            report['missing_outcome'] += 1
            continue
        report['closed_setups'] += 1
        first = min(legs, key=lambda r: str(r.get('entry_time') or ''))
        strategy = _row_metadata(first).get('strategy_name') or 'SMC'
        values[strategy + ':BASELINE_EXECUTED'].append(rr)
        version = first.get('strategy_version') or (_row_metadata(first).get('entry_learning_snapshot') or {}).get('strategy_version') or 'UNVERSIONED'
        version_key = strategy + ':' + str(version)
        cohort = report['by_version'].setdefault(version_key, {'closed_setups':0, 'sum_net_r':0.0})
        cohort['closed_setups'] += 1
        cohort['sum_net_r'] += rr
        capture = _row_metadata(first).get('entry_learning_snapshot') or {}
        comparison = capture.get('setup_sequence_shadow') or {}
        if not comparison.get('variants'):
            report['missing_variant_capture'] += 1
            continue
        try:
            captured_at = pd.to_datetime(capture.get('captured_at'), utc=True)
            entry_at = pd.to_datetime(first.get('entry_time'), utc=True)
            confirmed_at = pd.to_datetime(comparison.get('confirmation_time'), utc=True) + pd.Timedelta(minutes=5)
            if pd.isna(captured_at) or pd.isna(confirmed_at) or pd.isna(entry_at) or captured_at>entry_at or confirmed_at>captured_at:
                raise ValueError('noncausal capture')
        except (ValueError,TypeError):
            report['missing_variant_capture'] += 1
            continue
        for name, evidence in comparison['variants'].items():
            # Observed subset only, not a claim about trades never executed.
            if evidence.get('remaining_critical_failures') == [] and evidence.get('ob_respected') is True:
                values[strategy + ':' + name].append(rr)
    for name, rr in values.items():
        report['cohorts'][name] = {'closed_setups':len(rr), 'wins':sum(x>0 for x in rr),
            'losses':sum(x<0 for x in rr), 'mean_net_r':sum(rr)/len(rr),
            'sum_net_r':sum(rr), 'note':'Subconjunto observado; no demuestra mejora contrafactual'}
    return report
