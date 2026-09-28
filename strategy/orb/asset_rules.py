"""Per-asset ORB policy; inputs are closed candles from the existing provider."""
import math

import pandas as pd

ORB_STRATEGY_VERSION = "orb-ny-v4-asset-rules"


def default_asset_profiles():
    return {key: {**value, "allowed_modes": list(value["allowed_modes"])}
            for key, value in ASSET_CONFIG.items()}


ASSET_CONFIG = {
    "XAUUSD": dict(allowed_modes=["RETEST"], atr_buffer=0.08, max_range_atr_ratio=1.5, require_volume=False),
    "US30": dict(allowed_modes=["MOMENTUM", "RETEST"], atr_buffer=0.05, max_range_atr_ratio=2.0, require_volume=False),
    "NAS100": dict(allowed_modes=["MOMENTUM", "RETEST"], atr_buffer=0.05, max_range_atr_ratio=2.0, require_volume=False),
    "BTCUSD": dict(allowed_modes=["MOMENTUM"], atr_buffer=0.05, max_range_atr_ratio=1.8, require_volume=True),
}


def execution_metadata(signal):
    """Evidence to persist on every filled leg, including its eventual close."""
    if signal.get("orb_entry_mode") not in ("ORB_BREAKOUT_MOMENTUM", "ORB_BREAKOUT_RETEST"):
        return {}
    fields = {"strategy_name", "strategy_version", "retest_quality", "retest_quality_weight",
              "rejection_tail_ratio", "retest_candle_index", "asset_profile", "range_amplitude",
              "volume_evidence", "opening_range_atr_ratio"}
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
                  volume_status="UNAVAILABLE", missing_policy="NEUTRAL_BYPASS")
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
                      volume_ratio=current / average, volume_status="AVAILABLE")
        break
    if not required:
        result["missing_policy"] = "ASSET_FILTER_DISABLED"
    return result


def evaluate_retest_quality(retest_candle_index, rejection_tail_ratio):
    if retest_candle_index in (1, 2) and rejection_tail_ratio >= 0.5:
        return "HIGH_QUALITY"
    if retest_candle_index == 3:
        return "STANDARD_QUALITY"
    return "LOW_QUALITY"
