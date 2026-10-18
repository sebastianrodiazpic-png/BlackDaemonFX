"""Candidate ledger separate from executed trades and the permanent journal."""
import json
import hashlib
from datetime import datetime, timezone, timedelta
from sqlalchemy import text


DDL = [
    '''CREATE TABLE IF NOT EXISTS msnr_candidates (
        candidate_key TEXT PRIMARY KEY, episode_key TEXT NOT NULL, source TEXT NOT NULL,
        symbol TEXT NOT NULL, strategy_version TEXT NOT NULL, settings_hash TEXT NOT NULL,
        setup_id TEXT NOT NULL, variant TEXT NOT NULL, first_seen TEXT NOT NULL,
        last_seen TEXT NOT NULL, first_reason TEXT, last_reason TEXT, state TEXT,
        evaluations INTEGER NOT NULL DEFAULT 1, capture_json TEXT, settings_json TEXT,
        confirmed_at TEXT, executed INTEGER NOT NULL DEFAULT 0)''',
    'CREATE INDEX IF NOT EXISTS ix_msnr_candidate_lookup ON msnr_candidates(source,last_seen,symbol)',
    '''CREATE TABLE IF NOT EXISTS msnr_candidate_transitions (
        id INTEGER PRIMARY KEY, candidate_key TEXT NOT NULL, observed_at TEXT NOT NULL,
        state TEXT, reason TEXT, details_json TEXT)''',
    'CREATE INDEX IF NOT EXISTS ix_msnr_transition_lookup ON msnr_candidate_transitions(candidate_key,id)',
    '''CREATE TABLE IF NOT EXISTS msnr_candidate_outcomes (
        candidate_key TEXT PRIMARY KEY, observed_at TEXT NOT NULL, outcome TEXT NOT NULL,
        result_json TEXT NOT NULL, evidence_type TEXT NOT NULL DEFAULT 'OBSERVATION')''',
    '''CREATE TABLE IF NOT EXISTS msnr_model_registry (
        artifact_hash TEXT PRIMARY KEY, registered_at TEXT NOT NULL,
        path TEXT NOT NULL, provenance_json TEXT NOT NULL)''',
]


def ensure(repo):
    if getattr(repo, '_msnr_audit_schema_ready', False):
        return
    with repo.Session() as session:
        for command in DDL:
            session.execute(text(command))
        session.commit()
    repo._msnr_audit_schema_ready = True


def save_candidate(repo, *, source, symbol, version, settings, setup_id, variant,
                   state, reason, capture=None, confirmed_at=None, now=None):
    ensure(repo)
    from strategy.malaysian_snr.ai_policy import settings_signature
    signature = settings_signature(settings)
    episode = hashlib.sha256(json.dumps([source,symbol,version,signature,setup_id]).encode()).hexdigest()
    key = hashlib.sha256((episode+'|'+variant).encode()).hexdigest()
    observed = now or datetime.now(timezone.utc).isoformat()
    data = dict(candidate_key=key, episode_key=episode, source=source, symbol=symbol,
        strategy_version=version, settings_hash=signature, setup_id=setup_id, variant=variant,
        first_seen=observed, last_seen=observed, first_reason=reason, last_reason=reason,
        state=state, capture_json=json.dumps(capture,default=str) if capture else None,
        settings_json=json.dumps(settings,default=str), confirmed_at=confirmed_at,
        executed=int(state in ('ORDER_OPENED','SPLIT_ORDER_OPENED')))
    with repo.Session() as session:
        # The upsert preserves the previous last state until the transition
        # check; SQLite serializes writers within this transaction.
        session.execute(text('INSERT INTO msnr_candidates ('+','.join(data)+') VALUES ('+
            ','.join(':'+k for k in data)+''') ON CONFLICT(candidate_key) DO UPDATE SET
            last_seen=excluded.last_seen, evaluations=msnr_candidates.evaluations+1,
            capture_json=COALESCE(msnr_candidates.capture_json,excluded.capture_json),
            confirmed_at=COALESCE(msnr_candidates.confirmed_at,excluded.confirmed_at),
            executed=MAX(msnr_candidates.executed,excluded.executed)'''),data)
        old = session.execute(text('SELECT state,last_reason FROM msnr_candidates WHERE candidate_key=:key'),{'key':key}).first()
        if old != (state,reason) or session.execute(text(
                'SELECT 1 FROM msnr_candidate_transitions WHERE candidate_key=:key LIMIT 1'), {'key':key}).first() is None:
            session.execute(text('INSERT INTO msnr_candidate_transitions (candidate_key,observed_at,state,reason,details_json) '
                'VALUES (:key,:time,:state,:reason,:details)'),dict(key=key,time=observed,state=state,
                reason=reason,details=json.dumps((capture or {}).get('decision',{}),default=str)))
        session.execute(text('UPDATE msnr_candidates SET state=:state,last_reason=:reason WHERE candidate_key=:key'),
                        dict(key=key,state=state,reason=reason))
        session.commit()
    return key


def candidates(repo, *, source='DEMO', symbol=None, limit=100, pending=False):
    ensure(repo)
    where = 'c.source=:source AND c.confirmed_at IS NOT NULL'
    parameters = {'source':source, 'limit':min(1000,max(1,int(limit)))}
    if symbol:
        where += ' AND c.symbol=:symbol'
        parameters['symbol'] = symbol
    if pending:
        where += " AND (o.outcome IS NULL OR o.outcome IN ('PENDING','MISSING_HISTORY','MISSING_COSTS'))"
    with repo.Session() as session:
        rows = session.execute(text('SELECT c.* FROM msnr_candidates c LEFT JOIN msnr_candidate_outcomes o '
            'ON c.candidate_key=o.candidate_key WHERE '+where+' ORDER BY c.last_seen DESC LIMIT :limit'),parameters).mappings().all()
    return [{**dict(row),'capture':json.loads(row['capture_json'] or '{}'),
             'settings':json.loads(row['settings_json'] or '{}')} for row in rows]


