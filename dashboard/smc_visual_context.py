from __future__ import annotations

from typing import Any
import math
import pandas as pd


def _float(value):
    try:
        number = float(value)
        return number if math.isfinite(number) else None
    except Exception:
        return None


def _iso(value):
    try:
        return pd.to_datetime(value, utc=True).isoformat()
    except Exception:
        return None


def _bool(row, name: str) -> bool:
    try:
        value = row.get(name, False)
        return bool(value) if pd.notna(value) else False
    except Exception:
        return False


def _zone_status(data: pd.DataFrame, source_pos: int, low: float, high: float, direction: str) -> str:
    """Estado visual de una zona; no altera la estrategia."""
    future = data.iloc[source_pos + 1 :]
    if future.empty:
        return "FRESCA"
    touched = False
    for _, row in future.iterrows():
        candle_low = _float(row.get("low"))
        candle_high = _float(row.get("high"))
        candle_close = _float(row.get("close"))
        if candle_low is None or candle_high is None:
            continue
        if candle_low <= high and candle_high >= low:
            touched = True
        if direction == "BUY" and candle_close is not None and candle_close < low:
            return "INVALIDADA"
        if direction == "SELL" and candle_close is not None and candle_close > high:
            return "INVALIDADA"
    return "MITIGADA" if touched else "FRESCA"


def _fvg_status(data: pd.DataFrame, source_pos: int, low: float, high: float, direction: str) -> str:
    future = data.iloc[source_pos + 1 :]
    if future.empty:
        return "ABIERTA"
    touched = False
    for _, row in future.iterrows():
        candle_low = _float(row.get("low"))
        candle_high = _float(row.get("high"))
        if candle_low is None or candle_high is None:
            continue
        if direction == "BUY":
            if candle_low <= low:
                return "RELLENADA"
            if candle_low <= high:
                touched = True
        else:
            if candle_high >= high:
                return "RELLENADA"
            if candle_high >= low:
                touched = True
    return "MITIGADA_PARCIAL" if touched else "ABIERTA"


