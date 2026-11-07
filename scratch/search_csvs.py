import csv, glob

files = glob.glob("storage/analysis/*msnr*.csv")
print("Found files:", len(files))
for f in files:
    try:
        with open(f, "r", encoding="utf-8") as fp:
            reader = csv.reader(fp)
            header = next(reader, None)
            rows = list(reader)
            for r in rows:
                row_str = " ".join(r)
                if any(x in row_str for x in ["USDCHF", "AUDCAD", "AUDUSD", "Germany", "GER40"]):
                    print(f"File {f}: {row_str[:120]}")
    except Exception:
        pass
