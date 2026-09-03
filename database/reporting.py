from __future__ import annotations

from pathlib import Path
import json
import pandas as pd

from database.repository import TradingRepository


def _numeric(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(0.0, index=frame.index)
    return pd.to_numeric(frame[column], errors="coerce").fillna(0.0)


def _write_sheet(writer, frame: pd.DataFrame, name: str):
    frame.to_excel(writer, sheet_name=name, index=False)
    ws = writer.book[name]
    ws.freeze_panes = "A2"
    if len(frame.columns):
        ws.auto_filter.ref = ws.dimensions
    for column_cells in ws.columns:
        letter = column_cells[0].column_letter
        max_len = max(len(str(cell.value or "")) for cell in column_cells[:1000])
        ws.column_dimensions[letter].width = min(max(max_len + 2, 12), 40)


def export_trading_report(db_path=None, output_path=None, source: str | None = None):
    """Exporta un reporte completo desde SQLite a Excel."""
    repo = TradingRepository(db_path)
    trades = repo.trades_dataframe(source=source)
    summary = repo.summary(source=source)
    output = Path(output_path or "storage/exports/trading_report.xlsx")
    output.parent.mkdir(parents=True, exist_ok=True)

    if trades.empty:
        trades = pd.DataFrame(columns=[
            "id", "source", "instrument", "timeframe", "direction", "status",
            "result", "planned_rr", "realized_rr", "risk_amount", "net_pnl",
        ])
        by_instrument = pd.DataFrame(columns=["instrument", "operations", "wins", "losses", "net_pnl"])
        by_direction = pd.DataFrame(columns=["direction", "operations", "wins", "losses", "net_pnl"])
        equity_curve = pd.DataFrame(columns=["entry_time", "balance_after", "equity", "peak_balance"])
        drawdown = pd.DataFrame(columns=["entry_time", "drawdown_amount", "drawdown_percent"])
        smc = pd.DataFrame(columns=["id", "instrument", "direction", "setup_reason", "details_json"])
    else:
        trades = trades.copy()
        trades["net_pnl"] = _numeric(trades, "net_pnl")
        trades["realized_rr"] = _numeric(trades, "realized_rr")
        trades["planned_rr"] = _numeric(trades, "planned_rr")

        by_instrument = (
            trades.groupby(["instrument", "timeframe"], dropna=False)
            .agg(
                operations=("id", "count"),
                wins=("result", lambda s: (s == "WIN").sum()),
                losses=("result", lambda s: (s == "LOSS").sum()),
                ambiguous=("result", lambda s: (s == "AMBIGUOUS").sum()),
                net_pnl=("net_pnl", "sum"),
                avg_realized_rr=("realized_rr", "mean"),
                avg_planned_rr=("planned_rr", "mean"),
            )
            .reset_index()
        )

        by_direction = (
            trades.groupby("direction", dropna=False)
            .agg(
                operations=("id", "count"),
                wins=("result", lambda s: (s == "WIN").sum()),
                losses=("result", lambda s: (s == "LOSS").sum()),
                net_pnl=("net_pnl", "sum"),
                avg_realized_rr=("realized_rr", "mean"),
            )
            .reset_index()
        )

        equity_columns = [c for c in ["entry_time", "balance_after", "equity", "peak_balance", "net_pnl"] if c in trades.columns]
        equity_curve = trades[equity_columns].copy()
        drawdown_columns = [c for c in ["entry_time", "drawdown_amount", "drawdown_percent"] if c in trades.columns]
        drawdown = trades[drawdown_columns].copy()
        smc_columns = [c for c in ["id", "instrument", "timeframe", "direction", "setup_reason", "details_json"] if c in trades.columns]
        smc = trades[smc_columns].copy()

        if "details_json" in smc.columns:
            smc["details_json"] = smc["details_json"].apply(_pretty_json)

    summary_df = pd.DataFrame([summary])

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        _write_sheet(writer, summary_df, "01_Resumen")
        _write_sheet(writer, trades, "02_Operaciones")
        _write_sheet(writer, by_instrument, "03_Por_Instrumento")
        _write_sheet(writer, by_direction, "04_Por_Direccion")
        _write_sheet(writer, smc, "05_Senales_SMC")
        _write_sheet(writer, equity_curve, "06_Curva_Capital")
        _write_sheet(writer, drawdown, "07_Drawdown")

    return output


def _pretty_json(value):
    if value in (None, ""):
        return ""
    try:
        return json.dumps(json.loads(value), ensure_ascii=False, indent=2, default=str)
    except Exception:
        return str(value)
