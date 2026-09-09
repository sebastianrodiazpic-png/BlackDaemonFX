"""Tests de la estrategia standalone 'Apertura Índices Bursátiles' (NY 9:30).

Cubre: clasificación de mercado, sesgo H1 (07h vs 08h), confirmación M5 con
ventana de 20 minutos, cálculo de SL con spread, TP1/TP2 y break-even.
"""

from datetime import datetime, timezone

import pandas as pd
import pytest

from strategy.indices.ny_index_open import (
    NYIndexOpenConfig,
    NYIndexOpenStrategy,
    classify_ny_index_market,
    is_ny_index_open_symbol,
)


def test_classify_ny_index_market():
    assert classify_ny_index_market("Wall Street 30") == "WALL_STREET_30"
    assert classify_ny_index_market("US Tech 100") == "US_TECH_100"
    assert classify_ny_index_market("US500") == "US_500"
    assert classify_ny_index_market("XAUUSD") is None
    assert classify_ny_index_market("XAGUSD") is None


def test_is_ny_index_open_symbol():
    assert is_ny_index_open_symbol("Wall Street 30") is True
    assert is_ny_index_open_symbol("US Tech 100") is True
    assert is_ny_index_open_symbol("US500") is True
    assert is_ny_index_open_symbol("XAUUSD") is False
    assert is_ny_index_open_symbol("US Oil") is False


def _h1_candle(hour, open_, close, day="2024-01-08"):
    return {
        "time": pd.Timestamp(f"{day} {hour:02d}:00:00", tz="UTC"),
        "open": open_, "high": max(open_, close) + 1, "low": min(open_, close) - 1, "close": close,
    }


def _m5_candle(hour, minute, open_, close, day="2024-01-08"):
    return {
        "time": pd.Timestamp(f"{day} {hour:02d}:{minute:02d}:00", tz="UTC"),
        "open": open_, "high": max(open_, close) + 0.5, "low": min(open_, close) - 0.5, "close": close,
    }


class FakeProvider:
    """Data provider falso: H1 en horario NY = UTC-5 (sin DST, enero)."""

    def __init__(self, h1_rows, m5_rows, bid=6000.0, ask=6000.5):
        self.h1_df = pd.DataFrame(h1_rows)
        self.m5_df = pd.DataFrame(m5_rows)
        self.bid = bid
        self.ask = ask

    def get_candles(self, symbol, timeframe, count=500):
        return (self.h1_df if str(timeframe).upper() == "H1" else self.m5_df).copy()

    def get_current_tick(self, symbol):
        return {"symbol": symbol, "time": pd.Timestamp.utcnow(), "bid": self.bid, "ask": self.ask}


def _utc_hour_ny(hour_ny, minute_ny=0, day="2024-01-08"):
    # Enero: NY está en UTC-5 (sin horario de verano).
    return pd.Timestamp(f"{day} {hour_ny + 5:02d}:{minute_ny:02d}:00", tz="UTC")


def test_h1_bias_buy_when_8h_close_breaks_above_7h_body():
    h1_rows = [
        _h1_candle(12, 6000.0, 6005.0),  # 07:00 NY (12:00 UTC) cuerpo 6000-6005
        _h1_candle(13, 6005.0, 6010.0),  # 08:00 NY cierre 6010 > cuerpo 7h (6005) -> BUY
    ]
    m5_rows = [_m5_candle(14, 30, 6010.0, 6011.0)]  # 09:30 NY alcista -> confirma BUY
    m5_rows.append(_m5_candle(14, 35, 6011.0, 6012.0))
    provider = FakeProvider(h1_rows, m5_rows)
    strategy = NYIndexOpenStrategy(provider, NYIndexOpenConfig())

    now_utc = _utc_hour_ny(9, 40).to_pydatetime()
    result = strategy.analyze_symbol("US500", now_utc=now_utc)

    assert result["valid"] is True
    assert result["direction"] == "BUY"
    signal = result["signal"]
    assert signal["entry_price"] == 6011.0  # apertura de la vela M5 SIGUIENTE a la confirmación
    assert signal["stop_loss"] < signal["entry_price"]


def test_h1_bias_sell_when_8h_close_breaks_below_7h_body():
    h1_rows = [
        _h1_candle(12, 6005.0, 6000.0),  # 07:00 NY cuerpo 6000-6005
        _h1_candle(13, 6000.0, 5994.0),  # 08:00 NY cierre 5994 < cuerpo 7h (6000) -> SELL
    ]
    m5_rows = [_m5_candle(14, 30, 5994.0, 5993.0)]  # 09:30 NY bajista -> confirma SELL
    m5_rows.append(_m5_candle(14, 35, 5993.0, 5992.0))
    provider = FakeProvider(h1_rows, m5_rows)
    strategy = NYIndexOpenStrategy(provider, NYIndexOpenConfig())

    now_utc = _utc_hour_ny(9, 40).to_pydatetime()
    result = strategy.analyze_symbol("US500", now_utc=now_utc)

    assert result["valid"] is True
    assert result["direction"] == "SELL"
    signal = result["signal"]
    assert signal["entry_price"] == 5993.0
    assert signal["stop_loss"] > signal["entry_price"]


def test_no_bias_when_8h_close_stays_inside_7h_body():
    h1_rows = [
        _h1_candle(12, 6000.0, 6005.0),
        _h1_candle(13, 6001.0, 6002.0),  # cierre dentro del cuerpo 6000-6005
    ]
    provider = FakeProvider(h1_rows, [])
    strategy = NYIndexOpenStrategy(provider, NYIndexOpenConfig())

    now_utc = _utc_hour_ny(9, 40).to_pydatetime()
    result = strategy.analyze_symbol("US500", now_utc=now_utc)

    assert result["valid"] is False
    assert result["action"] == "NO_H1_BIAS"


