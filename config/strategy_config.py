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