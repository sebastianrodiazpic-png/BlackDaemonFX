import os
import tempfile

import pytest

# Base de datos aislada: sin esto, todo lo que crea TradingRepository() o RealtimeDashboardService(repository=None)
# abría la base VIVA del bot (C:/Users/.../BlackDaemonFx/trading_bot.sqlite3). El 25-oct-2026 una comprobación así
# sobrescribió la selección DEMO de Malaysian SNR (restaurada). Debe fijarse antes de importar database.database.
_test_tmp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".test_tmp")
os.makedirs(_test_tmp_dir, exist_ok=True)
os.environ.setdefault("DAEMONBLACKFX_DB_PATH", os.path.join(_test_tmp_dir, "trading_bot.sqlite3"))

# Los tests ejercitan la lógica de todos los workers; en producción algunos están desactivados para entradas nuevas
# (DAEMONBLACKFX_DISABLED_WORKERS, 24-oct-2026). Su valor por defecto se prueba en test_disabled_workers.py.
os.environ.setdefault("DAEMONBLACKFX_DISABLED_WORKERS", "")
os.environ.setdefault("DAEMONBLACKFX_TREND_PULLBACK_ENABLED", "1")

# Modos clásicos de ORB previos a la Fase 1 (18-oct-2026). Los tests de mecánica
# breakout/momentum/retest los activan explícitamente, porque en producción la Fase 1
# deja allowed_modes=[] en todos los activos (XAUUSD solo opera SWEEP).
ORB_CLASSIC_MODES = {
    "XAUUSD": ["MOMENTUM", "RETEST"],
    "XAGUSD": ["RETEST"],
    "US500": ["MOMENTUM", "RETEST"],
    "US30": ["MOMENTUM", "RETEST"],
    "NAS100": ["MOMENTUM", "RETEST"],
    "BTCUSD": ["MOMENTUM"],
    "EURUSD": ["MOMENTUM", "RETEST"],
}


@pytest.fixture
def orb_classic_modes(monkeypatch):
    from strategy.orb import asset_rules

    for key, modes in ORB_CLASSIC_MODES.items():
        profile = dict(asset_rules.ASSET_CONFIG[key], allowed_modes=list(modes))
        profile.pop("sweep_enabled", None)
        monkeypatch.setitem(asset_rules.ASSET_CONFIG, key, profile)
