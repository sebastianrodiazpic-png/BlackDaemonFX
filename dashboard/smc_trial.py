"""Small per-worker trial snapshots, independent of order execution."""
import json
import copy
import math
from datetime import date
import os
import re
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1] / "storage/runtime/smc_trial"
_LOCK = threading.Lock()
_STATE = {}


def _atomic_write(target, payload):
    """Retry transient Windows sharing failures without replacing the last good file."""
    temporary = target.with_name(target.name + '.' + uuid.uuid4().hex + '.tmp')
    try:
        temporary.write_text(payload, encoding='utf-8')
        for attempt in range(4):
            try:
                temporary.replace(target)
                return
            except PermissionError:
                if attempt == 3:
                    raise
                time.sleep(0.05 * 2 ** attempt)
    finally:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass


def audit_json_value(value):
    """Normalize temporal/numpy values before changing the persisted state."""
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): audit_json_value(v) for k,v in value.items()}
    if isinstance(value, (list, tuple)):
        return [audit_json_value(v) for v in value]
    if hasattr(value, 'item'):
        return audit_json_value(value.item())
    raise TypeError('Unsupported audit value: '+type(value).__name__)


def capture_failure(plan, quote, comparison, now):
    """Fail closed on incomplete or late observations; never backfill entry prices."""
    import pandas as pd
    try:
        entry, stop, target = (float(plan[k]) for k in ("entry_price", "stop_loss", "take_profit"))
        side = str(plan["direction"]).upper()
        expected = str(comparison.get("direction")).upper()
        expected = {"LONG":"BUY", "SHORT":"SELL"}.get(expected, expected)
        if side not in {"BUY", "SELL"} or side != expected:
            return "DIRECTION_MISMATCH"
        if not all(math.isfinite(x) and x > 0 for x in (entry, stop, target)):
            return "INVALID_PLAN"
        if not (stop < entry < target if side == "BUY" else target < entry < stop):
            return "INVALID_BARRIERS"
        closed = pd.to_datetime(comparison["confirmation_time"], utc=True) + pd.Timedelta(minutes=5)
        age = (pd.Timestamp(now)-closed).total_seconds()
        if pd.isna(closed) or not 0 <= age <= 600:
            return "STALE_OR_UNCLOSED_CONFIRMATION"
        if quote.get("spread_status") != "AVAILABLE" or quote.get("spread_source") != "MT5_EXECUTION":
            return "MISSING_EXECUTABLE_QUOTE"
        quote_time = pd.to_datetime(quote.get("spread_quote_time"), utc=True)
        quote_age = (pd.Timestamp(now)-quote_time).total_seconds()
        if pd.isna(quote_time) or not -60 <= quote_age <= 180:
            return "STALE_EXECUTABLE_QUOTE"
        bid, ask = float(quote["execution_bid"]), float(quote["execution_ask"])
        executable = ask if side == "BUY" else bid
        if not all(math.isfinite(x) and x > 0 for x in (bid, ask)) or ask < bid:
            return "INVALID_EXECUTABLE_QUOTE"
        if not (stop < executable < target if side == "BUY" else target < executable < stop):
            return "QUOTE_OUTSIDE_BARRIERS"
    except (KeyError, TypeError, ValueError):
        return "MISSING_CAUSAL_PLAN"
    return None


def instrument_group(profile, symbol):
    name = str(symbol).upper()
    if name.startswith("XAU"):
        return "ORO"
    if name.startswith("XAG"):
        return "PLATA"
    if str(profile).startswith("FOREX"):
        return "FOREX"
    if profile == "GOLD":
        return "INDICES_Y_OTROS"
    return "SINTETICOS"


