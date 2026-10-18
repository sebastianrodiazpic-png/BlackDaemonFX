"""Conditional entry refinements sharing the original H1 execution episode."""
from copy import copy
from dataclasses import replace


def analyze_variants(context, symbol, now):
    if now is None:
        import pandas as pd
        now = pd.Timestamp.now(tz='UTC')
    primary = context._analyze_symbol_impl(symbol, now)
    readings = [primary]
    contexts = [context]
    if context.config.m5_confirmation_mode != 'off':
        refined = copy(context)
        refined.config = replace(context.config, entry_timeframe='M5')
        contexts.append(refined)
        value = refined._analyze_symbol_impl(symbol, now)
        if value.get('valid'):
            value['shadow_only'] = bool(value.get('shadow_only') or context.config.m5_confirmation_mode=='shadow')
            value['signal']['execution_mode'] = 'SHADOW' if value['shadow_only'] else 'LIVE'
        readings.append(value)
    if context.config.h4_neutral_fallback_mode == 'shadow':
        for original, baseline in zip(contexts, list(readings)):
            if not baseline.get('h4_neutral_fallback_eligible'):
                continue
            fallback = copy(original)
            fallback.config = replace(original.config, h4_neutral_fallback_mode='live')
            value = fallback._analyze_symbol_impl(symbol, now)
            if value.get('valid') and value['signal'].get('h4_neutral_fallback_used'):
                value['shadow_only'] = True
                value['signal']['execution_mode'] = 'SHADOW'
                readings.append(value)
    # Observe wick-based confirmations in a separate interpretation. A shadow
    # pinbar must never consume the primary visit or hide a later regular close.
    if context.config.retest_pinbar_mode == 'shadow':
        for original in list(contexts):
            pinbar_context = copy(original)
            pinbar_context.config = replace(original.config, retest_pinbar_mode='live')
            value = pinbar_context._analyze_symbol_impl(symbol, now)
            pinbars = [candidate for candidate in
                ([value] if value.get('valid') else []) + value.get('shadow_candidates', [])
                if candidate.get('signal', {}).get('retest_evidence', {}).get('pinbar_only')]
            for candidate in pinbars:
                candidate['shadow_only'] = True
                candidate['signal']['execution_mode'] = 'SHADOW'
                candidate['signal']['pinbar_observation'] = True
                candidate['shadow_candidates'] = []
                readings.append(candidate)
    candidates = []
    seen = set()
    for reading in readings:
        for candidate in ([reading] if reading.get('valid') else []) + reading.get('shadow_candidates', []):
            sig = candidate.get('signal') or {}
            identity = (sig.get('setup_id'), sig.get('entry_timeframe', 'M15'),
                        bool(sig.get('h4_neutral_fallback_used')), bool(candidate.get('shadow_only')),
                        bool(sig.get('retest_evidence', {}).get('pinbar_only')))
            if identity in seen:
                continue
            seen.add(identity)
            candidate = dict(candidate)
            candidate.pop('shadow_candidates', None)
            candidates.append(candidate)
    selected = next((r for r in candidates if not r.get('shadow_only')),
                    candidates[0] if candidates else primary)
    selected = dict(selected)
    selected['shadow_candidates'] = [r for r in candidates if r is not selected and r.get('shadow_only')
        and r.get('signal') is not selected.get('signal')]
    selected['variant_diagnostics'] = [
        {'entry_timeframe': c.config.entry_timeframe, 'reason': r.get('reason'),
         'history_diagnostics': r.get('history_diagnostics')} for c,r in zip(contexts,readings)]
    return selected
