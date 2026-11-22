"""tests/test_performance_optimizations.py - Verificación de optimizaciones técnicas de rendimiento.

Valida:
1. Pre-calentamiento JIT de kernels SMC y cumplimiento del interruptor DAEMONBLACKFX_SMC_JIT_WARMUP.
2. Caché de velas Zero-Copy en MT5DataProvider y su interruptor DAEMONBLACKFX_CANDLE_ZERO_COPY_CACHE.
3. Persistencia por lotes (Batch Transactions) en TradingRepository (save_signals_batch y save_audit_events_batch).
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from brokers.mt5_data import MT5DataProvider
from database.models import DaemonAuditEvent, Signal
from database.repository import TradingRepository
from strategy.smc.choch_bos import detect_choch_bos
from strategy.smc.warmup import warmup_smc_kernels


def test_smc_warmup_runs_and_respects_flag(monkeypatch):
    # Probar que con flag desactivado no ejecuta
    monkeypatch.setenv("DAEMONBLACKFX_SMC_JIT_WARMUP", "0")
    res_disabled = warmup_smc_kernels(force=False)
    assert res_disabled["enabled"] is False

    # Probar que con flag activado ejecuta y compila
    monkeypatch.setenv("DAEMONBLACKFX_SMC_JIT_WARMUP", "1")
    res_enabled = warmup_smc_kernels(force=True)
    assert res_enabled["warmed_up"] is True
    assert res_enabled["enabled"] is True
    assert res_enabled["elapsed_ms"] >= 0.0


def test_choch_bos_executes_without_errors():
    n = 30
    df = pd.DataFrame(
        {
            "time": pd.date_range("2026-01-01", periods=n, freq="5min", tz="UTC"),
            "open": np.linspace(100.0, 110.0, n),
            "high": np.linspace(101.0, 111.0, n),
            "low": np.linspace(99.0, 109.0, n),
            "close": np.linspace(100.5, 110.5, n),
            "swing_high": np.zeros(n, dtype=bool),
            "swing_low": np.zeros(n, dtype=bool),
        }
    )
    df.loc[5, "swing_high"] = True
    df.loc[15, "swing_low"] = True

    res = detect_choch_bos(df)
    assert "choch_bullish" in res.columns
    assert "choch_bearish" in res.columns
    assert "bos_bullish" in res.columns
    assert "bos_bearish" in res.columns
    assert "structure_break_level" in res.columns
    assert len(res) == n


def test_mt5_data_provider_zero_copy_cache(monkeypatch):
    class DummyConnector:
        def is_connected(self):
            return True

        def connect(self):
            return True

        def disconnect(self):
            return True

    provider = MT5DataProvider(connector=DummyConnector())
    now = pd.Timestamp.now(tz="UTC")
    dates = pd.date_range("2026-11-01", periods=100, freq="5min", tz="UTC")
    sample_df = pd.DataFrame(
        {
            "time": dates,
            "open": np.linspace(100.0, 110.0, 100),
            "high": np.linspace(101.0, 111.0, 100),
            "low": np.linspace(99.0, 109.0, 100),
            "close": np.linspace(100.5, 110.5, 100),
            "tick_volume": np.ones(100, dtype=int) * 100,
            "spread": np.ones(100, dtype=int) * 2,
            "real_volume": np.ones(100, dtype=int) * 100,
        }
    )

    # Inyectar en caché interna
    cache_key = ("TEST_SYM", provider.TIMEFRAMES["M5"])
    import time

    provider._candle_cache[cache_key] = (time.monotonic(), sample_df)
    provider._resolved_symbol_cache["test_sym"] = "TEST_SYM"
    provider._ensured_symbols.add("TEST_SYM")

    # Caso 1: Zero-copy activado (por defecto)
    monkeypatch.setenv("DAEMONBLACKFX_CANDLE_ZERO_COPY_CACHE", "1")
    candles_zc = provider.get_candles("TEST_SYM", "M5", count=100)
    assert len(candles_zc) == 100
    # Al pedir exactamente count=100, devuelve la referencia directa
    assert candles_zc is sample_df

    # Caso 2: Zero-copy desactivado (hace copia)
    monkeypatch.setenv("DAEMONBLACKFX_CANDLE_ZERO_COPY_CACHE", "0")
    candles_copy = provider.get_candles("TEST_SYM", "M5", count=100)
    assert len(candles_copy) == 100
    assert candles_copy is not sample_df


def test_repository_save_signals_batch(tmp_path: Path):
    db_file = tmp_path / "test_batch.sqlite3"
    repo = TradingRepository(db_file)

    now = datetime.now(timezone.utc)
    batch = [
        {
            "instrument": f"PAIR_{i}",
            "timeframe": "M5",
            "signal_time": now,
            "direction": "BUY" if i % 2 == 0 else "SELL",
            "valid": True,
            "trend_ok": True,
            "order_block_ok": True,
            "confirmation_ok": True,
            "details": {"score": 85.0 + i},
        }
        for i in range(15)
    ]

    ids = repo.save_signals_batch(batch)
    assert len(ids) == 15
    assert all(isinstance(x, int) and x > 0 for x in ids)

    # Verificar lectura
    with repo.Session() as s:
        signals_in_db = s.query(Signal).all()
        assert len(signals_in_db) == 15
        assert signals_in_db[0].instrument == "PAIR_0"
        assert signals_in_db[14].instrument == "PAIR_14"

    # Verificar lista vacía
    assert repo.save_signals_batch([]) == []


def test_repository_save_audit_events_batch(tmp_path: Path):
    db_file = tmp_path / "test_batch_audit.sqlite3"
    repo = TradingRepository(db_file)

    now = datetime.now(timezone.utc)
    events = [
        {
            "event_type": "BATCH_TEST",
            "source": "DEMO",
            "instrument": f"SYM_{i}",
            "action": "EVALUATE",
            "reason": f"Reason {i}",
            "cycle_number": i,
            "payload": {"status": "ok", "index": i},
        }
        for i in range(10)
    ]

    ids = repo.save_audit_events_batch(events)
    assert len(ids) == 10
    assert all(isinstance(x, int) and x > 0 for x in ids)

    with repo.Session() as s:
        events_in_db = s.query(DaemonAuditEvent).all()
        assert len(events_in_db) == 10
        assert events_in_db[0].event_type == "BATCH_TEST"
        assert events_in_db[0].instrument == "SYM_0"

    assert repo.save_audit_events_batch([]) == []
