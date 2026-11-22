import pandas as pd
from pathlib import Path

ROOT = Path(".")
OUT_DIR = ROOT / "storage" / "analysis"

signal_files = [
    "real_win_asia_A.csv", "real_win_asia_B.csv", "real_win_asia_D.csv",
    "real_win_legacy_A.csv", "real_win_legacy_B.csv", "real_win_legacy_D.csv"
]

dfs = []
for fname in signal_files:
    fpath = OUT_DIR / f"msnr_variants_signals_{fname}"
    if fpath.exists():
        df = pd.read_csv(fpath)
        xau = df[df['symbol'] == 'XAUUSD'].copy()
        if len(xau) > 0:
            xau['origin'] = 'asia' if 'asia' in fname else 'legacy'
            dfs.append(xau)

all_xau = pd.concat(dfs, ignore_index=True).drop_duplicates(subset=['time'])
all_xau['dt'] = pd.to_datetime(all_xau['time'], utc=True)
all_xau['hour_utc'] = all_xau['dt'].dt.hour

print("--- XAUUSD Trades by Hour (UTC) in Asia Dataset ---")
by_hour = all_xau.groupby('hour_utc').agg(
    trades=('rr_live', 'count'),
    wins=('rr_live', lambda s: (s > 0).sum()),
    net_r=('rr_live', 'sum')
)
by_hour['wr'] = (by_hour['wins'] / by_hour['trades'] * 100).round(1)
print(by_hour)

# Check sessions:
# London (07:00 - 11:00 UTC)
# NY (12:30 - 17:00 UTC)
# Asia (00:00 - 07:00 UTC)
# Evening / Rollover (17:00 - 24:00 UTC)

def get_session(h):
    if 0 <= h < 7:
        return "1_Asia (00-07 UTC)"
    elif 7 <= h < 12:
        return "2_London (07-12 UTC)"
    elif 12 <= h < 17:
        return "3_New York (12-17 UTC)"
    else:
        return "4_Post-NY / Night (17-24 UTC)"

all_xau['session_zone'] = all_xau['hour_utc'].apply(get_session)
by_session = all_xau.groupby('session_zone').agg(
    trades=('rr_live', 'count'),
    wins=('rr_live', lambda s: (s > 0).sum()),
    net_r=('rr_live', 'sum')
)
by_session['wr'] = (by_session['wins'] / by_session['trades'] * 100).round(1)
print("\n--- XAUUSD Trades by Session Zone ---")
print(by_session)
