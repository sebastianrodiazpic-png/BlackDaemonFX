import pandas as pd

from strategy.execution.trade_pipeline import run_trade_pipeline


FILE_PATH = "data/historical/Volatility_90_Index_M5_2026_08.csv"


def main():
    print("=" * 70)
    print("PRUEBA DEL PIPELINE SMC COMPLETO")
    print("=" * 70)

    df = pd.read_csv(FILE_PATH)
    result = run_trade_pipeline(df)

    print("\nRESUMEN")
    for key, value in result["summary"].items():
        print(f"{key}: {value}")

    setups = result["setups"]
    confirmations = result["confirmations"]

    print("\nÚLTIMOS SETUPS")
    if setups.empty:
        print("No se detectaron setups completos.")
    else:
        columns = ["setup_time", "setup_type", "zone", "trend", "sweep_time", "structure_break_type"]
        print(setups[columns].tail(10).to_string(index=False))

    print("\nÚLTIMAS ENTRADAS CONFIRMADAS")
    if confirmations.empty:
        print("No se detectaron entradas confirmadas.")
    else:
        columns = ["entry_time", "direction", "entry_price", "stop_loss", "take_profit", "risk_reward_ratio"]
        print(confirmations[columns].tail(10).to_string(index=False))


if __name__ == "__main__":
    main()
