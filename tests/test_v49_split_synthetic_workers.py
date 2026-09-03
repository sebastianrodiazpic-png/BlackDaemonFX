
from pathlib import Path

from app.main import (
    BOT_PROFILES, SYNTHETIC_SPLIT_PROFILES, FULL_MULTI_BOT_PROFILES,
    VOLATILITY_SHARD_PROFILES,
)
from strategy.execution.live_trading_engine import LiveTradingConfig, LiveTradingEngine


def _engine(profile, magic):
    e = object.__new__(LiveTradingEngine)
    e.config = LiveTradingConfig(
        bot_profile=profile,
        magic=magic,
        execution_enabled=True,
    )
    return e


def test_synthetic_split_profiles_exist_and_have_unique_magic():
    expected = {"BOOM", "CRASH", "VOLATILITY", "STEP", "JUMP", "FLIP"}
    assert set(SYNTHETIC_SPLIT_PROFILES) == expected
    magics = [BOT_PROFILES[p]["magic"] for p in SYNTHETIC_SPLIT_PROFILES]
    assert len(magics) == len(set(magics))


def test_each_profile_has_exact_single_category():
    mapping = {
        "BOOM": ["boom"],
        "CRASH": ["crash"],
        "VOLATILITY": ["volatility"],
        "STEP": ["step"],
        "JUMP": ["jump"],
        "FLIP": ["flip"],
    }
    for profile, categories in mapping.items():
        assert BOT_PROFILES[profile]["categories"] == categories


def test_full_multi_bot_uses_split_synthetics_plus_forex_orb():
    assert "SYNTHETICS" not in FULL_MULTI_BOT_PROFILES
    assert "VOLATILITY" not in FULL_MULTI_BOT_PROFILES
    for profile in (
        "BOOM", "CRASH", *VOLATILITY_SHARD_PROFILES, "STEP", "JUMP", "FLIP",
        "FOREX_1", "FOREX_2", "FOREX_3", "FOREX_4", "ORB",
    ):
        assert profile in FULL_MULTI_BOT_PROFILES


def test_profile_symbol_matching_is_exclusive_for_main_families():
    e = _engine("BOOM", BOT_PROFILES["BOOM"]["magic"])
    assert e._symbol_matches_split_profile("Boom 1000 Index", "BOOM")
    assert not e._symbol_matches_split_profile("Crash 1000 Index", "BOOM")
    assert e._symbol_matches_split_profile("Crash 500 Index", "CRASH")
    assert e._symbol_matches_split_profile("Volatility 75 Index", "VOLATILITY")
    assert e._symbol_matches_split_profile("Step Index 400", "STEP")
    assert e._symbol_matches_split_profile("Jump 100 Index", "JUMP")


def test_legacy_synthetic_magic_is_adopted_only_by_matching_family():
    legacy_boom = {
        "instrument": "Boom 500 Index",
        "details": {"metadata": {"daemon_magic": 26082026}},
    }
    boom = _engine("BOOM", BOT_PROFILES["BOOM"]["magic"])
    crash = _engine("CRASH", BOT_PROFILES["CRASH"]["magic"])
    assert boom._trade_owned_by_current_bot(legacy_boom) is True
    assert crash._trade_owned_by_current_bot(legacy_boom) is False


def test_new_magic_trade_is_owned_only_by_exact_worker():
    trade = {
        "instrument": "Volatility 75 Index",
        "details": {"metadata": {"daemon_magic": BOT_PROFILES["VOLATILITY"]["magic"]}},
    }
    volatility = _engine("VOLATILITY", BOT_PROFILES["VOLATILITY"]["magic"])
    jump = _engine("JUMP", BOT_PROFILES["JUMP"]["magic"])
    assert volatility._trade_owned_by_current_bot(trade) is True
    assert jump._trade_owned_by_current_bot(trade) is False


def test_windows_launchers_exist():
    root = Path(__file__).resolve().parents[1]
    for name in (
        "run_boom_bot.bat",
        "run_crash_bot.bat",
        "run_volatility_bot.bat",
        "run_step_bot.bat",
        "run_jump_bot.bat",
        "run_flip_bot.bat",
        "run_synthetics_split.bat",
        "run_report_daemon.bat",
    ):
        assert (root / name).exists()
