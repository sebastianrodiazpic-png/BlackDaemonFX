with open('config/ict_instrument_policy.py', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add "VolSwitch High Vol Index" to ICT_5Y_RESCUED_SYNTHETICS
old_rescued = '''        "Jump 50 Index",
        "Wall Street 30",
    )'''

new_rescued = '''        "Jump 50 Index",
        "Wall Street 30",
        "VolSwitch High Vol Index",  # Rescatado por decisión del usuario (WR = 61.1 % con Criterio Humano)
    )'''

if old_rescued in text:
    text = text.replace(old_rescued, new_rescued, 1)
    print("Added VolSwitch High Vol Index to ICT_5Y_RESCUED_SYNTHETICS")
else:
    print("Warning: old_rescued not found in ict_instrument_policy.py")

# 2. Update preventive_prune_reason for REAL_SPREAD_PRUNED
old_prune_spread = 'if sym in REAL_SPREAD_PRUNED and str(profile).upper() != "MALAYSIAN_SNR":'
new_prune_spread = 'if sym in REAL_SPREAD_PRUNED and sym not in set(ICT_5Y_RESCUED_SYNTHETICS) and str(profile).upper() != "MALAYSIAN_SNR":'

if old_prune_spread in text:
    text = text.replace(old_prune_spread, new_prune_spread, 1)
    print("Updated preventive_prune_reason for REAL_SPREAD_PRUNED with rescued check")
else:
    print("Warning: old_prune_spread not found")

with open('config/ict_instrument_policy.py', 'w', encoding='utf-8') as f:
    f.write(text)

# 3. Update tests/test_ict_instrument_policy.py
with open('tests/test_ict_instrument_policy.py', 'r', encoding='utf-8') as f:
    t_text = f.read()

# Active synthetics is 33 (32 + VolSwitch)
t_text = t_text.replace('assert len(active) == 32', 'assert len(active) == 33')
# Volatility active is 16 (15 + VolSwitch)
t_text = t_text.replace('assert len(ICT_VOLATILITY_ACTIVE_SYMBOLS) == 15', 'assert len(ICT_VOLATILITY_ACTIVE_SYMBOLS) == 16')

# Update test_volswitch_high_vol_pruned_by_real_spread_in_ict_and_msnr
old_test_block = '''    for profile in ("SYNTHETICS",):
        assert sym not in ict_active_symbols(profile)
        assert "spread real" in preventive_prune_reason(sym, profile)
    assert sym not in MSNR_ACTIVE
    # Malaysian SNR (25-oct-2026): activo por acierto > 47 % por decisión del usuario (el tope spread/SL lo filtra).
    assert sym in ict_active_symbols("MALAYSIAN_SNR") and preventive_prune_reason(sym, "MALAYSIAN_SNR") == ""'''

new_test_block = '''    # Rescatado en SYNTHETICS y MALAYSIAN_SNR por decisión del usuario (WR = 61.1 % con Criterio Humano):
    for profile in ("SYNTHETICS", "MALAYSIAN_SNR"):
        assert sym in ict_active_symbols(profile), f"{sym} debe estar activo en {profile}"
        assert preventive_prune_reason(sym, profile) == "", f"{sym} no debe tener poda en {profile}"
    assert sym not in MSNR_ACTIVE'''

if old_test_block in t_text:
    t_text = t_text.replace(old_test_block, new_test_block, 1)
    print("Updated test_volswitch_high_vol_pruned_by_real_spread_in_ict_and_msnr to assert active in SYNTHETICS")
else:
    print("Warning: old_test_block not found in tests/test_ict_instrument_policy.py")

with open('tests/test_ict_instrument_policy.py', 'w', encoding='utf-8') as f:
    f.write(t_text)

print("Finished applying VolSwitch rescue patch!")
