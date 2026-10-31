"""Simulación fiel de Alchemist MSNR sobre velas M15 (bid del broker; ask = bid + spread).

- Orden límite: se llena si el bid llega al precio (venta) o el ask (compra); se cancela si sale de la sesión, si un
  cierre supera la cabeza o si el precio llega antes al objetivo.
- Gestión: en la vela del llenado solo cuenta el SL; con SL y objetivo en la misma vela, cuenta el SL; BE y parcial
  se aplican desde la vela siguiente; cierre forzado en la apertura de la primera vela desde las 16:45 NY.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from strategy.alchemist.rules import arrays


def next_force_flat_ns(t_ns: int, hhmm: str = "16:45") -> int:
    """Primer instante hh:mm de Nueva York estrictamente posterior a t_ns."""
    ny = pd.Timestamp(t_ns, tz="UTC").tz_convert("America/New_York")
    hour, minute = (int(x) for x in hhmm.split(":"))
    day = ny.tz_localize(None).normalize()
    for _ in range(2):
        cut = (day + pd.Timedelta(hours=hour, minutes=minute)).tz_localize("America/New_York")
        if cut > ny:
            return int(cut.tz_convert("UTC").value)
        day += pd.Timedelta(days=1)
    return int(cut.tz_convert("UTC").value)


class Market:
    """Datos M15 de un símbolo con su spread, pip y contexto de la estrategia."""

    def __init__(self, frames: dict, strategy, spread: float, pip: float, is_fx: bool):
        self.m = arrays(frames["M15"], "M15")
        self.strategy, self.cfg = strategy, strategy.config
        self.spread, self.pip, self.is_fx = float(spread), float(pip), bool(is_fx)
        self.ctx = strategy.context(frames)
        self.hours = pd.to_datetime(self.m["open_ns"], utc=True).hour.to_numpy()
        self.close_hours = pd.to_datetime(self.m["close_ns"], utc=True).hour.to_numpy()

    def in_session(self, hour: int) -> bool:
        return self.cfg.session_start_utc <= hour < self.cfg.session_end_utc


def manage_trade(mk: Market, direction: str, entry: float, sl: float, target: float, f: int, exit_mode: str):
    """Gestiona una posición llenada en la vela f. Devuelve (R, resultado, índice de salida)."""
    cfg, m, spread = mk.cfg, mk.m, mk.spread
    o, h, l = m["open"], m["high"], m["low"]
    sign = 1 if direction == "BUY" else -1
    risk = sign * (entry - sl)
    shift = spread if sign < 0 else 0.0  # las ventas cierran al ask
    ff = next_force_flat_ns(int(m["open_ns"][f]), cfg.force_flat_ny)
    cur_sl, locked, remaining, protected, pending_be = sl, 0.0, 1.0, False, False
    for i in range(f, len(o)):
        if pending_be:
            cur_sl, protected, pending_be = entry, True, False
        if i > f:
            if m["open_ns"][i] >= ff:
                px = o[i] + shift
                return locked + remaining * sign * (px - entry) / risk, "FORCE_FLAT", i
            opening = o[i] + shift
            if sign * (opening - cur_sl) <= 0:
                return locked + remaining * sign * (opening - entry) / risk, ("BE" if protected else "GAP_SL"), i
        hi, lo = h[i] + shift, l[i] + shift
        if (sign < 0 and hi >= cur_sl) or (sign > 0 and lo <= cur_sl):
            return locked + remaining * sign * (cur_sl - entry) / risk, ("BE" if protected else "SL"), i
        if i == f:
            continue
        if (sign < 0 and lo <= target) or (sign > 0 and hi >= target):
            return locked + remaining * sign * (target - entry) / risk, "TP", i
        favourable = sign * ((lo if sign < 0 else hi) - entry) / risk
        if exit_mode == "A" and not protected and favourable >= cfg.exit_be_r:
            pending_be = True
        if exit_mode == "B" and not protected and favourable >= cfg.partial_r:
            locked, remaining = cfg.partial_weight * cfg.partial_r, 1.0 - cfg.partial_weight
            pending_be = True
    last = len(o) - 1
    return locked + remaining * sign * (m["close"][last] + shift - entry) / risk, "END", last


def run_order(mk: Market, direction: str, entry, sl: float, signal_idx: int, cancel_level: float,
              valid_bars: int, exit_mode: str) -> dict:
    """Coloca una orden límite al cierre de `signal_idx` y, si se llena, la gestiona. Devuelve el resultado o el motivo."""
    cfg, m, spread = mk.cfg, mk.m, mk.spread
    o, h, l, c = m["open"], m["high"], m["low"], m["close"]
    if entry is None:
        return {"skip": "SIN_PRECIO_DE_ENTRADA"}
    sign = 1 if direction == "BUY" else -1
    risk = sign * (entry - sl)
    if risk <= 0:
        return {"skip": "SL_INVALIDO"}
    if not mk.in_session(int(mk.close_hours[signal_idx])):
        return {"skip": "FUERA_DE_SESION"}
    if (sign < 0 and entry <= c[signal_idx]) or (sign > 0 and entry >= c[signal_idx] + spread):
        return {"skip": "LIMITE_DEL_LADO_EQUIVOCADO"}
    t_ns = int(m["close_ns"][signal_idx])
    cap = cfg.max_sl_pips_fx * mk.pip if mk.is_fx else cfg.max_sl_atr_h1_other * mk.strategy.h1_atr_at(mk.ctx, t_ns)
    if risk > cap:
        return {"skip": "SL_DEMASIADO_GRANDE"}
    if spread / risk > cfg.max_spread_sl_ratio:
        return {"skip": "SPREAD_SL"}
    target = mk.strategy.target(mk.ctx, direction, float(entry), t_ns)
    if target is None:
        return {"skip": "SIN_OBJETIVO"}
    target_r = sign * (target - entry) / risk
    if target_r < cfg.min_target_r:
        return {"skip": "OBJETIVO_MENOR_5R"}
    fill = None
    end = min(len(o), signal_idx + 1 + valid_bars)
    for i in range(signal_idx + 1, end):
        if not mk.in_session(int(mk.hours[i])):
            return {"skip": "NO_LLENADA", "cancel_idx": i}
        if (sign < 0 and h[i] >= entry) or (sign > 0 and l[i] + spread <= entry):
            fill = i
            break
        if sign * (c[i] - cancel_level) <= 0 or (sign < 0 and l[i] <= target) or (sign > 0 and h[i] >= target):
            return {"skip": "NO_LLENADA", "cancel_idx": i}
    if fill is None:
        return {"skip": "NO_LLENADA", "cancel_idx": end - 1}
    rr, outcome, exit_idx = manage_trade(mk, direction, float(entry), float(sl), float(target), fill, exit_mode)
    return {"fill_idx": fill, "exit_idx": exit_idx, "entry": float(entry), "stop_loss": float(sl), "target": float(target),
            "risk": float(risk), "target_r": float(target_r), "spread_sl": spread / risk, "rr": float(rr),
            "outcome": outcome, "fill_ns": int(m["open_ns"][fill])}


def run_variant(mk: Market, setups: list, entry_mode: str, require_confluence: bool, exit_mode: str,
                start_ns: int, end_ns: int, funnel: dict | None = None) -> list:
    """Recorre los setups en orden con una orden o posición por símbolo; añade los QMM tras un SL completo.
    `funnel` (opcional) cuenta por qué se descarta cada setup."""
    cfg = mk.cfg
    funnel = funnel if funnel is not None else {}
    count = lambda key: funnel.__setitem__(key, funnel.get(key, 0) + 1)
    trades, busy = [], -1
    for s in sorted(setups, key=lambda x: x.signal_idx):
        if not (start_ns <= s.signal_ns < end_ns):
            continue
        count("SETUPS")
        if s.signal_idx <= busy:
            count("OCUPADO")
            continue
        if require_confluence and not s.confluence:
            count("SIN_CONFLUENCIA")
            continue
        res = run_order(mk, s.direction, s.entry(entry_mode), s.stop_loss, s.signal_idx, s.head_ext,
                        cfg.limit_valid_bars, exit_mode)
        if "skip" in res:
            count(res["skip"])
            busy = max(busy, res.get("cancel_idx", busy))
            continue
        count("OPERADO")
        trades.append({**res, "kind": s.kind, "direction": s.direction, "signal_ns": s.signal_ns,
                       "level_tf": s.level_tf, "turtle_soup": s.turtle_soup, "inducement": s.inducement})
        busy = res["exit_idx"]
        if cfg.enable_qmm and res["outcome"] in ("SL", "GAP_SL"):
            qdir = "BUY" if s.direction == "SELL" else "SELL"
            qsign = 1 if qdir == "BUY" else -1
            qsl = res["entry"] - qsign * res["risk"]
            q = run_order(mk, qdir, res["entry"], qsl, res["exit_idx"], qsl, cfg.qmm_window_bars, exit_mode)
            if "skip" in q:
                busy = max(busy, q.get("cancel_idx", busy))
                continue
            trades.append({**q, "kind": "QMM", "direction": qdir, "signal_ns": int(mk.m["close_ns"][res["exit_idx"]]),
                           "level_tf": s.level_tf, "turtle_soup": s.turtle_soup, "inducement": s.inducement})
            busy = q["exit_idx"]
    return trades


def random_baseline(mk: Market, trades: list, reps: int = 200, seed: int = 0, exit_mode: str = "A") -> np.ndarray:
    """Media de R de `reps` repeticiones: misma dirección, SL y objetivo en R, entrada al azar en la sesión del mes."""
    if not trades:
        return np.array([])
    rng = np.random.default_rng(seed)
    m, spread = mk.m, mk.spread
    months = pd.to_datetime(m["open_ns"], utc=True).strftime("%Y-%m").to_numpy()
    in_sess = np.array([mk.in_session(int(x)) for x in mk.hours])
    pools = {}
    means = np.zeros(reps)
    for t in trades:
        month = pd.Timestamp(t["fill_ns"], tz="UTC").strftime("%Y-%m")
        if month not in pools:
            pools[month] = np.flatnonzero((months == month) & in_sess)[:-1]
    for r in range(reps):
        total = 0.0
        for t in trades:
            pool = pools[pd.Timestamp(t["fill_ns"], tz="UTC").strftime("%Y-%m")]
            i = int(rng.choice(pool))
            sign = 1 if t["direction"] == "BUY" else -1
            entry = m["open"][i] + (spread if sign > 0 else 0.0)
            sl = entry - sign * t["risk"]
            target = entry + sign * t["target_r"] * t["risk"]
            total += manage_trade(mk, t["direction"], entry, sl, target, i, exit_mode)[0]
        means[r] = total / len(trades)
    return means
