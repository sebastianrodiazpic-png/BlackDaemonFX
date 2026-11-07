import csv

for fname in ["storage/analysis/msnr_selected_audit_detailed.csv", "storage/analysis/msnr_filters_report.md", "storage/analysis/msnr_improvements_simulation_report.md"]:
    try:
        with open(fname, "r", encoding="utf-8") as f:
            for line in f:
                if any(x in line for x in ["USDCHF", "AUDCAD", "AUDUSD", "Germany 40", "Germany"]):
                    print(f"{fname}: {line.strip()[:140]}")
    except Exception as e:
        print(f"Error {fname}: {e}")
