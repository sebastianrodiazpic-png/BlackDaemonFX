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
    # Auditoría Integral 212 Pares y Familia Step MultiStrategia:
    # Worker STEP (1) (Magic 26082104): Step Index 200, 400, 500
    # Worker STEP (2) (Magic 26082406): Step Index, 300, 1000, 1500, 2000
    "STEP": ("Step Index 200", "Step Index 400", "Step Index 500"),
    "STEP_2": ("Step Index", "Step Index 300", "Step Index 1000", "Step Index 1500", "Step Index 2000"),
    "JUMP": ("Jump 10 Index", "Jump 25 Index", "Jump 50 Index", "Jump 75 Index", "Jump 100 Index"),
    "VOLATILITY_3": (
        "Volatility 10 Index",
        "Volatility 100 Index",
        "Volatility 15 Index",
        "Volatility 25 Index",
        "Volatility 5 Index",
        "Volatility 50 Index",
        "Volatility 75 Index",
        "Volatility 90 Index",
    ),
    "VOLATILITY_1": (
        "High Frequency Vol 100 Index",
        "High Frequency Vol 50 Index",
        "High Frequency Vol 10 Index",
        "High Frequency Vol 25 Index",
        "High Frequency Vol 75 Index",
    ),
    "VOLATILITY_2": (
        "Ladder Volatility Down Index",
        "Ladder Volatility Up Index",
        "VolSwitch Low Vol Index",
        "VolSwitch Medium Vol Index",
    ),
    "VOLATILITY_4": (
        "Volatility 100 (1s) Index",
        "Volatility 150 (1s) Index",
        "Volatility 250 (1s) Index",
        "Volatility 50 (1s) Index",
        "Volatility 75 (1s) Index",
        "Volatility 90 (1s) Index",
        "Volatility 10 (1s) Index",
        "Volatility 15 (1s) Index",
        "Volatility 25 (1s) Index",
        "Volatility 30 (1s) Index",
        "Volatility 5 (1s) Index",
    ),
    "VOLATILITY": (
        "Volatility 10 Index",
        "Volatility 25 Index",
        "Volatility 50 (1s) Index",
        "Volatility 15 Index",
        "Volatility 75 (1s) Index",
        "Volatility 75 Index",
        "Volatility 250 (1s) Index",
        "Volatility 90 Index",
        "Volatility 50 Index",
        "Volatility 100 Index",
        "Volatility 5 Index",
        "High Frequency Vol 100 Index",
        "Vol over Boom 550",
        "Vol over Crash 550",
        "VolSwitch High Vol Index",
        "Volatility 150 (1s) Index",
        "Volatility 100 (1s) Index",
    ),
    "BOOM": (
        "Boom 1000 Index",
        "Boom 300 Index",
        "Boom 500 Index",
        "Boom 600 Index",
        "Boom 900 Index",
        "Volatility Boom 400 Index",
        "Volatility Boom 750 Index",
    ),
    "CRASH": (
        "Crash 1000 Index",
        "Crash 300 Index",
        "Crash 500 Index",
        "Crash 600 Index",
        "Crash 900 Index",
        "Volatility Crash 400 Index",
        "Volatility Crash 550 Index",
        "Volatility Crash 750 Index",
    ),
    "FOREX": (
        "GBPUSD", "GBPUSDmicro",
        "NZDUSD", "NZDUSDmicro",
        "CHFJPY", "CHFJPYmicro",
        "EURJPY", "EURJPYmicro",
        "EURCHF", "EURCHFmicro",
        "USDCHF", "USDCHFmicro",
        "GBPJPY", "GBPJPYmicro",
        "CADCHF", "CADCHFmicro",
    ),
    "FOREX_1": (
        "NZDCAD",
        "NZDUSD", "NZDUSDmicro",
        "NZDCHF",
        "NZDJPY",
        "NZDSGD",
    ),
    "FOREX_2": (
        "AUDCHF", "AUDCHFmicro",
        "AUDJPY", "AUDJPYmicro",
        "AUDNZD", "AUDNZDmicro",
        "AUDUSD", "AUDUSDmicro",
        "AUDCAD", "AUDCADmicro",
        "AUDSGD",
    ),
    "FOREX_3": (
        "EURAUD", "EURAUDmicro",
        "EURCAD", "EURCADmicro",
        "EURCHF", "EURCHFmicro",
        "EURGBP", "EURGBPmicro",
        "EURJPY", "EURJPYmicro",
        "EURNZD", "EURNZDmicro",
        "EURUSD", "EURUSDmicro",
        "EURHKD", "EURMXN", "EURNOK",
        "EURPLN", "EURSEK", "EURSGD", "EURZAR",
    ),
    "FOREX_4": (
        "USDCAD", "USDCADmicro",
        "USDCHF", "USDCHFmicro",
        "USDJPY", "USDJPYmicro",
        "USDCNH", "USDHKD", "USDMXN",
        "USDNOK", "USDPLN", "USDSEK",
        "USDSGD", "USDZAR",
    ),
    "FOREX_5": (
        "GBPAUD", "GBPCAD",
        "GBPCHF", "GBPCHFmicro",
        "GBPJPY", "GBPJPYmicro",
        "GBPNZD",
        "GBPUSD", "GBPUSDmicro",
        "GBPNOK", "GBPSEK", "GBPSGD",
    ),
    "GOLD": (
        "XAUUSD", "XAGUSD",
        "XAUUSDmicro", "XAGUSDmicro",
    ),
    "COMMODITIES_SNR": (
        "XAUUSD", "XAUUSDmicro", "microXAUUSD",
        "XAUEUR", "XAUEURmicro", "microXAUEUR",
        "XAGUSD", "XAGUSDmicro", "microXAGUSD",
        "US Oil", "UK Brent Oil",
    ),
    "COMMODITIES": (
        "XAUUSD", "XAUUSDmicro", "microXAUUSD",
        "XAUEUR", "XAUEURmicro", "microXAUEUR",
        "XAGUSD", "XAGUSDmicro", "microXAGUSD",
        "US Oil", "UK Brent Oil",
    ),
    "INDICESB_SNR": (
        "Wall Street 30", "US Tech 100", "US SP 500", "Germany 40",
    ),
    "INDICES": (
        "Wall Street 30", "US Tech 100", "US SP 500", "Germany 40",
    ),
    "FOREX_SNR": (
        "EURUSD", "EURUSDmicro",
        "GBPUSD", "GBPUSDmicro",
        "USDJPY", "USDJPYmicro",
        "AUDUSD", "AUDUSDmicro",
        "USDCAD", "USDCADmicro",
        "USDCHF", "USDCHFmicro",
        "NZDUSD", "NZDUSDmicro",
        "GBPJPY", "GBPJPYmicro",
        "EURJPY", "EURJPYmicro",
        "AUDJPY", "AUDJPYmicro",
        "CADJPY", "CADJPYmicro",
        "CHFJPY", "CHFJPYmicro",
        "EURCAD", "EURCADmicro",
        "EURAUD", "EURAUDmicro",
        "GBPAUD", "GBPAUDmicro",
        "GBPNZD", "GBPNZDmicro",
        "AUDCHF", "AUDCHFmicro",
        "CADCHF", "CADCHFmicro",
        "GBPCHF", "GBPCHFmicro",
        "EURGBP", "EURGBPmicro",
        "AUDCAD", "AUDCADmicro",
        "EURCHF", "EURCHFmicro",
        "EURNZD", "EURNZDmicro",
        "GBPCAD", "GBPCADmicro",
        "AUDNZD", "AUDNZDmicro",
        "BTCUSD", "BTCUSDmicro",
        "ETHUSD", "ETHUSDmicro",
    ),
    "ICT": (
        "BTCUSD", "ETHUSD",
        "BTCUSDmicro", "ETHUSDmicro",
        "XRPUSD",
        "XAUEUR", "XAUUSD",
        "XAUUSDmicro", "XAUEURmicro",
        "XAGUSD", "XAGUSDmicro",
        "US Oil", "UK Brent Oil",
    ),
    "MALAYSIAN_SNR": (
        "Step Index 400", "Crash 1000 Index", "Jump 25 Index",
        "GBPJPY", "USDJPY", "GBPUSD", "Boom 300 Index", "Volatility 250 (1s) Index",
        "Step Index", "Jump 10 Index", "Wall Street 30", "EURUSD",
        "Volatility 50 (1s) Index", "Volatility 90 Index", "Boom 1000 Index",
        "Step Index 200", "EURGBP", "XAUUSD", "Crash 600 Index",
    ),
    "ORB": (
        "XAUUSD", "XAUUSDmicro", "microXAUUSD",
        "XAUEUR", "XAUEURmicro", "microXAUEUR",
        "BTCUSD", "BTCUSDmicro",
        "USDCAD", "USDCADmicro",
        "AUDUSD", "AUDUSDmicro",
        "GBPUSD", "GBPUSDmicro",
        "XAGUSD", "XAGUSDmicro", "microXAGUSD",
        "US Oil",
        "USDCHF", "USDCHFmicro",
        "USDJPY", "USDJPYmicro",
        "ETHUSD", "ETHUSDmicro",
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
    # ORB NEW YORK: Activos Rentables con modo SWEEP y RETEST en Índices Americanos
    "ORB": (
        "XAUUSD", "XAUUSDmicro", "microXAUUSD",
        "XAUEUR", "XAUEURmicro", "microXAUEUR",
        "BTCUSD", "BTCUSDmicro",
        "USDCAD", "USDCADmicro",
        "AUDUSD", "AUDUSDmicro",
        "GBPUSD", "GBPUSDmicro",
        "XAGUSD", "XAGUSDmicro", "microXAGUSD",
        "US Oil",
        "USDCHF", "USDCHFmicro",
        "USDJPY", "USDJPYmicro",
        "ETHUSD", "ETHUSDmicro",
    ),
    "ICT": (
        "Crash 900 Index",
        "Volatility 50 (1s) Index",
        "Boom 900 Index",
        "Volatility 25 Index",
        "Jump 25 Index",
        "Step Index 200",
        "US Oil",
        "Step Index 400",
        "Jump 75 Index",
        "Step Index 500",
        "Volatility 10 Index",
    ),
}

