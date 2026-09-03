from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timezone
from zoneinfo import ZoneInfo
import math
import re

import pandas as pd


NEW_YORK = ZoneInfo("America/New_York")


def _norm_symbol(symbol: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(symbol or "").lower())


def classify_orb_market(symbol: str) -> str | None:
    """Clasifica únicamente los contratos ORB autorizados.

    Importante: no usamos el término genérico ``gold`` porque Deriv publica
    productos distintos (Gold BB, Gold MACO, etc.) que no son XAUUSD y algunos
    tienen trading deshabilitado.
    """
    name = _norm_symbol(symbol)

    # Oro: nombres concretos observados/soportados. Evaluar micro primero evita
    # que XAUUSDmicro sea absorbido por la familia XAUUSD estándar.
    if name in {"xauusdmicro", "microxauusd"}:
        return "MICRO_XAUUSD"
    if name == "xauusd":
        return "XAUUSD"

    aliases = {
        "WALL_STREET_30": ("wallstreet30", "us30", "dj30", "dow30", "dowjones30"),
        "US_TECH_100": ("ustech100", "ustec100", "ustec", "nasdaq100", "nas100"),
        "US_500": ("us500", "sp500", "spx500", "sandp500"),
    }
    for market, tokens in aliases.items():
        if any(token == name or token in name for token in tokens):
            return market
    return None


def is_orb_eligible_symbol(symbol: str) -> bool:
    return classify_orb_market(symbol) is not None


def is_orb_gold_symbol(symbol: str) -> bool:
    """True únicamente para las dos variantes de Oro autorizadas por ORB."""
    return classify_orb_market(symbol) in {"XAUUSD", "MICRO_XAUUSD"}


def score_orb_gold_contract_candidate(
    *,
    target_leg_risk: float,
    actual_leg_risk: float,
    spread_cost: float,
    margin_required: float,
    free_margin: float,
) -> dict:
    """Puntúa la calidad de ejecución del contrato de Oro.

    Menor score = mejor contrato para representar la MISMA oportunidad ORB.
    Priorizamos:
      1) precisión del riesgo de 0.5% después del volume_step;
      2) coste de spread respecto del riesgo de esa pierna;
      3) margen consumido respecto del margen libre.

    La señal técnica no gana puntos por ser XAUUSD o microXAUUSD: la elección es
    puramente de calidad de ejecución/riesgo para no duplicar exposición.
    """
    target = max(0.0, float(target_leg_risk))
    actual = max(0.0, float(actual_leg_risk))
    spread = max(0.0, float(spread_cost))
    margin = max(0.0, float(margin_required))
    free = max(0.0, float(free_margin))

    risk_error_ratio = abs(actual - target) / target if target > 0 else math.inf
    spread_risk_ratio = spread / target if target > 0 else math.inf
    margin_free_ratio = margin / free if free > 0 else math.inf

    # El error de sizing domina. Spread y margen actúan como desempate económico.
    score = (
        risk_error_ratio * 1000.0
        + spread_risk_ratio * 100.0
        + margin_free_ratio * 10.0
    )
    return {
        "score": float(score),
        "risk_error_ratio": float(risk_error_ratio),
        "spread_risk_ratio": float(spread_risk_ratio),
        "margin_free_ratio": float(margin_free_ratio),
        "target_leg_risk": target,
        "actual_leg_risk": actual,
        "spread_cost": spread,
        "margin_required": margin,
        "free_margin": free,
    }


def discover_orb_symbols(data_provider) -> list[str]:
    """Descubre únicamente contratos ORB operables en la cuenta MT5 actual.

    Los símbolos con ``trade_mode == 0`` se excluyen antes del preflight para
    que productos Deriv no utilizados (por ejemplo Gold BB/MACO) no bloqueen
    todo el arranque del daemon.
    """
    terms = ("XAUUSD", "Wall Street", "US Tech", "USTEC", "NASDAQ", "US500", "US 500", "SP500")
    found = set()
    get_info = getattr(data_provider, "get_symbol_info", None)

    for term in terms:
        try:
            candidates = data_provider.search_symbols(term)
        except Exception:
            continue

        for symbol in candidates:
            if not is_orb_eligible_symbol(symbol):
                continue

            # Cuando el proveedor expone trade_mode, 0 corresponde a
            # SYMBOL_TRADE_MODE_DISABLED en MetaTrader5.
            if callable(get_info):
                try:
                    info = get_info(symbol) or {}
                    trade_mode = info.get("trade_mode")
                    if trade_mode is not None and int(trade_mode) == 0:
                        continue
                except Exception:
                    # Si no podemos validar el contrato, no lo incorporamos
                    # automáticamente al universo de ejecución.
                    continue

            found.add(str(symbol))

    return sorted(found)


