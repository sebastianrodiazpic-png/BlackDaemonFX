import pytest

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
