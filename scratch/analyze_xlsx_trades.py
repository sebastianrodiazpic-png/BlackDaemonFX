import pandas as pd
import json

file_path = 'storage/exports/deriv_demo_trading_report.xlsx'
df = pd.read_excel(file_path, sheet_name='Trades')

print(f"Total trades: {len(df)}")
print("\n=== TOP 25 INSTRUMENTS ===")
print(df['instrument'].value_counts().head(25))

def classify(sym):
    if not isinstance(sym, str):
        return "Unknown"
    s = sym.upper()
    synthetics_kw = ['VOLATILITY', 'STEP', 'BOOM', 'CRASH', 'JUMP', 'DEX', 'RANGE BREAK', 'HZ', '1S', 'VOL']
    for kw in synthetics_kw:
        if kw in s:
            return "Sintéticos (Deriv)"
    if any(x in s for x in ['V10', 'V25', 'V50', 'V75', 'V100']):
        return "Sintéticos (Deriv)"
    if any(x in s for x in ['EUR', 'GBP', 'USD', 'JPY', 'AUD', 'CAD', 'CHF', 'NZD']):
        if any(x in s for x in ['BTC', 'ETH']):
            return "Cripto"
        if any(x in s for x in ['US30', 'SPX', 'NAS', 'TECH', 'WALL', 'GER', 'DAX']):
            return "Índices Reales"
        if any(x in s for x in ['XAU', 'XAG', 'GOLD', 'SILVER', 'OIL']):
            return "Commodities / Metales"
        return "Forex"
    if any(x in s for x in ['BTC', 'ETH']):
        return "Cripto"
    if any(x in s for x in ['OIL', 'BRENT', 'WTI', 'XAU', 'XAG']):
        return "Commodities / Metales"
    if any(x in s for x in ['US100', 'US500', 'US30', 'DAX', 'GER']):
        return "Índices Reales"
    return "Otros"

df['market_class'] = df['instrument'].apply(classify)

print("\n=== TRADES BY MARKET CLASS ===")
print(df['market_class'].value_counts())
print("\nPercentage by Market Class:")
print((df['market_class'].value_counts(normalize=True) * 100).round(2))

print("\n=== TRADES BY STRATEGY / PERFIL BOT ===")
for col in ['perfil_bot', 'estrategia_id', 'strategy_version']:
    if col in df.columns:
        print(f"\n--- {col} ---")
        print(df[col].value_counts().head(15))

print("\n=== CROSSTAB: STRATEGY (perfil_bot) vs MARKET CLASS ===")
if 'perfil_bot' in df.columns:
    print(pd.crosstab(df['perfil_bot'], df['market_class'], margins=True))

print("\n=== PERFORMANCE BY MARKET CLASS ===")
if 'realized_rr' in df.columns:
    print(df.groupby('market_class')['realized_rr'].agg(['count', 'mean', 'sum']))

if 'net_pnl' in df.columns:
    print("\nNet PnL by market class:")
    print(df.groupby('market_class')['net_pnl'].agg(['count', 'mean', 'sum']))

print("\n=== DATES RANGE ===")
print("Min entry_time:", df['entry_time'].min(), "Max entry_time:", df['entry_time'].max())

