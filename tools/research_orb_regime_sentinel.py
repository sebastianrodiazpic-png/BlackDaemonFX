"""¿Quita el Centinela de Régimen (modo FILTER) operaciones buenas o malas a ORB SWEEP? (solo lectura).

Parte de las operaciones del replay `tools/replay_orb_sweep_expanded.py` (storage/analysis/orb_sweep_expanded_trades.csv,
señal con paridad del modo vivo y gestión del contrato). Para cada señal aplica el `MarketRegimeSentinel` real, con la
misma configuración que el motor (FILTER, forex estricto), sobre las 40 velas H1 del broker CERRADAS antes de la
señal. No hay spread histórico por vela de ticks: el factor de spread anómalo no se evalúa (current_spread=None).

Se compara el R de las bloqueadas frente a las permitidas, por mitades (fecha mediana) y por símbolo.
Uso: python tools/research_orb_regime_sentinel.py
Salida: storage/analysis/orb_regime_sentinel_trades.csv y orb_regime_sentinel_report.md
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "storage" / "analysis"
LIVE_SYMBOLS = ("XAUUSD", "BTCUSD", "USDCAD")  # ORB SWEEP en vivo / prueba demo


def h1_history(mt5, symbol, start, end):
    rates = mt5.copy_rates_range(symbol, mt5.TIMEFRAME_H1, start.to_pydatetime(), end.to_pydatetime())
    if rates is None or len(rates) == 0:
        return None
    df = pd.DataFrame(rates)
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
    return df


def stats(r):
    r = pd.Series(r, dtype=float).dropna()
    if len(r) < 3:
        return dict(n=len(r), m=np.nan, t=np.nan)
    return dict(n=len(r), m=r.mean(), t=r.mean() / (r.std(ddof=1) / np.sqrt(len(r))))


def fmt(s):
    return f"{s['n']} · {s['m']:+.3f}" if s["n"] else "0 · —"


def main():
    import MetaTrader5 as mt5
    from strategy.regime.market_regime_sentinel import MarketRegimeConfig, MarketRegimeSentinel

    trades = pd.read_csv(OUT / "orb_sweep_expanded_trades.csv")
    trades["ts"] = pd.to_datetime(trades["signal_time"], utc=True)
    sentinel = MarketRegimeSentinel(MarketRegimeConfig(enabled=True, mode="FILTER", forex_strict_filter=True))
    if not mt5.initialize():
        raise SystemExit("MT5 no inicializa")
    rows = []
    for symbol, group in trades.groupby("symbol"):
        mt5.symbol_select(symbol, True)
        h1 = h1_history(mt5, symbol, group.ts.min() - pd.Timedelta(days=15), group.ts.max() + pd.Timedelta(days=1))
        if h1 is None:
            print(symbol, "sin H1", flush=True)
            continue
        close_ts = (h1["time"] + pd.Timedelta(hours=1)).values
        for _, trade in group.iterrows():
            idx = int(np.searchsorted(close_ts, np.datetime64(trade.ts.tz_localize(None)), side="right"))
            window = h1.iloc[max(0, idx - 40):idx]
            decision = sentinel.evaluate_symbol(symbol=symbol, df_h1=window)
            rows.append({**trade.drop(labels=["ts"]).to_dict(), "regime_blocked": bool(decision.is_toxic),
                         "regime_reason": decision.reason, "regime": decision.regime})
        print(symbol, "ok", len(group), flush=True)
    mt5.shutdown()
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "orb_regime_sentinel_trades.csv", index=False)
    df["ts"] = pd.to_datetime(df["signal_time"], utc=True)
    mid = df.ts.quantile(0.5)
    df["mitad"] = np.where(df.ts <= mid, 1, 2)

    L = ["# ORB SWEEP y el Centinela de Régimen (FILTER)\n",
         f"Operaciones del replay ampliado, mitades separadas en {mid.date()}. R por operación con la gestión "
         "EXTENDIDA (contrato actual). Celdas: n · R/op.\n",
         "| Universo | Permitidas | Bloqueadas | % bloq. | Bloq. mitad 1 | Bloq. mitad 2 | Perm. mitad 1 | Perm. mitad 2 |",
         "|---|---|---|---|---|---|---|---|"]
    universes = [("SWEEP en vivo (XAUUSD, BTCUSD, USDCAD)", df[(df.variant == "SWEEP") & df.symbol.isin(LIVE_SYMBOLS)]),
                 ("SWEEP todos", df[df.variant == "SWEEP"]), ("Todas las variantes", df)]
    universes += [(f"SWEEP {s}", df[(df.variant == "SWEEP") & (df.symbol == s)]) for s in LIVE_SYMBOLS]
    for name, u in universes:
        a, b = u[~u.regime_blocked], u[u.regime_blocked]
        share = 100 * len(b) / len(u) if len(u) else 0
        L.append(f"| {name} | {fmt(stats(a.net_r_ext))} | {fmt(stats(b.net_r_ext))} | {share:.0f} % | "
                 f"{fmt(stats(b[b.mitad == 1].net_r_ext))} | {fmt(stats(b[b.mitad == 2].net_r_ext))} | "
                 f"{fmt(stats(a[a.mitad == 1].net_r_ext))} | {fmt(stats(a[a.mitad == 2].net_r_ext))} |")
    L.append("\nMotivos de bloqueo (SWEEP en vivo): "
             + str(df[(df.variant == "SWEEP") & df.symbol.isin(LIVE_SYMBOLS) & df.regime_blocked].regime_reason.value_counts().to_dict()))
    (OUT / "orb_regime_sentinel_report.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
