"""Motor de Subasta Competitiva de Estrategias (Competitive Strategy Auction Engine).

Resuelve la competencia objetiva entre múltiples generadores de alfa
(específicamente ICT y Malaysian SNR) cuando operan sobre el mismo universo de activos:

1. Evaluación Paralela: Ambos candidatos son analizados independientemente.
2. Filtro de Restricción Direccional: Respeta restricciones de activos asimétricos
   (ej. Boom BUY only, Crash SELL only, Ladder Down SELL only).
3. Calificación de Confluencia Objetiva:
   Evalúa el Confluence Score (0 a 100) y Grado (A, B+, B, C) mediante HumanCriteriaEngine.
4. Reglas de Despacho al Broker:
   - Si ambas estrategias tienen señal activa y coinciden en dirección:
     ¡SÚPER-CONFLUENCIA! Se bonifica la puntuación (+5 pts) y se selecciona la mejor relación R:R.
   - Si ambas tienen señal activa y discrepan en dirección (ICT Buy vs MSNR Sell):
     VETO preventivo por conflicto direccional o prevalencia de marco mayor (D1/H1 vs M5).
   - Si compiten en la misma dirección o una sola es válida:
     Gana la estrategia con mayor Confluence Score que supere el umbral institucional
     (>= 75 pts en sintéticos / >= 65 pts en reales).
   - Si ninguna tiene señal de mercado inmediata (ambas en radar):
     Conserva la estructura macro de Malaysian SNR (ej. espera de retest) sin ocultarla
     detrás del ciclo M5 de ICT, emitiendo un estado combinado para la Matriz Centinela.

Zero Breaking Changes:
- Si DAEMONBLACKFX_COMPETITIVE_STRATEGY_AUCTION=0, recurre de forma transparente
  al despacho legado (first-valid-match).
"""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from strategy.human_criteria.human_criteria_engine import (
    HumanCriteriaDecision,
    HumanCriteriaEngine,
    classify_symbol_category,
)


@dataclass
class StrategyAuctionConfig:
    """Configuración del motor de subasta competitiva."""

    enabled: bool = field(
        default_factory=lambda: os.getenv("DAEMONBLACKFX_COMPETITIVE_STRATEGY_AUCTION", "1").strip().lower()
        not in ("0", "false", "off", "no")
    )
    synthetic_min_score: float = field(
        default_factory=lambda: float(os.getenv("DAEMONBLACKFX_AUCTION_SYNTHETIC_MIN_SCORE", "75.0"))
    )
    real_min_score: float = field(
        default_factory=lambda: float(os.getenv("DAEMONBLACKFX_AUCTION_REAL_MIN_SCORE", "65.0"))
    )
    direction_conflict_veto: bool = field(
        default_factory=lambda: os.getenv("DAEMONBLACKFX_AUCTION_CONFLICT_VETO", "1").strip().lower()
        not in ("0", "false", "off", "no")
    )
    cross_strategy_bonus: float = field(
        default_factory=lambda: float(os.getenv("DAEMONBLACKFX_AUCTION_CROSS_STRAT_BONUS", "5.0"))
    )
    prefer_htf_on_tie: bool = True


@dataclass
class CandidateEvaluation:
    """Evaluación técnica y de confluencia de una estrategia candidata."""

    strategy_name: str
    is_valid: bool
    action: str
    direction: str | None
    signal: dict[str, Any] | None
    score: float = 0.0
    grade: str = "GRADE_C_SUBPAR"
    allowed_by_human_criteria: bool = True
    disqualified: bool = False
    disqualification_reason: str | None = None
    radar_description: str | None = None
    raw_analysis: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "strategy_name": self.strategy_name,
            "is_valid": self.is_valid,
            "action": self.action,
            "direction": self.direction,
            "score": round(self.score, 2),
            "grade": self.grade,
            "allowed_by_human_criteria": self.allowed_by_human_criteria,
            "disqualified": self.disqualified,
            "disqualification_reason": self.disqualification_reason,
            "radar_description": self.radar_description,
        }


