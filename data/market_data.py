"""Utilidad manual de descarga de historico desde MT5 a CSV.

ESTADO: script auxiliar, NO forma parte del bot en produccion. El mapa de
dependencias no le encuentra ningun consumidor; se ejecuta a mano cuando se
quiere un CSV para analisis o backtest.

En produccion los datos de mercado llegan por `brokers.mt5_data`, no por aqui.

Vinculaciones:
    - `MetaTrader5`: abre y cierra su propia conexion, independiente de la que
      usa el bot.
"""

from datetime import datetime, timezone
import os

import MetaTrader5 as mt5
import pandas as pd


PRIMARY_SYMBOL = "Volatility 90 Index"


def initialize_mt5():
    """Inicializa la conexión con MetaTrader 5."""

    if not mt5.initialize():
        print("ERROR: No se pudo inicializar MetaTrader 5")
        print(f"Detalle: {mt5.last_error()}")
        return False

    print("MetaTrader 5 inicializado correctamente")
    return True


def get_historical_data(symbol, timeframe, start_date, end_date):
    """Descarga velas históricas entre dos fechas."""

    if not mt5.symbol_select(symbol, True):
        print(f"ERROR: No se pudo seleccionar el símbolo: {symbol}")
        return None

    rates = mt5.copy_rates_range(
        symbol,
        timeframe,
        start_date,
        end_date
    )

    if rates is None:
        print(f"ERROR al descargar datos: {mt5.last_error()}")
        return None

    df = pd.DataFrame(rates)

    if df.empty:
        print("No se recibieron datos históricos")
        return None

    # Convertir timestamp a fecha legible UTC
    df["time"] = pd.to_datetime(df["time"], unit="s", utc=True)

    return df


def save_historical_data(df, symbol, timeframe_name):
    """Guarda los datos en CSV."""

    base_dir = os.path.dirname(os.path.abspath(__file__))
    historical_dir = os.path.join(base_dir, "historical")

    os.makedirs(historical_dir, exist_ok=True)

    safe_symbol = symbol.replace(" ", "_").replace("(", "").replace(")", "")

    file_name = f"{safe_symbol}_{timeframe_name}_2026_08.csv"

    file_path = os.path.join(historical_dir, file_name)

    df.to_csv(file_path, index=False)

    print(f"\nDatos guardados correctamente en:")
    print(file_path)


def main():
    """Descarga M5 de `PRIMARY_SYMBOL` y lo guarda en CSV.

    El rango va desde una fecha fija codificada arriba hasta el instante
    actual. La conexion MT5 se cierra siempre en el `finally`, incluso si la
    descarga falla.
    """
    print("=" * 60)
    print("DESCARGA DE DATOS HISTÓRICOS - DERIV MT5")
    print("=" * 60)

    if not initialize_mt5():
        return

    try:
        # Agosto 2026
        start_date = datetime(2026, 8, 1, tzinfo=timezone.utc)

        # Fecha actual UTC
        end_date = datetime.now(timezone.utc)

        print(f"\nSímbolo: {PRIMARY_SYMBOL}")
        print(f"Desde: {start_date}")
        print(f"Hasta: {end_date}")

        df = get_historical_data(
            symbol=PRIMARY_SYMBOL,
            timeframe=mt5.TIMEFRAME_M5,
            start_date=start_date,
            end_date=end_date
        )

        if df is not None:

            print(f"\nVelas descargadas: {len(df)}")

            print("\nPRIMERAS 5 VELAS:")
            print(df.head())

            print("\nÚLTIMAS 5 VELAS:")
            print(df.tail())

            save_historical_data(
                df,
                PRIMARY_SYMBOL,
                "M5"
            )

    finally:
        mt5.shutdown()
        print("\nConexión MT5 cerrada correctamente")


if __name__ == "__main__":
    main()