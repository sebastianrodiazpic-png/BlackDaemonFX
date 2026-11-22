import sys
sys.path.insert(0, '.')

from app.main import (
    BOT_PROFILES,
    FULL_MULTI_BOT_PROFILES,
    _assert_full_multibot_architecture,
    _assert_synthetic_split_architecture,
    _build_multi_bot_dashboard_catalog,
)

print("Checking _assert_synthetic_split_architecture()...")
_assert_synthetic_split_architecture()
print("OK!")

print("Checking _assert_full_multibot_architecture()...")
_assert_full_multibot_architecture(FULL_MULTI_BOT_PROFILES)
print("OK!")

print("Building catalog for full multibot profiles...")
catalog = _build_multi_bot_dashboard_catalog(FULL_MULTI_BOT_PROFILES)
print(f"Catalog generated successfully with {len(catalog)} worker profiles:")
for p, meta in catalog.items():
    print(f" - {p}: magic={meta.get('magic')} mode={meta.get('mode')} label={meta.get('label')}")
print("ALL MULTI-BOT ARCHITECTURE CHECKS PASSED!")
