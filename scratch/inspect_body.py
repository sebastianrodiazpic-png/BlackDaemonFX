with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('<body>')
if idx != -1:
    print(text[idx:idx+1000])
