from dashboard.strategy_bases_page import WINNERS_DATA, LOSERS_DATA

msnr_winners = [w for w in WINNERS_DATA if w['strategy'] == 'Malaysian SNR']
print(f"Total MSNR winners in strategy bases: {len(msnr_winners)}")
for w in msnr_winners:
    print(f"{w['symbol']} | {w['segment']} | WR: {w['wr_strategy']}% | HC: {w['wr_hc']}%")

print("\n--- LOSERS ---")
msnr_losers = [l for l in LOSERS_DATA if l['strategy'] == 'Malaysian SNR']
print(f"Total MSNR losers in strategy bases: {len(msnr_losers)}")
for l in msnr_losers:
    print(f"{l['symbol']} | WR: {l['wr']}% | {l['reason']}")
