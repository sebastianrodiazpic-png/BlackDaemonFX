"""Política de clasificación del desenlace de una operación (copia de `execution`).

Decide si una operacion cerrada cuenta como GANADORA, PERDEDORA o
BREAK-EVEN. La regla central es que el resultado se juzga primero en R
(riesgo asumido) y solo despues en dinero: un cierre a +0.05R es ruido,
no una victoria, aunque el neto monetario sea positivo.

DUPLICIDAD CONOCIDA: existe un modulo gemelo en la raiz del proyecto,
`trade_outcome_policy.py`, con la misma politica. Al cambiar una regla hay
que revisar ambos para que no diverjan.

Vinculaciones:
- Lo consumen los modulos de reporting y el motor de ejecucion para
  etiquetar operaciones cerradas.
- Las etiquetas resultantes alimentan el entrenamiento de
  `strategy.ai.training`, por lo que un cambio aqui altera el modelo.
"""

from __future__ import annotations

# v48: una salida muy próxima a 0R no representa una ventaja estadística real.
# Se conserva la tolerancia que ya existía implícitamente en las clasificadores
# anteriores, pero ahora se aplica ANTES de mirar el signo monetario.
BREAK_EVEN_RR_TOLERANCE = 0.25


def safe_float(value):
    """Convierte a float devolviendo `None` si el valor falta o no es numérico.

    Evita que un campo ausente en base de datos se cuele como 0.0 y falsee
    la clasificacion del resultado.
    """
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def is_break_even_rr(realized_rr, tolerance: float = BREAK_EVEN_RR_TOLERANCE) -> bool:
    """Indica si el R realizado queda dentro de la banda neutra de break-even.

    Args:
        realized_rr: resultado en multiplos de R.
        tolerance: media anchura de la banda neutra, +-0.25R por defecto.

    Returns:
        `True` si el resultado esta demasiado cerca de cero para considerarlo
        decisivo. Un R ausente devuelve `False`, no break-even: sin dato no se
        puede afirmar que fuera neutro.
    """
    rr = safe_float(realized_rr)
    if rr is None:
        return False
    return -abs(float(tolerance)) <= rr <= abs(float(tolerance))


def decisive_outcome(
    *,
    realized_rr=None,
    net_pnl=None,
    status=None,
    classification=None,
    tolerance: float = BREAK_EVEN_RR_TOLERANCE,
):
    """Devuelve WIN / LOSS / BREAK_EVEN / OPEN / None.

    Prioridad:
    1. OPEN nunca participa.
    2. RR dentro de ±tolerance => BREAK_EVEN, aunque PnL sea levemente +/-.
    3. Clasificación explícita de BE/emergencia => no decisión.
    4. RR fuera de la zona neutral.
    5. Sólo si RR no existe, fallback por PnL.
    """
    if str(status or "").upper() == "OPEN":
        return "OPEN"

    label = str(classification or "").upper()
    if "BREAK EVEN" in label or "PUNTO DE EQUILIBRIO" in label:
        return "BREAK_EVEN"
    if "EMERGENCIA" in label or "EMERGENCY" in label:
        return None

    rr = safe_float(realized_rr)
    if rr is not None:
        if is_break_even_rr(rr, tolerance=tolerance):
            return "BREAK_EVEN"
        return "WIN" if rr > 0 else "LOSS"

    pnl = safe_float(net_pnl)
    if pnl is None or pnl == 0:
        return "BREAK_EVEN"
    return "WIN" if pnl > 0 else "LOSS"
