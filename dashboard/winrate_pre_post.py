"""Lógica compartida para comparar Win Rate PRE/POST mejoras (v106).

Separada de `dashboard/account_metrics.py` (que ya agrupa las operaciones en
`logical_groups`, una entrada por señal lógica) y de
`tools/winrate_pre_post_report.py` (CLI de solo lectura), para que ambos
midan exactamente lo mismo con el mismo criterio de frontera PRE/POST.

Las 3 mejoras de win rate que definen la frontera v106:
    1. Break-Even con bloqueo de ganancia real (profit lock).
    2. Filtro de horas de bajo edge en Sintéticos (con excepción de alta
       confluencia >= 90%).
    3. Salida por invalidación estructural del análisis, confirmada en velas
       M15 (sin umbral de RR de pérdida).

La frontera PRE/POST se determina por el campo `strategy_version` de cada
señal: cualquier valor cuyo número de versión (esquema `smc-vNNN-...`) sea
>= `POST_IMPROVEMENT_MIN_VERSION` se considera POST-despliegue.

Vinculaciones:
    - `dashboard.account_metrics.build_account_payload`: agrega la sección
      `winrate_pre_post` al payload de /account, alimentando este módulo con
      sus `logical_groups` ya calculados (misma agrupación TP1+runner=1).
    - `tools.winrate_pre_post_report`: CLI equivalente para consola.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict

# Versión mínima (inclusive) considerada "POST-mejoras". Cualquier
# strategy_version con un número de versión >= a este es POST; el resto,
# PRE. Se apoya en el esquema "smc-vNNN-..." ya usado en el proyecto.
POST_IMPROVEMENT_MIN_VERSION = 106

_VERSION_NUMBER_RE = re.compile(r"v(\d+)", re.IGNORECASE)


def _version_number(strategy_version):
    """Extrae el número de versión de un `strategy_version` tipo `smc-v106-...`.

    Devuelve `None` si no se encuentra el patrón `vNNN`, lo cual clasifica la
    señal como PRE por defecto (dato antiguo o de un flujo distinto, p.ej.
    `mt5-external-position`, `smc-reconciled-mt5-open`).
    """
    match = _VERSION_NUMBER_RE.search(str(strategy_version or ""))
    return int(match.group(1)) if match else None


def classify_period(strategy_version):
    """Clasifica una señal como PRE o POST según su `strategy_version`."""
    version_number = _version_number(strategy_version)
    if version_number is not None and version_number >= POST_IMPROVEMENT_MIN_VERSION:
        return "POST"
    return "PRE"


def canonical_family(instrument, bot_profile):
    """Reduce el instrumento/perfil a una familia legible para el reporte."""
    bot_profile = str(bot_profile or "").upper()
    for family in ("VOLATILITY", "BOOM", "CRASH", "STEP", "JUMP", "FLIP"):
        if bot_profile.startswith(family):
            return family
    if bot_profile:
        return bot_profile
    instrument = str(instrument or "").upper()
    for family in ("BOOM", "CRASH", "VOLATILITY", "STEP", "JUMP", "FLIP"):
        if family in instrument:
            return family
    if "GOLD" in instrument or "XAU" in instrument:
        return "GOLD"
    if len(instrument) == 6 and instrument.isalpha():
        return "FOREX"
    return "OTHER"


def win_rate(counter: Counter):
    """WR = win / (win + loss); ignora NEUTRAL en el denominador."""
    wins = counter.get("WIN", 0)
    losses = counter.get("LOSS", 0)
    decisive = wins + losses
    return (round(100.0 * wins / decisive, 1) if decisive else None), decisive


def _period_summary(rows):
    """Resume un conjunto de señales (period ya filtrado) en WR + por familia."""
    counter = Counter(r["outcome"] for r in rows)
    wr, decisive = win_rate(counter)
    by_family = defaultdict(Counter)
    for row in rows:
        by_family[row["family"]][row["outcome"]] += 1
    family_rows = []
    for family in sorted(by_family):
        fam_counter = by_family[family]
        fam_wr, fam_decisive = win_rate(fam_counter)
        family_rows.append({
            "family": family,
            "outcome_counts": dict(fam_counter),
            "win_rate": fam_wr,
            "decisive": fam_decisive,
        })
    return {
        "signal_count": len(rows),
        "outcome_counts": dict(counter),
        "win_rate": wr,
        "decisive": decisive,
        "by_family": family_rows,
    }


def build_pre_post_summary(signal_rows):
    """Payload PRE/POST a partir de filas de señal lógica ya construidas.

    Args:
        signal_rows: iterable de dicts, cada uno con al menos `outcome`
            ("WIN"/"LOSS"/"NEUTRAL"), `strategy_version` y `family`.

    Returns:
        dict con `pre`, `post` (forma de `_period_summary`),
        `delta_win_rate_pp` (POST - PRE en puntos porcentuales, o `None` si
        falta algún lado) y `post_sample_small` (True si la muestra POST
        decisiva tiene menos de 20 señales, umbral orientativo).
    """
    pre_rows = [r for r in signal_rows if classify_period(r.get("strategy_version")) == "PRE"]
    post_rows = [r for r in signal_rows if classify_period(r.get("strategy_version")) == "POST"]
    pre_summary = _period_summary(pre_rows)
    post_summary = _period_summary(post_rows)

    delta = None
    if pre_summary["win_rate"] is not None and post_summary["win_rate"] is not None:
        delta = round(post_summary["win_rate"] - pre_summary["win_rate"], 1)

    return {
        "post_improvement_min_version": POST_IMPROVEMENT_MIN_VERSION,
        "pre": pre_summary,
        "post": post_summary,
        "delta_win_rate_pp": delta,
        "post_sample_small": post_summary["decisive"] < 20,
    }
