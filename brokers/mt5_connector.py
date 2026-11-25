"""Conexion base con el terminal MetaTrader 5.

Es la capa mas baja de `brokers/`: solo abre, verifica y cierra la sesion con
el terminal ya instalado y logueado en el escritorio. No lee mercado ni envia
ordenes.

Vinculaciones:
    - `brokers.mt5_data` y `brokers.mt5_connection` lo usan como base.
    - `app.main` lo instancia al arrancar.
"""

import os
import time
import MetaTrader5 as mt5


class MT5Connector:
    """
    Gestiona la conexión entre Python y MetaTrader 5.
    """

    def __init__(self):
        """Crea el conector en estado desconectado; no toca el terminal aun."""
        self.connected = False

    def connect(self):
        """
        Inicializa la conexión con MetaTrader 5 con reintentos configurables.
        """
        if self.connected and self.is_connected():
            return True

        retries = max(1, int(os.getenv("DAEMONBLACKFX_MT5_RECONNECT_RETRIES", "3")))
        backoff = max(0.0, float(os.getenv("DAEMONBLACKFX_MT5_RECONNECT_BACKOFF_SECONDS", "1.0")))
        last_error = None

        for attempt in range(1, retries + 1):
            if not mt5.initialize():
                last_error = mt5.last_error()
                self.connected = False
                if attempt < retries and backoff > 0:
                    time.sleep(backoff * (2 ** (attempt - 1)))
                continue

            account_info = mt5.account_info()
            if account_info is None:
                last_error = mt5.last_error()
                mt5.shutdown()
                self.connected = False
                if attempt < retries and backoff > 0:
                    time.sleep(backoff * (2 ** (attempt - 1)))
                continue

            self.connected = True
            return True

        raise ConnectionError(
            f"No se pudo inicializar MetaTrader 5 tras {retries} intentos. "
            f"Error MT5: {last_error}"
        )

    def disconnect(self):
        """
        Cierra la conexión con MetaTrader 5.
        """

        if self.connected:

            mt5.shutdown()

            self.connected = False

        return True

    def is_connected(self):
        """
        Verifica si MetaTrader 5 continúa conectado.
        """

        if not self.connected:
            return False

        terminal_info = mt5.terminal_info()

        if terminal_info is None or not bool(getattr(terminal_info, "connected", False)):
            self.connected = False
            return False

        return True

    def get_account_info(self):
        """
        Obtiene la información de la cuenta actual.
        """

        if not self.is_connected():

            raise ConnectionError(
                "MetaTrader 5 no está conectado."
            )

        account_info = mt5.account_info()

        if account_info is None:

            raise RuntimeError(
                f"No se pudo obtener información "
                f"de la cuenta. Error MT5: {mt5.last_error()}"
            )

        return {
            "login": account_info.login,
            "server": account_info.server,
            "currency": account_info.currency,
            "balance": account_info.balance,
            "equity": account_info.equity,
            "margin": account_info.margin,
            "free_margin": account_info.margin_free,
            "profit": account_info.profit,
            "leverage": account_info.leverage
        }


if __name__ == "__main__":

    connector = MT5Connector()

    try:

        print("=" * 60)
        print("PRUEBA DE CONEXIÓN CON METATRADER 5")
        print("=" * 60)

        connector.connect()

        print("\nConexión exitosa.\n")

        account = connector.get_account_info()

        print("--- CUENTA ---")

        for key, value in account.items():

            print(f"{key}: {value}")

    except Exception as error:

        print(f"\nERROR: {error}")

    finally:

        connector.disconnect()

        print("\nConexión cerrada.")