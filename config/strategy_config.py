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
    # Fase 1 (18-oct-2026): Step Index, Jump 25 Index, Volatility 25 Index y XAGUSD quedan fuera de la
    # Estrategia ICT (expectativa negativa en ambas mitades del replay fiel 365d; ver ICTSabriMalleConfig.excluded_symbols).
    # STEP (Estrategia ICT): Step Index 400 (+44.50R) y Step Index 500 (+25.25R) son los líderes rentables en 2 años.
    "STEP": ("Step Index 400", "Step Index 500", "Step Index 200", "Step Index 100"),
    # JUMP (Estrategia ICT): Jump 75 (+37.75R) y Jump 10 (+13.00R) son los activos rentables de la familia.
    "JUMP": ("Jump 75 Index", "Jump 10 Index", "Jump 50 Index"),
    # VOLATILITY (Estrategia ICT): Selección curada liderada por Vol 10 (+61.25R), Vol 50 1s (+43.75R), Vol 25 (+20.75R), Vol 15 (+14.75R), Vol 75 1s (+13.75R), Vol 75 (+7.50R) y Vol 250 1s (+3.00R).
    "VOLATILITY": (
        "Volatility 10 Index",
        "Volatility 50 (1s) Index",
        "Volatility 15 Index",
        "Volatility 75 (1s) Index",
        "Volatility 75 Index",
        "Volatility 250 (1s) Index",
        "Volatility 90 Index",
        "Volatility 50 Index",
        "Volatility 100 Index",
        "Volatility 5 Index",
        "Volatility 90 (1s) Index",
        "High Frequency Vol 100 Index",
        "Vol over Boom 550",
        "High Frequency Vol 50 Index",
        "Vol over Crash 550",
        "VolSwitch High Vol Index",
        "Volatility 150 (1s) Index",
        "Volatility 100 (1s) Index",
    ),
    # BOOM (Estrategia ICT): Boom 500 (+13.00R), Boom 300 (+8.00R), Boom 900 (+2.75R) y Boom 600 (+0.50R).
    "BOOM": ("Boom 500 Index", "Boom 300 Index", "Boom 900 Index", "Boom 600 Index", "Boom 1000 Index"),
    # CRASH (Estrategia ICT): Crash 600 Index (+17.25R, 31.8% WR, PF 1.16) es el líder rentable.
    "CRASH": ("Crash 600 Index", "Crash 300 Index", "Crash 500 Index", "Crash 900 Index", "Crash 1000 Index"),
    # FOREX (Estrategia ICT): Todos los pares rentables señalados en auditoría multi-anual (libres de poda).
    "FOREX": (
        "EURUSD", "EURUSDmicro",
        "GBPUSD", "GBPUSDmicro",
        "USDCAD", "USDCADmicro",
        "USDCHF", "USDCHFmicro",
        "AUDUSD", "AUDUSDmicro",
        "USDJPY", "USDJPYmicro",
        "AUDJPY", "AUDJPYmicro",
        "AUDNZD", "AUDNZDmicro",
        "CADCHF", "CADCHFmicro",
        "CHFJPY", "CHFJPYmicro",
        "EURCHF", "EURCHFmicro",
        "GBPCAD", "GBPCADmicro",
        "EURJPY", "EURJPYmicro",
        "GBPJPY", "GBPJPYmicro",
    ),
    # GOLD: Conservado 100% intacto según requerimiento estricto.
    "GOLD": (
        "XAUUSD", "XAGUSD",
        "XAUUSDmicro", "XAGUSDmicro",
    ),
    # ICT SABRI MALLE (Metales, Cripto, Índices & Commodities): XAUUSD (+17.25R), BTCUSD (+10.25R), US Oil (+2.50R).
    # Fase 1: sin XAGUSD, Jump 25 Index ni Step Index.
    "ICT": (
        "XAUUSD", "XAUUSDmicro",
        "BTCUSD", "BTCUSDmicro",
        "US Oil",
        "EURUSD", "EURUSDmicro",
        "Jump 50 Index",
        "Crash 300 Index", "Crash 600 Index",
        "Boom 500 Index", "Boom 300 Index", "Boom 900 Index", "Boom 600 Index", "Boom 1000 Index",
        "Jump 75 Index", "Jump 10 Index",
        "Step Index 400", "Step Index 500",
        "Wall Street 30", "US Tech 100", "US SP 500",
    ),
    # MALAYSIAN SNR (M15 Fresh/Break - Variante C2): 23 activos canónicos rentables/marginales (60.6% WR, +37.64R).
    "MALAYSIAN_SNR": (
        "Step Index 400", "XAGUSD", "AUDNZD", "Crash 1000 Index", "Jump 25 Index",
        "GBPJPY", "USDJPY", "GBPUSD", "Boom 300 Index", "Volatility 250 (1s) Index",
        "Step Index", "Jump 10 Index", "GBPAUD", "Wall Street 30", "EURUSD",
        "Volatility 50 (1s) Index", "Volatility 90 Index", "Boom 1000 Index",
        "Step Index 200", "EURCHF", "EURGBP", "XAUUSD", "Crash 600 Index",
    ),
    # ORB NEW YORK (Fase 1): solo XAUUSD en modo SWEEP (+0.17R/+0.21R por mitad del replay Núñez 2Y).
    "ORB": (
        "XAUUSD", "XAUUSDmicro",
    ),
}

