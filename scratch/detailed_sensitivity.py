import sys
import sqlite3
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.prospective_m1_replay_runner import ProspectiveM1ReplayRunner

def evaluate_scenarios():
    db_path = PROJECT_ROOT / "storage" / "runtime" / "shadow_research_staging.sqlite3"
    arch_dir = PROJECT_ROOT / "storage" / "runtime" / "m1_prospective_cache"

    scenarios = [
        ("1. Ideal Signal Entry (Cero delay, Spread típico, 0.00R fricción)", "signal_entry", 0.0),
        ("2. Signal Entry + Fricción Leve (0.05R slippage/costo)", "signal_entry", 0.05),
        ("3. Signal Entry + Fricción Fuerte (0.10R slippage/costo)", "signal_entry", 0.10),
        ("4. Latencia de Polling (Fill en 1ra vela M1 >= created_at, 0.00R fricción)", "created_at", 0.0),
        ("5. Latencia de Polling + Fricción Leve (created_at + 0.05R slippage)", "created_at", 0.05),
    ]

    conn = sqlite3.connect(f"file:{db_path.resolve()}?mode=ro", uri=True)
    df_stg = pd.read_sql_query("SELECT * FROM shadow_signals WHERE timestamp >= '2026-10-15T17:35:16.304722+00:00' ORDER BY id ASC", conn)
    conn.close()

    ict_events = df_stg[(df_stg["strategy"] == "ICT") & (df_stg["variant"] == "base")].copy()
    msnr_events = df_stg[(df_stg["strategy"] == "MSNR") & (df_stg["variant"] == "enabled_19_h4_fresh")].copy()

    for title, fill_m, cost in scenarios:
        runner = ProspectiveM1ReplayRunner(
            db_path=db_path,
            dry_run=True,
            fill_mode=fill_m,
            cost_r=cost,
            archive_dir=arch_dir
        )
        # Load cache offline
        runner.fetch_market_data(["Boom 500 Index", "Crash 300 Index", "Boom 600 Index", "Jump 10 Index", "Crash 600 Index", "Boom 300 Index"])

        print(f"\n{'='*85}")
        print(f"ESCENARIO: {title}")
        print(f"{'='*85}")

        print("--- ICT SABRI MALLE (7 EVENTOS) ---")
        ict_results = []
        for _, r in ict_events.iterrows():
            sig_t = pd.to_datetime(r["timestamp"], utc=True)
            feat = r["features_json"]
            # parse feat
            import json
            f_dict = json.loads(feat) if feat else {}
            created_at_str = f_dict.get("created_at_live", r["timestamp"])
            cre_t = pd.to_datetime(created_at_str, utc=True)

            sim = runner.simulate_trade_m1(
                r["symbol"], r["direction"], sig_t, cre_t,
                r["entry_price"], r["stop_loss"], r["take_profit_1"], r["take_profit_2"],
                fill_mode=fill_m
            )
            ict_results.append({
                "id": r["id"],
                "symbol": r["symbol"],
                "dir": r["direction"],
                "sig_t": r["timestamp"][-14:-6],
                "outcome": sim["outcome"],
                "fill_p": sim["fill_price"],
                "bars": sim["bars_held"],
                "rr": sim["realized_rr"]
            })
            print(f"  Ev ID {r['id']:<2} | {r['symbol']:<16} {r['direction']:<4} | Sig: {r['timestamp'][-14:-6]} | Fill: {sim['fill_price']:<10.2f} | Out: {sim['outcome']:<20} | Barras: {sim['bars_held']:<3} | Net RR: {sim['realized_rr']:+.2f}R")

        df_ict_res = pd.DataFrame(ict_results)
        wins_i = df_ict_res[df_ict_res["rr"] > 0]["rr"].sum()
        loss_i = abs(df_ict_res[df_ict_res["rr"] < 0]["rr"].sum())
        net_i = df_ict_res["rr"].sum()
        pf_i = (wins_i / loss_i) if loss_i > 0 else 999.0

        # Drawdown acumulado
        cum = [0.0]
        for x in df_ict_res["rr"]:
            cum.append(cum[-1] + x)
        peaks = [cum[0]]
        dds = [0.0]
        for c in cum[1:]:
            p = max(peaks[-1], c)
            peaks.append(p)
            dds.append(p - c)
        max_dd_i = max(dds)

        print(f"  >> ICT TOTAL: Net PnL = {net_i:+.2f}R | Wins = {wins_i:.2f}R | Losses = {loss_i:.2f}R | PF = {pf_i:.2f} | MaxDD = {max_dd_i:.2f}R")

        print("\n--- MALAYSIAN SNR (5 EVENTOS: 3 ACEPTADOS, 2 FILTRADOS) ---")
        msnr_results = []
        for _, r in msnr_events.iterrows():
            sig_t = pd.to_datetime(r["timestamp"], utc=True)
            feat = r["features_json"]
            import json
            f_dict = json.loads(feat) if feat else {}
            created_at_str = f_dict.get("created_at_live", r["timestamp"])
            cre_t = pd.to_datetime(created_at_str, utc=True)

            if r["final_action"] == "DISCARDED_BY_FILTER":
                cf = runner.simulate_trade_m1(
                    r["symbol"], r["direction"], sig_t, cre_t,
                    r["entry_price"], r["stop_loss"], r["take_profit_1"], r["take_profit_2"],
                    fill_mode=fill_m
                )
                print(f"  Ev ID {r['id']:<2} | {r['symbol']:<16} {r['direction']:<4} | Sig: {r['timestamp'][-14:-6]} | FILTRADA H4 (AVOIDED / 0.00R) [Contrafactual: {cf['outcome']} {cf['realized_rr']:+.2f}R]")
            else:
                sim = runner.simulate_trade_m1(
                    r["symbol"], r["direction"], sig_t, cre_t,
                    r["entry_price"], r["stop_loss"], r["take_profit_1"], r["take_profit_2"],
                    fill_mode=fill_m
                )
                msnr_results.append({
                    "id": r["id"],
                    "symbol": r["symbol"],
                    "rr": sim["realized_rr"]
                })
                print(f"  Ev ID {r['id']:<2} | {r['symbol']:<16} {r['direction']:<4} | Sig: {r['timestamp'][-14:-6]} | Fill: {sim['fill_price']:<10.2f} | Out: {sim['outcome']:<20} | Barras: {sim['bars_held']:<3} | Net RR: {sim['realized_rr']:+.2f}R")

        df_m_res = pd.DataFrame(msnr_results)
        wins_m = df_m_res[df_m_res["rr"] > 0]["rr"].sum()
        loss_m = abs(df_m_res[df_m_res["rr"] < 0]["rr"].sum())
        net_m = df_m_res["rr"].sum()
        pf_m = (wins_m / loss_m) if loss_m > 0 else 999.0
        print(f"  >> MSNR TOTAL: Net PnL = {net_m:+.2f}R | Wins = {wins_m:.2f}R | Losses = {loss_m:.2f}R | PF = {pf_m:.2f}")

if __name__ == "__main__":
    evaluate_scenarios()
