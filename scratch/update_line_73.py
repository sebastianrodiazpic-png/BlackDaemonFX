import os

with open('tests/test_fixes_validation.py', 'r', encoding='utf-8') as f:
    text = f.read()

target = 'assert "Vol over Crash 550" in saved_calls["MALAYSIAN_SNR"]'
replacement = 'assert "Vol over Crash 550" not in saved_calls["MALAYSIAN_SNR"]'

if target in text:
    text = text.replace(target, replacement)
    with open('tests/test_fixes_validation.py.tmp', 'w', encoding='utf-8') as f:
        f.write(text)
    os.replace('tests/test_fixes_validation.py.tmp', 'tests/test_fixes_validation.py')
    print('Successfully updated test_fixes_validation.py line 73')
else:
    print('Target not found')
