from pathlib import Path
from sqlalchemy import select

from database.repository import TradingRepository
from database.models import InstrumentSelectionProfilePreference
from dashboard.realtime_dashboard import RealtimeDashboardService


def catalog():
    return {
        "forex": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD"],
        "orb_ny_gold": ["XAUUSDmicro"],
        "orb_ny_wall_street_30": ["Wall Street 30"],
        "orb_ny_us_tech_100": ["US Tech 100"],
        "orb_ny_us_500": ["US500"],
        "volatility": ["Volatility 75 Index"],
    }


def test_forex_survives_repository_restart(tmp_path):
    db = tmp_path / "bot.sqlite3"
    repo = TradingRepository(db_path=db)
    repo.save_instrument_selection_profile(
        ["EURUSD", "USDJPY"], selection_profile="FOREX", source="DEMO"
    )
    repo2 = TradingRepository(db_path=db)
    assert repo2.latest_instrument_selection_profile("FOREX", source="DEMO")["selected_symbols"] == ["EURUSD", "USDJPY"]


def test_forex_survives_dashboard_restart_and_stale_state_file(tmp_path):
    db = tmp_path / "bot.sqlite3"
    state = tmp_path / "dashboard.json"
    repo = TradingRepository(db_path=db)
    dash = RealtimeDashboardService(repository=repo, state_path=state, port=0)
    dash.set_instrument_catalog(catalog())
    result = dash.update_selected_symbols(["EURUSD", "AUDUSD"], selection_profile="FOREX")
    assert result["ok"] is True
    assert result["persistence_verified"] is True

    # Simula un snapshot visual antiguo/corrupto que marca todos los Forex.
    state.write_text('{"selection_profiles":{"FOREX":["EURUSD","GBPUSD","USDJPY","AUDUSD"]}}', encoding="utf-8")

    repo2 = TradingRepository(db_path=db)
    dash2 = RealtimeDashboardService(repository=repo2, state_path=state, port=0)
    dash2.set_instrument_catalog(catalog())
    snap = dash2.snapshot()
    assert snap["selection_profiles"]["FOREX"] == ["AUDUSD", "EURUSD"]
    assert snap["selection_persistence_status"] == "VERIFICADA"


def test_forex_and_orb_remain_independent_after_restart(tmp_path):
    db = tmp_path / "bot.sqlite3"
    repo = TradingRepository(db_path=db)
    repo.save_instrument_selection_profile(["EURUSD", "GBPUSD"], selection_profile="FOREX")
    repo.save_instrument_selection_profile(["US500"], selection_profile="ORB")

    restarted = TradingRepository(db_path=db)
    assert restarted.latest_instrument_selection_profile("FOREX")["selected_symbols"] == ["EURUSD", "GBPUSD"]
    assert restarted.latest_instrument_selection_profile("ORB")["selected_symbols"] == ["US500"]


def test_only_one_authoritative_row_per_profile_after_multiple_saves(tmp_path):
    db = tmp_path / "bot.sqlite3"
    repo = TradingRepository(db_path=db)
    repo.save_instrument_selection_profile(["EURUSD"], selection_profile="FOREX")
    repo.save_instrument_selection_profile(["GBPUSD"], selection_profile="FOREX")
    repo.save_instrument_selection_profile(["USDJPY"], selection_profile="FOREX")

    with repo.Session() as session:
        rows = list(session.execute(
            select(InstrumentSelectionProfilePreference).where(
                InstrumentSelectionProfilePreference.source == "DEMO",
                InstrumentSelectionProfilePreference.selection_profile == "FOREX",
            )
        ).scalars())
    assert len(rows) == 1
    assert repo.latest_instrument_selection_profile("FOREX")["selected_symbols"] == ["USDJPY"]
    assert repo.latest_instrument_selection_profile("FOREX")["version"] == 3


def test_empty_forex_selection_is_persistent_and_not_replaced_by_full_catalog(tmp_path):
    db = tmp_path / "bot.sqlite3"
    repo = TradingRepository(db_path=db)
    dash = RealtimeDashboardService(repository=repo, state_path=tmp_path/"a.json", port=0)
    dash.set_instrument_catalog(catalog())
    assert dash.update_selected_symbols([], selection_profile="FOREX")["ok"] is True

    dash2 = RealtimeDashboardService(repository=TradingRepository(db_path=db), state_path=tmp_path/"b.json", port=0)
    dash2.set_instrument_catalog(catalog())
    assert dash2.snapshot()["selection_profiles"]["FOREX"] == []
