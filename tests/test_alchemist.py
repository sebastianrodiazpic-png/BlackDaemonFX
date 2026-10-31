"""Alchemist MSNR (pre-registro 26-oct-2026): reglas causales, setups y simulación fiel."""
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from strategy.alchemist import AlchemistConfig, AlchemistStrategy
from strategy.alchemist.rules import arrays, build_levels, close_pivots, structure_trend, value_at
from strategy.alchemist.simulation import manage_trade, next_force_flat_ns, run_order


def ohlc(closes, start="2026-01-05 00:00", freq="15min", wick=0.05):
    closes = np.asarray(closes, float)
    opens = np.concatenate(([closes[0]], closes[:-1]))
    return pd.DataFrame({"time": pd.date_range(start, periods=len(closes), freq=freq, tz="UTC"), "open": opens,
                         "high": np.maximum(opens, closes) + wick, "low": np.minimum(opens, closes) - wick,
                         "close": closes})


def resample(m15, rule):
    g = m15.set_index("time").resample(rule, label="left", closed="left")
    df = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(),
                       "close": g["close"].last()}).dropna().reset_index()
    return df


def random_frames(n=6000, seed=3):
    rng = np.random.default_rng(seed)
    closes = 100 + np.cumsum(rng.normal(0, 0.25, n))
    m15 = ohlc(closes, start="2025-01-06 00:00")
    return {"M15": m15, "H1": resample(m15, "1h"), "H4": resample(m15, "4h"), "D1": resample(m15, "1D")}


# ----------------------------------------------------------------------------- reglas
def test_close_pivots_strict_and_confirmed_k_bars_later():
    closes = np.array([1, 2, 3, 2, 1, 2, 2, 3, 2, 1.0])
    assert close_pivots(closes, 2) == [(2, "H"), (4, "L"), (7, "H")]  # el empate 2,2 (5 y 6) no es pivote
    assert close_pivots(closes[:4], 2) == []  # sin las 2 velas posteriores no se confirma


def test_level_third_touch_discards_and_strong_break_flips_role():
    cfg = AlchemistConfig(level_pivot_k={"D1": 3, "H4": 3, "H1": 1}, level_zone_atr=0.2)
    # Cresta en 10 (A); vuelve a la zona tras salir de ella tres veces: el 3.er toque lo descarta.
    closes = [9, 10, 9, 8, 9.95, 8, 7.5, 9.95, 8, 7.5, 9.95, 8, 7.5]
    a = arrays(ohlc(closes, freq="1h", wick=0.01), "H1")
    level = next(lv for lv in build_levels(a, "H1", cfg) if lv.kind == "A" and lv.price == 10)
    touches = [e for e in level.events if e[2] > 0]
    assert [e[2] for e in touches] == [1, 2, 3] and touches[-1][3] is False
    assert level.state_at(touches[1][0]) == ("R", 2) and level.state_at(touches[2][0]) is None
    # Ruptura fuerte (cuerpo grande, > 0,5 ATR): pasa a soporte con 0 toques.
    a = arrays(ohlc([9, 10, 9, 8, 12, 12.5, 13], freq="1h", wick=0.01), "H1")
    level = next(lv for lv in build_levels(a, "H1", cfg) if lv.kind == "A" and lv.price == 10)
    assert level.events[1][1:] == ("S", 0, True)


def test_structure_trend_follows_breaks_of_confirmed_pivots():
    a = arrays(ohlc([5, 6, 5, 4, 5, 6, 7, 6, 5, 3], freq="1h"), "H1")
    times, values = structure_trend(a, 1)
    assert values[:2] == ["up", "down"]
    assert value_at(times, values, times[0] - 1) is None


