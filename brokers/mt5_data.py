"""Proveedor de datos de mercado desde MetaTrader 5.

Traduce la API nativa de MT5 a DataFrames de pandas listos para la estrategia,
resolviendo por el camino tres problemas practicos:

1. **Nombres inexactos**: el nombre comercial de un instrumento rara vez
   coincide con el del broker; `resolve_symbol` lo resuelve de forma tolerante.
2. **Simbolos no visibles**: MT5 exige activar un simbolo antes de leerlo;
   `ensure_symbol` lo hace y memoriza el resultado.
3. **Coste por ciclo**: con decenas de instrumentos por ciclo, repetir
   `symbols_get()` seria prohibitivo, de ahi las caches de sesion.

Todas las marcas de tiempo se devuelven en UTC, criterio unico del proyecto.

Vinculaciones:
    - `brokers.mt5_connector.MT5Connector`: sesion con el terminal.
    - `app.main` lo instancia y lo inyecta en el motor y la estrategia.
"""

import pandas as pd
import MetaTrader5 as mt5
import time

from brokers.mt5_connector import MT5Connector


class MT5DataProvider:
    """
    Proveedor de datos históricos y en tiempo real
    desde MetaTrader 5.
    """

    TIMEFRAMES = {

        "M1": mt5.TIMEFRAME_M1,
        "M2": mt5.TIMEFRAME_M2,
        "M3": mt5.TIMEFRAME_M3,
        "M4": mt5.TIMEFRAME_M4,
        "M5": mt5.TIMEFRAME_M5,
        "M6": mt5.TIMEFRAME_M6,
        "M10": mt5.TIMEFRAME_M10,
        "M12": mt5.TIMEFRAME_M12,
        "M15": mt5.TIMEFRAME_M15,
        "M20": mt5.TIMEFRAME_M20,
        "M30": mt5.TIMEFRAME_M30,

        "H1": mt5.TIMEFRAME_H1,
        "H2": mt5.TIMEFRAME_H2,
        "H3": mt5.TIMEFRAME_H3,
        "H4": mt5.TIMEFRAME_H4,
        "H6": mt5.TIMEFRAME_H6,
        "H8": mt5.TIMEFRAME_H8,
        "H12": mt5.TIMEFRAME_H12,

        "D1": mt5.TIMEFRAME_D1,
        "W1": mt5.TIMEFRAME_W1,
        "MN1": mt5.TIMEFRAME_MN1
    }

    def __init__(self, connector=None):
        """
        Inicializa el proveedor de datos.

        Si no se entrega un conector, se crea uno nuevo.
        """

        if connector is None:

            connector = MT5Connector()

        self.connector = connector

        # Cachés de sesión: evitan recorrer symbols_get() para cada símbolo y
        # cada timeframe durante un ciclo de 76 instrumentos.
        self._resolved_symbol_cache = {}
        self._ensured_symbols = set()

    # ==================================================
    # CONEXIÓN
    # ==================================================

    def connect(self):
        """Abre la sesion con el terminal delegando en el conector."""
        return self.connector.connect()

    def disconnect(self):
        """Cierra la sesion con el terminal."""
        return self.connector.disconnect()

    def _ensure_connection(self):
        """Reconecta si la sesion se cayo.

        Se invoca al principio de cada lectura, de modo que una caida temporal
        del terminal se recupere sola sin reiniciar el bot.
        """
        if not self.connector.is_connected():

            self.connector.connect()

    # ==================================================
    # TIMEFRAME
    # ==================================================

    def get_timeframe(self, timeframe):
        """Traduce un nombre como "M5" o "H1" a la constante de MT5.

        Raises:
            ValueError: si el marco no existe; el mensaje enumera los validos
                para que un error de configuracion se detecte de inmediato en
                vez de degenerar en datos incorrectos.
        """
        timeframe = str(timeframe).upper()

        if timeframe not in self.TIMEFRAMES:

            available = list(self.TIMEFRAMES.keys())

            raise ValueError(
                f"Timeframe no válido: {timeframe}. "
                f"Disponibles: {available}"
            )

        return self.TIMEFRAMES[timeframe]

    # ==================================================
    # BUSCAR SÍMBOLOS
    # ==================================================

    def search_symbols(self, text):
        """Busca simbolos cuyo nombre contenga `text` (sin distinguir mayusculas).

        Utilidad de exploracion; el flujo normal usa `resolve_symbol`.

        Returns:
            Lista ordenada de nombres coincidentes.
        """
        self._ensure_connection()

        text = str(text).lower()

        symbols = mt5.symbols_get()

        if symbols is None:

            error = mt5.last_error()

            raise RuntimeError(
                f"No se pudieron obtener los símbolos. "
                f"Error MT5: {error}"
            )

        results = []

        for symbol_info in symbols:

            symbol_name = symbol_info.name

            if text in symbol_name.lower():

                results.append(symbol_name)

        return sorted(results)

    # ==================================================
    # RESOLVER NOMBRE EXACTO DEL SÍMBOLO
    # ==================================================

    def resolve_symbol(self, symbol):
        """Traduce un nombre aproximado al nombre EXACTO del broker.

        Consulta el catalogo completo y cachea el resultado por nombre en
        minusculas, porque `symbols_get()` es caro y se pediria una vez por
        instrumento y marco temporal en cada ciclo.

        Returns:
            El nombre exacto tal como lo espera MT5.
        """
        self._ensure_connection()

        requested_symbol = str(symbol).strip()
        cache_key = requested_symbol.lower()

        cached = self._resolved_symbol_cache.get(cache_key)
        if cached:
            return cached

        symbols = mt5.symbols_get()
        if symbols is None:
            raise RuntimeError(
                f"No se pudieron obtener los símbolos. "
                f"Error MT5: {mt5.last_error()}"
            )

        # Construimos un índice una sola vez para esta resolución y guardamos el
        # resultado. En el demonio los símbolos ya vienen pre-resueltos.
        exact_names = {str(item.name): str(item.name) for item in symbols}
        lower_names = {
            str(item.name).lower(): str(item.name)
            for item in symbols
        }

        if requested_symbol in exact_names:
            exact = exact_names[requested_symbol]
            self._resolved_symbol_cache[cache_key] = exact
            return exact

        if cache_key in lower_names:
            exact = lower_names[cache_key]
            self._resolved_symbol_cache[cache_key] = exact
            return exact

        matches = [
            str(item.name)
            for item in symbols
            if cache_key in str(item.name).lower()
        ]

        if len(matches) == 1:
            exact = matches[0]
            self._resolved_symbol_cache[cache_key] = exact
            self._resolved_symbol_cache[exact.lower()] = exact
            return exact

        if len(matches) > 1:
            raise ValueError(
                f"Se encontraron varios símbolos para "
                f"'{requested_symbol}': {matches}"
            )

        raise ValueError(
            f"No se encontró el símbolo "
            f"'{requested_symbol}' en MetaTrader 5."
        )

    # ==================================================
    # ACTIVAR SÍMBOLO
    # ==================================================

    def ensure_symbol(self, symbol):
        """Resuelve el nombre y garantiza que el simbolo este activo en MT5.

        Un simbolo no visible en el Market Watch no devuelve velas ni ticks,
        asi que se selecciona con `symbol_select` y se vuelve a verificar. El
        resultado se memoriza en `_ensured_symbols` para no repetir dos
        llamadas a `symbol_info()` en cada analisis.

        Returns:
            El nombre exacto, ya activo y listo para leer.

        Raises:
            ValueError / RuntimeError: si el simbolo aparece en la lista pero
                no puede consultarse o activarse.
        """
        self._ensure_connection()

        requested = str(symbol).strip()
        exact_symbol = self._resolved_symbol_cache.get(
            requested.lower()
        ) or self.resolve_symbol(requested)

        # Si el símbolo ya fue validado y seleccionado durante esta sesión,
        # evitamos dos llamadas symbol_info() por cada análisis.
        if exact_symbol in self._ensured_symbols:
            return exact_symbol

        symbol_info = mt5.symbol_info(exact_symbol)

        if symbol_info is None:
            raise ValueError(
                f"El símbolo '{exact_symbol}' fue encontrado "
                f"en la lista, pero symbol_info() devolvió None. "
                f"Error MT5: {mt5.last_error()}"
            )

        if not symbol_info.visible:
            selected = mt5.symbol_select(
                exact_symbol,
                True
            )

            if not selected:
                raise RuntimeError(
                    f"No se pudo activar el símbolo "
                    f"'{exact_symbol}'. "
                    f"Error MT5: {mt5.last_error()}"
                )

        symbol_info = mt5.symbol_info(exact_symbol)
        if symbol_info is None:
            raise RuntimeError(
                f"El símbolo '{exact_symbol}' no pudo ser "
                f"obtenido después de activarlo. "
                f"Error MT5: {mt5.last_error()}"
            )

        self._resolved_symbol_cache[requested.lower()] = exact_symbol
        self._resolved_symbol_cache[exact_symbol.lower()] = exact_symbol
        self._ensured_symbols.add(exact_symbol)
        return exact_symbol

    def prepare_symbols(self, symbols):
        """Resuelve y activa una lista una sola vez antes del bucle del demonio."""
        return [self.ensure_symbol(symbol) for symbol in symbols]

    # ==================================================
    # INFORMACIÓN DEL SÍMBOLO
    # ==================================================

    def get_symbol_info(self, symbol):
        """Datos basicos del instrumento ya activado.

        Returns:
            dict con `name`, `visible`, `select`, `point`, `digits` y
            `trade_mode`. `point` y `digits` son los que usa el motor para
            redondear precios y calcular distancias de stop.
        """
        self._ensure_connection()

        exact_symbol = self.ensure_symbol(symbol)

        symbol_info = mt5.symbol_info(exact_symbol)

        if symbol_info is None:

            raise RuntimeError(
                f"No se pudo obtener información de "
                f"'{exact_symbol}'. "
                f"Error MT5: {mt5.last_error()}"
            )

        return {
            "name": symbol_info.name,
            "visible": symbol_info.visible,
            "select": symbol_info.select,
            "point": symbol_info.point,
            "digits": symbol_info.digits,
            "trade_mode": symbol_info.trade_mode
        }

    # ==================================================
    # OBTENER VELAS
    # ==================================================

    def get_candles(
        self,
        symbol,
        timeframe="M5",
        count=1000
    ):
        """Devuelve las ultimas `count` velas como DataFrame ordenado por tiempo.

        Reintenta hasta tres veces con esperas crecientes (0 / 0.15 / 0.40 s)
        ante fallos transitorios del terminal. El comentario del codigo lo
        subraya y conviene repetirlo: **solo se reintentan LECTURAS**. Reintentar
        el envio de una orden romperia su idempotencia y podria abrir posiciones
        duplicadas.

        La columna `time` se convierte a datetime UTC.

        Raises:
            RuntimeError: si tras los tres intentos no hay velas.
        """
        self._ensure_connection()

        exact_symbol = self.ensure_symbol(symbol)

        mt5_timeframe = self.get_timeframe(timeframe)

        rates = None
        last_error = None
        # v93: reintentos sólo de lectura ante fallos transitorios del terminal.
        # Nunca se reintentan aquí órdenes, preservando su idempotencia.
        for delay in (0.0, 0.15, 0.40):
            if delay:
                time.sleep(delay)
            rates = mt5.copy_rates_from_pos(
                exact_symbol,
                mt5_timeframe,
                0,
                count
            )
            if rates is not None and len(rates) > 0:
                break
            last_error = mt5.last_error()

        if rates is None:

            raise RuntimeError(
                f"No se pudieron obtener velas para "
                f"'{exact_symbol}'. "
                f"Error MT5 tras 3 intentos: {last_error}"
            )

        if len(rates) == 0:

            raise RuntimeError(
                f"No se encontraron velas para "
                f"'{exact_symbol}'."
            )

        df = pd.DataFrame(rates)

        df["time"] = pd.to_datetime(
            df["time"],
            unit="s",
            utc=True
        )

        df = (
            df
            .sort_values("time")
            .reset_index(drop=True)
        )

        return df

    # ==================================================
    # ÚLTIMA VELA CERRADA
    # ==================================================

    def get_last_closed_candle(
        self,
        symbol,
        timeframe="M5"
    ):
        """Ultima vela CERRADA, es decir la penultima del DataFrame.

        Distincion critica de toda la estrategia: la ultima vela que devuelve
        MT5 esta en formacion y sus maximos, minimos y cierre cambian tick a
        tick. Confirmar sobre ella produciria senales que se desvanecen. Por eso
        se devuelve `iloc[-2]`.

        Raises:
            RuntimeError: si no hay al menos dos velas.
        """
        candles = self.get_candles(
            symbol=symbol,
            timeframe=timeframe,
            count=3
        )

        if len(candles) < 2:

            raise RuntimeError(
                "No hay suficientes velas para "
                "obtener la última vela cerrada."
            )

        return candles.iloc[-2].copy()

    # ==================================================
    # TICK ACTUAL
    # ==================================================

    def get_current_tick(self, symbol):
        """Precio en vivo del instrumento.

        Returns:
            dict con `symbol`, `time` (UTC), `bid`, `ask` y `last`. La
            diferencia bid/ask es el spread que el motor evalua antes de
            ejecutar.
        """
        self._ensure_connection()

        exact_symbol = self.ensure_symbol(symbol)

        tick = mt5.symbol_info_tick(exact_symbol)

        if tick is None:

            raise RuntimeError(
                f"No se pudo obtener el tick de "
                f"'{exact_symbol}'. "
                f"Error MT5: {mt5.last_error()}"
            )

        return {
            "symbol": exact_symbol,

            "time": pd.to_datetime(
                tick.time,
                unit="s",
                utc=True
            ),

            "bid": float(tick.bid),

            "ask": float(tick.ask),

            "last": float(tick.last),

            "volume": float(tick.volume)
        }


if __name__ == "__main__":

    provider = MT5DataProvider()

    try:

        print("=" * 60)
        print("PRUEBA DIRECTA DE MT5DataProvider")
        print("=" * 60)

        provider.connect()

        symbols = provider.search_symbols(
            "Volatility"
        )

        print("\nSímbolos encontrados:")

        for symbol in symbols:

            print(symbol)

    except Exception as error:

        print(f"\nERROR: {error}")

    finally:

        provider.disconnect()

        print("\nConexión cerrada.")
