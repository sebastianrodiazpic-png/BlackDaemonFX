import sqlite3

DBS = [
    ("PROSPECTIVE", "storage/runtime/shadow_research.sqlite3"),
    ("STAGING", "storage/runtime/shadow_research_staging.sqlite3"),
]

lines = []
for name, path in DBS:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    cur = conn.cursor()
    lines.append(f"============================================================")
    lines.append(f"{name}: {path}")
    lines.append(f"============================================================")
    cur.execute("SELECT MIN(timestamp), MAX(timestamp), COUNT(*) FROM shadow_signals")
    lines.append(f"All signals (min_ts, max_ts, count): {cur.fetchone()}")
    cur.execute("SELECT strategy, COUNT(*), MIN(timestamp), MAX(timestamp) FROM shadow_signals GROUP BY strategy")
    for row in cur.fetchall():
        lines.append(f"  Strategy summary: {row}")
    cur.execute(
        "SELECT variant, final_action, simulated_outcome, market_outcome, COUNT(*), COALESCE(SUM(simulated_rr), 0.0), COALESCE(SUM(market_rr), 0.0) "
        "FROM shadow_signals WHERE strategy='MSNR' "
        "GROUP BY variant, final_action, simulated_outcome, market_outcome"
    )
    lines.append("\nMSNR Breakdown by (variant, final_action, simulated_outcome, market_outcome):")
    for row in cur.fetchall():
        lines.append(f"  {row}")
    lines.append("\nAll MSNR rows ordered by id:")
    cur.execute(
        "SELECT id, timestamp, symbol, direction, variant, mechanical_decision, rejection_reason, "
        "final_action, simulated_outcome, simulated_rr, market_outcome, market_rr, entry_price, stop_loss, take_profit_1 "
        "FROM shadow_signals WHERE strategy='MSNR' ORDER BY id"
    )
    for row in cur.fetchall():
        lines.append(f"  {row}")
    conn.close()

with open("scratch/audit_shadow_cohorts_ro_output.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print("Saved scratch/audit_shadow_cohorts_ro_output.txt")
