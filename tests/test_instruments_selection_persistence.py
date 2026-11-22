from database.repository import TradingRepository
from dashboard.realtime_dashboard import RealtimeDashboardService, DEFAULT_PRIORITIZED_SYMBOLS


def test_volatility_50_1s_not_in_defaults():
    assert "Volatility 50 (1s) Index" not in DEFAULT_PRIORITIZED_SYMBOLS.get("SYNTHETICS", [])
    assert "Volatility 50 (1s) Index" not in DEFAULT_PRIORITIZED_SYMBOLS.get("MALAYSIAN_SNR", [])


def test_deselect_volatility_50_1s_persists_across_refresh(tmp_path):
    repo = TradingRepository(db_path=tmp_path / "test_instruments.db")
    svc = RealtimeDashboardService(repository=repo, port=0, state_path=tmp_path / "state.json")
    
    # Simular catálogo de sintéticos con los índices de Volatility 1s
    catalog = {
        "volatility_4": [
            "Volatility 100 (1s) Index", "Volatility 150 (1s) Index", "Volatility 250 (1s) Index",
            "Volatility 50 (1s) Index", "Volatility 75 (1s) Index", "Volatility 90 (1s) Index",
            "Volatility 10 (1s) Index", "Volatility 15 (1s) Index", "Volatility 25 (1s) Index",
            "Volatility 30 (1s) Index", "Volatility 5 (1s) Index",
        ]
    }
    svc.set_instrument_catalog(catalog)
    
    # Lista de símbolos seleccionados EXCLUYENDO "Volatility 50 (1s) Index"
    selected_without_50_1s = [
        "Volatility 100 (1s) Index", "Volatility 150 (1s) Index", "Volatility 250 (1s) Index",
        "Volatility 75 (1s) Index", "Volatility 90 (1s) Index",
        "Volatility 10 (1s) Index", "Volatility 15 (1s) Index", "Volatility 25 (1s) Index",
        "Volatility 30 (1s) Index", "Volatility 5 (1s) Index",
    ]
    
    # Guardar selección como lo hace el usuario al presionar "Aplicar selección"
    res = svc.update_selected_symbols(selected_without_50_1s, selection_profile="SYNTHETICS", allow_selective=True)
    assert res.get("ok") is True
    
    # Verificar que en el estado inicial no esté Volatility 50 (1s) Index
    assert "Volatility 50 (1s) Index" not in svc.snapshot()["selection_profiles"]["SYNTHETICS"]
    
    # Ejecutar el refresco de perfiles desde DB (el que corre en cada poll /api/instruments)
    with svc._lock:
        svc._refresh_selection_profiles_from_db_locked()
        
    # Verificar que NO se reinserte Volatility 50 (1s) Index
    current_profiles = svc.snapshot()["selection_profiles"]
    assert "Volatility 50 (1s) Index" not in current_profiles["SYNTHETICS"]
    
    # Verificar que el payload cacheado tampoco lo contenga
    payload = svc._cached_instruments_payload(force=True)
    selected_in_payload = payload.get("selected_symbols") or []
    assert "Volatility 50 (1s) Index" not in selected_in_payload
