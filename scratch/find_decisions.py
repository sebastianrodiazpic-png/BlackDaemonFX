with open('dashboard/decisions_page.py', encoding='utf-8') as f:
    text = f.read()

idx = text.find('FOREX (5)')
if idx != -1:
    print('Found FOREX (5) in decisions_page.py at:', idx)
    print(text[idx-100:idx+1500])
else:
    print('FOREX (5) not found, searching 26082205')
    idx2 = text.find('26082205')
    print('idx2:', idx2)
