"""ORB diagnostics and immutable per-confirmation comparisons, never orders."""
import json
import os
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'storage/runtime/orb_audit'
_LOCK = threading.Lock()
_MEM_STATE = {}
_LAST_WRITE = {}
_DIRTY_DAYS = set()


def record(result, root=None):
    audit = result.get('orb_audit')
    if not audit or result.get('strategy_name') != 'ORB_NEW_YORK':
        return
    root = Path(root or ROOT)
    with _LOCK:
        day = str(audit['range_start'])[:10]
        state_key = (str(root), day)
        state = _MEM_STATE.get(state_key)
        if state is None:
            target = root / (day + '.json')
            try:
                state = json.loads(target.read_text(encoding='utf-8'))
            except (OSError, ValueError):
                state = {'day': day, 'latest': {}, 'candidates': {}}
            _MEM_STATE[state_key] = state

        state['updated_at'] = audit['evaluated_at']
        state['latest'][audit['symbol']] = {**audit, 'action': result.get('action'), 'reason': result.get('reason')}
        momentum = audit.get('momentum') or {}
        if momentum.get('evaluated'):
            key = '|'.join([audit['symbol'], str(momentum['confirmation_time']), str(momentum['direction'])])
            state['candidates'].setdefault(key, audit)

        # Throttle I/O a disco en Windows
        flush_sec = float(os.getenv("DAEMONBLACKFX_ORB_AUDIT_FLUSH_SECONDS", "5.0"))
        now_mono = time.monotonic()
        last_w = _LAST_WRITE.get(state_key, 0.0)
        action = str(result.get('action') or '')
        is_critical = bool(action in {'ORDER_OPENED', 'SPLIT_ORDER_OPENED', 'DRY_RUN_VALIDATED'} or action.startswith('ERROR'))

        if flush_sec > 0.0 and not is_critical and (now_mono - last_w) < flush_sec:
            _DIRTY_DAYS.add(state_key)
            return

        _write_state_to_disk(root, day, state)
        _LAST_WRITE[state_key] = now_mono
        _DIRTY_DAYS.discard(state_key)


def _write_state_to_disk(root, day, state):
    try:
        root.mkdir(parents=True, exist_ok=True)
        target = root / (day + '.json')
        temp = root / (day + '.' + str(os.getpid()) + '.tmp')
        temp.write_text(json.dumps(state, ensure_ascii=False, default=str), encoding='utf-8')
        temp.replace(target)
    except OSError:
        pass


def flush(root=None):
    """Vuelca estados en memoria pendientes a disco."""
    with _LOCK:
        for state_key in list(_DIRTY_DAYS):
            r_str, day = state_key
            r = Path(r_str)
            state = _MEM_STATE.get(state_key)
            if state:
                _write_state_to_disk(r, day, state)
                _LAST_WRITE[state_key] = time.monotonic()
        _DIRTY_DAYS.clear()


def snapshot(root=None):
    try:
        flush(root)
    except Exception:
        pass
    paths = sorted(Path(root or ROOT).glob('*.json'))
    if not paths:
        return {}
    try:
        return json.loads(paths[-1].read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return {'error': 'ORB_AUDIT_UNAVAILABLE'}