def build_smc_visual_context(analyzed: pd.DataFrame | None, candle_count: int = 90) -> dict[str, Any]:
    """Construye evidencia visual SMC a partir del DataFrame ya analizado.

    No calcula entradas ni modifica señales. Extrae y deriva únicamente capas de
    auditoría para el dashboard. Los FVG se etiquetan como contexto auxiliar
    porque todavía no son una condición de entrada del motor.
    """
    empty = {
        "events": [],
        "zones": [],
        "levels": [],
        "context": {},
        "legend": {
            "strategy": ["Swings", "HH/HL/LH/LL", "CHOCH/BOS", "Liquidez/Sweeps", "Order Blocks", "Premium/Discount"],
            "auxiliary": ["Fair Value Gaps / Imbalances"],
        },
    }
    if analyzed is None or analyzed.empty:
        return empty

    data = analyzed.copy()
    if "time" not in data.columns:
        return empty
    data["time"] = pd.to_datetime(data["time"], utc=True, errors="coerce")
    data = data.dropna(subset=["time"]).sort_values("time").tail(int(candle_count)).reset_index(drop=True)
    if data.empty:
        return empty

    events: list[dict[str, Any]] = []
    levels: list[dict[str, Any]] = []
    zones: list[dict[str, Any]] = []

    # Estructura y eventos que ya existen en el pipeline SMC.
    flags = [
        ("choch_bullish", "CHOCH alcista", "BUY", "structure"),
        ("choch_bearish", "CHOCH bajista", "SELL", "structure"),
        ("bos_bullish", "BOS alcista", "BUY", "structure"),
        ("bos_bearish", "BOS bajista", "SELL", "structure"),
        ("bullish_sweep", "Sweep de Sell-Side Liquidity", "BUY", "liquidity"),
        ("bearish_sweep", "Sweep de Buy-Side Liquidity", "SELL", "liquidity"),
    ]
    for pos, row in data.iterrows():
        ts = _iso(row.get("time"))
        if not ts:
            continue
        structure = row.get("structure")
        if _bool(row, "swing_high"):
            events.append({"time": ts, "type": "swing_high", "label": str(structure or "Swing High"), "direction": "SELL", "price": _float(row.get("high")), "layer": "swings", "source": "strategy"})
        if _bool(row, "swing_low"):
            events.append({"time": ts, "type": "swing_low", "label": str(structure or "Swing Low"), "direction": "BUY", "price": _float(row.get("low")), "layer": "swings", "source": "strategy"})
        for col, label, direction, layer in flags:
            if _bool(row, col):
                price = _float(row.get("sweep_level")) if "sweep" in col else (_float(row.get("low")) if direction == "BUY" else _float(row.get("high")))
                events.append({"time": ts, "type": col, "label": label, "direction": direction, "price": price, "layer": layer, "source": "strategy"})

        # Liquidez identificada por máximos/mínimos aproximadamente iguales.
        liq = _float(row.get("liquidity_level"))
        if liq is not None:
            if _bool(row, "buy_side_liquidity"):
                levels.append({"time": ts, "type": "buy_side_liquidity", "label": "Buy-Side Liquidity (BSL)", "price": liq, "direction": "SELL", "layer": "liquidity", "source": "strategy"})
            if _bool(row, "sell_side_liquidity"):
                levels.append({"time": ts, "type": "sell_side_liquidity", "label": "Sell-Side Liquidity (SSL)", "price": liq, "direction": "BUY", "layer": "liquidity", "source": "strategy"})

        # Order Block como zona completa, no sólo marcador puntual.
        ob_low, ob_high = _float(row.get("ob_low")), _float(row.get("ob_high"))
        ob_type = str(row.get("ob_type") or "").lower()
        if ob_low is not None and ob_high is not None and ob_high >= ob_low and ob_type in {"bullish", "bearish"}:
            direction = "BUY" if ob_type == "bullish" else "SELL"
            zones.append({
                "time": ts,
                "type": "order_block",
                "label": "Order Block alcista" if direction == "BUY" else "Order Block bajista",
                "low": ob_low,
                "high": ob_high,
                "direction": direction,
                "status": _zone_status(data, pos, ob_low, ob_high, direction),
                "layer": "orderblock",
                "source": "strategy",
            })

    # FVG / imbalance de tres velas. Es contexto SMC auxiliar, aún no gate de entrada.
    for i in range(2, len(data)):
        left, current = data.iloc[i - 2], data.iloc[i]
        left_high, left_low = _float(left.get("high")), _float(left.get("low"))
        cur_high, cur_low = _float(current.get("high")), _float(current.get("low"))
        ts = _iso(current.get("time"))
        if None in (left_high, left_low, cur_high, cur_low) or not ts:
            continue
        if cur_low > left_high:
            low, high = left_high, cur_low
            zones.append({"time": ts, "type": "fvg_bullish", "label": "FVG / Imbalance alcista", "low": low, "high": high, "direction": "BUY", "status": _fvg_status(data, i, low, high, "BUY"), "layer": "fvg", "source": "auxiliary"})
        elif cur_high < left_low:
            low, high = cur_high, left_low
            zones.append({"time": ts, "type": "fvg_bearish", "label": "FVG / Imbalance bajista", "low": low, "high": high, "direction": "SELL", "status": _fvg_status(data, i, low, high, "SELL"), "layer": "fvg", "source": "auxiliary"})

    last = data.iloc[-1]
    range_high = _float(last.get("range_high"))
    range_low = _float(last.get("range_low"))
    equilibrium = _float(last.get("equilibrium"))
    context = {
        "zone": str(last.get("zone") or "").upper() or None,
        "range_high": range_high,
        "range_low": range_low,
        "equilibrium": equilibrium,
        "latest_structure": str(last.get("structure") or "") or None,
        "premium_discount_available": all(v is not None for v in (range_high, range_low, equilibrium)),
    }

    # Deduplica niveles idénticos/adyacentes para no saturar el gráfico.
    unique_levels = {}
    for item in levels:
        key = (item["type"], round(float(item["price"]), 8))
        unique_levels[key] = item

    return {
        "events": events[-140:],
        "zones": zones[-100:],
        "levels": list(unique_levels.values())[-40:],
        "context": context,
        "legend": empty["legend"],
    }
