from risk.money_manager import MoneyManager


def main():

    print("=" * 60)
    print("PRUEBA DE MONEY MANAGEMENT")
    print("=" * 60)

    manager = MoneyManager(
        initial_balance=1000,
        risk_percent=1
    )

    print()
    print(
        f"Capital inicial: "
        f"${manager.get_current_balance():.2f}"
    )

    print(
        f"Riesgo por operación: "
        f"{manager.risk_percent:.2f}%"
    )

    print()

    trades = [
        2.0,
        -1.0,
        2.0,
        -1.0,
        -1.0,
        2.0
    ]

    print("SIMULANDO OPERACIONES")
    print("-" * 60)

    for number, realized_r in enumerate(
        trades,
        start=1
    ):

        result = manager.process_trade(
            realized_r=realized_r
        )

        print()
        print(
            f"OPERACIÓN {number}"
        )

        print(
            f"Balance antes: "
            f"${result.initial_balance:.2f}"
        )

        print(
            f"Riesgo: "
            f"${result.risk_amount:.2f}"
        )

        print(
            f"R realizado: "
            f"{result.realized_r:.2f}R"
        )

        print(
            f"Resultado: "
            f"${result.profit_loss:.2f}"
        )

        print(
            f"Balance después: "
            f"${result.final_balance:.2f}"
        )

    print()
    print("=" * 60)
    print("RESULTADO FINAL")
    print("=" * 60)

    print(
        f"Capital final: "
        f"${manager.get_current_balance():.2f}"
    )


if __name__ == "__main__":
    main()