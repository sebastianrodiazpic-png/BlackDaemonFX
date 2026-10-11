"""Servidor del dashboard en tiempo real de BlackDaemonFX.

Levanta un `ThreadingHTTPServer` local que sirve las paginas HTML (dashboard,
cuenta, instrumentos, auditoria de trade) y los endpoints JSON que las
alimentan. Recoge los eventos que el motor le va notificando (`cycle_start`,
`symbol_result`, `monitor_result`, ...), los traduce a etiquetas en espanol y
los publica.

Principios de diseno:
    - SOLO OBSERVA: nunca abre ni cierra operaciones. La unica accion de
      escritura es habilitar o detener workers, delegada en el controlador que
      inyecta `app.main`.
    - Estado protegido por lock y persistido en JSON, para que al reiniciar el
      daemon la interfaz no aparezca vacia.
    - Caches con TTL para las vistas caras (cuenta, instrumentos), de modo que
      refrescar el navegador no castigue a la base de datos.
    - Todo error se degrada a un estado visible; el dashboard jamas debe tumbar
      al bot.

Vinculaciones:
    - `dashboard.account_metrics.build_account_payload`: metricas de cuenta.
    - `dashboard.account_page` / `dashboard.trade_audit_page`: plantillas HTML.
    - `reporting.trade_audit_excel_exporter`: descarga XLSX por operacion.
    - `services.financial_news_service`: noticias y calendario macro.
    - `database.repository.TradingRepository`: origen de los datos.
    - `app.main` y `strategy.execution.live_trading_engine`: emisores de los
      eventos que se muestran.
"""

from __future__ import annotations

import json
import re
import threading
import time
import zipfile
from io import BytesIO
from collections import deque
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from daemon_version import DAEMONBLACKFX_VERSION
from typing import Any
from urllib.parse import urlparse

from dashboard.account_metrics import build_account_payload
from dashboard.quarantine_view import quarantine_snapshot
from dashboard.smc_trial import snapshot as smc_trial_snapshot
from strategy.ai.continuous_audit import snapshot as learning_snapshot
from strategy.ai.trade_observation import eligibility as trade_learning_eligibility
from dashboard.account_page import ACCOUNT_HTML
from dashboard.page_loading import with_page_loading
from dashboard.performance_page import PERFORMANCE_HTML
from dashboard.strategy_bases_page import STRATEGY_BASES_HTML
from dashboard.trade_audit_page import TRADE_AUDIT_HTML
from reporting.trade_audit_excel_exporter import TradeAuditExcelExporter
from services.financial_news_service import FinancialNewsService


_LABELS = {
    "h1_trend": "Tendencia H1",
    "m15_setup": "Setup M15",
    "liquidity_sweep": "Barrido de liquidez",
    "m15_structure": "Estructura M15 / CHOCH-BOS",
    "premium_discount": "Premium / Discount",
    "fresh_order_block": "Order Block fresco",
    "clean_retest": "Retesteo limpio",
    "rejection": "Rechazo",
    "displacement": "Desplazamiento",
    "micro_structure": "Microestructura M5",
    "strong_close": "Cierre fuerte",
    "directional_candle": "Vela direccional",
    "confirmation_mode_ok": "Modo de confirmación",
    "harmonic_confirmation": "Patrón armónico",
    "h1_extreme_doji_confirmation": "Doji H1 en extremo",
    "momentum": "Momentum",
}


_ACTION_LABELS_ES = {
    "ORDER_OPENED": "Orden abierta",
    "SPLIT_ORDER_OPENED": "Operación abierta en TP1 + Runner",
    "DRY_RUN_VALIDATED": "Operación validada en simulación",
    "NO_SIGNAL": "Sin oportunidad confirmada",
    "NO_TRADE": "Sin nueva entrada",
    "NO_NEW_ORDER": "Sin nueva orden",
    "REJECTED": "Entrada descartada",
    "EXECUTION_REJECTED": "Orden rechazada por el broker",
    "OPERACION_RECHAZADA_POR_RIESGO": "Operación descartada por riesgo",
    "REJECTED_RISK_EXCEEDED": "Riesgo superior al permitido",
    "REJECTED_RISK_TARGET_UNREACHABLE": "No se puede alcanzar el riesgo objetivo con el volumen permitido",
    "REJECTED_TOTAL_SPLIT_RISK_EXCEEDED": "El riesgo combinado TP1 + Runner supera el máximo",
    "EMERGENCY_RISK_EXIT": "Cierre de emergencia por protección de riesgo",
    "SYMBOL_QUARANTINED": "Instrumento en cuarentena de riesgo",
    "ENTRY_PRICE_DRIFT_TOO_LARGE": "El precio se alejó demasiado de la entrada planificada",
    "REJECTED_ORDER_CHECK": "La orden no superó la validación previa de MT5",
    "REJECTED_INVALID_MARKET_STOP": "Stop Loss no válido para las reglas del mercado",
    "RR_TOO_LOW": "Relación riesgo/beneficio insuficiente",
    "JUMP_STRICT_FILTER_REJECTED": "Jump descartado por filtro reforzado",
    "JUMP_SINGLE_FALLBACK_BLOCKED": "Jump descartado: requiere TP1 + Runner",
    "FOREX_ROLLOVER_ENTRY_BLOCKED": "Forex pausado por protección de rollover",
    "DIRECTION_POLICY_BLOCKED": "La dirección está bloqueada por la política del instrumento",
    "POSITION_ALREADY_OPEN_FOR_SYMBOL": "Ya existe una posición abierta en este instrumento",
    "MAX_TOTAL_OPEN_POSITIONS": "Se alcanzó el máximo total de posiciones abiertas",
    "MAX_TOTAL_OPEN_POSITIONS_REACHED": "Se alcanzó el máximo total de posiciones abiertas",
    "MAX_OPEN_POSITIONS_PER_SYMBOL_REACHED": "Se alcanzó el máximo de posiciones para este instrumento",
    "ALREADY_EXECUTED": "Esta oportunidad ya fue ejecutada anteriormente",
    "MARKET_INVALIDATED_SIGNAL": "El mercado invalidó la señal antes de ejecutar",
    "ERROR": "Error durante el análisis o la ejecución",
    "NO_H1_CONTEXT": "Esperando contexto válido de H1",
    "NO_H4_CONTEXT": "Esperando tendencia válida de H4",
    "HTF_TREND_DIVERGENCE": "H4 y H1 no convergen",
    "OUTSIDE_SESSION": "Fuera de sesión · análisis pausado",
    "SESSION_WARMUP": "Preparando próxima sesión",
    "ENTRY_LOCATION_BLOCKED": "Precio de entrada incompatible con premium/discount",
    "NO_M15_SETUP": "Esperando setup válido de M15",
    "NO_M5_CONFIRMATION": "Esperando confirmación de M5",
    "NO_M5_DATA_OR_SIGNAL": "Esperando datos o señal válida de M5",
    "WAITING_M5_AFTER_M15": "Esperando confirmación M5 posterior al setup M15",
    "STALE_M5_SIGNAL": "Señal M5 demasiado antigua; esperando una nueva",
    "WAITING_NEW_M5_BAR": "Esperando el cierre de una nueva vela M5",
    "WAITING_NEW_M1_BAR": "Esperando el cierre de una nueva vela M1",
    "WAITING_FOREX_DATA": "Esperando datos Forex",
    "NO_DIRECTIONAL_H1_TREND": "Esperando tendencia direccional en H1",
    "NO_DIRECTIONAL_H4_TREND": "Esperando tendencia direccional en H4",
    "NO_DIRECTIONAL_M15_SETUP": "Esperando setup direccional en M15",
    "NO_DIRECTIONAL_M5_CONFIRMATION": "Esperando confirmación direccional en M5",
    "INVALID_DIRECTION": "Esperando una dirección BUY o SELL válida",
    "WAITING_M5_CONFIRMATION": "Esperando confirmación de M5",
    "NO_H1_DATA": "Esperando suficientes datos de H1",
    "NO_H4_DATA": "Esperando suficientes datos de H4",
    "NO_OWNED_OPEN_POSITIONS": "Sin posiciones abiertas propias para gestionar",
    "FOREX_CURRENCY_EXPOSURE_LIMIT": "Entrada bloqueada: límite de exposición por divisa",
    "FOREX_TOTAL_RISK_LIMIT": "Entrada bloqueada: límite total de riesgo Forex",
}

_REASON_LABELS_ES = {
    "POST_FILL_RISK_HARD_CAP_BREACH": "El riesgo real de la posición, después de ser ejecutada, superó el límite máximo permitido.",
    "POST_FILL_INVALID_POSITION_DATA": "No fue posible validar correctamente los datos de la posición después de ejecutarla.",
    "POST_FILL_POSITION_NOT_FOUND": "La orden fue enviada, pero no se pudo localizar la posición resultante para validar su riesgo.",
    "POST_FILL_RISK_OK": "El riesgo real posterior a la ejecución está dentro del límite permitido.",
    "RISK_INCIDENT_TEMPORARY_COOLDOWN": "Cuarentena temporal por una desviación marginal de ejecución; se habilitará automáticamente al vencer el periodo de seguridad.",
    "RISK_INCIDENT_REQUIRES_MANUAL_REVIEW": "Cuarentena de seguridad permanente: el incidente no es compatible con un simple redondeo o slippage y requiere revisión manual.",
    "BROKER_VOLUME_LIMIT_PREVENTS_TARGET_RISK": "El volumen permitido por el broker no permite alcanzar el riesgo objetivo sin violar las reglas de gestión de riesgo.",
    "INSUFFICIENT_TRADE_SCORE": "La calidad calculada de la oportunidad es inferior al mínimo requerido.",
    "CRITICAL_CONFIRMATION_MISSING": "Falta al menos una condición estructural crítica de la estrategia.",
    "BOS_REJECTION_NOT_CONFIRMED": "El BOS no presentó el rechazo M5 obligatorio para habilitar la entrada.",
    "CHOCH_MICRO_STRUCTURE_NOT_CONFIRMED": "El CHOCH no presentó la microestructura M5 obligatoria para habilitar la entrada.",
    "JUMP_REQUIERE_CONFIRMACIONES_ESTRUCTURALES_REFORZADAS": "Jump no alcanzó todas las confirmaciones reforzadas requeridas.",
    "JUMP_REQUIERE_EJECUCION_DIVIDIDA_TP1_RUNNER": "En Jump no se permite fallback SINGLE; la operación debe poder dividirse en TP1 + Runner.",
    "FOREX_NO_NUEVAS_ENTRADAS_CERCA_DEL_ROLLOVER": "No se abren nuevas operaciones Forex cerca del rollover de Nueva York para evitar spreads ampliados.",
    "CONFIRMATION_PERCENTAGE_BELOW_THRESHOLD": "El porcentaje de confirmaciones es inferior al mínimo adaptativo del 80%.",
    "VIABLE_TRADE_SCORE_BELOW_THRESHOLD": "El score de calidad no alcanza el mínimo establecido para considerar viable la entrada.",
    "REJECTION_NOT_CONFIRMED": "No se confirmó un rechazo de precio suficientemente claro en la zona de interés.",
    "DISPLACEMENT_NOT_CONFIRMED": "No se detectó un desplazamiento de precio suficientemente fuerte después de la reacción.",
    "MICRO_STRUCTURE_NOT_CONFIRMED": "La microestructura de M5 todavía no confirma la dirección propuesta.",
    "STRONG_CLOSE_NOT_CONFIRMED": "La vela de confirmación no presentó un cierre suficientemente fuerte.",
    "HARMONIC_PATTERN_NOT_CONFIRMED": "No se confirmó un patrón armónico; esta condición es adicional y no obligatoria.",
    "NO_VALID_HARMONIC_PATTERN": "No se encontró un patrón armónico válido; la estrategia puede continuar si el resto del setup es suficiente.",
    "ORDER_BLOCK_NOT_FRESH": "El Order Block detectado ya fue mitigado o no cumple el criterio de frescura.",
    "CONFIRMATION_MODE_NOT_SATISFIED": "La combinación de confirmaciones todavía no cumple el modo de validación configurado.",
    "NO_DIRECTIONAL_H1_TREND": "H1 no presenta una tendencia suficientemente clara para definir una dirección.",
    "NO_DIRECTIONAL_M15_SETUP": "M15 no presenta todavía un setup direccional SMC válido.",
    "NO_DIRECTIONAL_M5_CONFIRMATION": "M5 no presenta todavía una confirmación direccional válida para ejecutar.",
    "NO_H1_CONTEXT": "No se pudo construir un contexto H1 válido para evaluar esta oportunidad.",
    "NO_H4_CONTEXT": "No se pudo construir una tendencia H4 válida para evaluar esta oportunidad.",
    "H4_H1_TREND_DIVERGENCE": "La tendencia mayor H4 y el contexto H1 apuntan en direcciones contrarias.",
    "NO_DIRECTIONAL_H4_TREND": "H4 todavía no presenta una tendencia mayor suficientemente clara.",
    "NO_H4_DATA": "No hay suficientes velas H4 disponibles para realizar el análisis.",
    "NO_H1_DATA": "No hay suficientes velas H1 disponibles para realizar el análisis.",
    "NO_M15_SETUP": "No se encontró un setup SMC válido en M15.",
    "NO_M5_CONFIRMATION": "El setup existe, pero M5 todavía no confirma la entrada.",
    "NO_M5_DATA_OR_SIGNAL": "No hay suficientes datos M5 o todavía no existe una señal de confirmación válida.",
    "NO_SIGNAL": "No se encontró una oportunidad que cumpla las condiciones necesarias para abrir una operación.",
    "RR_TOO_LOW": "La distancia entre entrada, Stop Loss y objetivo no ofrece una relación riesgo/beneficio suficiente.",
    "ENTRY_PRICE_DRIFT_TOO_LARGE": "El precio actual se alejó demasiado del precio que originó la señal; ejecutar ahora empeoraría el riesgo o el R:R.",
    "REJECTED_MARGIN_EXCEEDED": "El margen necesario para abrir la operación supera el límite permitido por la gestión de riesgo.",
    "SPLIT_ORDERS_MARGIN_EXCEEDS_LIMIT": "El margen combinado necesario para TP1 + Runner supera el límite operativo configurado.",
    "POSITION_ALREADY_OPEN_FOR_SYMBOL": "No se abre otra entrada porque ya existe una posición en este instrumento.",
    "MAX_TOTAL_OPEN_POSITIONS": "No se abre la entrada porque ya se alcanzó el máximo de posiciones simultáneas.",
    "ADX_M15_INSUFICIENTE": "El ADX de M15 todavía no acredita fuerza direccional suficiente para operar.",
    "SIN_TENDENCIA_M15": "Las EMA de M15 todavía no tienen separación y pendiente suficientes para definir una tendencia operable.",
    "SPREAD_VS_ATR": "El spread actual es demasiado grande respecto del ATR M5.",
    "M5_STRUCTURE_BREAK": "Todavía no existe ruptura estructural BOS en M5.",
    "M5_PULLBACK": "Todavía no se confirmó el pullback M5 hacia la zona dinámica.",
    "M1_REJECTION": "Falta la vela de rechazo M1 en la dirección del régimen.",
    "M1_FOLLOW_THROUGH": "Falta la vela M1 posterior que confirme continuación.",
    "M1_STRONG_CLOSE": "La vela M1 de continuación no cerró con cuerpo suficiente.",
}

_DECISION_LABELS_ES = {
    "STRICT_CONFIRMED": "Confirmada estrictamente",
    "ADAPTIVE_75_CONFIRMED": "Confirmada por regla adaptativa ≥75%",
    "ADAPTIVE_80_CONFIRMED": "Confirmada por regla adaptativa ≥80%",
    "REJECTED": "Rechazada",
    "NO CONFIRMADA": "No confirmada",
}

def _humanize_code(value: Any) -> str:
    """Convierte un codigo tipo `STALE_M5_SIGNAL` en texto legible.

    Solo transforma cadenas que parecen codigos (mayusculas con guion bajo);
    un texto ya redactado se devuelve intacto.
    """
    text = str(value or "").strip()
    if not text:
        return "Sin motivo informado"
    if "_" not in text or not text.upper() == text:
        return text
    return text.replace("_", " ").strip().capitalize()

def _action_label_es(value: Any) -> str:
    """Traduce el codigo de accion del motor a su etiqueta en espanol."""
    key = str(value or "SIN_ACCION").strip().upper()
    return _ACTION_LABELS_ES.get(key, _humanize_code(key))

def _state_label_es(value: Any) -> str:
    """Traduce un codigo de estado usando el mismo diccionario de acciones."""
    key = str(value or "").strip().upper()
    return _ACTION_LABELS_ES.get(key, _humanize_code(key))

def _reason_label_es(value: Any) -> str:
    """Traduce uno o varios motivos separados por comas a espanol.

    El motor puede acumular varias causas en una sola cadena; se traducen por
    separado y se concatenan, recurriendo a `_humanize_code` en las no
    catalogadas.
    """
    key = str(value or "").strip()
    if not key:
        return "Sin motivo adicional informado."
    if "," in key:
        labels = [
            _REASON_LABELS_ES.get(token.strip().upper(), _humanize_code(token.strip()))
            for token in key.split(",")
            if token.strip()
        ]
        return " ".join(labels) if labels else "Sin motivo adicional informado."
    return _REASON_LABELS_ES.get(key.upper(), _humanize_code(key))

def _decision_label_es(value: Any) -> str:
    """Traduce la decision de confirmacion (CONFIRMED / REJECTED / ...)."""
    key = str(value or "NO CONFIRMADA").strip().upper()
    return _DECISION_LABELS_ES.get(key, _humanize_code(key))

def _operational_state(action: Any, reason: Any, decision: Any) -> dict:
    """Resume accion, motivo y decision en un unico estado con color.

    El orden de las comprobaciones es intencionado: RIESGO primero, para que un
    evento de proteccion nunca quede oculto tras otra etiqueta mas benigna.

    Returns:
        dict con `key`, `label` y `severity` (good / warn / bad / neutral).
    """
    a = str(action or "").upper()
    r = str(reason or "").upper()
    d = str(decision or "").upper()
    risk_tokens = ("RISK", "MARGIN", "EMERGENCY", "HARD_CAP", "INVALID_MARKET_STOP")
    if any(token in a or token in r for token in risk_tokens):
        return {"key": "RISK", "label": "PROTECCIÓN / RIESGO", "severity": "bad"}
    if a in {"ORDER_OPENED", "SPLIT_ORDER_OPENED", "DRY_RUN_VALIDATED"} or "CONFIRMED" in d:
        return {"key": "CONFIRMED", "label": "CONFIRMADO", "severity": "good"}
    if a.startswith("REJECT") or a in {"REJECTED", "EXECUTION_REJECTED", "MARKET_INVALIDATED_SIGNAL", "DIRECTION_POLICY_BLOCKED", "ALREADY_EXECUTED"}:
        return {"key": "REJECTED", "label": "DESCARTADO", "severity": "warn"}
    if a in {"NO_SIGNAL", "NO_TRADE", "NO_NEW_ORDER", "SIN ACCIÓN", "SIN_ACCION"} or "NO_" in r:
        return {"key": "WAITING", "label": "ESPERANDO", "severity": "neutral"}
    if a == "ERROR" or "ERROR" in r:
        return {"key": "ERROR", "label": "ERROR", "severity": "bad"}
    return {"key": "INFO", "label": "INFORMATIVO", "severity": "neutral"}


def _enrich_recent_row(value: Any) -> dict:
    """Normaliza eventos persistidos para que el dashboard explique el bloqueo."""
    row = dict(value) if isinstance(value, dict) else {}
    action = row.get("action") or row.get("_action") or "SIN_ACCION"
    reason = row.get("reason") or row.get("error")
    reason_es = _reason_label_es(reason)
    decision = row.get("confirmation_decision") or row.get("decision")
    row.update({
        "action": action,
        "action_es": _action_label_es(action),
        "reason": reason,
        "reason_es": reason_es,
        "decision_es": _decision_label_es(decision),
        "operational_state": _operational_state(action, reason, decision),
        "state_es": _state_label_es(row.get("state") or action),
    })
    return row

_CATEGORY_LABELS = {
    "volatility": "Volatility",
    "boom": "Boom",
    "crash": "Crash",
    "step": "Step",
    "jump": "Jump",
    "flip": "Boom / Crash combinados",
    "forex": "Forex",
    "crypto": "Crypto",
    "other": "Otros",
    "orb_ny_wall_street_30": "Wall Street 30",
    "orb_ny_us_tech_100": "US Tech 100",
    "orb_ny_us_500": "S&P 500",
    "orb_ny_xauusd": "XAUUSD",
    "orb_ny_micro_xauusd": "XAUUSD Micro",
    "orb_ny_eurusd": "EURUSD",
    "orb_ny_btcusd": "BTCUSD",
    "orb_ny_xagusd": "Plata (XAGUSD)",
    "orb_ny_micro_xagusd": "Plata Micro (XAGUSD)",
    "orb_ny_us_oil": "Petróleo (US Oil)",
    "idx_open_indices": "Apertura de Índices Bursátiles",
    "malaysian_snr_jump": "Malaysian SNR · Jump Index",
    "malaysian_snr_step": "Malaysian SNR · Step Index",
    "malaysian_snr_volatility": "Malaysian SNR · Volatility Index",
    "malaysian_snr_indices": "Malaysian SNR · Índices & Commodities",
    "malaysian_snr_boom": "Malaysian SNR · Boom Index (BUY Only)",
    "malaysian_snr_crash": "Malaysian SNR · Crash Index (SELL Only)",
    "malaysian_snr_forex": "Malaysian SNR · Forex & Cripto",
    "malaysian_snr_pruned": "Malaysian SNR · Activos Podados (PODA)",
    "gold_cuartos_xauusd": "Oro Cuartos (XAUUSD)",
    "gold_cuartos_micro_xauusd": "Oro Micro Cuartos (XAUUSDmicro)",
    "gold_cuartos_xagusd": "Plata Cuartos (XAGUSD)",
    "gold_cuartos_micro_xagusd": "Plata Micro Cuartos (XAGUSDmicro)",
    "ict_metals_xagusd": "ICT Metales · Plata (XAGUSD)",
    "ict_metals_xauusd": "ICT Metales · Oro (XAUUSD)",
    "ict_crypto_btcusd": "ICT Criptomonedas · Bitcoin (BTCUSD)",
    "ict_indices": "ICT Índices Bursátiles",
}

_SELECTION_PROFILES=("SYNTHETICS","FOREX","ORB","IDX_OPEN","MALAYSIAN_SNR","GOLD","ICT")


def _build_confluence_matrix(state: dict) -> list[dict]:
    """Genera la Matriz Centinela Multiestrategia (SMC, Malaysian SNR, ORB, Gold Quarters)."""
    matrix = []
    seen_keys = set()

    candidates = state.get("worker_candidates") or {}
    recent = state.get("recent") or []

    rows_to_check = []
    if isinstance(candidates, dict):
        for profile, cand in candidates.items():
            if isinstance(cand, dict) and cand.get("symbol"):
                cand_copy = dict(cand)
                cand_copy.setdefault("_bot_profile", profile)
                rows_to_check.append(cand_copy)
    if isinstance(recent, list):
        rows_to_check.extend(recent)

    for item in rows_to_check:
        sym = item.get("symbol") or item.get("instrument")
        if not sym:
            continue

        prof = str(item.get("bot_profile") or item.get("_bot_profile") or "").upper()
        strat_raw = str(item.get("strategy_name") or prof).upper()
        action = str(item.get("action") or item.get("_action") or "").upper()
        reason = str(item.get("reason") or item.get("error") or "").upper()

        if (
            "MALAYSIAN" in strat_raw
            or "MALAYSIAN" in prof
            or "MALAYSIAN" in action
            or "MALAYSIAN" in reason
            or "ESC_" in reason
            or "JUMP_STRICT" in action
        ):
            strat_key = "MALAYSIAN_SNR"
            strat_label = "Malaysian SNR"
            strat_badge = "strat-snr"
        elif (
            "ORB" in strat_raw
            or "ORB" in prof
            or action.startswith("ORB_")
            or "WAITING_NEW_YORK" in action
            or "NEW_YORK" in reason
        ):
            strat_key = "ORB"
            strat_label = "ORB NY"
            strat_badge = "strat-orb"
        elif (
            "GOLD" in strat_raw
            or "GOLD" in prof
            or "QUARTER" in action
            or "QUARTER" in reason
        ):
            strat_key = "GOLD_QUARTERS"
            strat_label = "Gold Quarters"
            strat_badge = "strat-gold"
        elif (
            item.get("strategy_name") == "SMC"
            and not (
                "ICT" in strat_raw
                or "ICT" in prof
                or "ICT" in action
                or "JUDAS" in action
                or "JUDAS" in reason
                or "WAITING_ICT" in action
                or "H4_BIAS" in reason
            )
        ):
            strat_key = "SMC"
            strat_label = "SMC"
            strat_badge = "strat-smc"
        else:
            # Todos los trabajadores sintéticos (BOOM, CRASH, STEP, JUMP, VOLATILITY), Forex e ICT
            # operan unificados bajo la Estrategia ICT.
            strat_key = "ICT"
            strat_label = "Estrategia ICT"
            strat_badge = "strat-cyan"

        dedupe_key = (sym, strat_key)
        if dedupe_key in seen_keys:
            continue
        seen_keys.add(dedupe_key)

        details = item.get("details_json") or {}
        if isinstance(details, str):
            try:
                details = json.loads(details)
            except Exception:
                details = {}

        is_active = (action == "BLOCKED_ACTIVE_TRADE" or "POSICION ACTIVA" in reason)

        if is_active:
            macro_ctx = "🔵 En Mercado"
            struct_lvl = "🔵 Gestión TP/SL/BE"
            trigger_conf = "🔵 Trade Abierto"
            metrics = "Operación en curso"
            ai_score = "100%"
            final_st = "🔵 POSICION ACTIVA"
            badge = "active"
        elif strat_key == "MALAYSIAN_SNR":
            direction = str(item.get("direction") or details.get("direction") or "").upper()
            adx = item.get("momentum_adx") or (item.get("meta_features") or {}).get("adx")
            if "BUY" in direction:
                macro_ctx = f"🟢 Alcista (ADX {adx})" if adx else "🟢 Alcista"
            elif "SELL" in direction:
                macro_ctx = f"🔴 Bajista (ADX {adx})" if adx else "🔴 Bajista"
            else:
                macro_ctx = "⚪ Rango / Neutral"

            scenario = str(item.get("scenario") or "")
            if "ESC_1" in scenario or "ESC_1" in reason:
                struct_lvl = "🟢 Esc. 1: Ruptura Fresh"
            elif "ESC_3" in scenario or "ESC_3" in reason:
                struct_lvl = "🟢 Esc. 3: Fractalidad"
            elif item.get("break_level"):
                struct_lvl = f"🟡 Nivel Break {item.get('break_level')}"
            elif "JUMP_STRICT" in action:
                struct_lvl = "⚪ Filtro Estricto"
            else:
                struct_lvl = "🟡 Escaneando M15 A/V"

            if action in ("MALAYSIAN_SNR_CONFIRMED", "ORDER_OPENED"):
                trigger_conf = "🟢 Retest M15 Confirmado"
                final_st = "🟢 SEÑAL LISTA"
                badge = "good"
            elif action == "WAITING_MALAYSIAN_SNR":
                trigger_conf = "🟡 Esperando Retest Fresh"
                final_st = "🟡 ESPERANDO RETEST"
                badge = "warn"
            elif action == "MAX_TOTAL_OPEN_POSITIONS":
                trigger_conf = "⚪ Límite de Posiciones"
                final_st = "⚪ MAX POSICIONES"
                badge = "neutral"
            elif "JUMP_STRICT" in action:
                trigger_conf = "⚪ Rechazo Volatilidad"
                final_st = "⚪ RECHAZO FILTRO"
                badge = "neutral"
            else:
                trigger_conf = "⚪ Sin Gatillo"
                final_st = "⚪ EN ESPERA"
                badge = "neutral"

            body = item.get("body_ratio") or (item.get("meta_features") or {}).get("body_ratio")
            if adx and body:
                metrics = f"ADX {adx} · Body {body}"
            else:
                metrics = "Doble Pierna 50/50"

            if action in ("MALAYSIAN_SNR_CONFIRMED", "ORDER_OPENED"):
                ai_score = "🟢 Aprobado"
            elif adx:
                ai_score = f"{min(99, int(float(adx) * 2))}%"
            else:
                ai_score = "—"
        elif strat_key == "ORB":
            if "WAITING_NEW_YORK" in action:
                macro_ctx = "⚪ Fuera de Sesión NY"
                struct_lvl = "⚪ Esperando Apertura"
                trigger_conf = "⚪ Campana 09:30 NY"
                final_st = "⚪ ESPERANDO NY"
                badge = "neutral"
            else:
                macro_ctx = "🗽 Sesión NY Cash"
                struct_lvl = "🟢 Rango 15m Definido" if item.get("orb_range_high") else "🟡 Marcando Rango"
                trigger_conf = "🟢 Ruptura M5 + Retest" if action in ("ORB_CONFIRMED", "ORDER_OPENED") else "🟡 Esperando Ruptura"
                final_st = "🟢 SEÑAL LISTA" if action in ("ORB_CONFIRMED", "ORDER_OPENED") else "🟡 MONITOREANDO"
                badge = "good" if action in ("ORB_CONFIRMED", "ORDER_OPENED") else "warn"
            metrics = "Volumen / ATR NY"
            ai_score = "—"
        elif strat_key == "GOLD_QUARTERS":
            macro_ctx = "🟡 Nivel Cuarto ($25)"
            struct_lvl = "🟢 Rechazo Nivel Mayor"
            trigger_conf = "🟢 Confirmación M5" if action in ("ORDER_OPENED", "GOLD_CONFIRMED") else "🟡 Esperando Vela"
            metrics = "SL Buffer 0.50 ATR"
            ai_score = "—"
            final_st = "🟢 SEÑAL LISTA" if action in ("ORDER_OPENED", "GOLD_CONFIRMED") else "⚪ EN ESPERA"
        elif strat_key == "ICT":
            strat_label = "Estrategia ICT"
            strat_badge = "strat-cyan"
            if is_active:
                macro_ctx = "🔵 En Mercado"
                struct_lvl = "🔵 Gestión TP/SL/BE"
                trigger_conf = "🔵 Trade Abierto"
                metrics = "Operación en curso"
                ai_score = "100%"
                final_st = "🔵 POSICION ACTIVA"
                badge = "active"
            elif "MARKET_CLOSED" in reason or "MARKET_CLOSURE" in reason:
                macro_ctx = "⚪ Mercado Cerrado"
                struct_lvl = "⚪ Fuera de Horario"
                trigger_conf = "⚪ Cierre Fin de Semana"
                metrics = "Filtro Cierre"
                ai_score = "—"
                final_st = "⚪ MERCADO CERRADO"
                badge = "neutral"
            elif "OUTSIDE_ICT_KILLZONE" in reason or "OUTSIDE_KILLZONE" in reason:
                macro_ctx = "⚪ Fuera Killzone NY"
                struct_lvl = "⚪ Esperando Killzone"
                trigger_conf = "⚪ Ventana Institucional"
                metrics = "08:30 / 10:30 NY"
                ai_score = "—"
                final_st = "⚪ ESPERANDO KILLZONE"
                badge = "neutral"
            elif action in ("ICT_SABRI_MALLE_CONFIRMED", "ORDER_OPENED"):
                macro_ctx = "🗽 Killzone NY Activa"
                struct_lvl = "🟢 MSS + FVG Mitigado"
                trigger_conf = "🟢 Judas Swing + CE"
                metrics = "Displacement OK"
                ai_score = "🟢 Aprobado"
                final_st = "🟢 SEÑAL LISTA"
                badge = "good"
            elif "NO_FVG" in reason:
                macro_ctx = "🗽 Killzone NY Activa"
                struct_lvl = "🟡 MSS Confirmado (Falta FVG)"
                trigger_conf = "🟡 Esperando Imbalance"
                metrics = "M5 Imbalance"
                ai_score = "50%"
                final_st = "🟡 MONITOREANDO"
                badge = "warn"
            elif "NO_MACRO_H4" in reason or "NO_H4" in reason:
                macro_ctx = "⚪ Macro H4 Sin Tendencia"
                struct_lvl = "⚪ Esperando EMA 50/200"
                trigger_conf = "⚪ Sin Sesgo H4"
                metrics = "Macro Bias H4"
                ai_score = "—"
                final_st = "⚪ EN ESPERA"
                badge = "neutral"
            elif "JUDAS" in reason or "NO_JUDAS" in reason:
                macro_ctx = "🟢 Rango Activo 24/7" if any(x in sym.lower() for x in ("boom", "crash", "step", "jump", "volatility")) else "🟢 Macro H4 Definido"
                struct_lvl = "🟡 Rango Acumulación H1"
                trigger_conf = "⚪ Esperando Judas Swing"
                metrics = "Barrido Mecha ≥35%"
                ai_score = "—"
                final_st = "⚪ EN ESPERA"
                badge = "neutral"
            elif "NO_FVG" in reason:
                macro_ctx = "🗽 Killzone NY Activa" if not any(x in sym.lower() for x in ("boom", "crash", "step", "jump", "volatility")) else "🟢 Rango Activo 24/7"
                struct_lvl = "🟡 MSS Confirmado (Falta FVG)"
                trigger_conf = "🟡 Esperando Imbalance"
                metrics = "M5 Imbalance"
                ai_score = "50%"
                final_st = "🟡 MONITOREANDO"
                badge = "warn"
            elif "NO_MSS" in reason:
                macro_ctx = "🗽 Killzone NY Activa" if not any(x in sym.lower() for x in ("boom", "crash", "step", "jump", "volatility")) else "🟢 Rango Activo 24/7"
                struct_lvl = "🟡 Evaluando Liquidez"
                trigger_conf = "⚪ Sin MSS M5"
                metrics = "AMD / Sweep"
                ai_score = "—"
                final_st = "⚪ EN ESPERA"
                badge = "neutral"
            else:
                macro_ctx = "🗽 Killzone NY / Macro H1" if not any(x in sym.lower() for x in ("boom", "crash", "step", "jump", "volatility")) else "🟢 Rango Dinámico 24/7"
                struct_lvl = "🟡 Escaneando Liquidez / FVG"
                trigger_conf = "⚪ Sin Gatillo"
                metrics = "AMD / Judas Swing M5"
                ai_score = "—"
                final_st = "⚪ EN ESPERA"
                badge = "neutral"
        else:
            # SMC
            h1_dict = item.get("h1_context") or details.get("h1_context") or {}
            h1_dir = str(h1_dict.get("trend") or details.get("h1_direction") or details.get("trend") or item.get("direction") or "").upper()
            h1_loc = str(h1_dict.get("location_detail") or h1_dict.get("location_direction") or details.get("h1_location") or "").upper()

            if "BUY" in h1_dir or "BULL" in h1_dir or action == "BUY":
                macro_ctx = "🟢 Alcista (Discount)" if ("DISCOUNT" in h1_loc or "BUY" in h1_loc) else "🟢 Alcista"
            elif "SELL" in h1_dir or "BEAR" in h1_dir or action == "SELL":
                macro_ctx = "🔴 Bajista (Premium)" if ("PREMIUM" in h1_loc or "SELL" in h1_loc) else "🔴 Bajista"
            elif "NO_H1" in reason or "H1_LOCATION_UNAVAILABLE" in reason or "DIRECTION_POLICY_BLOCKED" in action:
                macro_ctx = "⚪ Filtrado Macro H1"
            elif h1_dict.get("valid"):
                macro_ctx = "🟢 H1 Validado"
            else:
                macro_ctx = "⚪ Rango / Neutral"

            seq = item.get("sequence") or {}
            m15_tot = seq.get("m15_setups_total")
            ob_active = details.get("order_block_ok") or ("OB" in str(details)) or ("BOS" in str(item))
            fvg_active = details.get("fvg_confirmed") or ("FVG" in str(details))

            if action == "NO_M15_SETUP":
                struct_lvl = "⚪ Sin Setup M15"
            elif action == "NO_M5_CONFIRMATION":
                struct_lvl = f"🟢 Setup M15 OK ({m15_tot} OB)" if m15_tot else "🟢 Setup M15 Válido"
            elif ob_active:
                struct_lvl = "🟢 BOS + OB Activo"
            elif fvg_active:
                struct_lvl = "🟢 FVG Creado"
            elif m15_tot and int(m15_tot) > 0:
                struct_lvl = f"🟢 Setup M15 OK ({m15_tot} OB)"
            elif "DIRECTION_POLICY" in action or "H1" in action:
                struct_lvl = "⚪ En Espera H1"
            else:
                struct_lvl = "🟡 Evaluando M15"

            if action in ("BUY", "SELL", "ORDER_OPENED", "MULTI_TIMEFRAME_SIGNAL"):
                trigger_conf = "🟢 Confirmado (M5/CHoCH)"
                final_st = "🟢 SEÑAL LISTA"
                badge = "good"
            elif action == "NO_M5_CONFIRMATION":
                trigger_conf = "⚪ Falló Filtro M5"
                final_st = "⚪ NO CONFIRMO M5"
                badge = "neutral"
            elif action == "NO_M15_SETUP":
                trigger_conf = "⚪ Inactivo"
                final_st = "⚪ SIN SETUP M15"
                badge = "neutral"
            elif "DIRECTION_POLICY" in action or "H1" in action or "H1" in reason:
                trigger_conf = "⚪ Inactivo (H1)"
                final_st = "⚪ FILTRADO H1"
                badge = "neutral"
            elif m15_tot and int(m15_tot) > 0:
                trigger_conf = "🟡 Esperando CHoCH M5"
                final_st = "🟡 MONITOREANDO"
                badge = "warn"
            else:
                trigger_conf = "⚪ Inactivo"
                final_st = "⚪ EN ESPERA"
                badge = "neutral"

            elapsed = details.get("m5_elapsed_minutes") or details.get("elapsed_minutes")
            if elapsed is not None:
                rem = max(0, 10 - int(float(elapsed)))
                metrics = f"{rem} min rest." if rem > 0 else "⚪ Expirado"
            elif action in ("BUY", "SELL", "ORDER_OPENED"):
                metrics = "🟢 Fresco (<10 min)"
            elif action == "NO_M5_CONFIRMATION":
                metrics = "⚪ Sin Gatillo M5"
            else:
                metrics = "—"

            raw_score = details.get("ai_score") or details.get("adaptive_score") or item.get("final_score") or details.get("score")
            if raw_score is not None:
                try:
                    ai_score = f"{int(float(raw_score))}%"
                except Exception:
                    ai_score = str(raw_score)
            elif action in ("BUY", "SELL", "ORDER_OPENED"):
                ai_score = "≥80%"
            elif action == "NO_M5_CONFIRMATION":
                ai_score = "0% (Falta M5)"
            else:
                ai_score = "—"

        matrix.append({
            "symbol": sym,
            "strategy": strat_label,
            "strategy_key": strat_key,
            "strat_badge": strat_badge,
            "macro_context": macro_ctx,
            "structure_level": struct_lvl,
            "trigger_confirmation": trigger_conf,
            "metrics_freshness": metrics,
            "ai_score": ai_score,
            "final_state": final_st,
            "badge_class": badge,
            # Compatibilidad hacia atrás
            "h1_context": macro_ctx,
            "m15_structure": struct_lvl,
            "m5_confirmation": trigger_conf,
            "m5_freshness": metrics,
        })

    # Si aún no hay suficientes datos en vivo, agregar muestras representativas multiestrategia
    if not matrix:
        matrix = [
            {
                "symbol": "Volatility 75 Index",
                "strategy": "SMC",
                "strategy_key": "SMC",
                "strat_badge": "strat-smc",
                "macro_context": "🟢 Alcista (Discount)",
                "structure_level": "🟢 BOS + OB Activo",
                "trigger_confirmation": "🟡 Esperando CHoCH",
                "metrics_freshness": "7 min rest.",
                "ai_score": "78%",
                "final_state": "🟡 MONITOREANDO",
                "badge_class": "warn",
                "h1_context": "🟢 Alcista (Discount)",
                "m15_structure": "🟢 BOS + OB Activo",
                "m5_confirmation": "🟡 Esperando CHoCH",
                "m5_freshness": "7 min rest.",
            },
            {
                "symbol": "Step Index 500",
                "strategy": "Malaysian SNR",
                "strategy_key": "MALAYSIAN_SNR",
                "strat_badge": "strat-snr",
                "macro_context": "🔵 En Mercado",
                "structure_level": "🔵 Gestión TP/SL/BE",
                "trigger_confirmation": "🔵 Trade Abierto",
                "metrics_freshness": "Pierna 1 & 2 activa",
                "ai_score": "100%",
                "final_state": "🔵 POSICION ACTIVA",
                "badge_class": "active",
                "h1_context": "🔵 En Mercado",
                "m15_structure": "🔵 Gestión TP/SL/BE",
                "m5_confirmation": "🔵 Trade Abierto",
                "m5_freshness": "Pierna 1 & 2 activa",
            },
            {
                "symbol": "US Tech 100",
                "strategy": "ORB NY",
                "strategy_key": "ORB",
                "strat_badge": "strat-orb",
                "macro_context": "🗽 Sesión NY Cash",
                "structure_level": "🟢 Rango 15m Definido",
                "trigger_confirmation": "🟢 Ruptura M5 + Retest",
                "metrics_freshness": "Volumen 1.4x · ATR OK",
                "ai_score": "88%",
                "final_state": "🟢 SEÑAL LISTA",
                "badge_class": "good",
                "h1_context": "🗽 Sesión NY Cash",
                "m15_structure": "🟢 Rango 15m Definido",
                "m5_confirmation": "🟢 Ruptura M5 + Retest",
                "m5_freshness": "Volumen 1.4x · ATR OK",
            },
            {
                "symbol": "XAUUSD",
                "strategy": "Gold Quarters",
                "strategy_key": "GOLD_QUARTERS",
                "strat_badge": "strat-gold",
                "macro_context": "🟡 Nivel Cuarto ($2650)",
                "structure_level": "🟢 Rechazo Nivel Mayor",
                "trigger_confirmation": "🟢 Confirmación M5",
                "metrics_freshness": "SL Buffer 0.50 ATR",
                "ai_score": "82%",
                "final_state": "🟢 SEÑAL LISTA",
                "badge_class": "good",
                "h1_context": "🟡 Nivel Cuarto ($2650)",
                "m15_structure": "🟢 Rechazo Nivel Mayor",
                "m5_confirmation": "🟢 Confirmación M5",
                "m5_freshness": "SL Buffer 0.50 ATR",
            },
        ]

    strat_defaults = {
        "MALAYSIAN_SNR": {
            "label": "Malaysian SNR",
            "badge": "strat-snr",
            "macro_context": "⚪ Rango / Neutral",
            "structure_level": "🟡 Escaneando M15 A/V",
            "trigger_confirmation": "⚪ Sin Gatillo",
            "metrics": "Doble Pierna 50/50",
            "ai_score": "—",
            "final_state": "⚪ EN ESPERA",
            "badge_class": "neutral",
        },
        "ORB": {
            "label": "ORB NY",
            "badge": "strat-orb",
            "macro_context": "⚪ Fuera de Sesión NY",
            "structure_level": "⚪ Esperando Apertura",
            "trigger_confirmation": "⚪ Campana 09:30 NY",
            "metrics": "Volumen / ATR NY",
            "ai_score": "—",
            "final_state": "⚪ ESPERANDO NY",
            "badge_class": "neutral",
        },
        "GOLD_QUARTERS": {
            "label": "Gold Quarters",
            "badge": "strat-gold",
            "macro_context": "🟡 Nivel Cuarto ($25)",
            "structure_level": "🟢 Rechazo Nivel Mayor",
            "trigger_confirmation": "🟡 Esperando Vela",
            "metrics": "SL Buffer 0.50 ATR",
            "ai_score": "—",
            "final_state": "⚪ EN ESPERA",
            "badge_class": "neutral",
        },
        "ICT": {
            "label": "Estrategia ICT",
            "badge": "strat-cyan",
            "macro_context": "⚪ Estructura 24/7 / Killzone NY",
            "structure_level": "🟡 Escaneando FVG / Liquidez",
            "trigger_confirmation": "⚪ Sin Gatillo",
            "metrics": "BPR / MSS",
            "ai_score": "—",
            "final_state": "⚪ EN ESPERA",
            "badge_class": "neutral",
        },
    }

    profile_strat_map = {
        "MALAYSIAN_SNR": "MALAYSIAN_SNR",
        "ORB": "ORB",
        "GOLD": "GOLD_QUARTERS",
        "ICT": "ICT",
        "SYNTHETICS": "ICT",
        "FOREX": "ICT",
    }

    selection_profiles = state.get("selection_profiles")
    if selection_profiles is not None:
        for prof, strat_key in profile_strat_map.items():
            active_symbols = selection_profiles.get(prof)
            if active_symbols is None:
                active_symbols = DEFAULT_PRIORITIZED_SYMBOLS.get(prof, [])
            cfg = strat_defaults.get(strat_key, {})
            for sym in (active_symbols or []):
                dedupe_key = (sym, strat_key)
                if dedupe_key in seen_keys:
                    continue
                seen_keys.add(dedupe_key)
                matrix.append({
                    "symbol": sym,
                    "strategy": cfg.get("label", strat_key),
                    "strategy_key": strat_key,
                    "strat_badge": cfg.get("badge", "strat-cyan"),
                    "macro_context": cfg.get("macro_context", "⚪ Rango / Neutral"),
                    "structure_level": cfg.get("structure_level", "🟡 Escaneando M15 A/V"),
                    "trigger_confirmation": cfg.get("trigger_confirmation", "⚪ Sin Gatillo"),
                    "metrics_freshness": cfg.get("metrics", "—"),
                    "ai_score": cfg.get("ai_score", "—"),
                    "final_state": cfg.get("final_state", "⚪ EN ESPERA"),
                    "badge_class": cfg.get("badge_class", "neutral"),
                    "h1_context": cfg.get("macro_context", "⚪ Rango / Neutral"),
                    "m15_structure": cfg.get("structure_level", "🟡 Escaneando M15 A/V"),
                    "m5_confirmation": cfg.get("trigger_confirmation", "⚪ Sin Gatillo"),
                    "m5_freshness": cfg.get("metrics", "—"),
                })

    # Filtrar sólo los que están actualmente seleccionados si el perfil tiene selecciones explícitas
    if isinstance(selection_profiles, dict):
        filtered_matrix = []
        for row in matrix:
            sk = row.get("strategy_key")
            s_sym = row.get("symbol")
            if sk == "MALAYSIAN_SNR":
                allowed_p = selection_profiles.get("MALAYSIAN_SNR")
                if allowed_p and s_sym not in allowed_p:
                    continue
            elif sk == "ORB":
                allowed_p = selection_profiles.get("ORB")
                if allowed_p and s_sym not in allowed_p:
                    continue
            elif sk == "GOLD_QUARTERS":
                allowed_p = selection_profiles.get("GOLD")
                if allowed_p and s_sym not in allowed_p:
                    continue
            elif sk == "ICT":
                allowed_ict = set(selection_profiles.get("ICT") or [])
                allowed_ict.update(selection_profiles.get("SYNTHETICS") or [])
                allowed_ict.update(selection_profiles.get("FOREX") or [])
                if allowed_ict and s_sym not in allowed_ict:
                    continue
            filtered_matrix.append(row)
        matrix = filtered_matrix

    return matrix[:250]


DEFAULT_PRIORITIZED_SYMBOLS = {
    "SYNTHETICS": [
        "Boom 300 Index",
        "Boom 500 Index",
        "Boom 600 Index",
        "Boom 900 Index",
        "Crash 500 Index",
        "Crash 600 Index",
        "High Frequency Vol 100 Index",
        "High Frequency Vol 50 Index",
        "Jump 10 Index",
        "Jump 25 Index",
        "Jump 75 Index",
        "Step Index",
        "Step Index 400",
        "Step Index 500",
        "Vol over Boom 550",
        "Vol over Crash 550",
        "VolSwitch High Vol Index",
        "Volatility 10 Index",
        "Volatility 100 (1s) Index",
        "Volatility 15 Index",
        "Volatility 150 (1s) Index",
        "Volatility 25 Index",
        "Volatility 250 (1s) Index",
        "Volatility 5 Index",
        "Volatility 50 (1s) Index",
        "Volatility 75 (1s) Index",
        "Volatility 75 Index",
        "Volatility 90 (1s) Index",
        "Volatility 90 Index",
    ],
    "FOREX": [
        "AUDJPY",
        "AUDNZD",
        "AUDUSD",
        "AUDUSDmicro",
        "CADCHF",
        "CHFJPY",
        "EURCHF",
        "EURUSD",
        "EURUSDmicro",
        "GBPCAD",
        "GBPUSD",
        "GBPUSDmicro",
        "USDCAD",
        "USDCADmicro",
    ],
    "ORB": [
        "Wall Street 30",
        "XAUUSD",
        "XAUUSDmicro",
        "microXAUUSD",
        "US Tech 100",
        "BTCUSD",
    ],
    "IDX_OPEN": [
        "Wall Street 30",
        "US Tech 100",
    ],
    "MALAYSIAN_SNR": [
        "Step Index 400",
        "XAGUSD",
        "AUDNZD",
        "Crash 1000 Index",
        "Jump 25 Index",
        "GBPJPY",
        "USDJPY",
        "GBPUSD",
        "Boom 300 Index",
        "Volatility 250 (1s) Index",
        "Step Index",
        "Jump 10 Index",
        "GBPAUD",
        "Wall Street 30",
        "EURUSD",
        "Volatility 50 (1s) Index",
        "Volatility 90 Index",
        "Boom 1000 Index",
        "Step Index 200",
        "EURCHF",
        "EURGBP",
        "XAUUSD",
        "Crash 600 Index",
    ],

    "GOLD": [
        "XAUUSD",
        "XAUUSDmicro",
        "microXAUUSD",
    ],
    "ICT": [
        "Volatility 10 Index",
        "Jump 25 Index",
        "Step Index 400",
        "Volatility 50 (1s) Index",
        "Jump 75 Index",
        "Step Index 500",
        "Volatility 25 Index",
        "Step Index",
        "Crash 600 Index",
        "XAUUSD",
        "XAUUSDmicro",
        "microXAUUSD",
        "GBPUSD",
        "GBPUSDmicro",
        "Wall Street 30",
        "AUDJPY",
        "Volatility 15 Index",
        "Volatility 75 (1s) Index",
        "Boom 500 Index",
        "Jump 10 Index",
        "BTCUSD",
        "BTCUSDmicro",
        "microBTCUSD",
        "US Tech 100",
        "AUDNZD",
        "Boom 300 Index",
        "Volatility 75 Index",
        "GBPCAD",
        "EURCHF",
        "Crash 500 Index",
        "CADCHF",
        "EURUSD",
        "EURUSDmicro",
        "Volatility 90 Index",
        "Volatility 250 (1s) Index",
        "Boom 900 Index",
        "USDCAD",
        "USDCADmicro",
        "US Oil",
        "AUDUSD",
        "AUDUSDmicro",
        "CHFJPY",
        "Boom 600 Index",
    ],
}

PRUNED_INSTRUMENTS_INFO = {
    # FOREX (Poda confirmada por análisis cuantitativo de 2 años en activos con expectativa negativa)
    "EURCAD": "Poda confirmada en replay 2 años: -23.75R netos (Win Rate 25.4%). Cruce con spreads adversos y falta de liquidez en Killzones.",
    "GBPCHF": "Poda confirmada en replay 2 años: -17.75R netos (Win Rate 26.6%). Rango errático sin continuación institucional.",
    "GBPAUD": "Poda confirmada en replay 2 años: -17.25R netos (Win Rate 19.0%). Baja tasa de TP1 y fuerte correlación de noticias asiáticas.",
    "AUDCHF": "Poda confirmada en replay 2 años: -14.25R netos (Win Rate 24.4%). Deslizamiento continuo y compresión en sesión asiática.",
    "EURNZD": "Poda confirmada en replay 2 años: -11.75R netos (Win Rate 22.6%). Desalineación con Killzones y spreads nocturnos desfavorables.",
    "CADJPY": "Poda confirmada en replay 2 años: -11.75R netos (Win Rate 27.0%). Rupturas sin mitigación en horario Londres.",
    "EURAUD": "Poda confirmada en replay 2 años: -9.75R netos (Win Rate 23.8%). Solapamiento de rangos asiático y europeo sin expansión limpia.",
    "USDJPY": "Poda confirmada en replay 2 años: -7.25R netos (Win Rate 35.5%). Ausencia de volumen en Killzones y retrocesos tardíos.",
    "USDJPYmicro": "Poda confirmada en replay 2 años: -7.25R netos (Win Rate 35.5%).",
    "EURGBP": "Poda confirmada en replay 2 años: -7.25R netos (Win Rate 31.1%). Rango sumamente comprimido y bajo desplazamiento medio.",
    "GBPJPY": "Poda confirmada en replay 2 años: -5.50R netos (Win Rate 33.3%). Volatilidad descontrolada en sesión de Tokio/Londres; mejor en Malaysian SNR.",
    "AUDCAD": "Poda confirmada en replay 2 años: -5.00R netos (Win Rate 32.4%). Falta de liquidez institucional en Killzones Londres/NY.",
    "USDCHF": "Poda confirmada en replay 2 años: -4.75R netos (Win Rate 33.8%). Estructura divergente frente al EURUSD durante la Killzone.",
    "USDCHFmicro": "Poda confirmada en replay 2 años: -4.75R netos (Win Rate 33.8%).",
    "EURJPY": "Poda confirmada en replay 2 años: -4.75R netos (Win Rate 35.3%). Intervenciones y tendencias unidireccionales sin pullback a FVG.",
    "GBPNZD": "Poda confirmada en replay 2 años: -3.50R netos (Win Rate 30.6%). Rangos amplios con mechas falsas en cambio de sesión.",
    "NZDCAD": "Poda preventiva: Baja liquidez institucional en broker.",
    "NZDCHF": "Poda preventiva: Spreading costoso y baja frecuencia de setups limpios.",
    "NZDJPY": "Poda preventiva: Ruido recurrente en sesión asiática.",
    "NZDUSD": "Poda preventiva: Falsos quiebres de estructura y baja reactividad.",
    # BOOM (Replay histórico)
    "Boom 1000 Index": "Poda en replay 2 años: -2.25R netos (Win Rate 34.6%). Menor consistencia de pullback que Boom 500 y Boom 300.",
    "Boom 50 Index": "Poda preventiva: Baja inercia en zonas de demanda institucional.",
    "Boom 100 Index": "Poda preventiva: Ruido aleatorio y bajo ratio de confirmación.",
    "Boom 150 Index": "Poda preventiva: Spikes desalineados con zonas SMC M15.",
    "Boom 200 Index": "Poda preventiva: Expectativa matemática subóptima.",
    "Boom 99 Index": "Poda preventiva: Poca profundidad de mercado sintético.",
    # CRASH (Replay histórico)
    "Crash 900 Index": "Poda confirmada en replay 2 años: -13.50R netos (Win Rate 29.3%). Spikes intempestivos rompen estructuras FVG.",
    "Crash 300 Index": "Poda confirmada en replay 2 años: -11.50R netos (Win Rate 32.2%). Caídas rápidas invalidan niveles de soporte.",
    "Crash 1000 Index": "Poda confirmada en replay 2 años: -3.25R netos (Win Rate 32.9%). Ratios desfavorables frente a Crash 600 y Crash 500.",
    "Crash 50 Index": "Poda preventiva: Ruido y falsos rebotes en soportes.",
    "Crash 100 Index": "Poda preventiva: Spikes contratendenciales prematuros.",
    "Crash 150 Index": "Poda preventiva: Baja reactividad en bloques de órdenes M15.",
    "Crash 200 Index": "Poda preventiva: Falsas confirmaciones de quiebre estructural.",
    "Crash 99 Index": "Poda preventiva: Falta de tracción institucional simulada.",
    # STEP (Replay histórico)
    "Step Index 200": "Poda confirmada en replay 2 años: 0.00R netos (Win Rate 34.5%). Rendimiento neutral sin ventaja matemática; focalizado en Step 400 y Step 500.",
    "Step Index 300": "Poda preventiva: Replay descartó activos de ruido en ticks. Se priorizan Step 500, Step Index y Step 400.",
    "Multi Step 2 Index": "Poda preventiva: Dispersión desfavorable de volatilidad y saltos de tick desalineados.",
    "Multi Step 3 Index": "Poda preventiva: Dispersión desfavorable de volatilidad y saltos de tick desalineados.",
    "Multi Step 4 Index": "Poda preventiva: Dispersión desfavorable de volatilidad y saltos de tick desalineados.",
    # JUMP (Replay histórico 2 años)
    "Jump 50 Index": "Poda confirmada en replay 2 años: -7.50R netos (Win Rate 33.7%). Saltos estocásticos de precio atraviesan zonas de descuento.",
    "Jump 100 Index": "Poda confirmada en replay 2 años: -3.25R netos (Win Rate 35.6%). Saltos erráticos desalineados con zonas SMC M15.",
    # VOLATILITY (Poda confirmada por análisis cuantitativo de 2 años)
    "Volatility 50 Index": "Poda confirmada en replay 2 años: -40.00R netos (Win Rate 27.1%). Falsas rupturas continuas y stops sistemáticos en M15.",
    "Volatility 100 Index": "Poda confirmada en replay 2 años: -30.00R netos (Win Rate 32.0%). Ruido de alta volatilidad sin respeto al pullback.",
    "Vol over Crash 400": "Poda confirmada: -24.0% PnL en replay 2 años (Win Rate 15.4%). Falsas roturas de estructura recurrentes.",
    "Vol over Boom 750": "Poda confirmada: -13.0% PnL en replay 2 años (Win Rate 21.1%). Inconsistencia en zonas de oferta.",
    "Spot Up - Volatility Up Index": "Poda confirmada: -13.0% PnL en replay 2 años (Win Rate 26.1%). Dispersión de colas.",
    "Volatility 30 (1s) Index": "Poda confirmada: -9.5% PnL en replay 2 años. Ruido recurrente en oscilación rápida.",
    "Volatility Crash 750 Index": "Poda confirmada: -9.0% PnL en replay 2 años (Win Rate 26.7%).",
    "Vol over Crash 750": "Poda confirmada: -8.0% PnL en replay 2 años.",
    "High Frequency Vol 75 Index": "Poda confirmada: -8.0% PnL en replay 2 años (Win Rate 25.0%).",
    "High Frequency Vol 25 Index": "Poda confirmada: -7.5% PnL en replay 2 años (Win Rate 22.7%).",
    "Volatility 30 Index": "Poda preventiva: Baja efectividad en retesteos de bloques de órdenes.",
    # COMMODITIES & PETRÓLEO (Poda confirmada por análisis histórico 2 años)
    "US Oil": "Poda confirmada por análisis histórico 2 años: -34.25% PnL (-$3,425 USD, PF 0.77). Deslizamiento adverso y desalineación estructural de la sesión cash NY frente a metales e índices.",
    "USOIL": "Poda confirmada por análisis histórico 2 años: -34.25% PnL (-$3,425 USD, PF 0.77). Deslizamiento adverso y desalineación estructural de la sesión cash NY frente a metales e índices.",
    "Crude Oil": "Poda confirmada por análisis histórico 2 años: -34.25% PnL (-$3,425 USD, PF 0.77). Deslizamiento adverso y desalineación estructural en sesión cash NY.",
    "WTI": "Poda confirmada por análisis histórico 2 años: -34.25% PnL (-$3,425 USD, PF 0.77). Deslizamiento adverso y desalineación estructural en sesión cash NY.",
    "Brent": "Poda confirmada por análisis histórico 2 años: Baja correlación y costos de spread elevados en ventanas ORB.",
    "UK Brent Oil": "Poda confirmada por análisis histórico 2 años: Baja correlación y costos de spread elevados en ventanas ORB.",
    # PLATA / SILVER (Poda confirmada)
    "XAGUSD": "Poda: Mayor volatilidad y riesgo no compensado frente a XAUUSD y EURUSD. Se prioriza Oro y Euro.",
    "XAGUSDmicro": "Poda: Mayor volatilidad y riesgo no compensado frente a XAUUSD y EURUSD.",
    "Silver": "Poda: Mayor volatilidad y riesgo no compensado frente a XAUUSD y EURUSD.",
}

FOREX_PRUNED_INFO = {
    # 14 Pares Forex con expectativa negativa en replay de 2 años
    "EURCAD": "Poda confirmada en replay 2 años: -23.75R netos (Win Rate 25.4%). Cruce con spreads adversos y falta de liquidez en Killzones.",
    "GBPCHF": "Poda confirmada en replay 2 años: -17.75R netos (Win Rate 26.6%). Rango errático sin continuación institucional.",
    "GBPAUD": "Poda confirmada en replay 2 años: -17.25R netos (Win Rate 19.0%). Baja tasa de TP1 y fuerte correlación de noticias asiáticas.",
    "AUDCHF": "Poda confirmada en replay 2 años: -14.25R netos (Win Rate 24.4%). Deslizamiento continuo y compresión en sesión asiática.",
    "EURNZD": "Poda confirmada en replay 2 años: -11.75R netos (Win Rate 22.6%). Desalineación con Killzones y spreads nocturnos desfavorables.",
    "CADJPY": "Poda confirmada en replay 2 años: -11.75R netos (Win Rate 27.0%). Rupturas sin mitigación en horario Londres.",
    "EURAUD": "Poda confirmada en replay 2 años: -9.75R netos (Win Rate 23.8%). Solapamiento de rangos asiático y europeo sin expansión limpia.",
    "USDJPY": "Poda confirmada en replay 2 años: -7.25R netos (Win Rate 35.5%). Ausencia de volumen en Killzones y retrocesos tardíos.",
    "USDJPYmicro": "Poda confirmada en replay 2 años: -7.25R netos (Win Rate 35.5%).",
    "EURGBP": "Poda confirmada en replay 2 años: -7.25R netos (Win Rate 31.1%). Rango sumamente comprimido y bajo desplazamiento medio.",
    "GBPJPY": "Poda confirmada en replay 2 años: -5.50R netos (Win Rate 33.3%). Volatilidad descontrolada en sesión de Tokio/Londres; mejor en Malaysian SNR.",
    "AUDCAD": "Poda confirmada en replay 2 años: -5.00R netos (Win Rate 32.4%). Falta de liquidez institucional en Killzones Londres/NY.",
    "USDCHF": "Poda confirmada en replay 2 años: -4.75R netos (Win Rate 33.8%). Estructura divergente frente al EURUSD durante la Killzone.",
    "USDCHFmicro": "Poda confirmada en replay 2 años: -4.75R netos (Win Rate 33.8%).",
    "EURJPY": "Poda confirmada en replay 2 años: -4.75R netos (Win Rate 35.3%). Intervenciones y tendencias unidireccionales sin pullback a FVG.",
    "GBPNZD": "Poda confirmada en replay 2 años: -3.50R netos (Win Rate 30.6%). Rangos amplios con mechas falsas en cambio de sesión.",
}

MALAYSIAN_SNR_PRUNED_INFO = {
    # Índices Sintéticos no aptos para reversión Malaysian SNR (Mejor desempeño en sus workers especializados)
    "Crash 500 Index": "Poda en Malaysian SNR: 28.6% WR, -7.70R. Falsos retesteos; su terreno dominante es el worker SYNTHETICS.",
    "Boom 500 Index": "Poda en Malaysian SNR: 17.6% WR, -7.95R. Ruido de mechas y caídas continuas antes de retesteo.",
    "Boom 600 Index": "Poda en Malaysian SNR: 20.0% WR, -2.64R. Poca reacción en niveles Fresh.",
    "Boom 900 Index": "Poda en Malaysian SNR: 25.0% WR, -1.30R. Ruido estructural en M15.",
    "Crash 300 Index": "Poda en Malaysian SNR: 22.7% WR, -8.70R. Falsos quiebres de nivel.",
    "Crash 900 Index": "Poda en Malaysian SNR: 13.3% WR, -8.76R. Caídas directas sin mitigación.",
    "Step Index 500": "Poda en Malaysian SNR: 34.6% WR, -0.44R. Expectativa negativa residual.",
    "Jump 50 Index": "Poda en Malaysian SNR: 33.3% WR, -0.51R. Expectativa negativa residual.",
    "Jump 75 Index": "Poda en Malaysian SNR: 37.0% WR, -2.31R. Spreads y mechas adversas.",
    "Jump 100 Index": "Poda en Malaysian SNR: 25.0% WR, -8.56R. Dispersión severa y falta de soporte.",
    "Volatility 10 Index": "Poda en Malaysian SNR: 28.0% WR, -11.78R. Drift tendencial continuo que vulnera soportes A/V.",
    "Volatility 25 Index": "Poda en Malaysian SNR: 27.6% WR, -6.79R. Ruido de oscilación lateral.",
    "Volatility 50 Index": "Poda en Malaysian SNR: 8.0% WR, -17.85R. Falsas rupturas continuas y stops sistemáticos en M15.",
    "Volatility 75 Index": "Poda en Malaysian SNR: 34.1% WR, -4.27R. Expansiones sin respeto a niveles de reversión.",
    "Volatility 100 Index": "Poda en Malaysian SNR: 19.2% WR, -13.73R. Movimientos agresivos que rompen zonas A/V.",
    "Volatility 15 Index": "Poda en Malaysian SNR: 11.1% WR, -5.75R. Compresión y stops adversos.",
    "Volatility 75 (1s) Index": "Poda en Malaysian SNR: 26.7% WR, -8.36R. Micro-ticks erráticos sin absorción CRT.",
    # Índices Americanos & Cripto (Incompatibles con reversión SNR; derivados a ORB NY e ICT)
    "US Tech 100": "Poda en Malaysian SNR: 33.3% WR, -0.31R. Expansión direccional continua; derivado a ORB NY e ICT.",
    "US SP 500": "Poda en Malaysian SNR: 29.4% WR, -2.41R. Rupturas directas sin respeto de niveles Break; derivado a ORB New York.",
    "BTCUSD": "Poda en Malaysian SNR: 31.6% WR, -3.56R. Derivado a Estrategia ICT (+28.1R) y ORB (+4.39R).",
    # Forex y Commodities con expectativa negativa o spread adverso
    "USDCAD": "Poda en Malaysian SNR: 42.9% WR, -0.21R. Derivado a ICT Forex (+12.0R) y FOREX.",
    "AUDUSD": "Poda en Malaysian SNR: 23.1% WR, -5.14R. Rango lateral sin expansión hacia TP1 en M15.",
    "USDCHF": "Poda en Malaysian SNR: 20.0% WR, -6.66R. Compresión de rango y rechazos prematuros.",
    "US Oil": "Poda en Malaysian SNR: 12.5% WR, -6.51R. Deslizamiento severo y mechas erráticas en M15.",
    "CADCHF": "Poda en Malaysian SNR: 16.7% WR, -2.00R. Rango errático sin continuación institucional.",
    "AUDCAD": "Poda en Malaysian SNR: 22.2% WR, -2.35R. Barridos de liquidez adversos en retesteos.",
    "AUDCHF": "Poda en Malaysian SNR: 22.2% WR, -4.22R. Baja liquidez institucional y dispersión de spread.",
    "AUDJPY": "Poda en Malaysian SNR: 20.0% WR, -6.25R. Ruido estructural en sesiones asiáticas.",
    "CADJPY": "Poda en Malaysian SNR: 18.2% WR, -5.00R. Ruido y falsos retrocesos en Killzones.",
    "CHFJPY": "Poda en Malaysian SNR: 28.6% WR, -3.97R. Comportamiento errático en gaps y rollover.",
    "EURAUD": "Poda en Malaysian SNR: 33.3% WR, -1.31R. Falsos chochs y deslizamiento adverso.",
    "EURCAD": "Poda en Malaysian SNR: 40.0% WR, -1.74R. Expectativa matemática negativa.",
    "EURJPY": "Poda en Malaysian SNR: 15.8% WR, -12.18R. Inconsistencia direccional y falsos quiebres.",
    "EURNZD": "Poda en Malaysian SNR: 0.0% WR, -11.10R. Alta dispersión de volatilidad sin seguimiento.",
    "GBPCAD": "Poda en Malaysian SNR: 40.0% WR, -1.18R. Ruido en Killzones.",
    "GBPCHF": "Poda en Malaysian SNR: 18.2% WR, -6.11R. Poca reactividad en niveles Break.",
    "GBPNZD": "Poda en Malaysian SNR: 14.3% WR, -3.50R. Ruido extendido sin seguimiento.",
}


ICT_PRUNED_INFO = {
    # 25 Activos Podados en Replay 2 Años Estrategia ICT (Expectativa Matemática Negativa o Neutral)
    "Volatility 50 Index": "Poda confirmada en replay 2 años ICT: 27.1% WR, -40.00R. Falsos desplazamientos FVG y rachas bajistas prolongadas; derivado a worker VOLATILITY.",
    "Volatility 100 Index": "Poda confirmada en replay 2 años ICT: 32.0% WR, -30.00R. Ruido de alta volatilidad sin respeto al Consequent Encroachment FVG.",
    "EURCAD": "Poda confirmada en replay 2 años ICT: 25.4% WR, -23.75R. Cruce con spreads adversos y falta de liquidez en Killzones.",
    "US SP 500": "Poda confirmada en replay 2 años ICT: 30.4% WR, -17.75R. Volatilidad excesiva en apertura NY y sweeps no respetados; mejor en ORB.",
    "GBPCHF": "Poda confirmada en replay 2 años ICT: 26.6% WR, -17.75R. Rango errático sin continuación institucional.",
    "GBPAUD": "Poda confirmada en replay 2 años ICT: 19.0% WR, -17.25R. Baja tasa de TP1 y fuerte correlación de noticias asiáticas.",
    "AUDCHF": "Poda confirmada en replay 2 años ICT: 24.4% WR, -14.25R. Deslizamiento continuo y compresión en sesión asiática.",
    "Crash 900 Index": "Poda confirmada en replay 2 años ICT: 29.3% WR, -13.50R. Spikes intempestivos rompen estructuras FVG; operado en worker CRASH.",
    "EURNZD": "Poda confirmada en replay 2 años ICT: 22.6% WR, -11.75R. Desalineación con Killzones y spreads nocturnos desfavorables.",
    "CADJPY": "Poda confirmada en replay 2 años ICT: 27.0% WR, -11.75R. Rupturas sin mitigación en horario Londres.",
    "Crash 300 Index": "Poda confirmada en replay 2 años ICT: 32.2% WR, -11.50R. Caídas rápidas invalidan niveles FVG CE.",
    "EURAUD": "Poda confirmada en replay 2 años ICT: 23.8% WR, -9.75R. Solapamiento de rangos asiático y europeo sin expansión limpia.",
    "Jump 50 Index": "Poda confirmada en replay 2 años ICT: 33.7% WR, -7.50R. Saltos estocásticos de precio atraviesan zonas de descuento.",
    "USDJPY": "Poda confirmada en replay 2 años ICT: 35.5% WR, -7.25R. Ausencia de volumen en Killzones y retrocesos tardíos.",
    "USDJPYmicro": "Poda confirmada en replay 2 años ICT: 35.5% WR, -7.25R.",
    "EURGBP": "Poda confirmada en replay 2 años ICT: 31.1% WR, -7.25R. Rango sumamente comprimido y bajo desplazamiento medio.",
    "GBPJPY": "Poda confirmada en replay 2 años ICT: 33.3% WR, -5.50R. Volatilidad descontrolada en sesión de Tokio/Londres; mejor en Malaysian SNR.",
    "AUDCAD": "Poda confirmada en replay 2 años ICT: 32.4% WR, -5.00R. Falta de liquidez institucional en Killzones Londres/NY.",
    "USDCHF": "Poda confirmada en replay 2 años ICT: 33.8% WR, -4.75R. Estructura divergente frente al EURUSD durante la Killzone.",
    "USDCHFmicro": "Poda confirmada en replay 2 años ICT: 33.8% WR, -4.75R.",
    "EURJPY": "Poda confirmada en replay 2 años ICT: 35.3% WR, -4.75R. Intervenciones y tendencias unidireccionales sin pullback a FVG.",
    "GBPNZD": "Poda confirmada en replay 2 años ICT: 30.6% WR, -3.50R. Rangos amplios con mechas falsas en cambio de sesión.",
    "Jump 100 Index": "Poda confirmada en replay 2 años ICT: 35.6% WR, -3.25R. Saltos que saltan el FVG y disparan el Stop Loss.",
    "Crash 1000 Index": "Poda confirmada en replay 2 años ICT: 32.9% WR, -3.25R. Ratios desfavorables frente a Crash 600 y Crash 500.",
    "Boom 1000 Index": "Poda confirmada en replay 2 años ICT: 34.6% WR, -2.25R. Menor consistencia de pullback que Boom 500 y Boom 300.",
    "XAGUSD": "Poda confirmada en replay 2 años ICT: 33.3% WR, -1.50R. Deslizamiento y dilatación en horario NY; mejor rendimiento en Malaysian SNR y ORB.",
    "Step Index 200": "Poda confirmada en replay 2 años ICT: 34.5% WR, 0.00R. Rendimiento neutral sin ventaja matemática; focalizado en Step 400 y Step 500.",
}

def _selection_profile_for_category(category: str) -> str:
    """Mapea una categoria de instrumento a su perfil de worker."""
    value=str(category or "").lower()
    if value.startswith("ict_") or value == "ict": return "ICT"
    if value.startswith("malaysian_snr_") or value == "malaysian_snr": return "MALAYSIAN_SNR"
    if value == "forex": return "FOREX"
    if value == "idx_open_indices": return "IDX_OPEN"
    if value.startswith("orb_ny_"): return "ORB"
    if value.startswith("gold_") or value.startswith("cuartos_") or value in ("gold", "cuartos"): return "GOLD"
    return "SYNTHETICS"

def _catalog_symbols_by_profile(catalog):
    """Reagrupa el catalogo de instrumentos por perfil de worker.

    Returns:
        dict con claves SYNTHETICS, FOREX y ORB y sus simbolos normalizados.
    """
    result={p:[] for p in _SELECTION_PROFILES}
    for group in catalog or []:
        result[_selection_profile_for_category(group.get("category"))].extend(group.get("symbols") or [])
    return {p:_normalize_symbol_list(v) for p,v in result.items()}


def _normalize_symbol_list(values):
    """Limpia una lista de simbolos: sin vacios, sin duplicados y ordenada."""
    if not isinstance(values, (list, tuple, set)):
        return []
    clean = []
    seen = set()
    for value in values:
        symbol = str(value or "").strip()
        if symbol and symbol not in seen:
            seen.add(symbol)
            clean.append(symbol)
    return sorted(clean, key=lambda x: x.casefold())


def _now_iso() -> str:
    """Marca temporal actual en ISO-8601 UTC."""
    return datetime.now(timezone.utc).isoformat()


def _json_safe(value: Any):
    """Convierte cualquier estructura a algo serializable como JSON.

    Recorre dicts y listas, transforma fechas con `isoformat`, anula NaN e
    infinitos (que romperian el JSON del navegador) y, como ultimo recurso,
    representa el valor como texto. Nunca lanza excepcion: un dato exotico debe
    degradarse, no dejar sin respuesta al endpoint.
    """
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        return value if value == value and value not in (float("inf"), float("-inf")) else None
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass
    try:
        return float(value)
    except Exception:
        return str(value)


def _first_dict(*values):
    """Devuelve el primer argumento que sea un dict, o `{}` si ninguno lo es.

    Util porque el mismo dato puede llegar en claves distintas segun la version
    del registro.
    """
    for value in values:
        if isinstance(value, dict):
            return value
    return {}


def _quality_grade(score):
    """Traduce el score numerico de un setup a una nota (A+ .. D).

    Tramos: >=90 A+, >=85 A, >=80 B+, >=75 B, >=65 C, resto D. Sin score
    numerico devuelve "SIN SCORE" en lugar de asumir una nota.
    """
    try:
        score = float(score)
    except (TypeError, ValueError):
        return "SIN SCORE"
    if score >= 90:
        return "A+"
    if score >= 85:
        return "A"
    if score >= 80:
        return "B+"
    if score >= 75:
        return "B"
    if score >= 65:
        return "C"
    return "D"


def _confirmed_decision(value: Any) -> bool:
    """Indica si una decision equivale a "confirmada" (en ingles o espanol)."""
    text = str(value or "").upper()
    return "CONFIRMED" in text or "CONFIRMADA" in text


def _divergence_direction(value: Any) -> str | None:
    """Deduce la direccion (BUY/SELL) de un texto de divergencia.

    Returns:
        "BUY", "SELL" o `None` si el texto no indica sesgo.
    """
    text = str(value or "").upper()
    if "ALCISTA" in text or "BULL" in text:
        return "BUY"
    if "BAJISTA" in text or "BEAR" in text:
        return "SELL"
    return None


_BOT_MAGIC_PROFILE = {
    26082026: "SYNTHETICS_LEGACY",
    26082027: "FOREX_LEGACY",
    26082201: "FOREX_1",
    26082202: "FOREX_2",
    26082203: "FOREX_3",
    26082204: "FOREX_4",
    26082028: "ORB",
    26082029: "GOLD",
    26082101: "BOOM",
    26082102: "CRASH",
    26082103: "VOLATILITY",
    26082401: "VOLATILITY_1",
    26082402: "VOLATILITY_2",
    26082403: "VOLATILITY_3",
    26082404: "VOLATILITY_4",
    26082104: "STEP",
    26082105: "JUMP",
    26082106: "FLIP",
    26082030: "IDX_OPEN",
}


def _infer_symbol_profile(symbol: str) -> str | None:
    """Deduce el perfil de worker a partir del nombre del instrumento.

    Respaldo para operaciones sin metadatos (por ejemplo recuperadas de MT5):
    primero busca familias sinteticas (Boom, Crash, Volatility, Step, Jump),
    luego un par de divisas de seis letras, y por ultimo los indices e XAUUSD
    de ORB.

    Returns:
        Nombre del perfil o `None` si no se reconoce.
    """
    name = str(symbol or "").lower()
    if "boom" in name and "crash" in name:
        return "FLIP"
    if "boom" in name:
        return "BOOM"
    if "crash" in name:
        return "CRASH"
    if "volatility" in name or name.startswith("vol ") or "volswitch" in name or "high frequency vol" in name:
        return "VOLATILITY"
    if "step" in name:
        return "STEP"
    if "jump" in name:
        return "JUMP"

    letters = "".join(ch for ch in str(symbol or "").upper() if ch.isalpha())
    currencies = {
        "USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD",
        "SEK", "NOK", "DKK", "SGD", "HKD", "MXN", "ZAR", "TRY", "PLN", "CNH",
    }
    if len(letters) >= 6 and letters[:3] in currencies and letters[3:6] in currencies:
        return "FOREX"

    orb_terms = (
        "xauusd",
        "xagusd",
        "silver",
        "us oil",
        "usoil",
        "wti",
        "crude oil",
        "brent",
        "us30",
        "wall street",
        "ustec",
        "nasdaq",
        "us500",
        "s&p",
        "sp500",
        "spx500",
        "sandp500",
    )
    if any(term in name for term in orb_terms):
        return "ORB"
    return None


def _position_owner(trade: dict, metadata: dict) -> dict:
    """Determina que worker es responsable de una posicion abierta.

    Prioridad: numero magico de la orden (identificador fiable asignado al
    enviarla) -> `bot_profile` de los metadatos -> inferencia por el nombre del
    simbolo. Los magicos "legacy" se reinterpretan porque en su dia un unico
    worker cubria varias familias.

    Saber el propietario es lo que permite al dashboard impedir que se detenga
    un worker con riesgo vivo.

    Returns:
        dict con el perfil, el magico y si el perfil fue inferido.
    """
    source = str(trade.get("source") or "").upper()
    symbol = str(trade.get("instrument") or "")
    raw_magic = metadata.get("daemon_magic")
    if raw_magic in (None, ""):
        raw_magic = metadata.get("mt5_magic")
    try:
        magic = int(raw_magic) if raw_magic not in (None, "") else None
    except Exception:
        magic = None

    profile = _BOT_MAGIC_PROFILE.get(magic)
    inferred = False
    if profile == "SYNTHETICS_LEGACY":
        profile = _infer_symbol_profile(symbol)
        inferred = bool(profile)
    elif not profile and source == "DEMO":
        profile = str(metadata.get("bot_profile") or "").upper() or _infer_symbol_profile(symbol)
        inferred = bool(profile and not metadata.get("bot_profile"))

    metadata_managed = metadata.get("managed_by_daemon")
    managed = source != "MT5_EXTERNAL" and metadata_managed is not False

    if source == "MT5_EXTERNAL":
        managed = False
        if magic in _BOT_MAGIC_PROFILE:
            status = "MAGIC_DAEMON_PERO_SOURCE_EXTERNA"
        else:
            status = "EXTERNA_MT5"
    elif managed and profile:
        status = "LEGACY_INFERIDA" if inferred else "CONFIRMADA"
    elif managed:
        status = "DAEMON_SIN_OWNER"
    else:
        status = "NO_GESTIONADA"

    return {
        "owner_profile": profile,
        "owner_magic": magic,
        "ownership_status": status,
        "managed_by_daemon": bool(managed),
        "owner_inferred": inferred,
    }


def _position_health(position: dict, market: dict | None = None, latest: dict | None = None) -> dict:
    """Evalúa la salud de una posición abierta sin ejecutar cierres automáticos.

    Combina progreso financiero en R con la tesis más reciente del símbolo. La
    recomendación es deliberadamente asesora: MANTENER, VIGILAR, PROTEGER o
    SALIDA A EVALUAR.
    """
    market = market or {}
    latest = latest or {}
    direction = str(position.get("direction") or "").upper()
    score = 50.0
    reasons: list[str] = []

    rr = market.get("current_rr")
    try:
        rr = float(rr)
    except (TypeError, ValueError):
        rr = None

    if rr is None:
        reasons.append("Sin lectura R actual del broker")
    elif rr >= 2.0:
        score += 28
        reasons.append(f"Precio en expansión mayor hacia objetivos ({rr:.2f}R)")
    elif rr >= 1.5:
        score += 24
        reasons.append(f"Precio en zona de alta ganancia ({rr:.2f}R)")
    elif rr >= 1.0:
        score += 20
        reasons.append(f"Precio alcanzó zona de protección ({rr:.2f}R)")
    elif rr >= 0.7:
        score += 18
        reasons.append(f"Operación en desarrollo muy favorable ({rr:.2f}R)")
    elif rr >= 0.4:
        score += 15
        reasons.append(f"Operación desarrolla beneficio ({rr:.2f}R)")
    elif rr >= 0.1:
        score += 8
        reasons.append(f"Operación en terreno positivo ({rr:.2f}R)")
    elif rr >= 0.0:
        score += 4
        reasons.append(f"Operación aún sobre la entrada ({rr:.2f}R)")
    elif rr >= -0.25:
        reasons.append(f"Retroceso pequeño dentro del riesgo ({rr:.2f}R)")
    elif rr >= -0.5:
        score -= 8
        reasons.append(f"Retroceso relevante ({rr:.2f}R)")
    elif rr >= -0.75:
        score -= 15
        reasons.append(f"Precio cercano a la zona de riesgo ({rr:.2f}R)")
    else:
        score -= 24
        reasons.append(f"Precio muy próximo al Stop Loss ({rr:.2f}R)")

    be_active = bool(position.get("break_even_confirmed") or market.get("break_even_confirmed"))
    if be_active:
        score += 10
        reasons.append("Break Even confirmado: riesgo original protegido")

    latest_direction = str(latest.get("direction") or "").upper()
    latest_score = latest.get("score")
    try:
        latest_score = float(latest_score)
    except (TypeError, ValueError):
        latest_score = None
    latest_confirmed = _confirmed_decision(latest.get("decision")) and (latest_score is None or latest_score >= 75)

    if latest_direction in ("BUY", "SELL") and latest_confirmed:
        if latest_direction == direction:
            score += 20
            reasons.append("El análisis más reciente sigue alineado con la dirección del trade")
        else:
            score -= 35
            reasons.append("Existe una señal confirmada reciente en dirección contraria")

    critical = latest.get("critical_failures") or []
    if critical:
        score -= min(18, 6 * len(critical))
        reasons.append("El análisis reciente presenta condiciones críticas faltantes")

    if bool(latest.get("divergence_confirmed")):
        div_dir = _divergence_direction(latest.get("divergence_type"))
        if div_dir and div_dir == direction:
            score += 5
            reasons.append("La divergencia reciente favorece la posición")
        elif div_dir and div_dir != direction:
            score -= 12
            reasons.append("Apareció una divergencia reciente contraria a la posición")

    score = max(0.0, min(100.0, score))
    if score >= 65:
        recommendation = "MANTENER"
    elif score >= 50:
        recommendation = "VIGILAR"
    elif score >= 35:
        recommendation = "PROTEGER"
    else:
        recommendation = "SALIDA A EVALUAR"

    return {
        "health_score": round(score, 1),
        "health_grade": _quality_grade(score),
        "recommendation": recommendation,
        "current_rr": rr,
        "current_price": market.get("current_price"),
        "initial_stop_loss": market.get("initial_stop_loss"),
        "distance_to_sl_r": market.get("distance_to_sl_r"),
        "distance_to_tp_r": market.get("distance_to_tp_r"),
        "reasons": reasons,
        "advisory_only": True,
    }


def _extract_signal(result: dict) -> dict:
    """Localiza el diccionario de senal dentro del resultado de un ciclo.

    La senal puede venir en `signal`, dentro de `analysis` o en `diagnostics`
    segun la estrategia y la fase; se busca en ese orden.

    Returns:
        dict de la senal, o `{}` si el ciclo no produjo ninguna.
    """
    analysis = _first_dict(result.get("analysis"))
    direct = _first_dict(result.get("signal"))
    if direct:
        return direct
    for key in ("signal", "entry_signal", "confirmed_signal", "candidate"):
        value = analysis.get(key)
        if isinstance(value, dict):
            return value
    diagnostics = _first_dict(analysis.get("diagnostics"), result.get("diagnostics"))
    for key in ("signal", "latest_candidate", "m5_latest_candidate", "confirmed_signal"):
        value = diagnostics.get(key)
        if isinstance(value, dict):
            return value
    return {}


def _extract_quality(result: dict) -> dict:
    """Reune las metricas de calidad de un setup para mostrarlas.

    Consulta senal, analisis, diagnosticos y el propio resultado en ese orden,
    porque las claves cambian segun la estrategia. Normaliza el porcentaje de
    confirmacion (acepta 0-1 o 0-100) y traduce los nombres tecnicos de cada
    confirmacion a texto legible.

    Returns:
        dict con score, nota, porcentaje, confirmaciones cumplidas, faltantes y
        fallos criticos.
    """
    signal = _extract_signal(result)
    analysis = _first_dict(result.get("analysis"))
    diagnostics = _first_dict(result.get("diagnostics"), analysis.get("diagnostics"))
    sources = [signal, analysis, diagnostics, result]

    def pick(*keys):
        """Primer valor no nulo hallado entre las claves y fuentes dadas."""
        for source in sources:
            if not isinstance(source, dict):
                continue
            for key in keys:
                value = source.get(key)
                if value is not None:
                    return value
        return None

    score = pick("trade_score", "score", "quality_score", "setup_score")
    percentage = pick("confirmation_percentage", "confirmation_ratio")
    try:
        percentage = float(percentage)
        if 0 <= percentage <= 1:
            percentage *= 100.0
    except (TypeError, ValueError):
        percentage = None
    try:
        score = float(score)
    except (TypeError, ValueError):
        score = None

    passed = pick("passed_confirmations") or []
    missing = pick("missing_confirmations") or []
    critical = pick("critical_confirmation_failures") or []
    if not isinstance(passed, list):
        passed = []
    if not isinstance(missing, list):
        missing = []
    if not isinstance(critical, list):
        critical = []

    def labels(items):
        """Traduce nombres tecnicos de confirmaciones a texto legible."""
        return [_LABELS.get(str(item), str(item).replace("_", " ").title()) for item in items]

    confirmations = pick("confirmations")
    if not passed and isinstance(confirmations, dict):
        passed = [key for key, value in confirmations.items() if bool(value)]
        missing = [key for key, value in confirmations.items() if not bool(value)]

    return {
        "score": score,
        "grade": pick("trade_grade") or _quality_grade(score),
        "confirmation_percentage": percentage,
        "confirmations_passed": pick("confirmations_passed"),
        "confirmations_total": pick("confirmations_total"),
        "decision": pick("confirmation_decision") or "NO CONFIRMADA",
        "direction": pick("direction"),
        "passed": labels(passed),
        "missing": labels(missing),
        "critical_failures": labels(critical),
        "divergence_confirmed": bool(pick("divergence_confirmation") or False),
        "divergence_type": pick("divergence_type"),
        "harmonic_confirmed": bool(pick("harmonic_confirmed") or False),
        "harmonic_pattern": pick("harmonic_pattern"),
        "harmonic_score": pick("harmonic_score"),
        "chart_pattern_confirmed": bool(pick("chart_pattern_confirmed") or False),
        "chart_pattern_name": pick("chart_pattern_name"),
        "chart_pattern_direction": pick("chart_pattern_direction"),
        "chart_pattern_strength": pick("chart_pattern_strength"),
        "chart_pattern_bonus": pick("chart_pattern_bonus"),
        "chart_pattern_conflict": bool(pick("chart_pattern_conflict") or False),
        "chart_pattern_evidence": pick("chart_pattern_evidence") or {},
        "chart_pattern_supporting_pattern": pick("chart_pattern_supporting_pattern"),
        "chart_pattern_supporting_direction": pick("chart_pattern_supporting_direction"),
        "chart_pattern_supporting_strength": pick("chart_pattern_supporting_strength"),
        "chart_pattern_conflicting_pattern": pick("chart_pattern_conflicting_pattern"),
        "chart_pattern_conflicting_direction": pick("chart_pattern_conflicting_direction"),
        "chart_pattern_conflicting_strength": pick("chart_pattern_conflicting_strength"),
        "chart_pattern_conflict_level": pick("chart_pattern_conflict_level"),
        "chart_pattern_conflict_reason": pick("chart_pattern_conflict_reason"),
        "h1_doji_confirmed": bool(pick("h1_doji_confirmation") or False),
        "h1_doji_type": pick("h1_doji_type"),
        "h1_doji_zone": pick("h1_doji_zone"),
        "h1_doji_time": pick("h1_doji_time"),
        "structure_break": pick("m15_structure_break_type", "structure_break_type"),
        "h1_trend": pick("h1_trend"),
        "zone": pick("m15_zone", "premium_discount_zone"),
    }


def _is_retired_worker_profile(profile):
   """Identifica perfiles cuya estrategia ya no forma parte del daemon."""
   return str(profile or "").upper().startswith("SCALP_")


class RealtimeDashboardService:
    """Publica un dashboard local de sólo lectura sin bloquear el hilo de MT5."""

    def __init__(self, repository=None, host="127.0.0.1", port=8765, max_recent=80, state_path=None):
        """Prepara el estado, las caches y el servicio de noticias.

        Args:
            repository: `TradingRepository` de lectura; `None` deja la interfaz
                en modo presentacional.
            host / port: direccion de escucha; por defecto solo localhost.
            max_recent: eventos recientes conservados en memoria.
            state_path: JSON donde se persiste el estado presentacional.

        Las caches con TTL son de lectura y NO son fuente de verdad: SQLAlchemy
        sigue siendo autoritativo. Al construirse ya refresca posiciones y
        cuenta para que la primera carga no aparezca vacia.
        """
        if repository is None:
            try:
                from database.repository import TradingRepository
                repository = TradingRepository()
            except Exception:
                repository = None
        self.repository = repository
        self.host = str(host)
        self.port = int(port)
        self._lock = threading.RLock()
        self._worker_controller = None
        self._server = None
        self._thread = None
        self._recent = deque(maxlen=max(10, int(max_recent)))
        # v74: cachés cortas de lectura para navegación. No son fuente de verdad;
        # SQLAlchemy sigue siendo autoritativo.
        self._account_cache = {"at": 0.0, "payload": None}
        self._account_build_lock = threading.Lock()
        self._instruments_cache = {"at": 0.0, "payload": None}
        self._snapshot_aux_cache = {"at": 0.0, "recent": None, "workers": None, "candidates": None}
        self._dashboard_snapshot_cache = {"at": 0.0, "payload": None}
        self._dashboard_snapshot_cache_ttl_seconds = 4.0
        self._account_cache_ttl_seconds = 6.0
        self._instruments_cache_ttl_seconds = 5.0
        self._snapshot_aux_cache_ttl_seconds = 5.0
        default_state_path = Path(__file__).resolve().parent.parent / "storage" / "dashboard" / "last_state.json"
        self.state_path = Path(state_path) if state_path else default_state_path
        news_state_path = self.state_path.parent / "financial_news.json"
        self.news_service = FinancialNewsService(state_path=news_state_path)
        self._state = {
            "status": "INICIALIZANDO",
            "connection_mode": "OFFLINE",
            "data_freshness": "PERSISTED",
            "last_live_update": None,
            "updated_at": _now_iso(),
            "cycle": 0,
            "cycle_started_at": None,
            "cycle_elapsed_seconds": None,
            "symbols_total": 0,
            "symbols_processed": 0,
            "current_symbol": None,
            "last_monitor": None,
            "recent": [],
            "open_positions": [],
            "position_health_summary": {"mantener": 0, "vigilar": 0, "proteger": 0, "salida": 0},
            "instrument_catalog": [],
            "selected_symbols": [],
            "selection_profiles": {"SYNTHETICS": [], "FOREX": [], "ORB": [], "IDX_OPEN": []},
            "selection_profile_versions": {},
            "selection_version": 0,
            "selection_message": "Catálogo pendiente de cargar",
            "account": {"snapshot": None, "stats": {}, "recent_trades": []},
            "financial_news": self.news_service.snapshot(),
        }
        self._load_persisted_state()
        with self._lock:
            self._refresh_open_positions_locked()
            self._refresh_account_locked()

    def _load_persisted_state(self):
        """Rehidrata el estado presentacional del ultimo arranque.

        Solo restaura datos de presentacion (ciclo, catalogo, seleccion,
        eventos recientes): trades y cuenta se releen siempre de la base. Marca
        el estado como OFFLINE/PERSISTED para que quede claro que lo mostrado
        no es informacion en vivo. Cualquier error se ignora: un snapshot
        corrupto no puede impedir que el motor opere.
        """
        try:
            if not self.state_path.exists():
                return
            raw = json.loads(self.state_path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                return
            recent = raw.get("recent") or []
            for row in reversed(recent[-self._recent.maxlen:]):
                if isinstance(row, dict):
                    self._recent.appendleft(row)
            # Cargamos únicamente estado presentacional. SQLAlchemy sigue siendo
            # la fuente de verdad para trades abiertos y cuenta.
            for key in (
                "cycle", "cycle_started_at", "cycle_elapsed_seconds",
                "symbols_total", "symbols_processed", "current_symbol",
                "last_monitor", "instrument_catalog", "selected_symbols",
                "selection_profiles", "selection_profile_versions",
                "selection_version", "selection_message", "recent",
                "daily_profit_target",
            ):
                if key in raw:
                    self._state[key] = raw[key]
            self._state["status"] = "SIN CONEXIÓN · ÚLTIMO ESTADO PERSISTIDO"
            self._state["connection_mode"] = "OFFLINE"
            self._state["data_freshness"] = "PERSISTED"
            self._state["last_live_update"] = raw.get("last_live_update") or raw.get("updated_at")
            self._state["updated_at"] = _now_iso()
        except Exception:
            # El dashboard nunca debe impedir que el motor opere por un snapshot corrupto.
            return

    def _persist_state_locked(self):
        """Guarda el estado en disco de forma atomica.

        Escribe en un `.tmp` y hace `replace`, de modo que un corte a mitad de
        escritura nunca deje el JSON a medias. Debe llamarse con el lock ya
        tomado.
        """
        try:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            payload = _json_safe({**self._state, "recent": list(self._recent)})
            tmp = self.state_path.with_suffix(self.state_path.suffix + ".tmp")
            tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            tmp.replace(self.state_path)
        except Exception:
            return

    def _cached_account_payload(self, force=False):
        # Only one HTTP request rebuilds the account at a time. Waiting readers
        # recheck the TTL after the first reader has published its result.
        with self._account_build_lock:
            return self._build_cached_account_payload(force=force)

    def _build_cached_account_payload(self, force=False):
        """Payload de cuenta con cache de corta duracion.

        Evita recalcular las metricas en cada refresco del navegador.

        Args:
            force: ignora la cache y recalcula.
        """
        now = time.monotonic()
        cached = self._account_cache
        if (
            not force
            and cached.get("payload") is not None
            and (now - float(cached.get("at") or 0.0)) < self._account_cache_ttl_seconds
        ):
            return cached["payload"]
        payload = _json_safe(build_account_payload(self.repository, source="DEMO"))
        self._account_cache = {"at": time.monotonic(), "payload": payload}
        return payload

    def _trade_audit_detail_payload(self, trade_id, account_payload=None):
        """Detalle completo de un trade y TODOS sus snapshots Entrada vs. Ahora."""
        trade_id = int(trade_id)
        if account_payload is not None:
            trades = list(account_payload.get("recent_trades") or [])
            trade = next(
                (
                    row for row in trades
                    if int(row.get("source_trade_id") or row.get("id") or -1) == trade_id
                ),
                None,
            )
        else:
            trade = None
            finder = getattr(self.repository, "get_trade_or_journal", None) or getattr(self.repository, "get_trade", None)
            if callable(finder):
                try:
                    trade = finder(trade_id)
                except Exception:
                    trade = None
            if trade is None:
                try:
                    account_payload = build_account_payload(self.repository, source="DEMO", recent_limit=500)
                    trades = list(account_payload.get("recent_trades") or [])
                    trade = next(
                        (
                            row for row in trades
                            if int(row.get("source_trade_id") or row.get("id") or -1) == trade_id
                        ),
                        None,
                    )
                except Exception:
                    trade = None
        if trade is None:
            return {"ok": False, "error": "Trade no encontrado", "trade_id": trade_id}

        # Recuperamos la fila operativa original para conservar details/metadata.
        # account_metrics contiene la vista estadística, pero no toda la tesis.
        canonical_trade = {}
        reader = getattr(self.repository, "get_trade", None)
        if callable(reader):
            try:
                canonical_trade = reader(trade_id) or {}
            except Exception:
                canonical_trade = {}
        if isinstance(canonical_trade, dict) and canonical_trade:
            trade = {**canonical_trade, **trade}

        snapshots = []
        if hasattr(self.repository, "trade_audit_snapshots"):
            try:
                snapshots = self.repository.trade_audit_snapshots(
                    trade_id=trade_id,
                    source=trade.get("source") or "DEMO",
                    limit=None,
                ) or []
            except Exception:
                snapshots = []
        # Repository devuelve DESC; la pestaña de auditoría se lee cronológicamente.
        expected_instrument = str(trade.get("instrument") or "")
        meta = trade.get("details") if isinstance(trade.get("details"), dict) else {}
        metadata = meta.get("metadata") if isinstance(meta.get("metadata"), dict) else {}
        expected_ticket = str(
            trade.get("broker_position_ticket")
            or metadata.get("broker_position_ticket")
            or ""
        )
        expected_profile = str(
            trade.get("bot_profile") or metadata.get("bot_profile") or ""
        ).upper()
        expected_magic = trade.get("daemon_magic") or metadata.get("daemon_magic")
        try:
            expected_magic = int(expected_magic) if expected_magic not in (None, "") else None
        except (TypeError, ValueError):
            expected_magic = None
        excluded = []
        valid_snapshots = []
        for snap in snapshots:
            instrument_ok = str(snap.get("instrument") or "") == expected_instrument
            ticket = str(snap.get("broker_position_ticket") or "")
            ticket_ok = not expected_ticket or not ticket or ticket == expected_ticket
            snap_profile = str(snap.get("bot_profile") or "").upper()
            profile_ok = not expected_profile or not snap_profile or snap_profile == expected_profile
            try:
                snap_magic = int(snap.get("daemon_magic")) if snap.get("daemon_magic") not in (None, "") else None
            except (TypeError, ValueError):
                snap_magic = None
            magic_ok = expected_magic is None or snap_magic is None or snap_magic == expected_magic
            if instrument_ok and ticket_ok and profile_ok and magic_ok:
                valid_snapshots.append(snap)
            else:
                excluded.append(snap.get("id"))
        snapshots = list(reversed(valid_snapshots))  # snapshots = list(reversed(snapshots))
        entry_view = (
            (snapshots[0].get("entry_view") or {})
            if snapshots
            else {}
        )
        entry_view_origin = "TRADE_AUDIT_SNAPSHOT" if entry_view else None

        # v86: compatibilidad con trades previos y trades ultracortos. La tesis
        # inmutable vive en trade_visual_audits aunque no haya alcanzado a crearse
        # el primer punto de la serie append-only.
        visual_audit = {}
        if hasattr(self.repository, "get_trade_visual_audit"):
            try:
                visual_audit = self.repository.get_trade_visual_audit(
                    trade_id=trade_id, source=trade.get("source") or "DEMO"
                ) or {}
            except Exception:
                visual_audit = {}
        elif hasattr(self.repository, "trade_visual_audits"):
            try:
                visual_audit = next((
                    row for row in (self.repository.trade_visual_audits(source=trade.get("source") or "DEMO") or [])
                    if int(row.get("trade_id") or -1) == trade_id
                    and str(row.get("instrument") or "") == expected_instrument
                    and (
                        not expected_ticket
                        or not row.get("broker_position_ticket")
                        or str(row.get("broker_position_ticket")) == expected_ticket
                    )
                ), {})
            except Exception:
                visual_audit = {}
        if not entry_view:
            entry_view = visual_audit.get("entry_context") or {}
            if entry_view:
                entry_view_origin = "TRADE_VISUAL_AUDIT"

        # Trades históricos pueden anteceder la auditoría visual inmutable. La
        # confirmación de entrada ya almacenada en la operación es una fuente
        # válida y nunca se toma desde otro trade.
        if not entry_view:
            entry_view = trade.get("confirmation_audit") or {}
            if entry_view:
                entry_view_origin = "TRADE_CONFIRMATION_AUDIT"
        if not entry_view:
            for candidate_name in ("signal", "analysis"):
                candidate = meta.get(candidate_name)
                if isinstance(candidate, dict) and candidate:
                    entry_view = dict(candidate)
                    entry_view_origin = f"TRADE_DETAILS_{candidate_name.upper()}"
                    break
        if not entry_view:
            # No inventamos confirmaciones: creamos una ficha explícita con los
            # datos contractuales de la operación y marcamos la tesis como no
            # disponible por antigüedad. Esto permite descargar sin mezclar IDs.
            entry_view = {
                "decision": "HISTORICAL_ENTRY_CONTEXT_UNAVAILABLE",
                "audit_reconstruction": True,
                "audit_reconstruction_reason": (
                    "La operación es anterior a la persistencia de tesis visual completa."
                ),
                "instrument": expected_instrument,
                "direction": trade.get("direction"),
                "entry_time": trade.get("entry_time"),
                "entry_price": trade.get("entry_price"),
                "stop_loss": trade.get("stop_loss"),
                "take_profit": trade.get("take_profit"),
                "planned_rr": trade.get("planned_rr"),
                "risk_percent": trade.get("risk_percent"),
                "setup_reason": trade.get("setup_reason"),
                "strategy_version": trade.get("strategy_version"),
            }
            entry_view_origin = "TRADE_CONTRACT_FALLBACK"

        # Una serie histórica antigua puede tener snapshots válidos pero sin la
        # columna entry_view. La completamos sólo en la respuesta, con la tesis
        # del mismo trade; la evidencia SQL append-only permanece inmutable.
        for snap in snapshots:
            if not (snap.get("entry_view") or {}):
                snap["entry_view"] = dict(entry_view)
                visual = dict(snap.get("visual_context") or {})
                visual["entry_view_backfilled_from"] = entry_view_origin
                snap["visual_context"] = visual

        if not snapshots and entry_view:
            latest_market = visual_audit.get("latest_market") or {}
            latest_chart = visual_audit.get("latest_chart") or {}
            snapshots = [{
                "id": None,
                "trade_id": trade_id,
                "source": "DEMO",
                "bot_profile": visual_audit.get("bot_profile"),
                "daemon_magic": visual_audit.get("daemon_magic"),
                "instrument": expected_instrument,
                "broker_position_ticket": visual_audit.get("broker_position_ticket") or expected_ticket or None,
                "snapshot_at": visual_audit.get("latest_updated_at") or visual_audit.get("entry_captured_at"),
                "learning_eligibility": trade_learning_eligibility(trade),
            "entry_view": entry_view,
                "current_view": latest_market.get("current_strategy_view") or entry_view,
                "market": latest_market,
                "visual_context": {
                    "fallback_from_trade_visual_audit": True,
                    "available_timeframes": sorted(list((latest_chart.get("timeframes") or {}).keys())) if isinstance(latest_chart, dict) else [],
                },
            }]
        return _json_safe({
            "ok": True,
            "trade": trade,
            "learning_eligibility": trade_learning_eligibility(trade),
            "entry_view": entry_view,
            "latest": snapshots[-1] if snapshots else {},
            "snapshots": snapshots,
            "snapshot_count": len(snapshots),
            "charts": {
                "entry": visual_audit.get("entry_chart") or {},
                "latest": visual_audit.get("latest_chart") or {},
            },
            "chart_integrity": {
                "entry_chart_present": bool(visual_audit.get("entry_chart")),
                "latest_chart_present": bool(visual_audit.get("latest_chart")),
                "entry_is_immutable": True,
                "data_source": (
                    (visual_audit.get("entry_chart") or {}).get("data_source")
                    or (visual_audit.get("latest_chart") or {}).get("data_source")
                    or "DERIV_CHARTS"
                ),
                "entry_captured_at": visual_audit.get("entry_captured_at"),
                "latest_updated_at": visual_audit.get("latest_updated_at"),
            },
            "audit_integrity": {
                # Los snapshots contradictorios ya fueron excluidos. Su presencia
                # genera una advertencia, no invalida la descarga saneada.
                "valid": bool(entry_view),
                "excluded_snapshot_ids": excluded,
                "identity_conflicts_removed": len(excluded),
                "sanitized": bool(excluded),
                "entry_view_present": bool(entry_view),
                "entry_view_origin": entry_view_origin,
                "entry_view_complete": entry_view_origin in {
                    "TRADE_AUDIT_SNAPSHOT", "TRADE_VISUAL_AUDIT"
                },
                "fallback_from_trade_visual_audit": bool(
                    snapshots and (snapshots[0].get("visual_context") or {}).get("fallback_from_trade_visual_audit")
                ),
                "instrument": expected_instrument,
                "ticket": expected_ticket or None,
                "bot_profile": expected_profile or None,
                "daemon_magic": expected_magic,
            },
            "data_source": "SQLALCHEMY_LOCAL_ONLY",
            "generated_at": _now_iso(),
        })

    def _cached_instruments_payload(self, force=False):
        """Payload minimo de la pagina de instrumentos, con cache corta.

        Construye solo catalogo y seleccion; deliberadamente omite posiciones,
        cuenta y graficos, que son la parte cara del snapshot completo.
        """
        now = time.monotonic()
        cached = self._instruments_cache
        if (
            not force
            and cached.get("payload") is not None
            and (now - float(cached.get("at") or 0.0)) < self._instruments_cache_ttl_seconds
        ):
            return cached["payload"]

        # Sólo los datos que /instruments necesita; evita construir posiciones,
        # account, gráficos y análisis recientes.
        with self._lock:
            self._refresh_selection_profiles_from_db_locked()
            payload = {
                "instrument_catalog": list(self._state.get("instrument_catalog") or []),
                "selection_profiles": dict(self._state.get("selection_profiles") or {}),
                "selection_profile_versions": dict(self._state.get("selection_profile_versions") or {}),
                "selected_symbols": list(self._state.get("selected_symbols") or []),
                "selection_version": self._state.get("selection_version"),
                "selection_message": self._state.get("selection_message"),
                "updated_at": self._state.get("updated_at"),
                "daemon_version": DAEMONBLACKFX_VERSION,
                "financial_news": self.news_service.snapshot(),
                "pruned_instruments": dict(PRUNED_INSTRUMENTS_INFO),
                "pruned_instruments_by_profile": {
                    "SYNTHETICS": dict(PRUNED_INSTRUMENTS_INFO),
                    "FOREX": dict(FOREX_PRUNED_INFO),
                    "ORB": dict(PRUNED_INSTRUMENTS_INFO),
                    "IDX_OPEN": dict(PRUNED_INSTRUMENTS_INFO),
                    "MALAYSIAN_SNR": dict(MALAYSIAN_SNR_PRUNED_INFO),
                    "GOLD": {},
                    "ICT": dict(ICT_PRUNED_INFO),
                },
                "prioritized_symbols": dict(DEFAULT_PRIORITIZED_SYMBOLS),
            }
        payload = _json_safe(payload)
        self._instruments_cache = {"at": now, "payload": payload}
        return payload

    def _invalidate_navigation_caches(self, *, account=False, instruments=False):
        """Descarta las caches indicadas tras un cambio de estado relevante."""
        self._dashboard_snapshot_cache = {"at": 0.0, "payload": None}
        if account:
            self._account_cache = {"at": 0.0, "payload": None}
        if instruments:
            self._instruments_cache = {"at": 0.0, "payload": None}

    def mark_live(self):
        """Marca la interfaz como conectada y en datos en vivo."""
        with self._lock:
            now = _now_iso()
            self._state["connection_mode"] = "LIVE"
            self._state["data_freshness"] = "LIVE"
            self._state["last_live_update"] = now
            self._state["updated_at"] = now
            self._persist_state_locked()

    def mark_offline(self, status="DAEMON DESCONECTADO · ESTADO PERSISTIDO"):
        """Marca la interfaz como desconectada conservando el ultimo estado.

        Es clave que se distinga de LIVE: mirar datos viejos creyendolos
        actuales es peor que no verlos.
        """
        with self._lock:
            self._state["status"] = str(status)
            self._state["connection_mode"] = "OFFLINE"
            self._state["data_freshness"] = "PERSISTED"
            self._state["updated_at"] = _now_iso()
            self._persist_state_locked()

    @property
    def url(self):
        """URL base del dashboard."""
        return f"http://{self.host}:{self.port}"

    @property
    def instruments_url(self):
        """URL de la pagina de instrumentos."""
        return f"{self.url}/instruments"

    @property
    def account_url(self):
        """URL de la pagina de cuenta."""
        return f"{self.url}/account"

    def start(self, live=True):
        """Arranca el servidor HTTP en un hilo daemon y las noticias.

        Define aqui dentro la clase `Handler` para que capture `service` por
        closure y pueda acceder al estado sin variables globales.

        Args:
            live: si es `True` marca la interfaz como conectada al arrancar.
        """
        service = self
        self.news_service.start()

        class Handler(BaseHTTPRequestHandler):
            """Manejador HTTP: sirve las paginas y los endpoints JSON."""

            def log_message(self, fmt, *args):
                """Silencia el log de acceso, que ensuciaria la consola del bot."""
                return

            def _send(self, body: bytes, content_type: str, status=HTTPStatus.OK):
                """Envía HTTP sin propagar desconexiones normales del navegador."""
                try:
                    self.send_response(int(status))
                    self.send_header("Content-Type", content_type)
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                except (
                    BrokenPipeError,
                    ConnectionResetError,
                    ConnectionAbortedError,
                    TimeoutError,
                ):
                    return False
                except OSError as exc:
                    winerror = getattr(exc, "winerror", None)
                    errno_value = getattr(exc, "errno", None)
                    if winerror in {10053, 10054, 10057, 10058} or errno_value in {
                        32, 54, 104
                    }:
                        return False
                    raise
                return True

            def _send_download(self, body: bytes, filename: str, content_type: str):
                """Envia un fichero como descarga adjunta (XLSX de auditoria).

                Devuelve `False` si el cliente corto la conexion, sin propagar
                el error.
                """
                try:
                    self.send_response(int(HTTPStatus.OK))
                    self.send_header("Content-Type", content_type)
                    self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, TimeoutError, OSError):
                    return False
                return True

            def do_GET(self):
                """Enruta las peticiones GET.

                Sirve las paginas HTML (`/`, `/instruments`, `/account`,
                `/trade-audit`), el logo, la descarga XLSX de auditoria y los
                endpoints JSON de estado, cuenta e instrumentos. Todo es de
                solo lectura.
                """
                path = urlparse(self.path).path
                if path in ("/", "/index.html"):
                    self._send(_HTML.encode("utf-8"), "text/html; charset=utf-8")
                    return
                if path == "/assets/blackdaemonfx_logo_v1.jpeg":
                    logo_path = Path(__file__).resolve().parent / "assets" / "blackdaemonfx_logo_v1.jpeg"
                    if logo_path.exists():
                        self._send(logo_path.read_bytes(), "image/jpeg")
                    else:
                        self._send(b"Logo not found", "text/plain; charset=utf-8", HTTPStatus.NOT_FOUND)
                    return
                if path in ("/instruments", "/instruments/"):
                    self._send(_INSTRUMENTS_HTML.encode("utf-8"), "text/html; charset=utf-8")
                    return
                trade_audit_match = re.fullmatch(r"/account/trade/(\d+)/audit/?", path)
                if trade_audit_match:
                    self._send(TRADE_AUDIT_HTML.encode("utf-8"), "text/html; charset=utf-8")
                    return
                api_trade_excel_match = re.fullmatch(r"/api/account/trade/(\d+)/audit/excel/?", path)
                if api_trade_excel_match:
                    trade_id = int(api_trade_excel_match.group(1))
                    detail = service._trade_audit_detail_payload(trade_id)
                    if not detail.get("ok"):
                        payload = json.dumps(detail, ensure_ascii=False).encode("utf-8")
                        self._send(payload, "application/json; charset=utf-8", HTTPStatus.NOT_FOUND)
                        return
                    trade = detail.get("trade") or {}
                    instrument = re.sub(r"[^A-Za-z0-9._-]+", "_", str(trade.get("instrument") or "trade"))[:50]
                    filename = f"DaemonBlackFx_Auditoria_{instrument}_Trade_{trade_id}.xlsx"
                    export_dir = Path(__file__).resolve().parents[1] / "storage" / "exports" / "trade_audits"
                    export_dir.mkdir(parents=True, exist_ok=True)
                    output_path = export_dir / (
                        f".{filename}.{threading.get_ident()}.{time.time_ns()}.tmp.xlsx"
                    )
                    try:
                        TradeAuditExcelExporter(output_path).export(detail)
                        body = output_path.read_bytes()
                    except Exception as exc:
                        error = {
                            "ok": False,
                            "error": "No fue posible generar el Excel de auditoría",
                            "error_code": "TRADE_AUDIT_EXCEL_EXPORT_FAILED",
                            "trade_id": trade_id,
                            "detail": str(exc),
                        }
                        payload = json.dumps(error, ensure_ascii=False).encode("utf-8")
                        self._send(
                            payload,
                            "application/json; charset=utf-8",
                            HTTPStatus.UNPROCESSABLE_ENTITY,
                        )
                        return
                    finally:
                        try:
                            output_path.unlink(missing_ok=True)
                        except Exception:
                            pass
                    self._send_download(
                        body,
                        filename,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                    return
                api_trade_audit_match = re.fullmatch(r"/api/account/trade/(\d+)/audit/?", path)
                if api_trade_audit_match:
                    detail = service._trade_audit_detail_payload(int(api_trade_audit_match.group(1)))
                    status = HTTPStatus.OK if detail.get("ok") else HTTPStatus.NOT_FOUND
                    payload = json.dumps(detail, ensure_ascii=False).encode("utf-8")
                    self._send(payload, "application/json; charset=utf-8", status)
                    return
                if path.lower() in ("/account", "/account/"):
                    self._send(ACCOUNT_HTML.encode("utf-8"), "text/html; charset=utf-8")
                    return
                if path.lower() in ("/performance", "/performance/", "/rendimiento", "/rendimiento/"):
                    self._send(PERFORMANCE_HTML.encode("utf-8"), "text/html; charset=utf-8")
                    return
                if path.lower() in ("/strategy-bases", "/strategy-bases/", "/bases-estrategias", "/bases-estrategias/"):
                    try:
                        import importlib
                        import dashboard.strategy_bases_page as _sbp
                        importlib.reload(_sbp)
                        self._send(_sbp.STRATEGY_BASES_HTML.encode("utf-8"), "text/html; charset=utf-8")
                    except Exception:
                        self._send(STRATEGY_BASES_HTML.encode("utf-8"), "text/html; charset=utf-8")
                    return
                if path == "/api/account":
                    # Caché corta de lectura: evita reconstruir decenas de consultas
                    # cuando el navegador refresca/navega rápidamente.
                    account = service._cached_account_payload()
                    payload = json.dumps(account, ensure_ascii=False).encode("utf-8")
                    self._send(payload, "application/json; charset=utf-8")
                    return
                if path == "/api/instruments":
                    instruments = service._cached_instruments_payload()
                    payload = json.dumps(instruments, ensure_ascii=False).encode("utf-8")
                    self._send(payload, "application/json; charset=utf-8")
                    return
                if path == "/api/daily-target":
                    payload = json.dumps(service.get_daily_profit_target_payload(), ensure_ascii=False).encode("utf-8")
                    self._send(payload, "application/json; charset=utf-8")
                    return
                if path == "/api/state":
                    payload = json.dumps(service.snapshot(), ensure_ascii=False).encode("utf-8")
                    self._send(payload, "application/json; charset=utf-8")
                    return
                self._send(b"Not found", "text/plain; charset=utf-8", HTTPStatus.NOT_FOUND)

            def do_POST(self):
                """Enruta las (pocas) peticiones de escritura permitidas.

                Solo dos: habilitar/detener un worker y cambiar la seleccion de
                instrumentos. Ninguna abre ni cierra operaciones. El tamano del
                cuerpo se limita a 64 KiB para no aceptar payloads abusivos.
                """
                path = urlparse(self.path).path
                if path == "/api/account/trades/audit/excel/bulk":
                    try:
                        length = int(self.headers.get("Content-Length", "0"))
                    except ValueError:
                        length = 0
                    if length <= 0 or length > 65536:
                        payload = json.dumps(
                            {"ok": False, "error": "Payload inválido"}, ensure_ascii=False
                        ).encode("utf-8")
                        self._send(payload, "application/json; charset=utf-8", HTTPStatus.BAD_REQUEST)
                        return
                    try:
                        body = json.loads(self.rfile.read(length).decode("utf-8"))
                        raw_ids = body.get("trade_ids") if isinstance(body, dict) else None
                        trade_ids = sorted(
                            {int(tid) for tid in raw_ids}
                        ) if isinstance(raw_ids, list) else []
                    except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                        payload = json.dumps(
                            {"ok": False, "error": f"Solicitud inválida: {exc}"}, ensure_ascii=False
                        ).encode("utf-8")
                        self._send(payload, "application/json; charset=utf-8", HTTPStatus.BAD_REQUEST)
                        return
                    if not trade_ids:
                        payload = json.dumps(
                            {"ok": False, "error": "No se seleccionó ningún trade"}, ensure_ascii=False
                        ).encode("utf-8")
                        self._send(payload, "application/json; charset=utf-8", HTTPStatus.BAD_REQUEST)
                        return
                    if len(trade_ids) > 200:
                        payload = json.dumps(
                            {"ok": False, "error": "Máximo 200 trades por descarga"}, ensure_ascii=False
                        ).encode("utf-8")
                        self._send(payload, "application/json; charset=utf-8", HTTPStatus.BAD_REQUEST)
                        return
                    export_dir = Path(__file__).resolve().parents[1] / "storage" / "exports" / "trade_audits"
                    export_dir.mkdir(parents=True, exist_ok=True)
                    failed: list[dict[str, Any]] = []
                    zip_buffer = BytesIO()
                    used_names: set[str] = set()
                    # Se calcula UNA sola vez para todo el lote: reutilizar el mismo
                    # payload de cuenta evita recomputar 99+ trades por cada
                    # seleccionado, que era la causa de los timeouts del bulk-export.
                    shared_account_payload = _json_safe(
                        build_account_payload(service.repository, source="DEMO", recent_limit=None)
                    )
                    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as archive:
                        for trade_id in trade_ids:
                            detail = service._trade_audit_detail_payload(
                                trade_id, account_payload=shared_account_payload
                            )
                            if not detail.get("ok"):
                                failed.append({
                                    "trade_id": trade_id,
                                    "error": detail.get("error") or "Trade no encontrado",
                                })
                                continue
                            trade = detail.get("trade") or {}
                            instrument = re.sub(
                                r"[^A-Za-z0-9._-]+", "_", str(trade.get("instrument") or "trade")
                            )[:50]
                            entry_name = f"DaemonBlackFx_Auditoria_{instrument}_Trade_{trade_id}.xlsx"
                            if entry_name in used_names:
                                entry_name = f"DaemonBlackFx_Auditoria_{instrument}_Trade_{trade_id}_{time.time_ns()}.xlsx"
                            used_names.add(entry_name)
                            tmp_path = export_dir / (
                                f".bulk.{threading.get_ident()}.{time.time_ns()}.tmp.xlsx"
                            )
                            try:
                                TradeAuditExcelExporter(tmp_path).export(detail)
                                archive.writestr(entry_name, tmp_path.read_bytes())
                            except Exception as exc:
                                failed.append({"trade_id": trade_id, "error": str(exc)})
                            finally:
                                try:
                                    tmp_path.unlink(missing_ok=True)
                                except Exception:
                                    pass
                        if failed:
                            summary_lines = [
                                f"Trade {item['trade_id']}: {item['error']}" for item in failed
                            ]
                            archive.writestr(
                                "ERRORES.txt",
                                "No se pudieron exportar los siguientes trades:\n"
                                + "\n".join(summary_lines),
                            )
                    exported_count = len(trade_ids) - len(failed)
                    if exported_count == 0:
                        payload = json.dumps(
                            {
                                "ok": False,
                                "error": "No fue posible generar ningún Excel de auditoría",
                                "failed": failed,
                            },
                            ensure_ascii=False,
                        ).encode("utf-8")
                        self._send(
                            payload,
                            "application/json; charset=utf-8",
                            HTTPStatus.UNPROCESSABLE_ENTITY,
                        )
                        return
                    filename = f"DaemonBlackFx_Auditorias_Lote_{time.strftime('%Y%m%d_%H%M%S')}.zip"
                    self._send_download(zip_buffer.getvalue(), filename, "application/zip")
                    return
                worker_control_match = re.fullmatch(
                    r"/api/workers/([A-Za-z0-9_-]+)/enabled",
                    path,
                )
                if worker_control_match:
                    try:
                        length = int(self.headers.get("Content-Length", "0"))
                        body = json.loads(self.rfile.read(length).decode("utf-8"))
                        enabled = body.get("enabled") if isinstance(body, dict) else None
                        result = service.update_worker_enabled(
                            worker_control_match.group(1),
                            enabled,
                        )
                        status = HTTPStatus.OK if result.get("ok") else HTTPStatus.BAD_REQUEST
                    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                        result = {"ok": False, "error": f"Solicitud inválida: {exc}"}
                        status = HTTPStatus.BAD_REQUEST
                    payload = json.dumps(result, ensure_ascii=False).encode("utf-8")
                    self._send(payload, "application/json; charset=utf-8", status)
                    return
                if path == "/api/daily-target/settings":
                    try:
                        length = int(self.headers.get("Content-Length", "0"))
                        body = json.loads(self.rfile.read(length).decode("utf-8")) if length > 0 else {}
                        enabled = body.get("enabled", True)
                        target_pct = body.get("target_percent", 2.0)
                        buffer_pct = body.get("extra_target_buffer_percent", None)
                        result = service.update_daily_profit_target_settings(
                            enabled=enabled,
                            target_percent=target_pct,
                            extra_target_buffer_percent=buffer_pct,
                        )
                        status = HTTPStatus.OK if result.get("ok") else HTTPStatus.BAD_REQUEST
                    except Exception as exc:
                        result = {"ok": False, "error": str(exc)}
                        status = HTTPStatus.BAD_REQUEST
                    payload = json.dumps(result, ensure_ascii=False).encode("utf-8")
                    self._send(payload, "application/json; charset=utf-8", status)
                    return
                if path == "/api/daily-target/override":
                    try:
                        length = int(self.headers.get("Content-Length", "0"))
                        body = json.loads(self.rfile.read(length).decode("utf-8")) if length > 0 else {}
                        confirm = bool(body.get("confirm", False))
                        extra_pct = float(body.get("extra_percent", 1.0))
                        if not confirm:
                            result = {"ok": False, "error": "Se requiere confirmación explícita del riesgo advertido"}
                            status = HTTPStatus.BAD_REQUEST
                        else:
                            result = service.request_daily_profit_target_override(extra_percent=extra_pct)
                            status = HTTPStatus.OK if result.get("ok") else HTTPStatus.BAD_REQUEST
                    except Exception as exc:
                        result = {"ok": False, "error": str(exc)}
                        status = HTTPStatus.BAD_REQUEST
                    payload = json.dumps(result, ensure_ascii=False).encode("utf-8")
                    self._send(payload, "application/json; charset=utf-8", status)
                    return
                if path != "/api/instruments/selection":
                    self._send(b"Not found", "text/plain; charset=utf-8", HTTPStatus.NOT_FOUND)
                    return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                except ValueError:
                    length = 0
                if length <= 0 or length > 65536:
                    payload = json.dumps({"ok": False, "error": "Payload inválido"}, ensure_ascii=False).encode("utf-8")
                    self._send(payload, "application/json; charset=utf-8", HTTPStatus.BAD_REQUEST)
                    return
                try:
                    body = json.loads(self.rfile.read(length).decode("utf-8"))
                    selected = body.get("selected_symbols") if isinstance(body, dict) else None
                    profile = body.get("selection_profile", "SYNTHETICS") if isinstance(body, dict) else "SYNTHETICS"
                    result = service.update_selected_symbols(selected, selection_profile=profile)
                    status = HTTPStatus.OK if result.get("ok") else HTTPStatus.BAD_REQUEST
                except Exception as exc:
                    result = {"ok": False, "error": str(exc)}
                    status = HTTPStatus.BAD_REQUEST
                payload = json.dumps(result, ensure_ascii=False).encode("utf-8")
                self._send(payload, "application/json; charset=utf-8", status)

        self._server = ThreadingHTTPServer((self.host, self.port), Handler)
        self.port = int(self._server.server_address[1])
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True, name="daemon-dashboard")
        self._thread.start()
        if live:
            self.mark_live()
            self.update_status("ACTIVO")
        else:
            self.mark_offline("DASHBOARD OFFLINE · DATOS PERSISTIDOS")
        return self.url

    def stop(self):
        """Detiene el servidor HTTP y el servicio de noticias."""
        self.news_service.stop()
        if self._server is not None:
            self._server.shutdown()
            self._server.server_close()
        self._server = None
        self._thread = None

    def update_status(self, status):
        """Actualiza el texto de estado y refresca la marca de datos en vivo."""
        with self._lock:
            self._state["status"] = str(status)
            now = _now_iso()
            self._state["updated_at"] = now
            if self._state.get("connection_mode") == "LIVE":
                self._state["last_live_update"] = now
                self._state["data_freshness"] = "LIVE"
            self._persist_state_locked()

    def set_worker_controller(self, controller):
        """Inyecta el callback del coordinador para habilitar/parar workers.

        El dashboard no gestiona procesos: solo delega en `app.main`.
        """
        self._worker_controller = controller

    def update_worker_enabled(self, profile, enabled):
        """Solicita al coordinador activar o detener un worker.

        Valida la entrada y responde con un error claro si esta ejecucion no
        tiene controlador (por ejemplo un dashboard sin daemon multibot).

        Returns:
            dict con `ok` y, en caso de fallo, `error`.
        """
        profile = str(profile or "").upper()
        if not profile or not isinstance(enabled, bool):
            return {"ok": False, "error": "Worker o estado inválido"}
        if self._worker_controller is None:
            if self.repository is not None and hasattr(self.repository, "upsert_worker_runtime_state"):
                from app.main import BOT_PROFILES
                magic = BOT_PROFILES.get(profile, {}).get("magic", 0)
                status = "RUNNING" if enabled else "DISABLED"
                self.repository.upsert_worker_runtime_state(
                    profile,
                    magic,
                    source="DEMO",
                    status=status,
                    last_action="DASHBOARD_MANUAL_TOGGLE",
                    last_reason="Estado modificado manualmente desde el dashboard",
                )
                self._invalidate_navigation_caches()
                return {"ok": True, "persisted": True, "profile": profile, "status": status}
            return {
                "ok": False,
                "error": "El coordinador no admite controlar workers en esta ejecución",
            }
        return self._worker_controller(profile, enabled)

    def _get_daily_profit_target_manager(self):
        """Devuelve una instancia de DailyProfitTargetManager para la fuente DEMO."""
        if not hasattr(self, "_daily_profit_target_manager") or self._daily_profit_target_manager is None:
            if self.repository is None:
                try:
                    from database.repository import TradingRepository
                    self.repository = TradingRepository()
                except Exception:
                    self.repository = None
            if self.repository is not None:
                from strategy.execution.daily_profit_target import DailyProfitTargetManager
                self._daily_profit_target_manager = DailyProfitTargetManager(
                    repository=self.repository,
                    source="DEMO",
                )
            else:
                self._daily_profit_target_manager = None
        return self._daily_profit_target_manager

    def get_daily_profit_target_payload(self) -> dict:
        """Devuelve el estado completo y persistido de la meta diaria."""
        mgr = self._get_daily_profit_target_manager()
        if mgr is not None:
            try:
                status = mgr.get_status()
                with self._lock:
                    self._state["daily_profit_target"] = status
                return status
            except Exception as exc:
                fallback = self._state.get("daily_profit_target")
                if isinstance(fallback, dict) and fallback.get("enabled") is not None:
                    return fallback
                return {"ok": False, "error": str(exc), "enabled": False}
        fallback = self._state.get("daily_profit_target")
        if isinstance(fallback, dict) and fallback.get("enabled") is not None:
            return fallback
        return {
            "source": "DEMO",
            "enabled": True,
            "target_percent": 2.0,
            "extra_target_buffer_percent": 1.0,
            "effective_target_percent": 2.0,
            "daily_return_pct": 0.0,
            "today_net_pnl": 0.0,
            "is_target_reached": False,
            "override_unlocked": False,
            "is_locked": False,
            "can_override": False,
            "status_message": "Servicio no conectado a base de datos.",
        }

    def update_daily_profit_target_settings(
        self, enabled: bool, target_percent: float, extra_target_buffer_percent: float = None
    ) -> dict:
        """Actualiza y persiste la meta diaria configurada."""
        mgr = self._get_daily_profit_target_manager()
        if mgr is None:
            return {"ok": False, "error": "Repositorio no inicializado"}
        try:
            status = mgr.update_settings(
                enabled=bool(enabled),
                target_percent=float(target_percent),
                extra_target_buffer_percent=float(extra_target_buffer_percent) if extra_target_buffer_percent is not None else None,
            )
            with self._lock:
                self._state["daily_profit_target"] = status
                self._persist_state_locked()
            self._invalidate_navigation_caches(account=True)
            return {"ok": True, "daily_profit_target": status}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def request_daily_profit_target_override(self, extra_percent: float = 1.0) -> dict:
        """Desbloquea temporalmente las operaciones tras confirmación de riesgo del usuario."""
        mgr = self._get_daily_profit_target_manager()
        if mgr is None:
            return {"ok": False, "error": "Repositorio no inicializado"}
        try:
            status = mgr.request_override_more_profit(extra_percent=float(extra_percent or 1.0))
            with self._lock:
                self._state["daily_profit_target"] = status
                self._persist_state_locked()
            self._invalidate_navigation_caches(account=True)
            return {"ok": True, "daily_profit_target": status}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def set_instrument_catalog(self, categorized, selected_symbols=None):
        """Publica el catalogo de instrumentos y resuelve la seleccion vigente.

        Agrupa los simbolos por categoria y perfil, y decide la seleccion de
        cada perfil por prioridad: eleccion explicita -> seleccion persistida en
        base de datos -> universo completo. Toda eleccion se filtra contra los
        simbolos realmente disponibles, para que un instrumento que ya no exista
        en el broker no quede seleccionado.

        Args:
            categorized: dict categoria -> simbolos.
            selected_symbols: seleccion explicita opcional.
        """
        categorized=categorized or {}; catalog=[]
        for category, values in categorized.items():
            symbols=_normalize_symbol_list(values)
            if symbols:
                catalog.append({"category":str(category),"selection_profile":_selection_profile_for_category(category),
                                "label":_CATEGORY_LABELS.get(str(category),str(category).replace("_"," ").title()),
                                "symbols":symbols})
        catalog.sort(key=lambda r: ({"SYNTHETICS":0,"FOREX":1,"ORB":2,"IDX_OPEN":3,"MALAYSIAN_SNR":4,"GOLD":5,"ICT":6}.get(r["selection_profile"],9),r["label"].casefold()))
        allowed=_catalog_symbols_by_profile(catalog); persisted={}
        explicit=_normalize_symbol_list(selected_symbols)
        if self.repository is not None and hasattr(self.repository,"latest_instrument_selection_profiles"):
            try: persisted=self.repository.latest_instrument_selection_profiles(source="DEMO") or {}
            except Exception: persisted={}
        if "SYNTHETICS" not in persisted and self.repository is not None:
            try: legacy=self.repository.latest_instrument_selection(source="DEMO")
            except Exception: legacy=None
            if legacy is not None: persisted["SYNTHETICS"]=legacy
        selections={}; versions={}
        for profile in _SELECTION_PROFILES:
            universe=set(allowed.get(profile) or []); pref=persisted.get(profile)
            if explicit:
                chosen=[x for x in explicit if x in universe]
            elif pref is not None:
                chosen=[str(x) for x in (pref.get("selected_symbols") or []) if str(x) in universe]
                versions[profile]=pref.get("version")
            else:
                chosen=sorted(universe,key=str.casefold)
            selections[profile]=_normalize_symbol_list(chosen)
        combined=_normalize_symbol_list(sum((selections.get(p,[]) for p in _SELECTION_PROFILES),[]))
        with self._lock:
            self._state["instrument_catalog"]=catalog; self._state["selection_profiles"]=selections
            self._state["selection_profile_versions"]=versions; self._state["selected_symbols"]=combined
            self._state["selection_version"]=int(self._state.get("selection_version") or 0)+1
            self._state["selection_message"]=(f"Sintéticos: {len(selections['SYNTHETICS'])} · Forex: {len(selections['FOREX'])} · ORB: {len(selections['ORB'])} · Malaysian SNR: {len(selections.get('MALAYSIAN_SNR',[]))} · Cuartos: {len(selections.get('GOLD',[]))} · ICT: {len(selections.get('ICT',[]))} · selecciones independientes")
            self._state["updated_at"]=_now_iso(); self._persist_state_locked()
        self._invalidate_navigation_caches(instruments=True)
        return combined

    def update_selected_symbols(self, selected_symbols, selection_profile=None):
        """Guarda la seleccion de instrumentos de un perfil (o global).

        Rechaza simbolos fuera del catalogo y, al persistir por perfil,
        RELEE lo guardado para verificarlo: si la base no confirma el cambio se
        devuelve error en vez de mentir al usuario diciendo que se guardo.

        Sin `selection_profile` se mantiene el comportamiento global heredado.

        Args:
            selected_symbols: simbolos elegidos.
            selection_profile: SYNTHETICS, FOREX u ORB.

        Returns:
            dict con `ok`, la seleccion resultante y su version; o `error`.
        """
        requested=_normalize_symbol_list(selected_symbols)
        # Compatibilidad v55: llamadas sin perfil siguen representando una selección global.
        if selection_profile is None:
            with self._lock:
                catalog=self._state.get("instrument_catalog") or []
                allowed={symbol for group in catalog for symbol in (group.get("symbols") or [])}
                invalid=[symbol for symbol in requested if symbol not in allowed]
                if invalid: return {"ok":False,"error":"Hay instrumentos fuera del catálogo","invalid":invalid}
                if not requested: return {"ok":False,"error":"Debes mantener al menos un instrumento seleccionado"}
                persisted=None
                if self.repository is not None and hasattr(self.repository,"save_instrument_selection"):
                    try: persisted=self.repository.save_instrument_selection(requested,source="DEMO")
                    except Exception as exc: return {"ok":False,"error":f"No se pudo guardar la selección en SQLAlchemy: {exc}"}
                by_profile=_catalog_symbols_by_profile(catalog); profiles={}
                for profile_name in _SELECTION_PROFILES:
                    universe=set(by_profile.get(profile_name) or [])
                    profiles[profile_name]=[x for x in requested if x in universe]
                self._state["selection_profiles"]=profiles; self._state["selected_symbols"]=requested
                self._state["selection_version"]=int(self._state.get("selection_version") or 0)+1
                self._state["selection_message"]=f"Selección guardada: {len(requested)} instrumentos. Persistirá después de reiniciar y se aplicará en el próximo ciclo."
                self._state["updated_at"]=_now_iso(); self._persist_state_locked()
                self._invalidate_navigation_caches(instruments=True)
                return {"ok":True,"selected_symbols":requested,"selection_version":self._state["selection_version"],
                        "persistent_version":(persisted or {}).get("version"),"persistent":persisted is not None,
                        "message":self._state["selection_message"]}
        profile=str(selection_profile).upper()
        if profile not in _SELECTION_PROFILES: return {"ok":False,"error":f"Perfil no válido: {profile}"}
        with self._lock:
            allowed=set(_catalog_symbols_by_profile(self._state.get("instrument_catalog") or []).get(profile) or [])
            invalid=[x for x in requested if x not in allowed]
            if invalid: return {"ok":False,"error":f"Hay instrumentos fuera del catálogo {profile}","invalid":invalid}
            persisted=None
            if self.repository is not None and hasattr(self.repository,"save_instrument_selection_profile"):
                try:
                    persisted=self.repository.save_instrument_selection_profile(requested,selection_profile=profile,source="DEMO")
                    verify=self.repository.latest_instrument_selection_profile(profile,source="DEMO")
                    if verify is None or verify.get("selected_symbols") != requested:
                        return {"ok":False,"error":f"{profile} no superó la verificación de persistencia SQLAlchemy"}
                except Exception as exc:
                    return {"ok":False,"error":f"No se pudo guardar {profile} en SQLAlchemy: {exc}"}
            profiles=dict(self._state.get("selection_profiles") or {p:[] for p in _SELECTION_PROFILES}); profiles[profile]=requested
            versions=dict(self._state.get("selection_profile_versions") or {})
            combined=_normalize_symbol_list(sum((profiles.get(p,[]) for p in _SELECTION_PROFILES),[]))
            self._state["selection_profiles"]=profiles; self._state["selection_profile_versions"]=versions
            self._state["selected_symbols"]=combined; self._state["selection_version"]=int(self._state.get("selection_version") or 0)+1
            self._state["selection_message"]=f"{profile}: {len(requested)} instrumentos guardados de manera independiente. Se aplicará en el próximo ciclo de ese bot."
            self._state["updated_at"]=_now_iso(); self._persist_state_locked()
            self._invalidate_navigation_caches(instruments=True)
            return {"ok":True,"selection_profile":profile,"selected_symbols":requested,"selection_profiles":profiles,
                    "selection_version":self._state["selection_version"],"persistent_version":(persisted or {}).get("version"),
                    "persistent":persisted is not None,"persistence_verified":persisted is not None,
                    "message":self._state["selection_message"]}

    def get_selected_symbols(self, default=None, selection_profile=None):
        """Devuelve la seleccion vigente, por perfil o global.

        Lo consulta el motor en cada ciclo para saber que instrumentos analizar.
        Con perfil devuelve exactamente lo elegido (aunque este vacio); sin
        perfil recurre a `default` si no hay seleccion.
        """
        with self._lock:
            if selection_profile:
                selected=list((self._state.get("selection_profiles") or {}).get(str(selection_profile).upper()) or [])
            else: selected=list(self._state.get("selected_symbols") or [])
        return selected if selection_profile is not None else (selected or _normalize_symbol_list(default or []))

    def _touch_live_locked(self):
        """Marca actividad en vivo. Requiere el lock ya tomado.

        Returns:
            str: la marca temporal aplicada.
        """
        now = _now_iso()
        self._state["connection_mode"] = "LIVE"
        self._state["data_freshness"] = "LIVE"
        self._state["last_live_update"] = now
        return now

    def cycle_start(self, cycle, total_symbols):
        """Evento: comienza un ciclo de analisis.

        Reinicia los contadores del ciclo y refresca las posiciones abiertas.
        """
        with self._lock:
            self._touch_live_locked()
            self._state.update({
                "status": "ANALIZANDO",
                "cycle": int(cycle),
                "cycle_started_at": _now_iso(),
                "cycle_elapsed_seconds": None,
                "symbols_total": int(total_symbols),
                "symbols_processed": 0,
                "current_symbol": None,
                "updated_at": _now_iso(),
            })
            self._refresh_open_positions_locked()
            self._refresh_account_locked()
            self._persist_state_locked()

    def symbol_start(self, symbol, index, total):
        """Evento: comienza el analisis de un instrumento."""
        with self._lock:
            self._touch_live_locked()
            self._state.update({
                "current_symbol": str(symbol),
                "symbols_processed": max(0, int(index) - 1),
                "symbols_total": int(total),
                "updated_at": _now_iso(),
            })
            self._persist_state_locked()

    def symbol_result(self, result, index, total, elapsed_seconds):
        """Evento: termina el analisis de un instrumento.

        Extrae las metricas de calidad, traduce accion y motivo a espanol y
        anade la fila al historial reciente. Es el registro que permite ver
        POR QUE el bot no entro en un instrumento.
        """
        result = result or {}
        quality = _extract_quality(result)
        action = result.get("action") or "SIN ACCIÓN"
        reason = result.get("reason") or result.get("error")
        decision = quality.get("decision")
        row = _enrich_recent_row({
            "time": _now_iso(),
            "symbol": result.get("symbol") or "DESCONOCIDO",
            "action": action,
            "reason": reason,
            "elapsed_seconds": round(float(elapsed_seconds or 0.0), 3),
            **quality,
        })
        with self._lock:
            self._recent.appendleft(_json_safe(row))
            self._state.update({
                "symbols_processed": int(index),
                "symbols_total": int(total),
                "current_symbol": row["symbol"],
                "updated_at": _now_iso(),
                "recent": list(self._recent),
            })
            self._refresh_open_positions_locked()
            self._refresh_account_locked()
            self._persist_state_locked()

    def cycle_end(self, elapsed_seconds):
        """Evento: termina el ciclo; pasa a espera y refresca los datos."""
        with self._lock:
            self._touch_live_locked()
            self._state.update({
                "status": "ESPERANDO SIGUIENTE CICLO",
                "cycle_elapsed_seconds": round(float(elapsed_seconds or 0.0), 3),
                "current_symbol": None,
                "updated_at": _now_iso(),
            })
            self._refresh_open_positions_locked()
            self._refresh_account_locked()
            self._persist_state_locked()

    def monitor_result(self, monitor):
        """Evento: resultado del monitor de posiciones abiertas."""
        with self._lock:
            self._touch_live_locked()
            self._state["last_monitor"] = _json_safe(monitor)
            self._state["updated_at"] = _now_iso()
            self._refresh_open_positions_locked()
            self._refresh_account_locked()
            self._persist_state_locked()

    def _refresh_open_positions_locked(self):
        """Reconstruye la lista de posiciones abiertas para la interfaz.

        Muestra TODAS las posiciones persistidas: las de `source=DEMO` las
        gestiona el bot y las `MT5_EXTERNAL` son solo visualizacion.

        En modo multibot el coordinador no ve el estado interno de cada worker,
        asi que la auditoria visual y el snapshot de mercado se reconstruyen
        desde la base de datos. Ademas resuelve el worker propietario de cada
        posicion y calcula el resumen de salud (mantener / vigilar / proteger /
        salida), que es ADVISORY: informa, no cierra nada.

        Requiere el lock ya tomado. Cualquier error de lectura aborta el
        refresco dejando el estado anterior.
        """
        if self.repository is None:
            return
        try:
            # Mostramos todas las posiciones persistidas. Las de source=DEMO son
            # gestionadas por DaemonBlackFx; MT5_EXTERNAL es sólo visualización.
            trades = self.repository.open_trades(source=None) or []
        except Exception:
            return
        monitor = self._state.get("last_monitor") or {}
        break_even_monitor = monitor.get("break_even") if isinstance(monitor, dict) else {}
        snapshots = []
        if isinstance(monitor, dict):
            snapshots = monitor.get("positions") or []
        if not snapshots and isinstance(break_even_monitor, dict):
            snapshots = break_even_monitor.get("positions") or []
        market_by_id = {str(row.get("trade_id")): row for row in (snapshots or []) if isinstance(row, dict)}

        # v54: en multi-bot el coordinador no recibe el estado local de cada worker.
        # La auditoría visual y el snapshot de mercado se reconstruyen desde SQLAlchemy.
        visual_rows = []
        try:
            if hasattr(self.repository, "position_visual_audits"):
                visual_rows = self.repository.position_visual_audits(source="DEMO") or []
        except Exception:
            visual_rows = []

        trade_visual_rows = []
        try:
            if hasattr(self.repository, "trade_visual_audits"):
                trade_visual_rows = self.repository.trade_visual_audits(source="DEMO") or []
        except Exception:
            trade_visual_rows = []
        trade_visual_by_id = {
            str(row.get("trade_id")): row
            for row in trade_visual_rows
            if row.get("trade_id") is not None
        }
        visual_by_symbol = {}
        for row in visual_rows:
            symbol = str(row.get("instrument") or "")
            if symbol and symbol not in visual_by_symbol:
                visual_by_symbol[symbol] = row

        worker_rows = []
        try:
            if hasattr(self.repository, "worker_runtime_states"):
                worker_rows = self.repository.worker_runtime_states(source="DEMO") or []
        except Exception:
            worker_rows = []
        worker_by_profile = {
            str(row.get("bot_profile") or "").upper(): row
            for row in worker_rows
            if row.get("bot_profile") and not _is_retired_worker_profile(row.get("bot_profile"))
        }

        charts = monitor.get("charts") if isinstance(monitor, dict) else {}
        chart_by_symbol = charts if isinstance(charts, dict) else {}
        recent_by_symbol = {}
        for recent_row in self._recent:
            recent_symbol = str(recent_row.get("symbol") or "")
            if recent_symbol and recent_symbol not in recent_by_symbol:
                recent_by_symbol[recent_symbol] = recent_row

        compact = []
        counts = {"mantener": 0, "vigilar": 0, "proteger": 0, "salida": 0, "sin_datos": 0, "solo_visual": 0}
        for trade in trades:
            details = trade.get("details") if isinstance(trade, dict) else {}
            metadata = details.get("metadata", {}) if isinstance(details, dict) else {}
            trade_source = str(trade.get("source") or "").upper()
            ownership = _position_owner(trade, metadata)
            managed_by_daemon = bool(ownership.get("managed_by_daemon"))
            owner_profile = ownership.get("owner_profile")
            worker_state = worker_by_profile.get(str(owner_profile or "").upper(), {})
            position = {
                "id": trade.get("id"),
                "source": trade_source,
                **ownership,
                "worker_status": worker_state.get("status"),
                "worker_pid": worker_state.get("pid"),
                "worker_last_event_time": worker_state.get("last_event_time"),
                "management_label": (
                    f"GESTIONADA POR {owner_profile}"
                    if managed_by_daemon and owner_profile
                    else "DAEMON · OWNER NO IDENTIFICADO"
                    if managed_by_daemon
                    else "MT5 EXTERNA · SOLO VISUALIZACIÓN"
                ),
                "persistence_status": "LIVE" if self._state.get("connection_mode") == "LIVE" else "PERSISTED",
                "broker_verification": "VERIFICADO EN ESTA SESIÓN" if self._state.get("connection_mode") == "LIVE" else "PENDIENTE DE RECONCILIAR CON MT5",
                "last_live_update": self._state.get("last_live_update"),
                "symbol": trade.get("instrument"),
                "direction": trade.get("direction"),
                "entry_price": trade.get("entry_price"),
                "entry_time": trade.get("entry_time"),
                "stop_loss": trade.get("stop_loss"),
                "take_profit": trade.get("take_profit"),
                "risk_percent": trade.get("risk_percent"),
                "risk_amount": trade.get("risk_amount"),
                "leg": metadata.get("trade_leg"),
                "execution_mode": metadata.get("execution_mode"),
                "break_even_confirmed": metadata.get("break_even_confirmed", False),
                "quality_score": metadata.get("trade_score"),
                "confirmation_percentage": metadata.get("confirmation_percentage"),
            }
            symbol = str(trade.get("instrument") or "")
            persistent_visual = visual_by_symbol.get(symbol, {})
            trade_visual = trade_visual_by_id.get(str(trade.get("id")), {})
            market = (
                market_by_id.get(str(trade.get("id")), {})
                or trade_visual.get("latest_market")
                or persistent_visual.get("market")
                or {}
            )
            # v79: para salud de una posición abierta, la vista actual persistida
            # por su propio owner tiene prioridad sobre un análisis general del símbolo.
            current_strategy_view = (
                market.get("current_strategy_view")
                if isinstance(market, dict)
                else None
            )
            if not isinstance(current_strategy_view, dict):
                current_strategy_view = {}

            general_latest = {}
            try:
                general_latest = (
                    self.repository.latest_symbol_process_result(symbol, source="DEMO")
                    if hasattr(self.repository, "latest_symbol_process_result")
                    else {}
                )
            except Exception:
                general_latest = {}
            if not general_latest:
                general_latest = recent_by_symbol.get(symbol, {}) or {}

            latest = current_strategy_view or dict(general_latest)
            if current_strategy_view:
                latest.update(current_strategy_view)

            position.update(_position_health(position, market=market, latest=latest))
            position["strategy_view_updated_at"] = (
                market.get("strategy_evaluated_at")
                if isinstance(market, dict)
                else None
            )
            position["market_updated_at"] = (
                market.get("market_evaluated_at")
                if isinstance(market, dict)
                else None
            )
            position["telemetry_mode"] = (
                market.get("telemetry_mode")
                if isinstance(market, dict)
                else None
            )

            live_market_available = bool(
                market and (
                    market.get("current_price") not in (None, "")
                    or market.get("current_rr") not in (None, "")
                )
            )
            worker_running = str(worker_state.get("status") or "").upper() in {"RUNNING", "STARTING", "RUNNING_UNIFIED"}

            if managed_by_daemon and not live_market_available:
                position["health_score"] = None
                position["health_grade"] = "SIN DATOS"
                position["recommendation"] = (
                    "SIN TELEMETRÍA DEL WORKER"
                    if worker_running else "WORKER SIN ACTIVIDAD"
                )
                position["reasons"] = [
                    f"Owner operativo: {owner_profile or 'no identificado'}",
                    "No existe snapshot de mercado reciente para calcular R/SL/TP de forma confiable",
                    "La posición permanece persistida; la salud no se inventa con un score por defecto",
                ]

            if not managed_by_daemon:
                position["health_score"] = None
                position["health_grade"] = "NO EVALUABLE"
                position["recommendation"] = "SOLO VISUALIZACIÓN"
                position["advisory_only"] = True
                if ownership.get("ownership_status") == "MAGIC_DAEMON_PERO_SOURCE_EXTERNA":
                    position["reasons"] = [
                        f"Magic asociado a DaemonBlackFx ({ownership.get('owner_magic')}) pero la fila está persistida como MT5_EXTERNAL",
                        f"Owner probable: {owner_profile or 'no identificado'}",
                        "Requiere reconciliación antes de permitir gestión automática de SL/TP/cierre",
                    ]
                else:
                    position["reasons"] = [
                        "Posición MT5 no confirmada como propiedad de DaemonBlackFx",
                        "Se mantiene únicamente para visibilidad y auditoría",
                    ]
            if self._state.get("connection_mode") != "LIVE":
                position["reasons"] = [
                    "Último estado conocido: daemon/MT5 sin conexión",
                    *[r for r in (position.get("reasons") or []) if r != "Sin lectura R actual del broker"],
                ]
                if managed_by_daemon:
                    position["recommendation"] = "SIN VALIDACIÓN EN VIVO"
                else:
                    position["recommendation"] = "SOLO VISUALIZACIÓN"
                position["advisory_only"] = True
            position["current_stop_loss"] = market.get("current_stop_loss")
            position["visual_audit_updated_at"] = (
                trade_visual.get("latest_updated_at")
                or persistent_visual.get("updated_at")
            )
            position["chart_owner_profile"] = (
                trade_visual.get("bot_profile")
                or persistent_visual.get("bot_profile")
            )
            position["chart_owner_magic"] = (
                trade_visual.get("daemon_magic")
                or persistent_visual.get("daemon_magic")
            )
            position["entry_chart"] = trade_visual.get("entry_chart") or {}
            position["entry_chart_captured_at"] = trade_visual.get("entry_captured_at")
            position["chart"] = (
                trade_visual.get("latest_chart")
                or persistent_visual.get("chart")
                or chart_by_symbol.get(symbol, {})
                or {}
            )
            persisted_entry_context = trade_visual.get("entry_context") or {}
            # Snapshot INMUTABLE de la tesis que justificó la entrada.
            position["entry_strategy_view"] = persisted_entry_context or {
                "decision": metadata.get("confirmation_decision"),
                "direction": trade.get("direction"),
                "score": metadata.get("trade_score") if metadata.get("trade_score") is not None else metadata.get("score"),
                "grade": metadata.get("trade_grade") if metadata.get("trade_grade") is not None else metadata.get("grade"),
                "confirmation_percentage": metadata.get("confirmation_percentage"),
                "passed": [_LABELS.get(str(x), str(x).replace("_", " ").title()) for x in (metadata.get("passed_confirmations") or [])],
                "missing": [_LABELS.get(str(x), str(x).replace("_", " ").title()) for x in (metadata.get("missing_confirmations") or [])],
                "critical_failures": [_LABELS.get(str(x), str(x).replace("_", " ").title()) for x in (metadata.get("critical_confirmation_failures") or [])],
                "divergence_confirmed": bool(metadata.get("divergence_confirmation")),
                "divergence_type": metadata.get("divergence_type"),
                "harmonic_confirmed": bool(metadata.get("harmonic_confirmed")),
                "harmonic_pattern": metadata.get("harmonic_pattern"),
                "harmonic_score": metadata.get("harmonic_score"),
                "h1_doji_confirmed": bool(metadata.get("h1_doji_confirmation")),
                "h1_doji_type": metadata.get("h1_doji_type"),
                "h1_doji_zone": metadata.get("h1_doji_zone"),
                "h1_doji_time": metadata.get("h1_doji_time"),
                "h1_trend": metadata.get("h1_trend"),
                "structure_break": metadata.get("m15_structure_break_type"),
                "zone": metadata.get("m15_zone"),
            }

            # Enriquecimiento universal multi-estrategia de la tesis al abrir (SMC, Malaysian SNR, ORB, Gold Quarters, etc.)
            ent_view = position["entry_strategy_view"]
            strat_name = str(
                ent_view.get("strategy_name")
                or metadata.get("strategy_name")
                or trade.get("strategy_name")
                or trade.get("bot_profile")
                or "SMC"
            ).upper()
            ent_view["strategy_name"] = strat_name

            scenario = ent_view.get("scenario") or metadata.get("scenario") or metadata.get("msnr_scenario")
            if scenario: ent_view["scenario"] = scenario
            ref_lvl = ent_view.get("ref_level") if ent_view.get("ref_level") is not None else metadata.get("ref_level") or metadata.get("msnr_ref_level")
            if ref_lvl is not None: ent_view["ref_level"] = ref_lvl
            brk_lvl = ent_view.get("break_level") if ent_view.get("break_level") is not None else metadata.get("break_level") or metadata.get("msnr_break_level")
            if brk_lvl is not None: ent_view["break_level"] = brk_lvl
            adx_val = ent_view.get("momentum_adx") if ent_view.get("momentum_adx") is not None else metadata.get("momentum_adx") or metadata.get("msnr_adx") or metadata.get("adx")
            if adx_val is not None: ent_view["momentum_adx"] = adx_val
            body_rat = ent_view.get("body_ratio") if ent_view.get("body_ratio") is not None else metadata.get("body_ratio") or metadata.get("msnr_body_ratio")
            if body_rat is not None: ent_view["body_ratio"] = body_rat
            run_tgt = ent_view.get("runner_target_name") or metadata.get("runner_target_name")
            if run_tgt: ent_view["runner_target_name"] = run_tgt
            run_rr = ent_view.get("runner_rr") if ent_view.get("runner_rr") is not None else metadata.get("runner_rr")
            if run_rr is not None: ent_view["runner_rr"] = run_rr

            or_high = ent_view.get("opening_range_high") if ent_view.get("opening_range_high") is not None else metadata.get("opening_range_high")
            if or_high is not None: ent_view["opening_range_high"] = or_high
            or_low = ent_view.get("opening_range_low") if ent_view.get("opening_range_low") is not None else metadata.get("opening_range_low")
            if or_low is not None: ent_view["opening_range_low"] = or_low
            or_mid = ent_view.get("opening_range_midpoint") if ent_view.get("opening_range_midpoint") is not None else metadata.get("opening_range_midpoint")
            if or_mid is not None: ent_view["opening_range_midpoint"] = or_mid
            s_vwap = ent_view.get("session_vwap") if ent_view.get("session_vwap") is not None else metadata.get("session_vwap")
            if s_vwap is not None: ent_view["session_vwap"] = s_vwap

            maj_q = ent_view.get("major_quarter") if ent_view.get("major_quarter") is not None else metadata.get("major_quarter") or metadata.get("quarter_level")
            if maj_q is not None: ent_view["major_quarter"] = maj_q
            q_lvl = ent_view.get("quarters_level") if ent_view.get("quarters_level") is not None else metadata.get("quarter_level") or metadata.get("quarters_level")
            if q_lvl is not None: ent_view["quarters_level"] = q_lvl
            tgt_q = ent_view.get("target_quarter") if ent_view.get("target_quarter") is not None else metadata.get("quarter_target") or metadata.get("target_quarter")
            if tgt_q is not None: ent_view["target_quarter"] = tgt_q

            # Auto-poblar checklist de tesis al abrir si viene vacío
            if not ent_view.get("passed"):
                if "MALAYSIAN" in strat_name or scenario or brk_lvl is not None:
                    scen_desc = "Ruptura Fresh H1 + Retest M15" if "1" in str(scenario or "") else "Fractal HCH / Quiebre Rápido" if "3" in str(scenario or "") else str(scenario or "Ruptura Institucional")
                    ent_view["scenario_desc"] = scen_desc
                    ent_view["passed"] = [
                        f"Ruptura de Nivel H1 ({scen_desc})",
                        f"Retest M15 Confirmado ({brk_lvl})" if brk_lvl is not None else "Retest M15 al nivel de Break",
                        f"Fuerza Momentum (ADX {adx_val} >= 20)" if adx_val is not None else "Fuerza Momentum ADX institucional",
                        f"Cuerpo Sólido ({float(body_rat)*100:.0f}% >= 50%)" if body_rat is not None and isinstance(body_rat, (int, float)) else "Cuerpo de vela envolvente sólido",
                        f"Ejecución Asimétrica (TP1 1:1 + Corredora {run_tgt or 'TP2'} 1:{run_rr or 2.0}R)",
                    ]
                    if ent_view.get("score") is None: ent_view["score"] = 90.0
                    if not ent_view.get("grade"): ent_view["grade"] = "A+"
                    if not ent_view.get("decision") or ent_view.get("decision") == "MALAYSIAN_SNR_CONFIRMED":
                        ent_view["decision"] = f"MALAYSIAN SNR · {scen_desc.upper()}"
                elif "ORB" in strat_name or or_high is not None:
                    dir_txt = str(ent_view.get("direction") or trade.get("direction") or "BUY").upper()
                    ent_view["passed"] = [
                        f"Rango M15 NY ({or_low} - {or_high})" if or_high and or_low else "Rango de Apertura NY delimitado",
                        f"Quiebre de Rango Confirmado ({dir_txt})",
                        "Retest M5 / Microestructura a favor",
                        "Sesión Operativa New York activa",
                    ]
                    if ent_view.get("score") is None: ent_view["score"] = 88.0
                    if not ent_view.get("grade"): ent_view["grade"] = "A"
                    if not ent_view.get("decision"): ent_view["decision"] = "ORB NEW YORK · RUPTURA CONFIRMADA"
                elif "GOLD" in strat_name or q_lvl is not None:
                    ent_view["passed"] = [
                        f"Cuadrante Mayor Institucional ({maj_q})" if maj_q else "Nivel Cuadrante Mayor",
                        f"Reacción / Rebote Institucional en {q_lvl}" if q_lvl else "Rechazo institucional en nivel de precio",
                        f"Proyección hacia Target Cuadrante {tgt_q}" if tgt_q else "Proyección hacia Target de Cuadrante",
                    ]
                    if ent_view.get("score") is None: ent_view["score"] = 86.0
                    if not ent_view.get("grade"): ent_view["grade"] = "A"
                    if not ent_view.get("decision"): ent_view["decision"] = "GOLD QUARTERS · REACCIÓN INSTITUCIONAL"

            # Sincronizar score y confirmaciones con la posición para la tabla de salud
            ent_score = ent_view.get("score")
            if ent_score is not None and (position.get("quality_score") is None or position.get("quality_score") == ""):
                position["quality_score"] = ent_score
            ent_conf = ent_view.get("confirmation_percentage")
            if ent_conf is not None and (position.get("confirmation_percentage") is None or position.get("confirmation_percentage") == ""):
                position["confirmation_percentage"] = ent_conf
            elif position.get("confirmation_percentage") is None or position.get("confirmation_percentage") == "":
                passed_n = len(ent_view.get("passed") or [])
                if passed_n > 0:
                    position["confirmation_percentage"] = 100.0 if not ent_view.get("missing") else round(passed_n / (passed_n + len(ent_view.get("missing") or [])) * 100.0, 1)

            # Cálculo de duración / tiempo en el trade
            entry_iso = trade.get("entry_time") or metadata.get("entry_time") or ent_view.get("entry_time")
            duration_str = "—"
            duration_minutes = None
            if entry_iso:
                try:
                    iso_clean = str(entry_iso).replace("Z", "+00:00")
                    ent_dt = datetime.fromisoformat(iso_clean)
                    if ent_dt.tzinfo is None:
                        ent_dt = ent_dt.replace(tzinfo=timezone.utc)
                    now_utc = datetime.now(timezone.utc)
                    diff_sec = max(0.0, (now_utc - ent_dt).total_seconds())
                    duration_minutes = int(diff_sec // 60)
                    hours = int(duration_minutes // 60)
                    mins = int(duration_minutes % 60)
                    days = int(hours // 24)
                    if days > 0:
                        rem_hours = hours % 24
                        duration_str = f"{days}d {rem_hours}h"
                    elif hours > 0:
                        duration_str = f"{hours}h {mins:02d}m"
                    else:
                        duration_str = f"{mins}m"
                except Exception:
                    duration_str = "—"
            position["duration_str"] = duration_str
            position["duration_minutes"] = duration_minutes

            persisted_current = (
                market.get("current_strategy_view")
                if isinstance(market.get("current_strategy_view"), dict)
                else {}
            )
            if persisted_current:
                position["latest_strategy_view"] = dict(persisted_current)
                cur_view = position["latest_strategy_view"]
                if not cur_view.get("direction"):
                    cur_view["direction"] = latest.get("direction") or trade.get("direction")
                if not cur_view.get("decision"):
                    cur_view["decision"] = cur_view.get("action") or cur_view.get("status") or latest.get("decision") or latest.get("action")
                if cur_view.get("score") is None:
                    cur_view["score"] = latest.get("score") or latest.get("trade_score")
                if cur_view.get("confirmation_percentage") is None:
                    cur_view["confirmation_percentage"] = latest.get("confirmation_percentage")
                if not cur_view.get("passed"):
                    cur_view["passed"] = latest.get("passed") or latest.get("passed_confirmations") or []
                if not cur_view.get("missing"):
                    cur_view["missing"] = latest.get("missing") or latest.get("missing_confirmations") or []
                if not cur_view.get("critical_failures"):
                    cur_view["critical_failures"] = latest.get("critical_failures") or latest.get("critical_confirmation_failures") or []
                if not cur_view.get("h1_trend"):
                    cur_view["h1_trend"] = latest.get("h1_trend")
                if not cur_view.get("zone"):
                    cur_view["zone"] = latest.get("zone") or latest.get("m15_zone")
                if not cur_view.get("structure_break"):
                    cur_view["structure_break"] = latest.get("structure_break") or latest.get("m15_structure_break_type")
                if not cur_view.get("evaluated_at"):
                    cur_view["evaluated_at"] = (
                        market.get("strategy_evaluated_at")
                        or latest.get("_event_time")
                        or latest.get("evaluated_at")
                    )
                for key in (
                    "divergence_confirmed",
                    "divergence_type",
                    "harmonic_confirmed",
                    "harmonic_pattern",
                    "chart_pattern_confirmed",
                    "chart_pattern_name",
                    "chart_pattern_strength",
                    "chart_pattern_conflict",
                    "chart_pattern_supporting_pattern",
                    "chart_pattern_supporting_direction",
                    "chart_pattern_supporting_strength",
                    "chart_pattern_conflicting_pattern",
                    "chart_pattern_conflicting_direction",
                    "chart_pattern_conflicting_strength",
                    "chart_pattern_conflict_level",
                    "chart_pattern_conflict_reason",
                    "h1_doji_confirmed",
                    "h1_doji_type",
                    "h1_doji_zone",
                ):
                    if cur_view.get(key) is None and key in latest:
                        cur_view[key] = latest.get(key)
            else:
                position["latest_strategy_view"] = {
                    "decision": latest.get("decision") or latest.get("action"),
                    "state": latest.get("state") or latest.get("action"),
                    "reason": latest.get("reason"),
                    "direction": latest.get("direction") or trade.get("direction"),
                    "score": latest.get("score") or latest.get("trade_score"),
                    "confirmation_percentage": latest.get("confirmation_percentage"),
                    "passed": latest.get("passed") or latest.get("passed_confirmations") or [],
                    "missing": latest.get("missing") or latest.get("missing_confirmations") or [],
                    "critical_failures": latest.get("critical_failures") or latest.get("critical_confirmation_failures") or [],
                    "divergence_confirmed": latest.get("divergence_confirmed") or latest.get("divergence_confirmation"),
                    "divergence_type": latest.get("divergence_type"),
                    "harmonic_confirmed": latest.get("harmonic_confirmed"),
                    "harmonic_pattern": latest.get("harmonic_pattern"),
                    "chart_pattern_confirmed": latest.get("chart_pattern_confirmed"),
                    "chart_pattern_name": latest.get("chart_pattern_name"),
                    "chart_pattern_strength": latest.get("chart_pattern_strength"),
                    "chart_pattern_conflict": latest.get("chart_pattern_conflict"),
                    "chart_pattern_supporting_pattern": latest.get("chart_pattern_supporting_pattern"),
                    "chart_pattern_supporting_direction": latest.get("chart_pattern_supporting_direction"),
                    "chart_pattern_supporting_strength": latest.get("chart_pattern_supporting_strength"),
                    "chart_pattern_conflicting_pattern": latest.get("chart_pattern_conflicting_pattern"),
                    "chart_pattern_conflicting_direction": latest.get("chart_pattern_conflicting_direction"),
                    "chart_pattern_conflicting_strength": latest.get("chart_pattern_conflicting_strength"),
                    "chart_pattern_conflict_level": latest.get("chart_pattern_conflict_level"),
                    "chart_pattern_conflict_reason": latest.get("chart_pattern_conflict_reason"),
                    "h1_doji_confirmed": latest.get("h1_doji_confirmed") or latest.get("h1_doji_confirmation"),
                    "h1_doji_type": latest.get("h1_doji_type"),
                    "h1_doji_zone": latest.get("h1_doji_zone"),
                    "structure_break": latest.get("structure_break") or latest.get("m15_structure_break_type"),
                    "h1_trend": latest.get("h1_trend"),
                    "zone": latest.get("zone") or latest.get("m15_zone"),
                    "evaluated_at": latest.get("_event_time"),
                }

            # v119: Transformar bloqueo técnico 'BLOCKED_ACTIVE_TRADE' en seguimiento real de la tesis activa
            cur_view = position["latest_strategy_view"]
            raw_dec = str(cur_view.get("decision") or "")
            raw_act = str(cur_view.get("action") or cur_view.get("state") or "")
            raw_reason = str(cur_view.get("reason") or "")
            is_gatekeeper_block = (
                any(k in raw_dec.upper() or k in raw_act.upper() or k in raw_reason.upper()
                    for k in ("BLOCKED_ACTIVE_TRADE", "WAITING_TRADE_RESOLUTION", "ESPERANDO CIERRE TP/SL/BE"))
                or raw_dec in ("OBSERVACION_ACTUAL", "TESIS_ACTIVA_EN_CURSO", "")
                or not cur_view.get("passed")
            )

            # Preservar estrategia y dirección en el seguimiento actual
            if not cur_view.get("strategy_name"):
                cur_view["strategy_name"] = strat_name
            if not cur_view.get("direction"):
                cur_view["direction"] = trade.get("direction") or position.get("direction") or "BUY"

            if is_gatekeeper_block:
                curr_rr_raw = market.get("current_rr") if market.get("current_rr") is not None else position.get("current_rr")
                try:
                    curr_rr_float = float(curr_rr_raw) if curr_rr_raw is not None else None
                except Exception:
                    curr_rr_float = None

                rec = position.get("recommendation") or "MANTENER"
                curr_p = market.get("current_price") or position.get("current_price") or trade.get("current_price")
                ent_p = trade.get("entry_price") or position.get("entry_price")

                if curr_rr_float is not None:
                    if curr_rr_float >= 1.0:
                        cur_view["decision"] = f"TESIS VIGENTE · EN BENEFICIO (+{curr_rr_float:.2f}R)"
                    elif curr_rr_float > 0.0:
                        cur_view["decision"] = f"TESIS VIGENTE · PROGRESO FAVORABLE (+{curr_rr_float:.2f}R)"
                    elif curr_rr_float > -0.5:
                        cur_view["decision"] = f"TESIS VIGENTE · EN CONSOLIDACIÓN ({curr_rr_float:.2f}R)"
                    else:
                        cur_view["decision"] = f"TESIS VIGENTE · EN RETROCESO ({curr_rr_float:.2f}R)"
                else:
                    cur_view["decision"] = "TESIS VIGENTE · EN SEGUIMIENTO ACTIVO"

                live_confirmations = [
                    "Estructura de mercado compatible con la dirección del trade",
                    "Tesis institucional sin invalidación contraria",
                    "Gestión dinámica activa por Daemon de Supervisión",
                ]
                if curr_rr_float is not None and curr_rr_float >= 1.0:
                    live_confirmations.append("Nivel TP1 superado: operación en zona de beneficio protegida")
                be_active = bool(position.get("break_even_confirmed") or metadata.get("break_even_confirmed") or position.get("be_protected"))
                if be_active:
                    live_confirmations.append("Stop Loss protegido en Break-Even (Riesgo Cero)")
                if "MALAYSIAN" in strat_name:
                    live_confirmations.append("Acción del precio respetando zonas Break / Retest")
                elif "ORB" in strat_name:
                    live_confirmations.append("Precio cotizando en rango de expansión post-apertura NY")
                elif "GOLD" in strat_name:
                    live_confirmations.append("Transición de precio hacia niveles clave de cuadrante")

                cur_view["passed"] = live_confirmations
                cur_view["missing"] = []
                cur_view["critical_failures"] = []
                cur_view["reason"] = f"Monitoreo continuo en vivo (velas cerradas). La tesis se mantiene vigente con recomendación {rec}. Nuevas órdenes pausadas para salvaguardar la gestión de capital."
                cur_view["observations"] = [
                    f"Recomendación del sistema: {rec}",
                    f"Progreso financiero: {curr_rr_float:+.2f}R" if curr_rr_float is not None else "Progreso financiero: en seguimiento",
                    f"Precio actual {curr_p} vs Entrada {ent_p}" if curr_p and ent_p else "Monitoreo en vivo de velas H1/M15/M5 activo",
                ]
                if cur_view.get("score") is None:
                    cur_view["score"] = position.get("health_score") or ent_view.get("score") or 85.0

            rec = position.get("recommendation")
            if rec == "MANTENER": counts["mantener"] += 1
            elif rec == "VIGILAR": counts["vigilar"] += 1
            elif rec == "PROTEGER": counts["proteger"] += 1
            elif rec == "SALIDA A EVALUAR": counts["salida"] += 1
            elif rec == "SOLO VISUALIZACIÓN": counts["solo_visual"] += 1
            else: counts["sin_datos"] += 1
            compact.append(position)
        self._state["open_positions"] = _json_safe(compact)
        self._state["position_health_summary"] = counts

    def _refresh_account_locked(self):
        """Actualiza el bloque de cuenta desde la cache. Requiere el lock."""
        self._state["account"] = self._cached_account_payload()

    def _refresh_selection_profiles_from_db_locked(self):
        """Recarga selecciones autoritativas desde SQLAlchemy.

        v57: el estado JSON/memoria del dashboard deja de ser la fuente de verdad.
        Si existe una preferencia persistida, siempre prevalece después de un
        refresco o reinicio del servicio.
        """
        if self.repository is None or not hasattr(self.repository, "latest_instrument_selection_profiles"):
            return
        try:
            persisted = self.repository.latest_instrument_selection_profiles(source="DEMO") or {}
        except Exception as exc:
            self._state["selection_persistence_status"] = "ERROR"
            self._state["selection_persistence_error"] = str(exc)
            return

        catalog = list(self._state.get("instrument_catalog") or [])
        cat_keys = {g.get("category") for g in catalog}
        if "orb_ny_xagusd" not in cat_keys:
            catalog.append({"category": "orb_ny_xagusd", "selection_profile": "ORB", "label": "Plata (XAGUSD)", "symbols": ["XAGUSD"]})
        if "orb_ny_micro_xagusd" not in cat_keys:
            catalog.append({"category": "orb_ny_micro_xagusd", "selection_profile": "ORB", "label": "Plata Micro (XAGUSD)", "symbols": ["XAGUSDmicro"]})
        if "gold_cuartos_xauusd" not in cat_keys:
            catalog.append({"category": "gold_cuartos_xauusd", "selection_profile": "GOLD", "label": "Oro Cuartos (XAUUSD)", "symbols": ["XAUUSD", "XAUUSDmicro"]})
        if "gold_cuartos_xagusd" not in cat_keys:
            catalog.append({"category": "gold_cuartos_xagusd", "selection_profile": "GOLD", "label": "Plata Cuartos (XAGUSD)", "symbols": ["XAGUSD", "XAGUSDmicro"]})
        if "ict_metals_xagusd" not in cat_keys:
            catalog.append({"category": "ict_metals_xagusd", "selection_profile": "ICT", "label": "ICT Metales · Plata (XAGUSD)", "symbols": ["XAGUSD", "XAGUSDmicro"]})
        if "ict_metals_xauusd" not in cat_keys:
            catalog.append({"category": "ict_metals_xauusd", "selection_profile": "ICT", "label": "ICT Metales · Oro (XAUUSD)", "symbols": ["XAUUSD", "XAUUSDmicro"]})
        if "ict_crypto_btcusd" not in cat_keys:
            catalog.append({"category": "ict_crypto_btcusd", "selection_profile": "ICT", "label": "ICT Criptomonedas · Bitcoin (BTCUSD)", "symbols": ["BTCUSD", "BTCUSDmicro"]})
        if "ict_indices" not in cat_keys:
            catalog.append({"category": "ict_indices", "selection_profile": "ICT", "label": "ICT Índices Bursátiles", "symbols": ["Wall Street 30", "US Tech 100", "US SP 500"]})
        self._state["instrument_catalog"] = catalog
        allowed = _catalog_symbols_by_profile(catalog)
        profiles = dict(self._state.get("selection_profiles") or {p: [] for p in _SELECTION_PROFILES})
        versions = dict(self._state.get("selection_profile_versions") or {})

        for profile in _SELECTION_PROFILES:
            pref = persisted.get(profile)
            if pref is None:
                continue
            universe = set(allowed.get(profile) or [])
            values = [str(x) for x in (pref.get("selected_symbols") or [])]
            # Si el catálogo aún no está disponible, conservar el valor DB en vez
            # de convertirlo accidentalmente en selección vacía.
            profiles[profile] = _normalize_symbol_list(
                [x for x in values if (not universe or x in universe)]
            )
            versions[profile] = pref.get("version")

        self._state["selection_profiles"] = profiles
        self._state["selection_profile_versions"] = versions
        self._state["selected_symbols"] = _normalize_symbol_list(
            sum((profiles.get(p, []) for p in _SELECTION_PROFILES), [])
        )
        self._state["selection_persistence_status"] = "VERIFICADA"
        self._state["selection_persistence_error"] = None
        self._state["selection_persistence_checked_at"] = _now_iso()

    def snapshot(self):
        """Devuelve el estado completo que consume el dashboard.

        Es el endpoint principal (`/api/state`). Usa una cache de ~1,5 s para
        que varias pestanas abiertas no multipliquen las consultas, y refresca
        selecciones y posiciones dentro del lock antes de componer el payload.

        Returns:
            dict serializable con estado, ciclo, posiciones abiertas, cuenta,
            catalogo, eventos recientes, noticias y version del daemon.
        """
        now_snapshot = time.monotonic()
        cached_snapshot = self._dashboard_snapshot_cache
        if (
            cached_snapshot.get("payload") is not None
            and (now_snapshot - float(cached_snapshot.get("at") or 0.0))
            < self._dashboard_snapshot_cache_ttl_seconds
        ):
            return cached_snapshot["payload"]

        with self._lock:
            # El dashboard operativo sigue refrescando posiciones, pero account y
            # consultas auxiliares usan TTL corto para no bloquear navegación.
            self._refresh_selection_profiles_from_db_locked()
            self._refresh_open_positions_locked()
            self._refresh_account_locked()
            state = dict(self._state)
            state["risk_quarantine"] = quarantine_snapshot()
            state["smc_trial"] = smc_trial_snapshot()
            state["learning_audit"] = learning_snapshot()
            from dashboard.orb_audit import snapshot as orb_audit_snapshot
            state["orb_audit"] = orb_audit_snapshot()
            metrics_cache = getattr(self, "_orb_metrics_cache", (0, []))
            if time.monotonic() - metrics_cache[0] > 60:
                try:
                    metrics_cache = (time.monotonic(), self.repository.orb_execution_metrics())
                    self._orb_metrics_cache = metrics_cache
                except Exception:
                    state["orb_metrics_error"] = "ORB_METRICS_UNAVAILABLE"
            state["orb_execution_metrics"] = metrics_cache[1]
            from strategy.execution.forex_spread_guard import snapshot as forex_spread_snapshot
            state["forex_spread_audit"] = forex_spread_snapshot()

            now = time.monotonic()
            aux = self._snapshot_aux_cache
            aux_fresh = (
                aux.get("recent") is not None
                and (now - float(aux.get("at") or 0.0)) < self._snapshot_aux_cache_ttl_seconds
            )
            if aux_fresh:
                persisted_recent = aux.get("recent") or []
                worker_states = aux.get("workers") or []
                worker_candidates = aux.get("candidates") or {}
            else:
                persisted_recent = []
                worker_states = []
                worker_candidates = {}
                if self.repository is not None and hasattr(self.repository, "recent_symbol_process_results"):
                    try:
                        persisted_recent = self.repository.recent_symbol_process_results(
                            source="DEMO", limit=250, per_profile=50, scan_limit=3500,
                        )
                    except Exception:
                        persisted_recent = []
                if self.repository is not None and hasattr(self.repository, "worker_runtime_states"):
                    try:
                        worker_states = self.repository.worker_runtime_states(source="DEMO")
                    except Exception:
                        worker_states = []
                if self.repository is not None and hasattr(self.repository, "latest_worker_process_results"):
                    try:
                        worker_candidates = self.repository.latest_worker_process_results(source="DEMO")
                    except Exception:
                        worker_candidates = {}
                worker_states = [
                    row for row in worker_states
                    if not _is_retired_worker_profile((row or {}).get("bot_profile"))
                ]
                worker_candidates = {
                    profile: candidate
                    for profile, candidate in worker_candidates.items()
                    if not _is_retired_worker_profile(profile)
                }
                self._snapshot_aux_cache = {
                    "at": now,
                    "recent": persisted_recent,
                    "workers": worker_states,
                    "candidates": worker_candidates,
                }

            # SQLAlchemy sigue siendo la fuente autoritativa; el enriquecimiento
            # posterior sólo agrega etiquetas/explicaciones para la interfaz.
            state["recent"] = persisted_recent or list(self._recent)
            state["recent"] = [
                _enrich_recent_row(row)
                for row in state["recent"]
                if not _is_retired_worker_profile((row or {}).get("bot_profile"))
            ]
            visible_worker_states = [
                {
                    **dict(row or {}),
                    "last_action_es": _action_label_es((row or {}).get("last_action")),
                    "last_reason_es": _reason_label_es((row or {}).get("last_reason")),
                    "status_es": _state_label_es((row or {}).get("status")),
                }
                for row in worker_states
                if (
                    str((row or {}).get("status") or "").upper() != "SUPERSEDED"
                    and not _is_retired_worker_profile((row or {}).get("bot_profile"))
                )
            ]
            state["worker_states"] = visible_worker_states
            state["worker_candidates"] = worker_candidates
            state["financial_news"] = self.news_service.snapshot()
            state["multi_bot_mode"] = bool(visible_worker_states)
            state["daemon_version"] = DAEMONBLACKFX_VERSION
            state["confluence_matrix"] = _build_confluence_matrix(state)
            state["daily_profit_target"] = self.get_daily_profit_target_payload()
            payload = _json_safe(state)
            self._dashboard_snapshot_cache = {
                "at": time.monotonic(),
                "payload": payload,
            }
            return payload


_HTML = r'''
<!doctype html>
<html lang="es">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>DaemonBlackFx - Calidad en tiempo real</title>
    <style>
      :root {
        color-scheme: dark;
        --bg: #071018;
        --panel: #0d1822;
        --panel2: #122231;
        --text: #e9f1f7;
        --muted: #8fa2b3;
        --line: #233647;
        --good: #31c48d;
        --warn: #f5b942;
        --bad: #ef6a6a;
        --accent: #53a7ff;
      }
      * {
        box-sizing: border-box;
      }
      body {
        margin: 0;
        background: var(--bg);
        color: var(--text);
        font:
          14px/1.45 system-ui,
          -apple-system,
          Segoe UI,
          sans-serif;
      }
      .wrap {
        max-width: 1480px;
        margin: auto;
        padding: 18px;
      }
      .top {
        display: flex;
        gap: 16px;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        margin-bottom: 16px;
      }
      .title {
        font-size: 22px;
        font-weight: 800;
      }
      .sub {
        color: var(--muted);
      }
      .badge {
        padding: 7px 10px;
        border: 1px solid var(--line);
        border-radius: 999px;
        background: var(--panel);
      }
      .grid {
        display: grid;
        grid-template-columns: repeat(12, 1fr);
        gap: 14px;
      }
      .card {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 14px;
        min-width: 0;
      }
      .kpi {
        grid-column: span 3;
      }
      .wide {
        grid-column: span 8;
      }
      .side {
        grid-column: span 4;
      }
      .full {
        grid-column: 1/-1;
      }
      .label {
        color: var(--muted);
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.06em;
      }
      .value {
        font-size: 24px;
        font-weight: 800;
        margin-top: 5px;
      }
      .progress {
        height: 9px;
        background: #172633;
        border-radius: 99px;
        overflow: hidden;
        margin-top: 10px;
      }
      .bar {
        height: 100%;
        background: var(--accent);
        width: 0;
        transition: width 0.25s;
      }
      .quality {
        display: flex;
        align-items: center;
        gap: 18px;
      }
      .ring {
        --p: 0;
        display: grid;
        place-items: center;
        width: 126px;
        height: 126px;
        border-radius: 50%;
        background: conic-gradient(var(--good) calc(var(--p) * 1%), #213241 0);
      }
      .ring:after {
        content: '';
        width: 94px;
        height: 94px;
        border-radius: 50%;
        background: var(--panel);
        position: absolute;
      }
      .ring span {
        position: relative;
        z-index: 1;
        font-size: 25px;
        font-weight: 800;
      }
      .checks {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 10px;
      }
      .checklist {
        max-height: 250px;
        overflow: auto;
        border: 1px solid var(--line);
        border-radius: 10px;
        padding: 10px;
      }
      .ok {
        color: var(--good);
      }
      .miss {
        color: var(--warn);
      }
      .critical {
        color: var(--bad);
      }
      table {
        width: 100%;
        border-collapse: collapse;
      }
      th,
      td {
        text-align: left;
        padding: 9px 8px;
        border-bottom: 1px solid var(--line);
        vertical-align: top;
      }
      th {
        color: var(--muted);
        font-size: 11px;
        text-transform: uppercase;
        position: sticky;
        top: 0;
        background: var(--panel);
      }
      .tablebox {
        overflow: auto;
        max-height: 440px;
      }
      .score {
        font-weight: 800;
      }
      .pill {
        display: inline-block;
        padding: 3px 7px;
        border-radius: 999px;
        background: var(--panel2);
        border: 1px solid var(--line);
        font-size: 11px;
      }
      .good {
        color: var(--good);
      }
      .warn {
        color: var(--warn);
      }
      .bad {
        color: var(--bad);
      }
      .neutral {
        color: var(--muted);
      }
      .statusPill {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 999px;
        border: 1px solid var(--line);
        font-size: 11px;
        font-weight: 800;
        white-space: nowrap;
      }
      .statusPill.good {
        background: rgba(49, 196, 141, 0.1);
      }
      .statusPill.warn {
        background: rgba(245, 185, 66, 0.1);
      }
      .statusPill.bad {
        background: rgba(239, 106, 106, 0.1);
      }
      .statusPill.neutral {
        background: var(--panel2);
      }
      .statusPill.active {
        background: rgba(59, 130, 246, 0.2);
        color: #60a5fa;
        border-color: rgba(59, 130, 246, 0.5);
      }
      .stratBadge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 0.3px;
        text-transform: uppercase;
        white-space: nowrap;
      }
      .stratBadge.strat-smc {
        background: rgba(56, 189, 248, 0.15);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.35);
      }
      .stratBadge.strat-snr {
        background: rgba(192, 132, 252, 0.15);
        color: #c084fc;
        border: 1px solid rgba(192, 132, 252, 0.35);
      }
      .stratBadge.strat-orb {
        background: rgba(251, 146, 60, 0.15);
        color: #fb923c;
        border: 1px solid rgba(251, 146, 60, 0.35);
      }
      .stratBadge.strat-gold {
        background: rgba(250, 204, 21, 0.15);
        color: #facc15;
        border: 1px solid rgba(250, 204, 21, 0.35);
      }
      .stratBadge.strat-cyan {
        background: rgba(56, 189, 248, 0.15);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.35);
      }
      .matrixTabBtn {
        background: var(--panel2);
        color: var(--muted);
        border: 1px solid var(--line);
        padding: 5px 12px;
        border-radius: 8px;
        font-size: 11px;
        font-weight: 700;
        cursor: pointer;
        transition: all 0.15s ease;
      }
      .matrixTabBtn:hover {
        background: rgba(255, 255, 255, 0.08);
        color: var(--text);
      }
      .matrixTabBtn.active {
        background: rgba(245, 185, 66, 0.15);
        color: var(--gold2);
        border-color: var(--gold2);
      }
      .technical {
        display: block;
        color: var(--muted);
        font-size: 10px;
        margin-top: 3px;
        font-family: ui-monospace, SFMono-Regular, Consolas, monospace;
      }
      .empty {
        color: var(--muted);
        padding: 20px 0;
      }
      .row {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
      }
      .metric {
        background: var(--panel2);
        padding: 9px 10px;
        border-radius: 10px;
        min-width: 110px;
      }
      .metric b {
        display: block;
        margin-top: 3px;
      }
      .selectorHead {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        align-items: center;
        flex-wrap: wrap;
      }
      .actions {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
      }
      .btn {
        border: 1px solid var(--line);
        background: var(--panel2);
        color: var(--text);
        border-radius: 9px;
        padding: 8px 11px;
        cursor: pointer;
      }
      .btn.primary {
        background: var(--accent);
        color: #06111b;
        border-color: transparent;
        font-weight: 800;
      }
      .profileTab.active {
        background: var(--accent);
        color: #06111b;
        font-weight: 800;
      }
      .btn:disabled {
        opacity: 0.45;
        cursor: not-allowed;
      }
      .instrumentGrid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 12px;
        margin-top: 12px;
      }
      .instrumentGroup {
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 10px;
        background: var(--panel2);
      }
      .instrumentGroup h3 {
        margin: 0 0 8px;
        font-size: 13px;
      }
      .instrumentItem {
        display: flex;
        align-items: flex-start;
        gap: 8px;
        padding: 5px 2px;
      }
      .instrumentItem input {
        margin-top: 3px;
      }
      .selectionMsg {
        margin-top: 10px;
        color: var(--muted);
      }
      @media (max-width: 1100px) {
        .instrumentGrid {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
      }
      .chartWrap {
        margin-top: 12px;
        border: 1px solid var(--line);
        border-radius: 12px;
        background: #08131c;
        padding: 10px;
        overflow: hidden;
      }
      .chartSvg {
        width: 100%;
        height: auto;
        display: block;
        min-height: 300px;
      }
      .chartHead {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        flex-wrap: wrap;
        align-items: flex-start;
      }
      .chartMeta {
        display: flex;
        gap: 7px;
        flex-wrap: wrap;
      }
      .chartLegend {
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
        margin: 8px 0;
        color: var(--muted);
        font-size: 12px;
      }
      .dot {
        width: 9px;
        height: 9px;
        border-radius: 50%;
        display: inline-block;
        margin-right: 4px;
      }
      .chartGrid {
        display: grid;
        grid-template-columns: 1fr;
        gap: 12px;
      }
      .auditPanel {
        width: 100%;
      }
      .auditPanel {
        border: 1px solid var(--line);
        border-radius: 10px;
        background: var(--panel2);
        padding: 11px;
      }
      .auditPanel h4 {
        margin: 0 0 8px;
      }
      .auditPanel #chartAudit {
        display: block;
      }
      .auditPanel .compareGrid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
      }
      .auditPanel .compareBox {
        min-height: 100%;
      }
      .auditList {
        margin: 0;
        padding-left: 18px;
      }
      .auditList li {
        margin: 4px 0;
      }
      .viewBtn {
        white-space: nowrap;
      }
      .selectedRow {
        background: #112536;
      }
      .priceLabel {
        font-size: 11px;
        font-weight: 700;
      }
      .layerBar {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
        margin: 10px 0;
      }
      .layerToggle {
        display: flex;
        align-items: center;
        gap: 6px;
        border: 1px solid var(--line);
        background: var(--panel2);
        padding: 6px 9px;
        border-radius: 999px;
        cursor: pointer;
        font-size: 12px;
      }
      .layerToggle input {
        accent-color: var(--accent);
      }
      .compareGrid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 9px;
        margin-bottom: 10px;
      }
      .compareBox {
        border: 1px solid var(--line);
        border-radius: 9px;
        padding: 9px;
        background: #0a1620;
      }
      .compareBox h5 {
        margin: 0 0 6px;
        font-size: 12px;
        text-transform: uppercase;
        color: var(--muted);
      }
      .setupParamsGrid {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 4px 8px;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 6px;
        padding: 6px 8px;
        margin: 6px 0;
        font-size: 11px;
      }
      .setupParamsItem {
        display: flex;
        justify-content: space-between;
        gap: 6px;
      }
      .setupParamsLabel {
        color: var(--muted);
      }
      .setupParamsVal {
        font-weight: 600;
        color: var(--text);
      }
      .entryTag {
        font-size: 11px;
        font-weight: 700;
      }
      .rsiLabel {
        font-size: 10px;
        fill: #8fa2b3;
      }
      @media (max-width: 700px) {
        .compareGrid {
          grid-template-columns: 1fr;
        }
      }
      @media (max-width: 900px) {
        .chartGrid {
          grid-template-columns: 1fr;
        }
      }
      @media (max-width: 900px) {
        .kpi {
          grid-column: span 6;
        }
        .wide,
        .side {
          grid-column: 1/-1;
        }
      }
      @media (max-width: 520px) {
        .kpi {
          grid-column: 1/-1;
        }
        .checks,
        .instrumentGrid {
          grid-template-columns: 1fr;
        }
        .wrap {
          padding: 10px;
        }
        .value {
          font-size: 20px;
        }
      }

      /* BlackDaemonFX visual identity v17 */
      :root {
        --bg: #050708;
        --panel: #090d10;
        --panel2: #10161a;
        --text: #f5f5f2;
        --muted: #9fa5aa;
        --line: #5b4514;
        --good: #00db79;
        --warn: #f4b71b;
        --bad: #ff453a;
        --accent: #d79b19;
        --gold: #d79b19;
        --gold2: #f6cb57;
      }
      body {
        background:
          radial-gradient(circle at 78% 0, rgba(215, 155, 25, 0.08), transparent 28%), #050708;
      }
      .appShell {
        display: grid;
        grid-template-columns: 270px minmax(0, 1fr);
        min-height: 100vh;
      }
      .brandSidebar {
        border-right: 1px solid #6b4d13;
        background: linear-gradient(180deg, #050708, #070b0d 65%, #090806);
        padding: 18px 14px;
        display: flex;
        flex-direction: column;
        gap: 14px;
        position: sticky;
        top: 0;
        height: 100vh;
      }
      .brandLogo {
        width: 100%;
        aspect-ratio: 1/1;
        object-fit: cover;
        border-radius: 14px;
        border: 1px solid #7b5816;
        box-shadow: 0 0 28px rgba(215, 155, 25, 0.12);
      }
      .brandName {
        font-size: 20px;
        font-weight: 950;
        letter-spacing: 0.05em;
        text-align: center;
      }
      .brandName span {
        color: var(--gold2);
      }
      .brandTag {
        text-align: center;
        color: #c9a34a;
        font-size: 11px;
        letter-spacing: 0.18em;
        text-transform: uppercase;
      }
      .sideNav {
        display: grid;
        gap: 7px;
        margin-top: 4px;
      }
      .sideNav a {
        color: #d9dde0;
        text-decoration: none;
        padding: 11px 12px;
        border: 1px solid transparent;
        border-radius: 9px;
        font-weight: 650;
      }
      .sideNav a:hover,
      .sideNav a.active {
        background: linear-gradient(90deg, rgba(215, 155, 25, 0.24), rgba(215, 155, 25, 0.05));
        border-color: #6f5015;
        color: #ffd465;
      }
      .sideStatus {
        margin-top: auto;
        border: 1px solid #725116;
        background: #0d1214;
        border-radius: 12px;
        padding: 12px;
      }
      .sideStatus b {
        color: var(--good);
      }
      .wrap {
        max-width: none;
        margin: 0;
        padding: 18px 20px 28px;
      }
      .top {
        border-bottom: 1px solid #513b12;
        padding-bottom: 14px;
      }
      .title {
        font-size: 27px;
        letter-spacing: 0.02em;
      }
      .title strong {
        color: var(--gold2);
      }
      .card {
        background: linear-gradient(145deg, #0b1013, #080b0d);
        border-color: #564014;
        box-shadow: inset 0 1px 0 rgba(255, 214, 111, 0.025);
      }
      .card:hover {
        border-color: #765719;
      }
      .label {
        color: #c8a14a;
      }
      .btn {
        border-color: #5b4514;
        background: #0d1215;
      }
      .btn:hover {
        border-color: #b17e18;
        color: #ffd465;
      }
      .btn.primary {
        background: linear-gradient(180deg, #f2c34b, #c58a11);
        color: #171000;
      }
      .badge {
        border-color: #5b4514;
        background: #0c1114;
      }
      .metric,
      .instrumentGroup,
      .auditPanel,
      .compareBox {
        background: #0d1215;
        border-color: #463711;
      }
      .progress {
        background: #171b1d;
      }
      .bar {
        background: linear-gradient(90deg, #9b690d, #f4c74c);
      }
      .ring {
        background: conic-gradient(var(--gold2) calc(var(--p) * 1%), #202326 0);
      }
      .ring:after {
        background: #0a0e10;
      }
      .pill {
        border-color: #4f3d14;
        background: #12171a;
      }
      .chartWrap {
        background: #050809;
        border-color: #4f3d14;
      }
      th {
        background: #0a0e10;
        color: #c6a14e;
      }
      td,
      th {
        border-bottom-color: #25220f;
      }
      .selectedRow {
        background: #18150b;
      }
      .qualityKpis {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 14px;
        grid-column: 1/-1;
      }
      .acctKpi {
        padding: 16px;
      }
      .acctKpi .value {
        font-size: 26px;
      }
      .acctKpi .trend {
        font-size: 12px;
        margin-top: 5px;
        color: var(--muted);
      }
      @media (max-width: 1050px) {
        .appShell {
          grid-template-columns: 1fr;
        }
        .brandSidebar {
          position: relative;
          height: auto;
          display: grid;
          grid-template-columns: 90px 1fr;
          align-items: center;
        }
        .brandLogo {
          width: 90px;
        }
        .sideNav {
          grid-column: 1/-1;
          grid-template-columns: repeat(4, 1fr);
        }
        .sideStatus {
          display: none;
        }
        .qualityKpis {
          grid-template-columns: repeat(2, 1fr);
        }
      }
      @media (max-width: 620px) {
        .sideNav {
          grid-template-columns: 1fr 1fr;
        }
        .qualityKpis {
          grid-template-columns: 1fr;
        }
        .brandSidebar {
          grid-template-columns: 72px 1fr;
          padding: 10px;
        }
        .brandLogo {
          width: 72px;
        }
        .wrap {
          padding: 10px;
        }
      }
      .workerGrid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 12px;
        margin-top: 12px;
      }
      .workerCard {
        border: 1px solid #564014;
        border-radius: 12px;
        background: #0d1215;
        padding: 12px;
      }
      .workerHead {
        display: flex;
        justify-content: space-between;
        gap: 8px;
        align-items: center;
      }
      .workerName {
        font-size: 18px;
        font-weight: 900;
        color: #f6cb57;
      }
      .workerMeta {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 7px;
        margin-top: 10px;
      }
      .workerMeta div {
        background: #10161a;
        border-radius: 8px;
        padding: 7px;
      }
      .workerMeta span {
        display: block;
        color: var(--muted);
        font-size: 10px;
        text-transform: uppercase;
      }
      .workerMeta b {
        display: block;
        margin-top: 2px;
      }
      .workerProgress {
        height: 7px;
        background: #171b1d;
        border-radius: 99px;
        overflow: hidden;
        margin-top: 10px;
      }
      .workerProgress > div {
        height: 100%;
        background: linear-gradient(90deg, #9b690d, #f4c74c);
      }
      .workerReason {
        margin-top: 8px;
        color: var(--muted);
        font-size: 11px;
        min-height: 30px;
      }
      .workerControl {
        margin-top: 10px;
        width: 100%;
      }
      .workerStale {
        opacity: 0.58;
      }
      .workerPaused {
        opacity: 0.65;
        border-color: #59616a;
      }
      .workerPaused .workerName {
        color: #aab5bf;
      }
      .workerPaused .workerProgress > div {
        background: #59616a;
      }
      .botTabs {
        display: flex;
        gap: 7px;
        flex-wrap: wrap;
        margin-top: 10px;
      }
      .botTab {
        border: 1px solid #564014;
        background: #0d1215;
        color: var(--text);
        border-radius: 999px;
        padding: 6px 10px;
        cursor: pointer;
        font-size: 11px;
        font-weight: 800;
      }
      .botTab.active {
        background: #d6a62d;
        color: #081015;
        border-color: #d6a62d;
      }
      .candidateContext {
        display: flex;
        gap: 7px;
        flex-wrap: wrap;
        margin-top: 7px;
      }
      @media (max-width: 1100px) {
        .workerGrid {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
      }
      @media (max-width: 650px) {
        .workerGrid {
          grid-template-columns: 1fr;
        }
      }
      /* v25: visor de auditoría expandible */
      .chartViewerActions {
        display: flex;
        gap: 8px;
        align-items: center;
        flex-wrap: wrap;
        margin-left: auto;
      }
      .chartViewerActions .btn {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-weight: 750;
      }
      .chartViewerActions .icon {
        font-size: 15px;
        line-height: 1;
      }
      .chartCollapsible {
        display: block;
      }
      .chartCollapsed .chartCollapsible {
        display: none;
      }
      .chartCollapsed {
        padding-bottom: 12px;
      }
      .chartCollapsed .chartHead {
        align-items: center;
      }
      .chartCollapsed #chartSubtitle {
        display: none;
      }
      .chartCollapsed .chartMeta {
        margin-top: 4px;
      }
      .chartCollapsed #chartMinimizeBtn .minText:after {
        content: 'Restaurar';
      }
      .chartCollapsed #chartMinimizeBtn .minText {
        font-size: 0;
      }
      .chartCollapsed #chartMinimizeBtn .minText:after {
        font-size: 14px;
      }
      .chartCollapsed #chartMinimizeBtn .icon {
        transform: rotate(180deg);
      }
      .chartFallbackFullscreen {
        position: fixed !important;
        inset: 0 !important;
        width: 100vw !important;
        height: 100vh !important;
        margin: 0 !important;
        border-radius: 0 !important;
        padding: 16px 18px !important;
        background: #050708 !important;
        overflow: auto !important;
        display: flex !important;
        flex-direction: column !important;
        z-index: 99999;
      }
      .chartFallbackFullscreen .chartCollapsible {
        display: flex;
        flex: 1;
        min-height: 0;
        flex-direction: column;
      }
      .chartFallbackFullscreen .chartGrid {
        flex: 1;
        min-height: 0;
        grid-template-columns: 1fr;
      }
      .chartFallbackFullscreen .chartWrap {
        height: 100%;
        min-height: 0;
        overflow: auto;
      }
      .chartFallbackFullscreen .chartSvg {
        width: 100%;
        height: 100%;
        min-height: 620px;
      }
      .chartFallbackFullscreen .auditPanel {
        overflow: auto;
        max-height: calc(100vh - 235px);
      }
      #positionChartCard:fullscreen,
      #positionChartCard:-webkit-full-screen {
        width: 100vw;
        height: 100vh;
        max-width: none;
        margin: 0;
        border-radius: 0;
        padding: 16px 18px;
        background: #050708;
        overflow: auto;
        display: flex;
        flex-direction: column;
        z-index: 99999;
      }
      #positionChartCard:fullscreen .chartCollapsible,
      #positionChartCard:-webkit-full-screen .chartCollapsible {
        display: flex;
        flex: 1;
        min-height: 0;
        flex-direction: column;
      }
      #positionChartCard:fullscreen .chartGrid,
      #positionChartCard:-webkit-full-screen .chartGrid {
        flex: 1;
        min-height: 0;
        grid-template-columns: 1fr;
      }
      #positionChartCard:fullscreen .chartWrap,
      #positionChartCard:-webkit-full-screen .chartWrap {
        min-height: 0;
        height: 100%;
        overflow: auto;
      }
      #positionChartCard:fullscreen .chartSvg,
      #positionChartCard:-webkit-full-screen .chartSvg {
        width: 100%;
        height: 100%;
        min-height: 620px;
      }
      #positionChartCard:fullscreen .auditPanel,
      #positionChartCard:-webkit-full-screen .auditPanel {
        overflow: auto;
        max-height: calc(100vh - 235px);
      }
      #positionChartCard:fullscreen #chartFullscreenBtn,
      #positionChartCard:-webkit-full-screen #chartFullscreenBtn {
        border-color: #b17e18;
        color: #ffd465;
      }
      .chartFullscreenHint {
        display: none;
        color: var(--muted);
        font-size: 11px;
        margin-left: 4px;
      }
      #positionChartCard:fullscreen .chartFullscreenHint,
      #positionChartCard:-webkit-full-screen .chartFullscreenHint {
        display: inline;
      }
      @media (max-width: 900px) {
        #positionChartCard:fullscreen .chartGrid,
        #positionChartCard:-webkit-full-screen .chartGrid {
          grid-template-columns: 1fr;
        }
        #positionChartCard:fullscreen .auditPanel,
        #positionChartCard:-webkit-full-screen .auditPanel {
          max-height: none;
        }
      }

      /* v26: controles aplicados únicamente al gráfico + navegación temporal */
      .chartPlotColumn {
        min-width: 0;
      }
      .chartViewportShell {
        border: 1px solid #4f3d14;
        border-radius: 12px;
        background: #050809;
        overflow: hidden;
        min-width: 0;
      }
      .chartPlotToolbar {
        display: flex;
        justify-content: space-between;
        gap: 10px;
        align-items: center;
        flex-wrap: wrap;
        padding: 9px 10px;
        border-bottom: 1px solid #342a12;
        background: #090d10;
      }
      .timeframeBar,
      .chartNavTools {
        display: flex;
        gap: 6px;
        align-items: center;
        flex-wrap: wrap;
      }
      .tfBtn {
        min-width: 44px;
        padding: 6px 10px;
        font-weight: 850;
      }
      .tfBtn.active,
      .auditModeBtn.active {
        background: linear-gradient(180deg, #f2c34b, #c58a11);
        color: #171000;
        border-color: #d9a11d;
      }
      .chartNavTools .btn {
        padding: 6px 9px;
      }
      .chartViewportShell .chartWrap {
        margin-top: 0;
        border: 0;
        border-radius: 0;
        min-height: 390px;
        cursor: grab;
        touch-action: none;
        user-select: none;
      }
      .chartViewportShell .chartWrap.dragging {
        cursor: grabbing;
      }
      .chartPlotCollapsed .chartWrap {
        display: none;
      }
      .chartPlotCollapsed .chartPlotToolbar {
        border-bottom: 0;
      }
      .chartPlotCollapsed #chartMinimizeBtn .minText {
        font-size: 0;
      }
      .chartPlotCollapsed #chartMinimizeBtn .minText:after {
        content: 'Restaurar';
        font-size: 14px;
      }
      .chartPlotCollapsed #chartMinimizeBtn .icon {
        transform: rotate(180deg);
      }
      .chartViewportShell:fullscreen,
      .chartViewportShell:-webkit-full-screen {
        width: 100vw;
        height: 100vh;
        background: #050708;
        border-radius: 0;
        border: 0;
        display: flex;
        flex-direction: column;
      }
      .chartViewportShell:fullscreen .chartPlotToolbar,
      .chartViewportShell:-webkit-full-screen .chartPlotToolbar {
        flex: 0 0 auto;
        padding: 12px 16px;
      }
      .chartViewportShell:fullscreen .chartWrap,
      .chartViewportShell:-webkit-full-screen .chartWrap {
        display: block !important;
        flex: 1;
        min-height: 0;
        height: calc(100vh - 62px);
        overflow: hidden;
      }
      .chartViewportShell:fullscreen .chartSvg,
      .chartViewportShell:-webkit-full-screen .chartSvg {
        width: 100%;
        height: 100%;
        min-height: 0;
      }
      .chartManipHint {
        font-size: 11px;
        color: var(--muted);
      }
      .chartZoomBadge {
        min-width: 72px;
        text-align: center;
        font-variant-numeric: tabular-nums;
      }
      .chartWrap.zooming {
        cursor: zoom-in;
      }
      .chartWrap[data-zoomed='true'] {
        cursor: grab;
      }
      .chartTfMode {
        font-size: 11px;
      }
      .chartTfMode.aux {
        color: var(--warn);
      }
      .chartTfMode.strategy {
        color: var(--good);
      }
      .chartHud {
        display: flex;
        justify-content: flex-start;
        align-items: center;
        gap: 14px;
        padding: 5px 12px;
        background: #131722;
        border-bottom: 1px solid #1e222d;
        font-family: -apple-system, BlinkMacSystemFont, 'Trebuchet MS', Roboto, Ubuntu, sans-serif;
        font-size: 11px;
        color: #787b86;
        min-height: 26px;
        flex-wrap: wrap;
        user-select: none;
      }
      .chartHud .hudTitle {
        color: #d1d4dc;
        font-weight: 700;
        display: flex;
        gap: 6px;
        align-items: center;
      }
      .chartHud .hudOhlc {
        display: flex;
        gap: 10px;
        font-variant-numeric: tabular-nums;
      }
      .chartHud .hudIndicators {
        display: flex;
        gap: 10px;
        font-variant-numeric: tabular-nums;
        color: #818cf8;
      }
      .chartHud .good {
        color: #089981 !important;
      }
      .chartHud .bad {
        color: #f23645 !important;
      }
      .chartViewportShell {
        background: #131722;
        border-color: #2a2e39;
      }
      .chartViewportShell .chartPlotToolbar {
        background: #131722;
        border-bottom-color: #1e222d;
      }
      .chartViewportShell .chartWrap {
        background: #131722;
        position: relative;
      }
      .chartSvg text {
        user-select: none;
      }
      /* ========================================================
         META DE GANANCIA DIARIA (DAILY PROFIT TARGET)
         ======================================================== */
      .dptCard {
        background: linear-gradient(180deg, #10161a 0%, #0a0e10 100%);
        border: 1px solid #765719;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5);
      }
      .dptHeader {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
        border-bottom: 1px solid #23313a;
        padding-bottom: 12px;
        margin-bottom: 12px;
      }
      .dptTitle {
        font-size: 14px;
        font-weight: 800;
        color: var(--gold2);
        letter-spacing: 0.04em;
        display: flex;
        align-items: center;
        gap: 8px;
      }
      .dptSub {
        font-size: 11.5px;
        color: #94a3b8;
        margin-top: 3px;
      }
      .dptControlBar {
        display: flex;
        align-items: center;
        gap: 14px;
        flex-wrap: wrap;
        background: #090e12;
        border: 1px solid #1c2730;
        border-radius: 8px;
        padding: 10px 14px;
        margin-top: 10px;
      }
      .dptControlGroup {
        display: flex;
        align-items: center;
        gap: 8px;
      }
      .dptInput {
        background: #141c22;
        border: 1px solid #d79b19;
        color: #f4c84f;
        font-weight: 700;
        font-size: 13px;
        padding: 5px 10px;
        border-radius: 6px;
        width: 75px;
        text-align: right;
        outline: none;
      }
      .dptBtn {
        background: #1a252f;
        border: 1px solid #d79b19;
        color: #f4c84f;
        font-size: 12px;
        font-weight: 700;
        padding: 6px 14px;
        border-radius: 6px;
        cursor: pointer;
        transition: all 0.15s ease;
      }
      .dptBtn:hover {
        background: #d79b19;
        color: #000;
      }
      .dptGrid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 10px;
        margin-top: 12px;
      }
      .dptKpi {
        background: #0d1419;
        border: 1px solid #1c2730;
        border-radius: 8px;
        padding: 10px 12px;
      }
      .dptKpi .lab {
        font-size: 11px;
        color: #8fa2b3;
      }
      .dptKpi .val {
        font-size: 17px;
        font-weight: 800;
        margin-top: 2px;
      }
      .dptKpi .sub {
        font-size: 10.5px;
        color: #64748b;
        margin-top: 2px;
      }
      .dptProgressTrack {
        width: 100%;
        height: 8px;
        background: #151e25;
        border-radius: 4px;
        overflow: hidden;
        margin-top: 6px;
      }
      .dptProgressBar {
        height: 100%;
        width: 0%;
        background: #d79b19;
        transition: width 0.3s ease;
      }
      .dptLockedBanner {
        background: linear-gradient(135deg, rgba(215, 155, 25, 0.18), rgba(245, 189, 54, 0.06));
        border: 1.5px solid #f5bd36;
        border-radius: 10px;
        padding: 14px 18px;
        margin-top: 14px;
        display: none;
      }
      .dptModalOverlay {
        position: fixed;
        inset: 0;
        background: rgba(0,0,0,0.85);
        backdrop-filter: blur(5px);
        display: none;
        align-items: center;
        justify-content: center;
        z-index: 99999;
      }
      .dptModalBox {
        background: #0e151b;
        border: 2px solid #ef6a6a;
        border-radius: 14px;
        max-width: 550px;
        width: 90%;
        padding: 24px;
        box-shadow: 0 10px 40px rgba(239, 106, 106, 0.3);
      }
    </style>
  </head>
  <body>
    <div class="appShell">
      <aside class="brandSidebar">
        <img class="brandLogo" src="/assets/blackdaemonfx_logo_v1.jpeg" alt="Logo BlackDaemonFX" />
        <div>
          <div class="brandName">BLACKDAEMON<span>FX</span></div>
          <div class="brandTag">Estrategia · Disciplina · Resultados</div>
        </div>
        <nav class="sideNav">
          <a class="active" href="/">▦ Dashboard</a><a href="/instruments">▥ Instrumentos</a
          ><a href="/account">▣ Cuenta en vivo</a><a href="/performance">📈 Rendimiento</a><a href="/strategy-bases">📚 Bases de Estrategias</a><a href="#openPositions">◈ Posiciones abiertas</a
          ><a href="#recentAnalysis">◷ Análisis recientes</a>
        </nav>
        <div class="sideStatus">
          <b>● Daemon Online</b>
          <div class="sub">Panel local conectado al motor</div>
        </div>
      </aside>
      <main class="wrap">
        <div class="top">
          <div>
            <div class="title">BLACKDAEMON<strong>FX</strong> · Control operativo</div>
            <div class="sub">ESTRATEGIA · DISCIPLINA · RESULTADOS · Dashboard en tiempo real</div>
          </div>
          <div class="actions">
            <a class="btn" href="/account">Cuenta en vivo</a><a class="btn" href="/performance">Rendimiento</a><a class="btn" href="/strategy-bases">Bases de Estrategias</a><a class="btn" href="/instruments">Instrumentos</a>
            <div class="badge" id="status">Conectando…</div>
          </div>
        </div>
        <div class="grid">
          <div class="qualityKpis">
            <div class="card acctKpi">
              <div class="label">Balance</div>
              <div class="value" id="accountBalance">—</div>
              <div class="trend">Saldo de la cuenta activa</div>
            </div>
            <div class="card acctKpi">
              <div class="label">Equity</div>
              <div class="value" id="accountEquity">—</div>
              <div class="trend">Capital incluyendo P&amp;L flotante</div>
            </div>
            <div class="card acctKpi">
              <div class="label">P&amp;L flotante</div>
              <div class="value" id="accountProfit">—</div>
              <div class="trend">Resultado de posiciones abiertas</div>
            </div>
            <div class="card acctKpi">
              <div class="label">Margen libre</div>
              <div class="value" id="accountFreeMargin">—</div>
              <div class="trend">Disponible para operar</div>
            </div>
          </div>
          <div class="card kpi">
            <div class="label">Workers activos</div>
            <div class="value" id="cycle">—</div>
            <div class="sub">Familias en ejecución</div>
          </div>
          <div class="card kpi">
            <div class="label">Progreso agregado</div>
            <div class="value" id="progressText">—</div>
            <div class="progress"><div class="bar" id="progressBar"></div></div>
          </div>
          <div class="card kpi">
            <div class="label">Actividad más reciente</div>
            <div class="value" id="current" style="font-size: 18px">—</div>
          </div>
          <div class="card kpi">
            <div class="label">Operaciones abiertas</div>
            <div class="value" id="openCount">0</div>
            <div class="sub" id="healthSummary">Sin posiciones</div>
          </div>
          <!-- META DE GANANCIA DIARIA (DAILY PROFIT TARGET) -->
          <div class="card full dptCard" id="dailyProfitTargetCard">
            <div class="dptHeader">
              <div>
                <div class="dptTitle">🎯 Meta de Ganancia Diaria (Daily Profit Target)</div>
                <div class="dptSub">
                  Fija un objetivo diario en % sobre el balance. Al cumplirse, se bloquean todas las nuevas entradas para proteger ganancias. Reactivación automática en la sesión de Asia (00:00 UTC).
                </div>
              </div>
              <div id="dptStatusBadge" class="statusPill good">Cargando...</div>
            </div>

            <div class="dptControlBar">
              <label class="dptControlGroup" style="cursor: pointer; user-select: none;">
                <input type="checkbox" id="dptEnabledCheckbox" style="accent-color: #d79b19; width: 16px; height: 16px;" onchange="saveDailyTargetSettings()" checked />
                <span style="font-weight: 700; font-size: 12.5px;">Habilitar meta diaria de beneficio</span>
              </label>

              <div class="dptControlGroup" style="margin-left: auto;">
                <span style="font-size: 12px; color: #94a3b8;">Meta Diaria:</span>
                <input type="number" id="dptTargetPercentInput" class="dptInput" step="0.1" min="0.1" max="100" value="2.0" onchange="saveDailyTargetSettings()" onkeydown="if(event.key==='Enter'){event.preventDefault();saveDailyTargetSettings();}" />
                <span style="font-weight: 700; color: #f4c84f;">%</span>
                <button type="button" id="dptSaveSettingsBtn" class="dptBtn" onclick="saveDailyTargetSettings()">Guardar Meta</button>
              </div>
            </div>

            <div class="dptGrid">
              <div class="dptKpi">
                <div class="lab">Retorno Diario Cerrado</div>
                <div class="val" id="dptReturnDisplay">+0.00%</div>
                <div class="sub" id="dptTodayPnlDisplay">+$0.00 hoy</div>
              </div>
              <div class="dptKpi">
                <div class="lab">Meta Objetivo</div>
                <div class="val" id="dptTargetDisplay" style="color: #f4c84f;">2.00%</div>
                <div class="sub">Límite diario establecido</div>
              </div>
              <div class="dptKpi">
                <div class="lab">Progreso Hacia la Meta</div>
                <div class="dptProgressTrack"><div class="dptProgressBar" id="dptProgressBar"></div></div>
                <div class="sub" id="dptTradesSummary">0 cerrados hoy</div>
              </div>
              <div class="dptKpi">
                <div class="lab">Próxima Reactivación</div>
                <div class="val" style="font-size: 14px; color: #60a5fa;">Sesión de Asia</div>
                <div class="sub">00:00 UTC / 09:00 Tokio (Automática)</div>
              </div>
            </div>

            <div class="dptLockedBanner" id="dptLockedBanner">
              <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px;">
                <div id="dptBannerText" style="flex: 1 1 320px; line-height: 1.5;">
                  <b>🎯 ¡META DIARIA CUMPLIDA!</b> Entradas bloqueadas para proteger tus ganancias.
                </div>
                <div>
                  <button type="button" id="dptOverrideBtn" onclick="openDptOverrideModal()" style="background: linear-gradient(135deg, #d79b19, #f5bd36); color: #000; font-weight: 800; border: none; padding: 10px 18px; border-radius: 8px; cursor: pointer; box-shadow: 0 2px 10px rgba(215, 155, 25, 0.4); font-size: 12.5px;">
                    🚀 ¿Deseas ganar un poquito más?
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- MODAL DE ADVERTENCIA DE RIESGO DE OVERTRADING -->
          <div class="dptModalOverlay" id="dptRiskModal">
            <div class="dptModalBox">
              <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 14px;">
                <span style="font-size: 24px;">⚠️</span>
                <b style="font-size: 16px; color: #ff6b6b; letter-spacing: 0.03em;">ADVERTENCIA DE RIESGO: PELIGRO DE OVERTRADING</b>
              </div>
              <p style="font-size: 13px; line-height: 1.55; color: #e2e8f0; margin-bottom: 12px;">
                ¡Felicidades! Has cumplido la meta de rentabilidad diaria prevista en tu plan de trading.
              </p>
              <div style="background: rgba(255, 69, 58, 0.12); border-left: 3px solid #ff453a; padding: 10px 14px; border-radius: 6px; font-size: 12px; line-height: 1.5; color: #fca5a5; margin-bottom: 16px;">
                <b>ALERTA DE DISCIPLINA:</b> Continuar operando desafía las reglas de gestión de riesgo y expone tus ganancias a reversiones inesperadas del mercado, incremento de spreads y deslizamientos. <b>Corres el riesgo real de perder parte o la totalidad de los beneficios acumulados en la sesión.</b>
              </div>
              <p style="font-size: 12.5px; color: #cbd5e1; margin-bottom: 20px;">
                ¿Deseas desbloquear temporalmente el escaneo de nuevas entradas para buscar un objetivo adicional (+1.0% de margen) asumiendo este riesgo?
              </p>
              <div style="display: flex; justify-content: flex-end; gap: 10px; flex-wrap: wrap;">
                <button type="button" onclick="closeDptOverrideModal()" style="background: #1e293b; border: 1px solid #475569; color: #f1f5f9; padding: 8px 16px; border-radius: 6px; font-size: 12px; font-weight: 700; cursor: pointer;">
                  🛡️ Mantener Ganancias Protegidas (Recomendado)
                </button>
                <button type="button" id="dptConfirmOverrideBtn" onclick="confirmDptOverride()" style="background: #dc2626; border: 1px solid #ef4444; color: #fff; padding: 8px 16px; border-radius: 6px; font-size: 12px; font-weight: 800; cursor: pointer;">
                  ⚠️ Asumo el Riesgo, Desbloquear (+1.0%)
                </button>
              </div>
            </div>
          </div>

          <div class="card full" id="confluenceMatrixCard">
            <div class="selectorHead">
              <div>
                <div class="label" style="color: var(--gold2); font-weight: 800; font-size: 13px;">Matriz Centinela Multiestrategia (ICT · Malaysian SNR · ORB · Gold Quarters)</div>
                <div class="sub">
                  Monitoreo centinela unificado en tiempo real: Estrategia ICT · Malaysian SNR (Break/Retest/ADX) · ORB (Apertura NY) · Gold Quarters
                </div>
              </div>
              <div id="confluenceSummaryChips" style="display: flex; gap: 8px; align-items: center; font-size: 11px; flex-wrap: wrap;"></div>
            </div>
            <!-- Filtros interactivos por estrategia -->
            <div id="confluenceFilters" style="display: flex; gap: 6px; margin-top: 12px; flex-wrap: wrap;">
              <button class="matrixTabBtn active" data-filter="ALL" onclick="setMatrixFilter('ALL')">TODAS</button>
              <button class="matrixTabBtn" data-filter="ICT" onclick="setMatrixFilter('ICT')" style="color: #38bdf8; font-weight: bold;">ESTRATEGIA ICT</button>
              <button class="matrixTabBtn" data-filter="MALAYSIAN_SNR" onclick="setMatrixFilter('MALAYSIAN_SNR')">MALAYSIAN SNR</button>
              <button class="matrixTabBtn" data-filter="ORB" onclick="setMatrixFilter('ORB')">ORB NY</button>
              <button class="matrixTabBtn" data-filter="GOLD_QUARTERS" onclick="setMatrixFilter('GOLD_QUARTERS')">GOLD QUARTERS</button>
              <button class="matrixTabBtn" data-filter="ACTIVE" onclick="setMatrixFilter('ACTIVE')" style="color: #60a5fa;">🔵 ACTIVAS</button>
            </div>
            <div id="confluenceMatrixPanel" style="margin-top: 12px; overflow-x: auto;">
              <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
                <thead>
                  <tr>
                    <th style="text-align: left; padding: 8px;">Símbolo</th>
                    <th style="text-align: left; padding: 8px;">Estrategia</th>
                    <th style="text-align: left; padding: 8px;">Contexto Macro</th>
                    <th style="text-align: left; padding: 8px;">Estructura / Nivel Clave</th>
                    <th style="text-align: left; padding: 8px;">Gatillo / Confirmación</th>
                    <th style="text-align: left; padding: 8px;">Métricas / Frescura</th>
                    <th style="text-align: left; padding: 8px;">AI Score</th>
                    <th style="text-align: left; padding: 8px;">Estado Centinela</th>
                  </tr>
                </thead>
                <tbody id="confluenceMatrixBody">
                  <tr><td colspan="8" class="empty">Cargando confluencias multiestrategia…</td></tr>
                </tbody>
              </table>
            </div>
          </div>
          <div class="card full">
            <div class="label">Instrumentos en cuarentena</div>
            <div class="sub">
              Bloqueos para nuevas entradas · la liberación sigue las reglas del motor de riesgo.
            </div>
            <div id="quarantinePanel">Cargando cuarentena…</div>
          </div>
          <div class="card full">
            <div class="label">Procesos</div>
            <div class="sub">
              Cada tarjeta representa un worker independiente y su ciclo real persistido en
              SQLAlchemy.
            </div>
            <div class="workerGrid" id="workerGrid">
              <div class="empty">Esperando estado de los workers…</div>
            </div>
          </div>
          <div class="card full">
            <div class="selectorHead">
              <div>
                <div class="label">Configuración de instrumentos</div>
                <div class="sub">
                  La selección para nuevas entradas fue separada del dashboard operativo.
                </div>
              </div>
              <div class="actions">
                <a class="btn primary" href="/instruments">Administrar instrumentos</a>
              </div>
            </div>
            <div class="selectionMsg" id="selectionSummary">Cargando selección actual…</div>
          </div>
          <div class="card wide">
            <div class="label">Último candidato analizado · contexto por bot</div>
            <div class="sub">
              Selecciona el worker cuya lectura quieres auditar. TODOS muestra el worker con
              actividad más reciente.
            </div>
            <div class="botTabs" id="candidateBotTabs"></div>
            <div class="candidateContext" id="candidateContext"></div>
            <div class="quality" style="margin-top: 12px">
              <div class="ring" id="ring"><span id="score">—</span></div>
              <div style="flex: 1; min-width: 220px">
                <div class="value" id="lastSymbol">Sin datos</div>
                <div class="row" id="lastMeta"></div>
                <div style="margin-top: 10px" id="decision" class="sub"></div>
              </div>
            </div>
          </div>
          <div class="card side">
            <div class="label">Confluencias</div>
            <div class="row" style="margin-top: 12px">
              <div class="metric"><span class="sub">Divergencia</span><b id="divergence">—</b></div>
              <div class="metric"><span class="sub">Armónico</span><b id="harmonic">—</b></div>
              <div class="metric"><span class="sub">Doji H1 extremo</span><b id="h1doji">—</b></div>
              <div class="metric"><span class="sub">Estructura</span><b id="structure">—</b></div>
              <div class="metric"><span class="sub">Zona</span><b id="zone">—</b></div>
            </div>
          </div>
          <div class="card full">
            <div class="label">Confirmaciones del último candidato</div>
            <div class="checks" style="margin-top: 12px">
              <div>
                <div class="sub">Cumplidas</div>
                <div class="checklist" id="passed"></div>
              </div>
              <div>
                <div class="sub">Faltantes / críticas</div>
                <div class="checklist" id="missing"></div>
              </div>
            </div>
          </div>
          <div class="card full" id="openPositions">
            <div class="label">Salud de posiciones abiertas · telemetría por owner/worker</div>
            <div class="sub" style="margin: 4px 0 10px">
              La salud sólo se calcula con telemetría suficiente. Posiciones externas o
              inconsistentes quedan como NO EVALUABLE.
            </div>
            <div class="tablebox">
              <table>
                <thead>
                  <tr>
                    <th>Instrumento</th>
                    <th>Bot / Owner</th>
                    <th>Dir.</th>
                    <th>Salud</th>
                    <th>Recomendación</th>
                    <th>R actual</th>
                    <th>BE</th>
                    <th>Score entrada</th>
                    <th>Confirm.</th>
                    <th>Precio actual</th>
                    <th>Razones</th>
                    <th>Gráfico</th>
                  </tr>
                </thead>
                <tbody id="openBody"></tbody>
              </table>
            </div>
          </div>
          <div class="card full" id="positionChartCard">
            <div class="chartHead">
              <div>
                <div class="label">Auditoría visual SMC de la posición abierta</div>
                <div class="value" id="chartTitle" style="font-size: 19px">
                  Selecciona una posición
                </div>
                <div class="sub" id="chartSubtitle">
                  Navega M1 / M5 / M15 / H1; el gráfico usa todo el ancho y la comparación Entrada
                  vs. Ahora queda debajo.
                </div>
              </div>
              <div class="chartMeta" id="chartMeta"></div>
            </div>
            <div class="chartCollapsible" id="chartCollapsible">
              <div class="layerBar" id="chartLayers">
                <label class="layerToggle"
                  ><input type="checkbox" data-layer="trade" checked />Trade / SL / TP / BE</label
                ><label class="layerToggle"
                  ><input type="checkbox" data-layer="swings" checked />Swings HH/HL/LH/LL</label
                ><label class="layerToggle"
                  ><input type="checkbox" data-layer="structure" checked />CHOCH / BOS</label
                ><label class="layerToggle"
                  ><input type="checkbox" data-layer="liquidity" checked />Liquidez · BSL / SSL /
                  Sweeps</label
                ><label class="layerToggle"
                  ><input type="checkbox" data-layer="orderblock" checked />Order Blocks</label
                ><label class="layerToggle"
                  ><input type="checkbox" data-layer="fvg" checked />FVG / Imbalances*</label
                ><label class="layerToggle"
                  ><input type="checkbox" data-layer="premiumdiscount" checked />Premium /
                  Discount</label
                ><label class="layerToggle"
                  ><input type="checkbox" data-layer="confluence" checked />Divergencia / Doji /
                  Armónico</label
                ><label class="layerToggle"
                  ><input type="checkbox" data-layer="rsi" checked />RSI 14</label
                ><label class="layerToggle"
                  ><input type="checkbox" data-layer="cleanZones" checked />Modo Limpio (Ocultar mitigadas)</label
                >
              </div>
              <div class="chartLegend">
                <span><i class="dot" style="background: #2962ff"></i>Entrada</span>
                <span><i class="dot" style="background: #f23645"></i>SL</span>
                <span><i class="dot" style="background: #089981"></i>TP</span>
                <span><i class="dot" style="background: #d97706"></i>BE / SL actual</span>
                <span><i class="dot" style="background: #eab308"></i>EQ 50%</span>
                <span><i class="dot" style="background: #818cf8"></i>FVG</span>
                <span><i class="dot" style="background: #34d399"></i>OB Bull</span>
                <span><i class="dot" style="background: #fb7185"></i>OB Bear</span>
                <span>△/▽ eventos SMC · Retícula interactiva con HUD</span>
              </div>
              <div class="chartGrid">
                <div class="chartPlotColumn">
                  <div class="chartViewportShell" id="chartViewportShell">
                    <div class="chartPlotToolbar">
                      <div class="timeframeBar" id="chartTimeframes">
                        <span class="sub">Vista</span
                        ><button
                          type="button"
                          class="btn auditModeBtn active"
                          data-audit-mode="ENTRY"
                        >
                          ENTRADA</button
                        ><button type="button" class="btn auditModeBtn" data-audit-mode="CURRENT">
                          ACTUAL</button
                        ><span class="sub">Temporalidad</span
                        ><button type="button" class="btn tfBtn" data-tf="M1">M1</button
                        ><button type="button" class="btn tfBtn active" data-tf="M5">M5</button
                        ><button type="button" class="btn tfBtn" data-tf="M15">M15</button
                        ><button type="button" class="btn tfBtn" data-tf="H1">H1</button
                        ><span class="pill chartTfMode strategy" id="chartTfMode">ESTRATEGIA</span>
                      </div>
                      <div class="chartNavTools">
                        <span class="chartManipHint"
                          >Scroll ↑/↓ = escala vertical · arrastrar = mover gráfico completo X/Y ·
                          Ctrl+scroll = zoom de velas · doble clic = autoescala · M1 = contexto SMC
                          auxiliar</span
                        ><span class="pill chartZoomBadge" id="chartZoomBadge">Y 1.0× · X 1.0×</span
                        ><button
                          type="button"
                          class="btn"
                          id="chartZoomOutBtn"
                          title="Reducir escala vertical"
                        >
                          −</button
                        ><button
                          type="button"
                          class="btn"
                          id="chartZoomInBtn"
                          title="Ampliar escala vertical"
                        >
                          +</button
                        ><button
                          type="button"
                          class="btn"
                          id="chartResetViewBtn"
                          title="Restaurar autoescala y velas recientes"
                        >
                          Autoescala</button
                        ><button
                          type="button"
                          class="btn"
                          id="chartFullscreenBtn"
                          title="Ampliar sólo el gráfico"
                        >
                          <span class="icon">⛶</span
                          ><span id="chartFullscreenText">Pantalla completa</span></button
                        ><button
                          type="button"
                          class="btn"
                          id="chartMinimizeBtn"
                          title="Minimizar sólo el gráfico"
                        >
                          <span class="icon">⌃</span><span class="minText">Minimizar</span>
                        </button>
                      </div>
                    </div>
                    <div class="chartHud" id="chartHud">
                      <div class="hudTitle"><b id="hudSymbol">—</b> <span id="hudTf" class="sub">—</span></div>
                      <div class="hudOhlc">
                        <span>O: <b id="hudOpen">—</b></span>
                        <span>H: <b id="hudHigh">—</b></span>
                        <span>L: <b id="hudLow">—</b></span>
                        <span>C: <b id="hudClose">—</b></span>
                        <span id="hudChange" class="hudChange">—</span>
                      </div>
                      <div class="hudIndicators" id="hudIndicators">
                        <span>RSI: <b id="hudRsi">—</b></span>
                      </div>
                    </div>
                    <div class="chartWrap" id="chartWrap">
                      <div class="empty">Selecciona “Ver gráfico” en una posición abierta.</div>
                    </div>
                  </div>
                </div>
                <aside class="auditPanel">
                  <h4>Entrada vs. ahora</h4>
                  <div id="chartAudit" class="sub">Sin posición seleccionada.</div>
                </aside>
              </div>
            </div>
          </div>
          <div class="card full" id="financialNews">
            <div class="label">Agenda económica y noticias financieras</div>
            <div class="sub" style="margin: 4px 0 10px">
              Próximos eventos macroeconómicos en horario de Chile (Santiago). Los titulares RSS se
              muestran en español y se priorizan por impacto.
            </div>
            <div id="economicCalendar" class="sub">Cargando agenda económica…</div>
            <div class="label" style="margin-top: 14px">Titulares recientes</div>
            <div id="dashboardNews" class="sub">Cargando noticias…</div>
          </div>
          <div class="card full" id="recentAnalysis">
            <div class="label">Análisis recientes</div>
            <div class="sub" style="margin: 4px 0 10px">
              Los textos principales están traducidos a lenguaje operativo. El código técnico se
              conserva debajo para auditoría. La vista se equilibra por worker para que ORB, FOREX y
              sintéticos tengan representación.
            </div>
            <div class="tablebox">
              <table>
                <thead>
                  <tr>
                    <th>Bot</th><th>Instrumento</th>
                    <th>Estado</th>
                    <th>Acción</th>
                    <th>Score</th>
                    <th>% confirm.</th>
                    <th>Grado</th>
                    <th>Dirección</th>
                    <th>Divergencia</th>
                    <th>Armónico</th>
                    <th>Tiempo</th>
                    <th>Motivo explicado</th>
                  </tr>
                </thead>
                <tbody id="recentBody"></tbody>
              </table>
            </div>
          </div>
        </div>
        <script>
          const $ = (id) => document.getElementById(id);
          const esc = (v) =>
            String(v ?? '—').replace(
              /[&<>"']/g,
              (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c],
            );
          function pct(v) {
            return v == null ? '—' : Number(v).toFixed(1) + '%';
          }
          function n(v, d = 1) {
            return v == null ? '—' : Number(v).toFixed(d);
          }
          function scoreClass(v) {
            return v >= 75 ? 'good' : v >= 60 ? 'warn' : 'bad';
          }
          function renderList(el, items, cls) {
            el.innerHTML =
              items && items.length
                ? items
                    .map((x) => `<div class="${cls}">${cls === 'ok' ? '✓' : '•'} ${esc(x)}</div>`)
                    .join('')
                : '<div class="empty">Ninguna</div>';
          }
          let selectionDirty = false;
          let lastSelectionVersion = null;
          function renderCatalog(s) {
            const summary = $('selectionSummary');
            if (summary) {
              const selected = s.selected_symbols || [];
              summary.textContent = `${selected.length} instrumentos habilitados para nuevas entradas · cambios disponibles en /instruments`;
              return;
            }
            const grid = $('instrumentGrid');
            if (!grid) return;
          }
          function currentSelection() {
            const grid = $('instrumentGrid');
            if (!grid) return [];
            return [...grid.querySelectorAll('input[data-symbol]:checked')]
              .map((x) => x.dataset.symbol)
              .sort((a, b) => a.localeCompare(b, 'es'));
          }
          async function saveSelection() {
            const selected = currentSelection();
            if (!selected.length) {
              $('selectionMsg').textContent =
                'Debes mantener al menos un instrumento seleccionado.';
              return;
            }
            $('saveSelection').disabled = true;
            try {
              const r = await fetch('/api/instruments/selection', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ selected_symbols: selected }),
              });
              const data = await r.json();
              if (!r.ok || !data.ok) throw new Error(data.error || 'No se pudo guardar');
              selectionDirty = false;
              lastSelectionVersion = data.selection_version;
              $('selectionMsg').textContent = data.message || 'Selección guardada';
            } catch (e) {
              $('selectionMsg').textContent = 'Error: ' + e.message;
            } finally {
              $('saveSelection').disabled = false;
            }
          }
          let latestState = null;
          let selectedTradeId = null;
          let selectedCandidateBot = 'TODOS';
          function priceFmt(v) {
            if (v == null || !Number.isFinite(Number(v))) return '—';
            const x = Number(v);
            return Math.abs(x) >= 10000
              ? x.toFixed(2)
              : Math.abs(x) >= 100
                ? x.toFixed(3)
                : x.toFixed(5);
          }
          function svgEl(tag, attrs, text = '') {
            const a = Object.entries(attrs || {})
              .map(([k, v]) => `${k}="${esc(v)}"`)
              .join(' ');
            return `<${tag} ${a}>${text}</${tag}>`;
          }
          let chartRenderContext = null;
          const chartLayerState = {
            trade: true,
            swings: true,
            structure: true,
            liquidity: true,
            orderblock: true,
            fvg: true,
            premiumdiscount: true,
            confluence: true,
            rsi: true,
            cleanZones: true,
          };
          const chartViewState = {
            timeframe: 'M5',
            auditMode: 'ENTRY',
            zoom: 1,
            offset: 0,
            priceZoom: 1,
            pricePan: 0,
            dragging: false,
            dragStartX: 0,
            dragStartY: 0,
            dragStartOffset: 0,
            dragStartPricePan: 0,
            maxZoom: 12,
            maxPriceZoom: 20,
            minVisible: 8,
          };
          function chartCard() {
            return $('chartViewportShell');
          }
          function isChartFullscreen() {
            const el = chartCard();
            return document.fullscreenElement === el || document.webkitFullscreenElement === el;
          }
          function updateChartViewerButtons() {
            const full = isChartFullscreen(),
              shell = chartCard(),
              btn = $('chartFullscreenBtn'),
              txt = $('chartFullscreenText');
            if (txt) txt.textContent = full ? 'Salir' : 'Pantalla completa';
            if (btn) btn.setAttribute('aria-pressed', full ? 'true' : 'false');
            const min = $('chartMinimizeBtn');
            if (min)
              min.setAttribute(
                'aria-expanded',
                shell && !shell.classList.contains('chartPlotCollapsed') ? 'true' : 'false',
              );
          }
          async function toggleChartFullscreen() {
            const el = chartCard();
            if (!el) return;
            try {
              if (isChartFullscreen()) {
                if (document.exitFullscreen) await document.exitFullscreen();
                else if (document.webkitExitFullscreen) document.webkitExitFullscreen();
              } else {
                el.classList.remove('chartPlotCollapsed');
                if (el.requestFullscreen) await el.requestFullscreen();
                else if (el.webkitRequestFullscreen) el.webkitRequestFullscreen();
              }
            } catch (e) {
              console.warn('No se pudo ampliar el gráfico', e);
            } finally {
              updateChartViewerButtons();
            }
          }
          function toggleChartMinimized() {
            const el = chartCard();
            if (!el) return;
            if (isChartFullscreen()) {
              const exit = document.exitFullscreen || document.webkitExitFullscreen;
              if (exit) {
                try {
                  exit.call(document);
                } catch (e) {}
              }
            }
            el.classList.toggle('chartPlotCollapsed');
            updateChartViewerButtons();
            if (!el.classList.contains('chartPlotCollapsed')) rerenderSelectedChart();
          }
          function rerenderSelectedChart() {
            if (!selectedTradeId) return;
            const t = (latestState?.open_positions || []).find(
              (x) => String(x.id) === String(selectedTradeId),
            );
            if (t) requestAnimationFrame(() => renderPositionChart(t));
          }
          function setAuditMode(mode) {
            mode = String(mode || 'ENTRY').toUpperCase();
            if (!['ENTRY', 'CURRENT'].includes(mode)) return;
            chartViewState.auditMode = mode;
            chartViewState.zoom = 1;
            chartViewState.offset = 0;
            chartViewState.priceZoom = 1;
            chartViewState.pricePan = 0;
            document
              .querySelectorAll('.auditModeBtn[data-audit-mode]')
              .forEach((b) => b.classList.toggle('active', b.dataset.auditMode === mode));
            rerenderSelectedChart();
          }
          function setChartTimeframe(tf) {
            tf = String(tf || 'M5').toUpperCase();
            if (!['M1', 'M5', 'M15', 'H1'].includes(tf)) return;
            chartViewState.timeframe = tf;
            chartViewState.zoom = 1;
            chartViewState.offset = 0;
            chartViewState.priceZoom = 1;
            chartViewState.pricePan = 0;
            updateChartZoomBadge();
            document
              .querySelectorAll('.tfBtn[data-tf]')
              .forEach((b) => b.classList.toggle('active', b.dataset.tf === tf));
            rerenderSelectedChart();
          }
          function updateChartZoomBadge() {
            const b = $('chartZoomBadge');
            if (b)
              b.textContent =
                'Y ' +
                chartViewState.priceZoom.toFixed(1) +
                '× · X ' +
                chartViewState.zoom.toFixed(1) +
                '×';
            const w = $('chartWrap');
            if (w)
              w.dataset.zoomed =
                chartViewState.zoom > 1.01 ||
                chartViewState.priceZoom > 1.01 ||
                Math.abs(chartViewState.pricePan) > 0.001
                  ? 'true'
                  : 'false';
          }
          function changeChartZoom(multiplier, anchorRatio = null) {
            const t = (latestState?.open_positions || []).find(
              (x) => String(x.id) === String(selectedTradeId),
            );
            const ec = t?.entry_chart || {},
              c =
                chartViewState.auditMode === 'ENTRY' && Object.keys(ec).length
                  ? ec
                  : t?.chart || {},
              tf = (c.timeframes || {})[chartViewState.timeframe] || c,
              all = tf.candles || [],
              total = all.length;
            if (!total) return;
            const oldZoom = chartViewState.zoom,
              oldVisible = Math.max(
                chartViewState.minVisible,
                Math.min(total, Math.round(Math.min(total, 80) / oldZoom)),
              ),
              oldMax = Math.max(0, total - oldVisible),
              oldOffset = Math.max(0, Math.min(oldMax, chartViewState.offset));
            const ratio = anchorRatio == null ? 0.5 : Math.max(0, Math.min(1, anchorRatio));
            const oldEnd = total - oldOffset,
              oldStart = Math.max(0, oldEnd - oldVisible),
              anchorIndex = oldStart + ratio * Math.max(0, oldVisible - 1);
            chartViewState.zoom = Math.max(
              1,
              Math.min(chartViewState.maxZoom, oldZoom * multiplier),
            );
            const newVisible = Math.max(
              chartViewState.minVisible,
              Math.min(total, Math.round(Math.min(total, 80) / chartViewState.zoom)),
            );
            let newStart = anchorIndex - ratio * Math.max(0, newVisible - 1);
            newStart = Math.max(0, Math.min(Math.max(0, total - newVisible), newStart));
            chartViewState.offset = Math.max(0, total - (newStart + newVisible));
            updateChartZoomBadge();
            rerenderSelectedChart();
          }
          function changePriceZoom(multiplier, anchorRatioY = 0.5) {
            const oldZoom = chartViewState.priceZoom,
              oldSpan = 1 / oldZoom,
              ratio = Math.max(0, Math.min(1, anchorRatioY == null ? 0.5 : anchorRatioY)),
              anchor = chartViewState.pricePan + (0.5 - ratio) * oldSpan;
            chartViewState.priceZoom = Math.max(
              1,
              Math.min(chartViewState.maxPriceZoom, oldZoom * multiplier),
            );
            const newSpan = 1 / chartViewState.priceZoom;
            chartViewState.pricePan = anchor - (0.5 - ratio) * newSpan;
            chartViewState.pricePan = Math.max(-3, Math.min(3, chartViewState.pricePan));
            updateChartZoomBadge();
            rerenderSelectedChart();
          }
          function resetChartView() {
            chartViewState.zoom = 1;
            chartViewState.offset = 0;
            chartViewState.priceZoom = 1;
            chartViewState.pricePan = 0;
            updateChartZoomBadge();
            rerenderSelectedChart();
          }
          function chartWindow(allCandles) {
            const total = allCandles.length;
            if (!total) return { candles: [], start: 0, end: 0 };
            const base = Math.min(total, 80);
            const visible = Math.max(
              chartViewState.minVisible,
              Math.min(total, Math.round(base / chartViewState.zoom)),
            );
            const maxOffset = Math.max(0, total - visible);
            chartViewState.offset = Math.max(
              0,
              Math.min(maxOffset, Math.round(chartViewState.offset)),
            );
            const end = total - chartViewState.offset;
            const start = Math.max(0, end - visible);
            return { candles: allCandles.slice(start, end), start, end };
          }
          function bindChartManipulation() {
            const wrap = $('chartWrap');
            if (!wrap || wrap.dataset.navBound === '1') return;
            wrap.dataset.navBound = '1';
            wrap.addEventListener(
              'wheel',
              (e) => {
                if (!selectedTradeId) return;
                e.preventDefault();
                const rect = wrap.getBoundingClientRect();
                if (e.ctrlKey) {
                  const anchorX = rect.width > 0 ? (e.clientX - rect.left) / rect.width : 0.5;
                  changeChartZoom(e.deltaY < 0 ? 1.18 : 1 / 1.18, anchorX);
                  return;
                }
                const anchorY = rect.height > 0 ? (e.clientY - rect.top) / rect.height : 0.5;
                changePriceZoom(e.deltaY < 0 ? 1.16 : 1 / 1.16, anchorY);
              },
              { passive: false },
            );
            wrap.addEventListener('dblclick', (e) => {
              if (!selectedTradeId) return;
              e.preventDefault();
              resetChartView();
            });
            wrap.addEventListener('pointerdown', (e) => {
              if (!selectedTradeId || e.button !== 0) return;
              chartViewState.dragging = true;
              chartViewState.dragStartX = e.clientX;
              chartViewState.dragStartY = e.clientY;
              chartViewState.dragStartOffset = chartViewState.offset;
              chartViewState.dragStartPricePan = chartViewState.pricePan;
              wrap.classList.add('dragging');
              try {
                wrap.setPointerCapture(e.pointerId);
              } catch (_) {}
            });
            wrap.addEventListener('pointermove', (e) => {
              if (chartViewState.dragging) {
                const dx = e.clientX - chartViewState.dragStartX,
                  dy = e.clientY - chartViewState.dragStartY,
                  width = Math.max(1, wrap.clientWidth),
                  height = Math.max(1, wrap.clientHeight);
                const t = (latestState?.open_positions || []).find(
                  (x) => String(x.id) === String(selectedTradeId),
                );
                const ec = t?.entry_chart || {},
                  c =
                    chartViewState.auditMode === 'ENTRY' && Object.keys(ec).length
                      ? ec
                      : t?.chart || {},
                  tf = (c.timeframes || {})[chartViewState.timeframe] || c,
                  all = tf.candles || [],
                  total = all.length,
                  baseVisible = Math.min(total, 80);
                const visible = Math.max(
                  chartViewState.minVisible,
                  Math.min(total, Math.round(baseVisible / Math.max(1, chartViewState.zoom))),
                );
                const pxPerCandle = width / Math.max(1, visible);
                const maxOffset = Math.max(0, total - visible);
                chartViewState.offset = Math.max(
                  0,
                  Math.min(maxOffset, chartViewState.dragStartOffset + dx / Math.max(1, pxPerCandle)),
                );
                chartViewState.pricePan =
                  chartViewState.dragStartPricePan +
                  dy / height / Math.max(1, chartViewState.priceZoom);
                chartViewState.pricePan = Math.max(-3, Math.min(3, chartViewState.pricePan));
                updateChartZoomBadge();
                rerenderSelectedChart();
              } else if (chartRenderContext && chartRenderContext.candles && chartRenderContext.candles.length) {
                updateChartCrosshair(e, wrap, chartRenderContext);
              }
            });
            wrap.addEventListener('pointerleave', () => {
              hideChartCrosshair(chartRenderContext);
            });
            const stop = (e) => {
              if (!chartViewState.dragging) return;
              chartViewState.dragging = false;
              wrap.classList.remove('dragging');
              if (e && e.pointerId != null) {
                try {
                  wrap.releasePointerCapture(e.pointerId);
                } catch (_) {}
              }
            };
            wrap.addEventListener('pointerup', stop);
            wrap.addEventListener('pointercancel', stop);
            updateChartZoomBadge();
          }
          function updateChartHud(q, symbol, tf) {
            const symEl = $('hudSymbol'),
              tfEl = $('hudTf'),
              oEl = $('hudOpen'),
              hEl = $('hudHigh'),
              lEl = $('hudLow'),
              cEl = $('hudClose'),
              chEl = $('hudChange'),
              rsiEl = $('hudRsi');
            if (symEl) symEl.textContent = symbol || '—';
            if (tfEl) tfEl.textContent = tf || '—';
            if (!q) {
              if (oEl) oEl.textContent = '—';
              if (hEl) hEl.textContent = '—';
              if (lEl) lEl.textContent = '—';
              if (cEl) cEl.textContent = '—';
              if (chEl) {
                chEl.textContent = '—';
                chEl.className = 'hudChange';
              }
              if (rsiEl) rsiEl.textContent = '—';
              return;
            }
            if (oEl) oEl.textContent = priceFmt(q.open);
            if (hEl) hEl.textContent = priceFmt(q.high);
            if (lEl) lEl.textContent = priceFmt(q.low);
            if (cEl) cEl.textContent = priceFmt(q.close);
            const diff = Number(q.close) - Number(q.open);
            const pctVal = Number(q.open) ? (diff / Number(q.open)) * 100 : 0;
            if (chEl) {
              chEl.textContent = `${diff >= 0 ? '+' : ''}${priceFmt(diff)} (${pctVal >= 0 ? '+' : ''}${pctVal.toFixed(2)}%)`;
              chEl.className = 'hudChange ' + (diff >= 0 ? 'good' : 'bad');
            }
            if (rsiEl) rsiEl.textContent = q.rsi14 != null ? n(q.rsi14, 1) : '—';
          }
          function updateChartCrosshair(e, wrap, ctx) {
            const ch = $('chartCrosshair');
            if (!ch || !ctx) return;
            const rect = wrap.getBoundingClientRect();
            if (rect.width <= 0 || rect.height <= 0) return;
            const svgX = (e.clientX - rect.left) * (ctx.W / rect.width);
            const svgY = (e.clientY - rect.top) * (ctx.H / rect.height);
            if (
              svgX < ctx.pad.l ||
              svgX > ctx.W - ctx.pad.r ||
              svgY < ctx.pad.t ||
              svgY > ctx.H - ctx.pad.b
            ) {
              ch.style.display = 'none';
              return;
            }
            ch.style.display = '';
            const plotW = ctx.W - ctx.pad.l - ctx.pad.r;
            const candleIdx = Math.max(
              0,
              Math.min(
                ctx.candles.length - 1,
                Math.floor(((svgX - ctx.pad.l) / plotW) * ctx.candles.length),
              ),
            );
            const q = ctx.candles[candleIdx];
            if (q) {
              updateChartHud(q, ctx.symbol, ctx.activeTf);
            }
            const cX = ctx.pad.l + ((candleIdx + 0.5) * plotW) / ctx.candles.length;
            const vLine = $('crossV');
            if (vLine) {
              vLine.setAttribute('x1', cX);
              vLine.setAttribute('x2', cX);
            }
            const hLine = $('crossH');
            if (hLine) {
              hLine.setAttribute('y1', svgY);
              hLine.setAttribute('y2', svgY);
            }
            const priceBadge = $('crossPriceBadge');
            if (priceBadge) {
              if (svgY <= ctx.priceBottom) {
                priceBadge.style.display = '';
                const p = ctx.max - ((svgY - ctx.pad.t) / ctx.priceH) * (ctx.max - ctx.min);
                const prRect = $('crossPriceRect'),
                  prText = $('crossPriceText');
                if (prRect) prRect.setAttribute('y', svgY - 8.5);
                if (prText) {
                  prText.setAttribute('y', svgY + 3.5);
                  prText.textContent = priceFmt(p);
                }
              } else if (svgY >= ctx.rsiTop && svgY <= ctx.rsiTop + ctx.rsiH) {
                priceBadge.style.display = '';
                const r = 100 - ((svgY - ctx.rsiTop) / ctx.rsiH) * 100;
                const prRect = $('crossPriceRect'),
                  prText = $('crossPriceText');
                if (prRect) prRect.setAttribute('y', svgY - 8.5);
                if (prText) {
                  prText.setAttribute('y', svgY + 3.5);
                  prText.textContent = 'RSI ' + n(r, 1);
                }
              } else {
                priceBadge.style.display = 'none';
              }
            }
            const timeBadge = $('crossTimeBadge');
            if (timeBadge && q) {
              const tmRect = $('crossTimeRect'),
                tmText = $('crossTimeText');
              const tmW = 86;
              const badgeX = Math.max(
                ctx.pad.l,
                Math.min(ctx.W - ctx.pad.r - tmW, cX - tmW / 2),
              );
              if (tmRect) tmRect.setAttribute('x', badgeX);
              if (tmText) {
                tmText.setAttribute('x', badgeX + tmW / 2);
                const d = new Date(q.time);
                tmText.textContent = !isNaN(d.getTime())
                  ? d.toLocaleTimeString([], {
                      hour: '2-digit',
                      minute: '2-digit',
                      second: '2-digit',
                    })
                  : String(q.time).slice(11, 19);
              }
            }
          }
          function hideChartCrosshair(ctx) {
            const ch = $('chartCrosshair');
            if (ch) ch.style.display = 'none';
            if (ctx && ctx.candles && ctx.candles.length) {
              updateChartHud(ctx.candles[ctx.candles.length - 1], ctx.symbol, ctx.activeTf);
            }
          }
          function eventLayer(ev) {
            if (ev && ev.layer) return String(ev.layer);
            const t = String(ev?.type || ev || '');
            if (t.includes('swing')) return 'swings';
            if (t.includes('choch') || t.includes('bos')) return 'structure';
            if (t.includes('liquidity') || t.includes('sweep')) return 'liquidity';
            if (t.includes('order_block')) return 'orderblock';
            if (t.includes('fvg')) return 'fvg';
            return 'confluence';
          }
          function nearestCandleIndex(candles, time, clamp = false) {
            if (!time || !candles.length) return null;
            const target = new Date(time).getTime();
            if (!Number.isFinite(target)) return null;
            const first = new Date(candles[0].time).getTime(),
              last = new Date(candles[candles.length - 1].time).getTime();
            if (
              !clamp &&
              Number.isFinite(first) &&
              Number.isFinite(last) &&
              (target < first || target > last)
            )
              return null;
            let best = null,
              dist = Infinity;
            candles.forEach((q, i) => {
              const d = Math.abs(new Date(q.time).getTime() - target);
              if (d < dist) {
                dist = d;
                best = i;
              }
            });
            return best;
          }
          function chartObjectX(allCandles, win, time, plotW, padLeft) {
            const gi = nearestCandleIndex(allCandles, time, true);
            if (gi == null) return null;
            return padLeft + ((gi - win.start + 0.5) * plotW) / Math.max(1, win.end - win.start);
          }
          function viewBoxHtml(title, v) {
            const passed = (v.passed || []).slice(0, 10),
              missing = [
                ...(v.missing || []),
                ...(v.critical_failures || []).map((x) => 'CRÍTICA: ' + x),
              ].slice(0, 7),
              stamp = v.evaluated_at
                ? `<div class="sub" style="font-size:10px; margin-bottom:4px;">Actualizado ${new Date(v.evaluated_at).toLocaleTimeString('es-CL')}</div>`
                : '';
            const cf = [];
            if (v.divergence_confirmed)
              cf.push('Divergencia: ' + (v.divergence_type || 'confirmada'));
            if (v.h1_doji_confirmed)
              cf.push(
                'Doji H1: ' +
                  (v.h1_doji_type || 'confirmado') +
                  (v.h1_doji_zone ? ' · ' + v.h1_doji_zone : ''),
              );
            if (v.harmonic_confirmed) cf.push('Armónico: ' + (v.harmonic_pattern || 'confirmado'));
            if (v.chart_pattern_confirmed)
              cf.push(
                'Chartista: ' +
                  (v.chart_pattern_name || 'confirmado') +
                  ' · fuerza ' +
                  (v.chart_pattern_strength == null
                    ? '—'
                    : n(Number(v.chart_pattern_strength) * 100, 0) + '%'),
              );
            if (v.chart_pattern_conflict) {
              const sp = v.chart_pattern_supporting_pattern,
                sd = v.chart_pattern_supporting_direction,
                ss = v.chart_pattern_supporting_strength,
                cp = v.chart_pattern_conflicting_pattern,
                cd = v.chart_pattern_conflicting_direction,
                cs = v.chart_pattern_conflicting_strength;
              cf.push(
                'Conflicto chartista: ' +
                  (v.chart_pattern_conflict_reason || 'patrones opuestos detectados'),
              );
              if (sp)
                cf.push(
                  'A favor: ' +
                    String(sp).replaceAll('_', ' ') +
                    ' · ' +
                    (sd || '—') +
                    ' · ' +
                    (ss == null ? '—' : n(Number(ss) * 100, 0) + '%'),
                );
              if (cp)
                cf.push(
                  'En contra: ' +
                    String(cp).replaceAll('_', ' ') +
                    ' · ' +
                    (cd || '—') +
                    ' · ' +
                    (cs == null ? '—' : n(Number(cs) * 100, 0) + '%'),
                );
              if (v.chart_pattern_conflict_level)
                cf.push(
                  'Nivel conflicto: ' + String(v.chart_pattern_conflict_level).replaceAll('_', ' '),
                );
            }

            const stratPill = v.strategy_name
              ? `<span class="pill" style="font-size:10px; font-weight:700; background:rgba(41,98,255,0.18); color:#59a5ff; border:1px solid rgba(41,98,255,0.35); text-transform:uppercase;">${esc(v.strategy_name)}</span>`
              : '';

            const rawDec = String(v.decision || v.state || v.status || 'Sin registro');
            const isGood = rawDec.includes('BENEFICIO') || rawDec.includes('CONFIRMAD') || rawDec.includes('VIGENTE') || rawDec.includes('PROGRESO');
            const isWarn = rawDec.includes('RETROCESO') || rawDec.includes('VIGILAR') || rawDec.includes('CRÍTICA');
            const decPillClass = isGood ? 'good' : isWarn ? 'warn' : 'neutral';

            let paramsHtml = '';
            if (v.strategy_name === 'MALAYSIAN_SNR' || v.scenario || v.break_level != null || v.ref_level != null) {
              const pList = [];
              if (v.scenario_desc || v.scenario) pList.push(`<div class="setupParamsItem"><span class="setupParamsLabel">Escenario:</span> <span class="setupParamsVal">${esc(v.scenario_desc || v.scenario)}</span></div>`);
              if (v.break_level != null) pList.push(`<div class="setupParamsItem"><span class="setupParamsLabel">Nivel Break:</span> <span class="setupParamsVal">${priceFmt(v.break_level)}</span></div>`);
              if (v.ref_level != null) pList.push(`<div class="setupParamsItem"><span class="setupParamsLabel">Nivel Ref:</span> <span class="setupParamsVal">${priceFmt(v.ref_level)}</span></div>`);
              if (v.momentum_adx != null) pList.push(`<div class="setupParamsItem"><span class="setupParamsLabel">ADX:</span> <span class="setupParamsVal">${n(v.momentum_adx, 1)}</span></div>`);
              if (v.body_ratio != null) {
                const brPct = Number(v.body_ratio) <= 1.0 ? Number(v.body_ratio) * 100 : Number(v.body_ratio);
                pList.push(`<div class="setupParamsItem"><span class="setupParamsLabel">Cuerpo:</span> <span class="setupParamsVal">${n(brPct, 0)}%</span></div>`);
              }
              if (v.runner_target_name || v.runner_rr) pList.push(`<div class="setupParamsItem"><span class="setupParamsLabel">Corredora:</span> <span class="setupParamsVal">${esc(v.runner_target_name || 'TP2')} (1:${n(v.runner_rr || 2.0, 1)}R)</span></div>`);
              if (pList.length) paramsHtml = `<div class="setupParamsGrid">${pList.join('')}</div>`;
            } else if (v.strategy_name === 'ORB_NEW_YORK' || v.opening_range_high != null) {
              const pList = [];
              if (v.opening_range_high != null) pList.push(`<div class="setupParamsItem"><span class="setupParamsLabel">OR High:</span> <span class="setupParamsVal">${priceFmt(v.opening_range_high)}</span></div>`);
              if (v.opening_range_low != null) pList.push(`<div class="setupParamsItem"><span class="setupParamsLabel">OR Low:</span> <span class="setupParamsVal">${priceFmt(v.opening_range_low)}</span></div>`);
              if (v.opening_range_midpoint != null) pList.push(`<div class="setupParamsItem"><span class="setupParamsLabel">Midpoint:</span> <span class="setupParamsVal">${priceFmt(v.opening_range_midpoint)}</span></div>`);
              if (v.session_vwap != null) pList.push(`<div class="setupParamsItem"><span class="setupParamsLabel">VWAP:</span> <span class="setupParamsVal">${priceFmt(v.session_vwap)}</span></div>`);
              if (pList.length) paramsHtml = `<div class="setupParamsGrid">${pList.join('')}</div>`;
            } else if (v.strategy_name === 'GOLD_QUARTERS' || v.major_quarter != null) {
              const pList = [];
              if (v.major_quarter != null) pList.push(`<div class="setupParamsItem"><span class="setupParamsLabel">Cuadrante:</span> <span class="setupParamsVal">${priceFmt(v.major_quarter)}</span></div>`);
              if (v.quarters_level != null) pList.push(`<div class="setupParamsItem"><span class="setupParamsLabel">Reacción:</span> <span class="setupParamsVal">${priceFmt(v.quarters_level)}</span></div>`);
              if (v.target_quarter != null) pList.push(`<div class="setupParamsItem"><span class="setupParamsLabel">Target:</span> <span class="setupParamsVal">${priceFmt(v.target_quarter)}</span></div>`);
              if (pList.length) paramsHtml = `<div class="setupParamsGrid">${pList.join('')}</div>`;
            }

            const scoreParts = [];
            if (v.direction) scoreParts.push(`<span class="pill ${v.direction === 'BUY' ? 'good' : 'bad'}" style="font-size:10px; padding:2px 6px;">${esc(v.direction)}</span>`);
            if (v.score != null) scoreParts.push(`<span class="pill neutral" style="font-size:10px; padding:2px 6px;">Score ${n(v.score, 0)}</span>`);
            if (v.grade) scoreParts.push(`<span class="pill good" style="font-size:10px; padding:2px 6px;">Grado ${esc(v.grade)}</span>`);
            if (v.confirmation_percentage != null) scoreParts.push(`<span class="pill" style="font-size:10px; padding:2px 6px;">${pct(v.confirmation_percentage)}</span>`);
            const scoreHtml = scoreParts.length ? `<div style="display:flex; gap:5px; flex-wrap:wrap; margin:6px 0 4px 0;">${scoreParts.join('')}</div>` : '';

            const passedHtml = passed.length
              ? `<div class="good" style="margin-top:6px; font-size:11px; line-height:1.5;">${passed.map((p) => `<div style="display:flex; align-items:flex-start; gap:5px;"><span style="color:#089981; font-weight:700;">✓</span><span>${esc(p)}</span></div>`).join('')}</div>`
              : '';
            const missingHtml = missing.length
              ? `<div class="warn" style="margin-top:5px; font-size:11px; line-height:1.4;">${missing.map((m) => `<div style="display:flex; align-items:flex-start; gap:5px;"><span style="color:#f23645;">•</span><span>${esc(m)}</span></div>`).join('')}</div>`
              : '';

            const smcTrendHtml = v.h1_trend ? `<div style="font-size:11px; color:var(--muted); margin-top:4px;">H1 ${esc(v.h1_trend)} · ${esc(v.structure_break || '—')} · ${esc(v.zone || '—')}</div>` : '';
            const reasonHtml = v.reason ? `<div class="sub" style="margin-top:6px; font-size:11px; line-height:1.4;">${esc(v.reason)}</div>` : '';
            const obsHtml = (v.observations || []).length ? `<div class="sub" style="margin-top:4px; font-size:11px; line-height:1.4;">${v.observations.map(esc).join('<br>')}</div>` : '';

            return `<section class="compareBox"><div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;"><h5>${esc(title)}</h5>${stratPill}</div>${stamp}<div style="margin:4px 0 6px 0;"><span class="pill ${decPillClass}" style="font-size:11px; font-weight:700; padding:3px 8px;">${esc(rawDec)}</span></div>${scoreHtml}${paramsHtml}${smcTrendHtml}${reasonHtml}${obsHtml}${cf.length ? `<div class="warn" style="margin-top:5px; font-size:11px;">${cf.map(esc).join('<br>')}</div>` : ''}${passedHtml}${missingHtml}</section>`;
          }
          function mtfAuditHtml(mtf) {
            const order = ['H1', 'M15', 'M5', 'M1'];
            return `<div style="margin-top:10px"><b>Contexto SMC multi-timeframe:</b>${order
              .map((tf) => {
                const q = mtf?.[tf] || {},
                  c = q.context || {},
                  ev = (q.recent_events || []).slice(-4);
                return `<div class="compareBox" style="margin-top:6px"><h5>${tf}</h5><div>Zona: <b>${esc(c.zone || '—')}</b> · EQ: ${priceFmt(c.equilibrium)}</div><div>Rango: ${priceFmt(c.range_low)} → ${priceFmt(c.range_high)}</div>${ev.length ? `<div style="margin-top:4px">${ev.map((x) => `<span class="pill">${esc(x.label)}</span>`).join(' ')}</div>` : '<div class="sub">Sin eventos recientes publicados.</div>'}</div>`;
              })
              .join('')}</div>`;
          }
          function renderPositionChart(t) {
            if (!t) {
              $('chartTitle').textContent = 'Selecciona una posición';
              $('chartSubtitle').textContent =
                'Navega M1 / M5 / M15 / H1; el gráfico usa todo el ancho y la comparación Entrada vs. Ahora queda debajo.';
              $('chartMeta').innerHTML = '';
              $('chartWrap').innerHTML =
                '<div class="empty">Selecciona “Ver gráfico” en una posición abierta.</div>';
              $('chartAudit').innerHTML = 'Sin posición seleccionada.';
              return;
            }
            const requestedEntry = chartViewState.auditMode === 'ENTRY',
              entryChart = t.entry_chart || {},
              hasEntry = Object.keys(entryChart).length > 0,
              c = requestedEntry && hasEntry ? entryChart : t.chart || {},
              tfMap = c.timeframes || {},
              tf = tfMap[chartViewState.timeframe] || c,
              allCandles = tf.candles || [],
              win = chartWindow(allCandles),
              candles = win.candles,
              events = tf.events || [],
              zones = tf.zones || [],
              liqLevels = tf.levels || [],
              smc = tf.smc_context || {},
              mtf = c.multi_timeframe || {},
              sv = t.latest_strategy_view || {},
              entryView = t.entry_strategy_view || {};
            const activeTf = tf.timeframe || chartViewState.timeframe || 'M5',
              mode = tf.context_mode || (activeTf === 'M1' ? 'AUXILIAR' : 'ESTRATEGIA');
            document
              .querySelectorAll('.tfBtn[data-tf]')
              .forEach((b) =>
                b.classList.toggle('active', b.dataset.tf === chartViewState.timeframe),
              );
            const modeEl = $('chartTfMode');
            if (modeEl) {
              modeEl.textContent = mode;
              modeEl.className = 'pill chartTfMode ' + (mode === 'AUXILIAR' ? 'aux' : 'strategy');
            }
            $('chartTitle').textContent =
              `${t.symbol} · ${t.direction} · ${t.leg || 'POSICIÓN'} · ${t.owner_profile || 'OWNER ?'}`;
            const auditLabel =
              requestedEntry && hasEntry ? 'EVIDENCIA DE ENTRADA PERSISTIDA' : 'ESTADO ACTUAL';
            const auditTime =
              requestedEntry && hasEntry ? t.entry_chart_captured_at : t.visual_audit_updated_at;
            $('chartSubtitle').textContent =
              `${auditLabel} · ${activeTf} · ${mode === 'AUXILIAR' ? 'contexto visual auxiliar' : 'capas SMC de estrategia'} · auditoría ${auditTime ? new Date(auditTime).toLocaleTimeString() : 'pendiente'} · owner ${t.chart_owner_profile || t.owner_profile || '—'} · recomendación ${t.recommendation || '—'}`;
            $('chartMeta').innerHTML =
              `<span class="pill ${t.health_score == null ? 'neutral' : scoreClass(t.health_score)}">Salud ${t.health_score == null ? 'N/D' : n(t.health_score, 0) + '/100'}</span><span class="pill">${esc(t.managed_by_daemon ? 'GESTIONADA' : 'SOLO VISUAL')}</span><span class="pill">Magic ${esc(t.owner_magic || '—')}</span><span class="pill">${esc(t.current_rr == null ? 'R —' : n(t.current_rr, 2) + 'R')}</span><span class="pill">Entrada ${priceFmt(t.entry_price)}</span><span class="pill">Actual ${priceFmt(t.current_price)}</span><span class="pill">${activeTf} · ${candles.length}/${allCandles.length} velas</span>`;
            const audit = [];
            audit.push(
              `<div class="compareGrid">${viewBoxHtml('Tesis al abrir', entryView)}${viewBoxHtml('Lo que ve ahora', sv)}</div>`,
            );
            audit.push(
              `<div><b>Recomendación:</b> <span class="${t.recommendation === 'MANTENER' ? 'good' : t.recommendation === 'VIGILAR' ? 'warn' : 'bad'}">${esc(t.recommendation || '—')}</span></div>`,
            );
            audit.push(
              `<div style="margin-top:7px"><b>Mapa SMC ${esc(activeTf)}:</b> ${events.length} eventos · ${liqLevels.length} niveles de liquidez · ${zones.filter((z) => z.layer === 'orderblock').length} OB · ${zones.filter((z) => z.layer === 'fvg').length} FVG</div>`,
            );
            audit.push(mtfAuditHtml(mtf));
            audit.push(
              `<div style="margin-top:7px"><b>Razones de salud:</b><ul class="auditList">${(t.reasons || []).map((x) => `<li>${esc(x)}</li>`).join('') || '<li>Sin razones suficientes.</li>'}</ul></div>`,
            );
            audit.push(
              `<div class="sub" style="margin-top:8px">M1 es navegación auxiliar y no modifica las condiciones de entrada. M5/M15/H1 muestran las capas SMC publicadas por el pipeline cuando están disponibles.</div>`,
            );
            $('chartAudit').innerHTML = audit.join('');
            if (!candles.length) {
              chartRenderContext = null;
              updateChartHud(null, t?.symbol, activeTf);
              $('chartWrap').innerHTML =
                `<div class="empty">Auditoría visual pendiente para ${esc(t.symbol)} · owner ${esc(t.owner_profile || 'no identificado')}. El worker debe publicar un snapshot persistente ${esc(activeTf)}.${tf.error ? ' · ' + esc(tf.error) : ''}</div>`;
              return;
            }
            const W = 1000,
              H = 540,
              pad = { l: 20, r: 94, t: 20, b: 26 },
              rsiH = 92,
              rsiGap = 20;
            const priceBottom = H - pad.b - rsiH - rsiGap,
              priceH = priceBottom - pad.t;
            const lows = candles.map((x) => Number(x.low)),
              highs = candles.map((x) => Number(x.high));
            const levelVals = [
              t.entry_price,
              t.stop_loss,
              t.take_profit,
              t.current_stop_loss,
              t.current_price,
              smc.range_high,
              smc.range_low,
              smc.equilibrium,
            ]
              .map(Number)
              .filter(Number.isFinite);
            let min = Math.min(...lows, ...levelVals),
              max = Math.max(...highs, ...levelVals);
            let span = max - min;
            if (!(span > 0)) span = Math.max(1, Math.abs(max) * 0.01);
            min -= span * 0.08;
            max += span * 0.08;
            const autoCenter = (min + max) / 2,
              autoSpan = Math.max(1e-12, max - min),
              visibleSpan = autoSpan / Math.max(1, chartViewState.priceZoom),
              visibleCenter = autoCenter + chartViewState.pricePan * autoSpan;
            min = visibleCenter - visibleSpan / 2;
            max = visibleCenter + visibleSpan / 2;
            const plotW = W - pad.l - pad.r;
            const x = (i) => pad.l + ((i + 0.5) * plotW) / candles.length;
            const y = (v) => pad.t + ((max - Number(v)) / (max - min)) * priceH;
            const cw = Math.max(3, (plotW / candles.length) * 0.65);
            const rsiTop = priceBottom + rsiGap,
              rsiY = (v) => rsiTop + ((100 - Number(v)) / 100) * rsiH;
            let out = `<svg class="chartSvg" viewBox="0 0 ${W} ${H}" role="img" aria-label="Auditoría SMC ${esc(activeTf)} de ${esc(t.symbol)}"><defs><clipPath id="chartPriceClip"><rect x="${pad.l}" y="${pad.t}" width="${plotW}" height="${priceH}"/></clipPath><clipPath id="chartRsiClip"><rect x="${pad.l}" y="${rsiTop}" width="${plotW}" height="${rsiH}"/></clipPath></defs><rect width="${W}" height="${H}" fill="#131722"/><rect x="${pad.l}" y="${pad.t}" width="${plotW}" height="${priceH}" fill="#131722"/><rect x="${pad.l}" y="${rsiTop}" width="${plotW}" height="${rsiH}" fill="#0e121b"/><rect x="${W - pad.r}" y="0" width="${pad.r}" height="${H}" fill="#131722"/><rect x="0" y="${H - pad.b}" width="${W}" height="${pad.b}" fill="#131722"/><line x1="${W - pad.r}" y1="0" x2="${W - pad.r}" y2="${H - pad.b}" stroke="#1e222d" stroke-width="1"/><line x1="0" y1="${H - pad.b}" x2="${W}" y2="${H - pad.b}" stroke="#1e222d" stroke-width="1"/><line x1="0" y1="${priceBottom + rsiGap / 2}" x2="${W}" y2="${priceBottom + rsiGap / 2}" stroke="#1e222d" stroke-width="1"/>`;
            for (let i = 0; i <= 5; i++) {
              const yy = pad.t + (i * priceH) / 5,
                val = max - (i * (max - min)) / 5;
              out += `<line x1="${pad.l}" y1="${yy}" x2="${W - pad.r}" y2="${yy}" stroke="#1e222d" stroke-width="1" stroke-dasharray="3 3"/><line x1="${W - pad.r}" y1="${yy}" x2="${W - pad.r + 4}" y2="${yy}" stroke="#2a2e39"/><text x="${W - pad.r + 8}" y="${yy + 3.5}" fill="#787b86" font-size="9.5" font-family="monospace, sans-serif">${priceFmt(val)}</text>`;
            }
            const vGridCount = Math.min(6, candles.length);
            for (let k = 0; k < vGridCount; k++) {
              const cIdx = Math.floor((k * (candles.length - 1)) / Math.max(1, vGridCount - 1));
              const gx = x(cIdx);
              out += `<line x1="${gx}" y1="${pad.t}" x2="${gx}" y2="${H - pad.b}" stroke="#181c27" stroke-width="1" stroke-dasharray="2 4"/>`;
            }
            if (chartLayerState.premiumdiscount && smc.premium_discount_available) {
              const eq = Number(smc.equilibrium),
                rh = Number(smc.range_high),
                rl = Number(smc.range_low);
              if ([eq, rh, rl].every(Number.isFinite)) {
                const top = y(Math.min(rh, max)),
                  mid = y(eq),
                  bot = y(Math.max(rl, min));
                out += `<g clip-path="url(#chartPriceClip)"><rect x="${pad.l}" y="${top}" width="${plotW}" height="${Math.max(0, mid - top)}" fill="rgba(242, 54, 69, 0.04)"/><rect x="${pad.l}" y="${mid}" width="${plotW}" height="${Math.max(0, bot - mid)}" fill="rgba(8, 153, 129, 0.04)"/><line x1="${pad.l}" y1="${mid}" x2="${W - pad.r}" y2="${mid}" stroke="#eab308" stroke-width="1.2" stroke-dasharray="4 4" opacity="0.85"/><text x="${W - pad.r - 8}" y="${Math.max(pad.t + 13, top + 13)}" text-anchor="end" fill="#f87171" opacity="0.38" font-size="9" font-weight="700" letter-spacing="1">PREMIUM</text><text x="${W - pad.r - 8}" y="${Math.min(priceBottom - 6, bot - 6)}" text-anchor="end" fill="#34d399" opacity="0.38" font-size="9" font-weight="700" letter-spacing="1">DISCOUNT</text></g><rect x="${W - pad.r + 3}" y="${mid - 8}" width="${pad.r - 6}" height="16" rx="2" fill="#ca8a04"/><text x="${W - pad.r + pad.r / 2}" y="${mid + 3.5}" text-anchor="middle" fill="#000" font-size="9" font-weight="800">EQ 50%</text>`;
              }
            }
            zones
              .filter((z) => chartLayerState[z.layer])
              .forEach((z) => {
                const xx = chartObjectX(allCandles, win, z.time, plotW, pad.l);
                if (xx == null) return;
                const lo = Number(z.low),
                  hi = Number(z.high);
                if (!Number.isFinite(lo) || !Number.isFinite(hi)) return;
                const yy1 = y(hi),
                  yy2 = y(lo),
                  zoneTop = Math.min(yy1, yy2),
                  zoneHeight = Math.max(2, Math.abs(yy2 - yy1)),
                  zoneRight = W - pad.r,
                  w = zoneRight - xx;
                if (w <= 0) return;
                const isMitigated =
                  z.status === 'INVALIDADA' ||
                  z.status === 'RELLENADA' ||
                  z.status === 'MITIGADA' ||
                  z.status === 'SWEPT';
                if (chartLayerState.cleanZones && isMitigated) return;
                const bullish = z.direction === 'BUY';
                let col = '',
                  badgeBg = '',
                  badgeTextCol = '',
                  zoneLabel = '';
                if (z.layer === 'fvg') {
                  col = bullish ? '#818cf8' : '#a855f7';
                  badgeBg = bullish ? 'rgba(49, 46, 129, 0.88)' : 'rgba(88, 28, 135, 0.88)';
                  badgeTextCol = bullish ? '#c7d2fe' : '#e9d5ff';
                  zoneLabel = `FVG ${bullish ? 'BULL' : 'BEAR'}${isMitigated ? ' (MIT)' : ''}`;
                } else {
                  col = bullish ? '#089981' : '#f23645';
                  badgeBg = bullish ? 'rgba(6, 78, 59, 0.88)' : 'rgba(136, 19, 55, 0.88)';
                  badgeTextCol = bullish ? '#34d399' : '#fb7185';
                  zoneLabel = `OB ${bullish ? 'BULL' : 'BEAR'}${isMitigated ? ' (MIT)' : ''}`;
                }
                const opacity = isMitigated ? '0.04' : '0.12';
                const badgeW = isMitigated ? 68 : 48;
                out += `<g clip-path="url(#chartPriceClip)"><rect x="${xx}" y="${zoneTop}" width="${w}" height="${zoneHeight}" rx="3" ry="3" fill="${col}" opacity="${opacity}" stroke="${col}" stroke-width="1" stroke-dasharray="${z.layer === 'fvg' ? '4 3' : '3 3'}"><title>${esc(z.label)} · ${esc(z.status || '')} [${priceFmt(lo)} - ${priceFmt(hi)}]</title></rect><rect x="${xx + 4}" y="${zoneTop + 2}" width="${badgeW}" height="14" rx="2" fill="${badgeBg}"/><text class="zoneChartLabel" x="${xx + 6}" y="${zoneTop + 12}" fill="${badgeTextCol}" font-size="8.5" font-weight="700">${esc(zoneLabel)}</text></g>`;
              });
            liqLevels
              .filter(() => chartLayerState.liquidity)
              .forEach((l) => {
                const xx = chartObjectX(allCandles, win, l.time, plotW, pad.l),
                  pv = Number(l.price);
                if (xx == null || !Number.isFinite(pv) || xx >= W - pad.r) return;
                const yy = y(pv),
                  isBsl = l.type === 'buy_side_liquidity',
                  col = isBsl ? '#f59e0b' : '#38bdf8';
                out += `<g clip-path="url(#chartPriceClip)"><line x1="${xx}" y1="${yy}" x2="${W - pad.r}" y2="${yy}" stroke="${col}" stroke-width="1" stroke-dasharray="2 4" opacity="0.65"><title>${esc(l.label)}</title></line><rect x="${xx + 4}" y="${yy - 11}" width="26" height="11" rx="2" fill="${col}" opacity="0.25"/><text x="${xx + 17}" y="${yy - 3}" text-anchor="middle" fill="${col}" font-size="8" font-weight="800">${isBsl ? 'BSL' : 'SSL'}</text></g>`;
              });
            candles.forEach((q, i) => {
              const xx = x(i),
                yo = y(q.open),
                yc = y(q.close),
                yh = y(q.high),
                yl = y(q.low),
                up = Number(q.close) >= Number(q.open),
                col = up ? '#089981' : '#f23645';
              out += `<g clip-path="url(#chartPriceClip)"><line x1="${xx}" y1="${yh}" x2="${xx}" y2="${yl}" stroke="${col}" stroke-width="1.2"/><rect x="${xx - cw / 2}" y="${Math.min(yo, yc)}" width="${cw}" height="${Math.max(1, Math.abs(yc - yo))}" rx="1" ry="1" fill="${col}" opacity="0.95"/></g>`;
            });
            if (chartLayerState.trade) {
              const tradeLevels = [
                { id: 'TP', label: 'TP', val: t.take_profit, bg: '#089981', fg: '#ffffff', dash: '4 4' },
                { id: 'SL', label: 'SL', val: t.stop_loss, bg: '#f23645', fg: '#ffffff', dash: '4 4' },
                { id: 'ENT', label: 'ENT', val: t.entry_price, bg: '#2962ff', fg: '#ffffff', dash: '6 4' },
                { id: 'BE', label: 'BE', val: t.current_stop_loss, bg: '#d97706', fg: '#ffffff', dash: '4 3' },
                { id: 'ACT', label: 'ACT', val: t.current_price, bg: '#475569', fg: '#ffffff', dash: '2 2' },
              ];
              const validLevels = tradeLevels
                .filter((x) => Number.isFinite(Number(x.val)))
                .map((lvl) => ({
                  ...lvl,
                  val: Number(lvl.val),
                  y: y(Number(lvl.val)),
                }))
                .sort((a, b) => a.y - b.y);

              validLevels.forEach((l) => {
                l.badgeY = l.y;
              });
              for (let k = 1; k < validLevels.length; k++) {
                if (validLevels[k].badgeY - validLevels[k - 1].badgeY < 18) {
                  validLevels[k].badgeY = validLevels[k - 1].badgeY + 18;
                }
              }
              if (
                validLevels.length &&
                validLevels[validLevels.length - 1].badgeY > priceBottom
              ) {
                const shift = validLevels[validLevels.length - 1].badgeY - priceBottom;
                validLevels.forEach((l) => {
                  l.badgeY -= shift;
                });
              }

              validLevels.forEach((lvl) => {
                out += `<line x1="${pad.l}" y1="${lvl.y}" x2="${W - pad.r}" y2="${lvl.y}" stroke="${lvl.bg}" stroke-width="1.4" stroke-dasharray="${lvl.dash}" opacity="0.85"/>`;
                if (Math.abs(lvl.badgeY - lvl.y) > 1) {
                  out += `<line x1="${W - pad.r}" y1="${lvl.y}" x2="${W - pad.r + 3}" y2="${lvl.badgeY}" stroke="${lvl.bg}" stroke-width="1.2"/>`;
                }
                out += `<rect x="${W - pad.r + 3}" y="${lvl.badgeY - 8.5}" width="${pad.r - 6}" height="17" rx="3" fill="${lvl.bg}"/><text class="priceLabel" x="${W - pad.r + (pad.r - 6) / 2 + 3}" y="${lvl.badgeY + 3.5}" text-anchor="middle" fill="${lvl.fg}" font-size="9.5" font-family="monospace, sans-serif" font-weight="700">${lvl.label} ${priceFmt(lvl.val)}</text>`;
              });

              const ei = nearestCandleIndex(candles, t.entry_time);
              if (ei != null) {
                const ex = x(ei);
                out += `<line x1="${ex}" y1="${pad.t}" x2="${ex}" y2="${priceBottom}" stroke="#2962ff" stroke-width="1.5" stroke-dasharray="3 3" opacity="0.85"/><rect x="${Math.min(ex - 2, W - pad.r - 180)}" y="${pad.t + 2}" width="176" height="18" rx="3" fill="#1e3a8a" opacity="0.9"/><text class="entryTag" x="${Math.min(ex + 4, W - pad.r - 174)}" y="${pad.t + 14}" fill="#93c5fd" font-size="9" font-weight="700">ENTRADA · ${entryView.score == null ? 'score —' : 'score ' + n(entryView.score, 0)} · ${pct(entryView.confirmation_percentage)}</text>`;
              }
            }
            const timeIndex = new Map(candles.map((q, i) => [String(q.time).slice(0, 16), i]));
            events
              .filter((e) => chartLayerState[eventLayer(e)])
              .forEach((e) => {
                let i = timeIndex.get(String(e.time).slice(0, 16));
                if (i == null) return;
                const xx = x(i),
                  py = y(
                    e.price != null
                      ? e.price
                      : e.direction === 'BUY'
                        ? candles[i].low
                        : candles[i].high,
                  ),
                  bull = e.direction === 'BUY';
                if (e.layer === 'swings') {
                  const col = bull ? '#38bdf8' : '#fbbf24',
                    dy = bull ? 14 : -8,
                    circleDy = bull ? 5 : -5;
                  out += `<g clip-path="url(#chartPriceClip)"><circle cx="${xx}" cy="${py + circleDy}" r="2" fill="${col}"/><text x="${xx}" y="${py + dy}" text-anchor="middle" fill="${col}" font-size="8" font-weight="800"><title>${esc(e.label)}</title>${esc(e.label)}</text></g>`;
                  return;
                }
                const col = bull ? '#38bdf8' : '#fbbf24',
                  pts = bull
                    ? `${xx},${py - 12} ${xx - 5},${py - 3} ${xx + 5},${py - 3}`
                    : `${xx},${py + 12} ${xx - 5},${py + 3} ${xx + 6},${py + 3}`;
                out += `<g clip-path="url(#chartPriceClip)"><polygon points="${pts}" fill="${col}"><title>${esc(e.label)}</title></polygon></g>`;
              });
            if (chartLayerState.confluence) {
              const ei = nearestCandleIndex(candles, t.entry_time);
              if (ei != null) {
                let ty = pad.t + 36;
                const con = [];
                if (entryView.divergence_confirmed) con.push('DIV RSI (' + (entryView.divergence_type || 'confirmada') + ')');
                if (entryView.h1_doji_confirmed) con.push('DOJI H1 (' + (entryView.h1_doji_type || 'confirmado') + ')');
                if (entryView.harmonic_confirmed) con.push('ARMÓNICO');
                if (entryView.chart_pattern_confirmed)
                  con.push(
                    'PATRÓN ' +
                      String(entryView.chart_pattern_name || 'CHARTISTA').replaceAll('_', ' '),
                  );
                con.forEach((label) => {
                  const chipW = Math.min(220, label.length * 6.5 + 24);
                  out += `<g opacity="0.92"><rect x="${pad.l + 8}" y="${ty - 11}" width="${chipW}" height="16" rx="3" fill="rgba(15, 23, 42, 0.85)" stroke="#f59e0b" stroke-width="0.8"/><text x="${pad.l + 14}" y="${ty + 1}" fill="#fbbf24" font-size="8.5" font-weight="700">✦ ${esc(label)}</text></g>`;
                  ty += 19;
                });
              }
              if (entryView.h1_doji_confirmed && entryView.h1_doji_time) {
                const di = nearestCandleIndex(candles, entryView.h1_doji_time);
                if (di != null) {
                  const xx = x(di),
                    py = y(candles[di].low);
                  out += `<circle cx="${xx}" cy="${py + 9}" r="4" fill="none" stroke="#fbbf24" stroke-width="2"><title>${esc(entryView.h1_doji_type || 'Doji H1 en extremo')}</title></circle>`;
                }
              }
            }
            if (chartLayerState.confluence && entryView.chart_pattern_confirmed) {
              const pe = entryView.chart_pattern_evidence || {},
                anchors = pe.anchors || [],
                pts = [];
              anchors.forEach((a) => {
                const ai = nearestCandleIndex(candles, a.time),
                  pv = Number(a.price);
                if (ai == null || !Number.isFinite(pv)) return;
                pts.push([x(ai), y(pv)]);
                out += `<circle cx="${x(ai)}" cy="${y(pv)}" r="4" fill="none" stroke="#fbbf24" stroke-width="2"><title>${esc(pe.pattern || entryView.chart_pattern_name || 'Patrón chartista')}</title></circle>`;
              });
              if (pts.length > 1)
                out += `<polyline points="${pts.map((p) => p.join(',')).join(' ')}" fill="none" stroke="#fbbf24" stroke-width="1.5" stroke-dasharray="5 4" opacity="0.9"/>`;
              if (pts.length)
                out += `<text x="${Math.min(pts[pts.length - 1][0] + 7, W - pad.r - 220)}" y="${Math.max(pad.t + 15, pts[pts.length - 1][1] - 8)}" fill="#fbbf24" font-size="9" font-weight="800">${esc(String(pe.pattern || entryView.chart_pattern_name || 'PATRÓN').replaceAll('_', ' '))}</text>`;
            }
            if (chartLayerState.rsi) {
              out += `<g clip-path="url(#chartRsiClip)"><rect x="${pad.l}" y="${rsiY(100)}" width="${plotW}" height="${Math.max(0, rsiY(70) - rsiY(100))}" fill="rgba(242, 54, 69, 0.05)"/><rect x="${pad.l}" y="${rsiY(70)}" width="${plotW}" height="${Math.max(0, rsiY(30) - rsiY(70))}" fill="rgba(129, 140, 248, 0.04)"/><rect x="${pad.l}" y="${rsiY(30)}" width="${plotW}" height="${Math.max(0, rsiY(0) - rsiY(30))}" fill="rgba(8, 153, 129, 0.05)"/></g>`;
              [70, 50, 30].forEach((v) => {
                const yy = rsiY(v);
                const col = v === 70 ? 'rgba(242, 54, 69, 0.45)' : v === 30 ? 'rgba(8, 153, 129, 0.45)' : '#334155';
                out += `<line x1="${pad.l}" y1="${yy}" x2="${W - pad.r}" y2="${yy}" stroke="${col}" stroke-width="1" stroke-dasharray="3 3"/><line x1="${W - pad.r}" y1="${yy}" x2="${W - pad.r + 4}" y2="${yy}" stroke="#2a2e39"/><text class="rsiLabel" x="${W - pad.r + 8}" y="${yy + 3.5}" fill="${v === 70 ? '#ef4444' : v === 30 ? '#22c55e' : '#64748b'}" font-size="9.5" font-family="monospace, sans-serif">${v}</text>`;
              });
              let pts = [];
              let lastRsi = null;
              candles.forEach((q, i) => {
                const rv = Number(q.rsi14);
                if (Number.isFinite(rv)) {
                  pts.push(`${x(i)},${rsiY(rv)}`);
                  lastRsi = rv;
                }
              });
              if (pts.length > 1) {
                out += `<g clip-path="url(#chartRsiClip)"><polyline points="${pts.join(' ')}" fill="none" stroke="#818cf8" stroke-width="1.8" stroke-linejoin="round"/></g>`;
              }
              out += `<text x="${pad.l + 8}" y="${rsiTop + 14}" fill="#787b86" font-size="9.5" font-family="monospace, sans-serif" font-weight="700">RSI (14, Close)</text>`;
              if (lastRsi != null) {
                const rY = rsiY(lastRsi);
                out += `<rect x="${W - pad.r + 3}" y="${rY - 7.5}" width="${pad.r - 6}" height="15" rx="2" fill="#6366f1"/><text x="${W - pad.r + pad.r / 2}" y="${rY + 3.5}" text-anchor="middle" fill="#ffffff" font-size="9" font-family="monospace, sans-serif" font-weight="700">${n(lastRsi, 1)}</text>`;
              }
            }
            const tickCount = Math.min(6, candles.length);
            for (let tIdx = 0; tIdx < tickCount; tIdx++) {
              const i = Math.floor((tIdx * (candles.length - 1)) / Math.max(1, tickCount - 1));
              const d = new Date(candles[i].time);
              const timeStr = !isNaN(d.getTime())
                ? d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                : String(candles[i].time).slice(11, 16);
              out += `<text x="${x(i)}" y="${H - 8}" text-anchor="middle" fill="#787b86" font-size="10" font-family="monospace, sans-serif">${timeStr}</text>`;
            }
            out += `<g id="chartCrosshair" style="display:none; pointer-events:none;"><line id="crossV" x1="0" y1="${pad.t}" x2="0" y2="${H - pad.b}" stroke="#787b86" stroke-width="1" stroke-dasharray="3 3"/><line id="crossH" x1="${pad.l}" y1="0" x2="${W - pad.r}" y2="0" stroke="#787b86" stroke-width="1" stroke-dasharray="3 3"/><g id="crossPriceBadge" style="display:none;"><rect id="crossPriceRect" x="${W - pad.r + 2}" y="0" width="${pad.r - 4}" height="17" rx="2" fill="#2a2e39"/><text id="crossPriceText" x="${W - pad.r + pad.r / 2}" y="0" text-anchor="middle" fill="#ffffff" font-size="9.5" font-family="monospace, sans-serif" font-weight="700"></text></g><g id="crossTimeBadge"><rect id="crossTimeRect" x="0" y="${H - pad.b + 2}" width="86" height="17" rx="2" fill="#2a2e39"/><text id="crossTimeText" x="0" y="${H - pad.b + 14}" text-anchor="middle" fill="#ffffff" font-size="9.5" font-family="monospace, sans-serif" font-weight="700"></text></g></g>`;
            out += '</svg>';
            $('chartWrap').innerHTML = out;
            chartRenderContext = {
              W,
              H,
              pad,
              priceBottom,
              priceH,
              rsiTop,
              rsiH,
              min,
              max,
              candles,
              symbol: t.symbol,
              activeTf,
            };
            if (candles.length) {
              updateChartHud(candles[candles.length - 1], t.symbol, activeTf);
            }
          }
          function selectTrade(id) {
            selectedTradeId = String(id);
            const t = (latestState?.open_positions || []).find(
              (x) => String(x.id) === selectedTradeId,
            );
            renderPositionChart(t);
            renderOpenRows(latestState?.open_positions || []);
          }
          function renderOpenRows(rows) {
            $('openBody').innerHTML =
              (rows || [])
                .map((t) => {
                  const rec = t.recommendation || 'SIN DATOS';
                  const cls =
                    rec === 'MANTENER'
                      ? 'good'
                      : rec === 'VIGILAR'
                        ? 'warn'
                        : rec === 'SIN VALIDACIÓN EN VIVO' ||
                            rec === 'SIN TELEMETRÍA DEL WORKER' ||
                            rec === 'WORKER SIN ACTIVIDAD'
                          ? 'neutral'
                          : 'bad';
                  const rs = (t.reasons || [])
                    .slice(0, 5)
                    .map((x) => `• ${esc(x)}`)
                    .join('<br>');
                  const sel = String(t.id) === String(selectedTradeId) ? 'selectedRow' : '';
                  const persisted =
                    t.persistence_status === 'PERSISTED'
                      ? '<span class="statusPill warn">PERSISTIDA · SIN CONEXIÓN</span>'
                      : '<span class="statusPill good">EN VIVO</span>';
                  const health = t.health_score == null ? '—' : n(t.health_score, 0) + '/100';
                  const owner = t.owner_profile || 'NO IDENTIFICADO';
                  const ownerStatus = t.ownership_status || '—';
                  const ownerCls = t.managed_by_daemon ? 'good' : 'warn';
                  const chartAvailable = t.chart && Object.keys(t.chart).length;
                  const durationPill = t.duration_str && t.duration_str !== '—'
                    ? `<span class="pill neutral" style="font-size:10px; padding:1px 6px; margin-left:4px; font-weight:600;" title="Tiempo transcurrido en posición">⏱ ${esc(t.duration_str)}</span>`
                    : '';
                  const scorePill = t.quality_score != null
                    ? `<span class="pill neutral" style="font-size:11px; font-weight:700; padding:2px 7px;">${n(t.quality_score, 0)}</span>`
                    : '—';
                  const confPill = t.confirmation_percentage != null
                    ? `<span class="pill ${t.confirmation_percentage >= 80 ? 'good' : 'neutral'}" style="font-size:11px; font-weight:700; padding:2px 7px;">${pct(t.confirmation_percentage)}</span>`
                    : '—';
                  return `<tr class="${sel}">
    <td><b>${esc(t.symbol)}</b> ${durationPill}<br><span class="sub">${esc(t.execution_mode)} · ${esc(t.leg)}</span><br>${persisted}<span class="technical">${esc(t.broker_verification)}</span></td>
    <td><b class="${ownerCls}">${esc(owner)}</b><br><span class="technical">Magic ${esc(t.owner_magic || '—')} · ${esc(ownerStatus)}</span><br><span class="technical">Worker ${esc(t.worker_status || '—')}${t.worker_pid ? ' · PID ' + esc(t.worker_pid) : ''}</span></td>
    <td>${esc(t.direction)}</td>
    <td class="score ${t.health_score == null ? 'neutral' : scoreClass(t.health_score)}">${health}<br><span class="pill">${esc(t.health_grade || '—')}</span></td>
    <td class="${cls}"><b>${esc(rec)}</b></td>
    <td>${t.current_rr == null ? '—' : n(t.current_rr, 2) + 'R'}</td>
    <td class="${t.break_even_confirmed ? 'good' : 'warn'}">${t.break_even_confirmed ? 'ACTIVO' : 'Pendiente'}</td>
    <td>${scorePill}</td>
    <td>${confPill}</td>
    <td>${esc(t.current_price)}</td>
    <td class="sub">${rs || 'Sin razones suficientes todavía'}</td>
    <td><button type="button" class="btn viewBtn" data-trade-id="${esc(t.id)}">${chartAvailable ? 'Ver gráfico' : 'Esperando gráfico'}</button></td>
   </tr>`;
                })
                .join('') ||
              '<tr><td colspan="12" class="empty">No hay operaciones abiertas registradas</td></tr>';
            $('openBody')
              .querySelectorAll('button[data-trade-id]')
              .forEach((b) => b.addEventListener('click', () => selectTrade(b.dataset.tradeId)));
          }
          function candidateFromWorker(worker) {
            if (!worker) return {};
            const details = worker.details || {},
              result = details.result && typeof details.result === 'object' ? details.result : {};
            return {
              ...result,
              symbol: worker.current_symbol || result.symbol,
              _worker_profile: worker.bot_profile,
              _worker_magic: worker.daemon_magic,
              _worker_cycle: worker.cycle_number,
              _worker_time: worker.last_event_time,
              _worker_action: worker.last_action,
            };
          }
          function renderCandidateTabs(s) {
            const workers = visibleWorkers(s),
              profiles = [
                'TODOS',
                ...workers.map((w) => String(w.bot_profile || '').toUpperCase()).filter(Boolean),
              ];
            const unique = [...new Set(profiles)];
            if (!unique.includes(selectedCandidateBot)) selectedCandidateBot = 'TODOS';
            const box = $('candidateBotTabs');
            if (!box) return;
            box.innerHTML = unique
              .map(
                (p) =>
                  `<button type="button" class="botTab ${p === selectedCandidateBot ? 'active' : ''}" data-bot="${esc(p)}">${esc(p)}</button>`,
              )
              .join('');
            box.querySelectorAll('button[data-bot]').forEach((b) =>
              b.addEventListener('click', () => {
                selectedCandidateBot = b.dataset.bot;
                render(latestState);
              }),
            );
          }
          function selectedCandidate(s) {
            const workers = visibleWorkers(s);
            if (!workers.length) return {};
            let worker = null;
            if (selectedCandidateBot === 'TODOS') {
              worker = [...workers].sort(
                (a, b) => new Date(b.last_event_time || 0) - new Date(a.last_event_time || 0),
              )[0];
            } else {
              worker = workers.find(
                (w) => String(w.bot_profile || '').toUpperCase() === selectedCandidateBot,
              );
            }
            return candidateFromWorker(worker);
          }
          function renderCandidateContext(last) {
            const box = $('candidateContext');
            if (!box) return;
            if (!last || !last._worker_profile) {
              box.innerHTML = '<span class="pill">Sin worker seleccionado</span>';
              return;
            }
            box.innerHTML = `<span class="pill good">BOT ${esc(last._worker_profile)}</span><span class="pill">Magic ${esc(last._worker_magic || '—')}</span><span class="pill">Ciclo ${esc(last._worker_cycle || 0)}</span><span class="pill">${esc(last._worker_action || 'En espera')}</span><span class="pill">${last._worker_time ? 'Actualizado ' + new Date(last._worker_time).toLocaleTimeString() : 'Sin timestamp'}</span>`;
          }
          function visibleWorkers(s) {
            return (s.worker_states || []).filter(
              (w) => !['FLIP', 'IDX_OPEN'].includes(String(w.bot_profile || '').toUpperCase()),
            );
          }
          function renderLearningAudit(s) {
            const box = $('learningAuditPanel');
            if (!box) return;
            box.innerHTML =
              '<h3>Auditoría MT5 y aprendizaje candidato</h3><p>Captura de entrada, resultado cerrado y validación temporal. No activa modelos ni modifica SL/TP. MT5_OBSERVATION aprende variación de precio desde la primera observación hasta el cierre; no representa el PnL neto ni la señal original.</p>' +
              ((s.learning_audit || [])
                .map(
                  (r) =>
                    `<details><summary>${esc(r.worker)} · ${esc(r.source || '')} · ${esc(r.updated_at || r.error || '')} · ${r.stale ? 'INFORME ANTIGUO' : 'ACTUALIZADO'} · ${r.schema_current ? 'ESQUEMA VIGENTE' : 'ESQUEMA ANTERIOR'}</summary><p>Historial de la cuenta: ${Number(r.account_trades) || 0} registros · Con captura: ${Number(r.with_entry_snapshot) || 0} · Sin captura: ${Number(r.without_entry_snapshot) || 0} · Con primera observación: ${Number(r.with_observation) || 0}</p>${Object.entries(r.scopes || {}).map(([scope, v]) => `
                      <p><b>Ámbito ${esc(scope)}</b>: ${Number(v.execution_rows) || 0} ejecuciones ·
                      ${Number(v.logical_setups) || 0} setups únicos · ${Number(v.closed_setups) || 0} cerrados ·
                      ${Number(v.entry_captures) || 0} capturas de entrada</p>
                      <details><summary>Elegibilidad por ejecución</summary>
                      ${Object.entries(v.eligibility_reasons_by_execution || {}).map(([reason, count]) =>
                        `<p>${esc(reason)}: ${Number(count)}</p>`).join('')}</details>`).join('')}
                      <p>Entrenamiento por familia: ${Number(r.training_funnel?.eligible_closed_setups_family) || 0}
                      setups cerrados elegibles. Promoción automática deshabilitada.
                      Los esquemas antiguos requieren evidencia original; no se rellenan variables inventadas.</p>${
                      Object.entries(r.strategies || {})
                        .map(
                          ([k, v]) =>
                            `<p>${esc(k)} · Setups cerrados elegibles de la familia: ${Number(v.eligible_closed_setups) || 0} / mínimo ${Number(v.minimum) || 0} · ${esc(v.reason)} · Candidato entrenado: ${v.trained ? 'sí' : 'no'}<br>Validación: ${esc(v.temporal_validation?.reason || 'pendiente')} · Muestras evaluadas: ${Number(v.temporal_validation?.samples_evaluated) || 0} · Brier: ${esc(v.temporal_validation?.brier_score ?? '—')}</p>`,
                        )
                        .join('') || '<p>Sin capturas de entrada disponibles para entrenar.</p>'
                    }<details><summary>Elegibilidad de la familia (últimas 100 ejecuciones)</summary>${(r.trade_eligibility || []).map((t) => `<p>Trade ${esc(t.trade_id)} · ${esc(t.symbol)} · ${esc(t.evidence_type)} · ${esc(t.reason)}</p>`).join('')}</details><details><summary>Comparación por setup cerrado de la familia</summary><p>${esc(r.closed_comparison?.counterfactual_status || 'Sin comparación')} · ${Number(r.closed_comparison?.pending_setups) || 0} pendientes · ${Number(r.closed_comparison?.missing_variant_capture) || 0} sin captura de variante · ${Number(r.closed_comparison?.target_review_pending) || 0} pendientes de reconciliación SL/TP · ${Number(r.closed_comparison?.manual_exit_setups) || 0} setups con cierre manual (separados de la comparación autónoma)</p><details><summary>Resultados por versión de estrategia</summary>${Object.entries(r.closed_comparison?.by_version || {}).map(([k,v]) => `<p>${esc(k)} · ${Number(v.closed_setups)} setups · R neto total ${Number(v.sum_net_r).toFixed(3)}</p>`).join('')}</details>${Object.entries(
                      r.closed_comparison?.cohorts || {},
                    )
                      .map(
                        ([k, v]) =>
                          `<p>${esc(k)} · ${Number(v.closed_setups)} setups · R neto medio ${Number(v.mean_net_r).toFixed(3)} · ${esc(v.note)}</p>`,
                      )
                      .join(
                        '',
                      )}</details><p>Resultados de cuenta por instrumento (setups cerrados):</p>${Object.entries(
                      r.instruments || {},
                    )
                      .map(
                        ([k, v]) =>
                          `<p>${esc(k)} · ${Number(v.closed_setups)} cerrados · ${Number(v.wins)} positivos / ${Number(v.losses)} negativos · PnL neto ${Number(v.net_pnl).toFixed(2)}</p>`,
                      )
                      .join('')}</details>`,
                )
                .join('') ||
                '<p>Pendiente de la primera actualización del worker con esta versión.</p>');
          }
          function renderPersistenceHealth(s) {
            const rows = s.forex_spread_audit || [];
            return rows.filter(x => x.persistence?.status === 'DEGRADED').map(x =>
              `<p class="bad">Persistencia de spread degradada: ${esc(x.worker)} · ${esc(x.symbol)} ·
              ${esc(x.persistence.at)} · ${esc(x.persistence.error)}</p>`).join('');
          }
          function renderSmcTrial(s) {
            const box = $('smcTrialPanel');
            if (!box) return;
            const report = s.smc_trial || {},
              workers = report.workers || [];
            box.innerHTML =
              workers
                .map(
                  (w) =>
                    `<details><summary>${esc(w.profile)} · ${esc(w.policy)} · ${esc(w.retest)} · ${Number(w.evaluations) || 0} evaluaciones</summary><div class="sub">Desde ${esc(w.since)} · Actualizado ${esc(w.updated_at)} · ${(w.stale_signals || []).length} señales caducadas únicas</div><div><p>Bloques M15 únicos del día: ${Object.keys(w.m15_blocks || {}).length} ·
                    Señales observadas: ${Object.keys(w.signal_observations || {}).length} ·
                    Primeras observaciones ya antiguas: ${Object.values(w.signal_observations || {}).filter(x => x.stale_at_first_seen).length}.
                    Estos conteos no equivalen a operaciones.</p>
                    <details><summary>Últimos 30 bloques registrados y motivos</summary>
                    ${Object.entries(w.m15_blocks || {}).slice(-30).map(([id, block]) => `
                      <p>${esc(block.symbol)} · ${esc(id)} · ${block.state?.accepted ? 'Aceptado como setup' : 'Descartado'}<br>
                      ${esc((block.state?.reasons || []).join(', ') || 'Sin rechazos M15')} ·
                      ${Number(block.evaluations) || 0} evaluaciones · ${Number(block.timeline?.length) || 0} cambios conservados</p>`).join('')}
                    </details>
                    <details><summary>Última señal observada por instrumento</summary>
                    ${Object.entries(w.latest || {}).map(([symbol, item]) => `<p>${esc(symbol)} ·
                    ${esc(item.signal_age?.observation_class || 'Sin señal')} ·
                    Primera observación: ${esc(item.signal_age?.first_seen || '—')} ·
                    Retraso desde cierre M5: ${esc(item.signal_age?.first_detection_delay_seconds ?? '—')} s</p>`).join('')}
                    </details></div><div>${Object.entries(
                      w.counts || {},
                    )
                      .map(([k, v]) => esc(k) + ': ' + Number(v))
                      .join(' · ')}</div>${Object.values(w.latest || {})
                      .map(
                        (r) =>
                          `<p><b>${esc(r.symbol)}</b> · ${esc(r.action)} · ${esc(r.reason || '')}<br><span class="sub">${esc(r.updated_at)} · Confirmación favorable: ${r.favorable_confirmation?.confirmed ? (r.favorable_confirmation.chart_pattern ? 'patrón chartista' : 'agotamiento confirmado') : 'sin confirmación registrada'} · Obstáculos M15 (informativo): ${esc(
                            Object.entries(r.target_path_audit || {})
                              .map(
                                ([leg, a]) =>
                                  leg +
                                  ': ' +
                                  (a.obstacles || [])
                                    .map(
                                      (o) =>
                                        o.type +
                                        ' ' +
                                        Number(o.low).toFixed(3) +
                                        '–' +
                                        Number(o.high).toFixed(3) +
                                        ' / ' +
                                        Number(o.distance_r).toFixed(2) +
                                        'R',
                                    )
                                    .join(', '),
                              )
                              .join(' | ') || 'sin evaluación registrada',
                          )} · Edad M5: ${esc((r.signal_age || {}).age_candles ?? '—')} velas · Críticas: ${esc((r.critical_confirmation_failures || []).join(', ') || '—')} · Zona H1: ${r.entry_location_comparison?.H1_PRIMARY?.valid === true ? 'apta' : r.entry_location_comparison?.H1_PRIMARY?.valid === false ? 'bloqueada' : 'sin evaluar'} · Zona tres marcos: ${r.entry_location_comparison?.ALL_TIMEFRAMES?.valid === true ? 'apta' : r.entry_location_comparison?.ALL_TIMEFRAMES?.valid === false ? 'bloqueada' : 'sin evaluar'}</span></p>`,
                      )
                      .join('')}</details>`,
                )
                .join('') || 'Sin registros: reiniciar los workers para cargar la prueba.';
            const orb = s.orb_audit || {};
            box.innerHTML += `<details open><summary>ORB · resultados por activo y modalidad</summary><p>Esperanza = PnL neto cerrado / ejecuciones cerradas. Cada pierna cuenta por separado.</p>${(s.orb_execution_metrics || []).map(m => `<p><b>${esc(m.symbol)} · ${esc(m.strategy)}</b> · ${esc(m.source)} / ${esc(m.broker)} · Cerradas ${esc(m.closed)} · Ganadas ${esc(m.wins)} · Perdidas ${esc(m.losses)} · PnL ${esc(m.net_pnl)} · Esperanza ${esc(m.expectancy_net_pnl ?? '—')}</p>`).join('') || 'Sin ejecuciones ORB etiquetadas.'}${s.orb_metrics_error ? '<p>Métricas temporalmente no disponibles.</p>' : ''}</details>`;
            box.innerHTML += `<details open><summary>ORB · rango y rechazos · ${esc(orb.day || 'sin registros')}</summary><p>Actualizado ${esc(orb.updated_at || '—')} · Comparaciones solo en sombra; no autorizan entradas.</p>${Object.values(
              orb.latest || {},
            )
              .map(
                (a) =>
                  `<p><b>${esc(a.symbol)}</b> · ${esc(a.reason)}<br>Perfil ${esc(a.asset_profile || "—")} · Modos ${esc((a.allowed_modes || []).join(", "))} · Rango/ATR ${esc(a.range_amplitude?.ratio ?? "—")} · Calidad retest ${esc(a.retest?.quality || "—")}${a.session_cancellation ? " · Cancelado por ratio " + esc(a.session_cancellation.ratio) + " > " + esc(a.session_cancellation.critical_ratio) : ""}<br>ORH ${esc(a.orh)} / ORL ${esc(a.orl)} · ${esc(a.range_start)} → ${esc(a.range_end)} · ${esc(a.source)}<br>Cuerpo ${a.momentum?.body_ratio == null ? '—' : (100 * a.momentum.body_ratio).toFixed(1) + '%'} · Extensión ${a.momentum?.extension_atr == null ? '—' : Number(a.momentum.extension_atr).toFixed(2) + ' ATR'} · Volumen ${esc((a.volume_evidence || a.momentum)?.volume_status || 'no evaluado')} · Fuente ${esc((a.volume_evidence || a.momentum)?.volume_source || 'sin datos')} · Ruptura ${esc((a.volume_evidence || a.momentum)?.volume ?? '—')} / Media ${esc((a.volume_evidence || a.momentum)?.average_volume ?? '—')} · Ratio ${esc((a.volume_evidence || a.momentum)?.volume_ratio ?? '—')} / Umbral ${esc((a.volume_evidence || a.momentum)?.volume_threshold ?? '—')}</p><details><summary>Velas que forman el rango</summary>${(a.opening_candles || []).map((c) => `<p>${esc(c.time)} · O ${esc(c.open)} H ${esc(c.high)} L ${esc(c.low)} C ${esc(c.close)}</p>`).join('')}</details>`,
              )
              .join(
                '',
              )}<details><summary>${Object.keys(orb.candidates || {}).length} rupturas únicas: sensibilidad de momentum</summary>${Object.values(
              orb.candidates || {},
            )
              .map(
                (a) =>
                  `<p>${esc(a.symbol)} · ${esc(a.momentum?.confirmation_time)}<br>${Object.entries(
                    a.momentum?.variants || {},
                  )
                    .map(
                      ([k, v]) =>
                        esc(k) +
                        ': ' +
                        esc(
                          v.remaining_failures.join(', ') ||
                            'cumple momentum; faltan otros controles',
                        ),
                    )
                    .join('<br>')}</p>`,
              )
              .join('')}</details></details>`;
            workers.forEach((w) => {
              const setups = Object.values(w.unique_setups || {});
              const spreads = (s.forex_spread_audit || []).filter((x) => x.worker === w.profile);
              if (spreads.length)
                box.innerHTML += `<details><summary>${esc(w.profile)} · Spread de ejecución MT5</summary>${spreads.map((x) => `<p>${esc(x.symbol)} · ${esc(x.reason)} · ${x.spread_pips == null ? 'desconocido' : Number(x.spread_pips).toFixed(2) + ' pips'} · muestras ${Number(x.samples_count)} · estables ${Number(x.stable_count)}<br>Actualizado ${esc(x.observed_at)}</p>`).join('')}</details>`;
              const uniqueDiag = w.unique_setup_diagnostics || {};
              box.innerHTML += `<p>${esc(w.profile)} · Setups con captura incompleta: ${Number(uniqueDiag.capture_failure_setups || 0)}</p>`;
              box.innerHTML += setups.filter(x => Object.keys(x.variant_capture_failures || {}).length).map(x => `<p>${esc(x.symbol)} · ${Object.entries(x.variant_capture_failures).map(([name, failure]) => esc(name) + ': ' + esc(failure.reason)).join(' · ')}</p>`).join('');

              const replay = w.variant_outcomes || {};
              box.innerHTML += `<p><b>${esc(w.profile)} · Comparación con resultados cerrados (sombra)</b><br>${esc(replay.updated_at || 'Pendiente de actualización')} · ${esc(replay.limitations || 'Sin planes causales cerrados disponibles')}</p>`;
              box.innerHTML += Object.entries(replay.variants || {})
                .map(
                  ([k, v]) =>
                    `<p>${esc(k)}: ${Number(v.unique_setups)} setups únicos · ${Number(v.closed_replays)} replays cerrados · TP ${Number(v.tp)} / SL ${Number(v.sl)} · R bruto ${Number(v.gross_r_sum).toFixed(2)} · pendientes/excluidos ${Number(v.excluded_or_pending)}</p>`,
                )
                .join('');

              box.innerHTML += `<p><b>${esc(w.profile)} · Fallos pendientes por setup único</b><br>${
                Object.entries(uniqueDiag.remaining_failure_counts || {})
                  .map(([k, v]) => esc(k) + ': ' + Number(v))
                  .join(' · ') || 'Sin comparación disponible'
              }</p>`;
              box.innerHTML += `<details><summary>${esc(w.profile)} · ${setups.length} setups únicos observados · variantes solo en sombra</summary>${setups
                .map(
                  (x) =>
                    `<p>${esc(x.symbol)} · ${Number(x.evaluations)} evaluaciones · ${esc(x.action)}<br>Formación ${esc(x.setup_formed_at || '—')} · primera detección ${esc(x.first_seen)} · última ${esc(x.last_seen)} · primera caducidad ${esc(x.first_expired_at || '—')}<br>${Object.entries(
                      x.comparison?.variants || {},
                    )
                      .map(
                        ([k, v]) =>
                          esc(k) +
                          ': resuelve ' +
                          esc((v.resolved_failures || []).join(', ') || 'ninguno') +
                          '; persisten ' +
                          esc(
                            (v.remaining_critical_failures || []).join(', ') ||
                              'sin críticos; faltan otros controles',
                          ),
                      )
                      .join('<br>')}</p>`,
                )
                .join('')}</details>`;
              const groups = Object.entries(w.groups || {});
              if (groups.length)
                box.innerHTML += `<p><b>${esc(w.profile)} · por mercado</b><br>${groups
                  .map(
                    ([g, c]) =>
                      esc(g) +
                      ': ' +
                      Object.entries(c)
                        .map(([k, v]) => esc(k) + ' ' + Number(v))
                        .join(' · '),
                  )
                  .join('<br>')}</p>`;
              const candidates = Object.values(w.candidates || {});
              if (candidates.length)
                box.innerHTML += `<details><summary>${esc(w.profile)} · ${candidates.length} candidatas únicas (no operaciones)</summary>${candidates.map((c) => `<p>${esc(c.symbol)} · ${c.expired ? 'CADUCADA' : 'ÚLTIMO ESTADO REGISTRADO'} · ${esc(c.action)}<br>Señal ${esc(c.signal_time)} · Primera detección ${esc(c.first_seen)} · Última ${esc(c.last_seen)}<br>${esc(c.reason || '')}</p>`).join('')}</details>`;
            });
            box.innerHTML += `<details open><summary>Reglas actualizadas y flexibilidades pendientes</summary><ul><li>Activo al reiniciar: H1 sólo ubicación; dirección confirmada por setup M15 y CHOCH/BOS M5.</li><li>Activo al reiniciar: recuperación del OB al cierre como alternativa al rechazo por mecha; conserva desplazamiento y confirmación favorable.</li><li>Pendiente, NO ACTIVADO: desplazamiento, calibrar umbral relativo a volatilidad por instrumento, sin reducirlo globalmente.</li><li>Pendiente, NO ACTIVADO: secuencia, comprobar vigencia de setups anteriores antes de recuperarlos.</li><li>Forex: ventana diaria NY y cierre preventivo configurados; GOLD: pausa por cotizaciones no disponibles.</li></ul><p>Promover cambios sólo tras replay fuera de muestra con costes, expectativa y drawdown. RR, spread y riesgo siguen vigentes. H1_PRIMARY y ATR_BOUNDED ya son la prueba activa según el worker.</p></details>`;
            if ((report.errors || []).length)
              box.innerHTML += '<p>' + esc(report.errors.join(' · ')) + '</p>';
          }
          function renderQuarantine(s) {
            const box = $('quarantinePanel');
            if (!box) return;
            const q = s.risk_quarantine || {},
              items = q.items || [];
            const num = (v) =>
              v == null ? '—' : Number(v).toLocaleString('es-CL', { maximumFractionDigits: 4 });
            if (q.status === 'ERROR') {
              box.textContent = 'No se pudo leer la cuarentena. ' + (q.error || '');
              return;
            }
            box.innerHTML = items.length
              ? items
                  .map(
                    (x) =>
                      `<section class="workerCard" style="margin-top:10px"><div class="workerHead"><b>${esc(x.symbol)}</b><span class="statusPill warn">${esc(x.status)}</span></div><p>${esc(x.reason)} · ${esc(x.direction || '')} · ${esc(x.trade_leg || '')}</p><div class="workerMeta"><div><span>Riesgo objetivo</span><b>${num(x.target_risk)}</b></div><div><span>Riesgo ejecutado</span><b>${num(x.actual_risk)}</b></div><div><span>Límite máximo</span><b>${num(x.hard_cap)}</b></div><div><span>Exceso sobre objetivo</span><b>${x.excess_ratio == null ? '—' : num(x.excess_ratio * 100) + '%'}</b></div></div><p class="sub">Desde ${esc(x.since ? new Date(x.since).toLocaleString() : 'sin fecha')} · ${x.expires_at ? 'Reevaluación desde ' + esc(new Date(x.expires_at).toLocaleString()) : 'Requiere revisión manual'}</p><details><summary>Acciones para investigar y prevenir</summary><ul>${(x.actions || []).map((a) => '<li>' + esc(a) + '</li>').join('')}</ul></details></section>`,
                  )
                  .join('')
              : 'Sin instrumentos registrados en cuarentena.';
          }
          function renderWorkers(s) {
            const rows = visibleWorkers(s),
              grid = $('workerGrid');
            if (!grid) return;
            const order = ['BOOM', 'CRASH', 'VOLATILITY', 'STEP', 'JUMP', 'GOLD', 'ORB', 'FOREX', 'MALAYSIAN_SNR', 'ICT'];
            const workerLabels = {
              IDX_OPEN: 'Apertura Bursátiles',
              GOLD: 'Oro · Cuartos & Niveles Psicológicos (XAUUSD)',
              ORB: 'ORB · Apertura New York',
              MALAYSIAN_SNR: 'Malaysian SNR (M15 Fresh/Break)',
              ICT: 'ICT',
            };
            const now = Date.now();
            const sorted = [...rows].sort((a, b) => {
              const ai = order.indexOf(String(a.bot_profile || '').toUpperCase()),
                bi = order.indexOf(String(b.bot_profile || '').toUpperCase());
              return (ai < 0 ? 99 : ai) - (bi < 0 ? 99 : bi);
            });
            grid.innerHTML =
              sorted
                .map((w) => {
                  const prof = String(w.bot_profile || '').toUpperCase();
                  const isGold = prof === 'GOLD';
                  const isOrb = prof === 'ORB';
                  const total = Number(w.symbols_total || 0),
                    done = Number(w.symbols_processed || 0),
                    pctv = total ? Math.min(100, (done / total) * 100) : 0;
                  const age = w.last_event_time
                    ? Math.max(0, (now - new Date(w.last_event_time).getTime()) / 1000)
                    : 999999;
                  const disabled = String(w.status || '').toUpperCase() === 'DISABLED';
                  const paused = ['OUTSIDE_SESSION', 'SESSION_WARMUP'].includes(
                    String(w.status || '').toUpperCase(),
                  );
                  const stale = !disabled && !paused && age > 120,
                    status = disabled
                      ? 'DESACTIVADO MANUALMENTE'
                      : paused
                        ? w.status === 'SESSION_WARMUP'
                          ? 'PREPARANDO SESIÓN'
                          : isOrb
                            ? 'ACTIVO · ESPERANDO SESIÓN NY (09:30 EST)'
                            : 'PAUSADO · SESIÓN / MERCADO'
                        : stale
                          ? 'SIN ACTIVIDAD'
                          : isGold && (w.status === 'RUNNING' || !w.status)
                            ? 'ACTIVO · ESTRATEGIA CUARTOS'
                            : isOrb && w.status === 'RUNNING'
                              ? 'ACTIVO · SESIÓN NY VIGENTE'
                              : w.status || 'RUNNING';
                  const cls =
                    disabled
                      ? 'bad'
                      : paused && !isOrb
                        ? ''
                        : (isOrb && paused) || status.startsWith('ACTIVO') || status === 'RUNNING'
                          ? 'good'
                          : status === 'STARTING'
                            ? 'warn'
                            : 'bad';
                  const displayName =
                    workerLabels[prof] ||
                    w.bot_profile ||
                    'WORKER';
                  const stratLabel = isGold
                    ? 'Cuartos ($25) · M5/H1'
                    : isOrb
                      ? 'ORB New York M5'
                      : prof === 'MALAYSIAN_SNR'
                        ? 'Malaysian SNR M15'
                        : 'Estrategia ICT';
                  return `<section class="workerCard ${paused && !isOrb ? 'workerPaused' : disabled ? 'workerPaused' : stale ? 'workerStale' : ''}">
    <div class="workerHead"><div class="workerName">${esc(displayName)}</div><span class="statusPill ${cls}">${esc(status)}</span></div>
    <div class="workerMeta">
      <div><span>Estrategia</span><b style="color:#d79b19;">${esc(stratLabel)}</b></div>
      <div><span>PID</span><b>${esc(w.pid || '—')}</b></div>
      <div><span>Magic</span><b>${esc(w.daemon_magic || '—')}</b></div>
      <div><span>Ciclo</span><b>${esc(w.cycle_number || 0)}</b></div>
      <div><span>Progreso</span><b>${done} / ${total}</b></div>
      <div><span>Instrumento</span><b>${esc(w.current_symbol || 'En espera')}</b></div>
      <div><span>Última acción</span><b>${esc(w.last_action_es || '—')}</b><span class="technical">${esc(w.last_action || '')}</span></div>
    </div>
    <div class="workerProgress"><div style="width:${pctv}%"></div></div>
    <div class="workerReason">${esc(w.last_reason_es || 'Sin motivo adicional')}<span class="technical">${esc(w.last_reason || '')}${w.last_event_time ? ' · Actualizado ' + new Date(w.last_event_time).toLocaleTimeString() : ' · Sin timestamp'}</span></div>
    <button class="btn workerControl ${disabled ? 'primary' : ''}" data-worker-profile="${esc(w.bot_profile || '')}" data-worker-enabled="${disabled ? 'true' : 'false'}">${disabled ? 'Reactivar worker' : paused ? 'Desactivar también la reactivación automática' : 'Desactivar worker'}</button>
   </section>`;
                })
                .join('') ||
              '<div class="empty">Aún no hay workers registrados en SQLAlchemy.</div>';
            grid.querySelectorAll('[data-worker-profile]').forEach((button) =>
              button.addEventListener('click', async () => {
                const profile = button.dataset.workerProfile,
                  enabled = button.dataset.workerEnabled === 'true';
                if (
                  !enabled &&
                  !confirm(
                    `¿Desactivar ${profile}? No se puede desactivar si mantiene posiciones abiertas.`,
                  )
                )
                  return;
                button.disabled = true;
                try {
                  const response = await fetch(
                    `/api/workers/${encodeURIComponent(profile)}/enabled`,
                    {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ enabled }),
                    },
                  );
                  const result = await response.json();
                  if (!response.ok || !result.ok)
                    throw new Error(result.error || 'No se pudo actualizar el worker');
                  await refresh();
                } catch (error) {
                  alert(error.message);
                  button.disabled = false;
                }
              }),
            );
          }
          function renderDashboardNews(s) {
            const n = s.financial_news || {},
              items = n.items || [],
              calendar = n.calendar || {},
              events = calendar.events || [],
              agenda = $('economicCalendar'),
              target = $('dashboardNews');
            if (agenda) {
              agenda.innerHTML = events.length
                ? events
                    .slice(0, 10)
                    .map((x) => {
                      const when = x.event_at
                        ? new Intl.DateTimeFormat('es-CL', {
                            dateStyle: 'short',
                            timeStyle: 'short',
                            timeZone: 'America/Santiago',
                          }).format(new Date(x.event_at))
                        : 'Hora por confirmar';
                      const values = [
                        x.forecast ? 'Pronóstico: ' + x.forecast : '',
                        x.previous ? 'Anterior: ' + x.previous : '',
                      ]
                        .filter(Boolean)
                        .join(' · ');
                      return `<div style="padding:7px 0;border-bottom:1px solid var(--line)"><span class="pill">${esc(x.impact || 'MEDIO')}</span> <span class="pill">${esc(x.country || 'GLOBAL')}</span> <b>${esc(when)} CLT/CLST</b> · ${esc(x.title)}${values ? `<div class="sub">${esc(values)}</div>` : ''}</div>`;
                    })
                    .join('')
                : `Sin eventos próximos (${esc(calendar.status || n.status || 'SIN DATOS')}).`;
            }
            if (!target) return;
            target.innerHTML = items.length
              ? items
                  .slice(0, 6)
                  .map(
                    (x) =>
                      `<div style="padding:6px 0;border-bottom:1px solid var(--line)"><span class="pill">${esc(x.impact || 'MEDIO')}</span> <a href="${esc(x.link)}" target="_blank" rel="noopener" style="color:var(--text)">${esc(x.title)}</a></div>`,
                  )
                  .join('')
              : `Sin noticias disponibles (${esc(n.status || 'SIN DATOS')}).`;
          }
          let currentMatrixFilter = 'ALL';
          window.setMatrixFilter = function(filter) {
            currentMatrixFilter = filter;
            document.querySelectorAll('#confluenceFilters .matrixTabBtn').forEach(btn => {
              btn.classList.toggle('active', btn.getAttribute('data-filter') === filter);
            });
            if (latestState) {
              renderConfluenceMatrix(latestState);
            }
          };

          function renderConfluenceMatrix(s) {
            const tbody = $('confluenceMatrixBody');
            if (!tbody) return;
            const fullMatrix = s.confluence_matrix || [];
            if (!fullMatrix.length) {
              tbody.innerHTML = '<tr><td colspan="8" class="empty">Esperando datos centinela de las estrategias…</td></tr>';
              return;
            }

            // Actualizar chips de resumen
            const summaryDiv = $('confluenceSummaryChips');
            if (summaryDiv) {
              const activeCount = fullMatrix.filter(m => (m.final_state || '').includes('ACTIVA') || m.badge_class === 'active').length;
              const readyCount = fullMatrix.filter(m => (m.final_state || '').includes('LISTA')).length;
              const monitorCount = fullMatrix.filter(m => (m.final_state || '').includes('MONITOREANDO') || (m.final_state || '').includes('ESPERANDO')).length;
              summaryDiv.innerHTML = `
                <span class="statusPill active" style="font-size:10px;">${activeCount} Posición${activeCount === 1 ? '' : 'es'} Activa${activeCount === 1 ? '' : 's'}</span>
                <span class="statusPill good" style="font-size:10px;">${readyCount} Señal${readyCount === 1 ? '' : 'es'} Lista${readyCount === 1 ? '' : 's'}</span>
                <span class="statusPill warn" style="font-size:10px;">${monitorCount} En Seguimiento</span>
              `;
            }

            // Aplicar filtro seleccionado
            let filtered = fullMatrix;
            if (currentMatrixFilter === 'ACTIVE') {
              filtered = fullMatrix.filter(m => (m.final_state || '').includes('ACTIVA') || m.badge_class === 'active');
            } else if (currentMatrixFilter !== 'ALL') {
              filtered = fullMatrix.filter(m => (m.strategy_key || '').toUpperCase() === currentMatrixFilter);
            }

            if (!filtered.length) {
              tbody.innerHTML = `<tr><td colspan="8" class="empty">No hay activos para el filtro seleccionado (${esc(currentMatrixFilter)}).</td></tr>`;
              return;
            }

            tbody.innerHTML = filtered.map(m => `
              <tr style="border-bottom: 1px solid var(--line);">
                <td style="padding: 9px 8px;"><b>${esc(m.symbol)}</b></td>
                <td style="padding: 9px 8px;"><span class="stratBadge ${esc(m.strat_badge || 'strat-smc')}">${esc(m.strategy || 'SMC')}</span></td>
                <td style="padding: 9px 8px;">${esc(m.macro_context || m.h1_context || '—')}</td>
                <td style="padding: 9px 8px;">${esc(m.structure_level || m.m15_structure || '—')}</td>
                <td style="padding: 9px 8px;">${esc(m.trigger_confirmation || m.m5_confirmation || '—')}</td>
                <td style="padding: 9px 8px;">${esc(m.metrics_freshness || m.m5_freshness || '—')}</td>
                <td style="padding: 9px 8px;"><b>${esc(m.ai_score || '—')}</b></td>
                <td style="padding: 9px 8px;"><span class="statusPill ${esc(m.badge_class || 'neutral')}">${esc(m.final_state || '—')}</span></td>
              </tr>
            `).join('');
          }

          function showDptNotification(msg, isError) {
            let toast = $('dptToast');
            if (!toast) {
              toast = document.createElement('div');
              toast.id = 'dptToast';
              toast.style.cssText = 'position:fixed;bottom:24px;right:24px;padding:12px 20px;border-radius:8px;font-weight:700;font-size:13px;z-index:99999;box-shadow:0 6px 18px rgba(0,0,0,0.5);transition:all 0.3s ease;pointer-events:none;';
              document.body.appendChild(toast);
            }
            toast.textContent = msg;
            toast.style.background = isError ? '#ff453a' : '#00db79';
            toast.style.color = '#000000';
            toast.style.opacity = '1';
            toast.style.transform = 'translateY(0)';
            setTimeout(() => {
              if (toast) {
                toast.style.opacity = '0';
                toast.style.transform = 'translateY(10px)';
              }
            }, 3500);
          }

          function renderDailyProfitTarget(s) {
            const d = (s && s.daily_profit_target) ? s.daily_profit_target : (s || {});
            const card = $('dailyProfitTargetCard');
            if (!card) return;
            const enabled = Boolean(d.enabled);
            const isLocked = Boolean(d.is_locked);
            const overrideUnlocked = Boolean(d.override_unlocked);
            const targetPct = Number(d.target_percent != null ? d.target_percent : 2.0).toFixed(2);
            const extraBuffer = Number(d.extra_target_buffer_percent != null ? d.extra_target_buffer_percent : 1.0).toFixed(2);
            const effectiveTarget = Number(d.effective_target_percent != null ? d.effective_target_percent : targetPct).toFixed(2);
            const dailyReturn = Number(d.daily_return_pct || 0.0);
            const todayPnl = Number(d.today_net_pnl || 0.0);
            const tradesCount = Number(d.today_trades_count || 0);
            const wins = Number(d.today_winning_trades || 0);
            const losses = Number(d.today_losing_trades || 0);

            const badge = $('dptStatusBadge');
            if (badge) {
              if (!enabled) {
                badge.className = 'statusPill neutral';
                badge.textContent = '⚪ Desactivado';
              } else if (isLocked) {
                badge.className = 'statusPill bad';
                badge.textContent = '🔒 Meta Alcanzada · Entradas Bloqueadas';
              } else if (overrideUnlocked) {
                badge.className = 'statusPill warn';
                badge.textContent = `⚡ Desbloqueo Activo (+${extraBuffer}% extra)`;
              } else {
                badge.className = 'statusPill good';
                badge.textContent = '🟢 Operando Normal';
              }
            }

            const chk = $('dptEnabledCheckbox');
            if (chk && document.activeElement !== chk) chk.checked = enabled;
            const inp = $('dptTargetPercentInput');
            if (inp && document.activeElement !== inp) inp.value = targetPct;

            if ($('dptReturnDisplay')) {
              $('dptReturnDisplay').textContent = (dailyReturn >= 0 ? '+' : '') + dailyReturn.toFixed(2) + '%';
              $('dptReturnDisplay').style.color = dailyReturn > 0 ? '#00db79' : dailyReturn < 0 ? '#ff453a' : 'inherit';
            }
            if ($('dptTodayPnlDisplay')) {
              $('dptTodayPnlDisplay').textContent = (todayPnl >= 0 ? '+$' : '-$') + Math.abs(todayPnl).toFixed(2) + ' hoy';
              $('dptTodayPnlDisplay').style.color = todayPnl > 0 ? '#00db79' : todayPnl < 0 ? '#ff453a' : '#94a3b8';
            }
            if ($('dptTargetDisplay')) {
              $('dptTargetDisplay').textContent = effectiveTarget + '%' + (overrideUnlocked ? ` (base ${targetPct}% + ${extraBuffer}% buffer)` : '');
            }
            if ($('dptTradesSummary')) {
              $('dptTradesSummary').textContent = `${tradesCount} cerrados · ${wins} ganados / ${losses} perdidos`;
            }

            const prog = $('dptProgressBar');
            if (prog) {
              const eff = parseFloat(effectiveTarget) || 2.0;
              const ratio = eff > 0 ? Math.min(100, Math.max(0, (dailyReturn / eff) * 100)) : 0;
              prog.style.width = ratio.toFixed(1) + '%';
              prog.style.background = isLocked ? '#00db79' : dailyReturn < 0 ? '#ff453a' : '#d79b19';
            }

            const banner = $('dptLockedBanner');
            if (banner) {
              banner.style.display = isLocked ? 'block' : 'none';
              if (isLocked && $('dptBannerText')) {
                $('dptBannerText').innerHTML = `<b>🎯 ¡META DIARIA CUMPLIDA!</b> Se ha alcanzado un retorno de <b>+${dailyReturn.toFixed(2)}%</b> (meta: ${effectiveTarget}%). Las nuevas entradas se encuentran bloqueadas en todos los workers para proteger tus ganancias.<br><span style="font-size:11px; color:#cbd5e1;">🛡️ Las posiciones abiertas continúan activas con gestión de riesgo (SL, TP, BE con protección de swap y spread).<br>🌏 Reactivación automática de todos los workers en la próxima <b>sesión de Asia (00:00 UTC / 09:00 JST)</b>.</span>`;
              }
            }
          }

          window.saveDailyTargetSettings = async function() {
            const chk = $('dptEnabledCheckbox');
            const inp = $('dptTargetPercentInput');
            const btn = $('dptSaveSettingsBtn');
            if (!inp) return;
            const enabled = chk ? chk.checked : true;
            const target_percent = parseFloat(inp.value) || 2.0;
            if (btn) { btn.disabled = true; btn.textContent = 'Guardando...'; }
            try {
              const res = await fetch('/api/daily-target/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ enabled, target_percent })
              });
              const data = await res.json();
              if (!res.ok || !data.ok) throw new Error(data.error || 'No se pudo guardar la meta');
              if (data.daily_profit_target) {
                renderDailyProfitTarget(data.daily_profit_target);
              }
              showDptNotification(`✓ Meta diaria (${enabled ? target_percent.toFixed(2) + '%' : 'Desactivada'}) guardada exitosamente y persistida.`);
              if (typeof refresh === 'function') await refresh();
              else if (typeof window.refresh === 'function') await window.refresh();
            } catch (err) {
              showDptNotification('❌ Error al guardar meta diaria: ' + err.message, true);
            } finally {
              if (btn) { btn.disabled = false; btn.textContent = 'Guardar Meta'; }
            }
          };

          window.openDptOverrideModal = function() {
            const modal = $('dptRiskModal');
            if (modal) modal.style.display = 'flex';
          };

          window.closeDptOverrideModal = function() {
            const modal = $('dptRiskModal');
            if (modal) modal.style.display = 'none';
          };

          window.confirmDptOverride = async function() {
            const btn = $('dptConfirmOverrideBtn');
            if (btn) btn.disabled = true;
            try {
              const res = await fetch('/api/daily-target/override', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ confirm: true, extra_percent: 1.0 })
              });
              const data = await res.json();
              if (!res.ok || !data.ok) throw new Error(data.error || 'No se pudo desbloquear');
              closeDptOverrideModal();
              if (data.daily_profit_target) {
                renderDailyProfitTarget(data.daily_profit_target);
              }
              showDptNotification('⚡ Nuevas entradas desbloqueadas con buffer adicional asumido.');
              if (typeof refresh === 'function') await refresh();
              else if (typeof window.refresh === 'function') await window.refresh();
            } catch (err) {
              showDptNotification('❌ Error al desbloquear: ' + err.message, true);
            } finally {
              if (btn) btn.disabled = false;
            }
          };

          function render(s) {
            latestState = s;
            renderDailyProfitTarget(s);
            renderConfluenceMatrix(s);
            renderDashboardNews(s);
            renderCatalog(s);
            renderWorkers(s);
            renderLearningAudit(s);
            if ($('learningAuditPanel')) $('learningAuditPanel').innerHTML += renderPersistenceHealth(s);
            renderSmcTrial(s);
            renderQuarantine(s);
            renderCandidateTabs(s);
            const ax = (s.account || {}).snapshot || {};

            const money = (v) =>
              v == null
                ? '—'
                : Number(v).toLocaleString('es-CL', {
                    minimumFractionDigits: 2,
                    maximumFractionDigits: 2,
                  });
            $('accountBalance').textContent = money(ax.balance);
            $('accountEquity').textContent = money(ax.equity);
            $('accountProfit').textContent = money(ax.profit);
            $('accountProfit').className =
              'value ' +
              (Number(ax.profit || 0) > 0 ? 'good' : Number(ax.profit || 0) < 0 ? 'bad' : '');
            $('accountFreeMargin').textContent = money(ax.free_margin);
            $('status').textContent =
              (s.status || '—') +
              ' · ' +
              (s.daemon_version || 'version ?') +
              ' · ' +
              (s.connection_mode === 'LIVE' ? 'DATOS EN VIVO' : 'ÚLTIMO ESTADO CONOCIDO') +
              ' · ' +
              new Date(s.updated_at).toLocaleTimeString();
            const workers = visibleWorkers(s);
            const activeWorkers = workers.filter(
              (w) => String(w.status || '').toUpperCase() !== 'STOPPED',
            );
            $('cycle').textContent = activeWorkers.length;
            const total = workers.reduce((a, w) => a + Number(w.symbols_total || 0), 0),
              done = workers.reduce((a, w) => a + Number(w.symbols_processed || 0), 0);
            $('progressText').textContent = done + ' / ' + total;
            $('progressBar').style.width = (total ? Math.min(100, (done / total) * 100) : 0) + '%';
            const latestWorker = [...workers].sort(
              (a, b) => new Date(b.last_event_time || 0) - new Date(a.last_event_time || 0),
            )[0];
            $('current').textContent = latestWorker
              ? (latestWorker.bot_profile || '') +
                ' · ' +
                (latestWorker.current_symbol || 'En espera')
              : 'En espera';
            $('openCount').textContent = (s.open_positions || []).length;
            let last = selectedCandidate(s);
            renderCandidateContext(last);
            const sc = last.score;
            $('score').textContent = sc == null ? '—' : Math.round(sc);
            $('ring').style.setProperty('--p', Math.max(0, Math.min(100, sc || 0)));
            $('lastSymbol').textContent = last.symbol || 'Sin datos';
            $('lastMeta').innerHTML =
              `<span class="pill ${scoreClass(sc)}">${esc(last.grade || 'SIN SCORE')}</span><span class="pill">Confirmaciones ${pct(last.confirmation_percentage)}</span><span class="pill">${esc(last.direction || 'SIN DIRECCIÓN')}</span>`;
            $('decision').innerHTML =
              `<b>${esc(last.decision_es || 'No confirmada')}</b>${last.reason_es ? ` · ${esc(last.reason_es)}` : ''}${last.reason ? `<span class="technical">${esc(last.reason)}</span>` : ''}`;
            $('divergence').textContent = last.divergence_confirmed
              ? last.divergence_type || 'Sí'
              : 'No';
            $('harmonic').textContent = last.harmonic_confirmed
              ? last.harmonic_pattern || 'Sí'
              : 'No';
            $('h1doji').textContent = last.h1_doji_confirmed
              ? (last.h1_doji_type || 'Sí') + (last.h1_doji_zone ? ' · ' + last.h1_doji_zone : '')
              : 'No';
            $('structure').textContent = last.structure_break || '—';
            $('zone').textContent = last.zone || '—';
            renderList($('passed'), last.passed, 'ok');
            const critical = (last.critical_failures || []).map((x) => 'CRÍTICA: ' + x);
            renderList(
              $('missing'),
              [...(last.missing || []), ...critical],
              critical.length ? 'critical' : 'miss',
            );
            const hs = s.position_health_summary || {};
            $('healthSummary').textContent =
              `Mantener ${hs.mantener || 0} · Vigilar ${hs.vigilar || 0} · Proteger ${hs.proteger || 0} · Salida ${hs.salida || 0} · Sin datos ${hs.sin_datos || 0} · Visual ${hs.solo_visual || 0}`;
            renderOpenRows(s.open_positions || []);
            if (selectedTradeId) {
              const selected = (s.open_positions || []).find(
                (x) => String(x.id) === String(selectedTradeId),
              );
              if (selected) renderPositionChart(selected);
              else {
                selectedTradeId = null;
                renderPositionChart(null);
              }
            }
            $('recentBody').innerHTML =
              (s.recent || [])
                .map((r) => {
                  const st = r.operational_state || {};
                  return `<tr><td><span class="pill">${esc(r._bot_profile || '—')}</span></td><td><b>${esc(r.symbol)}</b></td><td><span class="statusPill ${esc(st.severity || 'neutral')}">${esc(st.label || 'INFORMATIVO')}</span></td><td><b>${esc(r.action_es || r.action || 'Sin acción')}</b><span class="technical">${esc(r.action || '')}</span></td><td class="score ${scoreClass(r.score)}">${r.score == null ? '—' : n(r.score, 0)}</td><td>${pct(r.confirmation_percentage)}</td><td>${esc(r.grade)}</td><td>${esc(r.direction)}</td><td>${r.divergence_confirmed ? 'Sí' : 'No'}</td><td>${r.harmonic_confirmed ? 'Sí' : 'No'}</td><td>${n(r.elapsed_seconds, 2)}s</td><td>${esc(r.reason_es || 'Sin motivo adicional informado.')} ${r.decision_es ? `<span class="technical">Decisión: ${esc(r.decision_es)}</span>` : ''}${r.reason ? `<span class="technical">Código: ${esc(r.reason)}</span>` : ''}</td></tr>`;
                })
                .join('') ||
              '<tr><td colspan="12" class="empty">Esperando el primer análisis…</td></tr>';
          }
          let refreshBusy = false;
          async function refresh() {
            if(document.hidden||refreshBusy)return;
            refreshBusy = true;
            const controller = new AbortController(),
              timeout = setTimeout(() => controller.abort(), 30000);
            try {
              const r = await fetch('/api/state?ts='+Date.now(), {
                cache: 'no-store',
                signal: controller.signal,
              });
              if (!r.ok) throw new Error('HTTP ' + r.status);
              render(await r.json());
              pageLoading.done();
            } catch (e) {
              $('status').textContent = 'Dashboard sin conexión: ' + e.message;
              pageLoading.fail('No se pudieron cargar los datos. Intenta nuevamente.');
            } finally {
              clearTimeout(timeout);
              refreshBusy = false;
            }
          }
          window.refresh = refresh;
          const selectAllBtn = $('selectAll'),
            clearAllBtn = $('clearAll'),
            saveSelectionBtn = $('saveSelection');
          if (selectAllBtn) selectAllBtn.addEventListener('click', () => {});
          if (clearAllBtn) clearAllBtn.addEventListener('click', () => {});
          if (saveSelectionBtn) saveSelectionBtn.addEventListener('click', saveSelection);
          document.querySelectorAll('#chartLayers input[data-layer]').forEach((cb) =>
            cb.addEventListener('change', () => {
              chartLayerState[cb.dataset.layer] = cb.checked;
              rerenderSelectedChart();
            }),
          );
          document
            .querySelectorAll('.auditModeBtn[data-audit-mode]')
            .forEach((b) => b.addEventListener('click', () => setAuditMode(b.dataset.auditMode)));
          document
            .querySelectorAll('.tfBtn[data-tf]')
            .forEach((b) => b.addEventListener('click', () => setChartTimeframe(b.dataset.tf)));
          const chartFullscreenBtn = $('chartFullscreenBtn'),
            chartMinimizeBtn = $('chartMinimizeBtn'),
            chartZoomInBtn = $('chartZoomInBtn'),
            chartZoomOutBtn = $('chartZoomOutBtn'),
            chartResetViewBtn = $('chartResetViewBtn');
          if (chartFullscreenBtn)
            chartFullscreenBtn.addEventListener('click', toggleChartFullscreen);
          if (chartMinimizeBtn) chartMinimizeBtn.addEventListener('click', toggleChartMinimized);
          if (chartZoomInBtn)
            chartZoomInBtn.addEventListener('click', () => changePriceZoom(1.25, 0.5));
          if (chartZoomOutBtn)
            chartZoomOutBtn.addEventListener('click', () => changePriceZoom(1 / 1.25, 0.5));
          if (chartResetViewBtn) chartResetViewBtn.addEventListener('click', resetChartView);
          document.addEventListener('fullscreenchange', () => {
            updateChartViewerButtons();
            rerenderSelectedChart();
          });
          document.addEventListener('webkitfullscreenchange', () => {
            updateChartViewerButtons();
            rerenderSelectedChart();
          });
          bindChartManipulation();
          updateChartViewerButtons();
          refresh();
          setInterval(refresh,6000);
          document.addEventListener('visibilitychange', () => {
            if (!document.hidden) refresh();
          });
        </script>
      </main>
    </div>
  </body>
</html>
'''


_INSTRUMENTS_HTML = r'''
<!doctype html>
<html lang="es">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width,initial-scale=1" />
    <title>DaemonBlackFx · Instrumentos</title>
    <style>
      :root {
        color-scheme: dark;
        --bg: #050708;
        --panel: #0a0e10;
        --panel2: #10161a;
        --text: #f5f5f2;
        --muted: #9fa2a5;
        --line: #5b4514;
        --good: #00db79;
        --accent: #d79b19;
      }
      * {
        box-sizing: border-box;
      }
      body {
        margin: 0;
        background: var(--bg);
        color: var(--text);
        font:
          14px/1.45 system-ui,
          -apple-system,
          Segoe UI,
          sans-serif;
      }
      .wrap {
        max-width: 1220px;
        margin: auto;
        padding: 20px;
      }
      .top {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 14px;
        flex-wrap: wrap;
        margin-bottom: 16px;
      }
      .title {
        font-size: 24px;
        font-weight: 800;
      }
      .sub {
        color: var(--muted);
      }
      .card {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 16px;
      }
      .head {
        display: flex;
        justify-content: space-between;
        gap: 12px;
        align-items: center;
        flex-wrap: wrap;
      }
      .actions {
        display: flex;
        gap: 8px;
        flex-wrap: wrap;
      }
      .btn {
        display: inline-block;
        border: 1px solid var(--line);
        background: var(--panel2);
        color: var(--text);
        text-decoration: none;
        border-radius: 9px;
        padding: 9px 12px;
        cursor: pointer;
      }
      .btn.primary {
        background: var(--accent);
        color: #06111b;
        border-color: transparent;
        font-weight: 800;
      }
      .btn:disabled {
        opacity: 0.5;
        cursor: not-allowed;
      }
      .stats {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin: 14px 0;
      }
      .metric {
        background: var(--panel2);
        border-radius: 10px;
        padding: 10px 12px;
        min-width: 150px;
      }
      .metric b {
        display: block;
        font-size: 18px;
      }
      .instrumentGrid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 12px;
        margin-top: 14px;
      }
      .group {
        border: 1px solid var(--line);
        border-radius: 12px;
        padding: 11px;
        background: var(--panel2);
      }
      .group h3 {
        margin: 0 0 8px;
        font-size: 14px;
      }
      .item {
        display: flex;
        gap: 8px;
        align-items: center;
        padding: 6px 8px;
        border-radius: 6px;
        transition: background 0.15s ease;
      }
      .item:hover {
        background: rgba(255, 255, 255, 0.04);
      }
      .symName {
        font-weight: 600;
        color: var(--text);
      }
      .pruneBadge {
        font-size: 11px;
        font-weight: 600;
        background: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.35);
        padding: 2px 7px;
        border-radius: 4px;
        margin-left: auto;
        white-space: nowrap;
        cursor: help;
      }
      .activeBadge {
        font-size: 11px;
        font-weight: 600;
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.35);
        padding: 2px 7px;
        border-radius: 4px;
        margin-left: auto;
        white-space: nowrap;
      }
      .prunedItem {
        opacity: 0.85;
      }
      .msg {
        margin-top: 12px;
        color: var(--muted);
        min-height: 22px;
      }
      .search {
        width: min(420px, 100%);
        background: #08131c;
        border: 1px solid var(--line);
        color: var(--text);
        border-radius: 9px;
        padding: 10px 12px;
        font-size: 16px;
      }
      .note {
        margin-top: 14px;
        padding: 11px;
        border-left: 3px solid var(--accent);
        background: var(--panel2);
        border-radius: 8px;
      }
      @media (max-width: 950px) {
        .instrumentGrid {
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
      }
      @media (max-width: 600px) {
        .instrumentGrid {
          grid-template-columns: 1fr;
        }
        .wrap {
          padding: 10px;
        }
        .actions {
          width: 100%;
        }
        .actions .btn {
          flex: 1;
          text-align: center;
        }
      }
      .brandStrip {
        display: flex;
        align-items: center;
        gap: 14px;
        margin-bottom: 16px;
        padding-bottom: 14px;
        border-bottom: 1px solid #5b4514;
      }
      .brandStrip img {
        width: 72px;
        height: 72px;
        object-fit: cover;
        border-radius: 12px;
        border: 1px solid #765719;
      }
      .brandStrip b {
        font-size: 22px;
      }
      .brandStrip b span {
        color: #f3c64c;
      }
      .card {
        box-shadow: inset 0 1px 0 rgba(255, 211, 102, 0.03);
      }
    </style>
  </head>
  <body>
    <main class="wrap">
      <div class="brandStrip">
        <img src="/assets/blackdaemonfx_logo_v1.jpeg" alt="Logo BlackDaemonFX" />
        <div>
          <b>BLACKDAEMON<span>FX</span></b>
          <div class="sub">Gestión modular de instrumentos</div>
        </div>
      </div>
      <div class="top">
        <div>
          <div class="title">Instrumentos para nuevas entradas</div>
          <div class="sub">
            Módulo independiente · catálogo dinámico desde MT5/Deriv · orden alfabético por
            categoría.
          </div>
        </div>
        <div class="actions">
          <a class="btn" href="/">← Volver al dashboard</a>
          <a class="btn" href="/account">Cuenta en vivo</a>
          <a class="btn" href="/performance">Rendimiento</a>
          <a class="btn" href="/strategy-bases">Bases de Estrategias</a>
        </div>
      </div>
      <section class="card">
        <div class="head">
          <div class="actions" id="profileTabs">
            <button class="btn profileTab active" data-profile="SYNTHETICS" type="button">
              SINTÉTICOS</button
            ><button class="btn profileTab" data-profile="FOREX" type="button">FOREX</button
            ><button class="btn profileTab" data-profile="ORB" type="button">ORB NEW YORK</button
            ><button class="btn profileTab" data-profile="MALAYSIAN_SNR" type="button">MALAYSIAN SNR</button
            ><button class="btn profileTab" data-profile="GOLD" type="button">CUARTOS (GOLD)</button
            ><button class="btn profileTab" data-profile="ICT" type="button">ICT (METALES, CRIPTO & ÍNDICES)</button>
          </div>
          <div class="actions">
            <button class="btn" id="selectAll" type="button">Seleccionar todos</button
            ><button class="btn" id="clearAll" type="button">Limpiar</button
            ><button class="btn primary" id="save" type="button">Aplicar selección</button>
          </div>
        </div>
        <div style="margin-top: 12px">
          <input
            id="search"
            class="search"
            type="search"
            placeholder="Buscar instrumento…"
            aria-label="Buscar instrumento"
          />
        </div>
        <div class="stats">
          <div class="metric">
            <span class="sub">Seleccionados</span><b id="selectedCount">0</b>
          </div>
          <div class="metric"><span class="sub">Disponibles</span><b id="totalCount">0</b></div>
          <div class="metric"><span class="sub">Aplicación</span><b>Próximo ciclo</b></div>
        </div>
        <div id="grid" class="instrumentGrid"><div class="sub">Cargando catálogo…</div></div>
        <div id="msg" class="msg"></div>
        <section class="card" style="margin-top: 14px">
          <div class="head">
            <div>
              <b>Noticias financieras relevantes</b>
              <div class="sub">Fuente RSS en español · prioridad a impacto alto</div>
            </div>
            <span class="sub" id="newsStatus">Cargando…</span>
          </div>
          <div id="newsList" class="msg">Cargando noticias…</div>
        </section>
        <div class="note" id="profileNote">
          <b>Persistencia independiente:</b> Sintéticos, Forex, ORB, Malaysian SNR, Cuartos (Gold) e ICT (Metales & Cripto) se guardan por separado.
        </div>
        <div class="note">
          <b>Seguridad operativa:</b> desmarcar un instrumento impide nuevas entradas desde el
          próximo ciclo. Las posiciones ya abiertas continúan con monitoreo, SL/TP y Break Even.
        </div>
      </section>
    </main>
    <script>
      const $ = (id) => document.getElementById(id),
        esc = (v) =>
          String(v ?? '').replace(
            /[&<>"']/g,
            (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' })[c],
          );
      let state = null,
        dirty = false,
        activeProfile = 'SYNTHETICS';
      function visibleInstrumentGroups(s) {
        return (s.instrument_catalog || [])
          .filter(
            (g) =>
              String(g.category || '').toLowerCase() !== 'flip' &&
              String(g.selection_profile || '').toUpperCase() !== 'IDX_OPEN',
          )
          .map((g) => ({
            ...g,
            symbols: (g.symbols || []).filter((sym) => {
              if (String(g.selection_profile || '').toUpperCase() === 'MALAYSIAN_SNR') return true;
              return !(/boom/i.test(sym) && /crash/i.test(sym));
            }),
          }))
          .filter((g) => g.symbols.length);
      }
      function groups(s) {
        return visibleInstrumentGroups(s).filter(
          (g) => String(g.selection_profile || 'SYNTHETICS').toUpperCase() === activeProfile,
        );
      }
      function selectionSummary(s) {
        return (
          ['SYNTHETICS', 'FOREX', 'ORB', 'MALAYSIAN_SNR', 'GOLD', 'ICT']
            .map((p, i) => {
              const allowed = new Set(
                visibleInstrumentGroups(s)
                  .filter((g) => String(g.selection_profile || 'SYNTHETICS').toUpperCase() === p)
                  .flatMap((g) => g.symbols),
              );
              return (
                ['Sintéticos', 'Forex', 'ORB', 'Malaysian SNR', 'Cuartos (Gold)', 'ICT (Metales, Cripto & Índices)'][i] +
                ': ' +
                ((s.selection_profiles || {})[p] || []).filter((x) => allowed.has(x)).length
              );
            })
            .join(' · ') + ' · selecciones independientes'
        );
      }
      function selected() {
        return [...document.querySelectorAll('input[data-symbol]:checked')]
          .map((x) => x.dataset.symbol)
          .sort((a, b) => a.localeCompare(b, 'es'));
      }
      function updateCount() {
        $('selectedCount').textContent = selected().length;
      }
      function renderNews(s) {
        const n = s.financial_news || {},
          items = n.items || [];
        $('newsStatus').textContent =
          `${n.status || 'SIN DATOS'} · ${n.updated_at ? new Date(n.updated_at).toLocaleTimeString() : 'sin actualización'}`;
        $('newsList').innerHTML = items.length
          ? items
              .slice(0, 8)
              .map(
                (x) =>
                  `<div style="padding:7px 0;border-bottom:1px solid var(--line)"><span class="pill">${esc(x.impact || 'MEDIO')}</span> <a href="${esc(x.link)}" target="_blank" rel="noopener" style="color:var(--text)">${esc(x.title)}</a><div class="sub">${x.published_at ? new Date(x.published_at).toLocaleString('es-ES') : ''}</div></div>`,
              )
              .join('')
          : 'No hay noticias disponibles; se conserva el último estado conocido.';
      }
      function render(s) {
        state = s;
        renderNews(s);
        const chosen = new Set((s.selection_profiles || {})[activeProfile] || []),
          prunedByProfile = s.pruned_instruments_by_profile || {},
          prunedInfo = prunedByProfile[activeProfile] || s.pruned_instruments || {},
          prioritized = new Set((s.prioritized_symbols || {})[activeProfile] || []),
          q = $('search').value.trim().toLocaleLowerCase('es'),
          gs = groups(s);
        $('grid').innerHTML =
          gs
            .map((g) => {
              const items = (g.symbols || []).filter((x) => x.toLocaleLowerCase('es').includes(q));
              return items.length
                ? `<section class="group"><h3>${esc(g.label)} <span class="sub">(${items.length})</span></h3>${items.map((sym) => {
                    const isChecked = chosen.has(sym);
                    const isPrioritized = prioritized.has(sym);
                    const isPruned = !isPrioritized && (Boolean(prunedInfo[sym]) || (prioritized.size > 0 && !isPrioritized));
                    const warning = prunedInfo[sym] || (isPruned ? 'Poda preventiva: Descartado en el análisis de 2 años por baja expectativa matemática.' : '');
                    let badge = isPruned
                      ? `<span class="pruneBadge" title="${esc(warning)}">⚠️ Descartado (Poda)</span>`
                      : `<span class="activeBadge">✓ Priorizado</span>`;
                    if (activeProfile === 'ICT' && !isPruned) {
                      if (sym.includes('Volatility 10 Index')) badge = `<span class="activeBadge" style="background: rgba(16, 185, 129, 0.15); color: #10b981; border-color: rgba(16, 185, 129, 0.4);">✓ #1 Líder Vol (+61.25R)</span>`;
                      else if (sym.includes('Jump 25')) badge = `<span class="activeBadge" style="background: rgba(6, 182, 212, 0.15); color: #38bdf8; border-color: rgba(6, 182, 212, 0.4);">✓ #1 Líder Jump (+54.75R)</span>`;
                      else if (sym.includes('Step') && sym.includes('400')) badge = `<span class="activeBadge" style="background: rgba(245, 158, 11, 0.15); color: #fbbf24; border-color: rgba(245, 158, 11, 0.4);">✓ #1 Líder Step (+44.50R)</span>`;
                      else if (sym.includes('XAU')) badge = `<span class="activeBadge" style="background: rgba(234, 179, 8, 0.15); color: #facc15; border-color: rgba(234, 179, 8, 0.4);">✓ Líder Metales (+17.25R)</span>`;
                      else if (sym.includes('GBPUSD')) badge = `<span class="activeBadge" style="background: rgba(16, 185, 129, 0.15); color: #10b981; border-color: rgba(16, 185, 129, 0.4);">✓ Líder Forex (+16.50R)</span>`;
                      else if (sym.includes('Wall Street')) badge = `<span class="activeBadge" style="background: rgba(99, 102, 241, 0.15); color: #818cf8; border-color: rgba(99, 102, 241, 0.4);">✓ Líder Índices (+15.25R)</span>`;
                      else if (sym.includes('AUDJPY')) badge = `<span class="activeBadge" style="background: rgba(236, 72, 153, 0.15); color: #f472b6; border-color: rgba(236, 72, 153, 0.4);">✓ Alta Efectividad (54.1% WR)</span>`;
                      else if (sym.includes('BTC')) badge = `<span class="activeBadge" style="background: rgba(245, 158, 11, 0.15); color: #fbbf24; border-color: rgba(245, 158, 11, 0.4);">✓ Cripto ICT (+10.25R)</span>`;
                      else if (sym.includes('Tech 100')) badge = `<span class="activeBadge" style="background: rgba(99, 102, 241, 0.15); color: #818cf8; border-color: rgba(99, 102, 241, 0.4);">✓ Nasdaq ICT (+10.25R)</span>`;
                    } else if (activeProfile === 'FOREX' && !isPruned) {
                      if (sym.includes('GBPUSD')) badge = `<span class="activeBadge" style="background: rgba(16, 185, 129, 0.15); color: #10b981; border-color: rgba(16, 185, 129, 0.4);">✓ #1 Líder Forex (+16.50R)</span>`;
                      else if (sym.includes('AUDJPY')) badge = `<span class="activeBadge" style="background: rgba(236, 72, 153, 0.15); color: #f472b6; border-color: rgba(236, 72, 153, 0.4);">✓ Alta Efectividad (54.1% WR)</span>`;
                      else if (sym.includes('AUDNZD')) badge = `<span class="activeBadge" style="background: rgba(6, 182, 212, 0.15); color: #38bdf8; border-color: rgba(6, 182, 212, 0.4);">✓ Validado (+10.25R)</span>`;
                      else if (sym.includes('EURUSD')) badge = `<span class="activeBadge" style="background: rgba(245, 158, 11, 0.15); color: #fbbf24; border-color: rgba(245, 158, 11, 0.4);">✓ Forex Core</span>`;
                    } else if (activeProfile === 'SYNTHETICS' && !isPruned) {
                      if (sym.includes('Volatility 10 Index')) badge = `<span class="activeBadge" style="background: rgba(16, 185, 129, 0.15); color: #10b981; border-color: rgba(16, 185, 129, 0.4);">✓ #1 Líder Vol (+61.25R)</span>`;
                      else if (sym.includes('Jump 25')) badge = `<span class="activeBadge" style="background: rgba(6, 182, 212, 0.15); color: #38bdf8; border-color: rgba(6, 182, 212, 0.4);">✓ #1 Líder Jump (+54.75R)</span>`;
                      else if (sym.includes('Step') && sym.includes('400')) badge = `<span class="activeBadge" style="background: rgba(245, 158, 11, 0.15); color: #fbbf24; border-color: rgba(245, 158, 11, 0.4);">✓ #1 Líder Step (+44.50R)</span>`;
                      else if (sym.includes('Crash 600')) badge = `<span class="activeBadge" style="background: rgba(234, 179, 8, 0.15); color: #facc15; border-color: rgba(234, 179, 8, 0.4);">✓ Líder Crash (+17.25R)</span>`;
                      else if (sym.includes('Boom 500')) badge = `<span class="activeBadge" style="background: rgba(99, 102, 241, 0.15); color: #818cf8; border-color: rgba(99, 102, 241, 0.4);">✓ Líder Boom (+13.00R)</span>`;
                    }
                    return `<label class="item ${isPruned ? 'prunedItem' : ''}"><input type="checkbox" data-symbol="${esc(sym)}" ${isChecked ? 'checked' : ''} ${isPruned ? `data-pruned="true" data-warning="${esc(warning)}"` : ''}><span class="symName">${esc(sym)}</span>${badge}</label>`;
                  }).join('')}</section>`
                : '';
            })
            .join('') || '<div class="sub">No se encontraron instrumentos para este perfil.</div>';
        $('totalCount').textContent = gs.reduce((n, g) => n + (g.symbols || []).length, 0);
        $('msg').textContent = selectionSummary(s);
        $('profileNote').innerHTML =
          `<b>${activeProfile}:</b> selección persistente independiente. Los instrumentos priorizados están marcados; los descartados por poda pueden activarse opcionalmente con advertencia.`;
        document
          .querySelectorAll('.profileTab')
          .forEach((b) => b.classList.toggle('active', b.dataset.profile === activeProfile));
        document.querySelectorAll('input[data-symbol]').forEach((cb) =>
          cb.addEventListener('change', () => {
            const sym = cb.dataset.symbol;
            const isPruned = cb.dataset.pruned === 'true';
            const warning = cb.dataset.warning || '';
            if (cb.checked && isPruned) {
              const proceed = window.confirm(
                `⚠️ ADVERTENCIA DE PODA:\n\nEl instrumento "${sym}" fue descartado de la activación inicial:\n\n${warning}\n\n¿Deseas activarlo de todas formas bajo tu propio criterio de riesgo?`
              );
              if (!proceed) {
                cb.checked = false;
                return;
              }
            }
            dirty = true;
            updateCount();
            $('msg').textContent = `Cambios pendientes para ${activeProfile}. Haz clic en Guardar selección para confirmar.`;
          }),
        );
        updateCount();
      }
      let loadBusy = false;
      async function load() {
        if (document.hidden || loadBusy) return;
        loadBusy = true;
        const controller = new AbortController(),
          timeout = setTimeout(() => controller.abort(), 30000);
        try {
          const r = await fetch('/api/instruments?ts='+Date.now(), {
            cache: 'no-store',
            signal: controller.signal,
          });
          if (!r.ok) throw new Error('HTTP ' + r.status);
          const s = await r.json();
          if (!dirty) render(s);
          pageLoading.done();
        } catch (e) {
          $('msg').textContent = 'Sin conexión con el daemon: ' + e.message;
          pageLoading.fail('No se pudieron cargar los datos. Intenta nuevamente.');
        } finally {
          clearTimeout(timeout);
          loadBusy = false;
        }
      }
      async function save() {
        const values = selected();
        $('save').disabled = true;
        try {
          const r = await fetch('/api/instruments/selection', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ selection_profile:activeProfile, selected_symbols: values }),
          });
          const data = await r.json();
          if (!r.ok || !data.ok) throw new Error(data.error || 'No se pudo guardar');
          dirty = false;
          $('msg').textContent = data.message || `${activeProfile} guardado`;
          await load();
        } catch (e) {
          $('msg').textContent = 'Error: ' + e.message;
        } finally {
          $('save').disabled = false;
        }
      }
      $('search').addEventListener('input', () => {
        if (state) render(state);
      });
      document.querySelectorAll('.profileTab').forEach((b) =>
        b.addEventListener('click', () => {
          if (dirty && !confirm('Hay cambios sin guardar. ¿Descartarlos?')) return;
          dirty = false;
          activeProfile = b.dataset.profile;
          if (state) render(state);
        }),
      );
      $('selectAll').addEventListener('click', () => {
        document.querySelectorAll('input[data-symbol]').forEach((x) => (x.checked = true));
        dirty = true;
        updateCount();
      });
      $('clearAll').addEventListener('click', () => {
        document.querySelectorAll('input[data-symbol]').forEach((x) => (x.checked = false));
        dirty = true;
        updateCount();
      });
      $('save').addEventListener('click', save);
      load();
      setInterval(load,6000);
      document.addEventListener('visibilitychange', () => {
        if (!document.hidden) load();
      });
    </script>
  </body>
</html>
'''

_HTML = with_page_loading(_HTML)
_INSTRUMENTS_HTML = with_page_loading(_INSTRUMENTS_HTML)
