import MetaTrader5 as mt5


SEARCH_TEXT = "Spot Up"


def test_symbol():

    print("=" * 60)
    print("PRUEBA DETALLADA DEL SÍMBOLO MT5")
    print("=" * 60)

    # ==================================================
    # CONECTAR A MT5
    # ==================================================

    if not mt5.initialize():

        print("\n❌ No se pudo conectar a MT5")
        print(f"Error: {mt5.last_error()}")
        return

    print("\n☑ Conectado a MT5")

    try:

        # ==================================================
        # BUSCAR SÍMBOLOS
        # ==================================================

        print("\n--- BUSCANDO SÍMBOLOS ---")

        symbols = mt5.symbols_get()

        if symbols is None:

            print("\n❌ No se pudieron obtener símbolos")
            print(f"Error: {mt5.last_error()}")
            return

        matches = []

        for symbol in symbols:

            symbol_name = symbol.name

            if SEARCH_TEXT.lower() in symbol_name.lower():

                matches.append(symbol)

        print(
            f"\nSímbolos encontrados: {len(matches)}"
        )

        if not matches:

            print(
                f"\n❌ No se encontraron símbolos "
                f"relacionados con: {SEARCH_TEXT}"
            )

            return

        # ==================================================
        # MOSTRAR RESULTADOS EXACTOS
        # ==================================================

        print("\n--- NOMBRES EXACTOS DEVUELTOS POR MT5 ---")

        for index, symbol in enumerate(
            matches,
            start=1
        ):

            print(
                f"{index}. {repr(symbol.name)}"
            )

        # ==================================================
        # SELECCIONAR EL PRIMER SÍMBOLO
        # ==================================================

        selected_symbol = matches[0]

        symbol_name = selected_symbol.name

        print("\n--- SÍMBOLO SELECCIONADO ---")

        print(f"Nombre normal: {symbol_name}")
        print(f"Nombre repr: {repr(symbol_name)}")
        print(f"Longitud: {len(symbol_name)}")

        # ==================================================
        # INFORMACIÓN DIRECTA
        # ==================================================

        print("\n--- INFORMACIÓN DIRECTA DEL OBJETO ---")

        print(
            f"Visible actualmente: "
            f"{selected_symbol.visible}"
        )

        print(
            f"Select actualmente: "
            f"{selected_symbol.select}"
        )

        print(
            f"Trade mode: "
            f"{selected_symbol.trade_mode}"
        )

        # ==================================================
        # INTENTAR ACTIVAR
        # ==================================================

        print("\n--- ACTIVANDO SÍMBOLO ---")

        result = mt5.symbol_select(
            symbol_name,
            True
        )

        print(
            f"Resultado symbol_select: {result}"
        )

        print(
            f"Último error: {mt5.last_error()}"
        )

        # ==================================================
        # OBTENER INFORMACIÓN DEL SÍMBOLO
        # ==================================================

        print("\n--- INFORMACIÓN DEL SÍMBOLO ---")

        info = mt5.symbol_info(
            symbol_name
        )

        if info is None:

            print("❌ symbol_info devolvió None")

            print(
                f"Error: {mt5.last_error()}"
            )

            return

        print("✅ symbol_info obtenido correctamente")

        print(f"Nombre: {info.name}")
        print(f"Visible: {info.visible}")
        print(f"Select: {info.select}")
        print(f"Bid: {info.bid}")
        print(f"Ask: {info.ask}")
        print(f"Point: {info.point}")
        print(f"Digits: {info.digits}")

        # ==================================================
        # OBTENER TICK
        # ==================================================

        print("\n--- TICK ACTUAL ---")

        tick = mt5.symbol_info_tick(
            symbol_name
        )

        if tick is None:

            print("⚠ No hay tick disponible")

            print(
                f"Error: {mt5.last_error()}"
            )

        else:

            print("✅ Tick obtenido")

            print(f"Bid: {tick.bid}")
            print(f"Ask: {tick.ask}")
            print(f"Last: {tick.last}")
            print(f"Time: {tick.time}")

        # ==================================================
        # DESCARGAR VELAS M5
        # ==================================================

        print("\n--- DESCARGANDO VELAS M5 ---")

        rates = mt5.copy_rates_from_pos(
            symbol_name,
            mt5.TIMEFRAME_M5,
            0,
            100
        )

        if rates is None:

            print("❌ rates devolvió None")

            print(
                f"Error: {mt5.last_error()}"
            )

            return

        print(
            f"✅ Velas obtenidas: {len(rates)}"
        )

        if len(rates) > 0:

            print("\nPrimera vela:")

            print(rates[0])

            print("\nÚltima vela:")

            print(rates[-1])

    finally:

        mt5.shutdown()

        print("\nConexión MT5 cerrada.")


if __name__ == "__main__":

    test_symbol()