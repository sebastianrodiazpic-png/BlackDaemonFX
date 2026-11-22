"""
scratch/print_both_tables.py
"""
import sys
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

df = pd.read_csv("storage/analysis/replay_5y_perfect_strategy_bases.csv")

SYNTHETICS_38 = [
    "Crash 300 Index", "Crash 500 Index", "Crash 600 Index", "Crash 900 Index", "Crash 1000 Index",
    "Boom 300 Index", "Boom 500 Index", "Boom 600 Index", "Boom 900 Index", "Boom 1000 Index",
    "Step Index", "Step Index 200", "Step Index 400", "Step Index 500",
    "Jump 10 Index", "Jump 25 Index", "Jump 50 Index", "Jump 75 Index", "Jump 100 Index",
    "Volatility 5 Index", "Volatility 10 Index", "Volatility 15 Index", "Volatility 25 Index",
    "Volatility 50 Index", "Volatility 75 Index", "Volatility 90 Index", "Volatility 100 Index",
    "Volatility 50 (1s) Index", "Volatility 75 (1s) Index", "Volatility 90 (1s) Index",
    "Volatility 100 (1s) Index", "Volatility 150 (1s) Index", "Volatility 250 (1s) Index",
    "Vol over Boom 550", "Vol over Crash 550", "VolSwitch High Vol Index",
    "High Frequency Vol 50 Index", "High Frequency Vol 100 Index"
]

for strat, title in [("Malaysian SNR", "MALAYSIAN SNR (H1 Break / M15 Retest) - 38 Sinteticos Deriv"),
                     ("ICT Sabri Malle", "ICT SABRI MALLE (FVG, Mitigacion & MSS) - 38 Sinteticos Deriv")]:
    print(f"\n## {title}\n")
    print("| Instrumento | Trades Antes | WR Antes | PnL Antes ($) | Trades Después | WR Después | PnL Después ($) | Δ WR | Δ PnL ($) |")
    print("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
    sub = df[df["strategy"] == strat]
    for sym in SYNTHETICS_38:
        row = sub[sub["symbol"] == sym].iloc[0]
        ta = int(row["trades_antes"])
        wra = f"{row['wr_antes']:.1f}%"
        pnla = f"+${row['pnl_antes']:,.2f}"
        td = int(row["trades_despues"])
        wrd = f"{row['wr_despues']:.1f}%"
        pnld = f"+${row['pnl_despues']:,.2f}"
        dwr = f"+{row['delta_wr']:.1f} pp"
        dpnl = f"+${row['delta_pnl']:,.2f}"
        print(f"| **{sym}** | {ta} | {wra} | {pnla} | {td} | {wrd} | {pnld} | {dwr} | {dpnl} |")
