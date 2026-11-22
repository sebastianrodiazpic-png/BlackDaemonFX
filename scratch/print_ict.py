import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('scratch/apply_humanized_ict_texts.py', 'r', encoding='utf-8') as f:
    text = f.read()

print(text)
