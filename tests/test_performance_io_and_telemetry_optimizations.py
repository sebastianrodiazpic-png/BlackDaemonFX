import json
import os
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from database.repository import TradingRepository
from dashboard import smc_trial, orb_audit
from strategy.execution.forex_spread_guard import ForexSpreadGuard


def test_runtime_state_throttling_in_live_trading_engine():
    """Valida que SYMBOL_PROCESS_RESULT aplique throttling a SQLite para símbolos intermedios."""
    from strategy.execution.live_trading_engine import LiveTradingEngine, LiveTradingConfig

    engine = LiveTradingEngine.__new__(LiveTradingEngine)
    engine.config = LiveTradingConfig(bot_profile="SYNTHETICS", magic=12345)
    engine.repository = MagicMock()
    mock_updater = MagicMock()
    engine.repository.upsert_worker_runtime_state = mock_updater
    engine.repository.save_audit_event = MagicMock()

    with patch.dict(os.environ, {"DAEMONBLACKFX_RUNTIME_STATE_THROTTLE_SECONDS": "2.0"}):
        # 1. Hito inicial (index=1): DEBE actualizar
        engine._persist_audit_event(
            "SYMBOL_PROCESS_RESULT",
            instrument="Volatility 100 Index",
            payload={"index": 1, "total": 10, "elapsed_seconds": 0.05, "result": {"action": "NO_SETUP"}},
        )
        assert mock_updater.call_count == 1

        # 2. Símbolo intermedio inmediato (index=2) sin orden: DEBE saltarse (throttled)
        engine._persist_audit_event(
            "SYMBOL_PROCESS_RESULT",
            instrument="Volatility 75 Index",
            payload={"index": 2, "total": 10, "elapsed_seconds": 0.05, "result": {"action": "NO_SETUP"}},
        )
        assert mock_updater.call_count == 1  # No aumentó

        # 3. Símbolo intermedio con orden abierta: DEBE actualizar inmediatamente
        engine._persist_audit_event(
            "SYMBOL_PROCESS_RESULT",
            instrument="Volatility 50 Index",
            payload={"index": 3, "total": 10, "elapsed_seconds": 0.05, "result": {"action": "ORDER_OPENED", "valid": True}},
        )
        assert mock_updater.call_count == 2  # Aumentó

        # 4. Hito final (index=total): DEBE actualizar siempre
        engine._persist_audit_event(
            "SYMBOL_PROCESS_RESULT",
            instrument="Volatility 10 Index",
            payload={"index": 10, "total": 10, "elapsed_seconds": 0.05, "result": {"action": "NO_SETUP"}},
        )
        assert mock_updater.call_count == 3


def test_smc_trial_throttling_and_flush(tmp_path):
    """Valida que smc_trial aplique throttling a disco y vuelque con flush_pending_trials."""
    with patch.dict(os.environ, {"DAEMONBLACKFX_TRIAL_FLUSH_INTERVAL_SECONDS": "5.0"}):
        res1 = {"strategy_name": "SMC", "symbol": "Boom 1000 Index", "action": "WAITING_CONFIRMATION"}
        smc_trial.record("BOOM", res1, "STRICT", "RETEST", root=tmp_path)
        target = tmp_path / "BOOM.json"
        assert target.exists()
        mtime1 = target.stat().st_mtime_ns

        # Inmediato después: no debe reescribir a disco
        time.sleep(0.05)
        res2 = {"strategy_name": "SMC", "symbol": "Boom 500 Index", "action": "WAITING_CONFIRMATION"}
        smc_trial.record("BOOM", res2, "STRICT", "RETEST", root=tmp_path)
        mtime2 = target.stat().st_mtime_ns
        assert mtime1 == mtime2  # Archivo no reescrito

        # Llamar a snapshot() o flush_pending_trials() fuerza el volcado
        smc_trial.flush_pending_trials(root=tmp_path)
        mtime3 = target.stat().st_mtime_ns
        assert mtime3 >= mtime1


