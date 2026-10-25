"""Storyline diaria de los vídeos MSNR (Alchemist) en vivo, solo con velas cerradas — 20-oct-2026.

Storyline BAJISTA (espejo para alcista):
1. Una vela D1 abre por debajo de un nivel diario (pico/valle de cierres, radio 2), lo toca y cierra por debajo.
2. En los 3 días siguientes una vela H4 cierra por debajo del último mínimo oscilante H4 confirmado (radio 2).
Empieza al cierre de esa H4 y termina al tocar el siguiente nivel diario contrario, al empezar la opuesta o a los 15
días. Misma regla que tools/research_msnr_storyline_h4h1.py (como filtro no mejoró MSNR en el replay; se registra).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

D1 = pd.Timedelta(days=1)
H4 = pd.Timedelta(hours=4)


def _with_close_time(frame: pd.DataFrame, delta: pd.Timedelta) -> pd.DataFrame:
    out = frame.reset_index(drop=True).copy()
    out["time"] = pd.to_datetime(out["time"], utc=True)
    out["close_time"] = out["time"] + delta
    return out


def peak_levels(frame: pd.DataFrame, radius: int = 2) -> pd.DataFrame:
    c = frame["close"].to_numpy(float)
    rows = []
    for i in range(radius, len(frame) - radius):
        win = c[i - radius:i + radius + 1]
        if c[i] == win.max() or c[i] == win.min():
            rows.append((frame["close_time"].iloc[i + radius], c[i]))
    return pd.DataFrame(rows, columns=["avail", "level"])


def swing_points(frame: pd.DataFrame, radius: int = 2):
    h, l = frame["high"].to_numpy(float), frame["low"].to_numpy(float)
    lows, highs = [], []
    for i in range(radius, len(frame) - radius):
        conf = frame["close_time"].iloc[i + radius]
        if l[i] == l[i - radius:i + radius + 1].min():
            lows.append((conf, l[i]))
        if h[i] == h[i - radius:i + radius + 1].max():
            highs.append((conf, h[i]))
    return pd.DataFrame(lows, columns=["conf", "price"]), pd.DataFrame(highs, columns=["conf", "price"])


def storyline_events(d1: pd.DataFrame, h4: pd.DataFrame, lookback: int = 120) -> pd.DataFrame:
    d1 = _with_close_time(d1, D1)
    h4 = _with_close_time(h4, H4)
    lv = peak_levels(d1)
    sw_low, sw_high = swing_points(h4)
    events = []
    for i in range(len(d1)):
        bar = d1.iloc[i]
        lvls = lv[lv.avail <= bar["time"]]["level"].to_numpy()[-lookback:]
        if len(lvls) == 0:
            continue
        for direction in ("SELL", "BUY"):
            if direction == "SELL":
                hit = lvls[(bar.open < lvls) & (bar.high >= lvls) & (bar.close < lvls)]
            else:
                hit = lvls[(bar.open > lvls) & (bar.low <= lvls) & (bar.close > lvls)]
            if len(hit) == 0:
                continue
            rej = bar["close_time"]
            window = h4[(h4.close_time > rej) & (h4.close_time <= rej + pd.Timedelta(days=3))]
            start = None
            for _, hb in window.iterrows():
                pts = sw_low if direction == "SELL" else sw_high
                pts = pts[pts.conf <= hb["time"]]
                if pts.empty:
                    continue
                ref = pts["price"].iloc[-1]
                if (direction == "SELL" and hb.close < ref) or (direction == "BUY" and hb.close > ref):
                    start = hb["close_time"]
                    break
            if start is None:
                continue
            others = lv[lv.avail <= rej]["level"].to_numpy()
            if direction == "SELL":
                below = others[others < bar.close]
                target = below.max() if len(below) else np.nan
            else:
                above = others[others > bar.close]
                target = above.min() if len(above) else np.nan
            events.append({"start": start, "direction": direction, "target": target})
    if not events:
        return pd.DataFrame(columns=["start", "direction", "target"])
    return pd.DataFrame(events).sort_values("start").reset_index(drop=True)


def storyline_at(events: pd.DataFrame, h4: pd.DataFrame, t) -> str:
    """Storyline vigente en `t` (BUY / SELL / NONE), sin mirar al futuro."""
    t = pd.Timestamp(t)
    t = t.tz_localize("UTC") if t.tzinfo is None else t.tz_convert("UTC")
    past = events[events.start <= t] if len(events) else events
    if past is None or past.empty:
        return "NONE"
    ev = past.iloc[-1]
    if t > ev.start + pd.Timedelta(days=15):
        return "NONE"
    if pd.notna(ev.target):
        h4 = _with_close_time(h4, H4)
        path = h4[(h4.close_time > ev.start) & (h4.close_time <= t)]
        reached = (path.low <= ev.target).any() if ev.direction == "SELL" else (path.high >= ev.target).any()
        if reached:
            return "NONE"
    return str(ev.direction)


def current_storyline(d1: pd.DataFrame, h4: pd.DataFrame, now) -> str:
    if d1 is None or h4 is None or len(d1) < 10 or len(h4) < 10:
        return "NONE"
    return storyline_at(storyline_events(d1, h4), h4, now)
