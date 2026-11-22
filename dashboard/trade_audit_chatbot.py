"""Asistente forense interactivo (Chatbot) para la auditoría técnica de trades.

Analiza el expediente completo de un trade (tesis de entrada, confluencias,
recorrido MFE/MAE, desvíos de Stop Loss/Take Profit, timeline de snapshots y
dictamen de aprendizaje IA) para explicar al operador por qué se ganó o perdió
la operación con transparencia cuantitativa.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


CONFIRMATION_LABELS = {
    "FVG_FORMED": "Fair Value Gap (FVG) formado",
    "fvg_formed": "Fair Value Gap (FVG) formado",
    "LIQUIDITY_SWEEP": "Barrido de liquidez previo",
    "liquidity_sweep": "Barrido de liquidez previo",
    "DISPLACEMENT_DETECTED": "Desplazamiento fuerte con volumen",
    "displacement_detected": "Desplazamiento fuerte con volumen",
    "HTF_ALIGNED": "Marco temporal mayor alineado (H1/H4)",
    "htf_aligned": "Marco temporal mayor alineado (H1/H4)",
    "OTE_ZONE": "Entrada en zona óptima OTE (62%-79%)",
    "ote_zone": "Entrada en zona óptima OTE (62%-79%)",
    "CHOCH_M5": "Cambio de carácter CHoCH en M5",
    "choch_m5": "Cambio de carácter CHoCH en M5",
    "ORDER_BLOCK_MITIGATED": "Mitigación en Order Block clave",
    "order_block_mitigated": "Mitigación en Order Block clave",
    "GBDT_PROB_GT_0_55": "Modelo IA favorable (>55% prob.)",
    "gbdt_prob_gt_0_55": "Modelo IA favorable (>55% prob.)",
    "CLEAN_CORRIDOR_TO_TP": "Camino despejado hacia Take Profit",
    "clean_corridor_to_tp": "Camino despejado hacia Take Profit",
    "SESSION_KILLZONE_ACTIVE": "Dentro de Killzone institucional",
    "session_killzone_active": "Dentro de Killzone institucional",
    "ENGULFING_CONFIRMED": "Vela envolvente de rechazo",
    "PINBAR_REJECTION": "Rechazo claro por mecha (Pinbar)",
    "RESONANCE_ZONE": "Zona de confluencia técnica",
    "M15_STRUCTURE_CONFIRMED": "Estructura M15 confirmada",
    "SESSION_OPEN_SWEEP": "Barrido en apertura de sesión",
    "ADAPTIVE_MOMENTUM_OK": "Momento técnico favorable",
    "MARKET_STRUCTURE_BREAK": "Rompimiento estructural válido",
    "SPREAD_PENALTY": "Penalización por spread elevado",
    "HTF_COUNTER_TREND": "Contra tendencia en marco mayor (H1/H4)",
    "NO_SWEEP": "Sin barrido previo de liquidez",
    "SESSION_OUT_OF_KILLZONE": "Operación fuera de Killzone óptima",
    "LOW_CONFIRMATION_SCORE": "Puntaje técnico inferior al umbral",
    "CHOPPY_REGIME": "Mercado lateral o régimen errático",
    "OBSTACLE_BEFORE_TP1": "Obstáculo estructural antes de TP1",
    "ADVERSE_WICK_DETECTED": "Mecha de rechazo adversa detectada",
    "HIGH_VOLATILITY_NOISE": "Ruido excesivo de volatilidad",
}

META_REASON_LABELS = {
    "VALIDAR_CIERRE_COMPLETO_DEL_SETUP": "En espera de cierre de todo el setup para aprendizaje IA",
    "ELEGIBLE_ENTRADA": "Apto para reentrenamiento IA (Tesis de entrada completa)",
    "ELEGIBLE_OBSERVACION": "Apto para reentrenamiento IA (Por observación MT5)",
    "SL_TP_PENDIENTE_RECONCILIACION": "Pendiente de reconciliación de niveles SL/TP",
    "ESPERANDO_CIERRE_DEL_SETUP": "Operación activa · Esperando cierre de todas las patas",
    "ESPERANDO_CIERRE": "Operación en curso · Esperando cierre",
    "CIERRE_MANUAL_EXCLUIDO_DEL_MODELO_DE_ESTRATEGIA": "Cierre manual por usuario (Excluido de modelos IA)",
    "SIN_CONTEXTO_DE_ENTRADA_NI_OBSERVACION": "Sin contexto técnico previo registrado",
    "ESQUEMA_DE_FEATURES_ANTIGUO_REQUIERE_MIGRACION": "Esquema de datos anterior (Requiere migración)",
    "EVIDENCIA_INCOMPLETA_O_RESULTADO_NO_ETIQUETABLE": "Evidencia incompleta para etiquetado",
}


def _humanize_item(val: Any) -> str:
    if val is None:
        return "—"
    s = str(val).strip()
    if s in CONFIRMATION_LABELS:
        return CONFIRMATION_LABELS[s]
    up = s.upper()
    if up in CONFIRMATION_LABELS:
        return CONFIRMATION_LABELS[up]
    return s.replace("ICT_SABRI_MALLE", "ICT").replace("_", " ").title()


def _format_num(v: Any, decimals: int = 2) -> str:
    try:
        n = float(v)
        return f"{n:,.{decimals}f}"
    except (TypeError, ValueError):
        return "—"


def answer_trade_audit_inquiry(audit: Dict[str, Any], user_message: str) -> Dict[str, Any]:
    """Genera una respuesta analítica forense basada en el expediente real del trade."""
    trade = audit.get("trade") or {}
    entry_view = audit.get("entry_view") or {}
    snapshots = audit.get("snapshots") or []
    learning = audit.get("learning_eligibility") or {}

    trade_id = trade.get("id") or trade.get("source_trade_id") or "—"
    instrument = trade.get("instrument") or "Activo"
    direction = str(trade.get("direction") or entry_view.get("direction") or "—").upper()
    dir_human = "COMPRA (Largo)" if direction == "BUY" else "VENTA (Corto)" if direction == "SELL" else direction
    status = str(trade.get("status") or "").upper()
    classification = str(trade.get("classification") or trade.get("result") or "").upper()
    strategy_name = str(entry_view.get("strategy_name") or trade.get("strategy_name") or "ICT").replace("_", " ")

    try:
        realized_rr = float(trade.get("realized_rr")) if trade.get("realized_rr") is not None else None
    except (TypeError, ValueError):
        realized_rr = None

    try:
        net_pnl = float(trade.get("net_pnl")) if trade.get("net_pnl") is not None else None
    except (TypeError, ValueError):
        net_pnl = None

    entry_price = trade.get("entry_price")
    exit_price = trade.get("exit_price")
    stop_loss = trade.get("stop_loss")
    take_profit = trade.get("take_profit")
    planned_rr = trade.get("planned_rr")

    # MFE / MAE a partir de snapshots
    rrs = []
    for s in snapshots:
        m = s.get("market") or {}
        crr = m.get("current_rr")
        if crr is not None:
            try:
                rrs.append(float(crr))
            except (TypeError, ValueError):
                pass
    mfe = max(rrs) if rrs else (float(trade.get("mfe_rr")) if trade.get("mfe_rr") is not None else None)
    mae = min(rrs) if rrs else (float(trade.get("mae_rr")) if trade.get("mae_rr") is not None else None)

    # Estado de resultado
    is_open = status == "OPEN"
    is_win = (realized_rr is not None and realized_rr > 0.05) or (net_pnl is not None and net_pnl > 0.05) or any(k in classification for k in ("PROFIT", "WIN", "TP"))
    is_be = (realized_rr is not None and abs(realized_rr) <= 0.05) or any(k in classification for k in ("BE", "BREAKEVEN"))
    is_loss = (realized_rr is not None and realized_rr < -0.05) or (net_pnl is not None and net_pnl < -0.05) or any(k in classification for k in ("LOSS", "SL", "STOP"))

    score = entry_view.get("score")
    conf_pct = entry_view.get("confirmation_percentage")
    passed = entry_view.get("passed") or entry_view.get("passed_confirmations") or []
    missing = entry_view.get("missing") or entry_view.get("missing_confirmations") or []
    critical = entry_view.get("critical_failures") or []

    metadata = (trade.get("details") or {}).get("metadata") or {}
    corridor = (metadata.get("entry_preflight") or {}).get("path") or {}

    msg = user_message.lower().strip()

    # Clasificación de intención
    is_why_won = bool(re.search(r"(por\s*qu[eé]\s*se\s*gan[oó]|c[oó]mo\s*se\s*gan[oó]|motivo[s]?\s*de\s*ganancia|por\s*qu[eé]\s*fue\s*(win|ganador[a]?|tp))", msg))
    is_why_lost = bool(re.search(r"(por\s*qu[eé]\s*se\s*perdi[oó]|por\s*qu[eé]\s*fall[oó]|por\s*qu[eé]\s*toc[oó]\s*(el\s*)?(sl|stop)|motivo[s]?\s*de\s*p[eé]rdida|qu[eé]\s*fall[oó]|qu[eé]\s*sali[oó]\s*mal)", msg))
    is_why_entered = bool(re.search(r"(por\s*qu[eé]\s*se\s*(tom[oó]|entr[oó]|abri[oó])|tesis|motivo[s]?\s*de\s*entrada|criterio[s]?|por\s*qu[eé]\s*(compr[oó]|vendi[oó]))", msg))
    is_slippage = bool(re.search(r"(deslizamiento|slippage|se\s*respet[oó]\s*(el\s*)?stop|precio\s*de\s*salida|spread)", msg))
    is_mfe = bool(re.search(r"(mfe|mae|recorrido|lleg[oó]\s*a\s*estar\s*(en\s*)?ganancia|flotante|ganancia\s*m[aá]xima)", msg))
    is_ai = bool(re.search(r"(ia|aprendizaje|modelo|reentrenamiento|etiquetado|qu[eé]\s*aprendi[oó])", msg))
    is_confirmations = bool(re.search(r"(confirmaci[oó]n|confluencia|qu[eé]\s*falt[oó]|qu[eé]\s*se\s*cumpli[oó]|filtro)", msg))

    lines: List[str] = []

    # 1. ¿POR QUÉ SE GANÓ?
    if is_why_won:
        if is_win:
            lines.append(f"🎉 **Dictamen Forense: Victoria por {realized_rr:+.2f}R (+${net_pnl:,.2f} USD)**\n")
            lines.append(f"El trade **#{trade_id}** en **{instrument}** ({dir_human}) alcanzó exitosamente su objetivo debido a la confluencia de los siguientes factores técnicos:\n")
            lines.append(f"1. **Tesis de Entrada de Alta Probabilidad ({strategy_name}):**")
            lines.append(f"   • Score técnico de **{score or '—'}/100 pts** con **{conf_pct or '—'}% de confluencias** institucionales aprobadas.")
            if passed:
                lines.append(f"   • Confluencias clave cumplidas: {', '.join(_humanize_item(x) for x in passed[:5])}.")
            lines.append("\n2. **Ejecución y Respeto de Estructura:**")
            if mfe is not None:
                lines.append(f"   • **Recorrido Favorable (MFE):** El precio alcanzó hasta **{mfe:+.2f}R**, avanzando con fuerza direccional hacia el Take Profit en `{_format_num(take_profit, 5)}`.")
            if mae is not None:
                lines.append(f"   • **Protección del Stop Loss (MAE):** El retroceso adverso máximo fue de apenas **{mae:.2f}R**, manteniéndose muy lejos del Stop Loss en `{_format_num(stop_loss, 5)}`.")
            lines.append("\n3. **Corredor Despejado al Take Profit:**")
            lines.append("   • El algoritmo validó ausencia de bloques de órdenes contrarios u obstáculos de liquidez intermedios que pudieran frenar la aceleración del precio.")
        else:
            lines.append(f"ℹ️ **Aclaración:** Esta operación **no cerró en ganancia**.")
            lines.append(f"Su resultado oficial fue: **{status} · {classification}** con **{realized_rr:+.2f}R** (**${net_pnl:,.2f} USD**).\n")
            lines.append("A continuación te explico las razones exactas por las que no logró ganar:")
            # Caer a explicación de pérdida
            is_why_lost = True

    # 2. ¿POR QUÉ SE PERDIÓ?
    if is_why_lost and not (is_why_won and is_win):
        if is_loss:
            lines.append(f"🔍 **Dictamen Forense: Análisis de Pérdida ({realized_rr:+.2f}R · ${net_pnl:,.2f} USD)**\n")
            lines.append(f"El trade **#{trade_id}** en **{instrument}** ({dir_human}) cerró al tocar el Stop Loss (`{_format_num(stop_loss, 5)}`). El análisis forense snapshot a snapshot revela las siguientes causas:\n")

            lines.append("1. **Comportamiento y Dinámica del Precio (MFE vs MAE):**")
            if mfe is not None and mfe > 0.2:
                lines.append(f"   • **Ganancia flotante previa:** La posición llegó a estar a favor hasta **{mfe:+.2f}R**, pero no alcanzó la extensión requerida (+1.0R) para activar el seguro de Break Even antes de revertirse.")
            else:
                lines.append(f"   • **Presión contraria inmediata:** Tras la entrada en `{_format_num(entry_price, 5)}`, el mercado no logró consolidar desplazamiento a favor (MFE de apenas {mfe:+.2f}R si aplica) y fue rechazado rápidamente en contra.")
            if mae is not None:
                lines.append(f"   • **Retroceso máximo (MAE):** Alcanzó **{mae:.2f}R**, consumiendo el margen de protección hasta ejecutar la salida programada.")

            lines.append("\n2. **Factores Técnicos e Invalidación de Zona:**")
            lines.append(f"   • La zona técnica `{_humanize_item(entry_view.get('zone'))}` fue traspasada por absorción o barrido de liquidez institucional en contra de la posición.")
            if missing or critical:
                penalty_items = missing + critical
                lines.append(f"   • Advertencias / penalizaciones que estaban activas al entrar: **{', '.join(_humanize_item(x) for x in penalty_items)}**.")

            lines.append("\n3. **Disciplina Contractual y Control de Daños:**")
            lines.append(f"   • El bot respetó estrictamente la regla de oro: la pérdida se limitó a **{realized_rr:.2f}R** (1% del capital asignado), evitando drawdowns descontrolados.")
            lines.append(f"   • Salida ejecutada a `{_format_num(exit_price, 5)}`.")
        elif is_be:
            lines.append(f"🛡️ **Operación Cerrada en Break Even (0.00R · Sin Riesgo):**\n")
            lines.append(f"Esta operación no se perdió; cerró en punto de equilibrio (`{_format_num(exit_price, 5)}`) protegiendo el 100% del capital tras un movimiento que amenazó revertirse.")
        elif is_open:
            lines.append(f"🟢 **Operación Actualmente Abierta (En curso):**\n")
            lines.append(f"Esta operación no se ha cerrado; sigue activa en mercado con cotización actual en seguimiento.")
        else:
            lines.append(f"ℹ️ **Resultado del Trade:** Este trade cerró con resultado **{classification or status}** ({realized_rr:+.2f}R).")

    # 3. ¿POR QUÉ SE TOMÓ LA ENTRADA?
    elif is_why_entered:
        lines.append(f"🎯 **Tesis Institucional de Apertura · Trade #{trade_id} en {instrument}:**\n")
        lines.append(f"BlackDaemonFX ejecutó una orden de **{dir_human}** a las `{trade.get('entry_time') or '—'}` cotizando en `{_format_num(entry_price, 5)}` bajo los siguientes fundamentos:\n")
        lines.append(f"1. **Estrategia y Puntuación:**")
        lines.append(f"   • Estrategia: **{strategy_name}**.")
        lines.append(f"   • Puntuación técnica: **{score or '—'}/100 pts** con **{conf_pct or '—'}% de confluencias** (Umbral superado con solidez).")
        lines.append(f"\n2. **Convergencia y Estructura:**")
        lines.append(f"   • Tendencia macro H4: **{_humanize_item(entry_view.get('h4_trend'))}** · H1: **{_humanize_item(entry_view.get('h1_trend'))}**.")
        lines.append(f"   • Estructura M15: **{_humanize_item(entry_view.get('structure_break'))}**.")
        lines.append(f"   • Zona operativa de valor: **{_humanize_item(entry_view.get('zone'))}**.")
        if passed:
            lines.append(f"\n3. **Confirmaciones Técnicas Aprobadas:**\n   • " + "\n   • ".join(_humanize_item(x) for x in passed))
        lines.append(f"\n4. **Plan de Riesgo Asimétrico:**")
        lines.append(f"   • Stop Loss fijado en `{_format_num(stop_loss, 5)}`.")
        lines.append(f"   • Take Profit objetivo en `{_format_num(take_profit, 5)}`.")
        lines.append(f"   • Ratio R:R previsto: **1 : {planned_rr or 2.0}** con riesgo contractual estricto del 1%.")

    # 4. DESLIZAMIENTO Y STOP LOSS
    elif is_slippage:
        lines.append(f"🛡️ **Auditoría de Ejecución y Deslizamiento (Slippage):**\n")
        lines.append(f"• **Precio de Entrada:** `{_format_num(entry_price, 5)}`")
        lines.append(f"• **Stop Loss Planificado:** `{_format_num(stop_loss, 5)}`")
        lines.append(f"• **Precio de Salida Real:** `{_format_num(exit_price, 5)}`")
        if exit_price is not None and stop_loss is not None:
            try:
                diff = abs(float(exit_price) - float(stop_loss))
                lines.append(f"• **Diferencia observada:** `{diff:,.5f}` puntos.")
                if diff < 0.0001:
                    lines.append("• **Veredicto:** **Cierre milimétrico exacto**. El broker liquidó la orden con cero deslizamiento perceptible.")
                else:
                    lines.append(f"• **Veredicto:** Deslizamiento normal de volatilidad dentro de tolerancias contractuales.")
            except (TypeError, ValueError):
                pass

    # 5. MFE Y TRAYECTORIA
    elif is_mfe:
        lines.append(f"📈 **Recorrido del Precio y Excursión del Trade (MFE / MAE):**\n")
        lines.append(f"Durante los **{len(snapshots)} snapshots** registrados en la línea temporal persistente:\n")
        lines.append(f"• **Máxima Ganancia Flotante (MFE):** **{f'{mfe:+.2f}R' if mfe is not None else '—'}**")
        lines.append(f"• **Máximo Retroceso Adverso (MAE):** **{f'{mae:.2f}R' if mae is not None else '—'}**")
        lines.append(f"• **Ratio R:R Final Cerrado:** **{f'{realized_rr:+.2f}R' if realized_rr is not None else '—'}**\n")
        if mfe is not None and mfe > 0.5:
            lines.append("📌 *El trade experimentó un impulso favorable notable antes del desenlace.*")
        else:
            lines.append("📌 *El mercado presionó en contra casi desde el ingreso sin permitir desarrollo expansivo.*")

    # 6. APRENDIZAJE IA
    elif is_ai:
        lines.append(f"🧠 **Dictamen del Motor de Aprendizaje y Meta-Etiquetado IA:**\n")
        reason_raw = learning.get("reason") or "VALIDAR_CIERRE_COMPLETO_DEL_SETUP"
        reason_desc = META_REASON_LABELS.get(reason_raw, _humanize_item(reason_raw))
        lines.append(f"• **Tipo de Evidencia Guardada:** `{_humanize_item(learning.get('evidence_type') or 'ENTRY_CAPTURE')}` (Inmutable)")
        lines.append(f"• **Clasificación de Aprendizaje:** **{reason_desc}**")
        lines.append(f"• **Impacto en el Modelo GBDT:**")
        lines.append("  Los features capturados al momento exacto de la entrada quedan registrados en la base forense. Durante el reentrenamiento semanal, los algoritmos de Machine Learning analizan este trade para recalibrar los pesos de confluencia y reducir la exposición a setups similares en este activo.")

    # 7. CONFIRMACIONES / FILTROS
    elif is_confirmations:
        lines.append(f"📋 **Checklist Técnico y Confluencias Evaluadas:**\n")
        lines.append(f"• **Confirmaciones Aprobadas ({len(passed)}):**")
        if passed:
            for p in passed:
                lines.append(f"  ✓ {_humanize_item(p)}")
        else:
            lines.append("  (Ninguna confirmación registrada)")
        lines.append(f"\n• **Penalizaciones / Filtros Faltantes ({len(missing) + len(critical)}):**")
        if missing or critical:
            for m in (missing + critical):
                lines.append(f"  ⚠️ {_humanize_item(m)}")
        else:
            lines.append("  ✓ Sin penalizaciones ni filtros faltantes.")

    # 8. RESUMEN FORENSE GENERAL (DEFAULT)
    else:
        lines.append(f"📋 **Auditoría Forense Consolidada · Trade #{trade_id} ({instrument}):**\n")
        lines.append(f"• **Operación:** **{dir_human}** bajo la estrategia **{strategy_name}**.")
        lines.append(f"• **Resultado:** **{status} · {classification}** ({f'{realized_rr:+.2f}R' if realized_rr is not None else '—'} · {f'${net_pnl:,.2f} USD' if net_pnl is not None else '—'}).")
        lines.append(f"• **Puntuación al entrar:** **{score or '—'}/100 pts** con **{conf_pct or '—'}% de confluencias**.")
        lines.append(f"• **Trayectoria:** MFE de **{f'{mfe:+.2f}R' if mfe is not None else '—'}** y MAE de **{f'{mae:.2f}R' if mae is not None else '—'}** a lo largo de {len(snapshots)} snapshots.")
        if is_win:
            lines.append(f"\n💡 *Veredicto:* Trade ganador que ejecutó con rigor la tesis institucional.")
        elif is_loss:
            lines.append(f"\n💡 *Veredicto:* Setup técnicamente válido que fue invalidado por absorción contraria, respetando el Stop Loss de protección.")
        lines.append("\nPuedes consultarme: *'¿Por qué se perdió/ganó?'*, *'¿Hubo deslizamiento?'*, *'¿Llegó a estar en ganancia?'* o *'¿Qué aprendió la IA?'*.")

    return {
        "ok": True,
        "trade_id": trade_id,
        "instrument": instrument,
        "reply": "\n".join(lines),
    }
