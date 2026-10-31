"""AlchemistStrategy: Quasimodo (QML/QMC) en M15 sobre niveles clave D1/H4/H1 de cierres (pre-registro 26-oct-2026).

Uso en vivo y en replay: `setups(frames, spread)` con velas cerradas; un setup es operable en el cierre `signal_ns`.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from strategy.alchemist.config import AlchemistConfig
from strategy.alchemist.rules import arrays, atr, build_levels, close_pivots, structure_trend, value_at

HTF = ("D1", "H4", "H1")


@dataclass
class Setup:
    direction: str  # BUY | SELL
    kind: str  # QML | QMC
    shoulder_idx: int
    head_idx: int
    signal_idx: int
    signal_ns: int
    shoulder: float
    head_ext: float
    stop_loss: float
    turtle_soup: bool
    inducement: bool
    ce: float | None
    ob50: float | None
    level_tf: str | None = None
    level_price: float | None = None

    @property
    def sign(self) -> int:
        return 1 if self.direction == "BUY" else -1

    @property
    def confluence(self) -> bool:
        return self.turtle_soup or self.inducement

    def entry(self, mode: str):
        return {"shoulder": self.shoulder, "ce": self.ce, "ob50": self.ob50}[mode]


class AlchemistStrategy:
    def __init__(self, config: AlchemistConfig | None = None):
        self.config = config or AlchemistConfig()

    # ------------------------------------------------------------------ contexto de alta temporalidad
    def context(self, frames: dict) -> dict:
        cfg = self.config
        htf = {tf: arrays(frames[tf], tf) for tf in HTF}
        levels = sorted((lv for tf in HTF for lv in build_levels(htf[tf], tf, cfg)), key=lambda lv: lv.price)
        trend_t, trend_v = structure_trend(htf["H1"], cfg.trend_pivot_k)
        h1_atr = atr(htf["H1"], cfg.atr_period)
        return {"levels": levels, "prices": np.array([lv.price for lv in levels]),
                "max_half": max((lv.half for lv in levels), default=0.0),
                "trend": (trend_t, trend_v), "h1_close_ns": htf["H1"]["close_ns"], "h1_atr": h1_atr}

    def h1_atr_at(self, ctx: dict, t_ns: int) -> float:
        i = int(np.searchsorted(ctx["h1_close_ns"], t_ns, side="right")) - 1
        return float(ctx["h1_atr"][max(0, i)])

    def target(self, ctx: dict, direction: str, entry: float, t_ns: int):
        """Nivel válido de rol opuesto más cercano más allá de la entrada (liquidez opuesta), o None."""
        want = "S" if direction == "SELL" else "R"
        levels, prices = ctx["levels"], ctx["prices"]
        if direction == "SELL":
            order = range(int(np.searchsorted(prices, entry, side="left")) - 1, -1, -1)
        else:
            order = range(int(np.searchsorted(prices, entry, side="right")), len(levels))
        for i in order:
            lv = levels[i]
            if lv.created_ns > t_ns:
                continue
            state = lv.state_at(t_ns)
            if state is not None and state[0] == want:
                return lv.price
        return None

    def _key_level(self, ctx: dict, direction: str, head_ext: float, head_close: float, t_ns: int):
        """Nivel de rol contrario válido, con <= max_touches - 1 toques, en cuya zona entra la cabeza."""
        want = "R" if direction == "SELL" else "S"
        lo_p, hi_p = sorted((head_ext, head_close))
        span = ctx["max_half"]
        a = int(np.searchsorted(ctx["prices"], lo_p - span, side="left"))
        b = int(np.searchsorted(ctx["prices"], hi_p + span, side="right"))
        for lv in ctx["levels"][a:b]:
            if lv.created_ns > t_ns:
                continue
            state = lv.state_at(t_ns)
            if state is None or state[0] != want or state[1] > self.config.max_touches - 1:
                continue
            if direction == "SELL" and head_ext >= lv.price - lv.half and head_close <= lv.price + lv.half:
                return lv
            if direction == "BUY" and head_ext <= lv.price + lv.half and head_close >= lv.price - lv.half:
                return lv
        return None

    # ------------------------------------------------------------------ Quasimodo M15
    def setups(self, frames: dict, spread: float = 0.0, ctx: dict | None = None) -> list:
        cfg = self.config
        ctx = ctx or self.context(frames)
        m = arrays(frames["M15"], "M15")
        o, h, l, c, close_ns, open_ns = m["open"], m["high"], m["low"], m["close"], m["close_ns"], m["open_ns"]
        n, k = len(c), cfg.m15_pivot_k
        m_atr = atr(m, cfg.atr_period)
        pivots = close_pivots(c, k)
        minor = [p for p in close_pivots(c, cfg.minor_pivot_k)]
        out = []
        for (p1, k1), (p2, k2), (p3, k3) in zip(pivots, pivots[1:], pivots[2:]):
            if (k1, k2, k3) == ("H", "L", "H") and c[p3] > c[p1] > c[p2]:
                direction = "SELL"
            elif (k1, k2, k3) == ("L", "H", "L") and c[p3] < c[p1] < c[p2]:
                direction = "BUY"
            else:
                continue
            sign = 1 if direction == "BUY" else -1
            brk = None
            for j in range(p3 + 1, min(n, p3 + cfg.break_max_bars + 1)):
                if sign * (c[j] - c[p3]) < 0:  # supera la cabeza
                    break
                if sign * (c[j] - c[p2]) > 0:  # rompe el valle (venta: cierre < valle)
                    brk = j
                    break
            if brk is None:
                continue
            sig = max(brk, p3 + k)
            if sig >= n:
                continue
            lo = max(0, p3 - k)
            head_ext = float(h[lo:sig + 1].max()) if sign < 0 else float(l[lo:sig + 1].min())
            buffer = cfg.sl_buffer_atr * m_atr[sig]
            stop = head_ext + buffer + spread if sign < 0 else head_ext - buffer
            head_open = int(open_ns[p3])
            level = self._key_level(ctx, direction, head_ext, float(c[p3]), head_open)
            if level is not None:
                kind = "QML"
            elif value_at(*ctx["trend"], int(close_ns[sig])) == ("down" if sign < 0 else "up"):
                kind = "QMC"
            else:
                continue
            ts_bar = self._turtle_soup(h, l, c, sign, lo, min(sig, p3 + k))
            inducement = any(p2 < idx < p3 and kind_ == ("H" if sign < 0 else "L") for idx, kind_ in minor)
            ce = None
            if ts_bar is not None:
                if sign < 0:
                    wick = h[ts_bar] - max(o[ts_bar], c[ts_bar])
                    ce = float(h[ts_bar] - cfg.ce_ratio * wick)
                else:
                    wick = min(o[ts_bar], c[ts_bar]) - l[ts_bar]
                    ce = float(l[ts_bar] + cfg.ce_ratio * wick)
            ob50 = None
            for b in range(sig, lo - 1, -1):  # última vela contraria antes del desplazamiento
                if (sign < 0 and c[b] > o[b]) or (sign > 0 and c[b] < o[b]):
                    ob50 = float((o[b] + c[b]) / 2)
                    break
            out.append(Setup(direction, kind, p1, p3, sig, int(close_ns[sig]), float(c[p1]), head_ext, float(stop),
                             ts_bar is not None, inducement, ce, ob50,
                             level.tf if level else None, level.price if level else None))
        return out

    def _turtle_soup(self, h, l, c, sign, start, end):
        """Vela de la cabeza que barre las `turtle_soup_lookback` previas y cierra dentro del rango de la anterior."""
        lb, best = self.config.turtle_soup_lookback, None
        for b in range(max(lb, start), end + 1):
            inside = l[b - 1] <= c[b] <= h[b - 1]
            if sign < 0 and h[b] > h[b - lb:b].max() and inside and (best is None or h[b] > h[best]):
                best = b
            if sign > 0 and l[b] < l[b - lb:b].min() and inside and (best is None or l[b] < l[best]):
                best = b
        return best
