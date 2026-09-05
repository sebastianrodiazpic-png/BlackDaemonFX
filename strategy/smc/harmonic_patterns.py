"""Detección conservadora de patrones armónicos sobre swings confirmados.

No utiliza librerías externas: trabaja con los últimos cinco pivotes X-A-B-C-D
confirmados y tolerancias configurables sobre las relaciones de Fibonacci.
Está diseñada como confirmación/confluencia, no como señal independiente.

Reconoce cuatro familias clasicas: GARTLEY, BAT, BUTTERFLY y CRAB. Cada una se
define por un juego de proporciones de Fibonacci entre los cinco puntos.

Vinculaciones:
- Lo importa `strategy.smc.confirmation_engine`, que llama a
  `detect_harmonic_confirmation` y suma `harmonic_bonus_points` al score si el
  patron queda confirmado.
- La configuracion llega desde
  `strategy.execution.trade_pipeline.PipelineConfig` (campos `harmonic_*`).
- Consume las columnas `swing_high` / `swing_low` de
  `strategy.smc.swings.detect_swings`.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class HarmonicConfig:
    """Parametros de deteccion armonica. Inmutable para reproducibilidad.

    Campos:
    - `tolerance`: holgura admitida sobre cada relacion de Fibonacci.
    - `minimum_pattern_score`: puntuacion minima de ajuste para aceptarlo.
    - `max_swings_lookback`: cuantos pivotes alternados se consideran.
    - `max_d_age_candles`: antiguedad maxima del punto D; un patron cuyo D
      quedo lejos ya no sirve para entrar.
    - `bonus_points`: puntos que aporta al score del confirmation engine.
    - `require_pattern`: si es True su ausencia rechaza la entrada.
    """
    enabled: bool = True
    tolerance: float = 0.10
    minimum_pattern_score: float = 75.0
    max_swings_lookback: int = 12
    max_d_age_candles: int = 6
    bonus_points: float = 10.0
    require_pattern: bool = False


def _ratio(actual: float, reference: float) -> float:
    """Devuelve la proporcion absoluta entre dos tramos, evitando dividir por cero.

    Returns:
        `abs(actual) / abs(reference)`, o `0.0` si la referencia es
        practicamente nula.
    """
    if abs(reference) < 1e-12:
        return 0.0
    return abs(actual) / abs(reference)


def _near(value: float, target: float, tolerance: float) -> bool:
    """Indica si un valor cae dentro de la tolerancia absoluta del objetivo."""
    return abs(value - target) <= tolerance


def _score(ratios: list[tuple[float, float]], tolerance: float) -> float:
    """Puntua de 0 a 100 el ajuste de unas proporciones a sus objetivos.

    Cada error se normaliza por la tolerancia y se recorta a 2.0, de modo que
    una desviacion muy grande no hunda por si sola toda la puntuacion.

    Args:
        ratios: lista de pares `(valor_real, valor_objetivo)`.
        tolerance: tolerancia de referencia.

    Returns:
        Puntuacion acotada al rango 0-100; `0.0` si la lista viene vacia.
    """
    if not ratios:
        return 0.0
    errors = [min(abs(actual - target) / max(tolerance, 1e-9), 2.0) for actual, target in ratios]
    score = 100.0 * (1.0 - sum(errors) / (2.0 * len(errors)))
    return max(0.0, min(100.0, score))


def _alternating_swings(data: pd.DataFrame, max_swings: int) -> list[dict[str, Any]]:
    """Extrae la secuencia de pivotes ALTERNADOS maximo-minimo-maximo...

    Un patron armonico exige que X-A-B-C-D alternen de tipo. Esta funcion
    normaliza los pivotes crudos: cuando aparecen varios consecutivos del
    mismo tipo conserva solo el mas extremo (el maximo mas alto o el minimo
    mas bajo), colapsandolos en uno.

    Args:
        data: DataFrame con `time`, `high`, `low`, `swing_high`, `swing_low`.
        max_swings: cuantos pivotes finales devolver.

    Returns:
        Lista de dicts con `index`, `time`, `type` (`"H"` o `"L"`) y `price`,
        ordenada cronologicamente. Devuelve lista vacia si faltan columnas o
        no hay datos.

    Vinculaciones:
    - La usa `detect_harmonic_confirmation` en este mismo modulo.
    """
    if data.empty:
        return []
    required = {"time", "high", "low", "swing_high", "swing_low"}
    if not required.issubset(data.columns):
        return []

    points: list[dict[str, Any]] = []
    for idx, row in data.iterrows():
        if bool(row.get("swing_high", False)):
            points.append({"index": int(idx), "time": row["time"], "type": "H", "price": float(row["high"])})
        if bool(row.get("swing_low", False)):
            points.append({"index": int(idx), "time": row["time"], "type": "L", "price": float(row["low"])})

    points.sort(key=lambda x: x["index"])
    # Elimina pivotes consecutivos del mismo tipo conservando el extremo más útil.
    filtered: list[dict[str, Any]] = []
    for point in points:
        if not filtered or filtered[-1]["type"] != point["type"]:
            filtered.append(point)
            continue
        if point["type"] == "H" and point["price"] >= filtered[-1]["price"]:
            filtered[-1] = point
        elif point["type"] == "L" and point["price"] <= filtered[-1]["price"]:
            filtered[-1] = point
    return filtered[-max_swings:]


def _evaluate_pattern(name: str, x: float, a: float, b: float, c: float, d: float, tolerance: float, direction: str) -> tuple[bool, float, dict[str, float]]:
    """Comprueba si cinco puntos encajan en un patron armonico concreto.

    Calcula las cuatro proporciones caracteristicas (AB/XA, BC/AB, CD/BC y
    AD/XA) y las contrasta con los rangos de la familia solicitada. Ademas
    exige coherencia geometrica: en un patron alcista el punto D debe quedar
    por debajo de C y de A, y al reves en uno bajista.

    La validez y la puntuacion se calculan por separado: la validez usa los
    rangos ampliados con la tolerancia, mientras que el score mide cuan cerca
    esta cada proporcion del CENTRO de su rango. Por eso un patron puede ser
    valido y aun asi puntuar bajo.

    Args:
        name: `GARTLEY`, `BAT`, `BUTTERFLY` o `CRAB`.
        x, a, b, c, d: precios de los cinco pivotes.
        tolerance: holgura sobre los rangos de Fibonacci.
        direction: `"bullish"` o `"bearish"`.

    Returns:
        Tupla `(valido, score, ratios)`. Si algun tramo es degenerado (de
        longitud casi nula) devuelve `(False, 0.0, {})`.

    Vinculaciones:
    - La llama `detect_harmonic_confirmation` en este mismo modulo.
    """
    xa = a - x
    ab = b - a
    bc = c - b
    if min(abs(xa), abs(ab), abs(bc), abs(d - c)) <= 1e-12:
        return False, 0.0, {}

    r_ab_xa = _ratio(ab, xa)
    r_bc_ab = _ratio(bc, ab)
    r_cd_bc = _ratio(d - c, bc)
    r_ad_xa = _ratio(d - a, xa)

    # Relaciones estándar aproximadas. Las relaciones de B/C/CD son rangos,
    # mientras que la extensión XA->D define la PRZ principal del patrón.
    patterns = {
        "GARTLEY": {
            "ab_xa": (0.618, 0.618), "bc_ab": (0.382, 0.886),
            "cd_bc": (1.13, 1.618), "ad_xa": (0.786, 0.786),
        },
        "BAT": {
            "ab_xa": (0.382, 0.50), "bc_ab": (0.382, 0.886),
            "cd_bc": (1.618, 2.618), "ad_xa": (0.886, 0.886),
        },
        "BUTTERFLY": {
            "ab_xa": (0.786, 0.786), "bc_ab": (0.382, 0.886),
            "cd_bc": (1.618, 2.618), "ad_xa": (1.272, 1.272),
        },
        "CRAB": {
            "ab_xa": (0.382, 0.618), "bc_ab": (0.382, 0.886),
            "cd_bc": (2.24, 3.618), "ad_xa": (1.618, 1.618),
        },
    }
    targets = patterns[name]
    actuals = {
        "ab_xa": r_ab_xa, "bc_ab": r_bc_ab,
        "cd_bc": r_cd_bc, "ad_xa": r_ad_xa,
    }

    def in_range(value: float, bounds: tuple[float, float]) -> bool:
        """Comprueba si un valor cae en el rango ampliado por la tolerancia."""
        lo, hi = bounds
        width = max(hi - lo, 0.0)
        return (lo - tolerance) <= value <= (hi + tolerance)

    valid = all(in_range(actuals[key], bounds) for key, bounds in targets.items())
    if direction == "bullish" and not (d < c and d < a):
        valid = False
    if direction == "bearish" and not (d > c and d > a):
        valid = False

    # Score de ajuste: 100 si está en el centro del rango; se penaliza de forma
    # gradual fuera del centro, pero la validez siempre respeta las tolerancias.
    component_scores = []
    for key, (lo, hi) in targets.items():
        target = (lo + hi) / 2.0
        scale = max((hi - lo) / 2.0, tolerance, 1e-9)
        error = abs(actuals[key] - target) / scale
        component_scores.append(max(0.0, 1.0 - min(error, 1.0)))
    score = 100.0 * sum(component_scores) / len(component_scores)
    ratios = {
        "AB_XA": r_ab_xa, "BC_AB": r_bc_ab,
        "CD_BC": r_cd_bc, "AD_XA": r_ad_xa,
    }
    return valid, score, ratios


def detect_harmonic_confirmation(
    data: pd.DataFrame,
    direction: str,
    config: HarmonicConfig | None = None,
    zone_low: float | None = None,
    zone_high: float | None = None,
    confirmation_index: int | None = None,
) -> dict[str, Any]:
    """Devuelve el mejor patrón armónico confirmado en los swings disponibles.

    Proceso: obtiene la secuencia de pivotes alternados, prueba todas las
    ventanas de cinco puntos consecutivos contra las cuatro familias y se
    queda con el candidato de mayor puntuacion que ademas cumpla los filtros
    de antiguedad y de zona.

    Args:
        data: DataFrame con OHLC y columnas de pivote.
        direction: direccion buscada; se normaliza a `bullish` o `bearish`.
        config: parametros; si es `None` usa los de fabrica.
        zone_low: limite inferior de la zona donde debe caer el punto D.
        zone_high: limite superior de esa zona. Sirve para exigir que la PRZ
            del patron coincida con el Order Block.
        confirmation_index: indice de la vela de confirmacion, usado para
            medir la antiguedad del punto D contra `max_d_age_candles`.

    Returns:
        Dict con `harmonic_enabled`, `harmonic_confirmed`, `harmonic_pattern`,
        `harmonic_direction`, `harmonic_score`, `harmonic_bonus`, los tiempos
        de los cinco puntos, `harmonic_ratios` y
        `harmonic_rejection_reason`.

        Motivos de rechazo posibles: `HARMONIC_DISABLED`,
        `INSUFFICIENT_CONFIRMED_SWINGS` y los relativos a puntuacion, zona o
        antiguedad del punto D.

    Vinculaciones:
    - La llama `strategy.smc.confirmation_engine.evaluate_m5_confirmation`,
      que usa `harmonic_confirmed` para sumar el bonus y, si
      `require_harmonic` esta activo, para rechazar la entrada.
    """
    config = config or HarmonicConfig()
    result: dict[str, Any] = {
        "harmonic_enabled": bool(config.enabled),
        "harmonic_confirmed": False,
        "harmonic_pattern": None,
        "harmonic_direction": None,
        "harmonic_score": 0.0,
        "harmonic_bonus": 0.0,
        "harmonic_x_time": None,
        "harmonic_a_time": None,
        "harmonic_b_time": None,
        "harmonic_c_time": None,
        "harmonic_d_time": None,
        "harmonic_ratios": {},
        "harmonic_rejection_reason": None,
    }
    if not config.enabled:
        result["harmonic_rejection_reason"] = "HARMONIC_DISABLED"
        return result

    normalized_direction = "bullish" if str(direction).lower() in {"long", "buy", "bullish"} else "bearish"
    swings = _alternating_swings(data, max(5, int(config.max_swings_lookback)))
    if len(swings) < 5:
        result["harmonic_rejection_reason"] = "INSUFFICIENT_CONFIRMED_SWINGS"
        return result

    candidates = []
    names = ("GARTLEY", "BAT", "BUTTERFLY", "CRAB")
    for start in range(max(0, len(swings) - 8), len(swings) - 4):
        seq = swings[start:start + 5]
        types = "".join(p["type"] for p in seq)
        expected = "HLHLH" if normalized_direction == "bearish" else "LHLHL"
        if types != expected:
            continue
        x, a, b, c, d = [p["price"] for p in seq]
        if confirmation_index is not None and int(seq[-1]["index"]) > int(confirmation_index):
            continue
        if confirmation_index is not None and int(confirmation_index) - int(seq[-1]["index"]) > int(config.max_d_age_candles):
            continue
        if zone_low is not None and zone_high is not None:
            zl, zh = sorted((float(zone_low), float(zone_high)))
            zone_width = max(zh - zl, 1e-12)
            # D debe estar dentro del OB o muy cerca de su extremo (50% del ancho).
            if not (zl - 0.50 * zone_width <= d <= zh + 0.50 * zone_width):
                continue
        for name in names:
            valid, score, ratios = _evaluate_pattern(name, x, a, b, c, d, float(config.tolerance), normalized_direction)
            if valid and score >= float(config.minimum_pattern_score):
                candidates.append((score, name, seq, ratios))

    if not candidates:
        result["harmonic_rejection_reason"] = "NO_VALID_HARMONIC_PATTERN"
        return result

    score, name, seq, ratios = max(candidates, key=lambda item: item[0])
    result.update({
        "harmonic_confirmed": True,
        "harmonic_pattern": name,
        "harmonic_direction": normalized_direction,
        "harmonic_score": round(float(score), 2),
        "harmonic_bonus": float(config.bonus_points),
        "harmonic_x_time": pd.to_datetime(seq[0]["time"], utc=True).isoformat(),
        "harmonic_a_time": pd.to_datetime(seq[1]["time"], utc=True).isoformat(),
        "harmonic_b_time": pd.to_datetime(seq[2]["time"], utc=True).isoformat(),
        "harmonic_c_time": pd.to_datetime(seq[3]["time"], utc=True).isoformat(),
        "harmonic_d_time": pd.to_datetime(seq[4]["time"], utc=True).isoformat(),
        "harmonic_ratios": {k: round(float(v), 4) for k, v in ratios.items()},
        "harmonic_rejection_reason": None,
    })
    return result
