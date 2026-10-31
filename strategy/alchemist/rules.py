"""Reglas causales de Alchemist MSNR sobre velas cerradas.

Cada objeto lleva el instante (cierre de vela, ns UTC) en que queda confirmado, de modo que calcularlo sobre todo el
histórico y filtrar por ese instante equivale a calcularlo solo con las velas cerradas hasta entonces.
"""
from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

TF_MINUTES = {"M15": 15, "H1": 60, "H4": 240, "D1": 1440}
DAY_NS = 86_400 * 10**9


def arrays(df: pd.DataFrame, tf: str) -> dict:
    """OHLC como arrays y el instante de cierre de cada vela (apertura + duración), en ns UTC."""
    open_ns = pd.to_datetime(df["time"], utc=True).to_numpy(dtype="datetime64[ns]").astype("int64")
    return {"open_ns": open_ns, "close_ns": open_ns + TF_MINUTES[tf] * 60 * 10**9,
            **{k: df[k].to_numpy(float) for k in ("open", "high", "low", "close")}}


def atr(a: dict, period: int = 14) -> np.ndarray:
    """ATR simple (media de rangos verdaderos) hasta cada vela incluida."""
    h, l, c = a["high"], a["low"], a["close"]
    prev = np.concatenate(([c[0]], c[:-1])) if len(c) else c
    tr = np.maximum(h - l, np.maximum(np.abs(h - prev), np.abs(l - prev)))
    return pd.Series(tr).rolling(period, min_periods=1).mean().to_numpy()


def close_pivots(close: np.ndarray, k: int) -> list:
    """(índice, 'H'|'L') de los cierres estrictamente mayores/menores que los k de cada lado; confirmados en índice + k."""
    n = len(close)
    if n < 2 * k + 1:
        return []
    win = np.lib.stride_tricks.sliding_window_view(close, 2 * k + 1)
    centre = close[k:n - k]
    others = np.delete(win, k, axis=1)
    highs = np.all(others < centre[:, None], axis=1)
    lows = np.all(others > centre[:, None], axis=1)
    out = []
    for j in np.flatnonzero(highs | lows):
        out.append((int(j + k), "H" if highs[j] else "L"))
    return out


@dataclass
class Level:
    """Nivel clave de una temporalidad. `events`: (ns, rol 'R'|'S', toques, válido) tras cada cambio."""
    tf: str
    price: float
    half: float
    kind: str  # 'A' (cresta) | 'V' (valle)
    created_ns: int
    events: list = field(default_factory=list)
    _times: list = field(default_factory=list, repr=False)

    def state_at(self, t_ns: int):
        """(rol, toques) vigente con las velas cerradas hasta t_ns, o None si no existe o está descartado."""
        if not self._times:
            self._times = [e[0] for e in self.events]
        i = bisect_right(self._times, t_ns) - 1
        if i < 0:
            return None
        _, role, touches, valid = self.events[i]
        return (role, touches) if valid else None


def build_levels(a: dict, tf: str, cfg) -> list:
    """Niveles A/V sobre cierres con su historia de toques, rupturas y cambios de rol (SBR/RBS)."""
    o, h, l, c, close_ns = a["open"], a["high"], a["low"], a["close"], a["close_ns"]
    n, k = len(c), cfg.level_pivot_k[tf]
    av = atr(a, cfg.atr_period)
    lookback_ns = cfg.level_lookback_days[tf] * DAY_NS
    levels = []
    for idx, kind in close_pivots(c, k):
        conf = idx + k
        if conf >= n:
            continue
        price, half = float(c[idx]), float(cfg.level_zone_atr * av[conf])
        role, touches = ("R" if kind == "H" else "S"), 0
        inside = bool(h[conf] >= price - half and l[conf] <= price + half)
        level = Level(tf, price, half, "A" if kind == "H" else "V", int(close_ns[conf]))
        level.events.append((int(close_ns[conf]), role, 0, True))
        expiry = close_ns[conf] + lookback_ns
        for b in range(conf + 1, n):
            t = int(close_ns[b])
            if t > expiry:
                level.events.append((t, role, touches, False))
                break
            broke = c[b] > price + half if role == "R" else c[b] < price - half
            if broke:
                dist = abs(c[b] - price)
                rng, body = h[b] - l[b], abs(c[b] - o[b])
                if dist >= cfg.flip_min_atr * av[b] and rng > 0 and body / rng >= cfg.flip_min_body_ratio:
                    role, touches, inside = ("S" if role == "R" else "R"), 0, True
                    level.events.append((t, role, 0, True))
                    continue
                level.events.append((t, role, touches, False))
                break
            if h[b] >= price - half and l[b] <= price + half:
                if not inside:
                    touches += 1
                    inside = True
                    level.events.append((t, role, touches, touches <= cfg.max_touches))
                    if touches > cfg.max_touches:
                        break
            else:
                inside = False
        levels.append(level)
    return levels


def structure_trend(a: dict, k: int) -> tuple:
    """Estructura H1: ('up'|'down') tras cada cierre que rompe el último pivote confirmado. Devuelve (tiempos, valores)."""
    c, close_ns = a["close"], a["close_ns"]
    pivots = close_pivots(c, k)
    times, values = [], []
    last_high = last_low = None
    pi = 0
    for b in range(len(c)):
        while pi < len(pivots) and pivots[pi][0] + k <= b:
            idx, kind = pivots[pi]
            if kind == "H":
                last_high = float(c[idx])
            else:
                last_low = float(c[idx])
            pi += 1
        if last_high is not None and c[b] > last_high:
            times.append(int(close_ns[b])); values.append("up"); last_high = None
        elif last_low is not None and c[b] < last_low:
            times.append(int(close_ns[b])); values.append("down"); last_low = None
    return times, values


def value_at(times: list, values: list, t_ns: int):
    i = bisect_right(times, t_ns) - 1
    return values[i] if i >= 0 else None