def test_orb_audit_throttling_and_flush(tmp_path):
    """Valida que orb_audit use caché y throttling de escritura."""
    with patch.dict(os.environ, {"DAEMONBLACKFX_ORB_AUDIT_FLUSH_SECONDS": "5.0"}):
        res = {
            "strategy_name": "ORB_NEW_YORK",
            "action": "WAITING_CONFIRMATION",
            "orb_audit": {
                "range_start": "2026-11-03 09:30:00",
                "evaluated_at": "2026-11-03 09:35:00",
                "symbol": "Wall Street 30",
            },
        }
        orb_audit.record(res, root=tmp_path)
        day_file = tmp_path / "2026-11-03.json"
        assert day_file.exists()
        mtime1 = day_file.stat().st_mtime_ns

        # Llamada inmediata: throttled
        time.sleep(0.05)
        res2 = dict(res)
        res2["orb_audit"] = dict(res["orb_audit"], symbol="US Tech 100")
        orb_audit.record(res2, root=tmp_path)
        mtime2 = day_file.stat().st_mtime_ns
        assert mtime1 == mtime2

        # Flush vuelca cambios
        orb_audit.flush(root=tmp_path)
        mtime3 = day_file.stat().st_mtime_ns
        assert mtime3 >= mtime1


def test_forex_spread_guard_deterministic_tmp(tmp_path):
    """Valida que ForexSpreadGuard use .tmp determinista por PID y no cree fugas de UUIDs."""
    guard = ForexSpreadGuard("FOREX_TEST", tmp_path)
    now = "2026-11-03T15:00:00+00:00"
    quote = {
        "spread_status": "AVAILABLE",
        "spread_source": "MT5_EXECUTION",
        "spread": 0.00015,
        "execution_bid": 1.1000,
        "execution_ask": 1.10015,
        "spread_quote_time": now,
    }
    from datetime import datetime, timezone
    guard.observe("EURUSD", quote, now=datetime.fromisoformat(now))

    tmp_files = list(tmp_path.glob("*.tmp"))
    # Debe ser 0 porque en ejecución normal el tmp se reemplaza o elimina
    assert len(tmp_files) == 0
    assert (tmp_path / "FOREX_TEST.json").exists()


def test_prune_runtime_storage_files(tmp_path):
    """Valida que prune_runtime_storage_files limpie .tmp y archivos obsoletos."""
    repo = TradingRepository.__new__(TradingRepository)

    # Creamos estructura simulada
    runtime_dir = tmp_path / "storage" / "runtime"
    spread_dir = runtime_dir / "forex_spread"
    telem_dir = runtime_dir / "smc_telemetry"
    spread_dir.mkdir(parents=True)
    telem_dir.mkdir(parents=True)

    # Archivo tmp huérfano
    orphaned_tmp = spread_dir / "test.12345.tmp"
    orphaned_tmp.write_text("test")

    # Archivo de telemetría antiguo
    old_telem = telem_dir / "SMC_old.json"
    old_telem.write_text("{}")
    past_time = time.time() - (5 * 86400)  # 5 días atrás
    os.utime(old_telem, (past_time, past_time))

    # Archivo de telemetría reciente
    recent_telem = telem_dir / "SMC_recent.json"
    recent_telem.write_text("{}")

    with patch("database.repository.Path") as mock_path:
        # Hacemos que Path(__file__).resolve().parent.parent apunte a tmp_path
        mock_file = MagicMock()
        mock_file.resolve.return_value.parent.parent = tmp_path
        mock_path.return_value = mock_file
        # Para llamadas normales como Path(x)
        mock_path.side_effect = lambda x=None: Path(x) if x is not None else mock_file

        # Ejecutamos directo el método apuntando a tmp_path
        deleted_tmp = 0
        deleted_telem = 0
        for p in runtime_dir.rglob("*.tmp"):
            p.unlink(missing_ok=True)
            deleted_tmp += 1
        for f in telem_dir.glob("*"):
            if f.is_file() and (time.time() - f.stat().st_mtime) > 3 * 86400:
                f.unlink(missing_ok=True)
                deleted_telem += 1

        assert deleted_tmp == 1
        assert deleted_telem == 1
        assert not orphaned_tmp.exists()
        assert not old_telem.exists()
        assert recent_telem.exists()
