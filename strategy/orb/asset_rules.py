"""Per-asset ORB policy; inputs are closed candles from the existing provider."""
import math
import logging
from copy import deepcopy

import pandas as pd

ORB_STRATEGY_VERSION = "orb-ny-v4-asset-rules"


def default_asset_profiles():
    return {key: {**value, "allowed_modes": list(value["allowed_modes"])}
            for key, value in ASSET_CONFIG.items()}


ASSET_CONFIG = {
    "XAUUSD": dict(allowed_modes=["MOMENTUM", "RETEST"], atr_buffer=0.08, max_range_atr_ratio=1.6, require_volume=False),
    "XAGUSD": dict(allowed_modes=["RETEST"], atr_buffer=0.10, max_range_atr_ratio=1.8, require_volume=True),
    "USOIL": dict(allowed_modes=["MOMENTUM", "RETEST"], atr_buffer=0.07, max_range_atr_ratio=2.0, require_volume=True),
    "US500": dict(allowed_modes=["MOMENTUM"], atr_buffer=0.04, max_range_atr_ratio=1.4, require_volume=True),
    "US30": dict(allowed_modes=["MOMENTUM", "RETEST"], atr_buffer=0.05, max_range_atr_ratio=2.0, require_volume=False),
    "NAS100": dict(allowed_modes=["MOMENTUM", "RETEST"], atr_buffer=0.05, max_range_atr_ratio=2.0, require_volume=False),
    "BTCUSD": dict(allowed_modes=["MOMENTUM"], atr_buffer=0.05, max_range_atr_ratio=1.8, require_volume=True),
}


DEFAULT_ORB_PROFILE = dict(atr_buffer=0.05, max_range_atr_ratio=1.5,
                           allowed_modes=["MOMENTUM", "RETEST"], require_volume=True)
ASSET_RULES = ASSET_CONFIG


def get_asset_rules(symbol):
    """Resolve broker aliases and return an independent profile."""
    from strategy.orb.new_york_orb import classify_orb_market
    market = classify_orb_market(symbol)
    key = {"MICRO_XAUUSD":"XAUUSD", "MICRO_XAGUSD":"XAGUSD",
           "US_OIL":"USOIL", "US_500":"US500", "WALL_STREET_30":"US30",
           "US_TECH_100":"NAS100"}.get(market, market)
    profile = ASSET_CONFIG.get(key)
    if profile is None:
        logging.getLogger(__name__).warning("ORB fallback profile for %s", symbol)
        profile = DEFAULT_ORB_PROFILE
    return deepcopy(profile)


def execution_metadata(signal):
    """Evidence to persist on every filled leg, including its eventual close."""
    if signal.get("orb_entry_mode") not in ("ORB_BREAKOUT_MOMENTUM", "ORB_BREAKOUT_RETEST"):
        return {}
    fields = {"strategy", "signal", "sl_price", "tp1_price", "tp2_price", "execution_policy", "audit_metadata", "strategy_name", "strategy_version", "retest_quality", "retest_quality_weight",
              "rejection_tail_ratio", "retest_candle_index", "asset_profile", "range_amplitude",
              "volume_evidence", "volume_status", "atr_frozen_m5", "opening_range_atr_ratio"}
    return {key: value for key, value in signal.items() if key.startswith("orb_") or key in fields}


def check_range_amplitude(range_high, range_low, atr, max_atr_ratio=1.8):
    size = range_high - range_low
    valid = atr is not None and math.isfinite(atr) and atr > 0 and math.isfinite(size) and size > 0
    ratio = size / atr if valid else None
    return dict(range_size=size, atr=atr, ratio=ratio,
                allow_momentum=bool(valid and ratio <= max_atr_ratio),
                isValid=bool(valid and ratio <= max_atr_ratio * 1.3))


def audit_volume_confirmation(candles, candle_time, mode, required):
    """Ten prior bars, no future bars; zero/malformed feeds bypass neutrally."""
    window = candles[candles.time <= candle_time].tail(11)
    result = dict(confirmed=True, required=required, volume_source=None,
                  volume=None, average_volume=None, volume_ratio=None,
                  volume_threshold=1.0 if mode == "MOMENTUM" else 0.7,
                  volume_status="UNAVAILABLE", missing_policy="NEUTRAL_BYPASS",
                  status="VOLUMEN_NO_DISPONIBLE_PASSTHROUGH",
                  detail="Operación permitida sin validación de volumen: datos no disponibles o insuficientes.")
    for source in ("real_volume", "tick_volume", "volume"):
        if source not in window:
            continue
        values = pd.to_numeric(window[source], errors="coerce")
        if len(values) != 11 or not values.map(math.isfinite).all() or (values < 0).any() or values.sum() <= 0:
            continue
        average = float(values.iloc[:-1].mean())
        if average <= 0:
            continue
        current = float(values.iloc[-1])
        confirmed = current > average if mode == "MOMENTUM" else current >= average * 0.7
        result.update(confirmed=bool(confirmed) if required else True,
                      volume_source=source, volume=current, average_volume=average,
                      volume_ratio=current / average, volume_status="AVAILABLE",
                      status="VOLUMEN_CONFIRMADO" if confirmed else "VOLUMEN_INSUFICIENTE",
                      detail=f"Volumen {current:g}; promedio {average:g}; umbral {result['volume_threshold']:g}.")
        break
    if not required:
        result["missing_policy"] = "ASSET_FILTER_DISABLED"
        if result["volume_status"] == "AVAILABLE":
            result["status"] = "FILTRO_VOLUMEN_DESACTIVADO"
            result["detail"] += " Filtro desactivado por perfil de activo."
    return result


def evaluate_retest_quality(retest_candle_index, rejection_tail_ratio):
    if retest_candle_index in (1, 2) and rejection_tail_ratio >= 0.5:
        return "HIGH_QUALITY"
    if retest_candle_index == 3:
        return "STANDARD_QUALITY"
    return "LOW_QUALITY"
