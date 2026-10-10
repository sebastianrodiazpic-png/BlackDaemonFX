"""Calendar performance of completed logical operations, in Santiago time."""
from collections import defaultdict
from datetime import datetime
import math
from zoneinfo import ZoneInfo
import calendar


def _calculate_single_month_performance(
    year: int,
    month: int,
    logical_ops: list,
    current: datetime,
    base_balance: float,
    month_names: list,
    weekday_names: list,
) -> dict:
    """Calcula métricas detalladas día a día para un mes específico."""
    month_ops = [op for op in logical_ops if op["year"] == year and op["month"] == month]

    _, total_days_in_month = calendar.monthrange(year, month)
    first_weekday_idx = datetime(year, month, 1).weekday()  # 0 = Lunes, 6 = Domingo

    if year == current.year and month == current.month:
        days_elapsed = current.day
        today_day = current.day
    elif (year < current.year) or (year == current.year and month < current.month):
        days_elapsed = total_days_in_month
        today_day = None
    else:
        days_elapsed = 0
        today_day = None

    days_map = {}
    for op in month_ops:
        days_map.setdefault(op["day"], []).append(op)

    days_list = []
    calendar_days = []
    active_days_count = 0
    winning_days_count = 0
    losing_days_count = 0
    neutral_days_count = 0

    strategy_totals = defaultdict(lambda: {"pnl": 0.0, "trades": 0, "wins": 0, "losses": 0, "be": 0})

    for d in range(1, total_days_in_month + 1):
        dt = datetime(year, month, d)
        wk_idx = dt.weekday()
        wk_name = weekday_names[wk_idx]
        ops_today = days_map.get(d, [])
        # Ordenar operaciones del día desde la hora más reciente a la más antigua
        ops_today.sort(key=lambda op: str(op.get("datetime") or op.get("time_str") or ""), reverse=True)

        is_future = d > days_elapsed
        is_today = bool(year == current.year and month == current.month and d == current.day)

        if not is_future:
            day_pnl = round(sum(op["net_pnl"] for op in ops_today), 2)
            total_trades = len(ops_today)
            wins = sum(1 for op in ops_today if op["is_win"])
            losses = sum(1 for op in ops_today if op["is_loss"])
            be = sum(1 for op in ops_today if op["is_be"])
            wr = round((wins / total_trades * 100.0), 1) if total_trades > 0 else 0.0
            pos_pct = round((wins / total_trades * 100.0), 1) if total_trades > 0 else 0.0
            neg_pct = round((losses / total_trades * 100.0), 1) if total_trades > 0 else 0.0
            be_pct = round((be / total_trades * 100.0), 1) if total_trades > 0 else 0.0
            ret_pct = round((day_pnl / base_balance) * 100.0, 2) if base_balance > 0 else 0.0

            day_strats = {}
            for op in ops_today:
                s_name = op["strategy"]
                if s_name not in day_strats:
                    day_strats[s_name] = {"pnl": 0.0, "trades": 0, "wins": 0, "losses": 0}
                day_strats[s_name]["pnl"] = round(day_strats[s_name]["pnl"] + op["net_pnl"], 2)
                day_strats[s_name]["trades"] += 1
                if op["is_win"]:
                    day_strats[s_name]["wins"] += 1
                elif op["is_loss"]:
                    day_strats[s_name]["losses"] += 1

                strategy_totals[s_name]["pnl"] = round(strategy_totals[s_name]["pnl"] + op["net_pnl"], 2)
                strategy_totals[s_name]["trades"] += 1
                if op["is_win"]:
                    strategy_totals[s_name]["wins"] += 1
                elif op["is_loss"]:
                    strategy_totals[s_name]["losses"] += 1
                else:
                    strategy_totals[s_name]["be"] += 1

            day_assets = {}
            for op in ops_today:
                a_name = op["asset"]
                if a_name not in day_assets:
                    day_assets[a_name] = {"pnl": 0.0, "trades": 0}
                day_assets[a_name]["pnl"] = round(day_assets[a_name]["pnl"] + op["net_pnl"], 2)
                day_assets[a_name]["trades"] += 1

            if total_trades > 0:
                active_days_count += 1
                if day_pnl > 0.001:
                    winning_days_count += 1
                elif day_pnl < -0.001:
                    losing_days_count += 1
                else:
                    neutral_days_count += 1

            day_obj = {
                "day": d,
                "date": dt.strftime("%Y-%m-%d"),
                "weekday": wk_name,
                "weekday_idx": wk_idx,
                "net_pnl": day_pnl,
                "return_pct": ret_pct,
                "trades_count": total_trades,
                "wins": wins,
                "losses": losses,
                "break_even": be,
                "pos_trades_pct": pos_pct,
                "neg_trades_pct": neg_pct,
                "be_trades_pct": be_pct,
                "winrate": wr,
                "strategies": day_strats,
                "assets": day_assets,
                "operations": ops_today,
                "has_trades": total_trades > 0,
                "is_best_day": False,
                "is_worst_day": False,
                "is_today": is_today,
                "is_future": False,
            }
            days_list.append(day_obj)
            calendar_days.append(day_obj)
        else:
            day_obj = {
                "day": d,
                "date": dt.strftime("%Y-%m-%d"),
                "weekday": wk_name,
                "weekday_idx": wk_idx,
                "net_pnl": 0.0,
                "return_pct": 0.0,
                "trades_count": 0,
                "wins": 0,
                "losses": 0,
                "break_even": 0,
                "pos_trades_pct": 0.0,
                "neg_trades_pct": 0.0,
                "be_trades_pct": 0.0,
                "winrate": 0.0,
                "strategies": {},
                "assets": {},
                "operations": [],
                "has_trades": False,
                "is_best_day": False,
                "is_worst_day": False,
                "is_today": is_today,
                "is_future": True,
            }
            calendar_days.append(day_obj)

    # 4. Encontrar Mejor Día y Peor Día
    best_day = None
    worst_day = None
    active_days = [d for d in days_list if d["has_trades"]]

    if active_days:
        best_cand = max(active_days, key=lambda x: x["net_pnl"])
        if best_cand["net_pnl"] > 0:
            best_cand["is_best_day"] = True
            for cd in calendar_days:
                if cd["day"] == best_cand["day"]:
                    cd["is_best_day"] = True
            top_strat = "—"
            if best_cand["strategies"]:
                top_strat = max(best_cand["strategies"].items(), key=lambda kv: kv[1]["pnl"])[0]
            best_day = {
                "day": best_cand["day"],
                "date": best_cand["date"],
                "weekday": best_cand["weekday"],
                "net_pnl": best_cand["net_pnl"],
                "return_pct": best_cand["return_pct"],
                "trades": best_cand["trades_count"],
                "top_strategy": top_strat,
            }

        worst_cand = min(active_days, key=lambda x: x["net_pnl"])
        if worst_cand["net_pnl"] < 0:
            worst_cand["is_worst_day"] = True
            for cd in calendar_days:
                if cd["day"] == worst_cand["day"]:
                    cd["is_worst_day"] = True
            worst_strat = "—"
            if worst_cand["strategies"]:
                worst_strat = min(worst_cand["strategies"].items(), key=lambda kv: kv[1]["pnl"])[0]
            worst_day = {
                "day": worst_cand["day"],
                "date": worst_cand["date"],
                "weekday": worst_cand["weekday"],
                "net_pnl": worst_cand["net_pnl"],
                "return_pct": worst_cand["return_pct"],
                "trades": worst_cand["trades_count"],
                "worst_strategy": worst_strat,
            }

    total_month_pnl = round(sum(d["net_pnl"] for d in days_list), 2)
    total_month_ret = round((total_month_pnl / base_balance) * 100.0, 2) if base_balance > 0 else 0.0
    daily_wr = round((winning_days_count / active_days_count * 100.0), 1) if active_days_count > 0 else 0.0

    strategy_summary = []
    for s_name, s_data in strategy_totals.items():
        wr = round((s_data["wins"] / s_data["trades"] * 100.0), 1) if s_data["trades"] > 0 else 0.0
        s_days = [d for d in days_list if s_name in d["strategies"]]
        best_s_day = max(s_days, key=lambda x: x["strategies"][s_name]["pnl"])["day"] if s_days else None
        worst_s_day = min(s_days, key=lambda x: x["strategies"][s_name]["pnl"])["day"] if s_days else None
        strategy_summary.append({
            "strategy": s_name,
            "pnl": s_data["pnl"],
            "trades": s_data["trades"],
            "wins": s_data["wins"],
            "losses": s_data["losses"],
            "break_even": s_data["be"],
            "winrate": wr,
            "best_day": best_s_day,
            "worst_day": worst_s_day,
        })
    strategy_summary.sort(key=lambda x: x["pnl"], reverse=True)

    return {
        "year": year,
        "month": month,
        "month_key": f"{year}-{month:02d}",
        "month_name": month_names[month - 1],
        "days_elapsed": days_elapsed,
        "total_days_in_month": total_days_in_month,
        "first_weekday_idx": first_weekday_idx,
        "today_day": today_day,
        "days": days_list,
        "calendar_days": calendar_days,
        "best_day": best_day,
        "worst_day": worst_day,
        "active_days_count": active_days_count,
        "winning_days_count": winning_days_count,
        "losing_days_count": losing_days_count,
        "neutral_days_count": neutral_days_count,
        "daily_winrate": daily_wr,
        "total_month_pnl": total_month_pnl,
        "total_month_return_pct": total_month_ret,
        "strategy_summary": strategy_summary,
    }


