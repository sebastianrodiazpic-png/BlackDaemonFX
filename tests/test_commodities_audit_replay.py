from pathlib import Path
import pandas as pd
import pytest

from tools.replay_commodities_5y_audit import run_commodities_audit, OUTPUT_REPORT_CSV

def test_commodities_5y_audit_execution_and_report_integrity():
    run_commodities_audit()
    assert OUTPUT_REPORT_CSV.exists()
    df = pd.read_csv(OUTPUT_REPORT_CSV)
    assert len(df) == 5
    symbols = set(df['symbol'])
    assert "XAUUSD" in symbols
    assert "US Oil" in symbols
    assert "UK Brent Oil" in symbols
    assert "XAUEUR" in symbols
    assert "XAGUSD" in symbols

    # Validar que todos los activos tienen delta positivo en trades y retorno R
    for _, row in df.iterrows():
        assert row['trades_optimizado'] > row['trades_base']
        assert row['r_optimizado'] > row['r_base']
        assert row['wr_optimizado'] >= 57.0  # Todas las materias primas superan el 57% de acierto