def extract_signal_direction(analysis: dict[str, Any] | None) -> str | None:
    """Extrae la dirección normalizada ('BUY' o 'SELL') de una señal o análisis."""
    if not isinstance(analysis, dict):
        return None
    signal = analysis.get("signal") or analysis.get("entry") or {}
    direction = signal.get("direction") or analysis.get("action")
    if not direction:
        return None
    d = str(direction).strip().upper()
    if d in ("BUY", "LONG"):
        return "BUY"
    if d in ("SELL", "SHORT"):
        return "SELL"
    return None


def extract_radar_description(strategy_name: str, analysis: dict[str, Any] | None) -> str:
    """Genera una descripción humana del estado de radar cuando no hay gatillo activo."""
    if not isinstance(analysis, dict):
        return "Inactivo"
    
    strat_upper = str(strategy_name).upper()
    reason = str(analysis.get("reason") or "")
    action = str(analysis.get("action") or "")

    if "MALAYSIAN" in strat_upper or "SNR" in strat_upper:
        scenario = str(analysis.get("scenario") or "")
        retest_rem = analysis.get("retest_remaining_minutes") or analysis.get("retest_time_left")
        if retest_rem is not None:
            try:
                rem_val = float(retest_rem)
                if rem_val > 60:
                    return f"Retest Macro: ~{rem_val / 60.0:.1f} h restantes ({scenario or 'Ruptura'})"
                return f"Retest Próximo: ~{rem_val:.0f} min restantes ({scenario or 'Ruptura'})"
            except (ValueError, TypeError):
                pass
        if scenario:
            return f"Monitoreo Nivel ({scenario})"
        if "RETEST" in reason:
            return "Esperando Retest H1/D1"
        return "Monitoreando Estructura SNR"

    if "ICT" in strat_upper:
        if "SWEEP" in reason or "LIQUIDITY" in reason:
            return "Caza de Liquidez / FVG M5"
        if "JUDAS" in reason or "AMD" in reason:
            return "Esperando Desplazamiento Judas M5"
        if "FVG" in reason:
            return "Esperando Mitigación FVG M5"
        return "Escaneando Liquidez / FVG M5"

    return action or reason or "En Radar"


