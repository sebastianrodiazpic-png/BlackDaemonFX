from pathlib import Path

path = Path("tests/test_ict_instrument_policy.py")
text = path.read_text(encoding="utf-8")

# 1. len(active) == 35 -> 33
text = text.replace("assert len(active) == 35", "assert len(active) == 33")

# 2. Boom 500 Index in synthetics active check -> Boom 600 Index
text = text.replace('"Boom 500 Index", "Jump 25 Index"', '"Boom 600 Index", "Jump 25 Index"')

# 3. sanitize Boom 500 -> Boom 600
text = text.replace('["Crash 1000 Index", "Boom 500 Index"]) == ["Boom 500 Index"]', '["Crash 1000 Index", "Boom 600 Index"]) == ["Boom 600 Index"]')

# 4. len(MSNR_ACIERTO47_SYNTHETICS) == 21 -> 18
text = text.replace("assert len(MSNR_ACIERTO47_SYNTHETICS) == 21", "assert len(MSNR_ACIERTO47_SYNTHETICS) == 18")

# 5. MSNR prune reason
text = text.replace('assert ("acierto <= 50" in preventive_prune_reason("Boom 1000 Index"', 'assert ("acierto <= 51" in preventive_prune_reason("Boom 1000 Index"')
text = text.replace('assert ("acierto <= 50" in preventive_prune_reason("Crash 500 Index"', 'assert ("acierto <= 51" in preventive_prune_reason("Crash 500 Index"')
text = text.replace('assert ("acierto <= 50" in preventive_prune_reason("AUDNZD"', 'assert ("acierto <= 51" in preventive_prune_reason("AUDNZD"')

# 6. sanitize MSNR Boom 300 -> Boom 500
text = text.replace('["AUDNZD", "Boom 1000 Index", "Boom 300 Index"]) == ["Boom 300 Index"]', '["AUDNZD", "Boom 1000 Index", "Boom 500 Index"]) == ["Boom 500 Index"]')

# 7. apply_tool MSNR Boom 300 -> Boom 500
text = text.replace('["AUDNZD", "Boom 1000 Index", "Boom 300 Index"]', '["AUDNZD", "Boom 1000 Index", "Boom 500 Index"]')
text = text.replace('modes["Boom 300 Index"] == "live"', 'modes["Boom 500 Index"] == "live"')

# 8. dashboard MSNR save Boom 300 -> Boom 500
text = text.replace('"malaysian_snr_boom", "symbols": ["Boom 300 Index", "VolSwitch High Vol Index"]', '"malaysian_snr_boom", "symbols": ["Boom 500 Index", "VolSwitch High Vol Index"]')
text = text.replace('update_selected_symbols(["Boom 300 Index", "VolSwitch High Vol Index", "AUDNZD"]', 'update_selected_symbols(["Boom 500 Index", "VolSwitch High Vol Index", "AUDNZD"]')
text = text.replace('["Boom 300 Index", "VolSwitch High Vol Index"]', '["Boom 500 Index", "VolSwitch High Vol Index"]')
text = text.replace('saved["modes"]["Boom 300 Index"] == "live"', 'saved["modes"]["Boom 500 Index"] == "live"')

# 9. Forex len 16 -> 14, pruned 26 -> 28
text = text.replace("assert len(ICT_FOREX_ACTIVE) == 16", "assert len(ICT_FOREX_ACTIVE) == 14")
text = text.replace("assert len(ICT_FOREX_PRUNED_SYMBOLS) == 26", "assert len(ICT_FOREX_PRUNED_SYMBOLS) == 28")

path.write_text(text, encoding="utf-8")
print("Updated test_ict_instrument_policy.py successfully")

# Also check test_fixes_validation.py
fixes_path = Path("tests/test_fixes_validation.py")
fixes_text = fixes_path.read_text(encoding="utf-8")
fixes_text = fixes_text.replace('assert "Vol over Crash 550" in MSNR_ACIERTO47_SYNTHETICS', 'assert "Vol over Crash 550" not in MSNR_ACIERTO47_SYNTHETICS')
fixes_path.write_text(fixes_text, encoding="utf-8")
print("Updated test_fixes_validation.py successfully")
