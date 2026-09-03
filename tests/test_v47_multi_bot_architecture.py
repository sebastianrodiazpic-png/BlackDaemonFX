
import inspect
from pathlib import Path
from types import SimpleNamespace

from database.database import get_engine
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine
from app.main import BOT_PROFILES, run_demo_bot


def _engine(profile, magic):
    e = object.__new__(LiveTradingEngine)
    e.config = LiveTradingConfig(
        bot_profile=profile,
        magic=magic,
        execution_enabled=True,
    )
    return e


def test_magic_numbers_are_unique():
    magics = [spec["magic"] for spec in BOT_PROFILES.values()]
    assert len(magics) == len(set(magics))
    assert BOT_PROFILES["SYNTHETICS"]["magic"] == 26082026
    assert BOT_PROFILES["FOREX"]["magic"] == 26082027
    assert BOT_PROFILES["ORB"]["magic"] == 26082028


def test_trade_ownership_by_magic():
    synth = _engine("SYNTHETICS", 26082026)
    forex = _engine("FOREX", 26082027)
    orb = _engine("ORB", 26082028)

    trade = {"details": {"metadata": {"daemon_magic": 26082027}}}
    assert forex._trade_owned_by_current_bot(trade) is True
    assert synth._trade_owned_by_current_bot(trade) is False
    assert orb._trade_owned_by_current_bot(trade) is False


def test_legacy_trade_is_only_owned_by_historical_synthetics_bot():
    legacy = {"details": {"metadata": {}}}
    assert _engine("SYNTHETICS", 26082026)._trade_owned_by_current_bot(legacy) is True
    assert _engine("FOREX", 26082027)._trade_owned_by_current_bot(legacy) is False
    assert _engine("ORB", 26082028)._trade_owned_by_current_bot(legacy) is False


def test_run_demo_bot_supports_profile_magic_and_centralized_export_flag():
    params = inspect.signature(run_demo_bot).parameters
    assert "bot_profile" in params
    assert "magic" in params
    assert "auto_export" in params


def test_sqlite_uses_wal_and_busy_timeout(tmp_path):
    engine = get_engine(tmp_path / "multi.db")
    with engine.connect() as connection:
        journal = connection.exec_driver_sql("PRAGMA journal_mode").scalar_one()
        timeout = connection.exec_driver_sql("PRAGMA busy_timeout").scalar_one()
    assert str(journal).lower() == "wal"
    assert int(timeout) >= 30000


def test_windows_launchers_exist():
    root = Path(__file__).resolve().parents[1]
    assert (root / "run_synthetics_bot.bat").exists()
    assert (root / "run_forex_bot.bat").exists()
    assert (root / "run_orb_bot.bat").exists()
    assert (root / "run_all_bots.bat").exists()
