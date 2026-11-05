import pandas as pd

df = pd.read_csv("storage/analysis/replay_synthetics_human_criteria_comparison.csv")

for strat in ["ICT Sabri Malle (SMC)", "AMR-SMC (Step & Jump)", "Volatility SMC", "Malaysian SNR v3.2"]:
    sub = df[df["strategy"] == strat].sort_values(by="delta_r", ascending=False)
    print(f"### {strat} ({len(sub)} activos)")
    print("| Símbolo | Ops Antes | Ops Después | Vetadas | Pérdidas Evitadas | WR Antes | WR Después | Loss Antes | Loss Después | R Antes | R Después | Delta R |")
    print("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
    for _, row in sub.iterrows():
        s = row["symbol"]
        na = int(row["n_antes"])
        nd = int(row["n_despues"])
        nv = int(row["n_vetados"])
        pe = int(row["perdidas_evitadas"])
        wa = row["pct_win_antes"]
        wd = row["pct_win_despues"]
        la = row["pct_loss_antes"]
        ld = row["pct_loss_despues"]
        ra = row["r_antes"]
        rd = row["r_despues"]
        dr = row["delta_r"]
        print(f"| `{s}` | {na} | {nd} | {nv} | {pe} | {wa:.1f}% | {wd:.1f}% | {la:.1f}% | {ld:.1f}% | {ra:.2f} R | {rd:.2f} R | {dr:+.2f} R |")
    print()
