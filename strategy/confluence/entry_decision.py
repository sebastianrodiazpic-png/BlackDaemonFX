"""Trazabilidad de decisiones de entrada (Criterio Humano + Confluencia Tripartita + IA).

Hasta el 11-nov-2026 los trades no guardaban qué decidió el comité de admisión ni con qué datos, y los eventos
de auditoría no llevaban `execution_key`, así que no se podía unir una aprobación o un veto con su resultado.

Este módulo es lógica pura (sin MT5 ni base de datos):
- `build_entry_decision_record`: arma el registro compacto que se guarda en `trade.details.metadata.entry_decision`
  y en el payload de los eventos `HUMAN_CRITERIA_EVALUATED` / `TRIPARTITE_CONFLUENCE_EVALUATED`.
- `aggregate_decision_events` y `aggregate_trade_decisions`: resúmenes para la página /decisions.

Interruptor: DAEMONBLACKFX_ENTRY_DECISION_TRACE=0 desactiva el guardado (por defecto activo).
"""
from __future__ import annotations

import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Iterable

SCHEMA_VERSION = 1
HC_EVENT = "HUMAN_CRITERIA_EVALUATED"
TRI_EVENT = "TRIPARTITE_CONFLUENCE_EVALUATED"
VETO_PREFIXES = ("VETO_", "HUMAN_CRITERIA_")
_HC_PASS = "HUMAN_CRITERIA_PASSED"
_TRI_PASS = ("APPROVED", "BYPASS")


def normalize_strategy_name(name: str | None) -> str:
    """Normaliza nombres legados y variantes a la clave canónica de estrategia."""
    s = str(name or "").upper().strip()
    if not s or s in ("SIN_DATO", "?", "UNKNOWN"):
        return "SIN_DATO"
    if "ICT" in s or "SABRI" in s or s == "SMC":
        return "ICT"
    if "MALAYSIAN" in s or "MSNR" in s or "SNR" in s:
        return "MALAYSIAN_SNR"
    if "ORB" in s:
        return "ORB"
    if "PULLBACK" in s or "TREND" in s:
        return "TREND_PULLBACK"
    return s


def trace_enabled() -> bool:
    return os.getenv("DAEMONBLACKFX_ENTRY_DECISION_TRACE", "1").strip().lower() not in ("0", "false", "off", "no")


def _num(value: Any, digits: int = 3):
    try:
        if value is None:
            return None
        return round(float(value), digits)
    except (TypeError, ValueError):
        return None


def _as_dict(obj: Any) -> dict:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    to_dict = getattr(obj, "to_dict", None)
    if callable(to_dict):
        try:
            out = to_dict()
            return out if isinstance(out, dict) else {}
        except Exception:
            return {}
    return {}