def build_monthly_daily_performance(
    records,
    strategy_name,
    metadata,
    now=None,
    target_year=None,
    target_month=None,
    account_balance=None,
    confirmation_audits=None,
    audit_snapshot_summaries=None,
):
    """Genera la visual y datos día a día estilo calendario con navegación histórica."""
    current = now or datetime.now(ZoneInfo("America/Santiago"))
    current = current.astimezone(ZoneInfo("America/Santiago"))

    year = int(target_year) if target_year else current.year
    month = int(target_month) if target_month else current.month

    weekday_names = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    month_names = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

    base_balance = float(account_balance) if account_balance and float(account_balance) > 0 else 10000.0

    # 1. Agrupar por setup lógico
    groups = {}
    seen = set()
    for row in records:
        identity = row.get("id")
        if identity is not None:
            if identity in seen:
                continue
            seen.add(identity)
        meta = metadata(row) or {}
        key = (
            row.get("source"),
            row.get("broker"),
            row.get("instrument"),
            strategy_name(row),
            str(meta.get("parent_execution_key") or row.get("execution_key") or identity),
        )
        groups.setdefault(key, []).append(row)

    # 2. Extraer operaciones completas cerradas con fecha y día exactos
    logical_ops = []
    for key, rows in groups.items():
        if any(str(r.get("status")).upper() != "CLOSED" for r in rows):
            continue
        try:
            pnl_list = [float(r["net_pnl"]) for r in rows]
            if not all(math.isfinite(p) for p in pnl_list):
                continue
            dates = []
            for r in rows:
                raw_exit = r.get("exit_time")
                if not raw_exit:
                    continue
                t = datetime.fromisoformat(str(raw_exit).replace("Z", "+00:00"))
                if t.tzinfo is None:
                    t = t.replace(tzinfo=ZoneInfo("UTC"))
                dates.append(t.astimezone(ZoneInfo("America/Santiago")))
            if not dates:
                continue
            end = max(dates)
            net_pnl = round(sum(pnl_list), 2)
            strat = key[3] or "SMC"
            asset = key[2] or "SIN_ACTIVO"
            first_row = rows[0]
            first_meta = metadata(first_row) or {}
            source_id = first_row.get("source_trade_id") or first_row.get("id")

            # Auditoría técnica para este trade
            entry_audit = confirmation_audits.get(str(source_id), {}) if confirmation_audits else {}
            if not entry_audit:
                for r in rows:
                    if r.get("confirmation_audit"):
                        entry_audit = r.get("confirmation_audit")
                        break
                    if r.get("confirmation_decision"):
                        entry_audit = {
                            "decision": r.get("confirmation_decision"),
                            "score": r.get("confirmation_score"),
                            "passed": r.get("passed_confirmations") or [],
                            "missing": r.get("missing_confirmations") or [],
                            "critical_failures": r.get("critical_confirmation_failures") or [],
                            "chart_pattern_confirmed": r.get("chart_pattern_confirmed"),
                            "chart_pattern_name": r.get("chart_pattern_name"),
                        }
                        break

            snap_sum = audit_snapshot_summaries.get(str(source_id), {}) if audit_snapshot_summaries else {}
            snap_count = snap_sum.get("count", 0) if isinstance(snap_sum, dict) else (first_row.get("entry_vs_now_snapshot_count") or 0)

            logical_ops.append({
                "year": end.year,
                "month": end.month,
                "day": end.day,
                "datetime": end.isoformat(),
                "time_str": end.strftime("%H:%M:%S"),
                "date_str": end.strftime("%Y-%m-%d"),
                "strategy": strat,
                "asset": asset,
                "net_pnl": net_pnl,
                "is_win": net_pnl > 0.001,
                "is_loss": net_pnl < -0.001,
                "is_be": abs(net_pnl) <= 0.001,
                "rows_count": len(rows),
                "trade_id": first_row.get("id"),
                "source_trade_id": source_id,
                "ticket": first_row.get("broker_position_ticket"),
                "direction": first_row.get("direction"),
                "leg": first_meta.get("trade_leg") or first_row.get("leg") or "—",
                "realized_rr": first_row.get("realized_rr"),
                "status": first_row.get("status"),
                "classification": first_row.get("classification"),
                "pnl_percent": round((net_pnl / base_balance) * 100.0, 2) if base_balance > 0 else 0.0,
                # Datos completos de auditoría técnica
                "confirmation_decision": entry_audit.get("decision") or first_row.get("confirmation_decision"),
                "confirmation_score": entry_audit.get("score") if entry_audit.get("score") is not None else first_row.get("confirmation_score"),
                "passed_confirmations": entry_audit.get("passed") or first_row.get("passed_confirmations") or [],
                "missing_confirmations": entry_audit.get("missing") or first_row.get("missing_confirmations") or [],
                "critical_confirmation_failures": entry_audit.get("critical_failures") or first_row.get("critical_confirmation_failures") or [],
                "chart_pattern_confirmed": bool(entry_audit.get("chart_pattern_confirmed") or first_row.get("chart_pattern_confirmed")),
                "chart_pattern_name": entry_audit.get("chart_pattern_name") or first_row.get("chart_pattern_name"),
                "entry_vs_now_snapshot_count": snap_count,
            })
        except Exception:
            continue

    # Ordenar todas las operaciones lógicas de más reciente a más antigua
    logical_ops.sort(key=lambda op: str(op.get("datetime") or op.get("time_str") or ""), reverse=True)

    # 3. Detectar todos los meses disponibles en el historial
    all_month_tuples = sorted(
        list({(op["year"], op["month"]) for op in logical_ops} | {(current.year, current.month)}),
        reverse=True,
    )
    available_months = [
        {
            "key": f"{y}-{m:02d}",
            "year": y,
            "month": m,
            "label": f"{month_names[m - 1]} {y}",
            "is_current": bool(y == current.year and m == current.month),
        }
        for y, m in all_month_tuples
    ]

    # Precalcular el mapa de todos los meses para navegación instantánea
    all_months_data = {}
    for y, m in all_month_tuples:
        m_key = f"{y}-{m:02d}"
        all_months_data[m_key] = _calculate_single_month_performance(
            y, m, logical_ops, current, base_balance, month_names, weekday_names
        )

    # El mes objetivo
    target_key = f"{year}-{month:02d}"
    if target_key in all_months_data:
        target_month_data = dict(all_months_data[target_key])
    else:
        target_month_data = _calculate_single_month_performance(
            year, month, logical_ops, current, base_balance, month_names, weekday_names
        )

    target_month_data["available_months"] = available_months
    target_month_data["all_months"] = all_months_data
    target_month_data["account_balance"] = base_balance
    target_month_data["current_date"] = current.strftime("%Y-%m-%d")
    target_month_data["current_day"] = current.day

    return target_month_data


