# -*- coding: utf-8 -*-
import json
import re

with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    text = f.read()

m = re.search(r'const WINNERS_DATA = (\[.*?\]);', text, re.DOTALL)
winners = json.loads(m.group(1))
m_losers = re.search(r'const LOSERS_DATA = (\[.*?\]);', text, re.DOTALL)
losers = json.loads(m_losers.group(1))

msnr_w = {w['symbol']: w for w in winners if w['strategy'] == 'Malaysian SNR'}
msnr_l = {l['symbol']: l for l in losers if l['strategy'] == 'Malaysian SNR'}

print('MSNR Winners count:', len(msnr_w))
print('MSNR Losers count:', len(msnr_l))
print('\n--- CHECK USER MENTIONED SYMBOLS ---')
check_list = ['AUDCHF', 'GBPNZD', 'GBPAUD', 'XAUEUR', 'EURGBP', 'ETHUSD', 'Germany 40', 'AUDCAD', 'EURNZD', 'EURCHF', 'XAGUSD', 'GBPCAD', 'AUDNZD']
for sym in check_list:
    if sym in msnr_w:
        w = msnr_w[sym]
        print(f"[WINNER] {sym}: WR={w.get('win_rate')}%, PnL={w.get('pnl')}, is_profitable={w.get('is_profitable')}")
    if sym in msnr_l:
        l = msnr_l[sym]
        print(f"[LOSER]  {sym}: WR={l.get('win_rate')}%, PnL={l.get('pnl')}")
