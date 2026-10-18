"""SNR-specific AI contract. All other workers retain their existing policy."""
import hashlib
import json
import math
from dataclasses import replace

from strategy.ai.feature_extraction import extract_meta_features, FEATURE_SCHEMA, FEATURE_NAMES

FEATURE_SEMANTICS = 'msnr-confirmation-capture-v1'
OBJECTIVE_SCHEMA = 'msnr-net-dual-leg-v1'


def settings_signature(settings):
    # Operational controls and probability thresholds do not change setup geometry.
    excluded = {'version', 'updated_at', 'enable_candidate_audit', 'observe_candidate_outcomes',
        'candidate_outcome_hours', 'enable_setup_diagnostics', 'enable_structure_cache',
        'prioritize_pending_retests', 'analysis_outside_entry_lock', 'asset_modes',
        'm5_symbol_modes', 'continuation_symbol_modes', 'step_symbol_min_adx',
        'research_min_frequency_ratio', 'research_min_resolved_trades',
        'research_min_win_rate_improvement_pp',
        'additional_symbols', 'additional_symbols_mode'}
    values = {k:v for k,v in settings.items() if k not in excluded and not k.startswith('ai_')}
    return hashlib.sha256(json.dumps(values, sort_keys=True, separators=(',',':')).encode()).hexdigest()


def capture_features(signal, analysis, market):
    """Freeze training variables at confirmation; execution latency is separate metadata.

    Native replays must call this function with their real entry-time market
    snapshot. No scenario-specific guessed spread, pattern strength or fixed RR.
    """
    confirmed = signal.get('confirmation_closed_at') or signal.get('entry_time')
    if not confirmed:
        raise ValueError('MISSING_CONFIRMATION_CAPTURE_TIME')
    return extract_meta_features(signal=signal, analysis=analysis, market=market, evaluated_at=confirmed)


def compatibility(model, signal, settings):
    p = getattr(model, 'provenance', {}) or {}
    requirements = {'feature_semantics': FEATURE_SEMANTICS,
        'feature_schema': FEATURE_SCHEMA, 'objective_schema': OBJECTIVE_SCHEMA,
        'strategy_version': signal.get('strategy_version'),
        'settings_signature': settings_signature(settings)}
    problems = [key for key,value in requirements.items() if p.get(key) != value]
    if not model.trained:
        problems.append('untrained')
    if not model.calibrator.trained or not p.get('independent_test_verified'):
        problems.append('independent_calibration_and_test')
    feat_names = tuple(getattr(getattr(model, 'model', None), 'feature_names', getattr(model, 'feature_names', ())))
    if feat_names and feat_names != tuple(FEATURE_NAMES):
        problems.append('feature_names')
    weights = getattr(getattr(model, 'model', None), 'weights', None)
    if weights is not None:
        if any(len(values)!=len(FEATURE_NAMES) for values in
               (model.model.weights,model.model.mean,model.model.scale)):
            problems.append('model_dimensions')
        if any(value<=0 for value in model.model.scale):
            problems.append('model_scale')
        if not all(math.isfinite(v) for v in [*model.model.weights, model.model.bias,
                                             *model.model.mean, *model.model.scale]):
            problems.append('non_finite_model_parameters')
    return {'compatible': not problems, 'problems': problems, 'required': requirements,
            'provenance': p}


def active_model_status(settings, model_directory='storage/ai_models'):
    from pathlib import Path
    from .config import MalaysianSNRConfig
    from strategy.ai.model import CalibratedLogisticModel
    path = Path(model_directory)/'metalabel_MALAYSIAN_SNR_MALAYSIAN_SNR.json'
    try:
        raw_data = json.loads(path.read_text(encoding='utf-8'))
        from strategy.ai.gbdt_model import CalibratedGBDTModel
        if raw_data.get('model_type') == 'LIGHTGBM':
            model = CalibratedGBDTModel.from_dict(raw_data)
        else:
            model = CalibratedLogisticModel.from_dict(raw_data)
        check = compatibility(model,{'strategy_version':MalaysianSNRConfig().strategy_version},settings)
        return {'compatible':check['compatible'],'problems':check['problems'],'trained':model.trained,
                'message':'Modelo compatible.' if check['compatible'] else
                    'Modelo sin validacion compatible con estos ajustes. En Filtro + Bloquear candidato, la IA impide nuevas entradas. Observacion permite comparar sin su veto.'}
    except (OSError,ValueError,TypeError):
        return {'compatible':False,'trained':False,'problems':['model_unavailable'],
                'message':'Modelo compatible no disponible.'}


