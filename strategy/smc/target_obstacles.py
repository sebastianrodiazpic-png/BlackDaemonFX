"""Informational M15 obstacles. Never changes entry permission, SL or targets."""
import math
import pandas as pd


def collect_obstacles(data, direction):
    if data is None or data.empty:
        return []
    buy = direction == "BUY"
    items = []
    for _, row in data.iterrows():
        kind = row.get("ob_type")
        if kind != ("bearish" if buy else "bullish"):
            continue
        lo, hi = float(row.get("ob_low", float("nan"))), float(row.get("ob_high", float("nan")))
        if not (math.isfinite(lo) and math.isfinite(hi) and lo <= hi):
            continue
        known = row.get("ob_break_time")
        if pd.isna(known):
            continue
        later = data[pd.to_datetime(data["time"], utc=True) > pd.to_datetime(known, utc=True)]
        # Closing beyond the far edge invalidates this informational zone.
        if (later["close"].gt(hi).any() if buy else later["close"].lt(lo).any()):
            continue
        items.append({"type":"OPPOSING_OB", "low":lo, "high":hi, "formed_at":str(known)})
    # Range extreme is explicit, not an assertion that every historical pivot is active.
    level = float(data["high"].max() if buy else data["low"].min())
    if math.isfinite(level):
        items.append({"type":"M15_RANGE_EXTREME", "low":level, "high":level})
    return items


def target_path(entry, stop, target, direction, obstacles):
    risk = abs(float(entry)-float(stop))
    buy = direction == "BUY"
    hits=[]
    for zone in obstacles:
        lo,hi=float(zone["low"]),float(zone["high"])
        intersects = (hi >= entry and lo <= target) if buy else (lo <= entry and hi >= target)
        if intersects:
            distance=max(0.,lo-entry) if buy else max(0.,entry-hi)
            hits.append({**zone,"distance_r":distance/risk if risk else None})
    hits.sort(key=lambda z:z["distance_r"] if z["distance_r"] is not None else float("inf"))
    return {"mode":"INFORMATION_ONLY", "entry":entry,"stop_loss":stop,"target":target,
            "obstacles":hits,"clear_path":not hits,
            "method":"OPPOSING_OB_CLOSE_INVALIDATION_AND_RANGE_EXTREME"}
