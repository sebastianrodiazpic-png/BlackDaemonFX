"""
strategy/confluence/tripartite_confluence_gate.py
=================================================
Módulo central del Gatillo de Confluencia Tripartita para BlackDaemonFX:
  1. Pilar Estratégico (SMC / ICT, Malaysian SNR, ORB): Señal técnica válida con SL/TP dual-leg.
  2. Pilar Criterio Humano: Régimen ADX >= 20, Vela Clímax <= 85%, Escudo Anti-Spike y Control de Fricción de Spread.
  3. Pilar Filtro Activo de IA: Meta-Labeling probabilístico (LightGBM/Logistic) P(Win) >= 0.50 y expectativa R > 0.

Gestiona además la habilitación controlada y quirúrgica de los 26 ACTIVOS REHABILITADOS
mediante interruptores de configuración de entorno, garantizando Zero Breaking Changes.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple


# Catálogo canónico de activos rehabilitados por estrategia mediante Confluencia Tripartita:
REHABILITATED_ASSETS_BY_STRATEGY: Dict[str, set[str]] = {
    "ICT": {
        # Sintéticos Deriv rehabilitados
        "Jump 100 Index",
        "Crash 1000 Index",
        "Volatility 90 (1s) Index",
        "High Frequency Vol 50 Index",
        "High Frequency Vol 100 Index",
        # Forex mayores rehabilitados
        "EURUSD",
        "USDJPY",
        "USDCAD",
        "AUDUSD",
        # Metales y Commodities rehabilitados
        "XAGUSD",
        "XAUEUR",
        "UK Brent Oil",
        # Cripto e Índices rehabilitados
        "ETHUSD",
        "Germany 40",
        "US SP 500",
    },
    "MALAYSIAN_SNR": set(),  # Los 38 sintéticos ya eran activos y rentables
    "ORB": {
        "USDCHF",
        "US Oil",
        "UK Brent Oil",
        "Germany 40",
        "XAUEUR",
        "ETHUSD",
        "US Tech 100",
        "Wall Street 30",
        "US SP 500",
        "EURUSD",
    },
    "TREND_PULLBACK": {
        "Crash 900 Index",
        "Crash 1000 Index",
        "Boom 500 Index",
        "Boom 1000 Index",
        "Volatility 90 Index",
        "Volatility 90 (1s) Index",
        "High Frequency Vol 50 Index",
        "High Frequency Vol 100 Index",
        "Volatility 50 Index",
        "Step Index 500",
        "Jump 100 Index",
        "Volatility 100 Index",
    },
}

# Activos que deben permanecer en Poda Estricta por fricción de spread insalvable o incompatibilidad
STRICT_PRUNED_ASSETS_BY_STRATEGY: Dict[str, set[str]] = {
    "ICT": {
        "AUDCAD", "AUDCHF", "AUDJPY", "AUDNZD", "CADJPY", "CHFJPY",
        "EURAUD", "EURCAD", "EURGBP", "EURNZD", "GBPAUD", "GBPCAD",
        "GBPCHF", "GBPNZD",
    },
    "MALAYSIAN_SNR": {
        "AUDNZD", "EURCHF", "EURGBP", "EURNZD", "GBPCAD",
    },
    "ORB": {
        # 38 Sintéticos continuos 24/7 sin sesión de apertura bursátil NY
        "Crash 300 Index", "Crash 500 Index", "Crash 600 Index", "Crash 900 Index", "Crash 1000 Index",
        "Boom 300 Index", "Boom 500 Index", "Boom 600 Index", "Boom 900 Index", "Boom 1000 Index",
        "Step Index", "Step Index 200", "Step Index 400", "Step Index 500",
        "Jump 10 Index", "Jump 25 Index", "Jump 50 Index", "Jump 75 Index", "Jump 100 Index",
        "Volatility 5 Index", "Volatility 10 Index", "Volatility 15 Index", "Volatility 25 Index",
        "Volatility 50 Index", "Volatility 75 Index", "Volatility 90 Index", "Volatility 100 Index",
        "Volatility 50 (1s) Index", "Volatility 75 (1s) Index", "Volatility 90 (1s) Index",
        "Volatility 100 (1s) Index", "Volatility 150 (1s) Index", "Volatility 250 (1s) Index",
        "Vol over Boom 550", "Vol over Crash 550", "VolSwitch High Vol Index",
        "High Frequency Vol 50 Index", "High Frequency Vol 100 Index",
        # Cruces FX sin volumen institucional en apertura de NY
        "AUDCAD", "AUDCHF", "AUDJPY", "AUDNZD", "CADCHF", "CADJPY", "CHFJPY",
        "EURAUD", "EURCAD", "EURCHF", "EURGBP", "EURJPY", "EURNZD", "GBPAUD",
        "GBPCAD", "GBPCHF", "GBPJPY", "GBPNZD",
    },
}


# 11-nov-2026: los cruces Forex con WR >= 50 % en /Strategy-bases (ICT) dejan de estar en Poda Estricta.
# DAEMONBLACKFX_ICT_FOREX_50_RESCUE=0 los devuelve al veto (misma variable que config/ict_instrument_policy.py).
try:
    from config.ict_instrument_policy import ICT_FOREX_50_RESCUED_BASES as _ICT_FOREX_50_RESCUED
except Exception:  # pragma: no cover - el gate no debe depender de la política para importarse
    _ICT_FOREX_50_RESCUED = ()
if _ICT_FOREX_50_RESCUED:
    STRICT_PRUNED_ASSETS_BY_STRATEGY["ICT"] = set(STRICT_PRUNED_ASSETS_BY_STRATEGY["ICT"]) - set(_ICT_FOREX_50_RESCUED)


def canonical_symbol(sym: str) -> str:
    """Normaliza sufijos y prefijos de cuentas micro o alias broker (ej. EURUSDmicro -> EURUSD)."""
    s = str(sym or "").strip()
    if s.lower().startswith("micro"):
        s = s[5:]
    if s.lower().endswith("micro"):
        s = s[:-5]
    return s


def normalize_strategy_key(strat: str) -> str:
    """Normaliza nombres legados y variantes a la clave canónica de estrategia."""
    s = str(strat or "").upper().strip()
    if "ICT" in s or "SABRI" in s or s == "SMC":
        return "ICT"
    if "MALAYSIAN" in s or "SNR" in s:
        return "MALAYSIAN_SNR"
    if "ORB" in s:
        return "ORB"
    if "PULLBACK" in s or "TREND" in s:
        return "TREND_PULLBACK"
    # Mapeo de perfiles de workers sintéticos y forex que ejecutan ICT por defecto
    if s in {
        "BOOM", "CRASH", "STEP", "JUMP", "VOLATILITY",
        "VOLATILITY_1", "VOLATILITY_2", "VOLATILITY_3", "VOLATILITY_4",
        "FOREX", "FOREX_1", "FOREX_2", "FOREX_3", "FOREX_4", "FOREX_5",
        "SYNTHETICS", "COMMODITIES", "CRYPTO", "INDICES",
    }:
        return "ICT"
    return s


@dataclass
class TripartiteConfluenceConfig:
    """Configuración con interruptores por variable de entorno para Confluencia Tripartita."""

    # Interruptor Maestro
    enabled: bool = field(
        default_factory=lambda: os.getenv("DAEMONBLACKFX_TRIPARTITE_CONFLUENCE_ENABLED", "1").strip().lower()
        not in ("0", "false", "off", "no")
    )
    # Interruptores por Pilar
    human_criteria_active: bool = field(
        default_factory=lambda: os.getenv("DAEMONBLACKFX_TRIPARTITE_HUMAN_CRITERIA_ACTIVE", "1").strip().lower()
        not in ("0", "false", "off", "no")
    )
    ai_filter_active: bool = field(
        default_factory=lambda: os.getenv("DAEMONBLACKFX_TRIPARTITE_AI_FILTER_ACTIVE", "1").strip().lower()
        not in ("0", "false", "off", "no")
    )
    rehabilitated_assets_enabled: bool = field(
        default_factory=lambda: os.getenv("DAEMONBLACKFX_TRIPARTITE_REHABILITATED_ENABLED", "1").strip().lower()
        not in ("0", "false", "off", "no")
    )

    # Parámetros Cuantitativos de Validación
    min_ai_probability: float = field(
        default_factory=lambda: float(os.getenv("DAEMONBLACKFX_TRIPARTITE_MIN_AI_PROB", "0.50"))
    )
    min_ai_net_expectancy_r: float = field(
        default_factory=lambda: float(os.getenv("DAEMONBLACKFX_TRIPARTITE_MIN_AI_EXP_R", "0.02"))
    )
    anti_spike_shield_enabled: bool = field(
        default_factory=lambda: os.getenv("DAEMONBLACKFX_TRIPARTITE_ANTI_SPIKE", "1").strip().lower()
        not in ("0", "false", "off", "no")
    )
    max_climax_candle_body_ratio: float = field(
        default_factory=lambda: float(os.getenv("DAEMONBLACKFX_TRIPARTITE_MAX_BODY_RATIO", "0.85"))
    )
    min_adx_regime: float = field(
        default_factory=lambda: float(os.getenv("DAEMONBLACKFX_TRIPARTITE_MIN_ADX", "20.0"))
    )
    # Umbral compensatorio de Criterio Humano cuando la IA no está disponible
    min_human_score_without_ai: float = field(
        default_factory=lambda: float(os.getenv("DAEMONBLACKFX_TRIPARTITE_HUMAN_MIN_SCORE_NO_AI", "80.0"))
    )
    require_ai_strict: bool = field(
        default_factory=lambda: os.getenv("DAEMONBLACKFX_TRIPARTITE_REQUIRE_AI_STRICT", "0").strip().lower() in ("1", "true", "yes")
    )
    canonical_symbol_matching_enabled: bool = field(
        default_factory=lambda: os.getenv("DAEMONBLACKFX_TRIPARTITE_CANONICAL_SYMBOL", "1").strip().lower()
        not in ("0", "false", "off", "no")
    )


@dataclass
class TripartiteDecision:
    """Resultado estructurado de la evaluación del Gatillo de Confluencia Tripartita."""

    allowed: bool
    action: str  # "APPROVED", "VETO_HUMAN_CRITERIA", "VETO_AI_FILTER", "VETO_STRICT_PRUNING", "BYPASS"
    reason: str
    strategy_pillar_ok: bool = True
    human_criteria_pillar_ok: bool = True
    ai_filter_pillar_ok: bool = True
    ai_probability: float = 0.0
    human_criteria_score: float = 0.0
    is_rehabilitated_asset: bool = False
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "action": self.action,
            "reason": self.reason,
            "strategy_pillar_ok": self.strategy_pillar_ok,
            "human_criteria_pillar_ok": self.human_criteria_pillar_ok,
            "ai_filter_pillar_ok": self.ai_filter_pillar_ok,
            "ai_probability": round(self.ai_probability, 4),
            "human_criteria_score": round(self.human_criteria_score, 2),
            "is_rehabilitated_asset": self.is_rehabilitated_asset,
            "details": self.details,
        }


class TripartiteConfluenceGate:
    """Motor evaluador del Gatillo de Confluencia Tripartita (Estrategia + Criterio Humano + Filtro Activo de IA)."""

    def __init__(self, config: Optional[TripartiteConfluenceConfig] = None):
        self.config = config or TripartiteConfluenceConfig()

    def evaluate_confluence(
        self,
        *,
        symbol: str,
        strategy_name: str,
        direction: str,
        signal: Dict[str, Any],
        human_criteria_decision: Optional[Any] = None,
        ai_evaluation: Optional[Dict[str, Any]] = None,
        candle_body_ratio: Optional[float] = None,
        adx_value: Optional[float] = None,
        is_spike_danger: bool = False,
    ) -> TripartiteDecision:
        """Evalúa un trade bajo la estricta confluencia de los 3 pilares."""
        # 1. Si el interruptor maestro está apagado -> Zero Breaking Changes (Bypass transparente)
        if not self.config.enabled:
            return TripartiteDecision(
                allowed=True,
                action="BYPASS",
                reason="Confluencia Tripartita desactivada por interruptor de configuración (Modo Bypass).",
                strategy_pillar_ok=True,
                human_criteria_pillar_ok=True,
                ai_filter_pillar_ok=True,
            )

        strat_key = normalize_strategy_key(strategy_name)
        sym_clean = symbol.strip()
        sym_canon = canonical_symbol(sym_clean) if self.config.canonical_symbol_matching_enabled else sym_clean

        # 2. Comprobación de Activos en Poda Estricta / Incompatibles
        strict_pruned = STRICT_PRUNED_ASSETS_BY_STRATEGY.get(strat_key, set())
        is_pruned = sym_clean in strict_pruned or (self.config.canonical_symbol_matching_enabled and sym_canon in strict_pruned)
        if is_pruned:
            return TripartiteDecision(
                allowed=False,
                action="VETO_STRICT_PRUNING",
                reason=f"Activo '{sym_clean}' se encuentra en Poda Estricta/Incompatible para '{strat_key}' (Fricción de spread o sin horario de mercado).",
                strategy_pillar_ok=False,
                human_criteria_pillar_ok=False,
                ai_filter_pillar_ok=False,
            )

        # 3. Comprobación de Activos Rehabilitados
        rehab_assets = REHABILITATED_ASSETS_BY_STRATEGY.get(strat_key, set())
        is_rehab = sym_clean in rehab_assets or (self.config.canonical_symbol_matching_enabled and sym_canon in rehab_assets)
        if is_rehab and not self.config.rehabilitated_assets_enabled:
            return TripartiteDecision(
                allowed=False,
                action="VETO_REHABILITATION_DISABLED",
                reason=f"Activo rehabilitado '{sym_clean}' bloqueado porque el interruptor de rehabilitación está desactivado.",
                is_rehabilitated_asset=True,
            )

        # 4. Pilar 1: Estrategia Base (SMC / ICT, MSNR, ORB)
        # La señal debe traer Stop Loss y Take Profit numéricos consistentes
        sl = (
            signal.get("stop_loss")
            or signal.get("sl")
            or signal.get("stop")
            or signal.get("sl_price")
            or signal.get("stop_price")
            or signal.get("stop_loss_price")
        )
        tp = (
            signal.get("take_profit")
            or signal.get("tp")
            or signal.get("tp1")
            or signal.get("tp1_price")
            or signal.get("tp2_price")
            or signal.get("target_price")
            or signal.get("take_profit_price")
            or signal.get("risk_reward_ratio")
            or signal.get("planned_rr")
            or signal.get("runner_rr")
            or signal.get("tp_price")
        )
        if sl is None or tp is None:
            return TripartiteDecision(
                allowed=False,
                action="VETO_STRATEGY_PILLAR",
                reason="Pilar 1 (Estrategia) no cumplido: Faltan niveles de SL o TP en la señal.",
                strategy_pillar_ok=False,
            )

        # 5. Pilar 2: Criterio Humano (ADX, Clímax, Anti-Spike, Decisión de HumanCriteriaEngine)
        human_ok = True
        human_score = 75.0
        human_reason = "Aprobado por Criterio Humano"

        if self.config.human_criteria_active:
            # A. Escudo Anti-Spike en Sintéticos Crash / Boom
            if self.config.anti_spike_shield_enabled and is_spike_danger:
                return TripartiteDecision(
                    allowed=False,
                    action="VETO_HUMAN_CRITERIA_ANTI_SPIKE",
                    reason=f"Escudo Anti-Spike activado: Riesgo inminente de descarga en contra de la posición en '{sym_clean}'.",
                    human_criteria_pillar_ok=False,
                    is_rehabilitated_asset=is_rehab,
                )

            # B. Filtro de Vela Clímax (Evitar agotamiento de rango)
            if candle_body_ratio is not None and candle_body_ratio > self.config.max_climax_candle_body_ratio:
                return TripartiteDecision(
                    allowed=False,
                    action="VETO_HUMAN_CRITERIA_CLIMAX",
                    reason=f"Filtro de Clímax activado: Vela M15 sobreextendida (cuerpo {candle_body_ratio:.1%} > {self.config.max_climax_candle_body_ratio:.1%}).",
                    human_criteria_pillar_ok=False,
                    is_rehabilitated_asset=is_rehab,
                )

            # C. Filtro de Régimen ADX (Evitar chop lateral)
            if adx_value is not None and adx_value < self.config.min_adx_regime:
                return TripartiteDecision(
                    allowed=False,
                    action="VETO_HUMAN_CRITERIA_ADX",
                    reason=f"Filtro de Régimen activado: ADX insuficiente ({adx_value:.1f} < {self.config.min_adx_regime:.1f}) indicando chop lateral.",
                    human_criteria_pillar_ok=False,
                    is_rehabilitated_asset=is_rehab,
                )

            # D. Decisión del HumanCriteriaEngine si fue evaluado (soporta objeto o dict)
            if human_criteria_decision is not None:
                is_hc_dict = isinstance(human_criteria_decision, dict)
                hc_allowed = (
                    human_criteria_decision.get("allowed", True)
                    if is_hc_dict
                    else getattr(human_criteria_decision, "allowed", True)
                )
                hc_score = (
                    human_criteria_decision.get("score")
                    if is_hc_dict
                    else getattr(human_criteria_decision, "score", None)
                )
                hc_reason = (
                    human_criteria_decision.get("reason", "Rechazado por Criterio Humano")
                    if is_hc_dict
                    else getattr(human_criteria_decision, "reason", "Rechazado por Criterio Humano")
                )

                if not hc_allowed:
                    return TripartiteDecision(
                        allowed=False,
                        action="VETO_HUMAN_CRITERIA",
                        reason=str(hc_reason),
                        human_criteria_pillar_ok=False,
                        human_criteria_score=float(hc_score if hc_score is not None else 0.0),
                        is_rehabilitated_asset=is_rehab,
                    )
                if hc_score is not None:
                    try:
                        human_score = float(hc_score)
                    except (ValueError, TypeError):
                        pass

        # 6. Pilar 3: Filtro Activo de IA (Meta-Labeling)
        ai_ok = True
        ai_prob = 0.0
        ai_status = "EVALUATED"
        if self.config.ai_filter_active:
            if ai_evaluation is None:
                ai_status = "AI_INFERENCE_UNAVAILABLE"
                if self.config.require_ai_strict:
                    return TripartiteDecision(
                        allowed=False,
                        action="VETO_AI_FILTER_UNAVAILABLE",
                        reason="Filtro Activo de IA activado y modo estricto: inferencia de IA no disponible para la señal.",
                        strategy_pillar_ok=True,
                        human_criteria_pillar_ok=True,
                        ai_filter_pillar_ok=False,
                        ai_probability=0.0,
                        human_criteria_score=human_score,
                        is_rehabilitated_asset=is_rehab,
                    )
                # Modo humanizado: compensación por Criterio Humano reforzado
                if human_score < self.config.min_human_score_without_ai:
                    return TripartiteDecision(
                        allowed=False,
                        action="VETO_INSUFFICIENT_CONFLUENCE_WITHOUT_AI",
                        reason=(
                            f"Filtro de Confluencia: IA no disponible y Criterio Humano ({human_score:.1f}) "
                            f"inferior al umbral reforzado de compensación ({self.config.min_human_score_without_ai:.1f})."
                        ),
                        strategy_pillar_ok=True,
                        human_criteria_pillar_ok=False,
                        ai_filter_pillar_ok=False,
                        ai_probability=0.0,
                        human_criteria_score=human_score,
                        is_rehabilitated_asset=is_rehab,
                    )
                ai_prob = 0.50  # Neutro transparente para auditoría
            else:
                if isinstance(ai_evaluation, dict):
                    ai_prob = float(ai_evaluation.get("probability", 0.50))
                    ai_exp_r = float(ai_evaluation.get("net_expectancy_r", 0.05))
                else:
                    ai_prob = float(getattr(ai_evaluation, "probability", 0.50))
                    ai_exp_r = float(getattr(ai_evaluation, "net_expectancy_r", 0.05))

                if ai_prob < self.config.min_ai_probability:
                    return TripartiteDecision(
                        allowed=False,
                        action="VETO_AI_FILTER_PROBABILITY",
                        reason=f"Filtro Activo de IA activado: Probabilidad prevista P(Win)={ai_prob:.1%} inferior al umbral mínimo {self.config.min_ai_probability:.1%}.",
                        strategy_pillar_ok=True,
                        human_criteria_pillar_ok=True,
                        ai_filter_pillar_ok=False,
                        ai_probability=ai_prob,
                        human_criteria_score=human_score,
                        is_rehabilitated_asset=is_rehab,
                    )

                if ai_exp_r < self.config.min_ai_net_expectancy_r:
                    return TripartiteDecision(
                        allowed=False,
                        action="VETO_AI_FILTER_EXPECTANCY",
                        reason=f"Filtro Activo de IA activado: Expectativa neta {ai_exp_r:.3f} R inferior al umbral mínimo {self.config.min_ai_net_expectancy_r:.3f} R.",
                        strategy_pillar_ok=True,
                        human_criteria_pillar_ok=True,
                        ai_filter_pillar_ok=False,
                        ai_probability=ai_prob,
                        human_criteria_score=human_score,
                        is_rehabilitated_asset=is_rehab,
                    )

        # 7. APROBACIÓN TRIPARTITA
        approval_ai_text = f"IA P(Win)={ai_prob:.1%}" if ai_status == "EVALUATED" else "IA=No disponible (Compensado Criterio Humano)"
        return TripartiteDecision(
            allowed=True,
            action="APPROVED",
            reason=(
                f"Aprobado por Confluencia Tripartita: Estrategia={strat_key}, "
                f"Criterio Humano Score={human_score:.1f}, {approval_ai_text}"
                + (" [ACTIVO REHABILITADO]" if is_rehab else "")
            ),
            strategy_pillar_ok=True,
            human_criteria_pillar_ok=True,
            ai_filter_pillar_ok=True,
            ai_probability=ai_prob,
            human_criteria_score=human_score,
            is_rehabilitated_asset=is_rehab,
            details={
                "strategy": strat_key,
                "symbol": sym_clean,
                "direction": direction,
                "rehabilitated": is_rehab,
            },
        )
