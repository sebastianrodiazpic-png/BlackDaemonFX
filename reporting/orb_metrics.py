"""Separate ORB expectancy from the durable execution journal (one row per leg)."""
import json
import math


def summarize_orb_trades(records):
    groups = {}
    seen = set()
    for row in records:
        details = row.get("details") or row.get("details_json") or {}
        if isinstance(details, str):
            try:
                details = json.loads(details)
            except (ValueError, TypeError):
                continue
        if not isinstance(details, dict):
            continue
        metadata = {**(details.get("signal") or {}), **(details.get("metadata") or details)}
        mode = metadata.get("orb_entry_mode")
        strategy = metadata.get("orb_metrics_strategy") or {
            "ORB_BREAKOUT_MOMENTUM": "ORB_NY_MOMENTUM",
            "ORB_BREAKOUT_RETEST": "ORB_NY_RETEST",
        }.get(mode)
        if strategy not in ("ORB_NY_MOMENTUM", "ORB_NY_RETEST"):
            continue
        identity = row.get("journal_key") or row.get("execution_key") or row.get("id")
        identity = (row.get("source"), row.get("broker"), identity)
        if identity[-1] is not None and identity in seen:
            continue
        seen.add(identity)
        key = (row.get("source"), row.get("broker"), row.get("instrument"), strategy)
        group = groups.setdefault(key, dict(source=key[0], broker=key[1], symbol=key[2], strategy=strategy,
                                           executions=0, closed=0, wins=0, losses=0, net_pnl=0.0, volume_status_counts={}))
        group["executions"] += 1
        volume_status = metadata.get("volume_status") or (metadata.get("volume_evidence") or {}).get("status", "UNKNOWN")
        counts = group["volume_status_counts"]
        counts[volume_status] = counts.get(volume_status, 0) + 1
        if str(row.get("status", "")).upper() != "CLOSED":
            continue
        try:
            pnl = float(row.get("net_pnl"))
        except (TypeError, ValueError):
            continue
        if not math.isfinite(pnl):
            continue
        group["closed"] += 1
        group["wins"] += int(pnl > 0)
        group["losses"] += int(pnl < 0)
        group["net_pnl"] += pnl
    for group in groups.values():
        group["expectancy_net_pnl"] = group["net_pnl"] / group["closed"] if group["closed"] else None
    return list(groups.values())
