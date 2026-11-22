with open('dashboard/strategy_bases_page.py', encoding='utf-8') as f:
    text = f.read()

idx = text.find('WINNERS_DATA')
print('WINNERS_DATA found at:', idx)
print(text[idx:idx+1500])
