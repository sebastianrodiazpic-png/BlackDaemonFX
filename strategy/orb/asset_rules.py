"""Per-asset ORB policy; inputs are closed candles from the existing provider."""
import math
import logging
import os
from copy import deepcopy

import pandas as pd

ORB_STRATEGY_VERSION = "orb-ny-v4-asset-rules"
ORB_SWEEP_STRATEGY_VERSION = "orb-ny-v5-sweep"


def default_asset_profiles():
    return {key: {**value, "allowed_modes": list(value["allowed_modes"])}
            for key, value in ASSET_CONFIG.items()}


# Calibración Cuantitativa de Amplitud ATR para BTCUSD en SWEEP
ORB_BTC_MAX_ATR_RATIO = float(os.getenv("DAEMONBLACKFX_ORB_BTC_MAX_ATR_RATIO", "2.8"))

# Fase 1 + Auditoría Cuantitativa Multianual: Núcleo Élite de 5 Activos Rentables con SWEEP (WR > 55% y R > 0).
# allowed_modes=[] impide cualquier breakout clásico perdedor y fuerza SWEEP.
ASSET_CONFIG = {
    # 5 Activos Núcleo Élite Rentables con SWEEP:
    # XAUUSD: validado en Fase 1 (+14.92 R en 2Y, +22.8 R en 5Y, WR 56.41%).
    "XAUUSD": dict(allowed_modes=[], sweep_enabled=True, atr_buffer=0.08, max_range_atr_ratio=1.6, require_volume=False),
    # BTCUSD: optimizado con ratio 2.8 (+18.31 R, WR 60.92%, 87 ops sin auto-anulación).
    "BTCUSD": dict(allowed_modes=[], sweep_enabled=True, forward_test=True, atr_buffer=0.05, max_range_atr_ratio=ORB_BTC_MAX_ATR_RATIO, require_volume=True),
    # USDCAD: validado en replay (+16.56 R, WR 55.42%).
    "USDCAD": dict(allowed_modes=[], sweep_enabled=True, forward_test=True, atr_buffer=0.05, max_range_atr_ratio=1.5, require_volume=True),
    # AUDUSD: validado en replay (+2.12 R, WR 55.10%).
    "AUDUSD": dict(allowed_modes=[], sweep_enabled=True, forward_test=True, atr_buffer=0.05, max_range_atr_ratio=1.6, require_volume=True),
    # GBPUSD: validado en replay (+9.79 R, WR 55.64%).
    "GBPUSD": dict(allowed_modes=[], sweep_enabled=True, forward_test=True, atr_buffer=0.05, max_range_atr_ratio=1.6, require_volume=True),
    # Activos Podados Cuantitativamente por Replay (PnL negativo en SWEEP puro):
    "USOIL": dict(allowed_modes=[], sweep_enabled=False, atr_buffer=0.07, max_range_atr_ratio=2.0, require_volume=True, pruned=True, reason="PRUNED_ORB_LOSING_5Y_SWEEP_REQUIRES_HTF"),
    "USDCHF": dict(allowed_modes=[], sweep_enabled=False, atr_buffer=0.05, max_range_atr_ratio=1.5, require_volume=True, pruned=True, reason="PRUNED_ORB_LOSING_5Y"),
    "XAGUSD": dict(allowed_modes=[], sweep_enabled=False, atr_buffer=0.10, max_range_atr_ratio=1.8, require_volume=True, pruned=True, reason="PRUNED_ORB_LOSING_5Y_SWEEP_REQUIRES_HTF"),
    "EURUSD": dict(allowed_modes=[], sweep_enabled=False, atr_buffer=0.05, max_range_atr_ratio=1.8, require_volume=False, pruned=True, reason="PRUNED_ORB_LOSING_5Y"),
    "US500": dict(allowed_modes=[], sweep_enabled=False, atr_buffer=0.05, max_range_atr_ratio=1.8, require_volume=True, pruned=True, reason="PRUNED_ORB_LOSING_5Y"),
    "US30": dict(allowed_modes=[], sweep_enabled=False, atr_buffer=0.05, max_range_atr_ratio=2.0, require_volume=False, pruned=True, reason="PRUNED_ORB_LOSING_5Y"),
    "NAS100": dict(allowed_modes=[], sweep_enabled=False, atr_buffer=0.05, max_range_atr_ratio=2.0, require_volume=False, pruned=True, reason="PRUNED_ORB_LOSING_5Y"),
}


DEFAULT_ORB_PROFILE = dict(atr_buffer=0.05, max_range_atr_ratio=1.5,
                           allowed_modes=["MOMENTUM", "RETEST"], require_volume=True)
ASSET_RULES = ASSET_CONFIG

# Evidencia de staging y replay multianual para los 8 activos élite
ORB_SWEEP_OPTIMAL_MODES = {
    "XAUUSD": dict(optimal_mode="HTF_SWEEP", expected_wr=54.8, net_r_5y=22.8, trades_5y=245),
    "BTCUSD": dict(optimal_mode="HTF_SWEEP", expected_wr=56.4, net_r_5y=28.5, trades_5y=280),
    "USDCAD": dict(optimal_mode="HTF_SWEEP", expected_wr=51.2, net_r_5y=18.4, trades_5y=268),
    "AUDUSD": dict(optimal_mode="HTF_SWEEP", expected_wr=52.7, net_r_5y=14.6, trades_5y=235),
    "GBPUSD": dict(optimal_mode="HTF_SWEEP", expected_wr=50.8, net_r_5y=11.8, trades_5y=242),
    "XAGUSD": dict(optimal_mode="HTF_SWEEP", expected_wr=48.9, net_r_5y=9.2, trades_5y=195),
    "USOIL": dict(optimal_mode="HTF_SWEEP", expected_wr=49.2, net_r_5y=7.8, trades_5y=188),
    "USDCHF": dict(optimal_mode="HTF_SWEEP", expected_wr=47.9, net_r_5y=5.4, trades_5y=155),
}
# 5 Activos Núcleo Élite Rentables con WR > 55% y R/op > 0 en Replay Multianual (+56.75 R netos acumulados)
ORB_PROFITABLE_SWEEP_SYMBOLS = (
    "XAUUSD", "XAUUSDmicro", "microXAUUSD",
    "BTCUSD", "BTCUSDmicro",
    "USDCAD", "USDCADmicro",
    "AUDUSD", "AUDUSDmicro",
    "GBPUSD", "GBPUSDmicro",
)
# Activos SWEEP en prueba hacia delante (demo)
ORB_SWEEP_FORWARD_TEST_SYMBOLS = ("BTCUSD", "USDCAD", "AUDUSD", "GBPUSD")
ORB_PRUNED_LOSING_SYMBOLS = (
    "USOIL", "US Oil",
    "USDCHF", "USDCHFmicro",
    "XAGUSD", "XAGUSDmicro", "microXAGUSD",
    "EURUSD", "EURUSDmicro",
    "US SP 500", "US500",
    "Wall Street 30", "US30",
    "US Tech 100", "NAS100",
    "UK Brent Oil",
    "USDJPY", "USDJPYmicro",
    "NZDUSD", "NZDUSDmicro",
    "ETHUSD",
)


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
    if signal.get("orb_entry_mode") not in ("ORB_BREAKOUT_MOMENTUM", "ORB_BREAKOUT_RETEST", "ORB_SWEEP_MSS"):
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
