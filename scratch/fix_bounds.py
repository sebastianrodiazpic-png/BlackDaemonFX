from pathlib import Path

target_file = Path("strategy/ict/ict_strategy.py")
text = target_file.read_text(encoding="utf-8")

text = text.replace("    if curr_idx < 6:\n        return None", "    if curr_idx < 4:\n        return None")
text = text.replace("for back in range(3, min(lookback_bars, curr_idx - 2)):", "for back in range(1, min(lookback_bars, curr_idx - 1)):")

target_file.write_text(text, encoding="utf-8")
print("Bounds updated successfully!")
