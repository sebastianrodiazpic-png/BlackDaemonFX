from pathlib import Path

target_file = Path("strategy") / "execution" / "live_trading_engine.py"
print("Exists:", target_file.exists())
try:
    with open(target_file, "r+", encoding="utf-8") as f:
        print("Opened r+ successfully")
except Exception as e:
    print("Error opening:", e)
