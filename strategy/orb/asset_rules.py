"""Per-asset ORB policy; inputs are closed candles from the existing provider."""
import math
import logging
import os
from copy import deepcopy

import pandas as pd

ORB_STRATEGY_VERSION = "orb-ny-v4-asset-rules"
ORB_SWEEP_STRATEGY_VERSION = "orb-ny-v5-sweep"


def default_asset_profiles():
    profiles = {key: {**value, "allowed_modes": list(value["allowed_modes"])}
                for key, value in ASSET_CONFIG.items()}
    if os.getenv("DAEMONBLACKFX_ORB_INDICES_ENABLED", "1").strip().lower() in ("1", "true", "on"):
        for k in ("US30", "NAS100", "US500"):
            if k in profiles:
                profiles[k]["allowed_modes"] = ["RETEST", "MOMENTUM"]
                profiles[k]["sweep_enabled"] = True
                profiles[k]["pruned"] = False
                profiles[k]["max_range_atr_ratio"] = float(os.getenv("DAEMONBLACKFX_ORB_INDEX_MAX_ATR_RATIO", "3.0"))
    return profiles


# Calibración Cuantitativa de Amplitud ATR para BTCUSD en SWEEP
ORB_BTC_MAX_ATR_RATIO = float(os.getenv("DAEMONBLACKFX_ORB_BTC_MAX_ATR_RATIO", "2.8"))

# Índices Americanos con Escenario de Retest de Apertura (Wall Street Cash 09:30 NY):
ORB_INDICES_ENABLED = os.getenv("DAEMONBLACKFX_ORB_INDICES_ENABLED", "1").strip().lower() in ("1", "true", "on")
ORB_INDEX_MAX_ATR_RATIO = float(os.getenv("DAEMONBLACKFX_ORB_INDEX_MAX_ATR_RATIO", "3.0"))
ORB_INDEX_MODES = ["RETEST", "MOMENTUM"] if ORB_INDICES_ENABLED else []

# Fase 1 + Auditoría Cuantitativa Multianual: Núcleo Élite de Activos Rentables con SWEEP y Retest.
ASSET_CONFIG = {
    # Activos Élite con WR > 47% y R/op > 0 en el replay multianual
    "XAUUSD": dict(allowed_modes=[], sweep_enabled=True, atr_buffer=0.08, max_range_atr_ratio=1.6, require_volume=False),
    "BTCUSD": dict(allowed_modes=[], sweep_enabled=True, atr_buffer=0.05, max_range_atr_ratio=1.8, require_volume=True),
    "USDCAD": dict(allowed_modes=[], sweep_enabled=True, atr_buffer=0.05, max_range_atr_ratio=1.5, require_volume=True),
    "GBPUSD": dict(allowed_modes=[], sweep_enabled=True, atr_buffer=0.05, max_range_atr_ratio=1.5, require_volume=False),
    "AUDUSD": dict(allowed_modes=[], sweep_enabled=True, atr_buffer=0.05, max_range_atr_ratio=1.5, require_volume=False),
    # Activos Rescatados tras auditoría cuantitativa (HTF_SWEEP / Asimetría)
    "XAGUSD": dict(allowed_modes=[], sweep_enabled=True, htf_aligned=True, atr_buffer=0.08, max_range_atr_ratio=1.8, require_volume=True),
    "USOIL": dict(allowed_modes=[], sweep_enabled=True, allowed_directions=["BUY"], atr_buffer=0.07, max_range_atr_ratio=1.8, require_volume=True),
    "USDCHF": dict(allowed_modes=[], sweep_enabled=True, allowed_directions=["BUY"], atr_buffer=0.05, max_range_atr_ratio=1.5, require_volume=False),
    # Activos en Poda Preventiva (WR <= 47% o R/op negativo)
    "EURUSD": dict(allowed_modes=[], atr_buffer=0.05, max_range_atr_ratio=1.8, require_volume=False, pruned=True, reason="PRUNED_LOW_EXPECTANCY_NY"),
    "US500": dict(allowed_modes=[], atr_buffer=0.05, max_range_atr_ratio=1.8, require_volume=True, pruned=True, reason="PRUNED_WHIPSAWS_CASH_OPEN"),
    "US30": dict(allowed_modes=[], atr_buffer=0.05, max_range_atr_ratio=2.0, require_volume=False, pruned=True, reason="PRUNED_LOW_WINRATE_28PCT"),
    "NAS100": dict(allowed_modes=[], atr_buffer=0.05, max_range_atr_ratio=2.0, require_volume=False, pruned=True, reason="PRUNED_USE_ICT_INSTEAD"),
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
# 8 Activos Rentables con WR > 47% y R/op > 0 en Replay Multianual (+73.4 R netos acumulados)
ORB_PROFITABLE_SWEEP_SYMBOLS = (
    "XAUUSD", "XAUUSDmicro", "microXAUUSD",
    "BTCUSD", "BTCUSDmicro", "microBTCUSD",
    "USDCAD", "USDCADmicro", "microUSDCAD",
    "GBPUSD", "GBPUSDmicro", "microGBPUSD",
    "AUDUSD", "AUDUSDmicro", "microAUDUSD",
    "XAGUSD", "XAGUSDmicro", "microXAGUSD",
    "US Oil",
    "USDCHF", "USDCHFmicro", "microUSDCHF",
)
ORB_SWEEP_FORWARD_TEST_SYMBOLS = ("USDCAD", "GBPUSD", "AUDUSD")
# Activos en Poda Preventiva (descartados por WR <= 47% o balance negativo)
ORB_PRUNED_LOSING_SYMBOLS = (
    "EURUSD", "EURUSDmicro", "microEURUSD",
    "USDJPY", "USDJPYmicro", "microUSDJPY",
    "NZDUSD", "NZDUSDmicro", "microNZDUSD",
    "US SP 500", "US500",
    "Wall Street 30", "US30",
    "US Tech 100", "NAS100",
    "UK Brent Oil",
    "ETHUSD",
    "US Small Cap 2000",
    "US Mid Cap 400",
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
    res = deepcopy(profile)
    if key in ("US30", "NAS100", "US500") and os.getenv("DAEMONBLACKFX_ORB_INDICES_ENABLED", "1").strip().lower() in ("1", "true", "on"):
        res["allowed_modes"] = ["RETEST", "MOMENTUM"]
        res["sweep_enabled"] = True
        res["pruned"] = False
        res["max_range_atr_ratio"] = float(os.getenv("DAEMONBLACKFX_ORB_INDEX_MAX_ATR_RATIO", "3.0"))
    return res


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
