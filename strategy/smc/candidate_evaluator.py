"""Single adaptive decision entry point shared by the production confirmation engine."""
from strategy.smc.h1_adaptive_context import evaluate_h1_adaptive_context
from strategy.smc.m5_freshness import validate_m5_signal_freshness, evaluate_m5_confirmation_detailed
from strategy.smc.adaptive_score import calculate_adaptive_score


def evaluate_h1_context(h1_range, current_price, signal_type):
    side = str(signal_type).upper()
    context = evaluate_h1_adaptive_context(None, current_price, h1_range)
    valid = bool(side in {'BUY','SELL'} and context['is_valid_location'] and context['direction']==side)
    if h1_range and h1_range.get('adaptive_context_enabled') is False and context['context_type'].startswith('EXPANSION'):
        valid = False
    reason = context['reason']
    if not valid and context['is_valid_location']:
        reason = 'H1: Direccion o ubicacion incompatible con ' + context['context_type']
    elif not valid:
        reason = 'H1: ' + reason
    return dict(context, valid=valid, is_valid_location=valid, context=context['context_type'],
                score_bonus=(15 if context.get('source')=='FALLBACK_24H' else 25) if valid else 0,
                reason=reason)


def validate_m5_latency(choch_time, max_allowed_minutes=10, current_time=None):
    result = validate_m5_signal_freshness(choch_time,max_allowed_minutes,current_time)
    return dict(result, fresh=result['is_fresh'], elapsed=result['elapsed_minutes'])


def evaluate_m5_details(m5_data, max_age_minutes=10, current_time=None):
    result = evaluate_m5_confirmation_detailed(m5_data,current_time,max_age_minutes)
    return dict(result, score=result['m5_score'], vetos=result['veto_reasons'], tag=result['diagnostic_tag'])


def evaluate_m5_details_v2(m5_data, max_age_minutes=10, current_time=None):
    return evaluate_m5_details(m5_data, max_age_minutes, current_time)


def evaluate_m5_details_v3(m5_data, max_age_minutes=10, current_time=None):
    return evaluate_m5_details(m5_data, max_age_minutes, current_time)


def evaluate_candidate_signal(signal_type, current_price, h1_raw, m15_raw, m5_raw,
                              confluences=None, current_time=None, max_age_minutes=10, m1_raw=None):
    """Default clock is real UTC; historical callers must supply evaluation time.

    Keeps 85/70 modes and optional confluences from the existing score contract.
    Returned approval is strategy approval, not authorization to bypass execution guards.
    """
    h1_eval = evaluate_h1_context(h1_raw,current_price,signal_type)
    m5_input = dict(m5_raw, freshness_required=True, max_age_minutes=max_age_minutes)
    if current_time is not None:
        m5_input['evaluation_time'] = current_time
    result = calculate_adaptive_score(h1_eval,m15_raw,m5_input,confluences or {}, m1_data=m1_raw)
    if not h1_eval['valid']:
        result['reasons'] = [h1_eval['reason'] if reason.startswith('H1:') else reason
                             for reason in result['reasons']]
    return dict(result, h1_context=h1_eval, m15_evidence=dict(m15_raw),
                signal_type=str(signal_type).upper(), current_price=current_price,
                evaluator_version=('H1_REGIME_DUAL_M5_M1_V4' if m1_raw is not None or m5_raw.get('dual_trigger_enabled')
                                   else 'H1_REGIME_M5_FRESHNESS_V1'))


from strategy.smc.dual_trigger import (evaluate_dual_m5_m1_trigger,
    evaluate_m5_m1_trigger, validate_signal_latency)


def evaluate_candidate_signal_v4(signal_type, current_price, h1_raw, m15_raw,
                                  m5_raw, m1_raw=None, confluences=None,
                                  current_time=None, max_age_minutes=10):
    return evaluate_candidate_signal(signal_type, current_price, h1_raw, m15_raw,
        dict(m5_raw, dual_trigger_enabled=True), confluences, current_time,
        max_age_minutes, m1_raw=m1_raw)