# ========================================================
# PORTAFOLIO TRI-MOTOR (PASOS 1 A 4): TIERS DE RIESGO Y ORQUESTACIÓN
# ========================================================
TRI_MOTOR_TIER_S_ASSETS = {
    "MALAYSIAN_SNR": (
        "Step Index 400", "XAGUSD", "AUDNZD", "Jump 25 Index", "GBPJPY",
        "USDJPY", "GBPUSD", "Boom 300 Index", "Volatility 250 (1s) Index",
        "Step Index", "Jump 10 Index", "GBPAUD", "Wall Street 30", "EURUSD",
        "Volatility 50 (1s) Index", "Volatility 90 Index", "Boom 1000 Index",
        "Step Index 200", "EURCHF", "EURGBP", "XAUUSD", "Crash 600 Index",
    ),
    "ORB": (
        "XAUUSD", "XAUUSDmicro",
    ),
    "ICT": (
        "Volatility 10 Index",
        "Step Index 400",
        "Volatility 50 (1s) Index",
        "Jump 75 Index",
        "Step Index 500",
    ),
}

TRI_MOTOR_TIER_A_ASSETS = {
    "ICT": (
        "Crash 600 Index", "XAUUSD", "XAUUSDmicro",
        "GBPUSD", "GBPUSDmicro", "AUDJPY", "AUDJPYmicro", "Volatility 15 Index",
        "Volatility 75 (1s) Index", "Boom 500 Index", "Jump 10 Index", "AUDNZD", "AUDNZDmicro",
        "BTCUSD", "BTCUSDmicro", "Boom 300 Index", "Volatility 75 Index", "EURCHF", "EURCHFmicro",
        "CADCHF", "CADCHFmicro", "EURUSD", "EURUSDmicro", "Volatility 250 (1s) Index",
        "Boom 900 Index", "US Oil", "CHFJPY", "CHFJPYmicro", "Boom 600 Index",
    ),
    "MALAYSIAN_SNR": ("Crash 1000 Index",),
}

TRI_MOTOR_ORCHESTRATION_CONFIG = {
    "cap_per_strategy_symbol": 1,
    "anti_hedge_opposite_direction_guard": True,
    "tier_s_risk_percent": 1.0,
    "tier_a_risk_percent": 0.5,
    "dual_leg_split_ratio": (0.5, 0.5),
    "tp1_rr": 1.0,
    "be_plus_spread_on_tp1": True,
    "ict_gbdt_min_probability": 0.55,
    "msnr_c2_fx_metals_max_atr": 1.2,
    "msnr_c2_default_max_atr": 1.5,
    "msnr_min_adx": 30.0,
}
