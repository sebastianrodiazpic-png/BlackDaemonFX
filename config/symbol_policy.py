"""Politica de direccion permitida por instrumento sintetico.

Los indices Boom y Crash de Deriv tienen una asimetria estructural: Boom sube
con saltos bruscos y cae despacio, y Crash al reves. Operar contra el salto
significa arriesgarse a un movimiento instantaneo imposible de gestionar, asi
que la politica solo autoriza BUY en Boom y SELL en Crash.

Modulo puro, sin estado ni dependencias externas.

Vinculaciones:
    - `strategy.execution.live_trading_engine`, `multi_timeframe` y
      `trade_pipeline` consultan `is_direction_allowed` antes de admitir una
      senal; el rechazo aparece como `DIRECTION_POLICY_BLOCKED`.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SymbolDirectionPolicy:
    """Politica inmutable de un simbolo.

    Attributes:
        symbol: nombre tal como se recibio.
        category: `boom`, `crash` u `other`.
        allowed_direction: `BUY`, `SELL` o `None` si no hay restriccion.
        reason: codigo que se propaga a los diagnosticos.
    """

    symbol: str
    category: str
    allowed_direction: str | None
    reason: str


def classify_synthetic_symbol(symbol: str) -> str:
    """Clasifica el simbolo por su nombre en `boom`, `crash` u `other`.

    Exige exclusividad ('boom' sin 'crash' y viceversa) para que un nombre que
    contuviera ambos terminos no se clasificara mal y acabara autorizando una
    direccion peligrosa.
    """
    name = str(symbol or '').strip().lower()
    if 'boom' in name and 'crash' not in name:
        return 'boom'
    if 'crash' in name and 'boom' not in name:
        return 'crash'
    return 'other'


def get_symbol_direction_policy(symbol: str) -> SymbolDirectionPolicy:
    """Devuelve la politica del simbolo.

    Boom -> solo BUY (`BOOM_BUY_ONLY`), Crash -> solo SELL
    (`CRASH_SELL_ONLY`), cualquier otro -> sin restriccion.
    """
    category = classify_synthetic_symbol(symbol)
    if category == 'boom':
        return SymbolDirectionPolicy(
            symbol=str(symbol), category=category, allowed_direction='BUY',
            reason='BOOM_BUY_ONLY',
        )
    if category == 'crash':
        return SymbolDirectionPolicy(
            symbol=str(symbol), category=category, allowed_direction='SELL',
            reason='CRASH_SELL_ONLY',
        )
    return SymbolDirectionPolicy(
        symbol=str(symbol), category=category, allowed_direction=None,
        reason='NO_DIRECTION_RESTRICTION',
    )


def normalize_direction(direction: str | None) -> str | None:
    """Normaliza a `BUY`/`SELL`, aceptando los alias `LONG`/`SHORT`.

    Returns:
        `None` si el valor no es reconocible; el llamador debe tratar ese caso
        como direccion no autorizada, nunca como "sin restriccion".
    """
    value = str(direction or '').upper()
    aliases = {'LONG': 'BUY', 'SHORT': 'SELL'}
    value = aliases.get(value, value)
    return value if value in {'BUY', 'SELL'} else None


def is_direction_allowed(symbol: str, direction: str | None) -> bool:
    """Puerta de decision: ¿puede operarse este simbolo en esa direccion?

    Devuelve `False` ante una direccion irreconocible (criterio conservador:
    ante la duda no se opera).
    """
    policy = get_symbol_direction_policy(symbol)
    normalized = normalize_direction(direction)
    return normalized is not None and (
        policy.allowed_direction is None or normalized == policy.allowed_direction
    )


def direction_policy_diagnostics(symbol: str, direction: str | None = None) -> dict:
    """Version explicable de la decision, para logs y auditoria.

    Returns:
        dict con simbolo, categoria, direccion permitida, direccion solicitada,
        el codigo de motivo y `allowed`. Este ultimo es `None` cuando no se
        pregunto por ninguna direccion concreta, distinto de `False`.
    """
    policy = get_symbol_direction_policy(symbol)
    normalized = normalize_direction(direction)
    return {
        'symbol': policy.symbol,
        'category': policy.category,
        'allowed_direction': policy.allowed_direction,
        'requested_direction': normalized,
        'policy_reason': policy.reason,
        'allowed': None if normalized is None else is_direction_allowed(symbol, normalized),
    }
