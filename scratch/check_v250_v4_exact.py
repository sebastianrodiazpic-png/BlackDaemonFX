import pandas as pd
import numpy as np

# Load task-5452 log or rerun output
# Let's inspect trades from task-5452.log
with open('C:/Users/sebas/.gemini/antigravity-ide/brain/910b64e8-0e4d-429e-b1eb-15b16146fe6c/.system_generated/tasks/task-5452.log', 'r') as f:
    lines = f.readlines()

trade_lines = [l.strip() for l in lines[3:] if l.strip()]
data = []
for l in trade_lines:
    parts = l.split()
    idx = int(parts[0])
    dt = parts[1] + " " + parts[2]
    direction = parts[3]
    adx = float(parts[4])
    risk_atr = float(parts[5])
    rr = float(parts[6])
    outcome = parts[7]
    data.append({
        'symbol': 'Volatility 250 (1s) Index',
        'time': dt,
        'direction': direction,
        'adx': adx,
        'risk_atr': risk_atr,
        'rr': rr,
        'outcome': outcome
    })

df = pd.DataFrame(data)
df['time'] = pd.to_datetime(df['time'], utc=True)
print("Total trades con spread real 0.0035:", len(df))
print("Net R base:", df['rr'].sum())

# Filter ADX >= 30
adx_pass = df[df['adx'] >= 30.0]
print("Pass ADX >= 30:", len(adx_pass), "Net R:", adx_pass['rr'].sum())

# Filter ADX >= 30 and ATR <= 1.5
v2_pass = adx_pass[adx_pass['risk_atr'] <= 1.5]
print("Pass ADX >= 30 and ATR <= 1.5:", len(v2_pass))
if len(v2_pass) > 0:
    print(v2_pass)
