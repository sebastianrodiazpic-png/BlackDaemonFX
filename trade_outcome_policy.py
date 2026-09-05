"""Política única para clasificar el desenlace de una operación cerrada.

Existe para que WIN, LOSS y BREAK_EVEN signifiquen EXACTAMENTE lo mismo en
todo el sistema: metricas de la cuenta, informes en Excel y etiquetas de
entrenamiento de la IA. Si cada consumidor aplicase su propio criterio, el
win rate mostrado y el que aprende el modelo divergirian.

Idea central (v48): una salida muy proxima a 0R no es ni ganancia ni perdida
real, sino ruido. Por eso se aplica una banda neutral de +-0.25R ANTES de
mirar el signo monetario.

Vinculaciones:
- Existe un modulo homonimo en `strategy/execution/trade_outcome_policy.py`;
  comprobar cual se esta importando antes de tocar nada.
- Lo consumen los modulos de reporte y las metricas de la pantalla Cuenta.
"""

from __future__ import annotations

# v48: una salida muy próxima a 0R no representa una ventaja estadística real.
# Se conserva la tolerancia que ya existía implícitamente en las clasificadores
# anteriores, pero ahora se aplica ANTES de mirar el signo monetario.
BREAK_EVEN_RR_TOLERANCE = 0.25


def safe_float(value):
    """Convierte a float devolviendo `None` ante valores nulos o inválidos.

    Distingue a proposito el "no hay dato" (`None`) del cero, porque
    `decisive_outcome` los trata de forma muy distinta: sin RR recurre al
    PnL, mientras que un RR de cero es break-even.
    """
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def is_break_even_rr(realized_rr, tolerance: float = BREAK_EVEN_RR_TOLERANCE) -> bool:
    """Indica si el R realizado cae dentro de la banda neutral.

    La comparacion usa el valor absoluto de la tolerancia, asi que pasar un
    umbral negativo no invierte el criterio.

    Returns:
        True si `-tolerance <= rr <= tolerance`. Un RR ausente devuelve
        False, no break-even, para que la decision recaiga en el PnL.
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

    El ORDEN de esas reglas es lo esencial: se prefiere el RR sobre el PnL
    porque es comparable entre instrumentos y tamanos de posicion.

    Distincion critica entre los dos valores no decisivos:
    - `"OPEN"`: la operacion sigue viva, aun no hay desenlace.
    - `None`: hubo cierre, pero no debe contar en las estadisticas. Es el
      caso de los cierres de emergencia, provocados por el gestor y no por
      la tesis del trade.

    Args:
        realized_rr: R realizado; fuente preferente.
        net_pnl: resultado monetario, usado solo si falta el RR.
        status: estado de la operacion; `OPEN` corta de inmediato.
        classification: etiqueta textual del cierre.
        tolerance: media anchura de la banda neutral, en R.

    Returns:
        `"WIN"`, `"LOSS"`, `"BREAK_EVEN"`, `"OPEN"` o `None`.
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
