"""Motor de Criterio Humano (Human Criteria Decision Engine).

Actúa como un comité inteligente de evaluación de trades para que el bot tome decisiones
con criterio humano profesional:
1. Macro & Noticias: Protege Forex, Oro, Petróleo e Índices durante ventanas de alto impacto.
2. Tendencia & Régimen: Exige alineación HTF (H1) en índices sintéticos y veta mercados en fango/choppiness.
3. Calidad & Anti-Agotamiento: Evita compras/ventas en sobreextensiones parabólicas y premia rechazos con mecha.
4. Scoring de Confluencia (0 a 100): Califica el setup objetivamente.

REGLA ESTRICTA DE GOBERNANZA:
    Este motor evalúa si un trade es ADMISIBLE o VETADO.
    JAMÁS altera los niveles predefinidos de Stop Loss o Take Profit de la estrategia.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any
import numpy as np
import pandas as pd

from strategy.human_criteria.config import (
    HumanCriteriaConfig,
    MODE_FILTER,
    MODE_OBSERVE,
    MODE_OFF,
)
from strategy.regime.market_regime_sentinel import (
    REGIME_CLEAN_RANGE,
    REGIME_HIGH_VOLATILITY,
    REGIME_STABLE_TREND,
    REGIME_TOXIC_NOISE,
    classify_market_regime,
    compute_regime_metrics,
)
from services.financial_news_service import load_economic_calendar_state


@dataclass
class ScoreBreakdown:
    """Desglose de puntuación por componente (Total máx: 100 puntos)."""

    macro_news: float = 0.0          # Máx 25.0 (Reales) / 0.0 (Sintéticos)
    htf_trend: float = 0.0           # Máx 30.0
    regime_health: float = 0.0       # Máx 20.0 (Reales) / 25.0 (Sintéticos)
    candle_quality: float = 0.0      # Máx 15.0 (Reales) / 25.0 (Sintéticos)
    streak_health: float = 0.0       # Máx 10.0 (Sintéticos) / 0.0 (Reales)
    spread_friction: float = 0.0     # Máx 10.0
    spike_penalty: float = 0.0       # Penalización por asimetría de spikes (0.0 a 20.0)
    total_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HumanCriteriaDecision:
    """Decisión emitida por el motor de criterio humano."""

    symbol: str
    direction: str
    allowed: bool
    mode: str
    action: str
    score: float
    grade: str                       # GRADE_A_ELITE | GRADE_B_CAUTIOUS | GRADE_C_SUBPAR
    reason: str
    primary_veto_factor: str | None
    evaluated_at: str
    breakdown: ScoreBreakdown = field(default_factory=ScoreBreakdown)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result = asdict(self)
        result["breakdown"] = self.breakdown.to_dict()
        return result


def classify_symbol_category(symbol: str) -> str:
    """Clasifica el activo según su naturaleza de mercado."""
    s = str(symbol or "").strip().upper()
    s_low = s.lower()

    # Sintéticos Deriv
    if (
        "crash" in s_low
        or "boom" in s_low
        or "step" in s_low
        or "jump" in s_low
        or "volatility" in s_low
        or "dex" in s_low
        or "range break" in s_low
        or "drift" in s_low
        or "synthetic" in s_low
    ):
        return "SYNTHETIC"

    # Metales y Materias Primas
    if (
        "XAU" in s
        or "GOLD" in s
        or "XAG" in s
        or "SILVER" in s
        or "OIL" in s
        or "USOUSD" in s
        or "WTICO" in s
        or "BRENT" in s
    ):
        return "COMMODITY"

    # Índices Americanos / Globales
    if (
        "US TECH" in s
        or "NAS100" in s
        or "USTECH" in s
        or "WALL STREET" in s
        or "US30" in s
        or "DJ30" in s
        or "US500" in s
        or "SPX" in s
        or "GER40" in s
        or "UK100" in s
    ):
        return "INDEX"

    # Criptomonedas
    if "BTC" in s or "ETH" in s or "CRYPTO" in s:
        return "CRYPTO"

    # Forex (6 caracteres o divisas reconocidas)
    known_currencies = ("USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD")
    if len(s) >= 6:
        for c in known_currencies:
            if c in s:
                return "FOREX"

    return "OTHER"


def _calc_ema(series: pd.Series, span: int) -> pd.Series:
    """Calcula Exponential Moving Average sin lookahead."""
    return series.ewm(span=span, adjust=False).mean()


def _calc_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calcula Average True Range."""
    high = df["high"]
    low = df["low"]
    close = df["close"]
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(window=period, min_periods=period).mean()


