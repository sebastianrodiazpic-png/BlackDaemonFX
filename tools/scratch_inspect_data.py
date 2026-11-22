import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8-sig') as f:
    text = f.read()

pos_w = text.find('const WINNERS_DATA = [')
pos_w_end = text.find('];', pos_w) + 2
print(f'WINNERS_DATA: from {pos_w} to {pos_w_end}')
print('Tail of WINNERS_DATA:')
print(repr(text[pos_w_end-60:pos_w_end+60]))

pos_l = text.find('const LOSERS_DATA = [')
pos_l_end = text.find('];', pos_l) + 2
print(f'LOSERS_DATA: from {pos_l} to {pos_l_end}')
print('Tail of LOSERS_DATA:')
print(repr(text[pos_l_end-60:pos_l_end+60]))

pos_m = text.find('const STRATEGY_METRICS = {')
pos_m_end = text.find('};', pos_m) + 2
print(f'STRATEGY_METRICS: from {pos_m} to {pos_m_end}')
print('Tail of STRATEGY_METRICS:')
print(repr(text[pos_m_end-60:pos_m_end+60]))
