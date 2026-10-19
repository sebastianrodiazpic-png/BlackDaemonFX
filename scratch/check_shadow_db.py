import sqlite3
import pandas as pd

con = sqlite3.connect('file:storage/runtime/shadow_research.sqlite3?mode=ro', uri=True)
df = pd.read_sql_query("SELECT * FROM shadow_signals", con)
con.close()

print(f"Total rows: {len(df)}")
print("\nBreakdown by strategy and final_action:")
print(df.groupby(['strategy', 'final_action']).size())

print("\nBreakdown by strategy and rejection_reason:")
print(df.groupby(['strategy', 'rejection_reason']).size())

print("\nBreakdown by mechanical_decision:")
print(df.groupby(['strategy', 'mechanical_decision']).size())

print("\nMSNR signals details:")
msnr = df[df['strategy'] == 'MSNR']
print(msnr[['id', 'timestamp', 'symbol', 'direction', 'mechanical_decision', 'rejection_reason', 'final_action', 'market_outcome', 'market_rr', 'contrafactual_note']])

print("\nStaging DB check:")
try:
    con_st = sqlite3.connect('file:storage/runtime/shadow_research_staging.sqlite3?mode=ro', uri=True)
    df_st = pd.read_sql_query("SELECT * FROM shadow_signals", con_st)
    con_st.close()
    print(f"Total rows in staging: {len(df_st)}")
    print(df_st.groupby(['strategy', 'final_action']).size())
    print("\nMSNR in staging:")
    msnr_st = df_st[df_st['strategy'] == 'MSNR']
    print(f"Total MSNR in staging: {len(msnr_st)}")
    print(msnr_st.groupby(['mechanical_decision', 'rejection_reason']).size())
    print(msnr_st[['id', 'timestamp', 'symbol', 'direction', 'final_action', 'rejection_reason', 'market_outcome', 'market_rr']].head(10))
except Exception as e:
    print("Error in staging:", e)