def test_setups_are_causal_on_truncated_history():
    """Calcular con todo el histórico y filtrar por la señal = calcular solo con las velas cerradas hasta entonces."""
    frames = random_frames()
    strategy = AlchemistStrategy()
    full = strategy.setups(frames)
    assert full, "el paseo aleatorio debe generar algún QM"
    cut = frames["M15"]["time"].iloc[4500] + pd.Timedelta(minutes=15)
    truncated = {tf: df[df["time"] + pd.Timedelta(minutes={"M15": 15, "H1": 60, "H4": 240, "D1": 1440}[tf]) <= cut]
                 for tf, df in frames.items()}
    part = strategy.setups(truncated)
    key = lambda s: (s.direction, s.kind, s.shoulder_idx, s.head_idx, s.signal_idx, round(s.stop_loss, 9),
                     s.turtle_soup, s.inducement, s.level_tf)
    assert [key(s) for s in full if s.signal_ns <= cut.value] == [key(s) for s in part]
    for s in full:
        assert s.signal_idx >= s.head_idx + strategy.config.m15_pivot_k
        assert (s.direction == "SELL") == (s.stop_loss > s.shoulder)


# ----------------------------------------------------------------------------- simulación
def fake_market(highs, lows, opens=None, spread=0.0, start="2026-01-06 08:00", **cfg):
    highs, lows = np.asarray(highs, float), np.asarray(lows, float)
    opens = np.asarray(opens if opens is not None else (highs + lows) / 2, float)
    times = pd.date_range(start, periods=len(highs), freq="15min", tz="UTC")
    open_ns = times.to_numpy(dtype="datetime64[ns]").astype("int64")
    m = {"open": opens, "high": highs, "low": lows, "close": (highs + lows) / 2,
         "open_ns": open_ns, "close_ns": open_ns + 15 * 60 * 10**9}
    config = AlchemistConfig(**cfg)
    mk = SimpleNamespace(m=m, cfg=config, spread=spread, pip=0.0001, is_fx=True,
                         hours=times.hour.to_numpy(), close_hours=(times + pd.Timedelta(minutes=15)).hour.to_numpy(),
                         ctx={}, strategy=SimpleNamespace(target=lambda ctx, d, e, t: mk.target_price,
                                                          h1_atr_at=lambda ctx, t: 1.0))
    mk.in_session = lambda hour: config.session_start_utc <= hour < config.session_end_utc
    mk.target_price = None
    return mk


def test_manage_sl_wins_ties_and_only_sl_counts_on_fill_bar():
    mk = fake_market(highs=[1.0010, 1.0030, 1.0100], lows=[0.9990, 0.9950, 0.9990])
    # Compra en 1.0000, SL 0.9990, objetivo 1.0050: la vela 1 toca ambos → SL.
    assert manage_trade(mk, "BUY", 1.0, 0.9990, 1.0050, 0, "A")[:2] == (-1.0, "SL")
    mk = fake_market(highs=[1.0060, 1.0060], lows=[0.9995, 0.9995])
    rr, outcome, idx = manage_trade(mk, "BUY", 1.0, 0.9990, 1.0050, 0, "A")
    assert (round(rr, 6), outcome, idx) == (5.0, "TP", 1)  # el objetivo no cuenta en la vela del llenado


def test_manage_exit_a_breakeven_and_exit_b_partial():
    highs, lows = [1.0005, 1.0025, 1.0035, 1.0010], [0.9995, 1.0000, 1.0005, 0.9995]
    mk = fake_market(highs, lows)
    assert manage_trade(mk, "BUY", 1.0, 0.9990, 1.0100, 0, "A")[:2] == (0.0, "BE")  # +2R → BE → vuelve a la entrada
    rr, outcome, _ = manage_trade(mk, "BUY", 1.0, 0.9990, 1.0100, 0, "B")
    assert (round(rr, 6), outcome) == (1.5, "BE")  # 50 % en 3R + resto en BE


def test_manage_sell_uses_ask_and_force_flat_at_1645_ny():
    # Venta en 1.0000 con spread 0.0002: el ask (alto + spread) toca el SL 1.0010 aunque el bid llegue a 1.0009.
    mk = fake_market(highs=[1.0000, 1.0009], lows=[0.9995, 0.9995], spread=0.0002)
    assert manage_trade(mk, "SELL", 1.0, 1.0010, 0.9950, 0, "A")[1] == "SL"
    # 16:45 NY de un martes de enero = 21:45 UTC: se cierra en la apertura de esa vela.
    mk = fake_market(highs=[1.0005] * 10, lows=[0.9995] * 10, start="2026-01-06 19:45")
    rr, outcome, idx = manage_trade(mk, "BUY", 1.0, 0.9990, 1.0100, 0, "A")
    assert outcome == "FORCE_FLAT" and idx == 8


