import json
from pathlib import Path
import re
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

BRAIN_TASKS = Path(r"C:\Users\sebas\.gemini\antigravity\brain\474c9ef2-c70f-4b7c-a1f6-f59f9875d589\.system_generated\tasks")

# Leer los logs de las 3 tareas
log_step = (BRAIN_TASKS / "task-901.log").read_text(encoding="utf-8", errors="replace")
log_vol = (BRAIN_TASKS / "task-935.log").read_text(encoding="utf-8", errors="replace")
log_jump = (BRAIN_TASKS / "task-955.log").read_text(encoding="utf-8", errors="replace")

combined_logs = log_step + "\n" + log_vol + "\n" + log_jump

pattern = re.compile(
    r"\[RESULTADOS\s+(?P<symbol>[^\]]+)\]\s+"
    r"Directo 1:2:\s+Trades=(?P<d_trades>\d+)\s+\|\s+Wins=(?P<d_wins>\d+)\s+\|\s+Losses=(?P<d_losses>\d+)\s+\|\s+WinRate=(?P<d_wr>[\d\.]+)%\s+\|\s+Total R=(?P<d_r>[+-]?[\d\.]+)R\s+\|\s+Exp=(?P<d_exp>[+-]?[\d\.]+)R\s+"
    r"Con BE @ 1R:\s+Trades=(?P<b_trades>\d+)\s+\|\s+Wins=(?P<b_wins>\d+)\s+\|\s+BE=(?P<b_be>\d+)\s+\|\s+Losses=(?P<b_losses>\d+)\s+\|\s+Total R=(?P<b_r>[+-]?[\d\.]+)R\s+\|\s+Exp=(?P<b_exp>[+-]?[\d\.]+)R\s+"
    r"Pérdidas que llegaron a \+1\.0R:\s+(?P<mfe_reach>\d+)\s+de\s+(?P<mfe_tot>\d+)\s+\((?P<mfe_pct>[\d\.]+)%\)\s+"
    r"ADX Promedio:\s+Wins=(?P<adx_win>[\d\.]+)\s+vs\s+Losses=(?P<adx_loss>[\d\.]+)"
)

results = []
for match in pattern.finditer(combined_logs):
    d = match.groupdict()
    sym = d["symbol"].strip()
    fam = "STEP" if "step" in sym.lower() else ("VOLATILITY" if "volatility" in sym.lower() else "JUMP")
    results.append({
        "family": fam,
        "symbol": sym,
        "direct_trades": int(d["d_trades"]),
        "direct_wins": int(d["d_wins"]),
        "direct_losses": int(d["d_losses"]),
        "direct_win_rate": float(d["d_wr"]),
        "direct_total_r": float(d["d_r"]),
        "direct_expectancy_r": float(d["d_exp"]),
        "be_trades": int(d["b_trades"]),
        "be_wins": int(d["b_wins"]),
        "be_be": int(d["b_be"]),
        "be_losses": int(d["b_losses"]),
        "be_total_r": float(d["b_r"]),
        "be_expectancy_r": float(d["b_exp"]),
        "mfe_reached_1r": int(d["mfe_reach"]),
        "total_losses": int(d["mfe_tot"]),
        "mfe_pct": float(d["mfe_pct"]),
        "adx_wins": float(d["adx_win"]),
        "adx_losses": float(d["adx_loss"]),
    })

df = pd.DataFrame(results)
print("=== REPLAY RESULTS 180 DÍAS (6 MESES) - CONSOLIDADO ===")
print(df.to_string(index=False))

# Guardar a storage/analysis/
out_csv = PROJECT_ROOT / "storage/analysis/consolidated_replay_step_vol_jump_180d.csv"
df.to_csv(out_csv, index=False)
print(f"\nGuardado en {out_csv}")