def build_period_performance(records, strategy_name, metadata, now=None):
    current = now or datetime.now(ZoneInfo("America/Santiago"))
    current = current.astimezone(ZoneInfo("America/Santiago"))
    groups = {}
    seen = set()
    excluded = 0
    for row in records:
        identity = row.get("id")
        if identity is not None:
            if identity in seen:
                continue
            seen.add(identity)
        meta = metadata(row)
        key = (
            row.get("source"),
            row.get("broker"),
            row.get("instrument"),
            strategy_name(row),
            str(meta.get("parent_execution_key") or row.get("execution_key") or identity),
        )
        groups.setdefault(key, []).append(row)
    operations = []
    for key, rows in groups.items():
        if any(str(r.get("status")).upper() != "CLOSED" for r in rows):
            continue
        try:
            pnl = [float(r["net_pnl"]) for r in rows]
            if not all(math.isfinite(p) for p in pnl):
                raise ValueError()
            dates = []
            for r in rows:
                t = datetime.fromisoformat(str(r["exit_time"]).replace("Z", "+00:00"))
                if t.tzinfo is None:
                    t = t.replace(tzinfo=ZoneInfo("UTC"))
                dates.append(t.astimezone(ZoneInfo("America/Santiago")))
            end = max(dates)
            operations.append(dict(year=end.year, month=end.month, strategy=key[3], asset=key[2] or "SIN_ACTIVO", net_pnl=sum(pnl)))
        except (KeyError, TypeError, ValueError):
            excluded += 1

    years_list = list(
        range(
            max([current.year] + [o["year"] for o in operations]),
            min([current.year] + [o["year"] for o in operations]) - 1,
            -1,
        )
    )

    monthly_daily = build_monthly_daily_performance(records, strategy_name, metadata, now=now)

    return dict(
        timezone="America/Santiago",
        basis="Cierre final de operación; TP1 y runner agrupados",
        current_year=current.year,
        current_month=current.month,
        years=years_list,
        operations=operations,
        excluded_incomplete_data=excluded,
        monthly_daily_performance=monthly_daily,
    )
