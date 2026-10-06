"""Utilidades de detección y normalización canónica de símbolos y contrapartes micro.

Permite identificar si dos símbolos pertenecen al mismo activo subyacente
(p. ej. EURUSD vs EURUSDmicro, XAUUSD vs XAUUSDmicro, USDJPY vs USDJPYmicro)
para aplicar reglas universales de exclusión mutua de exposición.
"""

from __future__ import annotations

import re

KNOWN_FOREX_CURRENCIES: tuple[str, ...] = (
    "USD",
    "EUR",
    "GBP",
    "JPY",
    "CHF",
    "CAD",
    "AUD",
    "NZD",
    "SEK",
    "NOK",
    "DKK",
    "SGD",
    "HKD",
    "ZAR",
    "MXN",
    "TRY",
    "PLN",
    "CNH",
    "CZK",
    "HUF",
)


def norm_symbol(symbol: str) -> str:
    """Reduce el símbolo a minúsculas y sólo caracteres alfanuméricos."""
    return re.sub(r"[^a-z0-9]", "", str(symbol or "").lower())


def forex_pair_currencies(symbol: str) -> tuple[str, str] | tuple[None, None]:
    """Descompone un símbolo Forex en sus divisas base y cotizada.

    Tolera sufijos del broker como `micro`, `.m`, `_raw`, etc.
    """
    letters = "".join(ch for ch in str(symbol or "").upper() if ch.isalpha())
    for i in range(max(1, len(letters) - 5)):
        block = letters[i : i + 6]
        if len(block) == 6 and block[:3] in KNOWN_FOREX_CURRENCIES and block[3:] in KNOWN_FOREX_CURRENCIES:
            return block[:3], block[3:]
    return None, None


def canonical_symbol_root(symbol: str) -> str:
    """Extrae la raíz canónica del activo eliminando variantes micro o sufijos del broker.

    Ejemplos:
    - 'EURUSD' -> 'EURUSD'
    - 'EURUSDmicro' -> 'EURUSD'
    - 'USDJPYmicro' -> 'USDJPY'
    - 'XAUUSDmicro' -> 'XAUUSD'
    - 'microXAUUSD' -> 'XAUUSD'
    - 'XAGUSDmicro' -> 'XAGUSD'
    - 'Step Index' -> 'STEPINDEX'
    """
    s = str(symbol or "").strip()
    if not s:
        return ""

    base, quote = forex_pair_currencies(s)
    if base and quote:
        return f"{base}{quote}"

    clean = norm_symbol(s).upper()

    if "XAU" in clean or "GOLD" in clean:
        return "XAUUSD"
    if "XAG" in clean or "SILVER" in clean:
        return "XAGUSD"
    if "US30" in clean or "WALLSTREET" in clean or "DJI" in clean:
        return "US30"
    if "NAS100" in clean or "USTECH" in clean or "NDX" in clean:
        return "USTECH100"
    if "SPX" in clean or "US500" in clean:
        return "US500"

    # Eliminación de prefijo / sufijo micro
    if clean.startswith("MICRO"):
        clean = clean[5:]
    if clean.endswith("MICRO"):
        clean = clean[:-5]
    elif clean.endswith("MIC"):
        clean = clean[:-3]
    return clean


def is_micro_symbol(symbol: str) -> bool:
    """Determina si un símbolo corresponde a una versión micro o variante reducida."""
    clean = norm_symbol(symbol).upper()
    if "MICRO" in clean or clean.endswith("MIC") or clean.endswith("M"):
        return True
    return False


def counterpart_category(symbol: str) -> str:
    """Clasifica la categoría del activo para mensajes de auditoría."""
    base, quote = forex_pair_currencies(symbol)
    if base and quote:
        return "FOREX"
    clean = norm_symbol(symbol).upper()
    if "XAU" in clean or "GOLD" in clean:
        return "GOLD"
    if "XAG" in clean or "SILVER" in clean:
        return "SILVER"
    if any(k in clean for k in ("US30", "WALLSTREET", "NAS100", "USTECH", "US500")):
        return "INDEX"
    return "MICRO_COUNTERPART"


def is_counterpart_pair(symbol1: str, symbol2: str) -> bool:
    """Determina si dos símbolos representan el mismo activo en contratos diferentes (e.g. estándar vs micro).

    Devuelve True si ambos símbolos tienen la misma raíz canónica pero son
    tickers diferentes (e.g. EURUSD y EURUSDmicro).
    """
    n1 = norm_symbol(symbol1)
    n2 = norm_symbol(symbol2)
    if not n1 or not n2 or n1 == n2:
        return False
    r1 = canonical_symbol_root(symbol1)
    r2 = canonical_symbol_root(symbol2)
    return bool(r1 and r2 and r1 == r2)


def is_same_or_counterpart_symbol(symbol1: str, symbol2: str) -> bool:
    """Determina si dos símbolos son idénticos o contrapartes del mismo activo."""
    n1 = norm_symbol(symbol1)
    n2 = norm_symbol(symbol2)
    if not n1 or not n2:
        return False
    if n1 == n2:
        return True
    return is_counterpart_pair(symbol1, symbol2)
