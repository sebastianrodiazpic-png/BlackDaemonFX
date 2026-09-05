from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone

from trade_outcome_policy import decisive_outcome, is_break_even_rr


def _metadata(trade):
    details = trade.get("details") if isinstance(trade, dict) else {}
    return details.get("metadata", {}) if isinstance(details, dict) else {}


def _strategy_name(trade):
    meta = _metadata(trade)
    explicit = str(meta.get("strategy_name") or "").upper()
    if explicit:
        return explicit
    profile = str(meta.get("bot_profile") or "").upper()
    if profile == "ORB":
        return "ORB_NEW_YORK"
    if profile:
        return "SMC"
    return "RECUPERADA_MT5"


def classify_close(trade):
    status = str(trade.get("status") or "").upper()
    if status == "OPEN":
        return "ABIERTA"
    result = str(trade.get("result") or "").upper()
    exit_reason = str(trade.get("exit_reason") or "").upper()
    if "EMERGENCY" in result or "EMERGENCY" in exit_reason or "RIESGO" in result:
        return "EMERGENCIA"

    def num(value):
        try:
            return float(value) if value is not None else None
        except (TypeError, ValueError):
            return None

    rr = num(trade.get("realized_rr"))
    pnl = num(trade.get("net_pnl"))
    planned_rr = num(trade.get("planned_rr"))
    meta = _metadata(trade)

    # v48: la zona neutral se evalúa antes del signo monetario.
    if is_break_even_rr(rr):
        return "BREAK EVEN / OTRO"
    leg = str(meta.get("trade_leg") or "").upper()
    mt5_close_reason = str(meta.get("mt5_close_reason") or "").upper()

    # Para operaciones históricas reconstruidas directamente desde MT5 no
    # siempre existe RR/SL/TP planificado en la base local. La razón del deal
    # de cierre permite clasificar el resultado sin inventar esos datos.
    if mt5_close_reason == "SL":
        return "STOP LOSS"
    if mt5_close_reason == "TP":
        if leg == "TP1":
            return "TP1"
        if leg in {"RUNNER", "SINGLE", "FULL"}:
            if planned_rr is not None and planned_rr >= 3.75:
                return "TP4"
            if planned_rr is not None and planned_rr >= 2.75:
                return "TP3"
            return "TP2"
        return "TAKE PROFIT"

    if pnl is not None and pnl > 0:
        if leg == "TP1" or (planned_rr is not None and planned_rr <= 1.25):
            return "TP1"
        if leg in {"RUNNER", "SINGLE", "FULL"} or (planned_rr is not None and planned_rr >= 1.5):
            if rr is not None and rr >= 3.75:
                return "TP4"
            if rr is not None and rr >= 2.75:
                return "TP3"
            if rr is None or rr >= 1.5:
                return "TP2"
            return "GANANCIA PARCIAL"
    if rr is not None:
        if rr >= 3.75:
            return "TP4"
        if rr >= 2.75:
            return "TP3"
        if rr >= 1.5:
            return "TP2"
        if 0.75 <= rr < 1.5:
            return "TP1"
        if rr <= -0.75:
            return "STOP LOSS"
    if pnl is not None and pnl < 0:
        return "PÉRDIDA PARCIAL"
    if pnl is not None and pnl > 0:
        return "GANANCIA PARCIAL"
    return "OTRO"


