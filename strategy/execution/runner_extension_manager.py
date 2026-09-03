from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from strategy.smc.swings import detect_swings
from strategy.smc.choch_bos import detect_choch_bos


@dataclass(frozen=True)
class RunnerExtensionDecision:
    continue_runner: bool
    reason: str
    diagnostics: dict[str, Any]


def rr_price(entry_price: float, initial_stop_loss: float, direction: str, rr: float) -> float:
    entry = float(entry_price)
    stop = float(initial_stop_loss)
    risk = abs(entry - stop)
    if risk <= 0:
        raise ValueError("Riesgo inicial inválido para calcular precio RR.")
    return entry + risk * float(rr) if str(direction).upper() == "BUY" else entry - risk * float(rr)


def evaluate_runner_continuation(
    candles: pd.DataFrame,
    *,
    direction: str,
    stage_rr: float,
) -> RunnerExtensionDecision:
    """Evalúa si un RUNNER que ya alcanzó 2R/3R conserva estructura suficiente.

    Gating:
    - un CHOCH contrario reciente invalida la extensión;
    - el último evento estructural no puede ser contrario;
    - el cierre debe respetar el último swing protector;
    - al menos una de dos condiciones de continuidad debe acompañar:
      momentum de 3 velas o BOS/CHOCH alineado reciente.

    No predice el futuro: decide si merece conservar exposición mientras el SL
    ya protege una parte importante de la ganancia.
    """
    if candles is None or candles.empty or len(candles) < 12:
        return RunnerExtensionDecision(
            False,
            "DATOS_M5_INSUFICIENTES_PARA_EXTENSION",
            {"candles": 0 if candles is None else int(len(candles)), "stage_rr": float(stage_rr)},
        )

    df = candles.copy()
    required = {"time", "open", "high", "low", "close"}
    missing = sorted(required.difference(df.columns))
    if missing:
        return RunnerExtensionDecision(
            False,
            "COLUMNAS_M5_INSUFICIENTES_PARA_EXTENSION",
            {"missing": missing, "stage_rr": float(stage_rr)},
        )

    df["time"] = pd.to_datetime(df["time"], utc=True)
    df = df.sort_values("time").drop_duplicates("time").tail(80).reset_index(drop=True)
    df = detect_swings(df, left=2, right=2)
    df = detect_choch_bos(df)

    direction = str(direction).upper()
    recent = df.tail(12).copy()
    last3 = df.tail(3).copy()
    latest = df.iloc[-1]
    close = float(latest["close"])

    aligned_event_cols = (
        ("bos_bullish", "choch_bullish")
        if direction == "BUY"
        else ("bos_bearish", "choch_bearish")
    )
    opposite_event_cols = (
        ("bos_bearish", "choch_bearish")
        if direction == "BUY"
        else ("bos_bullish", "choch_bullish")
    )

    opposite_choch_col = "choch_bearish" if direction == "BUY" else "choch_bullish"
    opposite_choch_recent = bool(last3[opposite_choch_col].fillna(False).astype(bool).any())

    latest_structure_side = None
    latest_structure_type = None
    latest_structure_time = None
    for _, row in recent.iterrows():
        for col in aligned_event_cols:
            if bool(row.get(col, False)):
                latest_structure_side = "ALIGNED"
                latest_structure_type = col
                latest_structure_time = row.get("time")
        for col in opposite_event_cols:
            if bool(row.get(col, False)):
                latest_structure_side = "OPPOSITE"
                latest_structure_type = col
                latest_structure_time = row.get("time")

    if direction == "BUY":
        swings = df[df["swing_low"].fillna(False).astype(bool)]
        protective_swing = float(swings.iloc[-1]["low"]) if not swings.empty else None
        protective_structure_ok = protective_swing is None or close > protective_swing
        prior3_high = float(df.iloc[-4:-1]["high"].max())
        momentum_ok = close > prior3_high
    else:
        swings = df[df["swing_high"].fillna(False).astype(bool)]
        protective_swing = float(swings.iloc[-1]["high"]) if not swings.empty else None
        protective_structure_ok = protective_swing is None or close < protective_swing
        prior3_low = float(df.iloc[-4:-1]["low"].min())
        momentum_ok = close < prior3_low

    aligned_structure = latest_structure_side == "ALIGNED"
    opposite_structure = latest_structure_side == "OPPOSITE"

    diagnostics = {
        "stage_rr": float(stage_rr),
        "direction": direction,
        "latest_close": close,
        "opposite_choch_recent": opposite_choch_recent,
        "latest_structure_side": latest_structure_side,
        "latest_structure_type": latest_structure_type,
        "latest_structure_time": (
            pd.Timestamp(latest_structure_time).isoformat()
            if latest_structure_time is not None and pd.notna(latest_structure_time)
            else None
        ),
        "protective_swing": protective_swing,
        "protective_structure_ok": bool(protective_structure_ok),
        "momentum_ok": bool(momentum_ok),
        "aligned_structure": bool(aligned_structure),
    }

    if opposite_choch_recent:
        return RunnerExtensionDecision(False, "CHOCH_CONTRARIO_RECIENTE", diagnostics)
    if opposite_structure:
        return RunnerExtensionDecision(False, "ULTIMA_ESTRUCTURA_ES_CONTRARIA", diagnostics)
    if not protective_structure_ok:
        return RunnerExtensionDecision(False, "SWING_PROTECTOR_INVALIDADO", diagnostics)

    continuation_votes = int(bool(momentum_ok)) + int(bool(aligned_structure))
    if continuation_votes < 1:
        return RunnerExtensionDecision(False, "SIN_MOMENTUM_NI_ESTRUCTURA_DE_CONTINUACION", diagnostics)

    diagnostics["continuation_votes"] = continuation_votes
    return RunnerExtensionDecision(True, "CONTINUACION_ESTRUCTURAL_CONFIRMADA", diagnostics)
