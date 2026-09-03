import pandas as pd

from strategy.smc.swings import detect_swings
from strategy.smc.choch_bos import detect_choch_bos
from strategy.smc.order_blocks import detect_order_blocks

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

from strategy.backtest.backtest_metric import (
    calculate_backtest_metrics
)


# ==================================================
# CONFIGURACIÓN
# ==================================================

FILE_PATH = (
    "data/historical/"
    "Volatility_90_Index_M5_2026_08.csv"
)


def main():

    print("=" * 65)
    print("PRUEBA DE MÉTRICAS DEL BACKTEST SMC")
    print("=" * 65)

    # ==================================================
    # 1. CARGAR DATOS
    # ==================================================

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

    # ==================================================
    # 2. DETECTAR SWINGS
    # ==================================================

    print("\nProcesando Swing High / Swing Low...")

    df = detect_swings(
        df,
        left=3,
        right=3
    )

    print(
        "Swing High / Swing Low procesados."
    )

    # ==================================================
    # 3. DETECTAR CHOCH / BOS
    # ==================================================

    print("\nProcesando CHOCH / BOS...")

    df = detect_choch_bos(df)

    print(
        "CHOCH / BOS procesados."
    )

    # ==================================================
    # 4. DETECTAR ORDER BLOCKS
    # ==================================================

    print("\nProcesando Order Blocks...")

    order_blocks = detect_order_blocks(
        df
    )

    print(
        f"Order Blocks detectados: "
        f"{len(order_blocks)}"
    )

    # ==================================================
    # 5. PREMIUM / DISCOUNT
    # ==================================================

    print("\nCalculando Premium / Discount...")

    df = calculate_premium_discount(
        df,
        lookback=100
    )

    print(
        "Premium / Discount calculado."
    )

    # ==================================================
    # 6. UNIR ZONAS
    # ==================================================

    print("\nUniendo información de zonas...")

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

    # ==================================================
    # 7. DETECTAR SETUPS
    # ==================================================

    print("\nDetectando setups SMC...")

    setups = detect_setups(
        df,
        order_blocks,
        structure_lookback=100
    )

    print(
        f"Setups detectados: "
        f"{len(setups)}"
    )

    # ==================================================
    # 8. CONFIRMAR ENTRADAS
    # ==================================================

    print("\nBuscando confirmaciones de entrada...")

    confirmations = detect_entry_confirmations(
        df,
        setups
    )

    print(
        f"Confirmaciones detectadas: "
        f"{len(confirmations)}"
    )

    # ==================================================
    # 9. CALCULAR RISK / REWARD
    # ==================================================

    print("\nCalculando Risk / Reward...")

    trades = calculate_risk_reward(
        confirmations,
        risk_reward_ratio=2.0
    )

    print(
        f"Operaciones con R:R calculado: "
        f"{len(trades)}"
    )

    # ==================================================
    # 10. SIMULAR OPERACIONES
    # ==================================================

    print("\nSimulando operaciones...")

    simulated_trades = simulate_trades(
        df,
        trades
    )

    print(
        f"Operaciones simuladas: "
        f"{len(simulated_trades)}"
    )

    # ==================================================
    # 11. CALCULAR MÉTRICAS
    # ==================================================

    print("\nCalculando métricas del backtest...")

    analyzed_trades, metrics = (
        calculate_backtest_metrics(
            simulated_trades
        )
    )

    # ==================================================
    # RESULTADOS GENERALES
    # ==================================================

    print("\n" + "=" * 65)
    print("RESULTADOS GENERALES")
    print("=" * 65)

    print(
        f"\nOperaciones totales: "
        f"{metrics['total_trades']}"
    )

    print(
        f"Operaciones cerradas: "
        f"{metrics['closed_trades']}"
    )

    print(
        f"Operaciones ganadoras: "
        f"{metrics['winning_trades']}"
    )

    print(
        f"Operaciones perdedoras: "
        f"{metrics['losing_trades']}"
    )

    print(
        f"Operaciones sin resolver: "
        f"{metrics['unresolved_trades']}"
    )

    # ==================================================
    # PORCENTAJES
    # ==================================================

    print("\n" + "-" * 65)
    print("PORCENTAJES")
    print("-" * 65)

    print(
        f"\nWin Rate: "
        f"{metrics['win_rate']}%"
    )

    print(
        f"Loss Rate: "
        f"{metrics['loss_rate']}%"
    )

    # ==================================================
    # RENTABILIDAD
    # ==================================================

    print("\n" + "-" * 65)
    print("RENTABILIDAD")
    print("-" * 65)

    print(
        f"\nPnL total: "
        f"{metrics['total_pnl']:.3f}"
    )

    print(
        f"PnL promedio por operación: "
        f"{metrics['average_pnl']:.3f}"
    )

    print(
        f"Ganancia promedio: "
        f"{metrics['average_win']:.3f}"
    )

    print(
        f"Pérdida promedio: "
        f"{metrics['average_loss']:.3f}"
    )

    print(
        f"Ganancia bruta: "
        f"{metrics['gross_profit']:.3f}"
    )

    print(
        f"Pérdida bruta: "
        f"{metrics['gross_loss']:.3f}"
    )

    print(
        f"Profit Factor: "
        f"{metrics['profit_factor']}"
    )

    print(
        f"Expectancy: "
        f"{metrics['expectancy']:.3f}"
    )

    # ==================================================
    # DRAWDOWN
    # ==================================================

    print("\n" + "-" * 65)
    print("RIESGO Y DRAWDOWN")
    print("-" * 65)

    print(
        f"\nMáximo Drawdown: "
        f"{metrics['max_drawdown']:.3f}"
    )

    print(
        f"Máximo Drawdown %: "
        f"{metrics['max_drawdown_percent']:.3f}%"
    )

    print(
        f"Máxima racha ganadora: "
        f"{metrics['max_consecutive_wins']}"
    )

    print(
        f"Máxima racha perdedora: "
        f"{metrics['max_consecutive_losses']}"
    )

    # ==================================================
    # LONG / SHORT
    # ==================================================

    print("\n" + "-" * 65)
    print("RESULTADOS LONG / SHORT")
    print("-" * 65)

    print(
        f"\nOperaciones LONG: "
        f"{metrics['long_trades']}"
    )

    print(
        f"PnL LONG: "
        f"{metrics['long_pnl']:.3f}"
    )

    print(
        f"\nOperaciones SHORT: "
        f"{metrics['short_trades']}"
    )

    print(
        f"PnL SHORT: "
        f"{metrics['short_pnl']:.3f}"
    )

    # ==================================================
    # ÚLTIMAS OPERACIONES
    # ==================================================

    print("\n" + "=" * 65)
    print("ÚLTIMAS 10 OPERACIONES ANALIZADAS")
    print("=" * 65)

    columns_to_show = [
        "entry_time",
        "exit_time",
        "entry_price",
        "result",
        "pnl",
        "equity",
        "drawdown"
    ]

    available_columns = [
        column
        for column in columns_to_show
        if column in analyzed_trades.columns
    ]

    if not analyzed_trades.empty:

        print(
            analyzed_trades[
                available_columns
            ]
            .tail(10)
            .to_string(index=False)
        )

    # ==================================================
    # FINALIZAR
    # ==================================================

    print("\n" + "=" * 65)
    print("PRUEBA FINALIZADA CORRECTAMENTE")
    print("=" * 65)


if __name__ == "__main__":
    main()