@dataclass
class ORBConfig:
    enabled: bool = True
    timezone_name: str = "America/New_York"
    opening_hour: int = 9
    opening_minute: int = 30
    opening_range_minutes: int = 15
    session_close_hour: int = 16
    session_close_minute: int = 0
    timeframe: str = "M5"
    candle_count: int = 1000
    breakout_buffer_fraction: float = 0.0
    require_retest: bool = True
    require_vwap_alignment: bool = True
    require_poc_alignment: bool = True
    poc_bins: int = 24
    target_rr: float = 2.0
    stop_mode: str = "MIDPOINT"  # v61: protección estructural al 50% del ORB
    stop_buffer_fraction: float = 0.0
    one_signal_per_session: bool = True


class NewYorkORBStrategy:
    """Opening Range Breakout para la sesión cash de Nueva York.

    - Rango: 09:30 <= NY < 09:45.
    - Rupturas: desde 09:45 hasta antes de 16:00 NY.
    - Ruptura confirmada en M5 y entrada sólo tras retesteo del borde roto del ORB.
    - El retesteo debe tocar/reingresar al borde y cerrar nuevamente fuera del rango.
    - VWAP de sesión y POC aproximado por perfil de volumen se usan como filtros de contexto.
    """

    def __init__(self, data_provider, config: ORBConfig | None = None):
        self.data_provider = data_provider
        self.config = config or ORBConfig()
        self.tz = ZoneInfo(self.config.timezone_name)

    def _session_bounds(self, now_utc: datetime):
        now_utc = pd.Timestamp(now_utc)
        if now_utc.tzinfo is None:
            now_utc = now_utc.tz_localize("UTC")
        else:
            now_utc = now_utc.tz_convert("UTC")
        now_ny = now_utc.tz_convert(self.tz)
        d = now_ny.date()
        open_ny = pd.Timestamp(datetime.combine(d, time(self.config.opening_hour, self.config.opening_minute)), tz=self.tz)
        range_end_ny = open_ny + pd.Timedelta(minutes=int(self.config.opening_range_minutes))
        close_ny = pd.Timestamp(datetime.combine(d, time(self.config.session_close_hour, self.config.session_close_minute)), tz=self.tz)
        return now_ny, open_ny, range_end_ny, close_ny

    @staticmethod
    def _volume_column(df: pd.DataFrame) -> pd.Series:
        if "real_volume" in df.columns:
            rv = pd.to_numeric(df["real_volume"], errors="coerce").fillna(0.0)
            if float(rv.sum()) > 0:
                return rv.astype(float)
        if "tick_volume" in df.columns:
            return pd.to_numeric(df["tick_volume"], errors="coerce").fillna(0.0).astype(float)
        if "volume" in df.columns:
            return pd.to_numeric(df["volume"], errors="coerce").fillna(0.0).astype(float)
        return pd.Series([1.0] * len(df), index=df.index, dtype=float)

    @staticmethod
    def _session_vwap(df: pd.DataFrame) -> float | None:
        if df.empty:
            return None
        volume = NewYorkORBStrategy._volume_column(df)
        typical = (
            pd.to_numeric(df["high"], errors="coerce")
            + pd.to_numeric(df["low"], errors="coerce")
            + pd.to_numeric(df["close"], errors="coerce")
        ) / 3.0
        denom = float(volume.sum())
        if denom <= 0:
            return float(typical.mean()) if typical.notna().any() else None
        value = float((typical * volume).sum() / denom)
        return value if math.isfinite(value) else None

    @staticmethod
    def _session_poc(df: pd.DataFrame, bins: int = 24) -> float | None:
        if df.empty:
            return None
        low = float(pd.to_numeric(df["low"], errors="coerce").min())
        high = float(pd.to_numeric(df["high"], errors="coerce").max())
        if not (math.isfinite(low) and math.isfinite(high)):
            return None
        if high <= low:
            return float(pd.to_numeric(df["close"], errors="coerce").iloc[-1])

        bins = max(4, int(bins))
        width = (high - low) / bins
        volume = NewYorkORBStrategy._volume_column(df)
        typical = (
            pd.to_numeric(df["high"], errors="coerce")
            + pd.to_numeric(df["low"], errors="coerce")
            + pd.to_numeric(df["close"], errors="coerce")
        ) / 3.0
        bucket_volume = [0.0] * bins
        for price, vol in zip(typical.tolist(), volume.tolist()):
            if not (math.isfinite(float(price)) and math.isfinite(float(vol))):
                continue
            idx = min(bins - 1, max(0, int((float(price) - low) / width)))
            bucket_volume[idx] += max(0.0, float(vol))
        idx = max(range(bins), key=lambda i: bucket_volume[i])
        return low + (idx + 0.5) * width

    def _prepare_candles(self, symbol: str, now_utc: datetime) -> pd.DataFrame:
        df = self.data_provider.get_candles(symbol, self.config.timeframe, count=int(self.config.candle_count)).copy()
        if "time" not in df.columns:
            raise ValueError(f"ORB requiere columna time en las velas {self.config.timeframe}")
        df["time"] = pd.to_datetime(df["time"], utc=True)
        # Sólo velas cerradas. v61 usa M5 para breakout/retest.
        tf = str(self.config.timeframe or "M5").upper()
        timeframe_minutes = 5 if tf == "M5" else 1
        now_ts = pd.Timestamp(now_utc)
        if now_ts.tzinfo is None:
            now_ts = now_ts.tz_localize("UTC")
        else:
            now_ts = now_ts.tz_convert("UTC")
        df = df[(df["time"] + pd.Timedelta(minutes=timeframe_minutes)) <= now_ts].copy()
        df["time_ny"] = df["time"].dt.tz_convert(self.tz)
        return df.sort_values("time").reset_index(drop=True)

    def analyze_symbol(self, symbol: str, now_utc: datetime | None = None) -> dict:
        market = classify_orb_market(symbol)
        if not bool(self.config.enabled) or market is None:
            return {
                "valid": False,
                "strategy_name": "ORB_NEW_YORK",
                "action": "SYMBOL_NOT_ORB_ELIGIBLE",
                "reason": "ORB_SOLO_XAUUSD_MICROXAUUSD_WALL_STREET_30_US_TECH_100_US500",
                "symbol": symbol,
            }

        if now_utc is None:
            tick = self.data_provider.get_current_tick(symbol)
            now_utc = pd.Timestamp(tick["time"]).to_pydatetime()
        now_ny, open_ny, range_end_ny, close_ny = self._session_bounds(now_utc)

        base = {
            "valid": False,
            "strategy_name": "ORB_NEW_YORK",
            "strategy_version": "orb-ny-v1-vwap-poc",
            "symbol": symbol,
            "orb_market": market,
            "timezone": self.config.timezone_name,
            "session_date_ny": str(now_ny.date()),
            "session_open_ny": open_ny.isoformat(),
            "opening_range_end_ny": range_end_ny.isoformat(),
            "session_close_ny": close_ny.isoformat(),
        }

        if now_ny.weekday() >= 5:
            return {**base, "action": "NO_ORB_SESSION", "reason": "FIN_DE_SEMANA_NEW_YORK"}
        if now_ny < open_ny:
            return {**base, "action": "WAITING_NEW_YORK_OPEN", "reason": "ANTES_DE_09_30_NEW_YORK"}
        if now_ny >= close_ny:
            return {**base, "action": "NO_ORB_SESSION", "reason": "SESION_NEW_YORK_FINALIZADA"}

        df = self._prepare_candles(symbol, now_utc)
        session = df[(df["time_ny"] >= open_ny) & (df["time_ny"] < close_ny)].copy()
        opening = session[(session["time_ny"] >= open_ny) & (session["time_ny"] < range_end_ny)].copy()

        # v61: con M5 el ORB 09:30-09:45 queda formado por 3 velas cerradas.
        tf_minutes = 5 if str(self.config.timeframe or "M5").upper() == "M5" else 1
        needed = max(1, int(math.ceil(float(self.config.opening_range_minutes) / tf_minutes)))
        if now_ny < range_end_ny or len(opening) < needed:
            partial_high = float(opening["high"].max()) if not opening.empty else None
            partial_low = float(opening["low"].min()) if not opening.empty else None
            return {
                **base,
                "action": "BUILDING_OPENING_RANGE",
                "reason": "FORMANDO_RANGO_PRIMEROS_15_MINUTOS",
                "opening_range_candles": int(len(opening)),
                "opening_range_required_candles": needed,
                "opening_range_high": partial_high,
                "opening_range_low": partial_low,
            }

        range_high = float(opening["high"].max())
        range_low = float(opening["low"].min())
        range_size = range_high - range_low
        midpoint = (range_high + range_low) / 2.0
        if not math.isfinite(range_size) or range_size <= 0:
            return {**base, "action": "INVALID_OPENING_RANGE", "reason": "RANGO_ORB_SIN_AMPLITUD"}

        post_range = session[session["time_ny"] >= range_end_ny].copy()
        if post_range.empty:
            return {
                **base,
                "action": "WAITING_BREAKOUT",
                "reason": "RANGO_COMPLETO_ESPERANDO_PRIMERA_VELA_CERRADA_POST_09_45",
                "opening_range_high": range_high,
                "opening_range_low": range_low,
                "opening_range_midpoint": midpoint,
                "opening_range_size": range_size,
            }

        # v61 ORB: secuencia obligatoria en M5 = BREAKOUT -> RETEST -> ENTRADA.
        # El breakout debe ser la vela cerrada inmediatamente anterior al retest,
        # evitando perseguir rupturas antiguas.
        if len(post_range) < 2:
            return {
                **base,
                "action": "WAITING_M5_BREAKOUT_RETEST",
                "reason": "ESPERANDO_SECUENCIA_M5_BREAKOUT_MAS_RETEST",
                "opening_range_high": range_high,
                "opening_range_low": range_low,
                "opening_range_midpoint": midpoint,
                "opening_range_size": range_size,
            }

        breakout = post_range.iloc[-2]
        retest = post_range.iloc[-1]
        before_breakout = session[session["time"] < breakout["time"]]
        prev_close = (
            float(before_breakout.iloc[-1]["close"])
            if not before_breakout.empty
            else float(opening.iloc[-1]["close"])
        )
        breakout_close = float(breakout["close"])
        retest_close = float(retest["close"])
        retest_high = float(retest["high"])
        retest_low = float(retest["low"])
        buffer = range_size * max(0.0, float(self.config.breakout_buffer_fraction))

        breakout_up = prev_close <= range_high + buffer and breakout_close > range_high + buffer
        breakout_down = prev_close >= range_low - buffer and breakout_close < range_low - buffer

        # Retest BUY: vuelve a tocar el OR high pero confirma cerrando por encima.
        # Retest SELL: vuelve a tocar el OR low pero confirma cerrando por debajo.
        retest_buy_ok = breakout_up and retest_low <= range_high + buffer and retest_close > range_high + buffer
        retest_sell_ok = breakout_down and retest_high >= range_low - buffer and retest_close < range_low - buffer
        direction = "BUY" if retest_buy_ok else "SELL" if retest_sell_ok else None

        through_candidate = session[session["time"] <= retest["time"]].copy()
        vwap = self._session_vwap(through_candidate)
        poc = self._session_poc(through_candidate, bins=int(self.config.poc_bins))
        vwap_buy_ok = vwap is not None and retest_close > float(vwap)
        vwap_sell_ok = vwap is not None and retest_close < float(vwap)
        poc_buy_ok = poc is not None and retest_close > float(poc)
        poc_sell_ok = poc is not None and retest_close < float(poc)

        diagnostics = {
            "opening_range_high": range_high,
            "opening_range_low": range_low,
            "opening_range_midpoint": midpoint,
            "opening_range_size": range_size,
            "breakout_candle_time": pd.Timestamp(breakout["time"]).isoformat(),
            "breakout_candle_time_ny": pd.Timestamp(breakout["time_ny"]).isoformat(),
            "breakout_close": breakout_close,
            "retest_candle_time": pd.Timestamp(retest["time"]).isoformat(),
            "retest_candle_time_ny": pd.Timestamp(retest["time_ny"]).isoformat(),
            "retest_close": retest_close,
            "retest_high": retest_high,
            "retest_low": retest_low,
            "previous_close": prev_close,
            "session_vwap": vwap,
            "session_poc": poc,
            "vwap_buy_ok": bool(vwap_buy_ok),
            "vwap_sell_ok": bool(vwap_sell_ok),
            "poc_buy_ok": bool(poc_buy_ok),
            "poc_sell_ok": bool(poc_sell_ok),
            "breakout_up": bool(breakout_up),
            "breakout_down": bool(breakout_down),
            "retest_buy_ok": bool(retest_buy_ok),
            "retest_sell_ok": bool(retest_sell_ok),
            "volume_source": (
                "real_volume" if "real_volume" in through_candidate and float(pd.to_numeric(through_candidate["real_volume"], errors="coerce").fillna(0).sum()) > 0
                else "tick_volume" if "tick_volume" in through_candidate
                else "fallback"
            ),
        }

        if direction is None:
            reason = (
                "ULTIMA_SECUENCIA_M5_NO_TIENE_BREAKOUT_VALIDO"
                if not (breakout_up or breakout_down)
                else "BREAKOUT_M5_SIN_RETEST_CONFIRMADO_AL_ORB"
            )
            return {**base, **diagnostics, "action": "WAITING_M5_BREAKOUT_RETEST", "reason": reason}

        vwap_ok = vwap_buy_ok if direction == "BUY" else vwap_sell_ok
        poc_ok = poc_buy_ok if direction == "BUY" else poc_sell_ok
        failed = []
        if bool(self.config.require_vwap_alignment) and not vwap_ok:
            failed.append("VWAP_NO_ALINEADO_CON_RETEST")
        if bool(self.config.require_poc_alignment) and not poc_ok:
            failed.append("POC_NO_ALINEADO_CON_RETEST")
        if failed:
            return {
                **base, **diagnostics, "direction": direction,
                "action": "ORB_RETEST_FILTERED", "reason": ",".join(failed),
                "rejection_reasons": failed,
            }

        # v61: protección exacta en el 50% del Opening Range.
        # Sin buffer adicional: el midpoint es el nivel estructural de invalidación.
        stop_loss = midpoint
        entry_price = retest_close
        risk_distance = abs(entry_price - stop_loss)
        if risk_distance <= 0:
            return {**base, **diagnostics, "action": "INVALID_ORB_STOP", "reason": "DISTANCIA_DE_RIESGO_ORB_INVALIDA"}
        target_rr = max(0.1, float(self.config.target_rr))
        take_profit = entry_price + risk_distance * target_rr if direction == "BUY" else entry_price - risk_distance * target_rr

        confirmations = {
            "opening_range_complete": True,
            "m5_fresh_breakout": True,
            "orb_retest_confirmed": True,
            "vwap_alignment": bool(vwap_ok),
            "poc_alignment": bool(poc_ok),
            "new_york_session": True,
            "eligible_market": True,
            "stop_at_orb_50_percent": True,
        }
        passed = [name for name, ok in confirmations.items() if ok]
        missing = [name for name, ok in confirmations.items() if not ok]
        percentage = round(len(passed) / len(confirmations) * 100.0, 2)

        signal = {
            "strategy_name": "ORB_NEW_YORK",
            "strategy_version": "orb-ny-v2-m5-breakout-retest-midpoint",
            "timeframe": "M5",
            "valid": True,
            "direction": direction,
            "entry_time": pd.Timestamp(retest["time"]).to_pydatetime(),
            "entry_price": entry_price,
            "stop_loss": float(stop_loss),
            "take_profit": float(take_profit),
            "risk_reward_ratio": target_rr,
            "confirmation_ok": True,
            "confirmation_decision": "ORB_NY_M5_BREAKOUT_RETEST_CONFIRMED",
            "confirmation_percentage": percentage,
            "confirmations_passed": len(passed),
            "confirmations_total": len(confirmations),
            "passed_confirmations": passed,
            "missing_confirmations": missing,
            "critical_confirmations_ok": True,
            "critical_confirmation_failures": [],
            "rejection_reasons": [],
            "confirmations": confirmations,
            "trade_score": percentage,
            "trade_grade": "A" if percentage >= 90 else "B",
            "orb_market": market,
            "opening_range_high": range_high,
            "opening_range_low": range_low,
            "opening_range_midpoint": midpoint,
            "session_vwap": vwap,
            "session_poc": poc,
            "breakout_candle_time_ny": pd.Timestamp(breakout["time_ny"]).isoformat(),
            "retest_candle_time_ny": pd.Timestamp(retest["time_ny"]).isoformat(),
            "orb_risk_model": "1_PERCENT_TOTAL_SPLIT_0_5_TP1_0_5_RUNNER",
            "orb_runner_plan": "TP1_1R_RUNNER_2R_DYNAMIC_3R_4R",
        }

        return {
            **base,
            **diagnostics,
            "valid": True,
            "action": "ORB_SIGNAL_CONFIRMED",
            "reason": "BREAKOUT_M5_MAS_RETEST_ORB_CONFIRMADO_CON_VWAP_Y_POC",
            "direction": direction,
            "signal": signal,
            "entry": signal,
            "h1_trend": None,
            "m15_setup_type": None,
            "m15_structure_break_type": None,
            "m15_zone": None,
            "diagnostics": diagnostics,
        }
