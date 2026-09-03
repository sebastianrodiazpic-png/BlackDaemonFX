import MetaTrader5 as mt5


class MT5Connector:
    """
    Gestiona la conexión entre Python y MetaTrader 5.
    """

    def __init__(self):
        self.connected = False

    def connect(self):
        """
        Inicializa la conexión con MetaTrader 5.
        """

        if self.connected:
            return True

        if not mt5.initialize():

            error = mt5.last_error()

            raise ConnectionError(
                f"No se pudo inicializar MetaTrader 5. "
                f"Error MT5: {error}"
            )

        account_info = mt5.account_info()

        if account_info is None:

            error = mt5.last_error()

            mt5.shutdown()

            raise ConnectionError(
                f"MetaTrader 5 se inició, pero no hay "
                f"una cuenta conectada. Error MT5: {error}"
            )

        self.connected = True

        return True

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

        if terminal_info is None:

            self.connected = False

            return False

        return terminal_info.connected

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