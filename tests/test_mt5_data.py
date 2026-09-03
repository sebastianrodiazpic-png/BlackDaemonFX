from brokers.mt5_data import MT5DataProvider


def main():

    print("=" * 60)
    print("PRUEBA DE DATOS DESDE META TRADER 5")
    print("=" * 60)

    provider = MT5DataProvider()

    try:

        print("\nConectando a MT5...")

        provider.connect()

        print("Conexión exitosa.")

        print("\nBuscando símbolos relacionados con:")
        print("Volatility")

        symbols = provider.search_symbols(
            "Volatility"
        )

        print(f"\nSímbolos encontrados: {len(symbols)}")

        for symbol in symbols:

            print(symbol)

        # Usamos el nombre que sabemos que funcionó
        # anteriormente en tu prueba.

        symbol = "Spot Up - Volatility Up Index"

        print(f"\nSímbolo seleccionado: {symbol}")

        print("\nObteniendo información del símbolo...")

        info = provider.get_symbol_info(symbol)

        print(info)

        print("\nObteniendo tick actual...")

        tick = provider.get_current_tick(symbol)

        print(tick)

        print("\nObteniendo 100 velas M5...")

        candles = provider.get_candles(
            symbol=symbol,
            timeframe="M5",
            count=100
        )

        print(f"\nVelas obtenidas: {len(candles)}")

        print("\nPrimeras 5 velas:")

        print(candles.head())

        print("\nÚltimas 5 velas:")

        print(candles.tail())

    except Exception as error:

        print(f"\nERROR: {error}")

    finally:

        provider.disconnect()

        print("\nConexión MT5 cerrada.")


if __name__ == "__main__":

    main()