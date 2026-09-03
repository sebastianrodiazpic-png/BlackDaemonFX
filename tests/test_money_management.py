import pandas as pd


# ============================================================
# IMPORTS SMC
# ============================================================

from strategy.smc.swings import (
    detect_swings
)

from strategy.smc.choch_bos import (
    detect_choch_bos
)

from strategy.smc.order_blocks import (
    detect_order_blocks
)

from strategy.smc.premium_discount import (
    calculate_premium_discount
)

from strategy.smc.setup_detector import (
    detect_setups
)

from strategy.smc.entry_confirmation import (
    detect_entry_confirmations
)

from strategy.smc.risk_reward import (
    calculate_risk_reward
)

from strategy.smc.trade_simulator import (
    simulate_trades
)


# ============================================================
# IMPORTS BACKTEST
# ============================================================

from strategy.backtest.backtest_metric import (
    calculate_backtest_metrics
)


# ============================================================
# IMPORTS MONEY MANAGEMENT
# ============================================================

from strategy.risk.money_management import (
    apply_money_management,
    calculate_money_management_statistics,
    calculate_risk_amount,
    update_balance,
    run_money_management
)


# ============================================================
# CONFIGURACIÓN
# ============================================================

FILE_PATH = (
    "data/historical/"
    "Volatility_90_Index_M5_2026_08.csv"
)

INITIAL_BALANCE = 10000.0

RISK_PERCENT = 1.0


# ============================================================
# FUNCIÓN AUXILIAR
# ============================================================

