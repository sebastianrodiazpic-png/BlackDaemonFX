"""Observation-only unique block and signal histories; no execution gates."""
from datetime import datetime, timedelta


def update_blocks(state, result, now):
    registry = state.setdefault('m15_blocks', {})
    changed = []
    symbol = result.get('symbol')
    current_ids = set()
    observations = {}
    for item in result.get('m15_block_audit') or []:
        identity = '|'.join(str(x) for x in (symbol, 'M15', item.get('ob_time'),
                             item.get('direction'), item.get('ob_low'), item.get('ob_high')))
        previous = observations.get(identity)
        if previous is None or str(item.get('setup_time')) >= str(previous.get('setup_time')):
            observations[identity] = item
    for identity, item in observations.items():
        current_ids.add(identity)
        block = registry.setdefault(identity, {'symbol':symbol, 'first_seen':now.isoformat(),
                                               'evaluations':0, 'timeline':[]})
        block['evaluations'] += 1
        block['last_seen'] = now.isoformat()
        # Formation time can vary across weak impulses; the OB origin is its identity.
        point = {'accepted':bool(item.get('accepted')), 'reasons':sorted(set(item.get('reasons') or [])),
                 'zone':item.get('zone')}
        if block.get('state') != point:
            block['state'] = point
            block['setup_time'] = item.get('setup_time')
            transition = dict(point, observed_at=now.isoformat())
            block['timeline'].append(transition)
            block['timeline'] = block['timeline'][-32:]
            changed.append(dict(item, block_id=identity, observed_at=now.isoformat()))
    result['m15_block_audit'] = changed
    result['m15_block_summary'] = {'unit':'UNIQUE_OB', 'unique_blocks_today':len(registry),
                                 'blocks_in_evaluation':len(current_ids), 'changes':len(changed)}


def update_signal(state, result, now):
    age = dict(result.get('signal_age') or {})
    stamp = age.get('signal_time')
    if not stamp:
        return
    identity = '|'.join(str(x) for x in (result.get('symbol'),result.get('direction'),stamp))
    signals = state.setdefault('signal_observations', {})
    first = identity not in signals
    item = signals.setdefault(identity, {'first_seen':now.isoformat(),
                'stale_at_first_seen':bool(age.get('is_stale')), 'evaluations':0})
    item['evaluations'] += 1
    item['last_seen'] = now.isoformat()
    age.update(first_seen=item['first_seen'], evaluations=item['evaluations'],
               observation_class=('FIRST_SEEN_STALE' if age.get('is_stale') else 'FIRST_SEEN_FRESH')
                                 if first else 'REPEATED_HISTORICAL_SIGNAL',
               stale_at_first_seen=item['stale_at_first_seen'])
    try:
        closed = datetime.fromisoformat(str(stamp).replace('Z','+00:00')) + timedelta(minutes=5)
        seen = datetime.fromisoformat(item['first_seen'])
        age.update(signal_closed_at=closed.isoformat(),
                   first_detection_delay_seconds=max(0., (seen-closed).total_seconds()))
    except (ValueError,TypeError):
        age['first_detection_delay_seconds'] = None
    # First seen is monitoring evidence, not proof of processing latency.
    stages = result.get('stage_timing') or {}
    age['stage_work_seconds'] = sum(float(v.get('data_fetch_seconds') or 0) + float(v.get('pipeline_seconds') or 0)
                                    for v in stages.values() if isinstance(v, dict))
    age['timing_scope'] = 'FIRST_OBSERVATION_IN_DAILY_AUDIT'
    result['signal_age'] = age
