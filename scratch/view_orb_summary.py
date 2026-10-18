import json
from pathlib import Path

path = Path("storage/analysis/orb_improvements_audit/audit_summary.json")
data = json.loads(path.read_text(encoding="utf-8"))

print(f"{'SYMBOL':15s} | {'BASELINE':10s} | {'VAR1(11:30)':11s} | {'VAR2(HQ)':10s} | {'VAR3(PDH/L)':11s} | {'VAR5(TP1.5)':11s} | {'WR BASE':8s} | {'WR VAR1':8s} | {'WR VAR3':8s}")
print("-" * 110)
for s, m in data["by_symbol"].items():
    b_r = m.get("BASELINE_CURRENT", {}).get("net_r", 0)
    v1_r = m.get("VAR1_CUTOFF_1130", {}).get("net_r", 0)
    v2_r = m.get("VAR2_HIGH_QUALITY_RETEST", {}).get("net_r", 0)
    v3_r = m.get("VAR3_MACRO_LIQUIDITY", {}).get("net_r", 0)
    v5_r = m.get("VAR5_CALIBRATED_TP", {}).get("net_r", 0)
    b_wr = m.get("BASELINE_CURRENT", {}).get("global_winrate_pct", 0)
    v1_wr = m.get("VAR1_CUTOFF_1130", {}).get("global_winrate_pct", 0)
    v3_wr = m.get("VAR3_MACRO_LIQUIDITY", {}).get("global_winrate_pct", 0)
    print(f"{s:15s} | {b_r:+8.2f}R | {v1_r:+9.2f}R | {v2_r:+8.2f}R | {v3_r:+9.2f}R | {v5_r:+9.2f}R | {b_wr:6.1f}% | {v1_wr:6.1f}% | {v3_wr:6.1f}%")

print("-" * 110)
gm = data["global_metrics"]
for var, m in gm.items():
    print(f"{var:26s} | Trades: {m['trades']:4d} | WR TP1: {m['tp1_winrate_pct']:4.1f}% | WR TP2: {m['tp2_winrate_pct']:4.1f}% | Net R: {m['net_r']:+7.2f}R | PF: {m['profit_factor']:.2f} | DD: {m['max_drawdown_r']:.1f}R")
