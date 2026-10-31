import sqlite3
import os
import pandas as pd

dbs = [
    r'C:/Users/sebas/AppData/Local/BlackDaemonFx/trading_bot.sqlite3',
    'storage/trading_bot.sqlite3',
    'database/trading_bot.sqlite3'
]

for db in dbs:
    if not os.path.exists(db):
        print(f"File not found: {db}")
        continue
    print(f"\n=======================================================")
    print(f"ANALYZING: {db} (size: {os.path.getsize(db):,} bytes)")
    print(f"=======================================================")
    try:
        conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cur.fetchall()]
        print("Tables found:", tables)
        
        target_table = None
        for candidate in ['trades', 'positions', 'signals']:
            if candidate in tables:
                cur.execute(f"SELECT COUNT(*) FROM {candidate}")
                cnt = cur.fetchone()[0]
                print(f"Table '{candidate}': {cnt} rows")
                if candidate == 'trades' and cnt > 0:
                    target_table = 'trades'
        
        if target_table:
            # Check schema of trades table
            cur.execute(f"PRAGMA table_info({target_table})")
            cols = [r[1] for r in cur.fetchall()]
            print("Columns in trades:", cols)
            
            df = pd.read_sql_query(f"SELECT * FROM {target_table}", conn)
            print(f"Total rows in df: {len(df)}")
            
            # Print unique strategies
            strat_col = 'strategy_name' if 'strategy_name' in df.columns else ('strategy' if 'strategy' in df.columns else None)
            symbol_col = 'symbol' if 'symbol' in df.columns else None
            
            if strat_col and symbol_col:
                print("\n--- Trades by Strategy ---")
                print(df[strat_col].value_counts(dropna=False))
                
                # Classify symbols into categories: Synthetics vs Real/Forex/Commodities
                def classify_symbol(sym):
                    if not isinstance(sym, str):
                        return "Unknown"
                    s = sym.upper()
                    synthetics_keywords = [
                        'VOLATILITY', 'STEP', 'BOOM', 'CRASH', 'JUMP', 'DEX', 'RANGE BREAK', 
                        'HZ', '1S', 'VOL'
                    ]
                    for kw in synthetics_keywords:
                        if kw in s:
                            return "Sintéticos (Deriv)"
                    # Specific synthetics checks
                    if any(x in s for x in ['V10', 'V25', 'V50', 'V75', 'V100']):
                        return "Sintéticos (Deriv)"
                    if any(x in s for x in ['EUR', 'GBP', 'USD', 'JPY', 'AUD', 'CAD', 'CHF', 'NZD']):
                        if 'BTC' in s or 'ETH' in s or 'CRYPTO' in s:
                            return "Cripto"
                        if 'US30' in s or 'SPX' in s or 'NAS' in s or 'TECH' in s or 'WALL' in s:
                            return "Índices Reales"
                        if 'XAU' in s or 'XAG' in s or 'GOLD' in s or 'SILVER' in s or 'OIL' in s:
                            return "Commodities / Metales"
                        return "Forex"
                    if 'BTC' in s or 'ETH' in s:
                        return "Cripto"
                    if any(x in s for x in ['OIL', 'BRENT', 'WTI', 'XAU', 'XAG']):
                        return "Commodities / Metales"
                    if any(x in s for x in ['US100', 'US500', 'US30', 'DAX', 'GER']):
                        return "Índices Reales"
                    return "Otros / No clasificado"
                
                df['market_type'] = df[symbol_col].apply(classify_symbol)
                
                print("\n--- Trades by Market Type ---")
                print(df['market_type'].value_counts(dropna=False))
                
                print("\n--- Breakdown: Strategy vs Market Type ---")
                print(pd.crosstab(df[strat_col], df['market_type'], margins=True))
                
                print("\n--- Top 15 Symbols ---")
                print(df[symbol_col].value_counts().head(15))
                
                if 'status' in df.columns:
                    print("\n--- Status breakdown ---")
                    print(df['status'].value_counts())
                    
                if 'realized_rr' in df.columns:
                    print("\n--- Performance by Market Type (Realized RR) ---")
                    print(df.groupby('market_type')['realized_rr'].agg(['count', 'mean', 'sum']))
                    
                if 'created_at' in df.columns or 'entry_time' in df.columns:
                    time_col = 'created_at' if 'created_at' in df.columns else 'entry_time'
                    print(f"\n--- Date range ({time_col}) ---")
                    print("Min:", df[time_col].min(), "Max:", df[time_col].max())

        conn.close()
    except Exception as e:
        print(f"Error reading {db}: {e}")
