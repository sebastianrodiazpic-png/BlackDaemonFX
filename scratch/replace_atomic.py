import os

with open('tests/test_fixes_validation.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = 'assert "Vol over Crash 550" in MSNR_ACIERTO47_SYNTHETICS'
replacement = 'assert "Vol over Crash 550" not in MSNR_ACIERTO47_SYNTHETICS'

if target in text:
    text = text.replace(target, replacement)
    with open('tests/test_fixes_validation.py.tmp', 'w', encoding='utf-8') as f:
        f.write(text)
    os.replace('tests/test_fixes_validation.py.tmp', 'tests/test_fixes_validation.py')
    print('Successfully replaced tests/test_fixes_validation.py')
else:
    print('Target already replaced or not found')