class HumanCriteriaEngine:
    """Evaluador de confluencia y criterio para la toma de trades."""

    def __init__(self, config: HumanCriteriaConfig | None = None) -> None:
        self.config = config or HumanCriteriaConfig()

    def evaluate_candidate(
        self,
        symbol: str,
        direction: str,
        signal: dict[str, Any],
        df_h1: pd.DataFrame | None = None,
        df_ltf: pd.DataFrame | None = None,
        current_spread: float | None = None,
        current_time: datetime | None = None,
        repository: Any | None = None,
    ) -> HumanCriteriaDecision:
        """Evalúa una oportunidad candidata antes de permitir su ejecución.

        IMPORTANTE:
            - Esta función NO modifica Stop Loss ni Take Profit de `signal`.
            - Devuelve un veredicto estructurado con puntuación y desglose.
        """
        now = current_time or datetime.now(timezone.utc)
        sym = str(symbol or "").strip()
        dir_clean = str(direction or "").strip().upper()
        dir_clean = "BUY" if dir_clean in ("BUY", "LONG") else "SELL" if dir_clean in ("SELL", "SHORT") else dir_clean

        category = classify_symbol_category(sym)
        is_synthetic = (category == "SYNTHETIC")
        mode = str(self.config.mode or MODE_FILTER).upper()

        if not bool(self.config.enabled) or mode == MODE_OFF:
            return HumanCriteriaDecision(
                symbol=sym,
                direction=dir_clean,
                allowed=True,
                mode=MODE_OFF,
                action="HUMAN_CRITERIA_OFF",
                score=100.0,
                grade="GRADE_A_ELITE",
                reason="MOTOR_CRITERIO_DESACTIVADO",
                primary_veto_factor=None,
                evaluated_at=now.isoformat(),
                breakdown=ScoreBreakdown(total_score=100.0),
            )

        # 1. Macro & News Evaluation (0 pts en sintéticos; máx 25 pts en reales)
        score_news, news_blocked, news_reason, news_details = self._eval_macro_news(
            symbol=sym,
            category=category,
            now=now,
        )

        # 2. HTF Trend Evaluation (H1) & Mean Reversion Guard
        score_htf, htf_counter, htf_reason, htf_details = self._eval_htf_trend(
            symbol=sym,
            category=category,
            direction=dir_clean,
            df_h1=df_h1,
        )

        # 3. Spike Hazard Evaluation (Crash & Boom)
        spike_penalty, spike_veto, spike_reason, spike_details = self._eval_spike_hazard(
            symbol=sym,
            category=category,
            direction=dir_clean,
        )

        # 4. Market Regime & Choppiness Evaluation
        score_regime, regime_toxic, regime_reason, regime_details = self._eval_regime_health(
            symbol=sym,
            category=category,
            df_h1=df_h1,
            current_spread=current_spread,
        )

        # 5. Trigger Candle Quality & Anti-Climax Evaluation
        score_candle, candle_climax, candle_reason, candle_details = self._eval_candle_quality(
            symbol=sym,
            category=category,
            direction=dir_clean,
            df_ltf=df_ltf,
        )

        # 6. Instrument Streak & Recent Health Evaluation (Sintéticos)
        score_streak, streak_blocked, streak_reason, streak_details = self._eval_streak_health(
            symbol=sym,
            category=category,
            repository=repository,
            now=now,
        )

        # 7. Spread Friction vs Stop Loss
        score_spread, spread_details = self._eval_spread_friction(
            signal=signal,
            current_spread=current_spread,
        )

        strat_name = str(
            signal.get("strategy_name")
            or signal.get("strategy")
            or signal.get("source_strategy")
            or ""
        ).upper()
        is_msnr = ("MALAYSIAN" in strat_name) or ("MSNR" in strat_name)

        # Cálculo de Score Global (0 a 100)
        if is_synthetic:
            raw_score = score_htf + score_regime + score_candle + score_streak + score_spread - spike_penalty
            if is_msnr:
                min_score_thresh = float(getattr(self.config, "malaysian_snr_min_score_threshold", 60.0))
            else:
                min_score_thresh = float(getattr(self.config, "synthetic_min_score_threshold", 75.0))
        else:
            raw_score = score_news + score_htf + score_regime + score_candle + score_spread
            if is_msnr:
                min_score_thresh = float(getattr(self.config, "malaysian_snr_min_score_threshold", 60.0))
            else:
                min_score_thresh = float(self.config.min_score_threshold)

        total_score = round(min(100.0, max(0.0, raw_score)), 2)

        breakdown = ScoreBreakdown(
            macro_news=round(score_news, 2),
            htf_trend=round(score_htf, 2),
            regime_health=round(score_regime, 2),
            candle_quality=round(score_candle, 2),
            streak_health=round(score_streak, 2),
            spread_friction=round(score_spread, 2),
            spike_penalty=round(spike_penalty, 2),
            total_score=total_score,
        )

        # Clasificación por Grado
        if total_score >= self.config.elite_score_threshold:
            grade = "GRADE_A_ELITE"
        elif total_score >= min_score_thresh:
            grade = "GRADE_B_CAUTIOUS"
        else:
            grade = "GRADE_C_SUBPAR"

        details = {
            "category": category,
            "news": news_details,
            "htf_trend": htf_details,
            "spike_hazard": spike_details,
            "regime": regime_details,
            "candle": candle_details,
            "streak": streak_details,
            "spread": spread_details,
        }

        # Determinación de Vetos Críticos en Modo FILTER
        primary_veto: str | None = None
        action = "HUMAN_CRITERIA_PASSED"
        allowed = True

        if spike_veto:
            primary_veto = spike_reason
            action = "HUMAN_CRITERIA_SPIKE_HAZARD_BLOCKED"
        elif news_blocked:
            primary_veto = news_reason
            action = "HUMAN_CRITERIA_NEWS_BLOCKED"
        elif htf_counter:
            primary_veto = htf_reason
            action = "HUMAN_CRITERIA_COUNTERTREND_BLOCKED"
        elif candle_climax:
            primary_veto = candle_reason
            action = "HUMAN_CRITERIA_CLIMAX_BLOCKED"
        elif regime_toxic:
            primary_veto = regime_reason
            action = "HUMAN_CRITERIA_TOXIC_REGIME_BLOCKED"
        elif streak_blocked:
            primary_veto = streak_reason
            action = "HUMAN_CRITERIA_STREAK_BLOCKED"
        elif total_score < min_score_thresh:
            primary_veto = f"SCORE_BELOW_THRESHOLD ({total_score:.1f} < {min_score_thresh:.1f})"
            action = "HUMAN_CRITERIA_LOW_SCORE_BLOCKED"

        if primary_veto is not None:
            if mode == MODE_FILTER:
                allowed = False
                reason = f"CRITERIO_HUMANO_VETO:{primary_veto}"
            else:  # MODE_OBSERVE
                allowed = True
                action = f"{action}_OBSERVED"
                reason = f"CRITERIO_HUMANO_OBSERVADO:{primary_veto}"
        else:
            reason = f"CRITERIO_HUMANO_APROBADO: Score={total_score:.1f} ({grade})"

        return HumanCriteriaDecision(
            symbol=sym,
            direction=dir_clean,
            allowed=allowed,
            mode=mode,
            action=action,
            score=total_score,
            grade=grade,
            reason=reason,
            primary_veto_factor=primary_veto,
            evaluated_at=now.isoformat(),
            breakdown=breakdown,
            details=details,
        )

    # -------------------------------------------------------------------------
    # Sub-evaluadores
    # -------------------------------------------------------------------------

    def _eval_macro_news(
        self, symbol: str, category: str, now: datetime
    ) -> tuple[float, bool, str, dict[str, Any]]:
        """Evalúa si el activo está amenazado por eventos macro de alto impacto."""
        # Sintéticos no tienen fundamentales ni noticias macro (0 puntos de regalo)
        if category == "SYNTHETIC":
            return 0.0, False, "", {"status": "NOT_APPLICABLE_SYNTHETIC", "note": "Zero free macro points in synthetics"}

        if not bool(self.config.forex_news_guard_enabled) and not bool(self.config.commodities_news_guard_enabled):
            return self.config.weight_macro_news, False, "", {"status": "NEWS_GUARD_DISABLED"}

        # Identificar qué divisas / eventos impactan al activo
        affected_currencies = set()
        sym_u = symbol.upper()

        if category == "FOREX":
            known = ("USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD", "ZAR", "MXN")
            letters = "".join(ch for ch in sym_u if ch.isalpha())
            for i in range(max(1, len(letters) - 5)):
                block = letters[i:i+6]
                if len(block) == 6 and block[:3] in known and block[3:] in known:
                    affected_currencies.update({block[:3], block[3:]})
                    break
        elif category in ("COMMODITY", "INDEX"):
            # Oro, Petróleo, Índices US están directamente ligados al Dólar (USD)
            for usd_sym in self.config.usd_sensitive_symbols:
                if usd_sym in sym_u:
                    affected_currencies.add("USD")
                    break

        if not affected_currencies and category not in ("COMMODITY", "INDEX"):
            return self.config.weight_macro_news, False, "", {"status": "NO_CURRENCIES_MATCHED"}

        # Leer calendario económico
        before = timedelta(minutes=max(0, int(self.config.news_before_minutes)))
        after = timedelta(minutes=max(0, int(self.config.news_after_minutes)))
        calendar = load_economic_calendar_state(self.config.news_calendar_path)
        events = calendar.get("events") or []

        is_oil = any(k in sym_u.lower() for k in ("oil", "crude", "wtico", "usousd", "brent"))

        for ev in events:
            if not isinstance(ev, dict) or str(ev.get("impact") or "").upper() != "ALTO":
                continue

            country = str(ev.get("country") or "").upper()
            title = str(ev.get("title") or ev.get("title_original") or "").lower()

            matches = country in affected_currencies
            if is_oil and any(kw in title for kw in self.config.oil_event_keywords):
                matches = True

            if not matches:
                continue

            try:
                ev_at = datetime.fromisoformat(
                    str(ev.get("event_at") or "").replace("Z", "+00:00")
                ).astimezone(timezone.utc)
            except (ValueError, TypeError):
                continue

            # Comprobar si nos encontramos en la ventana de congelamiento
            if (ev_at - before) <= now <= (ev_at + after):
                phase = "PRE_EVENT" if now < ev_at else "POST_EVENT"
                return (
                    0.0,
                    True,
                    f"HIGH_IMPACT_NEWS_WINDOW:{country}:{ev.get('title')}:{phase}",
                    {"event": ev, "phase": phase, "event_at": ev_at.isoformat()},
                )

        # Sin eventos amenazantes en ventana
        return self.config.weight_macro_news, False, "", {"status": "CLEAR_NO_HIGH_IMPACT_EVENTS"}

    def _eval_htf_trend(
        self, symbol: str, category: str, direction: str, df_h1: pd.DataFrame | None
    ) -> tuple[float, bool, str, dict[str, Any]]:
        """Evalúa la alineación de tendencia en H1 (Marea Mayor) y sobreextensión."""
        is_synthetic = (category == "SYNTHETIC")
        max_pts = float(self.config.synthetic_weight_htf_trend if is_synthetic else self.config.weight_htf_trend)
        if df_h1 is None or len(df_h1) < 30:
            return max_pts * 0.60, False, "", {"status": "INSUFFICIENT_H1_CANDLES"}

        close = df_h1["close"]
        ema_fast = _calc_ema(close, self.config.synthetic_h1_fast_ema)
        ema_slow = _calc_ema(close, self.config.synthetic_h1_slow_ema)

        idx = len(df_h1) - 1
        c_last = float(close.iloc[idx])
        fast_last = float(ema_fast.iloc[idx])
        slow_last = float(ema_slow.iloc[idx]) if len(df_h1) >= 60 else fast_last

        # Pendiente de EMA rápida sobre las últimas 3 velas
        fast_prev = float(ema_fast.iloc[max(0, idx - 3)])
        slope_up = fast_last > fast_prev
        slope_down = fast_last < fast_prev

        is_bullish = c_last > fast_last and (fast_last >= slow_last or slope_up)
        is_bearish = c_last < fast_last and (fast_last <= slow_last or slope_down)

        details = {
            "close_h1": c_last,
            "ema_fast": fast_last,
            "ema_slow": slow_last,
            "is_bullish": is_bullish,
            "is_bearish": is_bearish,
        }

        is_counter = False
        score_res = 0.0
        reason = ""

        if direction == "BUY":
            if is_bullish:
                score_res = max_pts
            elif not is_bearish:
                # Zona de transición / retroceso leve
                score_res = max_pts * 0.60
            else:
                is_counter = True
                score_res = 0.0
                reason = "COUNTER_TREND_BUY_IN_BEARISH_H1"

        elif direction == "SELL":
            if is_bearish:
                score_res = max_pts
            elif not is_bullish:
                score_res = max_pts * 0.60
            else:
                is_counter = True
                score_res = 0.0
                reason = "COUNTER_TREND_SELL_IN_BULLISH_H1"
        else:
            score_res = max_pts * 0.50

        is_veto = is_counter and (category == "SYNTHETIC" and self.config.synthetic_require_h1_alignment)

        # Filtro de sobre-extensión elástica respecto a media HTF en sintéticos (Mean Reversion)
        if (
            is_synthetic
            and not is_counter
            and bool(getattr(self.config, "synthetic_mean_reversion_guard_enabled", True))
            and len(df_h1) >= 15
        ):
            atr_s = _calc_atr(df_h1, 14)
            atr_val = float(atr_s.iloc[idx]) if not np.isnan(atr_s.iloc[idx]) else 0.0
            if atr_val > 0:
                dist_ema = abs(c_last - fast_last)
                max_dev = float(getattr(self.config, "synthetic_max_ema_deviation_atr", 2.5)) * atr_val
                if dist_ema > max_dev:
                    penalty = float(getattr(self.config, "synthetic_mean_reversion_penalty_points", 10.0))
                    score_res = max(0.0, score_res - penalty)
                    details["mean_reversion_overextended"] = True
                    details["dist_ema_to_atr"] = round(dist_ema / atr_val, 2)

        return score_res, is_veto, reason, details

    def _eval_spike_hazard(
        self, symbol: str, category: str, direction: str
    ) -> tuple[float, bool, str, dict[str, Any]]:
        """Evalúa el riesgo de operar en contra del sentido natural de spikes en Boom/Crash."""
        if category != "SYNTHETIC" or not bool(getattr(self.config, "synthetic_spike_hazard_guard_enabled", True)):
            return 0.0, False, "", {"status": "NOT_APPLICABLE"}

        sym_u = symbol.upper()
        penalty = 0.0
        is_veto = False
        reason = ""

        is_crash_hazard = ("CRASH" in sym_u and direction == "BUY")
        is_boom_hazard = ("BOOM" in sym_u and direction == "SELL")

        if is_crash_hazard:
            penalty = float(getattr(self.config, "synthetic_spike_hazard_penalty_points", 20.0))
            reason = "CRASH_SPIKE_HAZARD_BUY: Compra en contra del flujo asimétrico de spikes bajistas"
            is_veto = bool(getattr(self.config, "synthetic_spike_hazard_veto_enabled", False))
        elif is_boom_hazard:
            penalty = float(getattr(self.config, "synthetic_spike_hazard_penalty_points", 20.0))
            reason = "BOOM_SPIKE_HAZARD_SELL: Venta en contra del flujo asimétrico de spikes alcistas"
            is_veto = bool(getattr(self.config, "synthetic_spike_hazard_veto_enabled", False))

        details = {
            "is_crash_hazard": is_crash_hazard,
            "is_boom_hazard": is_boom_hazard,
            "penalty_points": penalty,
            "hazard_detected": is_crash_hazard or is_boom_hazard,
        }
        return penalty, is_veto, reason, details

    def _eval_regime_health(
        self, symbol: str, category: str, df_h1: pd.DataFrame | None, current_spread: float | None
    ) -> tuple[float, bool, str, dict[str, Any]]:
        """Evalúa la salud del régimen de mercado y choppiness."""
        is_synthetic = (category == "SYNTHETIC")
        max_pts = float(self.config.synthetic_weight_regime_health if is_synthetic else self.config.weight_regime_health)
        if df_h1 is None or len(df_h1) < 20:
            return max_pts * 0.60, False, "", {"status": "INSUFFICIENT_DATA"}

        try:
            metrics = compute_regime_metrics(
                df=df_h1,
                current_spread=current_spread,
                period=14,
            )
            classification = classify_market_regime(metrics, symbol=symbol)
        except Exception as e:
            return max_pts * 0.50, False, "", {"error": str(e)}

        regime = classification.regime
        is_toxic = classification.is_toxic or (
            category == "SYNTHETIC"
            and metrics.choppiness_index > self.config.synthetic_choppiness_threshold
            and metrics.adx < self.config.synthetic_adx_min_threshold
        )

        details = {
            "regime": regime,
            "choppiness": metrics.choppiness_index,
            "adx": metrics.adx,
            "is_toxic": is_toxic,
        }

        if is_toxic:
            return 0.0, True, f"TOXIC_CHOPPY_REGIME:{classification.primary_factor}", details
        elif regime == REGIME_STABLE_TREND:
            return max_pts, False, "", details
        elif regime == REGIME_CLEAN_RANGE:
            return max_pts * 0.80, False, "", details
        elif regime == REGIME_HIGH_VOLATILITY:
            return max_pts * 0.70, False, "", details

        return max_pts * 0.50, False, "", details

    def _eval_candle_quality(
        self, symbol: str, category: str, direction: str, df_ltf: pd.DataFrame | None
    ) -> tuple[float, bool, str, dict[str, Any]]:
        """Evalúa la calidad de la vela desencadenante y el filtro anti-clímax."""
        is_synthetic = (category == "SYNTHETIC")
        max_pts = float(self.config.synthetic_weight_candle_quality if is_synthetic else self.config.weight_candle_quality)
        if df_ltf is None or len(df_ltf) < 15:
            return max_pts * 0.65, False, "", {"status": "INSUFFICIENT_LTF_CANDLES"}

        idx = len(df_ltf) - 1
        c = float(df_ltf["close"].iloc[idx])
        o = float(df_ltf["open"].iloc[idx])
        h = float(df_ltf["high"].iloc[idx])
        l = float(df_ltf["low"].iloc[idx])

        rng = max(1e-9, h - l)
        body = abs(c - o)
        upper_wick = h - max(c, o)
        lower_wick = min(c, o) - l

        # Calcular ATR(14) en LTF
        atr_series = _calc_atr(df_ltf, 14)
        atr_val = float(atr_series.iloc[idx]) if not np.isnan(atr_series.iloc[idx]) else (rng * 1.2)

        # 1. Filtro Anti-Agotamiento Clímax (no comprar en la cúspide de una vela parabólica)
        is_climax = False
        if bool(self.config.synthetic_climax_filter_enabled) and category == "SYNTHETIC" and atr_val > 0:
            if rng > (self.config.synthetic_climax_atr_multiplier * atr_val):
                # Si una sola vela mide más de 2.75x ATR y su cuerpo domina la vela (≥65% cuerpo) en la dirección del trade
                if (direction == "BUY" and c > o and (body / rng) >= 0.65 and (upper_wick / rng) < 0.20) or (
                    direction == "SELL" and c < o and (body / rng) >= 0.65 and (lower_wick / rng) < 0.20
                ):
                    is_climax = True

        details = {
            "candle_range": rng,
            "atr_ltf": atr_val,
            "upper_wick_ratio": round(upper_wick / rng, 2),
            "lower_wick_ratio": round(lower_wick / rng, 2),
            "is_climax": is_climax,
        }

        if is_climax:
            return 0.0, True, "PARABOLIC_CLIMAX_OVEREXTENSION", details

        # 2. Recompensa por Mecha de Rechazo Institucional
        if direction == "BUY":
            # Mecha inferior atractiva (los compradores defendieron el nivel)
            if lower_wick / rng >= 0.25:
                return max_pts, False, "", details
            elif upper_wick / rng >= 0.40:
                # Mecha superior adversa (los vendedores rechazaron el máximo)
                return max_pts * 0.40, False, "", details
        elif direction == "SELL":
            # Mecha superior atractiva (los vendedores rechazaron máximos)
            if upper_wick / rng >= 0.25:
                return max_pts, False, "", details
            elif lower_wick / rng >= 0.40:
                # Mecha inferior adversa
                return max_pts * 0.40, False, "", details

        return max_pts * 0.70, False, "", details

    def _eval_streak_health(
        self, symbol: str, category: str, repository: Any | None, now: datetime
    ) -> tuple[float, bool, str, dict[str, Any]]:
        """Evalúa la salud reciente y racha intradía del activo en sintéticos."""
        if category != "SYNTHETIC":
            return 0.0, False, "", {"status": "NOT_APPLICABLE_REAL_MARKET"}

        max_pts = float(getattr(self.config, "synthetic_weight_streak_health", 10.0))
        if not bool(getattr(self.config, "synthetic_streak_guard_enabled", True)):
            return max_pts, False, "", {"status": "STREAK_GUARD_DISABLED"}

        if repository is None:
            # Sin repositorio persistente en memoria: puntaje neutral saludable (80%)
            return max_pts * 0.80, False, "", {"status": "NO_REPOSITORY_PROVIDED"}

        checker = getattr(repository, "get_symbol_loss_status", None)
        if not callable(checker):
            return max_pts * 0.80, False, "", {"status": "CHECKER_NOT_AVAILABLE"}

        try:
            status = checker(symbol=symbol, source="DEMO", cooldown_minutes=60.0, now_utc=now)
        except Exception as e:
            return max_pts * 0.80, False, "", {"error": str(e)}

        is_cooldown = bool(status.get("cooldown_active", False))
        daily_losses = int(status.get("daily_losses_count", 0) or 0)

        details = {
            "cooldown_active": is_cooldown,
            "cooldown_rem_min": status.get("cooldown_remaining_minutes", 0.0),
            "daily_losses": daily_losses,
        }

        if is_cooldown:
            return 0.0, False, "SYMBOL_IN_POST_SL_COOLDOWN", details
        elif daily_losses >= 2:
            return max_pts * 0.20, False, "MULTIPLE_DAILY_LOSSES", details
        elif daily_losses == 1:
            return max_pts * 0.60, False, "SINGLE_DAILY_LOSS", details

        return max_pts, False, "", details

    def _eval_spread_friction(
        self, signal: dict[str, Any], current_spread: float | None
    ) -> tuple[float, dict[str, Any]]:
        """Evalúa la fricción del spread respecto al Stop Loss."""
        max_pts = self.config.weight_spread_friction
        spread = current_spread or float(signal.get("spread", 0.0) or 0.0)
        entry = float(signal.get("entry_price", 0.0) or 0.0)
        sl = float(signal.get("stop_loss", 0.0) or 0.0)

        sl_dist = abs(entry - sl)
        if sl_dist <= 0 or spread <= 0:
            return max_pts * 0.80, {"status": "NO_SPREAD_DATA"}

        ratio = spread / sl_dist
        details = {"spread": spread, "sl_dist": sl_dist, "spread_sl_ratio": round(ratio, 4)}

        if ratio <= 0.03:
            return max_pts, details
        elif ratio <= 0.08:
            return max_pts * 0.75, details
        elif ratio <= 0.15:
            return max_pts * 0.50, details
        else:
            return max_pts * 0.20, details