def evaluate_candidate_confluence(
    symbol: str,
    strategy_name: str,
    analysis: dict[str, Any] | None,
    direction_constraint: str | None,
    human_criteria_engine: HumanCriteriaEngine | None,
    now_utc: datetime | None = None,
) -> CandidateEvaluation:
    """Audita técnicamente a un candidato y calcula su puntuación de confluencia."""
    if not isinstance(analysis, dict):
        return CandidateEvaluation(
            strategy_name=strategy_name,
            is_valid=False,
            action="NO_DATA",
            direction=None,
            signal=None,
            score=0.0,
            grade="GRADE_C_SUBPAR",
            radar_description="Sin datos de análisis",
            raw_analysis={},
        )

    is_valid = bool(analysis.get("valid", False))
    action = str(analysis.get("action") or ("BUY" if is_valid else "NO_SIGNAL")).upper()
    direction = extract_signal_direction(analysis)
    signal = analysis.get("signal") or analysis.get("entry")
    radar_desc = extract_radar_description(strategy_name, analysis)

    cand = CandidateEvaluation(
        strategy_name=strategy_name,
        is_valid=is_valid,
        action=action,
        direction=direction,
        signal=signal if isinstance(signal, dict) else None,
        radar_description=radar_desc,
        raw_analysis=analysis,
    )

    # 1. Filtro de Restricción Direccional (ej. Crash SELL only, Boom BUY only)
    if direction_constraint is not None and is_valid:
        req_dir = str(direction_constraint).strip().upper()
        if direction != req_dir:
            cand.disqualified = True
            cand.disqualification_reason = f"VIOLATION_{req_dir}_ONLY_CONSTRAINT"
            cand.is_valid = False
            return cand

    # 2. Si no es válido para entrada inmediata, no requiere scoring completo de ejecución
    if not is_valid or not cand.signal or not direction:
        return cand

    # 3. Puntuación mediante HumanCriteriaEngine
    if human_criteria_engine is not None and bool(getattr(human_criteria_engine.config, "enabled", True)):
        try:
            # Asegurar que el nombre de estrategia esté explícito en la señal
            eval_signal = dict(cand.signal)
            eval_signal.setdefault("strategy_name", strategy_name)

            decision: HumanCriteriaDecision = human_criteria_engine.evaluate_candidate(
                symbol=symbol,
                direction=direction,
                signal=eval_signal,
                current_time=now_utc or datetime.now(timezone.utc),
            )
            cand.score = float(decision.score)
            cand.grade = str(decision.grade)
            cand.allowed_by_human_criteria = bool(decision.allowed)
            if not decision.allowed:
                cand.disqualified = True
                cand.disqualification_reason = f"HUMAN_CRITERIA_VETO: {decision.reason}"
        except Exception as e:
            # Tolerancia a fallos: fallback a score neutro si la evaluación de criterio humano falla
            cand.score = float(cand.signal.get("confluence_score") or 70.0)
            cand.grade = "GRADE_B_CAUTIOUS"
    else:
        # Puntuación interna o fallback
        cand.score = float(cand.signal.get("confluence_score") or 75.0)
        cand.grade = "GRADE_B_CAUTIOUS" if cand.score < 80 else "GRADE_A_ELITE"

    return cand


