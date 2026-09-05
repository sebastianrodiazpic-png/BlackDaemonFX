"""Gestor monetario en R: traduce resultados en R a dinero sobre el capital.

Trabaja en multiplos de R en lugar de en dinero absoluto. Con un riesgo de
10 unidades, un +2R son +20 y un -1R son -10. Esa normalizacion permite
comparar operaciones de instrumentos y tamanos distintos.

ESTADO — LEGADO. Sin consumidores en produccion; solo lo cubre
`tests/test_money_manager.py`. La operativa real calcula el riesgo en
`strategy.execution.live_trading_engine`.

Vinculaciones:
- No importa nada del proyecto ni es importado por modulos de produccion.
"""

from dataclasses import dataclass


@dataclass
class TradeRiskResult:
    """
    Resultado financiero de una operación.
    """

    initial_balance: float
    risk_percent: float
    risk_amount: float
    realized_r: float
    profit_loss: float
    final_balance: float


class MoneyManager:
    """
    Gestiona el riesgo y calcula el resultado monetario
    de las operaciones.

    La lógica trabaja inicialmente con R.

    Ejemplo:

    Riesgo = $10

    WIN con +2R:
        +$20

    LOSS con -1R:
        -$10
    """

    def __init__(
        self,
        initial_balance,
        risk_percent=1.0
    ):
        """Inicializa el gestor con el capital y el riesgo por operación.

        Args:
            initial_balance: capital de partida, debe ser mayor que cero.
            risk_percent: porcentaje del capital arriesgado en cada
                operacion, debe ser mayor que cero.

        Raises:
            ValueError: si el capital o el porcentaje no son positivos. Se
                valida al construir para que un gestor mal configurado no
                llegue a calcular resultados sin sentido.
        """
        self.balance = float(initial_balance)
        self.risk_percent = float(risk_percent)

        if self.balance <= 0:
            raise ValueError(
                "El capital inicial debe ser mayor que cero."
            )

        if self.risk_percent <= 0:
            raise ValueError(
                "El porcentaje de riesgo debe ser mayor que cero."
            )

    def get_current_balance(self):
        """
        Retorna el capital actual.
        """

        return float(self.balance)

    def calculate_risk_amount(
        self,
        balance=None
    ):
        """
        Calcula cuánto dinero se arriesga
        en una operación.
        """

        if balance is None:
            balance = self.balance

        balance = float(balance)

        risk_amount = (
            balance
            * self.risk_percent
            / 100
        )

        return float(risk_amount)

    def calculate_profit_loss(
        self,
        realized_r,
        balance=None
    ):
        """
        Calcula el resultado monetario
        utilizando el R realizado.

        Ejemplo:

        Balance = 1000
        Riesgo = 1%

        Riesgo monetario = 10

        realized_r = 2
        Resultado = +20

        realized_r = -1
        Resultado = -10
        """

        realized_r = float(realized_r)

        risk_amount = self.calculate_risk_amount(
            balance=balance
        )

        profit_loss = (
            risk_amount
            * realized_r
        )

        return float(profit_loss)

    def process_trade(
        self,
        realized_r
    ):
        """
        Procesa una operación y actualiza
        el balance de la cuenta.
        """

        initial_balance = float(
            self.balance
        )

        risk_amount = (
            self.calculate_risk_amount(
                balance=initial_balance
            )
        )

        profit_loss = (
            self.calculate_profit_loss(
                realized_r=realized_r,
                balance=initial_balance
            )
        )

        final_balance = (
            initial_balance
            + profit_loss
        )

        self.balance = float(
            final_balance
        )

        return TradeRiskResult(
            initial_balance=initial_balance,
            risk_percent=self.risk_percent,
            risk_amount=risk_amount,
            realized_r=float(realized_r),
            profit_loss=float(profit_loss),
            final_balance=float(final_balance)
        )

    def reset_balance(
        self,
        balance
    ):
        """
        Reinicia el balance.
        """

        balance = float(balance)

        if balance <= 0:
            raise ValueError(
                "El balance debe ser mayor que cero."
            )

        self.balance = balance