"""Replay fiel de Malaysian SNR para optimizar filtros y gestión sobre las MISMAS señales (solo lectura).

Ejecuta MalaysianSNRStrategy.analyze_symbol real (solo velas cerradas, sin lookahead) con la configuración
del motor vivo pero con C2 DESACTIVADO y sin allowlist, para capturar todas las señales candidatas.
Por señal guarda sus características (ADX, SL/ATR, spread/SL, escenario, dirección, hora, frescura...) y el
resultado con varias gestiones de 2 patas (50%/50%, BE tras TP1):
  rr_live  TP1 1R + runner 2R (actual)      rr_r15  TP1 1R + runner 1.5R
  rr_r3    TP1 1R + runner 3R               rr_1r   ambas patas a 1R
  rr_h05   TP1 0.5R + runner 2R
Filtros como C2 (ADX>=30 + SL/ATR) se evalúan después como subconjuntos.
Con --limit se añaden entradas LIMITADAS (válidas LIMIT_BARS velas M15, mismo SL, TPs desde el límite):
  lim_level  en el nivel SNR de la señal (ref_level)   lim_mid  a mitad entre el cierre y ref_level
Con --live-settings la estrategia usa los ajustes de ejecución guardados en la base (como el motor vivo).
Con --free-busy (y --spread-cap) una señal con spread/SL por encima del tope NO ocupa el símbolo, como hace hoy
el bot en vivo; sin él, toda señal ocupa el símbolo hasta su resultado ("ocupación fantasma").

Uso: python tools/replay_msnr_variants.py --days 365 [--end-days-ago 365] --tag y1 --workers 6
Salida: storage/analysis/msnr_variants_signals_<tag>.csv
"""
from __future__ import annotations

import argparse
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "storage" / "analysis"
LIMIT_BARS = 8
VARIANTS = {"rr_live": (1.0, 2.0), "rr_r15": (1.0, 1.5), "rr_r3": (1.0, 3.0), "rr_1r": (1.0, 1.0), "rr_h05": (0.5, 2.0)}


def live_config():
    """Misma configuración que construye LiveTradingEngine para MSNR, con C2 off y sin allowlist."""
    from strategy.malaysian_snr.config import MalaysianSNRConfig
    return MalaysianSNRConfig(enabled=True, entry_timeframe="M15", structure_timeframe="H1",
                              tp1_min_rr=1.0, tp2_runner_rr=2.0, enable_c2_fx_metals_atr_cap=False,
                              min_adx=30.0, c2_fx_metals_max_sl_atr=1.2, c2_default_max_sl_atr=1.5,
                              allowed_symbols=())


def frames_until(mt5, symbol, days, end):
    frames = {}
    for tf, const, extra in (("M15", mt5.TIMEFRAME_M15, 5), ("H1", mt5.TIMEFRAME_H1, 10), ("D1", mt5.TIMEFRAME_D1, 40)):
        rates = mt5.copy_rates_range(symbol, const, end - timedelta(days=days + extra), end)
        if rates is None or len(rates) < 50:
            return None
        df = pd.DataFrame(rates)
        df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)
        frames[tf] = df
    return frames


