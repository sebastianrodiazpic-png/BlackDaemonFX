import json, re

with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Find const WINNERS_DATA = [ ... ];
m = re.search(r'const\s+WINNERS_DATA\s*=\s*(\[.*?\]);', text, re.DOTALL)
if m:
    data_str = m.group(1)
    winners = json.loads(data_str)
    print(f"Total winners records: {len(winners)}")
    
    # Filter by strategy
    from collections import Counter
    strats = Counter(r.get('strategy') for r in winners)
    print("Strategies in WINNERS_DATA:", strats)
    
    msnr_winners = [r for r in winners if 'malaysian' in r.get('strategy', '').lower()]
    print(f"MSNR records in WINNERS_DATA: {len(msnr_winners)}")
    
    # Calculate totals for MSNR in WINNERS_DATA
    tot_trades = sum(r.get('trades', 0) for r in msnr_winners)
    tot_tp1 = sum(r.get('tp1', 0) for r in msnr_winners)
    tot_sl = sum(r.get('sl', 0) for r in msnr_winners)
    tot_pnl = sum(r.get('pnl', 0) for r in msnr_winners)
    weighted_wr = (tot_tp1 / tot_trades * 100) if tot_trades else 0
    print(f"\nMSNR EN WINNERS_DATA (/strategy-bases):")
    print(f"Total trades: {tot_trades}")
    print(f"TP1 (Wins): {tot_tp1}")
    print(f"SL (Losses): {tot_sl}")
    print(f"Weighted Win Rate: {weighted_wr:.2f}%")
    print(f"Total PnL ($): ${tot_pnl:,.2f}")
    
    print("\nTop 10 MSNR in WINNERS_DATA:")
    for r in sorted(msnr_winners, key=lambda x: x.get('pnl', 0), reverse=True)[:10]:
        print(f"  {r.get('symbol'):25} | Trades: {r.get('trades'):4} | WR: {r.get('win_rate'):5.2f}% | TP1: {r.get('tp1'):4} | SL: {r.get('sl'):3} | PnL: ${r.get('pnl'):,.2f}")
else:
    print("WINNERS_DATA not matched!")
