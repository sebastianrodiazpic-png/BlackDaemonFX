from brokers.mt5_connector import MT5Connector
from brokers.mt5_data import MT5DataProvider
from brokers.symbol_discovery import DerivSymbolDiscovery
from database.repository import TradingRepository
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


def print_analysis_diagnostics(result):
    diagnostics = result.get("diagnostics") or {}
    if not diagnostics:
        return

    print("  diagnostics:")
    print("    failed_stage:", diagnostics.get("failed_stage"))
    print("    sequence_status:", diagnostics.get("sequence_status"))

    for tf in ("h1", "m15", "m5"):
        item = diagnostics.get(tf)
        if item:
            print(
                f"    {tf.upper()}: candles={item.get('candles')} "
                f"setups={item.get('setups')} "
                f"confirmations={item.get('confirmations')} "
                f"last={item.get('last_candle_time')}"
            )


def print_position_diagnostics(result):
    info = result.get("position_diagnostics") or {}
    if not info:
        return

    print("  position_diagnostics:")
    print("    source:", info.get("source"))
    print("    total_open:", info.get("total_open"))
    print("    symbol_open:", info.get("symbol_open"))
    print("    max_total:", info.get("max_total"))
    print("    max_per_symbol:", info.get("max_per_symbol"))
    print("    limits_enforced:", info.get("limits_enforced"))

    open_trades = info.get("open_trades") or []
    if open_trades:
        print("    open_trades:")
        for trade in open_trades:
            print(
                "      "
                f"id={trade.get('trade_id')} | "
                f"symbol={trade.get('instrument')} | "
                f"direction={trade.get('direction')} | "
                f"status={trade.get('status')} | "
                f"position_ticket={trade.get('broker_position_ticket')}"
            )


def main():
    connector = MT5Connector()
    provider = MT5DataProvider(connector)

    try:
        provider.connect()
        repo = TradingRepository()

        # Los primeros 10 instrumentos sintéticos encontrados por Deriv.
        symbols = DerivSymbolDiscovery(connector).get_tradeable_synthetics()[:10]

        # PRUEBA SEGURA:
        # - execution_enabled=False: no abre órdenes.
        # - enforce_position_limits_in_dry_run=False: analiza señales aunque SQLite
        #   tenga operaciones OPEN antiguas.
        engine = LiveTradingEngine(
            provider,
            repo,
            LiveTradingConfig(
                execution_enabled=False,
                diagnostic_mode=True,
                enforce_position_limits_in_dry_run=False,
                max_total_open_positions=3,
                max_open_positions_per_symbol=1,
            ),
        )

        print("=" * 80)
        print("PRUEBA LIVE DEMO SMC H1 -> M15 -> M5")
        print("MODO: DRY_RUN VALIDADO - SIN APERTURA DE ÓRDENES")
        print("VALIDA: SL/TP del símbolo + volumen + riesgo + MT5 order_check")
        print("=" * 80)

        results = engine.process_symbols(symbols)

        summary = {}
        for result in results:
            action = result.get("action", "UNKNOWN")
            summary[action] = summary.get(action, 0) + 1

            print(f"\n{result.get('symbol')} -> {action}")

            if result.get("reason"):
                print("  reason:", result["reason"])

            if result.get("error"):
                print("  error:", result["error"])

            if action in {"DRY_RUN", "DRY_RUN_VALIDATED"}:
                print("  direction:", result.get("direction"))
                print("  entry:", result.get("entry_price"))
                print("  stop_loss:", result.get("stop_loss"))
                print("  take_profit:", result.get("take_profit"))
                print("  planned_rr:", result.get("planned_rr"))
                print("  volume:", result.get("volume"))
                print("  risk_amount:", result.get("risk_amount"))
                print("  actual_risk_amount:", result.get("actual_risk_amount"))
                print("  risk_base:", result.get("risk_base"), result.get("risk_base_value"))
                stop_validation = result.get("stop_validation") or {}
                print("  stop_validation:", stop_validation.get("reason"), "adjusted=", stop_validation.get("adjusted"))
                constraints = stop_validation.get("constraints") or {}
                print("  symbol_constraints:", {k: constraints.get(k) for k in ("digits", "point", "stops_level_points", "min_stop_distance", "volume_min", "volume_step")})
                order_check = result.get("order_check") or {}
                print("  order_check:", order_check.get("valid"), order_check.get("retcode"), order_check.get("comment"))

            print_analysis_diagnostics(result)
            print_position_diagnostics(result)

        print("\n" + "=" * 80)
        print("RESUMEN")
        print("=" * 80)
        for action, count in sorted(summary.items()):
            print(f"{action}: {count}")

    finally:
        connector.disconnect()


if __name__ == "__main__":
    main()