def build_entry_decision_record(
    *,
    symbol: str,
    direction: str,
    strategy_name: str,
    signal: dict | None,
    execution_key: str | None = None,
    bot_profile: str | None = None,
    adx_used: float | None = None,
    entered: bool | None = None,
) -> dict:
    """Registro compacto y serializable de lo que decidieron los tres pilares para una señal."""
    signal = signal if isinstance(signal, dict) else {}
    hc = _as_dict(signal.get("human_criteria"))
    tri = _as_dict(signal.get("tripartite_confluence"))
    ml = signal.get("meta_label") if isinstance(signal.get("meta_label"), dict) else {}
    breakdown = hc.get("breakdown") if isinstance(hc.get("breakdown"), dict) else {}

    record: dict[str, Any] = {
        "schema": SCHEMA_VERSION,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "symbol": str(symbol),
        "direction": str(direction).upper(),
        "strategy_key": str(strategy_name).upper(),
        "bot_profile": str(bot_profile).upper() if bot_profile else None,
        "execution_key": execution_key,
        "human_criteria": {
            "action": hc.get("action"),
            "allowed": hc.get("allowed"),
            "mode": hc.get("mode"),
            "score": _num(hc.get("score"), 2),
            "grade": hc.get("grade"),
            "reason": hc.get("reason"),
            "primary_veto_factor": hc.get("primary_veto_factor"),
            "breakdown": {k: _num(v, 2) for k, v in breakdown.items()},
        } if hc else None,
        "tripartite": {
            "action": tri.get("action"),
            "allowed": tri.get("allowed"),
            "reason": tri.get("reason"),
            "strategy_pillar_ok": tri.get("strategy_pillar_ok"),
            "human_criteria_pillar_ok": tri.get("human_criteria_pillar_ok"),
            "ai_filter_pillar_ok": tri.get("ai_filter_pillar_ok"),
            "ai_probability": _num(tri.get("ai_probability")),
            "human_criteria_score": _num(tri.get("human_criteria_score"), 2),
            "is_rehabilitated_asset": tri.get("is_rehabilitated_asset"),
        } if tri else None,
        "ai": {
            "mode": ml.get("mode"),
            "probability": _num(ml.get("probability")),
            "net_expectancy_r": _num(ml.get("net_expectancy_r")),
            "allowed": ml.get("allowed"),
            "shadow": ml.get("shadow"),
            "trained": ml.get("trained"),
            "available": True,
        } if ml else {"available": False},
        "context": {
            "adx_used_by_gate": _num(adx_used, 2),
            "adx": _num(signal.get("adx"), 2),
            "regime_adx": _num(signal.get("regime_adx"), 2),
            "candle_body_ratio": _num(signal.get("candle_body_ratio")),
            "spike_danger": bool(signal.get("spike_danger", False)),
        },
    }
    auction = _as_dict(signal.get("auction_metadata"))
    if auction:
        record["auction"] = {
            "winner_strategy": auction.get("winner_strategy"),
            "winner_score": _num(auction.get("winner_score"), 2),
            "winner_grade": auction.get("winner_grade"),
            "cross_strategy_confluence": bool(auction.get("cross_strategy_confluence", False)),
            "direction_conflict": bool(auction.get("direction_conflict", False)),
        }
    if entered is not None:
        record["entered"] = bool(entered)
    return {k: v for k, v in record.items() if v is not None}


def attach_to_trade_details(details: dict | None, record: dict) -> dict:
    """Devuelve una copia de `details` con `metadata.entry_decision` (sin tocar lo demás)."""
    details = dict(details) if isinstance(details, dict) else {}
    metadata = dict(details.get("metadata") or {})
    metadata["entry_decision"] = record
    details["metadata"] = metadata
    return details


def _is_veto(action: str | None) -> bool:
    a = str(action or "")
    return a.startswith("VETO_") or (a.startswith("HUMAN_CRITERIA_") and a != _HC_PASS and not a.endswith("_OBSERVED"))


def aggregate_decision_events(rows: Iterable[dict], recent_limit: int = 60) -> dict:
    """Resume eventos de auditoría (dicts con event_time, event_type, action, instrument, reason, execution_key, payload)."""
    by_action: Counter = Counter()
    by_day_action: dict = defaultdict(Counter)
    by_symbol_veto: Counter = Counter()
    by_strategy: dict = defaultdict(Counter)
    with_key = 0
    total = 0
    recent_vetoes: list[dict] = []
    for row in rows:
        et, action = str(row.get("event_type") or ""), str(row.get("action") or "")
        if et not in (HC_EVENT, TRI_EVENT):
            continue
        total += 1
        label = f"{'CH' if et == HC_EVENT else 'TRI'}:{action}"
        by_action[label] += 1
        day = str(row.get("event_time") or "")[:10]
        by_day_action[day][label] += 1
        payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
        raw_strat = str(payload.get("strategy_key") or (payload.get("details") or {}).get("strategy") or "SIN_DATO")
        by_strategy[raw_strat][label] += 1
        norm_strat = normalize_strategy_name(raw_strat)
        if norm_strat != raw_strat:
            by_strategy[norm_strat][label] += 1
        strat = norm_strat
        if row.get("execution_key"):
            with_key += 1
        if _is_veto(action):
            by_symbol_veto[str(row.get("instrument") or "?")] += 1
            if len(recent_vetoes) < recent_limit:
                recent_vetoes.append({
                    "time": str(row.get("event_time") or "")[:19],
                    "symbol": row.get("instrument"),
                    "stage": "Criterio Humano" if et == HC_EVENT else "Tripartita",
                    "action": action,
                    "reason": str(row.get("reason") or "")[:220],
                    "strategy": strat,
                    "execution_key": row.get("execution_key"),
                })
    return {
        "total_events": total,
        "events_with_execution_key": with_key,
        "by_action": dict(by_action.most_common()),
        "by_day": {d: dict(c.most_common()) for d, c in sorted(by_day_action.items())},
        "by_strategy": {s: dict(c.most_common()) for s, c in sorted(by_strategy.items())},
        "top_veto_symbols": by_symbol_veto.most_common(15),
        "recent_vetoes": recent_vetoes,
    }