TRI_MOTOR_TIER_A_ASSETS = {
    "ICT": (
        "XAUUSD", "XAUUSDmicro",
        "US Tech 100",
        "Volatility 150 (1s) Index", "Volatility 75 Index",
        "Volatility 75 (1s) Index", "Volatility 15 Index", "Boom 500 Index", "Jump 10 Index",
        "EURCHF", "EURCHFmicro", "EURCAD", "EURCADmicro", "GBPAUD", "GBPAUDmicro",
        "Volatility 250 (1s) Index", "Volatility 90 Index", "Volatility 5 Index",
        "High Frequency Vol 100 Index", "Volatility 100 Index", "Volatility 100 (1s) Index",
        "Boom 900 Index", "US Oil", "CHFJPY", "CHFJPYmicro", "GBPJPY", "GBPJPYmicro",
        "Boom 600 Index", "Crash 500 Index", "Jump 50 Index", "Jump 100 Index",
    ),
    "MALAYSIAN_SNR": ("Crash 1000 Index", "Jump 100 Index"),
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



# ========================================================
# PODA POR ACIERTO (WIN RATE) <= 45% EN SINTÉTICOS (replay fiel)
# ========================================================
# Criterio del usuario: solo se mantienen instrumentos con acierto > 45%.
#   ICT  (límite + tope spread/SL 2%, 365d): Boom 300 42.5%, Crash 1000 37.8%, Vol over Boom 550 44.5%,
#        Volatility 90 (1s) 41.7%.
#   MSNR (tope spread/SL 2%, 2 años): Step Index 42.2%, Volatility 100 40.4%, Jump 50 41.1%, Crash 300 42.6%,
#        Crash 600 41.7%, Boom 1000 36.7%, Volatility 90 (1s) 35.7%.
# DAEMONBLACKFX_SYNTH_WR45_PRUNE=0 desactiva esta poda.
# Definición en config/synth_wr45.py (la importa también config/ict_instrument_policy.py sin ciclos).
from config.synth_wr45 import ICT_WR45_PRUNED, MSNR_WR45_PRUNED, SYNTH_WR45_PRUNE_ENABLED  # noqa: E402,F401


def _without(symbols, pruned):
    return tuple(s for s in symbols if s not in set(pruned))


from config.ict_instrument_policy import ICT_5Y_RESCUED_SYNTHETICS as _RESCUED_SYNTHS, MALAYSIAN_SNR_ACTIVE as _MSNR_ACTIVE_ALL  # noqa: E402
for _family in ("STEP", "STEP_2", "JUMP", "VOLATILITY", "BOOM", "CRASH", "ICT"):
    PRUNED_ASSET_UNIVERSE[_family] = _without(PRUNED_ASSET_UNIVERSE[_family], set(ICT_WR45_PRUNED) - set(_RESCUED_SYNTHS))
PRUNED_ASSET_UNIVERSE["MALAYSIAN_SNR"] = tuple(_MSNR_ACTIVE_ALL)

# Política única de /Instruments ICT (config/ict_instrument_policy.py, 26-oct-2026): los universos de familia
# coinciden con lo que operan los workers; lo demás queda en PODA PREVENTIVA.
from config.ict_instrument_policy import (  # noqa: E402
    ICT_5Y_SYNTH_PRUNED as _ICT_5Y_SYNTH_PRUNED,
    ICT_ACTIVE_BY_PROFILE as _ICT_ACTIVE_BY_PROFILE,
    ICT_PHASE1_EXCLUDED as _ICT_PHASE1_EXCLUDED,
    ICT_SYNTHETIC_FAMILIES as _ICT_SYNTHETIC_FAMILIES,
)

for _tier in (TRI_MOTOR_TIER_S_ASSETS, TRI_MOTOR_TIER_A_ASSETS):
    if "ICT" in _tier:
        _tier["ICT"] = _without(_tier["ICT"], (*ICT_WR45_PRUNED, *_ICT_PHASE1_EXCLUDED, *_ICT_5Y_SYNTH_PRUNED))
    if "MALAYSIAN_SNR" in _tier:
        _tier["MALAYSIAN_SNR"] = _without(_tier["MALAYSIAN_SNR"], MSNR_WR45_PRUNED)

for _family, _symbols in _ICT_SYNTHETIC_FAMILIES.items():
    PRUNED_ASSET_UNIVERSE[_family] = tuple(_symbols)
PRUNED_ASSET_UNIVERSE["FOREX"] = tuple(_ICT_ACTIVE_BY_PROFILE["FOREX"])
PRUNED_ASSET_UNIVERSE["ICT"] = (
    "BTCUSD", "ETHUSD",
    "BTCUSDmicro", "ETHUSDmicro",
    "XRPUSD",
    "XAUEUR", "XAUUSD",
    "XAUUSDmicro", "XAUEURmicro",
    "XAGUSD", "XAGUSDmicro",
    "US Oil", "UK Brent Oil",
)
PRUNED_ASSET_UNIVERSE["COMMODITIES_SNR"] = (
    "XAUUSD", "XAUUSDmicro", "microXAUUSD",
    "XAUEUR", "XAUEURmicro", "microXAUEUR",
    "XAGUSD", "XAGUSDmicro", "microXAGUSD",
    "US Oil", "UK Brent Oil",
)
PRUNED_ASSET_UNIVERSE["COMMODITIES"] = PRUNED_ASSET_UNIVERSE["COMMODITIES_SNR"]
PRUNED_ASSET_UNIVERSE["INDICESB_SNR"] = (
    "Wall Street 30", "US Tech 100", "US SP 500", "Germany 40",
)
PRUNED_ASSET_UNIVERSE["INDICES"] = PRUNED_ASSET_UNIVERSE["INDICESB_SNR"]
PRUNED_ASSET_UNIVERSE["FOREX_SNR"] = tuple(_ICT_ACTIVE_BY_PROFILE["FOREX_SNR"])
