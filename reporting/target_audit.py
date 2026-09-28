"""Target reconciliation evidence. Never sends orders or changes broker stops."""
import math
import re


def target_changes(before, after):
    changes = {}
    for name in ("stop_loss", "take_profit"):
        if name not in after:
            continue
        old, new = before.get(name), after[name]
        if old is None and new is None:
            continue
        if old is not None and new is not None and math.isclose(float(old), float(new), rel_tol=1e-10, abs_tol=1e-10):
            continue
        changes[name] = {"previous": old, "observed": new}
    return changes


def exit_target_evidence(trade, reason, comment):
    match = re.search(r"\[(sl|tp)\s+([0-9]+(?:\.[0-9]+)?)\]", str(comment or ""), re.I)
    if not match or match[1].upper() != reason:
        return {"status": "UNAVAILABLE", "source": "MT5_DEAL_COMMENT"}
    name = "stop_loss" if reason == "SL" else "take_profit"
    observed = float(match[2])
    changes = target_changes(trade, {name: observed})
    return {"status": "MISMATCH" if changes else "MATCH", "field": name,
            "recorded": trade.get(name), "observed": observed,
            "source": "MT5_DEAL_COMMENT", "actor": "UNKNOWN",
            "changed_at": None, "requires_review": bool(changes)}