def _bucket(value: float | None, edges: tuple, labels: tuple) -> str:
    if value is None:
        return "sin dato"
    for edge, label in zip(edges, labels):
        if value < edge:
            return label
    return labels[-1]


def aggregate_trade_decisions(trades: Iterable[dict]) -> dict:
    """Resume trades (dicts con instrument, result, realized_rr, details) frente a su `entry_decision`."""
    trades = list(trades)
    with_dec = []
    for t in trades:
        meta = ((t.get("details") or {}).get("metadata") or {}) if isinstance(t.get("details"), dict) else {}
        dec = meta.get("entry_decision")
        if isinstance(dec, dict):
            with_dec.append((t, dec))

    def stats(items):
        closed = [t for t, _ in items if str(t.get("status") or "").upper() != "OPEN"]
        wins = sum(1 for t in closed if str(t.get("result") or "").upper() == "WIN")
        r = sum(float(t.get("realized_rr") or 0.0) for t in closed)
        return {"trades": len(items), "closed": len(closed), "wins": wins,
                "win_rate": round(100.0 * wins / len(closed), 1) if closed else None, "r_total": round(r, 2)}

    by_hc: dict = defaultdict(list)
    by_ai: dict = defaultdict(list)
    by_strat: dict = defaultdict(list)
    for t, d in with_dec:
        hc_score = ((d.get("human_criteria") or {}).get("score"))
        by_hc[_bucket(hc_score, (75, 80, 90), ("<75", "75-80", "80-90", ">=90"))].append((t, d))
        ai_p = ((d.get("ai") or {}).get("probability"))
        by_ai[_bucket(ai_p, (0.5, 0.6, 0.8), ("<0.50", "0.50-0.60", "0.60-0.80", ">=0.80"))].append((t, d))
        raw_s = str(d.get("strategy_key") or "?")
        by_strat[raw_s].append((t, d))
        norm_s = normalize_strategy_name(raw_s)
        if norm_s != raw_s:
            by_strat[norm_s].append((t, d))
    recent = []
    for t, d in sorted(with_dec, key=lambda x: str(x[0].get("entry_time") or ""), reverse=True)[:40]:
        tri = d.get("tripartite") or {}
        hc = d.get("human_criteria") or {}
        recent.append({
            "entry_time": str(t.get("entry_time") or "")[:19], "symbol": t.get("instrument"),
            "direction": t.get("direction"), "strategy": normalize_strategy_name(d.get("strategy_key")),
            "hc_score": hc.get("score"), "hc_grade": hc.get("grade"), "tri_action": tri.get("action"),
            "ai_probability": (d.get("ai") or {}).get("probability"),
            "adx_used": (d.get("context") or {}).get("adx_used_by_gate"),
            "status": t.get("status"), "result": t.get("result"), "realized_rr": t.get("realized_rr"),
        })
    return {
        "trades_total": len(trades),
        "trades_with_decision": len(with_dec),
        "coverage_pct": round(100.0 * len(with_dec) / len(trades), 1) if trades else None,
        "overall": stats(with_dec),
        "by_human_score": {k: stats(v) for k, v in sorted(by_hc.items())},
        "by_ai_probability": {k: stats(v) for k, v in sorted(by_ai.items())},
        "by_strategy": {k: stats(v) for k, v in sorted(by_strat.items())},
        "recent": recent,
    }
