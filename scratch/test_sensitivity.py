import sys
import sqlite3
import pandas as pd
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools.prospective_m1_replay_runner import ProspectiveM1ReplayRunner

def run_sensitivity():
    db_path = Path("storage/runtime/shadow_research_staging.sqlite3")
    arch_dir = Path("storage/runtime/m1_prospective_cache")

    scenarios = [
        ("Base signal_entry (0.0R)", "signal_entry", 0.0),
        ("Latency created_at (0.0R)", "created_at", 0.0),
        ("Friction cost_r=0.05R", "signal_entry", 0.05),
        ("Friction cost_r=0.10R", "signal_entry", 0.10),
        ("Latency + Friction 0.05R", "created_at", 0.05),
    ]

    for label, fill_m, cost in scenarios:
        runner = ProspectiveM1ReplayRunner(
            db_path=db_path,
            dry_run=True,
            fill_mode=fill_m,
            cost_r=cost,
            archive_dir=arch_dir
        )
        runner.execute_replay()

        # Recoger resultados de ICT y MSNR para cohorte prospectiva
        # Leemos staging de nuevo pero usando runner.cache_m1 y simulate
        conn = sqlite3.connect(f"file:{db_path.resolve()}?mode=ro", uri=True)
        df = pd.read_sql_query("SELECT * FROM shadow_signals WHERE timestamp >= '2026-10-15T17:35:16.304722+00:00'", conn)
        conn.close()

        ict_rrs = []
        msnr_rrs = []

        for _, r in df.iterrows():
            if r["strategy"] == "ICT" and r["variant"] == "base":
                feat = pd.Series(r)
                sim = runner.simulate_trade_m1(
                    r["symbol"], r["direction"],
                    pd.to_datetime(r["timestamp"], utc=True),
                    pd.to_datetime(r["timestamp"], utc=True),
                    r["entry_price"], r["stop_loss"], r["take_profit_1"], r["take_profit_2"],
                    fill_mode=fill_m
                )
                ict_rrs.append(sim["realized_rr"])
            elif r["strategy"] == "MSNR" and r["variant"] == "enabled_19_h4_fresh":
                if r["final_action"] == "ACCEPTED_EXECUTION":
                    sim = runner.simulate_trade_m1(
                        r["symbol"], r["direction"],
                        pd.to_datetime(r["timestamp"], utc=True),
                        pd.to_datetime(r["timestamp"], utc=True),
                        r["entry_price"], r["stop_loss"], r["take_profit_1"], r["take_profit_2"],
                        fill_mode=fill_m
                    )
                    msnr_rrs.append(sim["realized_rr"])

        ict_wins = sum([x for x in ict_rrs if x > 0])
        ict_loss = sum([abs(x) for x in ict_rrs if x < 0])
        ict_net = sum(ict_rrs)
        ict_pf = (ict_wins / ict_loss) if ict_loss > 0 else 999.0

        msnr_wins = sum([x for x in msnr_rrs if x > 0])
        msnr_loss = sum([abs(x) for x in msnr_rrs if x < 0])
        msnr_net = sum(msnr_rrs)
        msnr_pf = (msnr_wins / msnr_loss) if msnr_loss > 0 else 999.0

        print(f"\n[ESCENARIO: {label}]")
        print(f"  ICT  (N=7): Net RR = {ict_net:+.2f}R | Wins = {ict_wins:.2f}R | Loss = {ict_loss:.2f}R | PF = {ict_pf:.2f}")
        print(f"  MSNR (N=3): Net RR = {msnr_net:+.2f}R | Wins = {msnr_wins:.2f}R | Loss = {msnr_loss:.2f}R | PF = {msnr_pf:.2f}")

if __name__ == "__main__":
    run_sensitivity()
