"""SNR research catalogue. Membership alone never enables execution."""
FAMILIES = {
    'synthetics': (
        'Step Index', 'Step Index 200', 'Step Index 400', 'Step Index 500',
        'Jump 10 Index', 'Jump 25 Index', 'Jump 50 Index', 'Jump 75 Index', 'Jump 100 Index',
        'Volatility 10 Index', 'Volatility 15 Index', 'Volatility 25 Index',
        'Volatility 50 Index', 'Volatility 75 Index', 'Volatility 100 Index',
        'Volatility 50 (1s) Index', 'Volatility 75 (1s) Index',
        'Volatility 90 Index', 'Volatility 250 (1s) Index',
        'Boom 300 Index', 'Boom 500 Index', 'Boom 600 Index', 'Boom 900 Index', 'Boom 1000 Index',
        'Crash 300 Index', 'Crash 500 Index', 'Crash 600 Index', 'Crash 900 Index', 'Crash 1000 Index'),
    'forex': ('EURUSD', 'GBPUSD', 'USDJPY', 'USDCAD', 'USDCHF', 'AUDUSD',
        'AUDCAD', 'AUDCHF', 'AUDJPY', 'AUDNZD', 'CADCHF', 'CADJPY', 'CHFJPY',
        'EURAUD', 'EURCAD', 'EURCHF', 'EURGBP', 'EURJPY', 'EURNZD',
        'GBPAUD', 'GBPCAD', 'GBPCHF', 'GBPJPY', 'GBPNZD'),
    'crypto': ('BTCUSD',),
    'metals': ('XAUUSD', 'XAGUSD'),
    'indices': ('US SP 500', 'US Tech 100', 'Wall Street 30'),
    'commodities': ('US Oil',),
}
CATALOG_SYMBOLS = tuple(symbol for group in FAMILIES.values() for symbol in group)
RECOVERY_SYMBOLS = ('Crash 500 Index', 'Step Index 500', 'Volatility 10 Index',
    'Volatility 25 Index', 'Volatility 75 Index', 'Boom 500 Index', 'Boom 600 Index', 'BTCUSD')


def canonical_symbol(symbol):
    return str(symbol).strip().removesuffix('micro')


def symbol_mode(settings, symbol, base_symbols=()):
    name = canonical_symbol(symbol)
    override = settings.get('asset_modes', {}).get(name)
    if override is not None:
        return override
    if name in {canonical_symbol(s) for s in base_symbols}:
        return 'live'
    if name in settings.get('additional_symbols', ()):
        return settings['additional_symbols_mode']
    return 'off'


def resolve_symbol_settings(settings, symbol):
    resolved = dict(settings)
    resolved['step_min_adx']=settings.get('step_symbol_min_adx',{}).get(canonical_symbol(symbol),settings.get('step_min_adx',25.))
    for setting, mapping in (('m5_confirmation_mode', 'm5_symbol_modes'),
                             ('continuation_mode', 'continuation_symbol_modes')):
        resolved[setting] = settings.get(mapping, {}).get(canonical_symbol(symbol), settings[setting])
    return resolved


def catalogue(base_symbols):
    return [{'symbol': symbol, 'family': family, 'base_mode': 'live' if symbol in base_symbols else 'off'}
            for family, group in FAMILIES.items() for symbol in group]
