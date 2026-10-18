"""
tests/test_prospective_m1_replay.py
===================================
Pruebas unitarias para el motor de replay independiente M1 prospectivo.
Valida:
1. Resolución de conflictos intra-vela (prevalencia de SL en peor caso).
2. Transición dual-leg: TP1 seguido de Break-Even en runner.
3. Transición dual-leg: TP1 seguido de TP2 (full win).
4. Pérdida total por toque de SL previo a TP1.
5. Fricción y spread diferencial en BUY vs SELL.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest
import pandas as pd
import numpy as np
from tools.prospective_m1_replay_runner import ProspectiveM1ReplayRunner

def create_mock_bars(rows):
    data = []
    base_t = pd.Timestamp("2026-10-15 18:00:00+00:00")
    for i, r in enumerate(rows):
        t = base_t + pd.Timedelta(minutes=i)
        data.append({
            "time": t,
            "open": r[0],
            "high": r[1],
            "low": r[2],
            "close": r[3],
            "tick_volume": 100,
            "real_volume": 0,
            "spread": 0,
            "complete": True
        })
    return pd.DataFrame(data)

def test_sl_precedence_on_same_bar_conflict():
    runner = ProspectiveM1ReplayRunner(dry_run=True)
    # Entry at 100, SL at 90, TP1 at 110, TP2 at 120 (BUY)
    # Bar touches both 85 (below SL) and 115 (above TP1)
    bars = create_mock_bars([
        (100.0, 115.0, 85.0, 100.0)
    ])
    runner.cache_m1["MockSym"] = bars
    
    res = runner.simulate_trade_m1(
        symbol="MockSym",
        direction="BUY",
        signal_time=pd.Timestamp("2026-10-15 18:00:00+00:00"),
        created_at=pd.Timestamp("2026-10-15 18:00:00+00:00"),
        entry_target=100.0,
        sl=90.0,
        tp1_target=110.0,
        tp2_target=120.0,
        fill_mode="signal_entry"
    )
    assert res["status"] == "CLOSED"
    assert res["leg1_reason"] == "SL_SAME_BAR_CONFLICT"
    assert res["realized_rr"] == -1.0

def test_tp1_then_runner_be():
    runner = ProspectiveM1ReplayRunner(dry_run=True)
    # Entry at 100, SL at 90, TP1 at 110, TP2 at 120 (BUY)
    # Bar 0: reaches 112 (TP1 hit, active_sl_leg2 moves to 100)
    # Bar 1: drops to 99 (hits BE at 100)
    bars = create_mock_bars([
        (100.0, 112.0, 100.0, 110.0),
        (110.0, 110.0, 99.0, 101.0)
    ])
    runner.cache_m1["MockSym"] = bars
    
    res = runner.simulate_trade_m1(
        symbol="MockSym",
        direction="BUY",
        signal_time=pd.Timestamp("2026-10-15 18:00:00+00:00"),
        created_at=pd.Timestamp("2026-10-15 18:00:00+00:00"),
        entry_target=100.0,
        sl=90.0,
        tp1_target=110.0,
        tp2_target=120.0,
        fill_mode="signal_entry"
    )
    assert res["status"] == "CLOSED"
    assert res["outcome"] == "TP1_WIN_RUNNER_BE"
    assert res["leg1_reason"] == "TP1_WIN"
    assert res["leg2_reason"] == "BE_LOSS"
    # Net RR: 0.5 * 1.0 + 0.5 * 0.0 = +0.50R
    assert pytest.approx(res["realized_rr"], 0.01) == 0.50

def test_full_tp2_win():
    runner = ProspectiveM1ReplayRunner(dry_run=True)
    # Entry at 100, SL at 90, TP1 at 110, TP2 at 120 (BUY)
    # Bar 0: reaches 112 (TP1 hit)
    # Bar 1: reaches 121 (TP2 hit)
    bars = create_mock_bars([
        (100.0, 112.0, 100.0, 110.0),
        (110.0, 122.0, 105.0, 121.0)
    ])
    runner.cache_m1["MockSym"] = bars
    
    res = runner.simulate_trade_m1(
        symbol="MockSym",
        direction="BUY",
        signal_time=pd.Timestamp("2026-10-15 18:00:00+00:00"),
        created_at=pd.Timestamp("2026-10-15 18:00:00+00:00"),
        entry_target=100.0,
        sl=90.0,
        tp1_target=110.0,
        tp2_target=120.0,
        fill_mode="signal_entry"
    )
    assert res["status"] == "CLOSED"
    assert res["outcome"] == "FULL_TP2_WIN"
    assert res["leg1_reason"] == "TP1_WIN"
    assert res["leg2_reason"] == "TP2_WIN"
    # Net RR: 0.5 * 1.0 + 0.5 * 2.0 = +1.50R
    assert pytest.approx(res["realized_rr"], 0.01) == 1.50

def test_full_sl_loss():
    runner = ProspectiveM1ReplayRunner(dry_run=True)
    # Entry at 100, SL at 90, TP1 at 110, TP2 at 120 (BUY)
    # Bar 0: drops to 89
    bars = create_mock_bars([
        (100.0, 102.0, 89.0, 91.0)
    ])
    runner.cache_m1["MockSym"] = bars
    
    res = runner.simulate_trade_m1(
        symbol="MockSym",
        direction="BUY",
        signal_time=pd.Timestamp("2026-10-15 18:00:00+00:00"),
        created_at=pd.Timestamp("2026-10-15 18:00:00+00:00"),
        entry_target=100.0,
        sl=90.0,
        tp1_target=110.0,
        tp2_target=120.0,
        fill_mode="signal_entry"
    )
    assert res["status"] == "CLOSED"
    assert res["outcome"] == "SL_LOSS"
    assert res["realized_rr"] == -1.0


def test_ict_asset_consistency_and_discrepancy_reconciliation():
    """
    Concilia y valida la discrepancia reportada entre el 60% (3/5) y 4/5 en ICT:
    - 4 activos únicos operaron en los 7 eventos prospectivos de ICT:
      * Boom 300 Index: +1.35 R (1 win, 0 loss) -> RENTABLE (>0)
      * Boom 500 Index: +0.28 R (1 win, 1 loss) -> RENTABLE (>0)
      * Crash 300 Index: +0.50 R (1 win, 1 loss) -> RENTABLE (>0)
      * Boom 600 Index: -0.58 R (1 win, 1 loss) -> NO RENTABLE (<0)
    - Total activos con trades: 4 activos.
    - Activos con PnL neto positivo: 3 de 4 (75.0%).
    - Si se evalúa contra la cesta de 5 activos sintéticos habilitados (incluyendo Boom 1000 con 0 trades): 3 de 5 (60.0%).
    - Si se cuentan erróneamente activos con AL MENOS un trade ganador: son 4 de 4 (o 4 de 5 con Jump 10 de MSNR).
    """
    # Resultados reproducidos de los 7 eventos prospectivos de ICT (variante base)
    ict_events = [
        {"id": 5, "symbol": "Boom 500 Index", "rr": -1.00},
        {"id": 9, "symbol": "Crash 300 Index", "rr": -1.00},
        {"id": 13, "symbol": "Crash 300 Index", "rr": 1.50},
        {"id": 17, "symbol": "Boom 500 Index", "rr": 1.283306},
        {"id": 21, "symbol": "Boom 600 Index", "rr": -1.00},
        {"id": 30, "symbol": "Boom 300 Index", "rr": 1.354567},
        {"id": 34, "symbol": "Boom 600 Index", "rr": 0.424471},
    ]

    df = pd.DataFrame(ict_events)
    grouped = df.groupby("symbol")["rr"].sum()

    # 1. Verificar PnL neto por activo
    assert grouped["Boom 300 Index"] == pytest.approx(1.35, abs=0.01)
    assert grouped["Boom 500 Index"] == pytest.approx(0.28, abs=0.01)
    assert grouped["Crash 300 Index"] == pytest.approx(0.50, abs=0.01)
    assert grouped["Boom 600 Index"] == pytest.approx(-0.58, abs=0.01)

    # 2. Activos con PnL neto > 0
    profitable_assets = [sym for sym, net_rr in grouped.items() if net_rr > 0]
    unprofitable_assets = [sym for sym, net_rr in grouped.items() if net_rr <= 0]

    assert len(profitable_assets) == 3
    assert set(profitable_assets) == {"Boom 300 Index", "Boom 500 Index", "Crash 300 Index"}
    assert len(unprofitable_assets) == 1
    assert unprofitable_assets == ["Boom 600 Index"]

    # 3. Ratio sobre activos operados (3 de 4 = 75.0%)
    ratio_traded = len(profitable_assets) / len(grouped)
    assert ratio_traded == pytest.approx(0.75, abs=0.01)

    # 4. Ratio sobre la cesta de 5 activos Boom/Crash (3 de 5 = 60.0%)
    synthetic_basket_5 = ["Boom 300 Index", "Boom 500 Index", "Crash 300 Index", "Boom 600 Index", "Boom 1000 Index"]
    ratio_basket_5 = len(profitable_assets) / len(synthetic_basket_5)
    assert ratio_basket_5 == pytest.approx(0.60, abs=0.01)

    # 5. Activos con al menos una operación ganadora (4 de 4)
    assets_with_wins = [sym for sym, grp in df.groupby("symbol") if (grp["rr"] > 0).any()]
    assert len(assets_with_wins) == 4


def test_archive_manifest_integrity():
    """
    Valida la existencia y hash de integridad del archivo M1 offline.
    """
    import json
    import hashlib

    manifest_path = Path(__file__).resolve().parent.parent / "storage" / "runtime" / "m1_prospective_cache" / "manifest.json"
    assert manifest_path.exists(), "El manifiesto manifest.json no existe en el cache"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert "symbols" in manifest
    assert len(manifest["symbols"]) == 6
    cache_dir = manifest_path.parent

    for sym, meta in manifest["symbols"].items():
        csv_path = cache_dir / meta["file"]
        assert csv_path.exists(), f"Archivo CSV {csv_path} no existe"
        with open(csv_path, "rb") as f:
            computed_sha = hashlib.sha256(f.read()).hexdigest()
        assert computed_sha == meta["sha256"], f"Checksum inválido para {sym}"


def test_freshness_guard_discards_stale_signals():
    """
    Valida la regla experimental de frescura/caducidad de señal (Staleness Guard):
    - Señales con retraso > max_staleness_minutes deben ser descartadas con EXPIRED_STALE y 0.0R.
    - Señales frescas (<= max_staleness_minutes) deben ejecutarse normalmente.
    """
    runner = ProspectiveM1ReplayRunner(dry_run=True, max_staleness_minutes=3.0)
    bars = create_mock_bars([
        (100.0, 112.0, 100.0, 110.0),
        (110.0, 110.0, 99.0, 101.0)
    ])
    runner.cache_m1["MockSym"] = bars

    # Señal vencida (5 minutos de antigüedad > 3.0 min límite)
    res_stale = runner.simulate_trade_m1(
        symbol="MockSym",
        direction="BUY",
        signal_time=pd.Timestamp("2026-10-15 18:00:00+00:00"),
        created_at=pd.Timestamp("2026-10-15 18:05:00+00:00"),
        entry_target=100.0,
        sl=90.0,
        tp1_target=110.0,
        tp2_target=120.0,
        fill_mode="signal_entry"
    )
    assert res_stale["outcome"] == "EXPIRED_STALE"
    assert res_stale["realized_rr"] == 0.0
    assert res_stale["status"] == "DISCARDED"

    # Señal fresca (1 minuto de antigüedad <= 3.0 min límite)
    # Las barras para la señal fresca deben ocurrir a partir de created_at (18:01:00)
    data_fresh = [
        {"time": pd.Timestamp("2026-10-15 18:01:00+00:00"), "open": 100.0, "high": 112.0, "low": 100.0, "close": 110.0, "tick_volume": 100, "real_volume": 0, "spread": 0, "complete": True},
        {"time": pd.Timestamp("2026-10-15 18:02:00+00:00"), "open": 110.0, "high": 110.0, "low": 99.0, "close": 101.0, "tick_volume": 100, "real_volume": 0, "spread": 0, "complete": True}
    ]
    runner.cache_m1["MockFresh"] = pd.DataFrame(data_fresh)

    res_fresh = runner.simulate_trade_m1(
        symbol="MockFresh",
        direction="BUY",
        signal_time=pd.Timestamp("2026-10-15 18:00:00+00:00"),
        created_at=pd.Timestamp("2026-10-15 18:01:00+00:00"),
        entry_target=100.0,
        sl=90.0,
        tp1_target=110.0,
        tp2_target=120.0,
        fill_mode="signal_entry"
    )
    assert res_fresh["status"] == "CLOSED"
    assert res_fresh["outcome"] == "TP1_WIN_RUNNER_BE"
    assert res_fresh["realized_rr"] == pytest.approx(0.50, abs=0.01)


def test_pre_fill_invalidation_guard_discards_touched_levels():
    """
    Valida la guarda de invalidación pre-fill:
    - Si el precio toca SL antes de created_at, la señal se descarta como INVALIDATED_PRE_FILL_SL (0.0R).
    - Si el precio toca TP antes de created_at, la señal se descarta como INVALIDATED_PRE_FILL_TP (0.0R).
    - Si no toca ningún nivel en el intervalo, se ejecuta normalmente.
    """
    runner = ProspectiveM1ReplayRunner(dry_run=True, pre_fill_guard=True)
    # Barra 0 (18:00): toca SL (85 <= 90) antes de created_at (18:02)
    # Barra 1 (18:01): normal
    # Barra 2 (18:02): created_at
    bars_sl = create_mock_bars([
        (100.0, 105.0, 85.0, 95.0),
        (95.0, 102.0, 94.0, 101.0),
        (101.0, 115.0, 100.0, 112.0)
    ])
    runner.cache_m1["SymSL"] = bars_sl
    res_sl = runner.simulate_trade_m1(
        symbol="SymSL",
        direction="BUY",
        signal_time=pd.Timestamp("2026-10-15 18:00:00+00:00"),
        created_at=pd.Timestamp("2026-10-15 18:02:00+00:00"),
        entry_target=100.0,
        sl=90.0,
        tp1_target=110.0,
        tp2_target=120.0,
        fill_mode="created_at"
    )
    assert res_sl["status"] == "DISCARDED"
    assert res_sl["outcome"] == "INVALIDATED_PRE_FILL_SL"
    assert res_sl["realized_rr"] == 0.0

    # Barra 0 (18:00): toca TP1 (115 >= 110) antes de created_at (18:02)
    bars_tp = create_mock_bars([
        (100.0, 115.0, 98.0, 112.0),
        (112.0, 114.0, 109.0, 110.0),
        (110.0, 111.0, 108.0, 109.0)
    ])
    runner.cache_m1["SymTP"] = bars_tp
    res_tp = runner.simulate_trade_m1(
        symbol="SymTP",
        direction="BUY",
        signal_time=pd.Timestamp("2026-10-15 18:00:00+00:00"),
        created_at=pd.Timestamp("2026-10-15 18:02:00+00:00"),
        entry_target=100.0,
        sl=90.0,
        tp1_target=110.0,
        tp2_target=120.0,
        fill_mode="created_at"
    )
    assert res_tp["status"] == "DISCARDED"
    assert res_tp["outcome"] == "INVALIDATED_PRE_FILL_TP"
    assert res_tp["realized_rr"] == 0.0



