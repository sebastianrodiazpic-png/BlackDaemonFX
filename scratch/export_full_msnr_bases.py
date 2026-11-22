import json, re

with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    text = f.read()

m = re.search(r'const\s+WINNERS_DATA\s*=\s*(\[.*?\]);', text, re.DOTALL)
winners = json.loads(m.group(1))
msnr = [w for w in winners if w.get('strategy') == 'Malaysian SNR']

print(f"Total MSNR records en /Strategy-bases: {len(msnr)}")
tot_trades = sum(r['trades'] for r in msnr)
tot_tp1 = sum(r['tp1'] for r in msnr)
tot_sl = sum(r['sl'] for r in msnr)
tot_pnl = sum(r['pnl'] for r in msnr)
weighted_wr = (tot_tp1 / tot_trades * 100) if tot_trades else 0

print(f"Trades Totales: {tot_trades}")
print(f"TP1 Ganadas: {tot_tp1}")
print(f"SL Perdidas: {tot_sl}")
print(f"Win Rate Ponderado: {weighted_wr:.2f}%")
print(f"PnL Neto Total: ${tot_pnl:,.2f} USD (+{tot_pnl/100:.2f} R)")

print("\n--- TOP SINTÉTICOS EN /STRATEGY-BASES (PESTAÑA MALAYSIAN SNR) ---")
for r in sorted([x for x in msnr if 'Sintéticos' in x['category']], key=lambda x: x['pnl'], reverse=True)[:15]:
    print(f"Rank #{r['rank']:2} | {r['symbol']:25} | Trades: {r['trades']:4} | WR: {r['win_rate']:5.2f}% | TP1: {r['tp1']:3} | SL: {r['sl']:2} | PnL: ${r['pnl']:,.2f}")