def get_final_balance(
    trades,
    initial_balance
):
    """
    Obtiene el balance final de manera segura.

    Si existe la columna balance_after,
    utiliza el último balance registrado.

    Si no existe, devuelve el balance inicial.
    """

    if trades is None:
        return float(initial_balance)

    if not isinstance(
        trades,
        pd.DataFrame
    ):
        return float(initial_balance)

    if trades.empty:
        return float(initial_balance)

    if "balance_after" not in trades.columns:
        return float(initial_balance)

    final_value = trades[
        "balance_after"
    ].iloc[-1]

    if pd.isna(final_value):
        return float(initial_balance)

    return float(final_value)


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def main():

    print("=" * 65)
    print("PRUEBA DE MONEY MANAGEMENT SMC")
    print("=" * 65)

    # ========================================================
    # 1. CARGAR DATOS
    # ========================================================

    print("\nCargando datos históricos...")

    df = pd.read_csv(
        FILE_PATH
    )

    df["time"] = pd.to_datetime(
        df["time"]
    )

    print(
        f"Velas cargadas: {len(df)}"
    )

    # ========================================================
    # 2. DETECTAR SWING HIGH / SWING LOW
    # ========================================================

    print(
        "\nProcesando Swing High / Swing Low..."
    )

    df = detect_swings(
        df,
        left=3,
        right=3
    )

    print(
        "Swing High / Swing Low procesados."
    )

    # ========================================================
    # 3. DETECTAR CHOCH / BOS
    # ========================================================

    print(
        "\nProcesando CHOCH / BOS..."
    )

    df = detect_choch_bos(
        df
    )

    print(
        "CHOCH / BOS procesados."
    )

    # ========================================================
    # 4. DETECTAR ORDER BLOCKS
    # ========================================================

    print(
        "\nProcesando Order Blocks..."
    )

    order_blocks = detect_order_blocks(
        df
    )

    print(
        f"Order Blocks detectados: "
        f"{len(order_blocks)}"
    )

    # ========================================================
    # 5. CALCULAR PREMIUM / DISCOUNT
    # ========================================================

    print(
        "\nCalculando Premium / Discount..."
    )

    df = calculate_premium_discount(
        df,
        lookback=100
    )

    print(
        "Premium / Discount calculado."
    )

    # ========================================================
    # 6. UNIR INFORMACIÓN DE ZONAS
    # ========================================================

    print(
        "\nUniendo información de zonas..."
    )

    zone_columns = [
        "time",
        "range_high",
        "range_low",
        "equilibrium",
        "price_position",
        "zone"
    ]

    zone_data = df[
        zone_columns
    ].copy()

    order_blocks = order_blocks.merge(
        zone_data,
        on="time",
        how="left"
    )

    print(
        "Información de zonas unida correctamente."
    )

    # ========================================================
    # 7. DETECTAR SETUPS
    # ========================================================

    print(
        "\nDetectando setups SMC..."
    )

    setups = detect_setups(
        df,
        order_blocks,
        structure_lookback=100
    )

    print(
        f"Setups detectados: "
        f"{len(setups)}"
    )

    # ========================================================
    # 8. BUSCAR CONFIRMACIONES
    # ========================================================

    print(
        "\nBuscando confirmaciones de entrada..."
    )

    confirmations = detect_entry_confirmations(
        df,
        setups
    )

    print(
        f"Confirmaciones detectadas: "
        f"{len(confirmations)}"
    )

    # ========================================================
    # 9. CALCULAR RISK / REWARD
    # ========================================================

    print(
        "\nCalculando Risk / Reward..."
    )

    trades = calculate_risk_reward(
        confirmations,
        risk_reward_ratio=2.0
    )

    print(
        f"Operaciones con R:R calculado: "
        f"{len(trades)}"
    )

    # ========================================================
    # 10. SIMULAR OPERACIONES
    # ========================================================

    print(
        "\nSimulando operaciones..."
    )

    simulated_trades = simulate_trades(
        df,
        trades
    )

    print(
        f"Operaciones simuladas: "
        f"{len(simulated_trades)}"
    )

    # ========================================================
    # 11. CALCULAR MÉTRICAS DEL BACKTEST
    # ========================================================

    print(
        "\nCalculando métricas del backtest..."
    )

    analyzed_trades, metrics = (
        calculate_backtest_metrics(
            simulated_trades
        )
    )

    print(
        f"Operaciones analizadas: "
        f"{len(analyzed_trades)}"
    )

    # ========================================================
    # 12. RESULTADOS DEL BACKTEST
    # ========================================================

    print("\n" + "=" * 65)
    print("RESULTADOS DEL BACKTEST")
    print("=" * 65)

    print(
        f"\nOperaciones totales: "
        f"{metrics.get('total_trades', 0)}"
    )

    print(
        f"Operaciones cerradas: "
        f"{metrics.get('closed_trades', 0)}"
    )

    print(
        f"Operaciones ganadoras: "
        f"{metrics.get('winning_trades', 0)}"
    )

    print(
        f"Operaciones perdedoras: "
        f"{metrics.get('losing_trades', 0)}"
    )

    print(
        f"Operaciones sin resolver: "
        f"{metrics.get('unresolved_trades', 0)}"
    )

    print(
        f"\nWin Rate: "
        f"{metrics.get('win_rate', 0.0):.2f}%"
    )

    print(
        f"Loss Rate: "
        f"{metrics.get('loss_rate', 0.0):.2f}%"
    )

    print(
        f"\nPnL total: "
        f"{metrics.get('total_pnl', 0.0):.3f}"
    )

    print(
        f"Profit Factor: "
        f"{metrics.get('profit_factor', 0.0)}"
    )

    print(
        f"Expectancy: "
        f"{metrics.get('expectancy', 0.0):.3f}"
    )

    # ========================================================
    # 13. PRUEBA DE CÁLCULO INDIVIDUAL
    # ========================================================

    print(
        "\nProbando cálculo individual..."
    )

    if not analyzed_trades.empty:

        first_trade = analyzed_trades.iloc[0]

        example_balance = float(
            INITIAL_BALANCE
        )

        example_risk_amount = (
            calculate_risk_amount(
                balance=example_balance,
                risk_percent=RISK_PERCENT
            )
        )

        example_pnl = first_trade.get(
            "pnl",
            0.0
        )

        if pd.isna(example_pnl):
            example_pnl = 0.0

        example_pnl = float(
            example_pnl
        )

        example_balance_after = (
            update_balance(
                balance=example_balance,
                pnl=example_pnl
            )
        )

        print("\nEJEMPLO PRIMERA OPERACIÓN")

        print(
            f"Balance inicial: "
            f"{example_balance:.3f}"
        )

        print(
            f"Riesgo objetivo: "
            f"{RISK_PERCENT:.2f}%"
        )

        print(
            f"Monto arriesgado: "
            f"{example_risk_amount:.3f}"
        )

        print(
            f"PnL de la operación: "
            f"{example_pnl:.3f}"
        )

        print(
            f"Balance después: "
            f"{example_balance_after:.3f}"
        )

    # ========================================================
    # 14. APLICAR MONEY MANAGEMENT
    # ========================================================

    print(
        "\nAplicando Money Management..."
    )

    managed_trades = apply_money_management(
        trades=analyzed_trades,
        initial_balance=INITIAL_BALANCE,
        risk_percent=RISK_PERCENT
    )

    print(
        f"Operaciones procesadas: "
        f"{len(managed_trades)}"
    )

    # ========================================================
    # 15. VERIFICAR COLUMNAS GENERADAS
    # ========================================================

    print(
        "\nVerificando columnas generadas..."
    )

    required_management_columns = [
        "balance_before",
        "balance_after",
        "risk_percent",
        "risk_amount"
    ]

    missing_columns = [
        column
        for column in required_management_columns
        if column not in managed_trades.columns
    ]

    if missing_columns:

        raise ValueError(
            "Faltan columnas de Money Management: "
            f"{missing_columns}"
        )

    print(
        "Columnas verificadas correctamente."
    )

    # ========================================================
    # 16. CALCULAR ESTADÍSTICAS
    # ========================================================

    print(
        "\nCalculando estadísticas de Money Management..."
    )

    management_statistics = (
        calculate_money_management_statistics(
            trades=managed_trades,
            initial_balance=INITIAL_BALANCE
        )
    )

    # ========================================================
    # 17. MOSTRAR ESTADÍSTICAS MONEY MANAGEMENT
    # ========================================================

    print("\n" + "=" * 65)
    print("ESTADÍSTICAS DE MONEY MANAGEMENT")
    print("=" * 65)

    print(
        f"\nBalance inicial: "
        f"{management_statistics['initial_balance']:.3f}"
    )

    print(
        f"Balance final: "
        f"{management_statistics['final_balance']:.3f}"
    )

    print(
        f"Ganancia neta: "
        f"{management_statistics['net_profit']:.3f}"
    )

    print(
        f"Retorno total: "
        f"{management_statistics['return_percent']:.3f}%"
    )

    print(
        f"\nBalance máximo: "
        f"{management_statistics['max_balance']:.3f}"
    )

    print(
        f"Balance mínimo: "
        f"{management_statistics['min_balance']:.3f}"
    )

    print(
        f"\nMáximo Drawdown: "
        f"{management_statistics['max_drawdown_amount']:.3f}"
    )

    print(
        f"Máximo Drawdown %: "
        f"{management_statistics['max_drawdown_percent']:.3f}%"
    )

    # ========================================================
    # 18. OBTENER BALANCE FINAL DE FORMA SEGURA
    # ========================================================

    final_balance = get_final_balance(
        trades=managed_trades,
        initial_balance=INITIAL_BALANCE
    )

    print(
        f"\nBalance final verificado: "
        f"{final_balance:.3f}"
    )

    # ========================================================
    # 19. PRUEBA DE run_money_management
    # ========================================================

    print(
        "\nProbando run_money_management..."
    )

    run_managed_trades, run_statistics = (
        run_money_management(
            trades=analyzed_trades,
            initial_balance=INITIAL_BALANCE,
            risk_percent=RISK_PERCENT
        )
    )

    print(
        f"Operaciones procesadas por "
        f"run_money_management: "
        f"{len(run_managed_trades)}"
    )

    print(
        f"Balance final de run_money_management: "
        f"{run_statistics['final_balance']:.3f}"
    )

    # ========================================================
    # 20. MOSTRAR ÚLTIMAS OPERACIONES
    # ========================================================

    print("\n" + "=" * 65)
    print("ÚLTIMAS 10 OPERACIONES CON MONEY MANAGEMENT")
    print("=" * 65)

    columns_to_show = [
        "entry_time",
        "exit_time",
        "entry_price",
        "result",
        "pnl",
        "balance_before",
        "risk_percent",
        "risk_amount",
        "balance_after"
    ]

    available_columns = [
        column
        for column in columns_to_show
        if column in managed_trades.columns
    ]

    if not managed_trades.empty:

        print(
            managed_trades[
                available_columns
            ]
            .tail(10)
            .to_string(index=False)
        )

    # ========================================================
    # 21. VALIDACIONES FINALES
    # ========================================================

    print("\n" + "-" * 65)
    print("VALIDACIONES FINALES")
    print("-" * 65)

    invalid_balance_before = 0

    invalid_balance_after = 0

    if not managed_trades.empty:

        invalid_balance_before = int(
            (
                managed_trades[
                    "balance_before"
                ].isna()
            ).sum()
        )

        invalid_balance_after = int(
            (
                managed_trades[
                    "balance_after"
                ].isna()
            ).sum()
        )

    print(
        f"\nOperaciones con "
        f"Balance Before inválido: "
        f"{invalid_balance_before}"
    )

    print(
        f"Operaciones con "
        f"Balance After inválido: "
        f"{invalid_balance_after}"
    )

    if invalid_balance_before > 0:

        raise ValueError(
            "Existen operaciones con "
            "balance_before inválido."
        )

    if invalid_balance_after > 0:

        raise ValueError(
            "Existen operaciones con "
            "balance_after inválido."
        )

    # ========================================================
    # FINALIZAR
    # ========================================================

    print("\n" + "=" * 65)
    print("PRUEBA FINALIZADA CORRECTAMENTE")
    print("=" * 65)


# ============================================================
# EJECUCIÓN
# ============================================================

if __name__ == "__main__":
    main()