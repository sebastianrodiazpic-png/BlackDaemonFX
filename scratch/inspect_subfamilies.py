import pandas as pd
import numpy as np

df = pd.read_csv('scratch/msnr_complete_23_faithful_trades_clean.csv')

synths = [
    'Boom 1000 Index', 'Boom 300 Index', 'Crash 1000 Index', 'Crash 600 Index',
    'Jump 10 Index', 'Jump 25 Index', 'Step Index', 'Step Index 200',
    'Step Index 400', 'Volatility 250 (1s) Index', 'Volatility 50 (1s) Index',
    'Volatility 90 Index'
]
forex = ['AUDNZD', 'EURCHF', 'EURGBP', 'EURUSD', 'GBPAUD', 'GBPJPY', 'GBPUSD', 'USDJPY']
metals_indices = ['XAUUSD', 'XAGUSD', 'Wall Street 30']

def get_subfamily(sym):
    if sym in synths:
        return 'SINTETICOS'
    elif sym in forex:
        return 'FOREX'
    elif sym in metals_indices:
        return 'METALES_INDICES'
    return 'OTHER'

df['subfamily'] = df['symbol'].apply(get_subfamily)

print("=== DISTRIBUCIÓN POR SUBFAMILIA EN 957 TRADES BASE ===")
for sub, g in df.groupby('subfamily'):
    print(f"\n--- Subfamilia: {sub} ({len(g)} trades) ---")
    print(f"ADX:     mean={g['adx'].mean():.1f}, median={g['adx'].median():.1f}, %>=30={len(g[g['adx']>=30])/len(g)*100:.1f}%, %>=25={len(g[g['adx']>=25])/len(g)*100:.1f}%")
    print(f"RiskATR: mean={g['risk_atr'].mean():.2f}, median={g['risk_atr'].median():.2f}, %<=1.5={len(g[g['risk_atr']<=1.5])/len(g)*100:.1f}%, %<=2.0={len(g[g['risk_atr']<=2.0])/len(g)*100:.1f}%")
    print(f"Body:    mean={g['body_ratio'].mean():.2f}, median={g['body_ratio'].median():.2f}")
    print(f"PnL Raw: {g['rr'].sum():+.2f} R, WR={len(g[g['rr']>0])/len(g)*100:.1f}%")

    # Pass rate of V4 filter (ADX >= 30, ATR <= 1.5)
    v4_pass = g[(g['adx'] >= 30) & (g['risk_atr'] <= 1.5)]
    print(f"V4 Filter Pass (ADX>=30, ATR<=1.5): {len(v4_pass)} trades ({len(v4_pass)/len(g)*100:.1f}%) | PnL={v4_pass['rr'].sum():+.2f} R | WR={len(v4_pass[v4_pass['rr']>0])/len(v4_pass)*100:.1f}%" if len(v4_pass)>0 else "V4 Filter Pass: 0 trades")
