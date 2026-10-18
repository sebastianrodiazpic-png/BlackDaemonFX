"""Small runtime helpers shared by standalone and multi-profile MSNR workers."""
from datetime import datetime, timezone
from .universe import canonical_symbol, symbol_mode


def cycle_symbols(engine, selected):
    settings = engine.malaysian_snr_strategy.settings_snapshot()
    symbols = list(dict.fromkeys(selected))
    if settings['additional_symbols_mode'] != 'off':
        symbols = list(dict.fromkeys([*symbols, *settings['additional_symbols']]))
    symbols = list(dict.fromkeys([*symbols,
        *[name for name,mode in settings.get('asset_modes', {}).items() if mode!='off']]))
    symbols = [symbol for symbol in symbols
               if settings.get('asset_modes', {}).get(canonical_symbol(symbol))!='off']
    if settings['prioritize_pending_retests']:
        pending = getattr(engine, '_msnr_pending_retests', {})
        now = datetime.now(timezone.utc).timestamp()
        symbols.sort(key=lambda symbol: (0 if pending.get(symbol,0)>now else 1,
                                        pending.get(symbol,float('inf')) if pending.get(symbol,0)>now else 0))
    base = getattr(getattr(engine.malaysian_snr_strategy, 'config', None), 'allowed_symbols', ()) or selected
    # Preserve the pending-retest order within each tier; observational assets
    # must not take precedence over executable opportunities.
    symbols.sort(key=lambda symbol: 1 if symbol_mode(settings, symbol, base)=='shadow' else 0)
    return symbols


def track_pending(engine, symbol, analysis):
    pending = getattr(engine, '_msnr_pending_retests', None)
    if pending is None:
        pending = engine._msnr_pending_retests = {}
    details = analysis.get('diagnostics') or {}
    reasons = {'WAITING_FIRST_RETEST','WAITING_POST_BREAK_RETEST','WAITING_RETEST_RECOVERY','RETEST_WEAK_RECOVERY'}
    try:
        expiry = datetime.fromisoformat(details['expires_at'].replace('Z','+00:00')).timestamp()
        if analysis.get('reason') in reasons and expiry>datetime.now(timezone.utc).timestamp():
            pending[symbol] = expiry
            return
    except (KeyError,ValueError,TypeError):
        pass
    pending.pop(symbol,None)


def observation_result(symbol, analysis):
    shadow = bool(analysis.get('shadow_only'))
    return {'symbol':symbol, 'strategy_name':'MALAYSIAN_SNR', 'valid':False,
            'action':'MSNR_SHADOW_SIGNAL' if shadow else analysis.get('action','WAITING_MALAYSIAN_SNR'),
            'reason':'MSNR_OBSERVATION_ONLY' if shadow else analysis.get('reason'),
            'shadow_only':shadow, 'analysis':analysis}
