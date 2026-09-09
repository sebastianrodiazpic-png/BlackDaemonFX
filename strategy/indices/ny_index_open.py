"""Estrategia "Apertura Índices Bursátiles" (Wall Street 30 / US Tech 100 / US SP 500).

Estrategia INDEPENDIENTE del pipeline SMC y del ORB clásico: no usa order
blocks, VWAP ni POC. Se apoya en dos temporalidades:

1. H1 — sesgo direccional: compara el CUERPO de la vela de las 08:00 NY
   contra el cuerpo de la vela de las 07:00 NY.
   - Si el cierre de la vela de las 08:00 supera el cuerpo completo de la
     vela de las 07:00 (close_8h > max(open_7h, close_7h)) el sesgo es COMPRA.
   - Si el cierre de la vela de las 08:00 queda por debajo del cuerpo
     completo de la vela de las 07:00 (close_8h < min(open_7h, close_7h)) el
     sesgo es VENTA.
   - Cualquier otro caso (el cierre de las 08:00 queda dentro del cuerpo de
     las 07:00) no define sesgo: no hay operación posible ese día.

2. M5 — confirmación de entrada, desde la apertura de Nueva York (09:30 NY)
   hasta 20 minutos después (09:50 NY): se espera que alguna de las velas M5
   cierre alineada con el sesgo H1 (alcista si el sesgo es compra, bajista si
   es venta). En cuanto una vela M5 confirma, la entrada se ejecuta a
   mercado en la apertura de la SIGUIENTE vela M5.

Gestión de riesgo: dos entradas parciales al 0.5% de riesgo cada una
(1% total). El SL en puntos es fijo por instrumento (configurable), con el
spread actual sumado para no ser barrido por el spread. La primera entrada
cierra en 1:1; la segunda busca 1:2 y su stop se mueve a break-even (precio
de entrada + spread) en cuanto el precio alcanza el 1:1.

Vinculaciones:
- La orquesta `strategy.execution.live_trading_engine`, que la invoca para
  los símbolos elegibles (ver `is_ny_index_open_symbol`).
- Depende de un `data_provider` con `get_candles` y `get_current_tick`,
  normalmente el proveedor MT5 de `brokers/`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from zoneinfo import ZoneInfo
import re

import pandas as pd

from strategy.orb.new_york_orb import classify_orb_market, is_orb_index_symbol


NEW_YORK = ZoneInfo("America/New_York")


def _norm_symbol(symbol: str) -> str:
    """Reduce el símbolo a minúsculas y sólo caracteres alfanuméricos."""
    return re.sub(r"[^a-z0-9]", "", str(symbol or "").lower())


def classify_ny_index_market(symbol: str) -> str | None:
    """Clasifica los tres índices autorizados para esta estrategia.

    Reutiliza la clasificación ya existente de `strategy.orb.new_york_orb`
    (mismos alias de broker), restringida a los tres índices US.

    Returns:
        `WALL_STREET_30`, `US_TECH_100`, `US_500`, o `None`.
    """
    market = classify_orb_market(symbol)
    if market in {"WALL_STREET_30", "US_TECH_100", "US_500"}:
        return market
    return None


def is_ny_index_open_symbol(symbol: str) -> bool:
    """True para los tres índices autorizados por esta estrategia."""
    return classify_ny_index_market(symbol) is not None


# Puntos de SL fijos por instrumento (antes de sumar el spread), definidos
# explícitamente por el usuario: Wall Street 30 y US Tech 100 = 40 puntos,
# US SP 500 = 4 puntos (ajustado por el usuario tras revisar la escala del
# instrumento; el spread se sigue sumando igual que en el resto).
DEFAULT_STOP_LOSS_POINTS = {
    "WALL_STREET_30": 40.0,
    "US_TECH_100": 40.0,
    "US_500": 4.0,
}


@dataclass
class NYIndexOpenConfig:
    """Parámetros de sesión, sesgo H1 y gestión de riesgo de la estrategia.

    `h1_bias_hour`/`h1_confirmation_hour`: horas NY de las velas H1 que se
    comparan para fijar el sesgo diario (por defecto 07:00 y 08:00 NY).

    `m5_confirmation_window_minutes`: ventana, desde la apertura de NY, en la
    que se admite una vela M5 de confirmación (por defecto 20 minutos, es
    decir hasta las 09:50 NY, aunque el enunciado original hable de "la
    primera, segunda o tercera vela" — se amplió a una ventana de tiempo
    para seguir esperando confirmación sin límite de velas).

    `stop_loss_points`: puntos de SL por mercado ORB antes de sumar spread.
    `target_rr`: relación riesgo:beneficio buscada por la segunda entrada
    (target 1:2); la primera entrada siempre cierra en 1:1.
    `risk_percent_total`/`split_entry_risk_fraction`: 1% total repartido en
    dos entradas de 0.5% cada una.
    """

    enabled: bool = True
    timezone_name: str = "America/New_York"
    h1_bias_hour: int = 7
    h1_confirmation_hour: int = 8
    opening_hour: int = 9
    opening_minute: int = 30
    m5_confirmation_window_minutes: int = 20
    h1_timeframe: str = "H1"
    m5_timeframe: str = "M5"
    candle_count: int = 500
    stop_loss_points: dict = None  # se rellena en __post_init__
    target_rr: float = 2.0
    tp1_rr: float = 1.0
    risk_percent_total: float = 1.0
    split_entry_risk_fraction: float = 0.5
    one_signal_per_session: bool = True

    def __post_init__(self):
        if self.stop_loss_points is None:
            self.stop_loss_points = dict(DEFAULT_STOP_LOSS_POINTS)


class NYIndexOpenStrategy:
    """Apertura de índices US: sesgo H1 (07h vs 08h) + confirmación M5.

    - Sesgo: cuerpo de la vela 08:00 NY vs cuerpo de la vela 07:00 NY.
    - Confirmación: primera vela M5, desde la apertura (09:30 NY) y durante
      `m5_confirmation_window_minutes`, que cierre alineada con el sesgo.
    - Entrada: apertura de la vela M5 siguiente a la de confirmación.
    - Riesgo: SL fijo en puntos por instrumento + spread; dos entradas al
      0.5% (1:1 y 1:2 con break-even + spread tras alcanzar el 1:1).
    """

    def __init__(self, data_provider, config: NYIndexOpenConfig | None = None):
        self.data_provider = data_provider
        self.config = config or NYIndexOpenConfig()
        self.tz = ZoneInfo(self.config.timezone_name)
        # Memoria de "una señal por sesión", igual criterio que el ORB clásico.
        self._session_signal_memory: dict[str, str] = {}

    def _session_bounds(self, now_utc: datetime):
        now_utc = pd.Timestamp(now_utc)
        if now_utc.tzinfo is None:
            now_utc = now_utc.tz_localize("UTC")
        else:
            now_utc = now_utc.tz_convert("UTC")
        now_ny = now_utc.tz_convert(self.tz)
        d = now_ny.date()
        bias_hour_start = pd.Timestamp(datetime.combine(d, time(self.config.h1_bias_hour, 0)), tz=self.tz)
        confirmation_hour_start = pd.Timestamp(datetime.combine(d, time(self.config.h1_confirmation_hour, 0)), tz=self.tz)
        open_ny = pd.Timestamp(datetime.combine(d, time(self.config.opening_hour, self.config.opening_minute)), tz=self.tz)
        confirmation_deadline_ny = open_ny + pd.Timedelta(minutes=int(self.config.m5_confirmation_window_minutes))
        return now_ny, bias_hour_start, confirmation_hour_start, open_ny, confirmation_deadline_ny

    def _prepare_candles(self, symbol: str, timeframe: str, now_utc: datetime) -> pd.DataFrame:
        """Descarga velas y filtra sólo las ya cerradas al instante `now_utc`."""
        df = self.data_provider.get_candles(
            symbol, timeframe, count=int(self.config.candle_count)
        ).copy()
        if "time" not in df.columns:
            raise ValueError(f"NY_INDEX_OPEN requiere columna time en las velas {timeframe}")
        df["time"] = pd.to_datetime(df["time"], utc=True)
        tf = str(timeframe or "M5").upper()
        timeframe_minutes = 60 if tf == "H1" else 5
        now_ts = pd.Timestamp(now_utc)
        if now_ts.tzinfo is None:
            now_ts = now_ts.tz_localize("UTC")
        else:
            now_ts = now_ts.tz_convert("UTC")
        df = df[(df["time"] + pd.Timedelta(minutes=timeframe_minutes)) <= now_ts].copy()
        df["time_ny"] = df["time"].dt.tz_convert(self.tz)
        return df.sort_values("time").reset_index(drop=True)

    @staticmethod
    def _h1_bias(bias_candle: pd.Series, confirmation_candle: pd.Series) -> str | None:
        """Determina el sesgo comparando cuerpos de las velas 07h y 08h NY.

        Returns:
            `BUY` si el cierre de la vela de confirmación supera el cuerpo
            completo de la vela de sesgo; `SELL` si queda por debajo;
            `None` si el cierre queda dentro del cuerpo (sin sesgo claro).
        """
        bias_body_high = max(float(bias_candle["open"]), float(bias_candle["close"]))
        bias_body_low = min(float(bias_candle["open"]), float(bias_candle["close"]))
        confirmation_close = float(confirmation_candle["close"])
        if confirmation_close > bias_body_high:
            return "BUY"
        if confirmation_close < bias_body_low:
            return "SELL"
        return None

    def mark_signal_used(self, symbol: str, session_date_str: str) -> None:
        """Registra que la señal de esta sesión ya fue aprovechada.

        v109: se invoca desde `live_trading_engine` solo DESPUÉS de que la
        señal supere todos los gates posteriores a `analyze_symbol` (política
        de dirección, filtro estricto Jump si aplica, R:R mínimo y
        meta-labeling). Antes se marcaba dentro de `analyze_symbol` en cuanto
        se armaba la señal candidata, lo que bloqueaba el resto de la sesión
        aunque esa señal fuera descartada después sin abrir operación.
        """
        if bool(self.config.one_signal_per_session):
            self._session_signal_memory[str(symbol)] = str(session_date_str)

    def analyze_symbol(self, symbol: str, now_utc: datetime | None = None) -> dict:
        """Evalúa un símbolo y devuelve la señal, válida o no.

        SIEMPRE devuelve un dict, nunca lanza por falta de señal: cuando no
        hay entrada, `valid` es `False` y `action`/`reason` explican en qué
        paso se detuvo.
        """
        market = classify_ny_index_market(symbol)
        if not bool(self.config.enabled) or market is None:
            return {
                "valid": False,
                "strategy_name": "NY_INDEX_OPEN",
                "action": "SYMBOL_NOT_NY_INDEX_OPEN_ELIGIBLE",
                "reason": "NY_INDEX_OPEN_SOLO_WALL_STREET_30_US_TECH_100_US500",
                "symbol": symbol,
            }

        if now_utc is None:
            tick = self.data_provider.get_current_tick(symbol)
            now_utc = pd.Timestamp(tick["time"]).to_pydatetime()
        now_ny, bias_hour_start, confirmation_hour_start, open_ny, confirmation_deadline_ny = (
            self._session_bounds(now_utc)
        )

        base = {
            "valid": False,
            "strategy_name": "NY_INDEX_OPEN",
            "strategy_version": "ny-index-open-v1-h1-bias-m5-confirmation",
            "symbol": symbol,
            "ny_index_market": market,
            "timezone": self.config.timezone_name,
            "session_date_ny": str(now_ny.date()),
            "h1_bias_candle_ny": bias_hour_start.isoformat(),
            "h1_confirmation_candle_ny": confirmation_hour_start.isoformat(),
            "session_open_ny": open_ny.isoformat(),
            "m5_confirmation_deadline_ny": confirmation_deadline_ny.isoformat(),
        }

        if now_ny.weekday() >= 5:
            return {**base, "action": "NO_SESSION", "reason": "FIN_DE_SEMANA_NEW_YORK"}

        h1_df = self._prepare_candles(symbol, self.config.h1_timeframe, now_utc)
        h1_session = h1_df[h1_df["time_ny"].dt.date == now_ny.date()]
        bias_candle_rows = h1_session[h1_session["time_ny"].dt.hour == int(self.config.h1_bias_hour)]
        confirmation_candle_rows = h1_session[
            h1_session["time_ny"].dt.hour == int(self.config.h1_confirmation_hour)
        ]

        if bias_candle_rows.empty or confirmation_candle_rows.empty:
            return {
                **base,
                "action": "WAITING_H1_BIAS_CANDLES",
                "reason": "ESPERANDO_CIERRE_VELAS_H1_07_Y_08_NEW_YORK",
            }

        bias_candle = bias_candle_rows.iloc[-1]
        confirmation_candle = confirmation_candle_rows.iloc[-1]
        h1_bias = self._h1_bias(bias_candle, confirmation_candle)

        diagnostics = {
            "h1_bias_open": float(bias_candle["open"]),
            "h1_bias_close": float(bias_candle["close"]),
            "h1_confirmation_open": float(confirmation_candle["open"]),
            "h1_confirmation_close": float(confirmation_candle["close"]),
            "h1_bias_body_high": max(float(bias_candle["open"]), float(bias_candle["close"])),
            "h1_bias_body_low": min(float(bias_candle["open"]), float(bias_candle["close"])),
            "h1_bias": h1_bias,
        }

        if h1_bias is None:
            return {
                **base,
                **diagnostics,
                "action": "NO_H1_BIAS",
                "reason": "CIERRE_08H_DENTRO_DEL_CUERPO_DE_LA_VELA_07H_SIN_SESGO",
            }

        if now_ny < open_ny:
            return {
                **base,
                **diagnostics,
                "action": "WAITING_NEW_YORK_OPEN",
                "reason": "ANTES_DE_LA_APERTURA_NEW_YORK",
            }

        m5_df = self._prepare_candles(symbol, self.config.m5_timeframe, now_utc)
        window = m5_df[
            (m5_df["time_ny"] >= open_ny) & (m5_df["time_ny"] < confirmation_deadline_ny)
        ].copy()

        if window.empty:
            return {
                **base,
                **diagnostics,
                "action": "WAITING_M5_CONFIRMATION",
                "reason": "ESPERANDO_PRIMERA_VELA_M5_CERRADA_POST_APERTURA",
            }

        confirmation_row = None
        for _, row in window.iterrows():
            candle_bullish = float(row["close"]) > float(row["open"])
            candle_bearish = float(row["close"]) < float(row["open"])
            if h1_bias == "BUY" and candle_bullish:
                confirmation_row = row
                break
            if h1_bias == "SELL" and candle_bearish:
                confirmation_row = row
                break

        if confirmation_row is None:
            if now_ny >= confirmation_deadline_ny:
                return {
                    **base,
                    **diagnostics,
                    "action": "M5_CONFIRMATION_WINDOW_EXPIRED",
                    "reason": "NINGUNA_VELA_M5_CONFIRMO_SESGO_H1_EN_20_MINUTOS",
                }
            return {
                **base,
                **diagnostics,
                "action": "WAITING_M5_CONFIRMATION",
                "reason": "ESPERANDO_VELA_M5_ALINEADA_CON_SESGO_H1",
            }

        # Entrada = apertura de la vela M5 SIGUIENTE a la que confirmó.
        confirmation_time = pd.Timestamp(confirmation_row["time"])
        next_candles = m5_df[m5_df["time"] > confirmation_time]
        if next_candles.empty:
            return {
                **base,
                **diagnostics,
                "action": "WAITING_NEXT_M5_CANDLE_FOR_ENTRY",
                "reason": "CONFIRMACION_M5_LISTA_ESPERANDO_VELA_DE_ENTRADA",
                "m5_confirmation_candle_time_ny": pd.Timestamp(confirmation_row["time_ny"]).isoformat(),
            }

        entry_candle = next_candles.iloc[0]
        entry_price = float(entry_candle["open"])
        direction = h1_bias

        session_date_str = str(now_ny.date())
        if bool(self.config.one_signal_per_session):
            remembered = self._session_signal_memory.get(str(symbol))
            if remembered == session_date_str:
                return {
                    **base,
                    **diagnostics,
                    "direction": direction,
                    "action": "NY_INDEX_OPEN_SESSION_SIGNAL_LIMIT_REACHED",
                    "reason": "YA_SE_UTILIZO_LA_SEÑAL_DE_ESTA_SESION",
                }

        stop_points = float(
            (self.config.stop_loss_points or {}).get(market, DEFAULT_STOP_LOSS_POINTS.get(market, 40.0))
        )
        tick = self.data_provider.get_current_tick(symbol)
        spread_points = abs(float(tick["ask"]) - float(tick["bid"]))
        total_stop_points = stop_points + spread_points

        stop_loss = (
            entry_price - total_stop_points if direction == "BUY" else entry_price + total_stop_points
        )
        risk_distance = abs(entry_price - stop_loss)
        if risk_distance <= 0:
            return {**base, **diagnostics, "action": "INVALID_STOP", "reason": "DISTANCIA_DE_RIESGO_INVALIDA"}

        tp1_rr = max(0.1, float(self.config.tp1_rr))
        target_rr = max(0.1, float(self.config.target_rr))
        take_profit_1 = (
            entry_price + risk_distance * tp1_rr if direction == "BUY" else entry_price - risk_distance * tp1_rr
        )
        take_profit_2 = (
            entry_price + risk_distance * target_rr if direction == "BUY" else entry_price - risk_distance * target_rr
        )
        # Break-even de la segunda entrada: precio de entrada + spread (a
        # favor de la dirección) para no perder por el costo del spread al
        # cerrarse en BE. Se activa cuando el precio alcanza el TP1 (1:1).
        break_even_price = (
            entry_price + spread_points if direction == "BUY" else entry_price - spread_points
        )

        # v109: el marcado de "señal usada" se movió fuera de este metodo
        # (ver `mark_signal_used`) para que el motor lo invoque solo tras
        # confirmar que la señal supero TODOS los gates posteriores
        # (direccion, jump, R:R, meta-label). Antes se marcaba aqui mismo, lo
        # que bloqueaba reintentos el resto de la sesion aunque la señal
        # fuera descartada despues sin haber abierto ninguna operacion.
        confirmations = {
            "h1_bias_defined": True,
            "new_york_session_open": True,
            "m5_confirmation_aligned_with_h1_bias": True,
            "eligible_market": True,
        }
        percentage = 100.0

        signal = {
            "strategy_name": "NY_INDEX_OPEN",
            "strategy_version": "ny-index-open-v1-h1-bias-m5-confirmation",
            "timeframe": "M5",
            "valid": True,
            "direction": direction,
            "entry_time": pd.Timestamp(entry_candle["time"]).to_pydatetime(),
            "entry_price": entry_price,
            "stop_loss": float(stop_loss),
            "stop_loss_points": stop_points,
            "spread_points": spread_points,
            "total_stop_points": total_stop_points,
            "take_profit": float(take_profit_2),
            "take_profit_1": float(take_profit_1),
            "take_profit_2": float(take_profit_2),
            "break_even_price": float(break_even_price),
            "risk_reward_ratio": target_rr,
            "tp1_risk_reward_ratio": tp1_rr,
            "confirmation_ok": True,
            "confirmation_decision": "NY_INDEX_OPEN_H1_BIAS_M5_CONFIRMED",
            "confirmation_percentage": percentage,
            "confirmations_passed": len(confirmations),
            "confirmations_total": len(confirmations),
            "passed_confirmations": list(confirmations.keys()),
            "missing_confirmations": [],
            "critical_confirmations_ok": True,
            "critical_confirmation_failures": [],
            "rejection_reasons": [],
            "confirmations": confirmations,
            "trade_score": percentage,
            "trade_grade": "A",
            "ny_index_market": market,
            "ny_index_session_date": session_date_str,
            "h1_bias": h1_bias,
            "m5_confirmation_candle_time_ny": pd.Timestamp(confirmation_row["time_ny"]).isoformat(),
            "entry_candle_time_ny": pd.Timestamp(entry_candle["time_ny"]).isoformat(),
            "risk_model": "1_PERCENT_TOTAL_SPLIT_0_5_TP1_1R_0_5_TP2_2R_BE_AFTER_TP1",
        }

        return {
            **base,
            **diagnostics,
            "valid": True,
            "action": "NY_INDEX_OPEN_SIGNAL_CONFIRMED",
            "reason": "SESGO_H1_MAS_CONFIRMACION_M5_CONFIRMADOS",
            "direction": direction,
            "signal": signal,
            "entry": signal,
            "diagnostics": diagnostics,
        }
