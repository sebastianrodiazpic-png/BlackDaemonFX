"""Tests de las optimizaciones de rendimiento de procesos, I/O y memoria (26-oct-2026)."""
import json
from types import SimpleNamespace

import pytest

import app.main as main_mod
from dashboard.realtime_dashboard import RealtimeDashboardService
from marketdata.factory import ExternalMarketDataSettings
from marketdata.normalization import MarketDataIdentity, normalize_candles
from marketdata.shadow import ShadowMarketDataProvider


def test_skip_disabled_worker_processes_by_default(monkeypatch):
    monkeypatch.delenv("DAEMONBLACKFX_SKIP_DISABLED_WORKER_PROCESSES", raising=False)
    monkeypatch.delenv("DAEMONBLACKFX_DISABLED_WORKERS", raising=False)
    monkeypatch.delenv("DAEMONBLACKFX_DRIFT", raising=False)
    monkeypatch.delenv("DAEMONBLACKFX_SPAWN_EMPTY_FLIP_WORKER", raising=False)

    repo = SimpleNamespace(open_trades=lambda source="DEMO": [])

    for disabled_prof in ("FOREX_2", "FOREX_3", "FOREX_4", "VOLATILITY_2", "VOLATILITY_3", "VOLATILITY_4", "GOLD", "DRIFT", "FLIP"):
        skip, reason = main_mod._should_skip_disabled_worker_process(disabled_prof, repo)
        assert skip is True, f"{disabled_prof} debería omitirse cuando no tiene posiciones abiertas"
        assert reason

    for active_prof in ("BOOM", "CRASH", "VOLATILITY_1", "STEP", "JUMP", "ORB", "MALAYSIAN_SNR", "RSI2", "CARRY"):
        skip, reason = main_mod._should_skip_disabled_worker_process(active_prof, repo)
        assert skip is False and reason is None


def test_disabled_worker_with_open_positions_is_never_skipped(monkeypatch):
    monkeypatch.delenv("DAEMONBLACKFX_SKIP_DISABLED_WORKER_PROCESSES", raising=False)
    repo_by_profile = SimpleNamespace(
        open_trades=lambda source="DEMO": [
            {"id": 1, "instrument": "XAUUSD", "details": {"metadata": {"bot_profile": "GOLD"}}}
        ]
    )
    skip, _ = main_mod._should_skip_disabled_worker_process("GOLD", repo_by_profile)
    assert skip is False

    gold_magic = main_mod.BOT_PROFILES["GOLD"]["magic"]
    repo_by_magic = SimpleNamespace(
        open_trades=lambda source="DEMO": [
            {"id": 2, "instrument": "XAUUSD", "daemon_magic": gold_magic, "details": {}}
        ]
    )
    skip_magic, _ = main_mod._should_skip_disabled_worker_process("GOLD", repo_by_magic)
    assert skip_magic is False


def test_skip_disabled_worker_processes_switch_off(monkeypatch):
    monkeypatch.setenv("DAEMONBLACKFX_SKIP_DISABLED_WORKER_PROCESSES", "0")
    repo = SimpleNamespace(open_trades=lambda source="DEMO": [])
    skip, reason = main_mod._should_skip_disabled_worker_process("GOLD", repo)
    assert skip is False and reason is None


def test_external_market_data_settings_default_to_external(monkeypatch):
    monkeypatch.delenv("DAEMON_MARKET_DATA_MODE", raising=False)
    assert ExternalMarketDataSettings().mode == "external"
    assert ExternalMarketDataSettings.from_environment().mode == "external"
    monkeypatch.setenv("DAEMON_MARKET_DATA_MODE", "shadow")
    assert ExternalMarketDataSettings.from_environment().mode == "shadow"


def test_shadow_provider_rotates_file_and_respects_write_switch(tmp_path, monkeypatch):
    class Primary:
        connector = object()

        def get_candles(self, symbol, timeframe, count):
            return normalize_candles(
                [
                    {"time": "2026-09-14T11:55:00Z", "open": 1, "high": 2, "low": 0.5, "close": 1.5},
                    {"time": "2026-09-14T12:00:00Z", "open": 1.5, "high": 2, "low": 1, "close": 1.7},
                ],
                identity=MarketDataIdentity(symbol, "frxEURUSD", "DERIV"),
                timeframe=timeframe,
            )

    class Reference:
        def get_candles(self, symbol, timeframe, count):
            return Primary().get_candles(symbol, timeframe, count)

    out = tmp_path / "shadow.jsonl"
    out.write_bytes(b"x" * (2 * 1024 * 1024))
    monkeypatch.setenv("DAEMON_SHADOW_MAX_FILE_MB", "1.0")
    provider = ShadowMarketDataProvider(Primary(), Reference(), output_path=out)
    provider.get_candles("EURUSD", "M5", 10)

    rotated = tmp_path / "shadow.jsonl.1"
    assert rotated.exists() and rotated.stat().st_size == 2 * 1024 * 1024
    assert out.exists() and out.stat().st_size < 2048

    # Interruptor de escritura desactivado
    monkeypatch.setenv("DAEMON_SHADOW_WRITE_ENABLED", "0")
    size_before = out.stat().st_size
    provider.get_candles("EURUSD", "M5", 10)
    assert out.stat().st_size == size_before


def test_compact_persisted_dashboard_state_excludes_heavy_keys(tmp_path, monkeypatch):
    state_file = tmp_path / "last_state.json"
    monkeypatch.delenv("DAEMONBLACKFX_COMPACT_PERSISTED_STATE", raising=False)
    dash = RealtimeDashboardService(repository=None, host="127.0.0.1", port=0, state_path=state_file)
    with dash._lock:
        dash._state["account"] = {"snapshot": {"balance": 10000}, "recent_trades": [{"id": i} for i in range(500)]}
        dash._state["open_positions"] = [{"id": 1, "chart": {"candles": [1, 2, 3]}}]
        dash._state["cycle"] = 42
        dash._persist_state_locked()

    persisted = json.loads(state_file.read_text(encoding="utf-8"))
    assert persisted["cycle"] == 42
    assert "account" not in persisted
    assert "open_positions" not in persisted

    # Con el interruptor desactivado se vuelve a guardar completo
    monkeypatch.setenv("DAEMONBLACKFX_COMPACT_PERSISTED_STATE", "0")
    with dash._lock:
        dash._persist_state_locked()
    persisted_full = json.loads(state_file.read_text(encoding="utf-8"))
    assert "account" in persisted_full
    assert "open_positions" in persisted_full
