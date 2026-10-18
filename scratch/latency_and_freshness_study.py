import sys
import sqlite3
import json
import pandas as pd
import numpy as np
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.prospective_m1_replay_runner import ProspectiveM1ReplayRunner

def run_study():
    db_path = PROJECT_ROOT / "storage" / "runtime" / "shadow_research_staging.sqlite3"
    arch_dir = PROJECT_ROOT / "storage" / "runtime" / "m1_prospective_cache"

    conn = sqlite3.connect(f"file:{db_path.resolve()}?mode=ro", uri=True)
    df = pd.read_sql_query("SELECT * FROM shadow_signals WHERE timestamp >= '2026-10-15T17:35:16.304722+00:00' ORDER BY id ASC", conn)
    conn.close()

    runner = ProspectiveM1ReplayRunner(
        db_path=db_path,
        dry_run=True,
        archive_dir=arch_dir
    )
    runner.fetch_market_data(["Boom 500 Index", "Crash 300 Index", "Boom 600 Index", "Jump 10 Index", "Crash 600 Index", "Boom 300 Index"])

    ict_events = df[(df["strategy"] == "ICT") & (df["variant"] == "base")].copy()
    msnr_events = df[(df["strategy"] == "MSNR") & (df["variant"] == "enabled_19_h4_fresh")].copy()

    print("=========================================================================================")
    print("1. AUDITORÍA DE TIMESTAMPS Y DELTAS DE INGESTIÓN (PROXY DE LATENCIA)")
    print("=========================================================================================")
    print(f"{'Strat':<4} | {'ID':<2} | {'Symbol':<16} | {'Direction':<4} | {'signal_time (UTC)':<20} | {'created_at (UTC)':<20} | {'Delta (min)':<11} | {'Action':<19}")
    print("-" * 105)

    all_prosp = pd.concat([ict_events, msnr_events]).sort_values("id")
    for _, r in all_prosp.iterrows():
        feat = json.loads(r["features_json"]) if r["features_json"] else {}
        cre_str = feat.get("created_at_live", r["timestamp"])
        t_sig = pd.to_datetime(r["timestamp"], utc=True)
        t_cre = pd.to_datetime(cre_str, utc=True)
        delta_min = (t_cre - t_sig).total_seconds() / 60.0
        print(f"{r['strategy']:<4} | {r['id']:<2} | {r['symbol']:<16} | {r['direction']:<4} | {r['timestamp'][:19]:<20} | {cre_str[:19]:<20} | {delta_min:>8.2f} m | {r['final_action']:<19}")

    print("\n=========================================================================================")
    print("2. BARRIDO DE SENSIBILIDAD POR MINUTOS DE RETRASO EN LA ENTRADA (M1 STEPS)")
    print("=========================================================================================")
    print("Definición: La entrada se ejecuta en la barra M1 con time >= signal_time + delay_minutes.")
    print("-" * 95)
    header = f"{'Demora':<12} | {'ICT Net RR':<11} | {'ICT Wins':<10} | {'ICT Loss':<10} | {'ICT PF':<8} | {'ICT MaxDD':<10} | {'MSNR Net RR':<12} | {'MSNR PF'}"
    print(header)
    print("-" * 95)

    delays = [0, 1, 2, 3, 4, 5, 10, 15]

    def simulate_with_exact_delay(events_df, delay_min, strat_name, cost_r=0.0):
        results = []
        for _, r in events_df.iterrows():
            if strat_name == "MSNR" and r["final_action"] == "DISCARDED_BY_FILTER":
                continue
            sig_t = pd.to_datetime(r["timestamp"], utc=True)
            # Entrada simulada con retraso exacto de delay_min
            sim_entry_time = sig_t + pd.Timedelta(minutes=delay_min)
            bars = runner.cache_m1.get(r["symbol"])
            future = bars[bars["time"] >= sim_entry_time].copy().reset_index(drop=True)
            if future.empty:
                results.append(0.0)
                continue
            
            # fill en la primera barra disponible tras delay
            sim = runner.simulate_trade_m1(
                r["symbol"], r["direction"],
                signal_time=sig_t,
                created_at=sim_entry_time,
                entry_target=r["entry_price"],
                sl=r["stop_loss"],
                tp1_target=r["take_profit_1"],
                tp2_target=r["take_profit_2"],
                fill_mode="created_at"
            )
            # adjust cost
            rr = sim["realized_rr"] - cost_r
            results.append(rr)

        wins = sum([x for x in results if x > 0])
        loss = abs(sum([x for x in results if x < 0]))
        net = sum(results)
        pf = (wins / loss) if loss > 0 else (999.0 if wins > 0 else 0.0)

        cum = [0.0]
        for x in results:
            cum.append(cum[-1] + x)
        peaks = [cum[0]]
        dds = [0.0]
        for c in cum[1:]:
            p = max(peaks[-1], c)
            peaks.append(p)
            dds.append(p - c)
        max_dd = max(dds) if dds else 0.0

        return net, wins, loss, pf, max_dd

    for d in delays:
        net_i, w_i, l_i, pf_i, dd_i = simulate_with_exact_delay(ict_events, d, "ICT", cost_r=0.0)
        net_m, w_m, l_m, pf_m, dd_m = simulate_with_exact_delay(msnr_events, d, "MSNR", cost_r=0.0)
        label = f"+{d} min" if d > 0 else "0 min (Ideal)"
        print(f"{label:<12} | {net_i:>+7.2f} R    | {w_i:>6.2f} R   | {l_i:>6.2f} R   | {pf_i:>6.2f} | {dd_i:>6.2f} R   | {net_m:>+8.2f} R    | {pf_m:>6.2f}")

    print("-" * 95)
    # También concreated_at real
    # Para ICT
    ict_cre_rrs = []
    for _, r in ict_events.iterrows():
        feat = json.loads(r["features_json"]) if r["features_json"] else {}
        cre_t = pd.to_datetime(feat.get("created_at_live", r["timestamp"]), utc=True)
        sig_t = pd.to_datetime(r["timestamp"], utc=True)
        sim = runner.simulate_trade_m1(
            r["symbol"], r["direction"], sig_t, cre_t,
            r["entry_price"], r["stop_loss"], r["take_profit_1"], r["take_profit_2"],
            fill_mode="created_at"
        )
        ict_cre_rrs.append(sim["realized_rr"])
    w_ic = sum([x for x in ict_cre_rrs if x > 0])
    l_ic = abs(sum([x for x in ict_cre_rrs if x < 0]))
    net_ic = sum(ict_cre_rrs)
    pf_ic = (w_ic / l_ic) if l_ic > 0 else 0.0

    # Para MSNR
    msnr_cre_rrs = []
    for _, r in msnr_events.iterrows():
        if r["final_action"] == "DISCARDED_BY_FILTER":
            continue
        feat = json.loads(r["features_json"]) if r["features_json"] else {}
        cre_t = pd.to_datetime(feat.get("created_at_live", r["timestamp"]), utc=True)
        sig_t = pd.to_datetime(r["timestamp"], utc=True)
        sim = runner.simulate_trade_m1(
            r["symbol"], r["direction"], sig_t, cre_t,
            r["entry_price"], r["stop_loss"], r["take_profit_1"], r["take_profit_2"],
            fill_mode="created_at"
        )
        msnr_cre_rrs.append(sim["realized_rr"])
    w_mc = sum([x for x in msnr_cre_rrs if x > 0])
    l_mc = abs(sum([x for x in msnr_cre_rrs if x < 0]))
    net_mc = sum(msnr_cre_rrs)
    pf_mc = (w_mc / l_mc) if l_mc > 0 else 0.0

    print(f"{'created_at':<12} | {net_ic:>+7.2f} R    | {w_ic:>6.2f} R   | {l_ic:>6.2f} R   | {pf_ic:>6.2f} | {'N/A':<10} | {net_mc:>+8.2f} R    | {pf_mc:>6.2f}")

    print("\n=========================================================================================")
    print("3. EVALUACIÓN DE REGLA EXPERIMENTAL DE CADUCIDAD DE SEÑAL (FRESHNESS GUARD)")
    print("=========================================================================================")
    print("Hipótesis: Si delta_min > Max_Staleness, la señal se DESCARTA (EXPIRED / 0.0R) en vez de ejecutarse tarde.")
    print("-" * 95)
    
    thresholds = [1, 2, 3, 5, 8, 10, 15]
    print(f"{'Umbral Max (T_max)':<20} | {'ICT Operados':<14} | {'ICT Expirados':<14} | {'ICT Net PnL (R)':<16} | {'ICT PF'}")
    print("-" * 95)

    for t_max in thresholds:
        executed_rrs = []
        n_expired = 0
        n_exec = 0
        for _, r in ict_events.iterrows():
            feat = json.loads(r["features_json"]) if r["features_json"] else {}
            cre_str = feat.get("created_at_live", r["timestamp"])
            t_sig = pd.to_datetime(r["timestamp"], utc=True)
            t_cre = pd.to_datetime(cre_str, utc=True)
            delta_min = (t_cre - t_sig).total_seconds() / 60.0

            if delta_min > t_max:
                n_expired += 1
                # Descartada por caducidad: no se ejecuta, PnL = 0.0R
                executed_rrs.append(0.0)
            else:
                n_exec += 1
                # Se ejecuta en created_at
                sim = runner.simulate_trade_m1(
                    r["symbol"], r["direction"], t_sig, t_cre,
                    r["entry_price"], r["stop_loss"], r["take_profit_1"], r["take_profit_2"],
                    fill_mode="created_at"
                )
                executed_rrs.append(sim["realized_rr"])

        wins = sum([x for x in executed_rrs if x > 0])
        loss = abs(sum([x for x in executed_rrs if x < 0]))
        net = sum(executed_rrs)
        pf = (wins / loss) if loss > 0 else (999.0 if wins > 0 else 0.0)
        print(f"T_max <= {t_max:>2} min       | {n_exec:<14} | {n_expired:<14} | {net:>+10.2f} R        | {pf:>6.2f}")

    print("\n=========================================================================================")
    print("4. COMPARATIVA DE PRECIOS: SIGNAL TARGET vs OPEN(SIG_TIME) vs OPEN(CREATED_AT)")
    print("=========================================================================================")
    header_p = f"{'ID':<2} | {'Symbol':<16} | {'Dir':<4} | {'Signal Target':<14} | {'Open(SigTime)':<14} | {'Open(CreatedAt)':<16} | {'Slippage CreatedAt':<18} | {'RR(SigEntry)':<13} | {'RR(CreatedAt)'}"
    print(header_p)
    print("-" * 115)

    for _, r in ict_events.iterrows():
        feat = json.loads(r["features_json"]) if r["features_json"] else {}
        sig_t = pd.to_datetime(r["timestamp"], utc=True)
        cre_t = pd.to_datetime(feat.get("created_at_live", r["timestamp"]), utc=True)
        bars = runner.cache_m1[r["symbol"]]
        
        b_sig = bars[bars["time"] >= sig_t]
        open_sig = b_sig["open"].iloc[0] if not b_sig.empty else 0.0
        
        b_cre = bars[bars["time"] >= cre_t]
        open_cre = b_cre["open"].iloc[0] if not b_cre.empty else 0.0
        
        # Slippage adverso: si BUY, (open_cre - entry_target); si SELL, (entry_target - open_cre)
        sign = 1 if r["direction"] == "BUY" else -1
        slippage = sign * (open_cre - r["entry_price"])

        sim_sig = runner.simulate_trade_m1(
            r["symbol"], r["direction"], sig_t, sig_t,
            r["entry_price"], r["stop_loss"], r["take_profit_1"], r["take_profit_2"],
            fill_mode="signal_entry"
        )
        sim_cre = runner.simulate_trade_m1(
            r["symbol"], r["direction"], sig_t, cre_t,
            r["entry_price"], r["stop_loss"], r["take_profit_1"], r["take_profit_2"],
            fill_mode="created_at"
        )
        print(f"{r['id']:<2} | {r['symbol']:<16} | {r['direction']:<4} | {r['entry_price']:<14.3f} | {open_sig:<14.3f} | {open_cre:<16.3f} | {slippage:>+15.3f} pts | {sim_sig['realized_rr']:>+10.2f} R    | {sim_cre['realized_rr']:>+10.2f} R")

if __name__ == "__main__":
    run_study()

