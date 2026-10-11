import sys, os
sys.path.insert(0, os.path.abspath("."))
from marketdata.deriv import DerivMarketDataProvider

provider = DerivMarketDataProvider()
provider.connect()
symbols = provider.active_symbols()
for s in sorted(symbols, key=lambda x: str(x.get("underlying_symbol", ""))):
    sym = s.get("underlying_symbol", "")
    name = s.get("underlying_symbol_name", "")
    print(f"{sym:<15} | {name}")
