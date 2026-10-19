"""ORB SWEEP (orb-ny-v5-sweep): paridad exacta con el replay 2Y de XAUUSD.

El modo en vivo debe reproducir señal a señal la variante SWEEP de
tools/replay_orb_nunez_2y.py (misma hora, dirección y stop estructural).
Se omite si el histórico M5 o el CSV del replay no están disponibles.
"""
import json
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "storage" / "analysis" / "orb_nunez_2y"


def test_xauusd_profile_is_sweep_only():
    from strategy.orb.asset_rules import ASSET_CONFIG, ORB_SWEEP_STRATEGY_VERSION
    assert ASSET_CONFIG["XAUUSD"]["sweep_enabled"] is True
    assert ASSET_CONFIG["XAUUSD"]["allowed_modes"] == []
    assert ORB_SWEEP_STRATEGY_VERSION == "orb-ny-v5-sweep"
    for key, profile in ASSET_CONFIG.items():
        if key != "XAUUSD":
            assert profile["allowed_modes"] == [] and not profile.get("sweep_enabled")


@pytest.mark.skipif(not (OUT / "history" / "XAUUSD_M5.csv").exists() or not (OUT / "trades.csv").exists(),
                    reason="histórico del replay no disponible")
def test_sweep_matches_replay_signal_by_signal_first_sessions():
    import tools.replay_orb_nunez_2y as R
    import strategy.orb.new_york_orb as orb
    df, _ = R.load("XAUUSD")
    point = json.loads((R.OUT / "fetch_audit.json").read_text())["XAUUSD"]["point"]
    provider = R.Provider(df, point)
    strategy = R.ReplayStrategy(provider, orb.ORBConfig(target_rr=2.0, break_even_enabled=True))
    days = [d for d, _ in df.groupby(df.ny_date, sort=True)
            if d.weekday() < 5 and pd.Timestamp(d, tz="UTC") >= R.START][:120]
    live = []
    for day in days:
        group = df[df.ny_date == day]
        minutes = group.ny_minute
        if len(group[(minutes >= 570) & (minutes < 585)]) != 3:
            continue
        for idx in group[(minutes >= 585) & (minutes < 955)].index:
            provider.index = idx
            now = df.time.iloc[idx] + pd.Timedelta(minutes=5)
            result = strategy.analyze_symbol("XAUUSD", now)
            if result.get("valid"):
                signal = result["signal"]
                assert signal["orb_entry_mode"] == "ORB_SWEEP_MSS"
                assert signal["strategy_version"] == "orb-ny-v5-sweep"
                live.append((str(now)[:19], signal["direction"], round(signal["stop_loss"], 6)))
                strategy.mark_signal_used("XAUUSD", signal["orb_session_date"], signal["breakout_candle_time"])
                break
            if result.get("action") in ("ORB_SESSION_CANCELLED", "WAITING_ORB_ATR", "ORB_SWEEP_WINDOW_CLOSED"):
                break
    replay = pd.read_csv(OUT / "trades.csv")
    replay = replay[(replay.variant == "SWEEP") & (replay.symbol == "XAUUSD")]
    last = pd.Timestamp(days[-1], tz="America/New_York") + pd.Timedelta(days=1)
    replay = replay[pd.to_datetime(replay.signal_time, utc=True) < last]
    expected = sorted((str(r.signal_time)[:19], r.direction, round(r.stop_loss, 6)) for r in replay.itertuples())
    assert live, "se esperaban señales SWEEP en el periodo"
    assert sorted(live) == expected
