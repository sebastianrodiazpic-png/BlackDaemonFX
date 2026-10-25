"""Escenario MSNR de confirmación H4→H1 (vídeos Alchemist; validado en replay el 20-oct-2026).

Regla (solo velas cerradas, idéntica a tools/research_msnr_storyline_h4h1.py):
1. Niveles H4 = picos y valles de los cierres (gráfico de líneas, radio 2), disponibles cuando se confirman.
2. Una vela H4 RECHAZA un nivel: en venta abre por debajo, su máximo lo toca y cierra por debajo (espejo en compra).
3. En las 4 velas H1 que empiezan al cierre de esa H4, la PRIMERA que cierra rompiendo el último nivel open-close de
   H1 (dos velas del mismo color, nivel = cierre de la 1.ª, últimas 30 velas) en el sentido de la operación dispara la
   entrada, que se ejecuta en la H1 siguiente.
4. SL tras el extremo de la H4 del rechazo ± 0,1 ATR(14) H1 (+ spread en venta).

Replay fiel 2 años, 37 sintéticos, tope spread/SL 2 %: 18.595 operaciones, +0,029 R/t (y0 +0,026 / y1 +0,031);
con la política de dirección del bot (Boom solo BUY, Crash solo SELL) +0,017 R/t (y0 +0,017 / y1 +0,018).
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

H4H1_SCENARIO = "ESC_5_H4H1_CONFIRMATION"
H4H1_CONFIRMATION = "H4_REJECT_H1_OPEN_CLOSE_BREAK"
H4H1_STRATEGY_VERSION = "msnr-h4h1-v1"
H4 = pd.Timedelta(hours=4)
H1 = pd.Timedelta(hours=1)


def line_levels(frame: pd.DataFrame, delta: pd.Timedelta, radius: int = 2) -> list[tuple[pd.Timestamp, float]]:
    """Picos/valles de los cierres con el momento en que quedan confirmados (cierre de la vela i + radius)."""
    closes = frame["close"].to_numpy(float)
    times = pd.to_datetime(frame["time"], utc=True)
    out = []
    for i in range(radius, len(frame) - radius):
        win = closes[i - radius:i + radius + 1]
        if closes[i] == win.max() or closes[i] == win.min():
            out.append((times.iloc[i + radius] + delta, float(closes[i])))
    return out


def rejected_levels(bar, levels, direction: str) -> list[float]:
    if direction == "SELL":
        return [lv for lv in levels if bar.open < lv <= bar.high and bar.close < lv]
    return [lv for lv in levels if bar.open > lv >= bar.low and bar.close > lv]


def open_close_break(o: np.ndarray, c: np.ndarray, j: int, direction: str, lookback: int = 30) -> float | None:
    """Nivel open-close roto por la vela j (None si no rompe)."""
    lo = max(0, j - lookback)
    pairs = [c[m - 1] for m in range(lo + 1, j)
             if (c[m - 1] > o[m - 1]) == (c[m] > o[m]) and c[m - 1] != o[m - 1]]
    if not pairs:
        return None
    ref = pairs[-1]
    if direction == "SELL" and c[j] < ref < o[j]:
        return float(ref)
    if direction == "BUY" and c[j] > ref > o[j]:
        return float(ref)
    return None


def _atr(frame: pd.DataFrame, period: int = 14) -> np.ndarray:
    prev = frame["close"].shift()
    tr = pd.concat([frame["high"] - frame["low"], (frame["high"] - prev).abs(), (frame["low"] - prev).abs()], axis=1).max(axis=1)
    return tr.rolling(period).mean().to_numpy()


def detect_h4h1(h4: pd.DataFrame, h1: pd.DataFrame, now, *, spread: float = 0.0, level_lookback: int = 120,
                h1_window: int = 4, oc_lookback: int = 30, atr_buffer: float = 0.10,
                spread_cap: float = 0.02) -> dict | None:
    """Devuelve la configuración H4→H1 disparada por la última H1 cerrada, o None.

    `h4` y `h1` deben contener solo velas cerradas (columna `time` = apertura). La señal solo es válida durante la
    vela H1 siguiente a la que rompe (entrada a mercado en esa vela, como en el replay).
    """
    if h4 is None or h1 is None or len(h4) < 10 or len(h1) < oc_lookback + 2:
        return None
    now = pd.Timestamp(now)
    now = now.tz_localize("UTC") if now.tzinfo is None else now.tz_convert("UTC")
    t4 = pd.to_datetime(h4["time"], utc=True).reset_index(drop=True)
    t1 = pd.to_datetime(h1["time"], utc=True).reset_index(drop=True)
    j = len(h1) - 1
    if not (t1.iloc[j] + H1 <= now < t1.iloc[j] + 2 * H1):
        return None
    o1, c1 = h1["open"].to_numpy(float), h1["close"].to_numpy(float)
    levels = line_levels(h4.reset_index(drop=True), H4)
    for k in range(len(h4) - 1, -1, -1):
        close_k = t4.iloc[k] + H4
        if close_k > t1.iloc[j]:
            continue
        if t1.iloc[j] > close_k + (h1_window - 1) * H1:
            break
        bar = h4.iloc[k]
        avail = [lv for at, lv in levels if at <= t4.iloc[k]][-level_lookback:]
        for direction in ("SELL", "BUY"):
            hit = rejected_levels(bar, avail, direction)
            if not hit:
                continue
            first = None
            for jj in range(len(h1)):
                if t1.iloc[jj] < close_k or t1.iloc[jj] > close_k + (h1_window - 1) * H1:
                    continue
                ref = open_close_break(o1, c1, jj, direction, oc_lookback)
                if ref is not None:
                    first = (jj, ref)
                    break
            if first is None:
                continue  # el replay prueba la otra dirección si esta no rompe
            if first[0] != j:
                return None  # ya disparó (o disparará) en otra vela: el replay solo toma la primera ruptura
            atr = _atr(h1)[j]
            atr = float(atr) if math.isfinite(atr) else 0.0
            sign = 1 if direction == "BUY" else -1
            stop = float(bar.high + atr_buffer * atr + spread) if sign < 0 else float(bar.low - atr_buffer * atr)
            fill = float(c1[j]) + (spread if sign > 0 else 0.0)
            risk = sign * (fill - stop)
            if risk <= 0 or (spread_cap and spread / risk > spread_cap):
                continue  # como el replay: descartada por spread/riesgo, se prueba la otra dirección
            return {"direction": direction, "stop_loss": stop, "entry_reference": float(c1[j]),
                    "h4_level": float(hit[0]), "h1_open_close_level": first[1], "atr_h1": atr,
                    "h4_bar_time": t4.iloc[k].isoformat(), "h1_break_time": t1.iloc[j].isoformat(),
                    "setup_id": f"H4H1|{t4.iloc[k].isoformat()}|{direction}"}
        return None
    return None
