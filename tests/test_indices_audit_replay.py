# -*- coding: utf-8 -*-
"""
Tests unitarios para la auditoría de 5 años del worker INDICES.
"""

from pathlib import Path
import pandas as pd
from tools.replay_indices_5y_audit import run_indices_audit, OUTPUT_REPORT_CSV


def test_indices_5y_audit_replay_execution():
    run_indices_audit()
    assert OUTPUT_REPORT_CSV.exists(), "El archivo indices_5y_audit_report.csv debe existir"
    
    df = pd.read_csv(OUTPUT_REPORT_CSV)
    assert len(df) == 4, "Debe auditar exactamente los 4 índices bursátiles"
    
    symbols = set(df["symbol"])
    assert symbols == {"Wall Street 30", "US Tech 100", "US SP 500", "Germany 40"}
    
    # Validar que todos los activos incrementan su volumen manteniendo WR > 50%
    assert (df["trades_opt"] > df["trades_base"]).all(), "El volumen debe incrementarse en todos los índices"
    assert (df["wr_opt"] >= 50.0).all(), "Todos los índices deben mantener WR >= 50%"
    assert (df["r_opt"] > df["r_base"]).all(), "El retorno neto R debe incrementarse en todos los índices"
    
    # Validar diferencial neto positivo
    total_delta_r = df["delta_r"].sum()
    assert total_delta_r >= 70.0, f"El retorno neto adicional debe ser >= +70R (obtenido: +{total_delta_r}R)"
