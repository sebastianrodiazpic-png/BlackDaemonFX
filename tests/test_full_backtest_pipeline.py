from backtesting.backtest_pipeline import run_full_backtest_pipeline


def main():
    result = run_full_backtest_pipeline(
        historical_file="data/historical/Volatility_90_Index_M5_2026_08.csv",
        entries_file="storage/analysis/Volatility_90_Index_M5_confirmations.csv",
        instrument="Volatility 90 Index",
        timeframe="M5",
        initial_balance=1000.0,
        risk_percent=1.0,
        compound=True,
        strategy_version="smc-v1-backtest-aug-2026",
    )

    print("=" * 65)
    print("PIPELINE COMPLETO FINALIZADO")
    print("=" * 65)
    print(f"Velas: {result['candles']}")
    print(f"Entradas: {result['entries']}")
    print(f"Trades: {result['trades']}")
    print(f"Backtest: {result['backtest_file']}")
    print(f"Money management: {result['money_management_file']}")
    print(f"SQLite nuevas: {result['persistence']['import']['created']}")
    print(f"SQLite existentes: {result['persistence']['import']['existing']}")
    print(f"Excel: {result['persistence']['report']}")


if __name__ == "__main__":
    main()