def resolve_competitive_strategy_auction(
    symbol: str,
    msnr_analysis: dict[str, Any] | None,
    ict_analysis: dict[str, Any] | None,
    direction_constraint: str | None = None,
    human_criteria_engine: HumanCriteriaEngine | None = None,
    config: StrategyAuctionConfig | None = None,
    now_utc: datetime | None = None,
) -> dict[str, Any]:
    """Resuelve la subasta competitiva entre Malaysian SNR e ICT.

    Devuelve el diccionario `analysis` ganador listo para su despacho o registro,
    enriquecido con los metadatos de la subasta (`auction_metadata`).
    """
    cfg = config or StrategyAuctionConfig()

    # MODO BYPASS: Compatibilidad retroactiva 100% fiel
    if not cfg.enabled:
        if msnr_analysis and msnr_analysis.get("valid"):
            if direction_constraint is None or extract_signal_direction(msnr_analysis) == direction_constraint:
                res = dict(msnr_analysis)
                res["strategy_name"] = "MALAYSIAN_SNR"
                res["context_policy"] = "MALAYSIAN_SNR_NATIVE"
                return res
        if ict_analysis:
            res = dict(ict_analysis)
            res["strategy_name"] = "ICT"
            res["context_policy"] = "ICT_NATIVE"
            if direction_constraint and res.get("valid") and extract_signal_direction(res) != direction_constraint:
                res["valid"] = False
                res["reason"] = f"{direction_constraint}_ONLY_VIOLATION"
            return res
        return {
            "valid": False,
            "symbol": symbol,
            "action": "NO_SIGNAL",
            "strategy_name": "MULTI_STRATEGY",
        }

    # Evaluar ambos candidatos independientemente
    cand_msnr = evaluate_candidate_confluence(
        symbol=symbol,
        strategy_name="MALAYSIAN_SNR",
        analysis=msnr_analysis,
        direction_constraint=direction_constraint,
        human_criteria_engine=human_criteria_engine,
        now_utc=now_utc,
    )

    cand_ict = evaluate_candidate_confluence(
        symbol=symbol,
        strategy_name="ICT",
        analysis=ict_analysis,
        direction_constraint=direction_constraint,
        human_criteria_engine=human_criteria_engine,
        now_utc=now_utc,
    )

    category = classify_symbol_category(symbol)
    min_score_threshold = cfg.synthetic_min_score if category == "SYNTHETIC" else cfg.real_min_score

    msnr_passes = (
        cand_msnr.is_valid
        and not cand_msnr.disqualified
        and cand_msnr.allowed_by_human_criteria
        and cand_msnr.score >= (min_score_threshold - 5.0)  # MSNR tiene tolerancia estructural de 5 pts
    )

    ict_passes = (
        cand_ict.is_valid
        and not cand_ict.disqualified
        and cand_ict.allowed_by_human_criteria
        and cand_ict.score >= min_score_threshold
    )

    auction_meta: dict[str, Any] = {
        "auction_enabled": True,
        "symbol": symbol,
        "evaluated_at": (now_utc or datetime.now(timezone.utc)).isoformat(),
        "candidates": {
            "MALAYSIAN_SNR": cand_msnr.to_dict(),
            "ICT": cand_ict.to_dict(),
        },
        "winner_strategy": None,
        "winner_score": 0.0,
        "winner_grade": None,
        "cross_strategy_confluence": False,
        "direction_conflict": False,
        "decision_reason": None,
    }

    # =========================================================================
    # CASO 1: AMBAS ESTRATEGIAS TIENEN SEÑAL ACTIVA Y CALIFICADA
    # =========================================================================
    if msnr_passes and ict_passes:
        # A. Comprobación de conflicto direccional
        if cand_msnr.direction != cand_ict.direction:
            auction_meta["direction_conflict"] = True
            if cfg.direction_conflict_veto:
                auction_meta["decision_reason"] = (
                    f"VETO_DIRECTION_CONFLICT: Malaysian SNR propone {cand_msnr.direction} (H1/D1) "
                    f"mientras ICT propone {cand_ict.direction} (M5). Trade cancelado por seguridad institucional."
                )
                res = {
                    "valid": False,
                    "symbol": symbol,
                    "strategy_name": "MULTI_STRATEGY",
                    "action": "VETO_DIRECTION_CONFLICT",
                    "reason": auction_meta["decision_reason"],
                    "auction_metadata": auction_meta,
                }
                return res
            elif cfg.prefer_htf_on_tie:
                # Prevalencia del marco temporal macro (MSNR D1/H1 sobre ICT M5)
                winning_cand = cand_msnr
                auction_meta["decision_reason"] = "Resolución por jerarquía macro HTF (MSNR D1/H1 > ICT M5)"
            else:
                winning_cand = cand_msnr if cand_msnr.score >= cand_ict.score else cand_ict
        else:
            # B. SÚPER-CONFLUENCIA CRUZADA (Ambas en la misma dirección)
            auction_meta["cross_strategy_confluence"] = True
            cand_msnr.score += cfg.cross_strategy_bonus
            cand_ict.score += cfg.cross_strategy_bonus
            auction_meta["decision_reason"] = (
                f"SÚPER-CONFLUENCIA: ICT y Malaysian SNR coinciden en {cand_msnr.direction}. "
                f"Bonificación de +{cfg.cross_strategy_bonus:.1f} pts aplicada."
            )
            # Seleccionar la que ofrezca mayor score o mejor ratio R:R
            if cand_msnr.score >= cand_ict.score:
                winning_cand = cand_msnr
            else:
                winning_cand = cand_ict

        return _build_winning_response(winning_cand, auction_meta)

    # =========================================================================
    # CASO 2: EXACTAMENTE UNA ESTRATEGIA CALIFICA PARA ENTRADA
    # =========================================================================
    if msnr_passes and not ict_passes:
        auction_meta["decision_reason"] = "Malaysian SNR califica para ejecución; ICT no presenta gatillo activo."
        return _build_winning_response(cand_msnr, auction_meta)

    if ict_passes and not msnr_passes:
        auction_meta["decision_reason"] = "ICT califica para ejecución; Malaysian SNR no presenta gatillo activo."
        return _build_winning_response(cand_ict, auction_meta)

    # =========================================================================
    # CASO 3: UNA O AMBAS TIENEN SEÑAL PERO NO ALCANZAN EL UMBRAL DE CALIDAD
    # =========================================================================
    if cand_msnr.is_valid or cand_ict.is_valid:
        rejection_reasons = []
        if cand_msnr.is_valid:
            rejection_reasons.append(f"MSNR ({cand_msnr.score:.1f} pts < {min_score_threshold - 5.0:.1f})")
        if cand_ict.is_valid:
            rejection_reasons.append(f"ICT ({cand_ict.score:.1f} pts < {min_score_threshold:.1f})")

        auction_meta["decision_reason"] = f"REJECTED_AUCTION_SUBPAR_SCORE: {', '.join(rejection_reasons)}"
        return {
            "valid": False,
            "symbol": symbol,
            "strategy_name": "MULTI_STRATEGY",
            "action": "AUCTION_SCORES_SUBPAR",
            "reason": auction_meta["decision_reason"],
            "auction_metadata": auction_meta,
        }

    # =========================================================================
    # CASO 4: NINGUNA TIENE GATILLO INMEDIATO (AMBAS EN RADAR / OBSERVACIÓN)
    # =========================================================================
    # Determinamos el ancla estructural principal:
    # Si Malaysian SNR tiene un nivel macro identificado (Break/Retest activo),
    # prevalece la estructura macro de MSNR en lugar de esconderse tras ICT.
    has_msnr_radar = bool(
        cand_msnr.raw_analysis.get("scenario")
        or cand_msnr.raw_analysis.get("setup_id")
        or "RETEST" in str(cand_msnr.raw_analysis.get("reason") or "").upper()
    )

    if has_msnr_radar:
        res = dict(cand_msnr.raw_analysis)
        res["strategy_name"] = "MALAYSIAN_SNR"
        res["context_policy"] = "MALAYSIAN_SNR_NATIVE"
        res["auction_metadata"] = auction_meta
        auction_meta["decision_reason"] = "Radar anclado en nivel estructural macro Malaysian SNR."
        return res

    # Si MSNR no tiene nivel activo, usar el escaneo de ICT
    if ict_analysis:
        res = dict(cand_ict.raw_analysis)
        res["strategy_name"] = "ICT"
        res["context_policy"] = "ICT_NATIVE"
        res["auction_metadata"] = auction_meta
        auction_meta["decision_reason"] = "Radar anclado en microestructura ICT M5."
        return res

    return {
        "valid": False,
        "symbol": symbol,
        "strategy_name": "MULTI_STRATEGY",
        "action": "NO_SIGNAL",
        "reason": "Ambas estrategias en radar neutral",
        "auction_metadata": auction_meta,
    }


def _build_winning_response(winner: CandidateEvaluation, auction_meta: dict[str, Any]) -> dict[str, Any]:
    """Construye el dict `analysis` enriquecido para la estrategia ganadora."""
    res = dict(winner.raw_analysis)
    res["valid"] = True
    res["strategy_name"] = winner.strategy_name
    res["context_policy"] = f"{winner.strategy_name}_NATIVE"

    auction_meta["winner_strategy"] = winner.strategy_name
    auction_meta["winner_score"] = round(winner.score, 2)
    auction_meta["winner_grade"] = winner.grade
    res["auction_metadata"] = auction_meta

    # Enriquecer la señal interna con los metadatos de la subasta
    signal = res.get("signal") or res.get("entry")
    if isinstance(signal, dict):
        signal["strategy_name"] = winner.strategy_name
        signal["auction_metadata"] = auction_meta
        signal["confluence_score"] = round(winner.score, 2)
        signal["confluence_grade"] = winner.grade

    return res
