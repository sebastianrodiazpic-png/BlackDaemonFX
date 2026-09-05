"""Descubrimiento y clasificacion del catalogo de instrumentos del broker.

Recorre los simbolos que ofrece MT5, los clasifica por familia (volatility,
boom, crash, step, jump, flip) o los identifica como pares de divisas, y filtra
los que realmente se pueden operar.

La distincion entre "existe" y "es operable" es central: un simbolo puede
aparecer en el catalogo pero estar invisible o con el trading deshabilitado.
Los metodos `get_tradeable_*` activan el simbolo y verifican `trade_mode`, y
son los unicos que deben alimentar el bucle en vivo.

Vinculaciones:
    - `config.instruments.InstrumentManager`: unico consumidor.
    - `config.symbol_policy` usa la misma nocion de categoria para decidir la
      direccion permitida.
"""

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
    """Explora el catalogo MT5 y separa lo operable de lo que no lo es.

    No cachea: cada consulta refleja el estado actual del terminal.
    """

    def __init__(self, connector):
        """Guarda el conector; exige que ya este conectado al consultar."""
        self.connector = connector

    def _ensure_connection(self):
        """Verifica la conexion.

        A diferencia de `MT5DataProvider`, aqui NO se reconecta: se lanza
        `ConnectionError`. El descubrimiento ocurre en el arranque, donde una
        desconexion debe ser un fallo visible y no algo que se enmascare.
        """
        if not self.connector.is_connected():

            raise ConnectionError(
                "MetaTrader 5 no está conectado."
            )

    def get_all_symbols(self):
        """Todos los nombres del catalogo del broker, ordenados.

        Sin filtrar: incluye instrumentos invisibles o deshabilitados.
        """
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
        """Clasifica un simbolo en su familia sintetica.

        El caso especial va primero: si el nombre contiene "boom" Y "crash" se
        trata de un indice FLIP, que combina ambos comportamientos y por tanto
        no hereda la restriccion direccional de ninguno.

        Returns:
            "volatility", "boom", "crash", "step", "jump", "flip" u "other".
        """
        symbol_lower = symbol.lower()

        if "boom" in symbol_lower and "crash" in symbol_lower:

            return "flip"

        for category, keywords in DERIV_CATEGORIES.items():

            for keyword in keywords:

                if keyword in symbol_lower:

                    return category

        return "other"

    def get_deriv_synthetics(self):
        """Agrupa TODO el catalogo por categoria.

        Returns:
            dict categoria -> lista de simbolos, incluida la clave "other" con
            lo no reconocido. Sin filtrar por operabilidad.
        """
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
        """Lista plana de sinteticos reconocidos, excluyendo "other".

        Deduplica y ordena. Sigue sin filtrar por operabilidad.
        """
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
        """Metadatos de contratacion del simbolo.

        Returns:
            dict con nombre, visibilidad, `trade_mode`, limites de volumen
            (`volume_min`, `volume_max`, `volume_step`), `point` y `digits`; o
            `None` si el simbolo no existe. Los limites de volumen son los que
            condicionan si el riesgo objetivo puede respetarse.
        """
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
        """Sinteticos realmente operables ahora mismo.

        Para cada candidato: si no es visible intenta activarlo, y descarta los
        que tengan `trade_mode == SYMBOL_TRADE_MODE_DISABLED`. Los fallos se
        saltan en silencio con `continue`, porque un instrumento no disponible
        es una situacion normal y no debe abortar el arranque.

        Este es el metodo que debe alimentar el bucle en vivo.
        """
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
        """Todos los pares FX del catalogo, deduplicados y ordenados.

        Cualquier excepcion al examinar un simbolo concreto se ignora para que
        un instrumento problematico no impida detectar el resto.
        """
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
        """Imprime el catalogo agrupado por categoria con su total.

        Utilidad de diagnostico para comprobar que se detecta lo esperado.

        Returns:
            El mismo diccionario que `get_deriv_synthetics()`.
        """
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