import csv
with open("storage/analysis/simulacion_msnr_mejoras_5y.csv", "r", encoding="utf-8") as f:
    reader = csv.reader(f)
    for r in reader:
        line = " | ".join(r)
        if any(x in line for x in ["USDCHF", "AUDCAD", "AUDUSD", "Germany 40", "Vol over"]):
            print(line)
