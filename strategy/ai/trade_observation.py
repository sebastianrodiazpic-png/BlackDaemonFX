"""Read-only MT5 observation; provenance and isolated learning outcomes."""
from datetime import datetime, timezone
import math
import pandas as pd
from strategy.ai.feature_extraction import extract_meta_features, FEATURE_NAMES


def observe(provider, trade):
    now = datetime.now(timezone.utc)
    tick = provider.get_current_tick(trade['instrument'])
    direction = str(trade['direction']).upper()
    price = float(tick['bid'] if direction == 'BUY' else tick['ask'])
    spread = float(tick['ask']) - float(tick['bid'])
    data = provider.get_candles(trade['instrument'], 'M5', count=40).copy()
    data['time'] = pd.to_datetime(data['time'], utc=True)
    data = data[data.time + pd.Timedelta(minutes=5) <= pd.Timestamp(now)].sort_values('time')
    if data.empty or (pd.Timestamp(now) - data.time.iloc[-1]).total_seconds() > 600:
        raise ValueError('OBSERVATION_M5_UNAVAILABLE_OR_STALE')
    if not math.isfinite(price) or price <= 0 or spread < 0:
        raise ValueError('OBSERVATION_INVALID_QUOTE')
    prev = data.close.shift(1)
    atr = pd.concat([data.high-data.low, (data.high-prev).abs(), (data.low-prev).abs()], axis=1).max(axis=1).tail(14).mean()
    sl = float(trade.get('stop_loss') or 0)
    risk = price-sl if direction == 'BUY' else sl-price
    view = {'strategy_name':'MT5_OBSERVATION', 'evidence_type':'FIRST_OBSERVATION',
            'evaluated_at':now.isoformat(), 'direction':direction, 'observed_price':price,
            'original_entry_time':str(trade.get('entry_time')), 'original_entry_price':trade.get('entry_price'),
            'stop_loss':trade.get('stop_loss'), 'take_profit':trade.get('take_profit'),
            'm5_last_closed_time':data.time.iloc[-1].isoformat(), 'atr':float(atr),
            'range_high':float(data.high.max()), 'range_low':float(data.low.min()),
            'risk_distance':risk if sl > 0 and risk > 0 else None,
            'learning_scope':'PRICE_FROM_OBSERVATION_TO_EXIT', 'management_allowed':False}
    view['candles'] = [{**{k:float(r[k]) for k in ('open','high','low','close')},'time':r['time'].isoformat()} for _,r in data.iterrows()]
    view['features'] = extract_meta_features(signal={'direction':direction, 'atr':float(atr)},
            market={'entry_price':price,'spread':spread}, evaluated_at=now.isoformat())
    view['feature_names'] = list(FEATURE_NAMES)
    return view


def capture_observation(metadata, view):
    """Keep first evidence immutable and freeze one later risk-valid observation."""
    import copy
    changed = False
    if not metadata.get('mt5_observation'):
        metadata['mt5_observation'] = copy.deepcopy(view)
        changed = True
    first = metadata['mt5_observation']
    risk = view.get('risk_distance')
    if (not first.get('risk_distance') and not metadata.get('mt5_risk_observation')
            and isinstance(risk, (int, float)) and math.isfinite(risk) and risk > 0
            and view.get('features')
            and pd.Timestamp(view['evaluated_at']) >= pd.Timestamp(first['evaluated_at'])):
        later = copy.deepcopy(view)
        later['evidence_type'] = 'FIRST_VALID_RISK_OBSERVATION'
        metadata['mt5_risk_observation'] = later
        changed = True
    return changed


def selected_observation(metadata):
    return metadata.get('mt5_risk_observation') or metadata.get('mt5_observation') or {}


