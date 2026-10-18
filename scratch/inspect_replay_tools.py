from pathlib import Path

ROOT = Path("c:/TradingBoot/smc_synthetic_bot")

replay_tools = [
    ROOT / "tools/replay_gold_quarters_augmented.py",
    ROOT / "tools/replay_orb_nunez_2y.py",
    ROOT / "tools/replay_ict_60_assets_2year_audit.py",
    ROOT / "tools/replay_msnr_two_year_comparison.py"
]

print("=== INSPECTING EXISTING REPLAY TOOLS ===")
for t in replay_tools:
    if t.exists():
        src = t.read_text(encoding="utf-8-sig")
        lines = src.splitlines()
        print(f"\nTool: {t.name} ({len(lines)} lines)")
        # Print docstring or first 30 lines
        for l in lines[:35]:
            print("  ", l)
    else:
        print(f"\nTool: {t.name} does not exist.")
