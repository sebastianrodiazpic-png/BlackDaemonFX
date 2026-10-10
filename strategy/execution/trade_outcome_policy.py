"""Política de clasificación del desenlace de una operación.

Reexporta desde `trade_outcome_policy` para garantizar una única fuente de
verdad en todo el sistema y eliminar código duplicado.
"""

from __future__ import annotations

from trade_outcome_policy import (
    BREAK_EVEN_RR_TOLERANCE,
    decisive_outcome,
    is_break_even_rr,
    safe_float,
)

__all__ = [
    "BREAK_EVEN_RR_TOLERANCE",
    "decisive_outcome",
    "is_break_even_rr",
    "safe_float",
]