def test_m5_confirmation_window_expires_after_20_minutes():
    h1_rows = [
        _h1_candle(12, 6000.0, 6005.0),
        _h1_candle(13, 6005.0, 6010.0),  # sesgo BUY
    ]
    # Ninguna vela M5 confirma BUY (todas bajistas) dentro de la ventana.
    m5_rows = [
        _m5_candle(14, 30, 6010.0, 6009.0),
        _m5_candle(14, 35, 6009.0, 6008.0),
        _m5_candle(14, 40, 6008.0, 6007.0),
        _m5_candle(14, 45, 6007.0, 6006.0),
    ]
    provider = FakeProvider(h1_rows, m5_rows)
    strategy = NYIndexOpenStrategy(provider, NYIndexOpenConfig())

    now_utc = _utc_hour_ny(9, 51).to_pydatetime()  # pasados los 20 minutos
    result = strategy.analyze_symbol("US500", now_utc=now_utc)

    assert result["valid"] is False
    assert result["action"] == "M5_CONFIRMATION_WINDOW_EXPIRED"


def test_stop_loss_points_are_instrument_specific_and_include_spread():
    config = NYIndexOpenConfig()
    assert config.stop_loss_points["WALL_STREET_30"] == 40.0
    assert config.stop_loss_points["US_TECH_100"] == 40.0
    assert config.stop_loss_points["US_500"] == 4.0

    h1_rows = [
        _h1_candle(12, 6000.0, 6005.0),
        _h1_candle(13, 6005.0, 6010.0),
    ]
    m5_rows = [_m5_candle(14, 30, 6010.0, 6011.0)]
    m5_rows.append(_m5_candle(14, 35, 6011.0, 6012.0))
    provider = FakeProvider(h1_rows, m5_rows, bid=6011.8, ask=6012.2)
    strategy = NYIndexOpenStrategy(provider, NYIndexOpenConfig())

    now_utc = _utc_hour_ny(9, 40).to_pydatetime()
    result = strategy.analyze_symbol("US500", now_utc=now_utc)
    signal = result["signal"]

    spread = 6012.2 - 6011.8
    assert signal["spread_points"] == pytest.approx(spread)
    assert signal["total_stop_points"] == pytest.approx(4.0 + spread)
    assert signal["stop_loss"] == pytest.approx(signal["entry_price"] - (4.0 + spread))


def test_tp1_1r_tp2_2r_and_break_even_includes_spread():
    h1_rows = [
        _h1_candle(12, 6000.0, 6005.0),
        _h1_candle(13, 6005.0, 6010.0),
    ]
    m5_rows = [_m5_candle(14, 30, 6010.0, 6011.0)]
    m5_rows.append(_m5_candle(14, 35, 6011.0, 6012.0))
    provider = FakeProvider(h1_rows, m5_rows, bid=6011.8, ask=6012.2)
    strategy = NYIndexOpenStrategy(provider, NYIndexOpenConfig())

    now_utc = _utc_hour_ny(9, 40).to_pydatetime()
    signal = strategy.analyze_symbol("US500", now_utc=now_utc)["signal"]

    risk = signal["entry_price"] - signal["stop_loss"]
    assert signal["take_profit_1"] == pytest.approx(signal["entry_price"] + risk * 1.0)
    assert signal["take_profit_2"] == pytest.approx(signal["entry_price"] + risk * 2.0)
    assert signal["break_even_price"] == pytest.approx(signal["entry_price"] + signal["spread_points"])


def test_analyze_symbol_does_not_consume_session_signal_by_itself():
    """v109: analizar dos veces la misma sesión NO debe bloquear la señal.

    Antes, `analyze_symbol` marcaba la sesión como "usada" apenas armaba la
    señal candidata, así que una segunda llamada (por ejemplo, porque el
    motor la descartó después en un gate posterior sin abrir operación)
    quedaba bloqueada con NY_INDEX_OPEN_SESSION_SIGNAL_LIMIT_REACHED aunque
    nunca se hubiera ejecutado ninguna entrada real.
    """
    h1_rows = [
        _h1_candle(12, 6000.0, 6005.0),
        _h1_candle(13, 6005.0, 6010.0),  # sesgo BUY
    ]
    m5_rows = [_m5_candle(14, 30, 6010.0, 6011.0)]
    m5_rows.append(_m5_candle(14, 35, 6011.0, 6012.0))
    provider = FakeProvider(h1_rows, m5_rows)
    strategy = NYIndexOpenStrategy(provider, NYIndexOpenConfig())

    now_utc = _utc_hour_ny(9, 40).to_pydatetime()

    first = strategy.analyze_symbol("US500", now_utc=now_utc)
    assert first["valid"] is True
    assert first["signal"]["ny_index_session_date"] == first["session_date_ny"]

    # Sin llamar a mark_signal_used, una segunda evaluación de la misma
    # sesión debe seguir devolviendo la señal, no el límite de sesión.
    second = strategy.analyze_symbol("US500", now_utc=now_utc)
    assert second["valid"] is True
    assert second["action"] == "NY_INDEX_OPEN_SIGNAL_CONFIRMED"

    # Solo tras marcarla explícitamente (equivalente a que el motor confirmó
    # que la señal superó todos los gates posteriores) se bloquea el resto
    # de la sesión.
    strategy.mark_signal_used("US500", first["session_date_ny"])
    third = strategy.analyze_symbol("US500", now_utc=now_utc)
    assert third["valid"] is False
    assert third["action"] == "NY_INDEX_OPEN_SESSION_SIGNAL_LIMIT_REACHED"
    assert third["reason"] == "YA_SE_UTILIZO_LA_SEÑAL_DE_ESTA_SESION"

