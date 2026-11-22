with open('dashboard/realtime_dashboard.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, l in enumerate(lines):
    if any(k in l for k in ['"MALAYSIAN_SNR":', '"FOREX_SNR":', '"COMMODITIES_SNR":', '"TREND_PULLBACK":']):
        for j in range(i, min(i+15, len(lines))):
            print(f"{j+1}: {lines[j].strip()}")
