from brokers.mt5_connection import MT5Connector
from brokers.mt5_data import MT5DataProvider


def main():

    print("=" * 60)
    print("PRUEBA DE DATOS DESDE META TRADER 5")
    print("=" * 60)

    connector = MT5Connector()

    print("\nConectando a MT5...")

    if not connector.connect():

        print("❌ No se pudo conectar a MetaTrader 5.")
        return

    print("Conexión exitosa.")

    try:

        # ==============================================
        # CREAR PROVEEDOR DE DATOS
        # ==============================================

        data_provider = MT5DataProvider(
            connector=connector
        )

        # ==============================================
        # BUSCAR SÍMBOLOS
        # ==============================================

        print("\nBuscando símbolos relacionados con:")
        print("Volatility")

        symbols = data_provider.search_symbols(
            "Volatility"
        )

        print(f"\nSímbolos encontrados: {len(symbols)}")

        for symbol in symbols:

            print(symbol)

        # ==============================================
        # SÍMBOLO PROBADO Y FUNCIONAL
        # ==============================================

        symbol = "Spot Up - Volatility Up Index"

        print("\n" + "=" * 60)
        print("SÍMBOLO SELECCIONADO")
        print("=" * 60)

        print(f"Símbolo: {symbol}")

        # ==============================================
        # ACTIVAR SÍMBOLO
        # ==============================================

        print("\nActivando símbolo...")

        data_provider.ensure_symbol(
            symbol
        )

        print("✅ Símbolo activado correctamente.")

        # ==============================================
        # INFORMACIÓN DEL SÍMBOLO
        # ==============================================

        print("\n" + "=" * 60)
        print("INFORMACIÓN DEL SÍMBOLO")
        print("=" * 60)

        import MetaTrader5 as mt5

        symbol_info = mt5.symbol_info(
            symbol
        )

        if symbol_info is not None:

            print(f"Nombre: {symbol_info.name}")
            print(f"Visible: {symbol_info.visible}")
            print(f"Select: {symbol_info.select}")
            print(f"Point: {symbol_info.point}")
            print(f"Digits: {symbol_info.digits}")
            print(f"Trade mode: {symbol_info.trade_mode}")

        # ==============================================
        # OBTENER TICK ACTUAL
        # ==============================================

        print("\n" + "=" * 60)
        print("TICK ACTUAL")
        print("=" * 60)

        tick = data_provider.get_current_tick(
            symbol
        )

        print(f"Símbolo: {tick['symbol']}")
        print(f"Hora UTC: {tick['time']}")
        print(f"Bid: {tick['bid']}")
        print(f"Ask: {tick['ask']}")
        print(f"Last: {tick['last']}")

        # ==============================================
        # OBTENER VELAS M5
        # ==============================================

        print("\n" + "=" * 60)
        print("DESCARGANDO VELAS M5")
        print("=" * 60)

        candles = data_provider.get_candles(
            symbol=symbol,
            timeframe="M5",
            count=100
        )

        print(f"\nVelas obtenidas: {len(candles)}")

        print("\nPrimeras 5 velas:")

        print(
            candles.head()
        )

        print("\nÚltimas 5 velas:")

        print(
            candles.tail()
        )

        # ==============================================
        # ÚLTIMA VELA CERRADA
        # ==============================================

        print("\n" + "=" * 60)
        print("ÚLTIMA VELA CERRADA")
        print("=" * 60)

        last_closed = data_provider.get_last_closed_candle(
            symbol=symbol,
            timeframe="M5"
        )

        print(last_closed)

        print("\n" + "=" * 60)
        print("PRUEBA FINALIZADA CORRECTAMENTE")
        print("=" * 60)

    except Exception as error:

        print("\n❌ ERROR:")
        print(error)

    finally:

        connector.disconnect()

        print("\nConexión MT5 cerrada.")


if __name__ == "__main__":

    main()