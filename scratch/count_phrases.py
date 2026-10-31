with open('dashboard/realtime_dashboard.py', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# Let's inspect where these exact phrases exist
phrases = [
    "Carry Forex G10",
    "DRIF",
    "Cuartos · Oro/Plata (XAUUSD / XAGUSD)",
    "RSI(2) diario · Índices US",
    "NIGHT",
    "MSNR",
]

for p in phrases:
    count = text.count(p)
    print(f"Phrase '{p}': {count} occurrences")