def score_candidate(engine, symbol, signal, analysis, market, *, source, settings):
    config = replace(engine.config, enabled=settings['ai_mode']!='off',
        mode='SHADOW' if settings['ai_mode']=='shadow' else 'FILTER',
        min_probability=settings['ai_min_probability'],
        min_probability_forex=settings['ai_min_probability_forex'],
        min_probability_gold=settings['ai_min_probability_gold'],
        min_probability_volatility=settings['ai_min_probability_volatility'],
        min_net_expectancy_r=settings['ai_min_net_expectancy_r'])
    # A lightweight view shares the locked model cache without mutating worker config.
    from copy import copy
    scorer = copy(engine)
    scorer.config = config
    model = scorer.load_model('MALAYSIAN_SNR')
    check = compatibility(model, signal, settings)
    # score_signal uses the same generic extractor; anchoring evaluated_at in the
    # analysis cannot override its clock, so its features are replaced canonically.
    frozen = capture_features(signal, analysis, market)
    from strategy.ai.feature_extraction import feature_vector
    from datetime import datetime, timezone
    readable = model.trained and not set(check['problems']).intersection(
        {'model_dimensions','model_scale','non_finite_model_parameters'})
    probability = model.probability(feature_vector(frozen)) if readable else 0.
    expectancy = model.net_expectancy_r(probability) if model.trained else 0.
    thresholds = {'min_probability': scorer.resolve_min_probability(symbol),
                  'min_net_expectancy_r': config.min_net_expectancy_r}
    live_features = extract_meta_features(signal=signal, analysis=analysis, market=market,
                                         evaluated_at=datetime.now(timezone.utc).isoformat())
    if settings['ai_mode']=='off':
        allowed, shadow, reason = True, True, 'MSNR_AI_DISABLED'
    elif settings['ai_mode']=='shadow':
        allowed, shadow, reason = True, True, 'MSNR_AI_OBSERVATION_ONLY'
    elif not check['compatible']:
        allowed = settings['ai_incompatible_policy']=='observe' and str(source).upper()=='DEMO'
        shadow, reason = True, 'MSNR_AI_INCOMPATIBLE_OBSERVATION_DEMO' if allowed else 'MSNR_AI_MODEL_INCOMPATIBLE'
    elif probability + 1e-9 < thresholds['min_probability']:
        allowed, shadow, reason = False, False, 'PROBABILITY_BELOW_THRESHOLD'
    elif expectancy + 1e-9 < thresholds['min_net_expectancy_r']:
        allowed, shadow, reason = False, False, 'NET_EXPECTANCY_BELOW_THRESHOLD'
    else:
        allowed, shadow, reason = True, False, 'PROBABILITY_AND_EXPECTANCY_ACCEPTED'
    return {'symbol':symbol, 'worker':engine.worker, 'strategy_name':'MALAYSIAN_SNR',
        'mode':settings['ai_mode'].upper(), 'probability':round(probability,6),
        'net_expectancy_r':round(expectancy,6), 'allowed':allowed, 'shadow':shadow,
        'reason':reason, 'trained':model.trained, 'features':frozen, 'thresholds':thresholds,
        'probability_status':'VALIDATED_COMPATIBLE' if check['compatible'] else 'UNVALIDATED_FOR_CURRENT_SETTINGS',
        'feature_semantics':FEATURE_SEMANTICS, 'objective_schema':OBJECTIVE_SCHEMA,
        'execution_latency_seconds':live_features.get('signal_open_age_seconds'),
        'model_compatibility':check, 'evaluated_at':datetime.now(timezone.utc).isoformat()}
