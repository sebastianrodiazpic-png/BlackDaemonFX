import json
with open('scratch/winners_clean.json', 'r', encoding='utf-8') as f:
    winners = json.load(f)

msnr_winners = [w for w in winners if w['strategy'] == 'Malaysian SNR']
print(f"Count MSNR in winners_clean.json: {len(msnr_winners)}")
for w in msnr_winners:
    print(f"Rank {w['rank']}: {w['symbol']} | WR: {w['win_rate']}% | PnL: {w['pnl']} R")
