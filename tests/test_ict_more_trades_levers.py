"""Palancas ICT para más trades sin bajar el acierto (replay fiel ICT 365d, límite + tope spread/SL 2%)."""
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from strategy.execution.live_trading_engine import DEFAULT_MAX_OPEN_POSITIONS, LiveTradingConfig, LiveTradingEngine

ROOT = Path(__file__).resolve().parents[1]
UNPRUNED = {"Boom 500 Index", "Boom 600 Index", "Crash 300 Index", "Step Index 200",
            "Volatility 10 Index", "Volatility 100 Index", "Volatility 100 (1s) Index"}


def test_unpruned_synthetics_in_worker_allowlists():
    c = LiveTradingConfig()
    allowed = (set(c.step_allowed_symbols) | set(c.volatility_allowed_symbols) | set(c.boom_allowed_symbols)
               | set(c.crash_allowed_symbols))
    assert UNPRUNED <= allowed
    # Siguen podados: WR <= 50% o R neto <= 0 en el replay fiel de 212 pares
    assert "Volatility 90 (1s) Index" not in allowed and "Crash 1000 Index" not in allowed


def test_env_restores_previous_pruning():
    out = subprocess.run([sys.executable, "-c",
                          "from strategy.execution.live_trading_engine import LiveTradingConfig as C; c=C();"
                          "print('Boom 500 Index' in c.boom_allowed_symbols, 'Volatility 10 Index' in c.volatility_allowed_symbols)"],
                         cwd=str(ROOT), capture_output=True, text=True, timeout=300,
                         env={**__import__("os").environ, "DAEMONBLACKFX_ICT_UNPRUNE_SYNTHETICS": "0"})
    assert out.returncode == 0, out.stderr[-400:]
    assert out.stdout.strip().splitlines()[-1] == "False False"


def test_max_open_positions_is_eight_operations():
    assert DEFAULT_MAX_OPEN_POSITIONS == 16
    assert LiveTradingConfig().max_open_positions == 16
    main_src = (ROOT / "app" / "main.py").read_text(encoding="utf-8")
    assert "default=DEFAULT_MAX_OPEN_POSITIONS" in main_src  # --max-open-positions de los workers
    assert 'getattr(args, "max_open_positions", 10)' not in main_src


def test_max_open_positions_env_override():
    out = subprocess.run([sys.executable, "-c",
                          "from strategy.execution.live_trading_engine import LiveTradingConfig as C; print(C().max_open_positions)"],
                         cwd=str(ROOT), capture_output=True, text=True, timeout=300,
                         env={**__import__("os").environ, "DAEMONBLACKFX_MAX_OPEN_POSITIONS": "12"})
    assert out.returncode == 0, out.stderr[-400:]
    assert out.stdout.strip().splitlines()[-1] == "12"


def test_ict_synthetic_meta_label_runs_in_shadow():
    assert LiveTradingConfig().ict_synthetic_meta_label_shadow is True
    import inspect
    src = inspect.getsource(LiveTradingEngine)
    i_shadow = src.index('"shadow_override": "ICT_SYNTHETIC_META_SHADOW"')
    i_block = src.index('"action": "META_LABEL_FILTER_REJECTED"')
    assert i_shadow < i_block  # la sombra se aplica antes del bloqueo
    assert 'and self._is_synthetic_symbol(exact_symbol)' in src[i_shadow - 600:i_shadow]
