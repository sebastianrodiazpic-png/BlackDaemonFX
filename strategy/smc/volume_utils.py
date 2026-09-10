"""Utilidades de volumen compartidas entre estrategias.

Centraliza la selección de la mejor columna de volumen disponible en un
DataFrame de velas MT5. Antes de este módulo, la misma lógica estaba
duplicada en `strategy.orb.new_york_orb.NewYorkORBStrategy._volume_column`;
se extrajo aquí para que `strategy.smc.volume_confirmation` la reutilice sin
repetir código, y para que ORB pueda delegar en ella también.

Vinculaciones:
- La usa `strategy.orb.new_york_orb.NewYorkORBStrategy._volume_column`
  (delegado, mantiene compatibilidad hacia atrás con el nombre histórico).
- La usa `strategy.smc.volume_confirmation.detect_volume_confirmation`.
"""
from __future__ import annotations

import pandas as pd


def select_volume_column(df: pd.DataFrame) -> pd.Series:
    """Elige la mejor columna de volumen disponible en las velas.

    Preferencia: `real_volume` (solo si su suma es positiva, ya que muchos
    brokers la publican vacía), luego `tick_volume`, luego `volume`.

    Último recurso: una serie de unos, que evita que la estrategia falle por
    falta del dato. Los llamadores que necesiten distinguir "sin volumen
    fiable" deben usar `has_reliable_volume` en vez de inspeccionar la suma
    de esta serie (una serie de unos siempre suma > 0).

    Args:
        df: DataFrame de velas con alguna combinación de columnas
            `real_volume`, `tick_volume`, `volume`.

    Returns:
        Serie de floats con el volumen por vela, mismo índice que `df`.
    """
    if "real_volume" in df.columns:
        rv = pd.to_numeric(df["real_volume"], errors="coerce").fillna(0.0)
        if float(rv.sum()) > 0:
            return rv.astype(float)
    if "tick_volume" in df.columns:
        return pd.to_numeric(df["tick_volume"], errors="coerce").fillna(0.0).astype(float)
    if "volume" in df.columns:
        return pd.to_numeric(df["volume"], errors="coerce").fillna(0.0).astype(float)
    return pd.Series([1.0] * len(df), index=df.index, dtype=float)


def has_reliable_volume(df: pd.DataFrame) -> bool:
    """Indica si `df` trae alguna columna de volumen real (no el fallback de unos)."""
    for column in ("real_volume", "tick_volume", "volume"):
        if column in df.columns:
            series = pd.to_numeric(df[column], errors="coerce").fillna(0.0)
            if float(series.sum()) > 0:
                return True
    return False
