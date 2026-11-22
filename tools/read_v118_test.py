import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('tests/test_v118_multistrategy_sentinel_matrix.py', 'r', encoding='utf-8') as f:
    text = f.read()

print(text[:2500])
