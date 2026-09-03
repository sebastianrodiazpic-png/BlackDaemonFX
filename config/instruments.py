from brokers.symbol_discovery import (
    DerivSymbolDiscovery,
)


DEFAULT_CATEGORIES = [
    "volatility",
    "boom",
    "crash",
    "step",
    "jump",
    "flip",
    "forex",
]


class InstrumentManager:

    def __init__(self, connector):
        self.discovery = DerivSymbolDiscovery(
            connector
        )

    def get_all_instruments(self):
        """
        Devuelve el universo tradeable soportado por DaemonBlackFx:
        sintéticos + Forex. ORB se incorpora aparte en app/main.py.
        """
        synthetics = self.discovery.get_tradeable_synthetics()
        forex = self.discovery.get_tradeable_forex()
        return sorted(set(synthetics).union(forex))

    def get_instruments_by_category(
        self,
        category,
    ):
        category = str(category).lower()

        categorized = (
            self.discovery.get_deriv_synthetics()
        )

        return categorized.get(
            category,
            [],
        )

    def get_active_symbols(
        self,
        categories=None,
    ):
        """
        Devuelve símbolos sintéticos tradeables filtrados por categoría.

        A diferencia de get_deriv_synthetics(), este método no devuelve
        instrumentos deshabilitados ni símbolos que MT5 no pudo activar.
        """
        if categories is None:
            categories = DEFAULT_CATEGORIES

        categories = {
            str(category).strip().lower()
            for category in categories
            if str(category).strip()
        }

        if not categories:
            return []

        synthetic_symbols = self.discovery.get_tradeable_synthetics()
        forex_symbols = self.discovery.get_tradeable_forex()

        active_symbols = []

        for symbol in synthetic_symbols:
            category = self.discovery.classify_symbol(symbol)
            if category in categories:
                active_symbols.append(symbol)

        if "forex" in categories:
            active_symbols.extend(forex_symbols)

        return sorted(
            list(set(active_symbols))
        )
