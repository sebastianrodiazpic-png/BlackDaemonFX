import json, glob, os

files = glob.glob("storage/learning_audit/*.json")
print(f"Total audit json files: {len(files)}")
total_trades = 0
for fpath in sorted(files):
    if "retrain" in fpath:
        continue
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            data = json.load(f)
        worker = data.get("worker", os.path.basename(fpath))
        trades = data.get("account_trades", 0)
        total_trades += trades if isinstance(trades, int) else 0
        training_funnel = data.get("training_funnel", {})
        instruments = data.get("instruments", {})
        print(f"Worker {worker:20} | trades: {trades:5} | instruments: {len(instruments):3} | funnel: {training_funnel}")
    except Exception as e:
        print(f"Error {fpath}: {e}")
print(f"Total account trades across audits: {total_trades}")
