from pathlib import Path

target_file = Path("strategy/ict/ict_strategy.py")
text = target_file.read_text(encoding="utf-8")

old_str = '"scenario": "AMD_KILLZONE_FVG_REJECTION",'
new_str = '''"scenario": ifvg_bpr_scenario if (is_ifvg_bpr and ifvg_bpr_scenario) else "AMD_KILLZONE_FVG_REJECTION",
            "is_ifvg_bpr": is_ifvg_bpr,
            "requires_meta_label": True if is_ifvg_bpr else False,'''

if old_str in text:
    text = text.replace(old_str, new_str, 1)
    target_file.write_text(text, encoding="utf-8")
    print("Scenario patch applied!")
else:
    print("Old string not found!")