def test_next_force_flat_handles_dst():
    summer = pd.Timestamp("2026-07-01 12:00", tz="UTC").value
    assert pd.Timestamp(next_force_flat_ns(summer), tz="UTC") == pd.Timestamp("2026-07-01 20:45", tz="UTC")
    winter_late = pd.Timestamp("2026-01-06 22:00", tz="UTC").value
    assert pd.Timestamp(next_force_flat_ns(winter_late), tz="UTC") == pd.Timestamp("2026-01-07 21:45", tz="UTC")


def test_run_order_filters_and_limit_fill():
    mk = fake_market(highs=[1.0000, 1.0004, 1.0012, 1.0002], lows=[0.9990, 0.9995, 1.0001, 0.9900])
    sell = dict(direction="SELL", entry=1.0010, sl=1.0020, signal_idx=0, cancel_level=1.0020, valid_bars=16,
                exit_mode="A")
    mk.target_price = None
    assert run_order(mk, **sell)["skip"] == "SIN_OBJETIVO"
    mk.target_price = 0.9990  # 2R < 5R
    assert run_order(mk, **sell)["skip"] == "OBJETIVO_MENOR_5R"
    mk.target_price = 0.9950  # 6R
    res = run_order(mk, **sell)
    assert res["fill_idx"] == 2 and res["outcome"] == "TP" and round(res["rr"], 6) == 6.0
    assert run_order(mk, **{**sell, "entry": 0.9990})["skip"] == "LIMITE_DEL_LADO_EQUIVOCADO"
    assert run_order(mk, **{**sell, "sl": 1.0400})["skip"] == "SL_DEMASIADO_GRANDE"  # > 30 pips
    # Cancelación: un cierre por encima de la cabeza antes del llenado.
    mk2 = fake_market(highs=[1.0000, 1.0008, 1.0030], lows=[0.9990, 1.0006, 1.0021])
    mk2.target_price = 0.9950
    assert run_order(mk2, **{**sell, "cancel_level": 1.0005})["skip"] == "NO_LLENADA"


def test_run_order_rejects_spread_and_session():
    mk = fake_market(highs=[1.0000, 1.0012], lows=[0.9990, 1.0001], spread=0.0001)
    mk.target_price = 0.9900
    order = dict(direction="SELL", entry=1.0010, sl=1.0020, signal_idx=0, cancel_level=1.0020, valid_bars=16,
                 exit_mode="A")
    assert run_order(mk, **order)["skip"] == "SPREAD_SL"  # 1 pip de spread / 10 pips de SL = 10 % > 5 %
    night = fake_market(highs=[1.0000, 1.0012], lows=[0.9990, 1.0001], start="2026-01-06 03:00")
    night.target_price = 0.9900
    assert run_order(night, **order)["skip"] == "FUERA_DE_SESION"


def test_replay_tool_defaults_match_preregistration():
    import tools.replay_alchemist as replay
    assert replay.PRIMARY == ("shoulder", True, "A") and len(replay.VARIANTS) == 12
    assert replay.UNIVERSE == ("EURUSD", "GBPUSD", "USDJPY", "USDCHF", "USDCAD", "AUDUSD", "NZDUSD", "XAUUSD")
    assert [p[0] for p in replay.PERIODS] == ["D", "A", "B"]
    cfg = AlchemistConfig()
    assert (cfg.min_target_r, cfg.max_touches, cfg.max_sl_pips_fx, cfg.max_spread_sl_ratio) == (5.0, 2, 30.0, 0.05)
    df = pd.DataFrame({"variant": ["shoulder|conf|A"] * 3, "period": ["D", "A", "B"], "rr": [5.0, -1.0, -1.0],
                       "symbol": "EURUSD", "kind": "QML", "outcome": ["TP", "SL", "SL"]})
    text, verdict = replay.summary(df, np.zeros(10), 3)
    assert verdict.startswith("NO CONCLUYENTE") and "Variante principal" in text
