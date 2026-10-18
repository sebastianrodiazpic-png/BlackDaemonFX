"""Parametros por defecto de la estrategia SMC.

Constantes puras, sin logica. Definen los tres marcos temporales del analisis,
la calidad exigida a un Order Block, el motor de confirmacion M5 y los limites
de riesgo base.

Jerarquia importante: estos son valores POR DEFECTO. El motor en vivo puede
recibir umbrales propios por instrumento o por perfil de bot, que prevalecen
sobre lo definido aqui.

Notas sobre las claves menos evidentes:
    - `maximum_touches`: un Order Block deja de ser fresco tras ser tocado; por
      eso solo se admite 1.
    - `confirmation_mode`: `inside`, `midpoint` o `break_ob`, de mas laxo a mas
      estricto respecto a donde debe reaccionar el precio dentro del bloque.
    - `max_confirmation_age_candles`: cuantas velas M5 puede tener la
      confirmacion para seguir siendo valida AL ABRIR. Es el origen de
      `STALE_M5_SIGNAL` y NO debe usarse para cerrar posiciones ya abiertas.
    - `displacement_range_multiplier`: cuanto debe superar el rango medio el
      impulso para considerarse desplazamiento real.

Vinculaciones:
    - `app.main` lo importa y lo propaga a la estrategia.
    - Los consumidores efectivos viven en `strategy.smc` y
      `strategy.execution.multi_timeframe`.
"""

STRATEGY_VERSION = "ict-sabri-malle-v1"

TIMEFRAMES = {

    "structure": "H1",

    "confirmation": "M15",

    "entry": "M5"
}


ORDER_BLOCK_CONFIG = {

    # Context / M15 Order Block quality
    "minimum_score": 85,
    "maximum_touches": 1,
    "maximum_age_candles": 100,
    "require_liquidity_sweep": True,
    "require_choch_or_bos": True,
    "require_retest": True,

    # M5 confirmation engine
    "require_rejection": True,
    "require_displacement": True,
    "require_micro_confirmation": True,
    "require_momentum": False,
    "minimum_body_ratio": 0.65,
    "minimum_rejection_wick_ratio": 0.30,
    "displacement_range_multiplier": 1.35,
    "momentum_range_multiplier": 1.00,
    "range_lookback": 20,
    "confirmation_mode": "midpoint",  # inside | midpoint | break_ob
    "max_confirmation_age_candles": 2,
    "require_strong_close": True,
    "strong_close_fraction": 0.30,

    # Harmonic pattern confluence (opcional inicialmente)
    "harmonic_enabled": True,
    "harmonic_tolerance": 0.10,
    "harmonic_minimum_score": 75.0,
    "harmonic_bonus_points": 10.0,
    "require_harmonic": False,
}



RISK_CONFIG = {

    "risk_percent": 1.0,

    "minimum_rr": 2.0,

    "default_rr": 2.0,

    "max_open_positions": 5  # 5 operaciones lógicas (hasta 10 posiciones físicas con split)
}

# ========================================================
# UNIVERSO DE ACTIVOS FILTRADOS / PODA POR PERFIL DE WORKER
# ========================================================
PRUNED_ASSET_UNIVERSE = {
    # STEP: Step Index 400 es el único activo rentable en 2 años (+3.7 R, PF 1.04). Se conservan los demás para compatibilidad.
    "STEP": ("Step Index 400", "Step Index", "Step Index 500", "Step Index 200", "Step Index 100"),
    # JUMP: Jump 50 Index (+15.6 R, 35.5% WR, PF 1.16) y Jump 25 Index (+6.5 R) son los líderes absolutos de la familia.
    "JUMP": ("Jump 50 Index", "Jump 25 Index", "Jump 75 Index", "Jump 10 Index"),
    # VOLATILITY: Selección curada con los activos de menor drawdown histórico (Vol 90, 25, 15, 10, etc.)
    "VOLATILITY": (
        "Volatility 90 Index",
        "Volatility 25 Index",
        "Volatility 15 Index",
        "Volatility 10 Index",
        "Volatility 50 Index",
        "Volatility 100 Index",
        "Volatility 250 (1s) Index",
        "Volatility 5 Index",
        "Volatility 90 (1s) Index",
        "High Frequency Vol 100 Index",
        "Vol over Boom 550",
        "High Frequency Vol 50 Index",
        "Vol over Crash 550",
        "VolSwitch High Vol Index",
        "Volatility 50 (1s) Index",
        "Volatility 75 Index",
        "Volatility 75 (1s) Index",
        "Volatility 150 (1s) Index",
        "Volatility 100 (1s) Index",
    ),
    # BOOM: Boom 500 (+13.4 R), Boom 300 (+8.2 R), Boom 1000 (+7.6 R) y Boom 600 (+3.5 R) son rentables. Boom 900 podado (-29.3 R).
    "BOOM": ("Boom 500 Index", "Boom 300 Index", "Boom 1000 Index", "Boom 600 Index"),
    # CRASH: Crash 300 Index es el único líder rentable (+13.5 R, 36.1% WR, PF 1.20).
    "CRASH": ("Crash 300 Index", "Crash 500 Index", "Crash 600 Index", "Crash 900 Index", "Crash 1000 Index"),
    # FOREX: Versiones normales y micro habilitables. EURUSD / EURUSDmicro es el líder rentable (+15.1 R con cierre intradía).
    "FOREX": (
        "EURUSD", "EURUSDmicro",
        "USDCAD", "USDCADmicro",
        "USDCHF", "USDCHFmicro",
        "AUDUSD", "AUDUSDmicro",
        "GBPUSD", "GBPUSDmicro",
        "USDJPY", "USDJPYmicro",
    ),
    # GOLD: Conservado 100% intacto según requerimiento estricto.
    "GOLD": (
        "XAUUSD", "XAGUSD",
        "XAUUSDmicro", "XAGUSDmicro",
    ),
    # ICT SABRI MALLE: Activos líderes del replay de 2 años (Metales, Cripto, Sintéticos y Forex con normal y micro).
    "ICT": (
        "XAUUSD", "XAUUSDmicro",
        "BTCUSD", "BTCUSDmicro",
        "Jump 50 Index",
        "EURUSD", "EURUSDmicro",
        "Crash 300 Index",
        "Boom 500 Index", "Boom 300 Index", "Boom 1000 Index", "Boom 600 Index",
        "Jump 25 Index",
        "Step Index 400",
        "XAGUSD", "XAGUSDmicro",
        "Wall Street 30", "US Tech 100", "US SP 500",
    ),
}