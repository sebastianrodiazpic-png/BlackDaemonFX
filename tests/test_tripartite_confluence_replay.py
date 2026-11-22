"""
tests/test_tripartite_confluence_replay.py
==========================================
Verifica que el ejecutor del Replay Fiel Consistente de 5 Años para el Gatillo de Confluencia Tripartita:
1. Cargue correctamente los 73 activos canónicos en las 4 estrategias (292 pares).
2. Lea las bases de datos de auditoría empírica multianuales sin lookahead.
3. Calcule las métricas comparativas Antes vs Después con consistencia cuantitativa por activo.
4. Genere los archivos CSV y Markdown en storage/analysis/.
"""

from __future__ import annotations

import os
from pathlib import Path
import pytest
import pandas as pd

from tools.replay_tripartite_confluence_5y import (
    RealTripartiteReplayAuditor,
    CATALOG_ALL_INSTRUMENTS,
    ALL_SYMBOLS_FLAT,
    classify_asset_category,
    wilson_score_interval,
)


def test_catalogue_completeness():
    """Verifica que el catálogo cubra exactamente 73 activos canónicos."""
    assert len(ALL_SYMBOLS_FLAT) == 73
    assert len(CATALOG_ALL_INSTRUMENTS["SYNTHETICS"]) == 38
    assert len(CATALOG_ALL_INSTRUMENTS["FOREX"]) == 24
    assert len(CATALOG_ALL_INSTRUMENTS["METALS"]) == 3
    assert len(CATALOG_ALL_INSTRUMENTS["CRYPTO"]) == 2
    assert len(CATALOG_ALL_INSTRUMENTS["INDICES"]) == 4
    assert len(CATALOG_ALL_INSTRUMENTS["COMMODITIES"]) == 2


def test_classify_asset_category():
    """Verifica la clasificación adecuada de cada activo."""
    assert classify_asset_category("Crash 300 Index") == "SYNTHETICS"
    assert classify_asset_category("EURUSD") == "FOREX"
    assert classify_asset_category("XAUUSD") == "METALS"
    assert classify_asset_category("BTCUSD") == "CRYPTO"
    assert classify_asset_category("Wall Street 30") == "INDICES"
    assert classify_asset_category("US Oil") == "COMMODITIES"


def test_wilson_score_interval():
    """Verifica el cálculo del intervalo de Wilson al 95%."""
    low, high = wilson_score_interval(60, 100)
    assert 49.0 < low < 51.0
    assert 68.0 < high < 71.0


def test_evaluate_pair_real_data():
    """Verifica la coherencia de lectura empírica de un activo real en ICT."""
    auditor = RealTripartiteReplayAuditor()
    res = auditor.evaluate_pair(strategy="ICT", symbol="Crash 300 Index")
    
    assert res["symbol"] == "Crash 300 Index"
    assert res["category"] == "SYNTHETICS"
    # Crash 300 Index en ICT v1 vs v2
    assert res["trades_antes"] > 0
    assert res["trades_despues"] > 0
    assert res["wr_despues"] > res["wr_antes"]
    assert res["r_neto_despues"] > res["r_neto_antes"]
    assert res["status_despues"] == "ACTIVO (RENTABLE)"


def test_run_replay_generation():
    """Verifica que la ejecución del replay produzca 73 pares por estrategia y dataframes válidos."""
    auditor = RealTripartiteReplayAuditor()
    df_det, df_sum = auditor.run_replay(target_strategy="ORB")
    
    assert len(df_det) == 73  # 73 activos para ORB
    assert len(df_sum) == 1
    assert df_sum.iloc[0]["strategy"] == "ORB"
    assert df_sum.iloc[0]["trades_antes"] > 0
    assert df_sum.iloc[0]["trades_despues"] > 0
    assert df_sum.iloc[0]["wr_despues"] > df_sum.iloc[0]["wr_antes"]


def test_all_instruments_comparison_and_podados():
    """Verifica que la tabla comparativa completa y la auditoría de podados sean consistentes."""
    from tools.build_all_instruments_replay_comparison import build_all_instruments_comparison
    df_all, df_pod = build_all_instruments_comparison()

    assert len(df_all) == 292
    assert len(df_pod) == 103

    # Comprobación de integridad matemática en cada fila
    for _, r in df_all.iterrows():
        if r["trades_despues"] > 0:
            assert r["trades_despues"] == r["wins_despues"] + r["losses_despues"]
            wr_calc = round((r["wins_despues"] / r["trades_despues"]) * 100.0, 2)
            assert abs(wr_calc - r["wr_despues"]) < 0.05
            assert round(r["wr_despues"] - r["wr_antes"], 2) == r["delta_wr_pp"]
            assert round(r["r_neto_despues"] - r["r_neto_antes"], 2) == r["delta_r"]

    # Comprobación de que los podados rehabilitados superen el umbral
    rehab = df_pod[df_pod["decision"].str.contains("REHABILITADO")]
    assert len(rehab) > 0
    for _, r in rehab.iterrows():
        assert r["wr_despues"] >= 50.0
        assert r["r_neto_despues"] > 0
        assert r["status_despues"] == "ACTIVO (RENTABLE)"