def run_symbol(symbol, days, end_days_ago, limit=False, live_settings=None, free_busy=False, spread_cap=0.02):
    import MetaTrader5 as mt5
    from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy, is_fx_or_metal_symbol, is_synthetic_symbol
    from strategy.malaysian_snr.config import MalaysianSNRConfig
    from tools.replay_msnr_live_faithful import HistoricalProvider, simulate

    if not mt5.initialize():
        return symbol, [], "MT5_INIT"
    mt5.symbol_select(symbol, True)
    frames = frames_until(mt5, symbol, days, datetime.now(timezone.utc) - timedelta(days=end_days_ago))
    info = mt5.symbol_info(symbol)
    mt5.shutdown()
    if frames is None or info is None:
        return symbol, [], "SIN_DATOS"
    spread = float(info.spread) * float(info.point)
    cfg = live_config()
    allow = {a.strip().lower().removesuffix("micro") for a in MalaysianSNRConfig().allowed_symbols}
    provider = HistoricalProvider(frames)
    strat = MalaysianSNRStrategy(provider, cfg, runtime_settings_loader=(lambda: dict(live_settings)) if live_settings else None)
    m15 = frames["M15"].reset_index(drop=True)
    h, l, c, o = (m15[k].values.astype(float) for k in ("high", "low", "close", "open"))
    start_cut = m15["time"].iloc[-1] - pd.Timedelta(days=days)
    mid_cut = start_cut + pd.Timedelta(days=days / 2)
    rows, busy, seen = [], -1, set()
    n = len(m15)
    for i in range(100, n - 2):
        if m15["time"].iloc[i] < start_cut or i <= busy:
            continue
        provider.now = m15["time"].iloc[i] + pd.Timedelta(minutes=15)
        res = strat.analyze_symbol(symbol, now_utc=provider.now.to_pydatetime())
        if not res.get("valid"):
            continue
        sig = res["signal"]
        sid = sig.get("setup_id")
        if sid and sid in seen:
            continue
        d, sl = sig["direction"], float(sig["stop_loss"])
        sign = 1 if d == "BUY" else -1
        fill = o[i + 1] + (spread if d == "BUY" else 0.0)
        risk = sign * (fill - sl)
        if risk <= 0:
            continue
        if free_busy and spread / risk > spread_cap:
            continue  # descartada por spread: en vivo el símbolo queda libre
        room = None
        if sig.get("obstacle_level"):
            room = sign * (float(sig["tp2_price"]) - fill) / risk
            if room < 1.0:
                continue
        rec = dict(symbol=symbol, time=str(provider.now), period="H1" if provider.now < mid_cut else "H2",
                   direction=d, scenario=sig.get("scenario"), adx=float(sig.get("adx") or sig.get("momentum_adx") or np.nan),
                   body_ratio=sig.get("body_ratio"), risk_atr=risk / float(sig["atr"]) if sig.get("atr") else np.nan,
                   spread_sl=spread / risk, hour_utc=provider.now.hour, weekday=provider.now.dayofweek,
                   entry_confirmation=sig.get("entry_confirmation"), freshness=(sig.get("freshness") or {}).get("state"),
                   obstacle_room_rr=room, synthetic=is_synthetic_symbol(symbol), fx_metal=is_fx_or_metal_symbol(symbol),
                   in_allowlist=symbol.strip().lower().removesuffix("micro") in allow)
        future_end = n - 1
        args = (h[i + 1:future_end], l[i + 1:future_end], c[i + 1:future_end])
        kw = dict(opens=o[i + 1:future_end], spreads=np.full(future_end - i - 1, spread),
                  leg1_weight=cfg.leg1_risk_ratio, leg2_weight=cfg.leg2_risk_ratio)
        live_bars = None
        for name, (tp1_rr, tp2_rr) in VARIANTS.items():
            if room is not None:
                tp2_rr = min(tp2_rr, room)
            rr, out, bars = simulate(d, fill, sl, fill + sign * tp1_rr * risk, fill + sign * max(tp1_rr, tp2_rr) * risk, *args, **kw)
            rec[name], rec[name + "_out"] = rr, out
            if name == "rr_live":
                live_bars = bars
        if limit:
            ref = sig.get("ref_level")
            close_i = float(c[i])
            for lname, lpx in (("lim_level", ref), ("lim_mid", None if ref is None else (close_i + float(ref)) / 2.0)):
                if lpx is None or not (sign * (close_i - lpx) > 0 and sign * (lpx - sl) > 0):
                    rec[lname], rec[lname + "_fill"] = np.nan, "NIVEL_INVALIDO"
                    continue
                lpx = float(lpx)
                filled = None
                for j in range(i + 1, min(n - 1, i + 1 + LIMIT_BARS)):
                    if (sign > 0 and l[j] + spread <= lpx) or (sign < 0 and h[j] >= lpx):
                        filled = j
                        break
                    if (sign > 0 and l[j] <= sl) or (sign < 0 and h[j] + spread >= sl):
                        break
                if filled is None:
                    rec[lname], rec[lname + "_fill"] = np.nan, "NO_FILL"
                    continue
                lrisk = sign * (lpx - sl)
                if (sign > 0 and l[filled] <= sl) or (sign < 0 and h[filled] + spread >= sl):
                    rec[lname], rec[lname + "_fill"] = -1.0, "SL_EN_VELA_FILL"
                    continue
                largs = (h[filled + 1:future_end], l[filled + 1:future_end], c[filled + 1:future_end])
                lkw = dict(opens=o[filled + 1:future_end], spreads=np.full(max(0, future_end - filled - 1), spread),
                           leg1_weight=cfg.leg1_risk_ratio, leg2_weight=cfg.leg2_risk_ratio)
                tp2 = 2.0 if room is None else min(2.0, sign * (float(sig["tp2_price"]) - lpx) / lrisk)
                rr, out, _ = simulate(d, lpx, sl, lpx + sign * lrisk, lpx + sign * max(1.0, tp2) * lrisk, *largs, **lkw)
                rec[lname], rec[lname + "_fill"], rec[lname + "_spread_sl"] = rr, "LIMITE", spread / lrisk
        busy = i + (live_bars or 1)
        if sid:
            seen.add(sid)
        rows.append(rec)
    return symbol, rows, "OK"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=365)
    ap.add_argument("--end-days-ago", type=int, default=0)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--symbols", type=str, default="")
    ap.add_argument("--tag", type=str, default="y1")
    ap.add_argument("--limit", action="store_true")
    ap.add_argument("--live-settings", action="store_true")
    ap.add_argument("--synthetics-only", action="store_true")
    ap.add_argument("--enable-all-assets", action="store_true")
    ap.add_argument("--free-busy", action="store_true", help="las señales descartadas por spread no ocupan el símbolo")
    ap.add_argument("--spread-cap", type=float, default=0.02)
    ap.add_argument("--override", type=str, default="", help='JSON con ajustes a sobrescribir, p.ej. {"breaker_pair_mode": "shadow"}')
    args = ap.parse_args()
    if args.symbols:
        syms = [s.strip() for s in args.symbols.split(",") if s.strip()]
    else:
        from strategy.malaysian_snr.config import MalaysianSNRConfig
        base = set(pd.read_csv(OUT / "ict_faithful_365d_v2_trades.csv", usecols=["symbol"]).symbol.unique())
        base |= set(MalaysianSNRConfig().allowed_symbols)
        base |= {"EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD", "EURGBP", "EURJPY", "GBPJPY",
                 "AUDJPY", "AUDNZD", "CADCHF", "CHFJPY", "EURCHF", "GBPCAD", "EURAUD", "GBPAUD", "XAUUSD", "XAGUSD",
                 "BTCUSD", "ETHUSD", "US Tech 100", "US SP 500", "Wall Street 30", "US Oil"}
        syms = sorted(base)
    live_settings = None
    if args.live_settings:
        from database.repository import TradingRepository
        live_settings = TradingRepository(r"C:/Users/sebas/AppData/Local/BlackDaemonFx/trading_bot.sqlite3").latest_msnr_runtime_settings(source="DEMO")
        print("ajustes vivos versión", live_settings.get("version"), flush=True)
        if args.enable_all_assets:
            # Mismos ajustes que el motor vivo, pero sin desactivar activos (asset_modes 'off') para poder medirlos.
            off = sorted(k for k, v in (live_settings.get("asset_modes") or {}).items() if v == "off")
            live_settings = {**live_settings, "asset_modes": {}}
            print("activos 'off' en la base habilitados para medir:", len(off), flush=True)
        if args.override:
            import json as _json
            over = _json.loads(args.override)
            live_settings = {**live_settings, **over}
            print("ajustes sobrescritos:", over, flush=True)
    if args.synthetics_only:
        from strategy.malaysian_snr.malaysian_snr_strategy import is_synthetic_symbol
        syms = [s for s in syms if is_synthetic_symbol(s)]
    rows = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        futs = [pool.submit(run_symbol, s, args.days, args.end_days_ago, args.limit, live_settings,
                            args.free_busy, args.spread_cap) for s in syms]
        for f in as_completed(futs):
            s, rr, status = f.result()
            rows += rr
            print(f"{s}: {status} señales={len(rr)}", flush=True)
    pd.DataFrame(rows).to_csv(OUT / f"msnr_variants_signals_{args.tag}.csv", index=False)
    print("ok", len(rows))


if __name__ == "__main__":
    main()