def record(profile, result, policy, retest, root=None, now=None, quote_reader=None):
    if result.get("strategy_name") != "SMC":
        return result
    result = audit_json_value(result)
    root = Path(root or ROOT)
    now = now or datetime.now(timezone.utc)
    day = now.astimezone(ZoneInfo("America/Santiago")).date().isoformat()
    profile = re.sub(r"[^A-Za-z0-9_-]", "_", str(profile))
    key = (str(root), profile, day)
    with _LOCK:
        if key not in _STATE:
            try:
                previous = json.loads((root / (profile + ".json")).read_text(encoding="utf-8"))
                if previous.get("day") == day and previous.get("profile") == profile:
                    _STATE[key] = previous
            except (OSError, ValueError):
                pass
        state = _STATE.setdefault(key, {"profile": profile, "day": day, "since": now.isoformat(), "counts": {}, "latest": {}, "stale_signals": [], "evaluations": 0})
        state.update(updated_at=now.isoformat(), policy=policy, retest=retest)
        from dashboard.setup_audit import update_blocks, update_signal
        update_blocks(state, result, now)
        update_signal(state, result, now)
        comparison = result.get("setup_sequence_shadow") or {}
        if comparison.get("setup_time"):
            identity = "|".join(str(x) for x in (result.get("symbol"),comparison.get("direction"),
                comparison["setup_time"],comparison.get("ob_low"),comparison.get("ob_high")))
            setup = state.setdefault("unique_setups", {}).setdefault(identity, {
                "symbol":result.get("symbol"), "first_seen":now.isoformat(), "evaluations":0})
            setup.update(last_seen=now.isoformat(), action=result.get("action"), comparison=comparison)
            setup.setdefault("setup_formed_at", comparison.get("setup_time"))
            setup["stage_timing"] = result.get("stage_timing") or {}
            setup["signal_age"] = result.get("signal_age") or {}
            if result.get("action") == "STALE_M5_SIGNAL":
                setup.setdefault("first_expired_at", now.isoformat())
            candidates = dict(comparison.get("variants", {}))
            if comparison.get("baseline_critical_failures") == []:
                candidates["BASELINE"] = {"remaining_critical_failures":[], "ob_respected":True}
            quote = copy.deepcopy(result.get("shadow_quote") or {})
            for variant, evidence in candidates.items():
                if evidence.get("remaining_critical_failures") == [] and evidence.get("ob_respected") is True:
                    if variant not in setup.get("first_variant_ready", {}) and not quote and callable(quote_reader):
                        quote = quote_reader(result.get("symbol"))
                    if variant in setup.get("first_variant_ready", {}):
                        continue  # Historical captures are immutable, including incomplete legacy ones.
                    quote = audit_json_value(quote or {})
                    failure = capture_failure(result.get("shadow_plan") or {}, quote, comparison, now)
                    if failure:
                        setup.setdefault("variant_capture_failures", {})[variant] = {
                            "reason": failure, "observed_at": now.isoformat(), "entry_authorized": False}
                        continue
                    setup.setdefault("variant_capture_failures", {}).pop(variant, None)
                    setup.setdefault("first_variant_ready", {}).setdefault(variant, {
                        "observed_at": now.isoformat(), "confirmation_time": comparison.get("confirmation_time"),
                        "execution_quote": copy.deepcopy(quote),
                        "plan": copy.deepcopy(result.get("shadow_plan") or {}), "evidence": copy.deepcopy(evidence),
                        "status": "PENDING_CLOSED_REPLAY", "entry_authorized": False})
            setup["evaluations"] += 1
            point = {"confirmation_time":comparison.get("confirmation_time"),
                     "action":result.get("action"), "variants":comparison.get("variants", {})}
            timeline = setup.setdefault("timeline", [])
            previous_point = {k:v for k,v in timeline[-1].items() if k != "observed_at"} if timeline else None
            if previous_point != point:
                point["observed_at"] = now.isoformat()
                timeline.append(point)
                setup["timeline"] = timeline[-64:]
        state["evaluations"] += 1
        action = result.get("action") or "UNKNOWN"
        state["counts"][action] = state["counts"].get(action, 0) + 1
        symbol = result.get("symbol") or "?"
        group = instrument_group(profile, symbol)
        group_counts = state.setdefault("groups", {}).setdefault(group, {})
        group_counts[action] = group_counts.get(action, 0) + 1
        signal_time = (result.get("signal_age") or {}).get("signal_time")
        if signal_time:
            identity = symbol + ":" + str(result.get("direction")) + ":" + str(signal_time)
            candidate = state.setdefault("candidates", {}).setdefault(identity, {
                "symbol": symbol, "group": group, "signal_time": signal_time,
                "first_seen": now.isoformat()})
            candidate.update(last_seen=now.isoformat(), action=action,
                             reason=result.get("reason"), expired=action == "STALE_M5_SIGNAL")
        state["latest"][symbol] = {k: result.get(k) for k in ("symbol", "action", "reason", "direction", "signal_age", "critical_confirmation_failures", "entry_location_comparison", "retest_comparison", "favorable_confirmation", "m5_structure_event", "ob_close_recovery", "target_path_audit", "setup_sequence_shadow", "m15_block_audit", "historical_m5_rejection", "m15_block_summary")}
        state["latest"][symbol]["updated_at"] = now.isoformat()
        if action == "STALE_M5_SIGNAL":
            identity = symbol + ":" + str((result.get("signal_age") or {}).get("signal_time"))
            if identity not in state["stale_signals"]:
                state["stale_signals"].append(identity)
        root.mkdir(parents=True, exist_ok=True)
        target = root / (profile + ".json")
        payload = json.dumps(state, ensure_ascii=False)
        _atomic_write(target, payload)
        # Preserve completed days for unique-setup comparisons after rollover.
        archive = root / "history"
        archive.mkdir(exist_ok=True)
        archive_target = archive / (profile + "_" + day + ".json")
        _atomic_write(archive_target, payload)
        return result


def snapshot(root=None):
    rows, errors = [], []
    for path in sorted(Path(root or ROOT).glob("*.json")):
        try:
            worker = json.loads(path.read_text(encoding="utf-8"))
            unique = worker.get("unique_setups", {})
            failures = {}
            for setup in unique.values():
                variants = (setup.get("comparison") or {}).get("variants", {})
                for failure in (variants.get("STRUCTURE_AND_DISPLACEMENT_WITHIN_3_BARS") or {}).get("remaining_critical_failures", []):
                    failures[failure] = failures.get(failure, 0) + 1
            worker["unique_setup_diagnostics"] = {"setups":len(unique),
                "remaining_failure_counts":failures, "counting_unit":"LATEST_COMPARISON_PER_SETUP",
                "variant_ready_setups":sum(bool(x.get("first_variant_ready")) for x in unique.values()),
                "capture_failure_setups":sum(bool(x.get("variant_capture_failures")) for x in unique.values()),
                "expired_setups":sum(bool(x.get("first_expired_at")) for x in unique.values()),
                "entry_authorized":False}
            replay_path = Path(root or ROOT) / "replay" / (str(worker.get("profile")) + ".json")
            if replay_path.exists():
                worker["variant_outcomes"] = json.loads(replay_path.read_text(encoding="utf-8"))
            rows.append(worker)
        except (OSError, ValueError) as exc:
            errors.append(path.name + ": " + str(exc))
    return {"workers": rows, "errors": errors}
