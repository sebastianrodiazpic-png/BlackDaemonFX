"""Modo ranking: prioriza señales simultáneas por probabilidad y expectativa."""

from __future__ import annotations

from strategy.ai.meta_labeling import MetaLabelDecision


def rank_signals(
    decisions,
    *,
    max_signals: int | None = None,
    require_allowed: bool = True,
) -> list[dict]:
    """Ordena señales del mismo ciclo y marca cuáles se ejecutan.

    Criterio: mayor expectativa neta primero; ante empate, mayor probabilidad.
    Las señales que el filtro ya rechazó nunca ascienden en el ranking.
    """
    rows = []
    for decision in decisions or []:
        if isinstance(decision, MetaLabelDecision):
            payload = decision.to_dict()
        elif isinstance(decision, dict):
            payload = dict(decision)
        else:
            continue
        rows.append(payload)

    rows.sort(
        key=lambda item: (
            1 if item.get("allowed", True) else 0,
            float(item.get("net_expectancy_r", 0.0) or 0.0),
            float(item.get("probability", 0.0) or 0.0),
        ),
        reverse=True,
    )

    limit = None if max_signals is None else max(0, int(max_signals))
    selected = 0
    for position, row in enumerate(rows, start=1):
        row["rank"] = position
        eligible = bool(row.get("allowed", True)) or not require_allowed
        if eligible and (limit is None or selected < limit):
            row["selected"] = True
            row["rank_reason"] = "TOP_RANKED_SIGNAL"
            selected += 1
        else:
            row["selected"] = False
            row["rank_reason"] = (
                "REJECTED_BY_META_LABEL_FILTER" if not eligible
                else "LOWER_PRIORITY_THAN_SELECTED_SIGNALS"
            )
    return rows
