"""Script de diagnostico: lista los simbolos que ofrece el terminal MT5.

ESTADO: herramienta manual, sin consumidores en el codigo. Sirve para averiguar
el nombre EXACTO de un instrumento en el broker, que suele diferir del nombre
comercial y es fuente habitual de errores de configuracion.

El descubrimiento que si usa el bot esta en `brokers.symbol_discovery`.
"""

import MetaTrader5 as mt5


def list_symbols():
    """Imprime cuenta, servidor y el nombre de todos los simbolos disponibles.

    Abre y cierra su propia sesion MT5. No devuelve nada: es puramente de
    consola.
    """
    print("=" * 70)
    print("DETECCIÓN DE SÍMBOLOS DISPONIBLES EN METATRADER 5")
    print("=" * 70)

    # Inicializar MT5
    if not mt5.initialize():
        print("\n❌ No se pudo inicializar MetaTrader 5")
        print(f"Error: {mt5.last_error()}")
        return

    print("\n✅ MetaTrader 5 conectado")

    # Obtener información de la cuenta
    account = mt5.account_info()

    if account:
        print(f"Servidor: {account.server}")
        print(f"Moneda: {account.currency}")

    # Obtener todos los símbolos
    symbols = mt5.symbols_get()

    if symbols is None:
        print("\n❌ No se pudieron obtener símbolos")
        print(f"Error: {mt5.last_error()}")
        mt5.shutdown()
        return

    print(f"\nTotal de símbolos encontrados: {len(symbols)}")

    print("\n" + "=" * 70)
    print("LISTA DE TODOS LOS SÍMBOLOS")
    print("=" * 70)

    for symbol in symbols:
        print(symbol.name)

    mt5.shutdown()


if __name__ == "__main__":
    list_symbols()