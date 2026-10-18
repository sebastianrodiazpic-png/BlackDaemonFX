"""Audit complete candidates and returned data errors without sending orders."""
import time
from datetime import datetime, timezone


def audit_result(engine, symbol, result):
    if not isinstance(result,dict):
        return
    analysis = result.get('analysis') or getattr(getattr(engine,'_msnr_audit_local',None),'analysis',None) or {}
    try:
        controls = analysis.get('runtime_controls') or engine.malaysian_snr_strategy.settings_snapshot()
        if not controls['enable_candidate_audit']:
            return
        repo = engine.repository
        reason = str(result.get('reason') or analysis.get('reason') or '')
        if reason.startswith(('PROVIDER_ERROR', 'INVALID_CANDLE_DATA')):
            result['returned_data_error'] = True
            engine._persist_audit_event('MSNR_DATA_ERROR',instrument=symbol,action='ERROR',reason=reason)
        if not callable(getattr(repo,'save_msnr_candidate',None)):
            return
        readings = [analysis,*analysis.get('shadow_candidates',[])]
        for reading in readings:
            signal = reading.get('signal') or {}
            diagnostics = reading.get('diagnostics') or {}
            setup = signal.get('setup_id') or diagnostics.get('setup_id')
            if not setup:
                continue
            decision = signal.get('meta_label') or (result.get('meta_label') if reading is analysis else None)
            capture = None
            if signal:
                market = dict((decision or {}).get('market_snapshot') or {})
                if not market:
                    market = {'planned_rr':signal.get('risk_reward_ratio'),
                        'risk_percent':float(engine.config.risk_percent),'entry_price':signal['entry_price']}
                    market.update(engine._meta_execution_spread(symbol))
                if not decision:
                    from .ai_policy import score_candidate
                    decision = score_candidate(engine.meta_labeling,symbol,signal,reading,market,
                        source=engine.config.source,settings=controls)
                capture = {'signal':dict(signal),'market':market,'decision':decision,
                    'observed_at':datetime.now(timezone.utc).isoformat(),
                    'execution_key':result.get('execution_key') if reading is analysis else None,
                    'break_even_offset_points':int(getattr(engine.config,'break_even_offset_points',2))}
            variant = (signal.get('entry_timeframe') or diagnostics.get('entry_timeframe') or 'M15')
            if signal.get('h4_neutral_fallback_used'):
                variant += '_H4_NEUTRAL'
            if signal.get('retest_evidence', {}).get('pinbar_only'):
                variant += '_PINBAR'
            state = result.get('action','WAITING') if reading is analysis else 'MSNR_SHADOW_SIGNAL'
            reason = result.get('reason') if reading is analysis else 'MSNR_OBSERVATION_ONLY'
            repo.save_msnr_candidate(source=engine.config.source,symbol=symbol,
                version=signal.get('strategy_version') or reading.get('strategy_version') or engine.malaysian_snr_strategy.config.strategy_version,
                settings=controls,setup_id=setup,variant=variant,state=state,reason=reason,
                capture=capture,confirmed_at=signal.get('confirmation_closed_at'))
        diagnostics = analysis.get('diagnostics') or {}
        selected = diagnostics.get('setup_id')
        for other in diagnostics.get('candidates',[]):
            if not other.get('setup_id') or other['setup_id']==selected:
                continue
            repo.save_msnr_candidate(source=engine.config.source,symbol=symbol,
                version=analysis.get('strategy_version') or engine.malaysian_snr_strategy.config.strategy_version,
                settings=controls,setup_id=other['setup_id'],variant='M15',state='WAITING',
                reason=other.get('reason'))
        if controls['observe_candidate_outcomes']:
            schedule = getattr(engine,'_msnr_outcome_next',{})
            if time.monotonic()>=schedule.get(symbol,0):
                schedule[symbol] = time.monotonic()+300
                engine._msnr_outcome_next = schedule
                schedule_outcomes(engine, symbol)
    except Exception as exc:
        # Visible diagnostics: an audit failure cannot authorize or duplicate an order.
        result['candidate_audit_error'] = str(exc)
        if callable(getattr(engine,'_persist_audit_event',None)):
            engine._persist_audit_event('MSNR_CANDIDATE_AUDIT_ERROR',instrument=symbol,
                                       action='ERROR',reason=str(exc))


def schedule_outcomes(engine, symbol):
    """Serialize broker observations in a daemon thread, outside entry cycles."""
    import queue
    import threading
    jobs = getattr(engine, '_msnr_outcome_jobs', None)
    if jobs is None:
        jobs = engine._msnr_outcome_jobs = queue.Queue(maxsize=64)
        def run():
            from .candidate_outcomes import refresh
            while True:
                asset = jobs.get()
                try:
                    refresh(engine.repository,engine.provider,asset,engine.config.source)
                except Exception as exc:
                    engine._persist_audit_event('MSNR_OUTCOME_AUDIT_ERROR',instrument=asset,
                                               action='ERROR',reason=str(exc))
                finally:
                    jobs.task_done()
        thread = threading.Thread(target=run,name='msnr-candidate-outcomes',daemon=True)
        engine._msnr_outcome_thread = thread
        thread.start()
    try:
        jobs.put_nowait(symbol)
    except queue.Full:
        engine._persist_audit_event('MSNR_OUTCOME_QUEUE_FULL',instrument=symbol,
                                   action='ERROR',reason='Observaciones pendientes: cola completa')
