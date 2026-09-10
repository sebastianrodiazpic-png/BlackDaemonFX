import time
from pathlib import Path
from dashboard.realtime_dashboard import RealtimeDashboardService


class Repo:
    def __init__(self):
        self.account_calls=0
        self.selection_calls=0
    def latest_instrument_selection_profiles(self, source="DEMO"):
        self.selection_calls+=1
        return {
            "FOREX":{"selected_symbols":["EURUSD"],"version":1},
            "ORB":{"selected_symbols":["XAUUSD"],"version":1},
            "SYNTHETICS":{"selected_symbols":["Boom 1000 Index"],"version":1},
        }
    def latest_instrument_selection(self, source="DEMO"):
        return None
    def open_trades(self, source="DEMO"):
        return []
    def trade_visual_audits(self, source="DEMO"):
        return []
    def position_visual_audits(self, source="DEMO"):
        return []
    def latest_worker_process_results(self, source="DEMO"):
        return {}
    def worker_runtime_states(self, source="DEMO"):
        return []
    def recent_symbol_process_results(self, **kwargs):
        return []


def _service(tmp_path):
    repo=Repo()
    s=RealtimeDashboardService(repository=repo,state_path=tmp_path/"state.json")
    s.set_instrument_catalog({
        "boom":["Boom 1000 Index"],
        "forex":["EURUSD","GBPUSD"],
        "orb_ny_gold":["XAUUSD"],
    })
    return s,repo


def test_instruments_payload_is_light_and_cached(tmp_path):
    s,repo=_service(tmp_path)
    first=s._cached_instruments_payload(force=True)
    calls=repo.selection_calls
    second=s._cached_instruments_payload()
    assert first==second
    assert repo.selection_calls==calls
    assert "instrument_catalog" in first
    assert "selection_profiles" in first
    assert "open_positions" not in first
    assert "account" not in first
    assert "recent" not in first


def test_instruments_cache_invalidates_after_catalog_change(tmp_path):
    s,repo=_service(tmp_path)
    a=s._cached_instruments_payload(force=True)
    s.set_instrument_catalog({"forex":["EURUSD","GBPUSD","USDJPY"]})
    b=s._cached_instruments_payload()
    universe={x for g in b["instrument_catalog"] for x in g["symbols"]}
    assert "USDJPY" in universe


def test_dashboard_source_has_dedicated_instruments_endpoint():
    root=Path(__file__).resolve().parents[1]
    text=(root/"dashboard"/"realtime_dashboard.py").read_text(encoding="utf-8")
    assert 'if path == "/api/instruments":' in text
    assert "fetch('/api/instruments?ts='+Date.now()" in text


def test_dashboard_main_still_uses_state_endpoint():
    root=Path(__file__).resolve().parents[1]
    text=(root/"dashboard"/"realtime_dashboard.py").read_text(encoding="utf-8")
    assert "async function refresh(){if(document.hidden)return;try{const r=await fetch('/api/state?ts='" in text


def test_short_ttls_are_configured():
    root=Path(__file__).resolve().parents[1]
    text=(root/"dashboard"/"realtime_dashboard.py").read_text(encoding="utf-8")
    # v109: TTLs subidos (optimizacion de memoria del coordinador, ver punto 1
    # y 3 de la revision de rendimiento) para acompanar el polling mas
    # espaciado del navegador (6s en vez de 2s).
    assert "self._account_cache_ttl_seconds = 6.0" in text
    assert "self._instruments_cache_ttl_seconds = 5.0" in text
    assert "self._snapshot_aux_cache_ttl_seconds = 5.0" in text