def learning_rows(records):
    """Project observations into their own dataset; never rewrite original fills."""
    from strategy.ai.training import _row_metadata
    result=[]
    for row in records:
        meta = _row_metadata(row)
        observation = selected_observation(meta)
        if not observation:
            result.append(row)
            continue
        risk = observation.get('risk_distance')
        if not risk or not observation.get('features'):
            result.append(row)
            continue
        projected = dict(row)
        metadata = {'strategy_name':'MT5_OBSERVATION', 'bot_profile':'EXTERNAL',
            'target_reconciliation':meta.get('target_reconciliation'),
            'entry_learning_snapshot': {'schema':'observation-v1', 'features':observation['features'],
                                       'feature_names':observation['feature_names']}}
        projected['details'] = {'metadata':metadata}
        projected['entry_time'] = observation['evaluated_at']
        projected['realized_rr'] = None
        projected['net_pnl'] = None
        try:
            if str(row.get('status')).upper() == 'CLOSED':
                sign = 1 if observation['direction']=='BUY' else -1
                projected['realized_rr'] = sign*(float(row['exit_price'])-observation['observed_price'])/risk
        except (TypeError,ValueError,KeyError): pass
        result.append(projected)
    return result


def eligibility(row, records=None):
    from strategy.ai.training import _row_metadata, build_training_dataset, externally_closed
    meta = _row_metadata(row)
    evidence = 'ENTRY_CAPTURE' if meta.get('entry_learning_snapshot') else 'FIRST_OBSERVATION' if meta.get('mt5_observation') else 'NO_ENTRY_EVIDENCE'
    observation = selected_observation(meta)
    if observation and not meta.get('entry_learning_snapshot'):
        evidence = observation.get('evidence_type') or 'FIRST_OBSERVATION'
    parent=meta.get('parent_execution_key')
    siblings=[r for r in (records or []) if _row_metadata(r).get('parent_execution_key')==parent] if parent else []
    if any((_row_metadata(r).get('target_reconciliation') or {}).get('requires_review') for r in siblings):
        return {'trade_id':row.get('id'),'symbol':row.get('instrument'),'evidence_type':evidence,'reason':'SL_TP_PENDIENTE_RECONCILIACION'}
    if parent and any(str(r.get('status')).upper()=='OPEN' for r in siblings):
        return {'trade_id':row.get('id'),'symbol':row.get('instrument'),'evidence_type':evidence,'reason':'ESPERANDO_CIERRE_DEL_SETUP'}
    if not observation and (externally_closed(row) or any(externally_closed(r) for r in siblings)):
        return {'trade_id':row.get('id'),'symbol':row.get('instrument'),'evidence_type':evidence,'reason':'CIERRE_MANUAL_EXCLUIDO_DEL_MODELO_DE_ESTRATEGIA'}
    if (meta.get('target_reconciliation') or {}).get('requires_review'): reason = 'SL_TP_PENDIENTE_RECONCILIACION'
    elif evidence == 'NO_ENTRY_EVIDENCE': reason = 'SIN_CONTEXTO_DE_ENTRADA_NI_OBSERVACION'
    elif str(row.get('status')).upper() != 'CLOSED': reason = 'ESPERANDO_CIERRE'
    elif (meta.get('entry_learning_snapshot') or observation).get('feature_names') != list(FEATURE_NAMES): reason = 'ESQUEMA_DE_FEATURES_ANTIGUO_REQUIERE_MIGRACION'
    elif build_training_dataset(learning_rows([row]))['rows']: reason = 'ELEGIBLE_OBSERVACION' if observation and not meta.get('entry_learning_snapshot') else 'ELEGIBLE_ENTRADA'
    else: reason = 'EVIDENCIA_INCOMPLETA_O_RESULTADO_NO_ETIQUETABLE'
    if parent and records is None and reason=='ELEGIBLE_ENTRADA': reason='VALIDAR_CIERRE_COMPLETO_DEL_SETUP'
    return {'trade_id':row.get('source_trade_id') or row.get('id'), 'symbol':row.get('instrument'), 'evidence_type':evidence, 'reason':reason}