def save_outcome(repo, candidate_key, result):
    ensure(repo)
    with repo.Session() as session:
        session.execute(text('''INSERT INTO msnr_candidate_outcomes
            (candidate_key,observed_at,outcome,result_json) VALUES (:key,:time,:outcome,:result)
            ON CONFLICT(candidate_key) DO UPDATE SET observed_at=excluded.observed_at,
            outcome=excluded.outcome,result_json=excluded.result_json'''),
            dict(key=candidate_key,time=datetime.now(timezone.utc).isoformat(),
                 outcome=result['outcome'],result=json.dumps(result,default=str)))
        session.commit()


def closed_execution_result(repo, parent_key, source='DEMO'):
    """Net result from two closed journal legs, with their actual monetary risk."""
    if not parent_key:
        return None
    import math
    with repo.Session() as session:
        rows = session.execute(text('''SELECT status,exit_time,risk_amount,net_pnl,details_json
            FROM trade_journal WHERE source=:source AND execution_key IN (:tp1,:runner)'''),
            dict(source=source,tp1=parent_key+':TP1',runner=parent_key+':RUNNER')).mappings().all()
    if len(rows)!=2 or any(r['status']!='CLOSED' or not r['exit_time'] for r in rows):
        return None
    risks = [float(r['risk_amount'] or 0) for r in rows]
    profits = [float(r['net_pnl']) for r in rows]
    if not all(math.isfinite(v) for v in risks+profits) or any(v<=0 for v in risks):
        return None
    from strategy.ai.training import externally_closed
    for row in rows:
        meta = json.loads(row['details_json'] or '{}')
        metadata = meta.get('metadata') or {}
        if (metadata.get('target_reconciliation') or {}).get('requires_review'):
            return None
        if externally_closed({'details':meta}):
            return None
    return {'outcome':'EXECUTED_CLOSED','evidence_type':'EXECUTED_JOURNAL_NET_TWO_LEGS',
            'eligible_for_training':True,'fees_verified':True,
            'net_r':sum(profits)/sum(risks),'closed_at':max(str(r['exit_time']) for r in rows)}


def funnel(repo, source='DEMO'):
    ensure(repo)
    cutoff = (datetime.now(timezone.utc)-timedelta(days=7)).isoformat()
    with repo.Session() as session:
        summary = session.execute(text('''SELECT COUNT(DISTINCT episode_key) AS unique_setups,
            COUNT(*) AS variants, COALESCE(SUM(evaluations),0) AS evaluations,
            COUNT(DISTINCT CASE WHEN confirmed_at IS NOT NULL THEN episode_key END) AS confirmed,
            COUNT(DISTINCT CASE WHEN executed=1 THEN episode_key END) AS executed
            FROM msnr_candidates WHERE source=:source AND last_seen>=:cutoff'''),
            dict(source=source,cutoff=cutoff)).mappings().one()
        outcomes = session.execute(text('''SELECT o.outcome,COUNT(*) AS count FROM msnr_candidate_outcomes o
            JOIN msnr_candidates c ON c.candidate_key=o.candidate_key
            WHERE c.source=:source AND c.last_seen>=:cutoff GROUP BY o.outcome'''),
            dict(source=source,cutoff=cutoff)).mappings().all()
        blockers = session.execute(text('''SELECT last_reason,COUNT(DISTINCT episode_key) AS count
            FROM msnr_candidates WHERE source=:source AND last_seen>=:cutoff AND executed=0
            GROUP BY last_reason ORDER BY count DESC LIMIT 10'''),dict(source=source,cutoff=cutoff)).mappings().all()
        first_blockers = session.execute(text('''SELECT first_reason AS reason,COUNT(DISTINCT episode_key) AS count
            FROM msnr_candidates WHERE source=:source AND last_seen>=:cutoff AND executed=0
            GROUP BY first_reason ORDER BY count DESC LIMIT 10'''),dict(source=source,cutoff=cutoff)).mappings().all()
        by_symbol = session.execute(text('''SELECT symbol,COUNT(DISTINCT episode_key) AS unique_setups,
            COUNT(DISTINCT CASE WHEN confirmed_at IS NOT NULL THEN episode_key END) AS confirmed,
            COUNT(DISTINCT CASE WHEN executed=1 THEN episode_key END) AS executed,
            MIN(first_seen) AS first_recorded_at FROM msnr_candidates
            WHERE source=:source AND last_seen>=:cutoff GROUP BY symbol ORDER BY symbol'''),
            dict(source=source,cutoff=cutoff)).mappings().all()
    return {**dict(summary), 'outcomes':[dict(r) for r in outcomes], 'blockers':[dict(r) for r in blockers],
            'first_blockers':[dict(r) for r in first_blockers], 'by_symbol':[dict(r) for r in by_symbol],
            'window_days':7, 'source':source, 'win_rate':None,
            'note':'Resultados de observacion separados de operaciones reales; no acreditan WinRate.'}


def register_model(repo, path, payload):
    ensure(repo)
    encoded = json.dumps(payload,sort_keys=True).encode()
    key = hashlib.sha256(encoded).hexdigest()
    with repo.Session() as session:
        session.execute(text('INSERT OR IGNORE INTO msnr_model_registry '
            '(artifact_hash,registered_at,path,provenance_json) VALUES (:key,:time,:path,:provenance)'),
            dict(key=key,time=datetime.now(timezone.utc).isoformat(),path=str(path),
                 provenance=json.dumps(payload.get('provenance',{}))))
        session.commit()
    return key
