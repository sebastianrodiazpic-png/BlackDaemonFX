"""Contrato canónico de velas y ticks para todas las estrategias."""

from dataclasses import dataclass
from typing import Any, Mapping

import pandas as pd


CANONICAL_CANDLE_COLUMNS = (
    "time", "open", "high", "low", "close", "tick_volume", "spread", "real_volume",
)
TIMEFRAME_SECONDS = {
    "M1": 60, "M2": 120, "M3": 180, "M4": 240, "M5": 300,
    "M10": 600, "M15": 900, "M30": 1800, "H1": 3600,
    "H2": 7200, "H4": 14400, "D1": 86400,
}


class MarketDataValidationError(RuntimeError):
    """Deriv respondió, pero los datos no cumplen el contrato."""


@dataclass(frozen=True)
class MarketDataIdentity:
    execution_symbol: str
    native_symbol: str
    source: str


def timeframe_seconds(timeframe):
    key = str(timeframe).upper().strip()
    if key not in TIMEFRAME_SECONDS:
        raise ValueError(f"Timeframe Deriv no soportado: {timeframe}")
    return int(TIMEFRAME_SECONDS[key])


def normalize_candles(rows: Any, *, identity: MarketDataIdentity, timeframe: str):
    frame = rows.copy() if isinstance(rows, pd.DataFrame) else pd.DataFrame(rows)
    if frame.empty:
        raise MarketDataValidationError(
            f"{identity.source} no devolvió velas para {identity.native_symbol}"
        )
    required = {"time", "open", "high", "low", "close"}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise MarketDataValidationError(f"Respuesta Deriv incompleta: faltan {missing}")
    numeric = ["open", "high", "low", "close"]
    for column in numeric:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["time"] = pd.to_datetime(frame["time"], utc=True, errors="coerce")
    frame = frame.dropna(subset=["time", *numeric])
    frame = frame.drop_duplicates(subset=["time"], keep="last")
    frame = frame.sort_values("time").reset_index(drop=True)
    if frame.empty:
        raise MarketDataValidationError("Deriv devolvió velas sin filas válidas")
    invalid = (
        (frame["high"] < frame[["open", "close", "low"]].max(axis=1))
        | (frame["low"] > frame[["open", "close", "high"]].min(axis=1))
        | (frame[numeric].min(axis=1) <= 0)
    )
    if bool(invalid.any()):
        raise MarketDataValidationError(
            f"OHLC inválido para {identity.native_symbol} @ {frame.loc[invalid, 'time'].iloc[0]}"
        )
    for column in ("tick_volume", "spread", "real_volume"):
        if column not in frame:
            frame[column] = 0.0
        frame[column] = pd.to_numeric(frame[column], errors="coerce").fillna(0.0)
    if "complete" not in frame:
        frame["complete"] = True
    frame["complete"] = frame["complete"].fillna(False).astype(bool)
    frame = frame[[*CANONICAL_CANDLE_COLUMNS, "complete"]]
    frame.attrs.update({
        "market_data_source": identity.source,
        "execution_symbol": identity.execution_symbol,
        "native_symbol": identity.native_symbol,
        "timeframe": str(timeframe).upper(),
        "volume_reliable": bool(
            frame["real_volume"].sum() > 0 or frame["tick_volume"].sum() > 0
        ),
    })
    return frame


def normalize_tick(payload: Mapping[str, Any], *, identity: MarketDataIdentity):
    bid = float(payload.get("bid") or payload.get("last") or 0.0)
    ask = float(payload.get("ask") or payload.get("last") or 0.0)
    last = float(payload.get("last") or ((bid + ask) / 2 if bid and ask else bid or ask))
    if bid <= 0 or ask <= 0 or last <= 0 or ask + 1e-12 < bid:
        raise MarketDataValidationError(
            f"Tick inválido para {identity.native_symbol}: bid={bid}, ask={ask}, last={last}"
        )
    timestamp = pd.to_datetime(
        payload.get("time") or payload.get("timestamp") or pd.Timestamp.now(tz="UTC"),
        utc=True,
        errors="coerce",
    )
    if pd.isna(timestamp):
        raise MarketDataValidationError(f"Tick sin timestamp para {identity.native_symbol}")
    return {
        "symbol": identity.execution_symbol,
        "native_symbol": identity.native_symbol,
        "source": identity.source,
        "time": timestamp,
        "bid": bid,
        "ask": ask,
        "last": last,
        "volume": float(payload.get("volume") or 0.0),
    }
