"""H2 — Seguimiento de tendencia diario (Donchian 55/20, stop 2xATR20). Solo lectura; no toca el bot.

Reglas pre-registradas en storage/analysis/research_preregistro_20261019.md:
  * Entrada: cierre > máximo de 55 días (BUY) o < mínimo de 55 días (SELL); fill en la apertura siguiente.
  * Stop inicial 2x ATR(20); salida por cierre < mínimo de 20 días (BUY) / > máximo de 20 días (SELL) o stop.
  * Costes: spread (actual, MT5) en entrada y salida + swap por noche cuando swap_mode es en puntos.
  * Resultado en R. Test de azar: entradas en fechas/direcciones aleatorias con la misma gestión.

Uso: python tools/research_trend_following.py
Salida: storage/analysis/research_trend_following_trades.csv y _report.md
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "storage" / "analysis"
UNIVERSE = {
    "Índices": ["US SP 500", "US Tech 100", "Wall Street 30", "US Small Cap 2000", "US Mid Cap 400", "Germany 40",
                "UK 100", "France 40", "Europe 50", "Japan 225", "Australia 200", "Hong Kong 50", "China H Shares",
                "Netherlands 25", "Swiss 20", "Spain 35"],
    "Metales": ["XAUUSD", "XAGUSD", "XAUEUR"],
    "Energía": ["US Oil", "UK Brent Oil", "NGAS"],
    "Forex": ["EURUSD", "GBPUSDmicro", "USDJPYmicro", "AUDUSDmicro", "USDCADmicro", "USDCHFmicro", "NZDUSDmicro",
              "EURGBPmicro", "EURJPYmicro", "GBPJPYmicro", "AUDJPYmicro", "EURCHFmicro", "EURAUDmicro", "EURCADmicro",
              "AUDCADmicro", "AUDNZDmicro", "AUDCHFmicro", "GBPCHFmicro", "EURNZDmicro", "AUDSGD", "EURSGD", "HKDJPY"],
    "Cripto": ["BTCUSD", "ETHUSD", "SOLUSD", "XLMUSD", "TRXUSD", "IOTUSD", "NEOUSD", "ADAUSD", "DOTUSD", "LNKUSD",
               "DOGUSD", "UNIUSD", "XTZUSD", "ETCUSD", "FILUSD", "AVAUSD"],
}
ENTRY_N, EXIT_N, ATR_N, STOP_ATR = 55, 20, 20, 2.0


def load(mt5, sym):
    if not mt5.symbol_select(sym, True):
        return None, None
    r = mt5.copy_rates_from_pos(sym, mt5.TIMEFRAME_D1, 0, 5000)
    info = mt5.symbol_info(sym)
    if r is None or len(r) < 2 * 252 or info is None:
        return None, None
    df = pd.DataFrame(r)
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    return df[["time", "open", "high", "low", "close"]].reset_index(drop=True), info


def atr(df, n):
    tr = pd.concat([df.high - df.low, (df.high - df.close.shift()).abs(), (df.low - df.close.shift()).abs()], axis=1).max(axis=1)
    return tr.rolling(n).mean()


def simulate(df, info, entries):
    """entries: lista de (idx_señal, side). Devuelve trades con la gestión pre-registrada."""
    spread = float(info.spread) * float(info.point)
    swap_pts = info.swap_mode == 1  # SYMBOL_SWAP_MODE_POINTS
    hh_exit = df.high.rolling(EXIT_N).max()
    ll_exit = df.low.rolling(EXIT_N).min()
    a = atr(df, ATR_N)
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    out, busy = [], -1
    for i, side in entries:
        if i <= busy or i + 1 >= len(df) or not np.isfinite(a.iloc[i]):
            continue
        fill = o[i + 1] + (spread if side > 0 else 0.0)
        stop = fill - side * STOP_ATR * a.iloc[i]
        risk = abs(fill - stop)
        if risk <= 0:
            continue
        exit_px, j = None, i + 1
        for j in range(i + 1, len(df)):
            if (side > 0 and l[j] <= stop) or (side < 0 and h[j] + spread >= stop):
                exit_px = stop if (side > 0 and o[j] > stop) or (side < 0 and o[j] + spread < stop) else o[j] + (spread if side < 0 else 0)
                break
            if j > i + 1 and ((side > 0 and c[j] < ll_exit.iloc[j - 1]) or (side < 0 and c[j] > hh_exit.iloc[j - 1])):
                if j + 1 < len(df):
                    exit_px = o[j + 1] + (spread if side < 0 else 0.0)
                    j += 1
                break
        if exit_px is None:
            exit_px, j = c[-1] + (spread if side < 0 else 0.0), len(df) - 1
        nights = max(0, (df.time.iloc[j] - df.time.iloc[i + 1]).days)
        swap = (info.swap_long if side > 0 else info.swap_short) * float(info.point) * nights if swap_pts else 0.0
        pnl = side * (exit_px - fill) + swap
        out.append(dict(entry_time=df.time.iloc[i + 1], exit_time=df.time.iloc[j], side=side, fill=fill, stop=stop,
                        exit=exit_px, r=pnl / risk, r_sin_swap=(side * (exit_px - fill)) / risk, nights=nights,
                        swap_modo_puntos=swap_pts))
        busy = j
    return out


def donchian_entries(df):
    hh = df.high.rolling(ENTRY_N).max().shift(1)
    ll = df.low.rolling(ENTRY_N).min().shift(1)
    sig = []
    for i in range(ENTRY_N + ATR_N, len(df) - 1):
        if df.close.iloc[i] > hh.iloc[i]:
            sig.append((i, 1))
        elif df.close.iloc[i] < ll.iloc[i]:
            sig.append((i, -1))
    return sig


def stats(r):
    r = pd.Series(r, dtype=float).dropna()
    if len(r) < 3:
        return dict(n=len(r), media=np.nan, t=np.nan, wr=np.nan, pf=np.nan)
    gl = -r[r < 0].sum()
    return dict(n=len(r), media=r.mean(), t=r.mean() / (r.std(ddof=1) / np.sqrt(len(r))), wr=100 * (r > 0).mean(),
                pf=r[r > 0].sum() / gl if gl else np.inf)


def main():
    import MetaTrader5 as mt5
    assert mt5.initialize(), "MT5 no inicializa"
    rng = np.random.default_rng(55)
    trades, sims_by_symbol, missing = [], {}, []
    for group, syms in UNIVERSE.items():
        for s in syms:
            df, info = load(mt5, s)
            if df is None:
                missing.append(s)
                continue
            tr = simulate(df, info, donchian_entries(df))
            for t in tr:
                t.update(symbol=s, grupo=group)
            trades += tr
            # Azar: mismas veces, fechas y direcciones aleatorias, misma gestión
            n = max(len(tr), 1)
            sims = []
            for _ in range(200):
                idx = np.sort(rng.integers(ENTRY_N + ATR_N, len(df) - 2, size=n * 3))
                ent = [(int(i), int(rng.choice([-1, 1]))) for i in idx]
                sims.append([x["r"] for x in simulate(df, info, ent)][:n])
            sims_by_symbol[s] = sims
            print(f"{group:8s} {s:20s} D1 desde {df.time.iloc[0].date()} | trades {len(tr):3d} | R/t "
                  f"{np.mean([x['r'] for x in tr]) if tr else float('nan'):+.3f}", flush=True)
    mt5.shutdown()
    t = pd.DataFrame(trades)
    t.to_csv(OUT / "research_trend_following_trades.csv", index=False)
    mid = t.entry_time.quantile(0.5)
    t["mitad"] = np.where(t.entry_time <= mid, 1, 2)
    # Distribución de azar de la media de cartera (concatenando los sims de cada símbolo)
    port = []
    for k in range(200):
        allr = [x for s in sims_by_symbol for x in (sims_by_symbol[s][k] if k < len(sims_by_symbol[s]) else [])]
        port.append(np.mean(allr) if allr else np.nan)
    port = np.array(port)
    L = ["# H2 — Tendencia diaria Donchian 55/20 (replay solo lectura)\n",
         f"Universo: {t.symbol.nunique()} mercados reales con ≥ 2 años de D1; sin datos: {', '.join(missing) or '—'}.",
         f"Mitades separadas en {mid.date()}. Costes: spread actual + swap (modo puntos).\n",
         "| segmento | n | R/trade | t | WR% | PF | mitad 1 | mitad 2 | R/trade sin swap |", "|---|---|---|---|---|---|---|---|---|"]
    for name, g in [("CARTERA", t)] + [(gr, t[t.grupo == gr]) for gr in UNIVERSE] + [("BUY", t[t.side > 0]), ("SELL", t[t.side < 0])]:
        m, m1, m2 = stats(g.r), stats(g[g.mitad == 1].r), stats(g[g.mitad == 2].r)
        L.append(f"| {name} | {m['n']} | {m['media']:+.3f} | {m['t']:+.2f} | {m['wr']:.1f} | {m['pf']:.2f} | "
                 f"{m1['media']:+.3f} | {m2['media']:+.3f} | {g.r_sin_swap.mean():+.3f} |")
    obs = t.r.mean()
    L.append(f"\n**Test de azar (entradas aleatorias, misma gestión):** media cartera observada {obs:+.3f} R; "
             f"azar media {np.nanmean(port):+.3f}, p95 {np.nanpercentile(port, 95):+.3f}; p = {(port >= obs).mean():.3f}\n")
    L.append("\n## Por símbolo\n\n| símbolo | grupo | n | R/trade | mitad 1 | mitad 2 |\n|---|---|---|---|---|---|")
    for (s, gr), g in t.groupby(["symbol", "grupo"]):
        L.append(f"| {s} | {gr} | {len(g)} | {g.r.mean():+.3f} | {g[g.mitad == 1].r.mean():+.3f} | {g[g.mitad == 2].r.mean():+.3f} |")
    (OUT / "research_trend_following_report.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L[:20]))


if __name__ == "__main__":
    sys.exit(main())