def build_account_payload(repository, source="DEMO", recent_limit=None):
    stats = {
        "total": 0, "open": 0, "closed": 0, "tp1": 0, "tp2": 0, "tp3": 0, "tp4": 0,
        "stop_loss": 0, "take_profit": 0, "break_even": 0, "emergency": 0,
        "wins": 0, "losses": 0, "win_rate": 0.0, "net_pnl": 0.0,
        "decisive_legs": 0, "logical_setups": 0, "logical_wins": 0,
        "logical_losses": 0, "logical_neutral": 0, "setup_win_rate": 0.0,
        "by_strategy": [],
    }
    payload = {
        "snapshot": None,
        "stats": stats,
        "recent_trades": [],
        "data_source": "SQLALCHEMY_LOCAL_ONLY",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stats_reset": None,
        "database": None,
        "persistence": {
            "snapshot": "account_snapshots",
            "activity": "trade_journal",
            "history": "trade_journal",
            "entry_confirmations": "trade_visual_audits.entry_context_json",
            "entry_vs_now_history": "trade_audit_snapshots",
            "transient_dashboard_state_used": False,
        },
    }
    if repository is None:
        return payload

    try:
        snapshot = repository.latest_account_snapshot() if hasattr(repository, "latest_account_snapshot") else None
        stats_reset = repository.latest_account_stats_reset(source=source) if hasattr(repository, "latest_account_stats_reset") else None
        # Cuenta activa es DB-only y respeta la ventana estadística persistente.
        frame = repository.account_trade_history_dataframe(source=source) if hasattr(repository, "account_trade_history_dataframe") else (repository.trade_history_dataframe(source=source) if hasattr(repository, "trade_history_dataframe") else (repository.trades_dataframe(source=source) if hasattr(repository, "trades_dataframe") else None))
    except Exception as exc:
        payload["error"] = str(exc)
        return payload

    records = [] if frame is None or getattr(frame, "empty", True) else frame.to_dict("records")

    confirmation_audits = {}
    try:
        if hasattr(repository, "trade_visual_audit_entry_contexts"):
            confirmation_audits = repository.trade_visual_audit_entry_contexts(
                source=source
            ) or {}
        elif hasattr(repository, "trade_visual_audits"):
            for audit in (repository.trade_visual_audits(source=source) or []):
                tid = audit.get("trade_id")
                if tid is not None:
                    confirmation_audits[str(tid)] = audit.get("entry_context") or {}
    except Exception:
        confirmation_audits = {}

    audit_snapshot_summaries = {}
    try:
        if hasattr(repository, "trade_audit_snapshot_summaries"):
            audit_snapshot_summaries = repository.trade_audit_snapshot_summaries(
                source=source
            ) or {}
        elif hasattr(repository, "trade_audit_snapshots"):
            for snap in (repository.trade_audit_snapshots(source=source) or []):
                tid = str(snap.get("trade_id"))
                summary = audit_snapshot_summaries.setdefault(
                    tid, {"count": 0, "latest_snapshot": None}
                )
                summary["count"] += 1
                if summary["latest_snapshot"] is None:
                    summary["latest_snapshot"] = snap
    except Exception:
        audit_snapshot_summaries = {}

    stats["total"] = len(records)
    logical_groups = {}
    for trade in records:
        classification = classify_close(trade)
        trade["classification"] = classification
        if str(trade.get("status") or "").upper() == "OPEN":
            stats["open"] += 1
            continue
        stats["closed"] += 1
        if classification == "TP1": stats["tp1"] += 1
        elif classification == "TP2": stats["tp2"] += 1
        elif classification == "TP3": stats["tp3"] += 1
        elif classification == "TP4": stats["tp4"] += 1
        elif classification == "TAKE PROFIT": stats["take_profit"] += 1
        elif classification == "STOP LOSS": stats["stop_loss"] += 1
        elif classification == "BREAK EVEN / OTRO": stats["break_even"] += 1
        elif classification == "EMERGENCIA": stats["emergency"] += 1
        try:
            pnl = float(trade.get("net_pnl") or 0.0)
        except (TypeError, ValueError):
            pnl = 0.0
        stats["net_pnl"] += pnl
        strategy = _strategy_name(trade)
        outcome = decisive_outcome(
            realized_rr=trade.get("realized_rr"),
            net_pnl=pnl,
            status=trade.get("status"),
            classification=classification,
        )
        if outcome == "WIN":
            stats["wins"] += 1
        elif outcome == "LOSS":
            stats["losses"] += 1

        meta = _metadata(trade)
        parent_key = meta.get("parent_execution_key")
        execution_key = trade.get("execution_key")
        candidate_key = parent_key if parent_key not in (None, "") else execution_key
        if candidate_key in (None, "") or str(candidate_key).strip().casefold() in {"nan", "none"}:
            candidate_key = f"TRADE:{trade.get('id')}"
        logical_key = str(candidate_key)
        logical = logical_groups.setdefault(logical_key, {
            "strategy": strategy, "net_pnl": 0.0, "risk_amount": 0.0,
            "has_risk_amount": False, "all_emergency": True,
        })
        logical["net_pnl"] += pnl
        try:
            risk_amount = float(trade.get("risk_amount") or 0.0)
        except (TypeError, ValueError):
            risk_amount = 0.0
        if risk_amount > 0:
            logical["risk_amount"] += risk_amount
            logical["has_risk_amount"] = True
        logical["all_emergency"] = bool(logical["all_emergency"] and classification == "EMERGENCIA")

    decisive = stats["wins"] + stats["losses"]
    stats["decisive_legs"] = decisive
    stats["win_rate"] = (stats["wins"] / decisive * 100.0) if decisive else 0.0
    by_strategy = defaultdict(lambda: {
        "strategy": None, "setups": 0, "wins": 0, "losses": 0,
        "neutral": 0, "net_pnl": 0.0, "gross_profit": 0.0,
        "gross_loss": 0.0,
    })
    for logical in logical_groups.values():
        # Un cierre de emergencia sin PnL pertenece a ejecución/riesgo, no al
        # desempeño de la tesis; se informa aparte y no contamina el win rate.
        if logical["all_emergency"] and abs(logical["net_pnl"]) <= 1e-9:
            continue
        stats["logical_setups"] += 1
        if logical["has_risk_amount"] and logical["risk_amount"] > 0:
            logical_rr = logical["net_pnl"] / logical["risk_amount"]
            setup_outcome = "WIN" if logical_rr > 0.25 else "LOSS" if logical_rr < -0.25 else "NEUTRAL"
        else:
            setup_outcome = "WIN" if logical["net_pnl"] > 0 else "LOSS" if logical["net_pnl"] < 0 else "NEUTRAL"
        logical["outcome"] = setup_outcome
        if setup_outcome == "WIN":
            stats["logical_wins"] += 1
        elif setup_outcome == "LOSS":
            stats["logical_losses"] += 1
        else:
            stats["logical_neutral"] += 1

        strategy_row = by_strategy[logical["strategy"]]
        strategy_row["strategy"] = logical["strategy"]
        strategy_row["setups"] += 1
        strategy_row["net_pnl"] += logical["net_pnl"]
        if logical["net_pnl"] > 0:
            strategy_row["gross_profit"] += logical["net_pnl"]
        elif logical["net_pnl"] < 0:
            strategy_row["gross_loss"] += abs(logical["net_pnl"])
        if setup_outcome == "WIN":
            strategy_row["wins"] += 1
        elif setup_outcome == "LOSS":
            strategy_row["losses"] += 1
        else:
            strategy_row["neutral"] += 1

    logical_decisive = stats["logical_wins"] + stats["logical_losses"]
    stats["setup_win_rate"] = (
        stats["logical_wins"] / logical_decisive * 100.0
        if logical_decisive else 0.0
    )
    for row in by_strategy.values():
        strategy_decisive = row["wins"] + row["losses"]
        row["win_rate"] = row["wins"] / strategy_decisive * 100.0 if strategy_decisive else 0.0
        row["net_pnl"] = round(row["net_pnl"], 2)
        row["gross_profit"] = round(row["gross_profit"], 2)
        row["gross_loss"] = round(row["gross_loss"], 2)
        row["average_pnl"] = round(row["net_pnl"] / row["setups"], 2) if row["setups"] else 0.0
        row["profit_factor"] = (
            round(row["gross_profit"] / row["gross_loss"], 2)
            if row["gross_loss"] > 0 else None
        )
    stats["by_strategy"] = sorted(
        by_strategy.values(),
        key=lambda row: (-row["net_pnl"], -(row["profit_factor"] or 0), row["strategy"] or ""),
    )
    records.sort(key=lambda t: (str(t.get("entry_time") or ""), int(t.get("id") or 0)), reverse=True)
    recent = []
    for trade in (records if recent_limit is None else records[:max(1, int(recent_limit))]):
        meta = _metadata(trade)
        source_trade_id = trade.get("source_trade_id") or trade.get("id")
        entry_audit = confirmation_audits.get(str(source_trade_id), {})
        recent.append({
            "id": trade.get("id"), "source_trade_id": source_trade_id, "instrument": trade.get("instrument"), "direction": trade.get("direction"),
            "strategy": _strategy_name(trade),
            "broker_position_ticket": trade.get("broker_position_ticket"),
            "status": trade.get("status"), "result": trade.get("result"), "entry_time": trade.get("entry_time"),
            "exit_time": trade.get("exit_time"), "planned_rr": trade.get("planned_rr"), "realized_rr": trade.get("realized_rr"),
            "net_pnl": trade.get("net_pnl"), "risk_percent": trade.get("risk_percent"),
            "leg": meta.get("trade_leg"), "execution_mode": meta.get("execution_mode"),
            "mfe_rr": meta.get("max_favorable_excursion_rr"),
            "mae_rr": meta.get("max_adverse_excursion_rr"),
            "runner_extension_stage": meta.get("runner_extension_stage"),
            "runner_profit_lock_rr": meta.get("runner_profit_lock_rr"),
            "classification": trade.get("classification"),
            "confirmation_audit": entry_audit,
            "confirmation_decision": entry_audit.get("decision"),
            "confirmation_score": entry_audit.get("score"),
            "confirmation_percentage": entry_audit.get("confirmation_percentage"),
            "passed_confirmations": entry_audit.get("passed") or [],
            "missing_confirmations": entry_audit.get("missing") or [],
            "critical_confirmation_failures": entry_audit.get("critical_failures") or [],
            "confirmation_details": entry_audit.get("confirmation_details") or {},
            "chart_pattern_confirmed": bool(entry_audit.get("chart_pattern_confirmed")),
            "chart_pattern_name": entry_audit.get("chart_pattern_name"),
            "chart_pattern_strength": entry_audit.get("chart_pattern_strength"),
            "chart_pattern_evidence": entry_audit.get("chart_pattern_evidence") or {},
            "chart_pattern_conflict": bool(entry_audit.get("chart_pattern_conflict")),
            "chart_pattern_supporting_pattern": entry_audit.get("chart_pattern_supporting_pattern"),
            "chart_pattern_supporting_direction": entry_audit.get("chart_pattern_supporting_direction"),
            "chart_pattern_supporting_strength": entry_audit.get("chart_pattern_supporting_strength"),
            "chart_pattern_conflicting_pattern": entry_audit.get("chart_pattern_conflicting_pattern"),
            "chart_pattern_conflicting_direction": entry_audit.get("chart_pattern_conflicting_direction"),
            "chart_pattern_conflicting_strength": entry_audit.get("chart_pattern_conflicting_strength"),
            "chart_pattern_conflict_level": entry_audit.get("chart_pattern_conflict_level"),
            "chart_pattern_conflict_reason": entry_audit.get("chart_pattern_conflict_reason"),
            "entry_vs_now_snapshot_count": audit_snapshot_summaries.get(
                str(source_trade_id), {}
            ).get("count", 0),
            "entry_vs_now_latest": audit_snapshot_summaries.get(
                str(source_trade_id), {}
            ).get("latest_snapshot") or {
                "snapshot_at": audit_snapshot_summaries.get(
                    str(source_trade_id), {}
                ).get("latest_snapshot_at")
            },
        })
    try:
        db_info = repository.database_diagnostics() if hasattr(repository, "database_diagnostics") else None
    except Exception as exc:
        db_info = {"error": str(exc)}

    meta_labeling = None
    try:
        if hasattr(repository, "meta_label_decision_summary"):
            meta_labeling = repository.meta_label_decision_summary(source=source)
    except Exception as exc:
        meta_labeling = {"error": str(exc)}

    return {
        "snapshot": snapshot,
        "stats": stats,
        "recent_trades": recent,
        "meta_labeling": meta_labeling,
        "data_source": "SQLALCHEMY_LOCAL_ONLY",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "stats_reset": stats_reset,
        "database": db_info,
        "persistence": {
            "snapshot": "account_snapshots",
            "activity": "trade_journal",
            "history": "trade_journal",
            "entry_confirmations": "trade_visual_audits.entry_context_json",
            "entry_vs_now_history": "trade_audit_snapshots",
            "meta_labeling": "daemon_audit_events.META_LABEL_SIGNAL_SCORED",
            "transient_dashboard_state_used": False,
        },
    }
