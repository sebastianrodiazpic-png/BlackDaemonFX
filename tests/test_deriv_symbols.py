import MetaTrader5 as mt5

from brokers.mt5_connector import MT5Connector


def print_symbols(title, symbols):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)

    if not symbols:
        print("No se encontraron instrumentos.")
        return

    for symbol in symbols:
        print(f"• {symbol}")

    print(f"\nTotal encontrados: {len(symbols)}")


def search_symbols(text):
    """
    Busca instrumentos disponibles en MetaTrader 5
    que contengan el texto indicado.
    """

    symbols = mt5.symbols_get()

    if symbols is None:
        print(
            f"\n❌ No se pudieron obtener los símbolos: "
            f"{mt5.last_error()}"
        )
        return []

    text = text.lower()

    results = []

    for symbol_info in symbols:

        symbol_name = symbol_info.name

        if text in symbol_name.lower():

            results.append(symbol_name)

    return sorted(results)


def main():

    print("=" * 70)
    print("BUSCADOR DE ÍNDICES SINTÉTICOS DERIV")
    print("=" * 70)

    connector = MT5Connector()

    try:

        # ==================================================
        # CONECTAR
        # ==================================================

        connector.connect()

        print("\n✅ MetaTrader 5 conectado correctamente")

        # ==================================================
        # STEP
        # ==================================================

        step_symbols = search_symbols(
            "step"
        )

        print_symbols(
            "STEP INDEX DISPONIBLES",
            step_symbols
        )

        # ==================================================
        # BOOM
        # ==================================================

        boom_symbols = search_symbols(
            "boom"
        )

        print_symbols(
            "BOOM INDEX DISPONIBLES",
            boom_symbols
        )

        # ==================================================
        # CRASH
        # ==================================================

        crash_symbols = search_symbols(
            "crash"
        )

        print_symbols(
            "CRASH INDEX DISPONIBLES",
            crash_symbols
        )

        # ==================================================
        # VOLATILITY
        # ==================================================

        volatility_symbols = search_symbols(
            "volatility"
        )

        print_symbols(
            "VOLATILITY INDEX DISPONIBLES",
            volatility_symbols
        )

        # ==================================================
        # JUMP
        # ==================================================

        jump_symbols = search_symbols(
            "jump"
        )

        print_symbols(
            "JUMP INDEX DISPONIBLES",
            jump_symbols
        )

        print("\n" + "=" * 70)
        print("RESUMEN")
        print("=" * 70)

        print(
            f"STEP:       {len(step_symbols)}"
        )

        print(
            f"BOOM:       {len(boom_symbols)}"
        )

        print(
            f"CRASH:      {len(crash_symbols)}"
        )

        print(
            f"VOLATILITY: {len(volatility_symbols)}"
        )

        print(
            f"JUMP:       {len(jump_symbols)}"
        )

    except Exception as error:

        print(
            f"\n❌ ERROR: {error}"
        )

    finally:

        connector.disconnect()

        print(
            "\n🔌 Conexión MT5 cerrada."
        )


if __name__ == "__main__":
    main()