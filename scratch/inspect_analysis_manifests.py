from pathlib import Path
import json

ROOT = Path("c:/TradingBoot/smc_synthetic_bot")

analysis_dir = ROOT / "storage/analysis"
print("=== INSPECTING ANALYSIS REPORTS & MANIFESTS ===")

for p in analysis_dir.glob("**/history_manifest.json"):
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        print(f"\nManifest: {p.relative_to(ROOT)}")
        print(f"  Window: {data.get('start')} to {data.get('end')}")
        print(f"  Symbols count: {len(data.get('symbols', []))}")
        sample = data.get('symbols', [])[:3]
        for s in sample:
            print(f"    {s.get('symbol')}: {s.get('bars_m15')} M15 bars, {s.get('bars_h1')} H1 bars")
    except Exception as e:
        print(f"Error reading {p}: {e}")

# Check orb_nunez_2y results if any
orb_summary = analysis_dir / "orb_nunez_2y/summary.json"
if orb_summary.exists():
    try:
        data = json.loads(orb_summary.read_text(encoding="utf-8"))
        print(f"\nORB Summary: {orb_summary.relative_to(ROOT)}")
        print(json.dumps(data, indent=2)[:500])
    except Exception as e:
        print(f"Error reading ORB summary: {e}")
