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

STRATEGY_VERSION = "SMC_V2"

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

    "minimum_rr": 1.5,

    "default_rr": 2.0,

    "max_open_positions": 3
}