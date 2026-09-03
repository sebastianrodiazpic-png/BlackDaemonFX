import MetaTrader5 as mt5


DERIV_CATEGORIES = {
    "volatility": [
        "volatility",
        "vol "
    ],
    "boom": [
        "boom"
    ],
    "crash": [
        "crash"
    ],
    "step": [
        "step"
    ],
    "jump": [
        "jump"
    ],
    "flip": [
        "flip"
    ]
}


FOREX_CURRENCIES = {
    "USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD",
    "SEK", "NOK", "DKK", "SGD", "HKD", "MXN", "ZAR", "TRY", "PLN", "CNH",
}


def _looks_like_forex_name(symbol):
    """Fallback para brokers con sufijos: EURUSDm, GBPUSD.a, USDJPYm, etc."""
    raw = str(symbol or "").upper()
    letters = "".join(ch for ch in raw if ch.isalpha())
    if len(letters) < 6:
        return False
    base, quote = letters[:3], letters[3:6]
    return base in FOREX_CURRENCIES and quote in FOREX_CURRENCIES and base != quote


class DerivSymbolDiscovery:

    def __init__(self, connector):
        self.connector = connector

    def _ensure_connection(self):

        if not self.connector.is_connected():

            raise ConnectionError(
                "MetaTrader 5 no está conectado."
            )

    def get_all_symbols(self):

        self._ensure_connection()

        symbols = mt5.symbols_get()

        if symbols is None:

            error = mt5.last_error()

            raise RuntimeError(
                f"No se pudieron obtener símbolos. "
                f"Error: {error}"
            )

        return sorted(
            [
                symbol.name
                for symbol in symbols
            ]
        )

    def classify_symbol(self, symbol):

        symbol_lower = symbol.lower()

        if "boom" in symbol_lower and "crash" in symbol_lower:

            return "flip"

        for category, keywords in DERIV_CATEGORIES.items():

            for keyword in keywords:

                if keyword in symbol_lower:

                    return category

        return "other"

    def get_deriv_synthetics(self):

        symbols = self.get_all_symbols()

        result = {
            "volatility": [],
            "boom": [],
            "crash": [],
            "step": [],
            "jump": [],
            "flip": [],
            "other": []
        }

        for symbol in symbols:

            category = self.classify_symbol(symbol)

            if category in result:

                result[category].append(symbol)

        return result

    def get_all_synthetic_symbols(self):

        categorized = self.get_deriv_synthetics()

        symbols = []

        for category in [
            "volatility",
            "boom",
            "crash",
            "step",
            "jump",
            "flip"
        ]:

            symbols.extend(
                categorized.get(category, [])
            )

        return sorted(
            list(set(symbols))
        )

    def get_symbol_info(self, symbol):

        self._ensure_connection()

        info = mt5.symbol_info(symbol)

        if info is None:

            return None

        return {
            "name": info.name,
            "visible": bool(info.visible),
            "trade_mode": int(info.trade_mode),
            "volume_min": float(info.volume_min),
            "volume_max": float(info.volume_max),
            "volume_step": float(info.volume_step),
            "point": float(info.point),
            "digits": int(info.digits)
        }

    def get_tradeable_synthetics(self):

        symbols = self.get_all_synthetic_symbols()

        tradeable = []

        for symbol in symbols:

            info = mt5.symbol_info(symbol)

            if info is None:
                continue

            if not info.visible:

                selected = mt5.symbol_select(
                    symbol,
                    True
                )

                if not selected:
                    continue

                info = mt5.symbol_info(symbol)

                if info is None:
                    continue

            if info.trade_mode == mt5.SYMBOL_TRADE_MODE_DISABLED:
                continue

            tradeable.append(symbol)

        return sorted(tradeable)

    def is_forex_symbol(self, symbol):
        """Identifica FX usando metadata MT5 y, si falta, el nombre del símbolo."""
        self._ensure_connection()
        info = mt5.symbol_info(symbol)
        if info is not None:
            base = str(getattr(info, "currency_base", "") or "").upper()
            quote = str(getattr(info, "currency_profit", "") or "").upper()
            if base in FOREX_CURRENCIES and quote in FOREX_CURRENCIES and base != quote:
                return True
        return _looks_like_forex_name(symbol)

    def get_all_forex_symbols(self):
        self._ensure_connection()
        forex = []
        for symbol in self.get_all_symbols():
            try:
                if self.is_forex_symbol(symbol):
                    forex.append(symbol)
            except Exception:
                continue
        return sorted(set(forex))

    def get_tradeable_forex(self):
        """Devuelve únicamente pares FX habilitados/seleccionables en el MT5 actual."""
        self._ensure_connection()
        tradeable = []
        for symbol in self.get_all_forex_symbols():
            info = mt5.symbol_info(symbol)
            if info is None:
                continue
            if not bool(getattr(info, "visible", False)):
                if not mt5.symbol_select(symbol, True):
                    continue
                info = mt5.symbol_info(symbol)
                if info is None:
                    continue
            if int(getattr(info, "trade_mode", mt5.SYMBOL_TRADE_MODE_DISABLED)) == mt5.SYMBOL_TRADE_MODE_DISABLED:
                continue
            tradeable.append(symbol)
        return sorted(set(tradeable))

    def print_report(self):

        categorized = self.get_deriv_synthetics()

        print("\n" + "=" * 70)
        print("INSTRUMENTOS DERIV DETECTADOS")
        print("=" * 70)

        total = 0

        for category, symbols in categorized.items():

            if not symbols:
                continue

            print(
                f"\n{category.upper()} "
                f"({len(symbols)})"
            )

            for symbol in symbols:

                print(f"  - {symbol}")

                total += 1

        print("\n" + "-" * 70)
        print(f"TOTAL DETECTADO: {total}")
        print("=" * 70)

        return categorized