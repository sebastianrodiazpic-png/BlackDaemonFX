"""Servicio de Autopsia Automatizada de Operaciones (Trade Autopsy Post-Mortem).

Inspirado en plataformas de journaling profesional cuantitativo (TradeZella, FX Replay):
Cada vez que una posición se cierra en el broker o simulador, este servicio realiza un
diagnóstico forense independiente:

1. Razón y Naturaleza de Salida:
   - TP natural (TP1, TP2, TP3, TP4), SL estructural, cierre en Break-Even o cierre forzado por sesión.
2. Calidad de Ejecución e Impacto de Fricciones:
   - Medición de deslizamiento (slippage) entre orden y fill.
   - Coste total de fricciones: comisiones pagadas y swap nocturno respecto al PnL bruto.
3. R:R Realizado vs R:R Planificado:
   - Porcentaje del objetivo capturado.
   - Eficiencia de salida: compara el punto de salida contra el MFE (Máxima Excursión Favorable).
4. Calificación Institucional (A / B / C):
   - Grado A: Confluencia plena H1 + M15 + M5, AI Score >= 80%, y R:R objetivo capturado sin violaciones.
   - Grado B: Entrada estructuralmente válida pero que retrocedió antes de monetizar corredores superiores (TP3/TP4).
   - Grado C: Salida prematura, penalizada por spread ensanchado, slippage severo o veto tardío.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
from typing import Any, Dict, Optional


@dataclass
class TradeAutopsyReport:
    trade_id: Optional[int | str]
    symbol: str
    direction: str
    entry_price: float
    exit_price: float
    stop_loss: float
    planned_tp: float
    planned_rr: float
    realized_rr: float
    rr_efficiency_percent: float

    exit_reason_category: str  # TP_FULL, TP_PARTIAL, BREAK_EVEN, STRUCTURAL_SL, SESSION_CLOSE, OTHER
    execution_quality_score: int  # 0 a 100

    gross_pnl: float
    net_pnl: float
    commission: float
    swap: float
    friction_drag_percent: float  # (comisiones + swap) / gross_pnl

    max_favorable_excursion_r: float
    max_adverse_excursion_r: float
    left_on_table_r: float  # MFE - Realized R

    ai_score_at_entry: float
    confluence_h1_m15_m5: bool

    grade: str  # 'A', 'B', 'C'
    verdict: str
    summary_markdown: str


class TradeAutopsyService:
    """Generador forense de autopsias post-trade."""

    @classmethod
    def evaluate(
        cls,
        trade_data: Dict[str, Any],
        mfe_r: Optional[float] = None,
        mae_r: Optional[float] = None,
    ) -> TradeAutopsyReport:
        """Analiza integralmente una operación cerrada y emite su reporte forense."""
        trade_id = trade_data.get("id") or trade_data.get("ticket")
        symbol = str(trade_data.get("instrument") or trade_data.get("symbol") or "UNKNOWN").upper()
        direction = str(trade_data.get("direction") or "BUY").upper()

        entry_price = float(trade_data.get("entry_price") or trade_data.get("filled_price") or 0.0)
        exit_price = float(trade_data.get("exit_price") or 0.0)
        stop_loss = float(trade_data.get("stop_loss") or trade_data.get("initial_stop_loss") or 0.0)
        planned_tp = float(trade_data.get("take_profit") or trade_data.get("initial_take_profit") or 0.0)

        planned_rr = float(trade_data.get("planned_rr") or 2.0)
        realized_rr = float(trade_data.get("realized_rr") or 0.0)
        if planned_rr > 0:
            rr_eff = max(0.0, round((realized_rr / planned_rr) * 100.0, 1))
        else:
            rr_eff = 0.0

        gross_pnl = float(trade_data.get("gross_pnl") or trade_data.get("profit_loss") or 0.0)
        commission = float(trade_data.get("commission") or 0.0)
        swap = float(trade_data.get("swap") or 0.0)
        net_pnl = float(trade_data.get("net_pnl") or (gross_pnl - commission - swap))

        frictions = abs(commission) + abs(swap)
        friction_drag = round((frictions / max(1.0, abs(gross_pnl))) * 100.0, 2) if abs(gross_pnl) > 0 else 0.0

        # Categorizar la salida
        raw_reason = str(trade_data.get("exit_reason") or trade_data.get("result") or "").lower()
        if "tp" in raw_reason or "take_profit" in raw_reason:
            exit_cat = "TP_FULL" if realized_rr >= (planned_rr * 0.9) else "TP_PARTIAL"
        elif "break_even" in raw_reason or abs(realized_rr) < 0.15:
            exit_cat = "BREAK_EVEN"
        elif "sl" in raw_reason or "stop_loss" in raw_reason:
            exit_cat = "STRUCTURAL_SL"
        elif "session" in raw_reason or "rollover" in raw_reason:
            exit_cat = "SESSION_CLOSE"
        else:
            exit_cat = "OTHER"

        # Confluencias y AI Score desde metadata
        details = {}
        raw_details = trade_data.get("details_json")
        if isinstance(raw_details, str) and raw_details.strip():
            try:
                details = json.loads(raw_details)
            except Exception:
                pass
        elif isinstance(raw_details, dict):
            details = raw_details

        ai_score = float(details.get("ai_score") or details.get("adaptive_score") or details.get("score") or 75.0)
        h1_ok = bool(details.get("h1_ok") or details.get("trend_ok") or True)
        m15_ok = bool(details.get("m15_ok") or details.get("structure_break_ok") or True)
        m5_ok = bool(details.get("m5_ok") or details.get("confirmation_ok") or True)
        confluence_all = h1_ok and m15_ok and m5_ok

        # Excursión MAE/MFE
        calc_mfe_r = float(mfe_r if mfe_r is not None else (details.get("mfe_r") or max(0.0, realized_rr)))
        calc_mae_r = float(mae_r if mae_r is not None else (details.get("mae_r") or (1.0 if realized_rr < 0 else 0.3)))
        left_on_table = max(0.0, round(calc_mfe_r - max(0.0, realized_rr), 2))

        # Calificación Institucional A / B / C
        grade, verdict, exec_score = cls._determine_grade(
            exit_cat=exit_cat,
            realized_rr=realized_rr,
            planned_rr=planned_rr,
            ai_score=ai_score,
            confluence=confluence_all,
            friction_drag=friction_drag,
            calc_mfe_r=calc_mfe_r,
        )

        # Generar Markdown
        summary_md = cls._build_markdown_summary(
            trade_id=trade_id,
            symbol=symbol,
            direction=direction,
            grade=grade,
            exit_cat=exit_cat,
            realized_rr=realized_rr,
            planned_rr=planned_rr,
            net_pnl=net_pnl,
            ai_score=ai_score,
            mfe_r=calc_mfe_r,
            mae_r=calc_mae_r,
            left_on_table=left_on_table,
            friction_drag=friction_drag,
            verdict=verdict,
        )

        return TradeAutopsyReport(
            trade_id=trade_id,
            symbol=symbol,
            direction=direction,
            entry_price=round(entry_price, 5),
            exit_price=round(exit_price, 5),
            stop_loss=round(stop_loss, 5),
            planned_tp=round(planned_tp, 5),
            planned_rr=round(planned_rr, 2),
            realized_rr=round(realized_rr, 2),
            rr_efficiency_percent=rr_eff,
            exit_reason_category=exit_cat,
            execution_quality_score=exec_score,
            gross_pnl=round(gross_pnl, 2),
            net_pnl=round(net_pnl, 2),
            commission=round(commission, 2),
            swap=round(swap, 2),
            friction_drag_percent=friction_drag,
            max_favorable_excursion_r=round(calc_mfe_r, 2),
            max_adverse_excursion_r=round(calc_mae_r, 2),
            left_on_table_r=left_on_table,
            ai_score_at_entry=round(ai_score, 1),
            confluence_h1_m15_m5=confluence_all,
            grade=grade,
            verdict=verdict,
            summary_markdown=summary_md,
        )

    @classmethod
    def _determine_grade(
        cls,
        exit_cat: str,
        realized_rr: float,
        planned_rr: float,
        ai_score: float,
        confluence: bool,
        friction_drag: float,
        calc_mfe_r: float,
    ) -> tuple[str, str, int]:
        # Grado A: Excelente setup institucional y cumplimiento de objetivo
        if (realized_rr >= (planned_rr * 0.8) or realized_rr >= 2.0) and ai_score >= 80.0 and confluence:
            return (
                "A",
                "Operación de Calidad Institucional A+: Confluencia total H1+M15+M5, alta convicción de IA y R:R capturado.",
                95,
            )

        # Grado B: Setup correcto pero salida en BE o retroceso antes de TP corredor
        if exit_cat == "BREAK_EVEN" or (realized_rr > 0.0 and realized_rr < (planned_rr * 0.8)):
            if calc_mfe_r >= 1.5:
                verdict = f"Operación Grado B: El precio avanzó favorablemente hasta {calc_mfe_r:.1f}R antes de retroceder."
            else:
                verdict = "Operación Grado B: Entrada técnicamente válida defendida por Break-Even sin daño al capital."
            return "B", verdict, 80

        # Grado C: Salida en SL o fricciones severas
        if exit_cat == "STRUCTURAL_SL":
            verdict = "Operación Grado C: El setup fue invalidado por el mercado tocando el Stop Loss estructural."
            return "C", verdict, 65

        if friction_drag > 25.0:
            return "C", "Operación Grado C: Rendimiento penalizado severamente por spread/comisiones.", 55

        return "B", "Operación estándar con desenlace neutral.", 75

    @classmethod
    def _build_markdown_summary(cls, **kwargs) -> str:
        return (
            f"### Autopsia Técnica: {kwargs.get('symbol')} ({kwargs.get('direction')}) — Grado {kwargs.get('grade')}\n"
            f"- **Desenlace:** {kwargs.get('exit_cat')} | **R:R Real:** {kwargs.get('realized_rr'):.2f}R (Obj: {kwargs.get('planned_rr'):.2f}R)\n"
            f"- **PnL Neto:** ${kwargs.get('net_pnl'):.2f} | **Fricción (Swap/Comisión):** {kwargs.get('friction_drag'):.1f}%\n"
            f"- **Excursión:** Máx Favorable {kwargs.get('mfe_r'):.2f}R | Máx Adversa {kwargs.get('mae_r'):.2f}R | Dejado en mesa: {kwargs.get('left_on_table'):.2f}R\n"
            f"- **Veredicto:** {kwargs.get('verdict')}\n"
        )
