"""Pipeline de backtesting: de las señales históricas al informe de resultados.

Orquesta la evaluacion historica completa en tres pasos encadenados:

1. `trade_simulator.simulate_all_trades` recorre las velas posteriores a cada
   senal y determina si habria tocado antes el stop o el objetivo.
2. `backtest_money_management.apply_money_management` traduce esos resultados
   en R a la evolucion monetaria de una cuenta.
3. `backtest_storage.persist_money_management_results` guarda todo en base de
   datos y exporta el informe.

ESTE ES EL MOTOR DE BACKTEST VIVO. Lo invoca `app.main` desde la interfaz.
No confundir con `strategy/backtest/`, que solo aporta un calculador de
metricas sin consumidores en produccion.

Vinculaciones:
- Consumido por `app.main`.
- Consume los tres modulos hermanos del paquete `backtesting`.
"""

from __future__ import annotations

from pathlib import Path
import pandas as pd

from backtesting.trade_simulator import simulate_all_trades, get_backtest_summary
from backtesting.backtest_money_management import (
    apply_money_management,
    get_money_management_summary,
    save_money_management_results,
)
from backtesting.backtest_storage import persist_money_management_results


def run_full_backtest_pipeline(
    historical_file: str | Path,
    entries_file: str | Path,
    instrument: str,
    timeframe: str = "M5",
    initial_balance: float = 1000.0,
    risk_percent: float = 1.0,
    compound: bool = True,
    max_bars: int | None = None,
    backtest_output: str | Path | None = None,
    money_management_output: str | Path | None = None,
    db_path: str | Path | None = None,
    report_path: str | Path = "storage/exports/trading_report.xlsx",
    strategy_version: str = "smc-v1",
):
    """Ejecuta el flujo completo histórico -> backtest -> gestión -> SQLite -> Excel."""
    historical_file = Path(historical_file)
    entries_file = Path(entries_file)
    if not historical_file.exists():
        raise FileNotFoundError(f"No existe el histórico: {historical_file}")
    if not entries_file.exists():
        raise FileNotFoundError(f"No existe el archivo de entradas: {entries_file}")

    safe_name = instrument.replace(" ", "_")
    backtest_output = Path(backtest_output or f"storage/analysis/{safe_name}_{timeframe}_backtest.csv")
    money_management_output = Path(
        money_management_output or f"storage/analysis/{safe_name}_{timeframe}_money_management.csv"
    )
    backtest_output.parent.mkdir(parents=True, exist_ok=True)
    money_management_output.parent.mkdir(parents=True, exist_ok=True)

    candles = pd.read_csv(historical_file)
    entries = pd.read_csv(entries_file)
    if "time" not in candles.columns:
        raise ValueError("El histórico debe contener la columna 'time'.")
    if "entry_time" not in entries.columns:
        raise ValueError("Las entradas deben contener la columna 'entry_time'.")

    candles["time"] = pd.to_datetime(candles["time"], utc=True)
    entries["entry_time"] = pd.to_datetime(entries["entry_time"], utc=True)
    candles = candles.sort_values("time").reset_index(drop=True)
    entries = entries.sort_values("entry_time").reset_index(drop=True)

    trades = simulate_all_trades(candles=candles, entries=entries, max_bars=max_bars)
    trades.to_csv(backtest_output, index=False)
    backtest_summary = get_backtest_summary(trades)

    managed = apply_money_management(
        trades=trades,
        initial_balance=initial_balance,
        risk_percent=risk_percent,
        compound=compound,
    )
    saved_money_file = save_money_management_results(managed, money_management_output)
    money_summary = get_money_management_summary(managed, initial_balance=initial_balance)

    persistence = persist_money_management_results(
        file_path=saved_money_file,
        instrument=instrument,
        timeframe=timeframe,
        db_path=db_path,
        report_path=report_path,
        strategy_version=strategy_version,
    )

    return {
        "candles": len(candles),
        "entries": len(entries),
        "trades": len(trades),
        "backtest_file": backtest_output,
        "money_management_file": saved_money_file,
        "backtest_summary": backtest_summary,
        "money_management_summary": money_summary,
        "persistence": persistence,
    }
