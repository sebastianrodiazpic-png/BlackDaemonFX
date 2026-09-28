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
from dashboard.account_page import ACCOUNT_HTML
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
    "NO_M5_DATA_OR_SIGNAL": "Esperando datos o señal válida de M5",
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
    "other": "Otros",
    "orb_ny_wall_street_30": "Wall Street 30",
    "orb_ny_us_tech_100": "US Tech 100",
    "orb_ny_us_500": "S&P 500",
    "orb_ny_xauusd": "XAUUSD",
    "orb_ny_micro_xauusd": "XAUUSD Micro",
    "orb_ny_xagusd": "Plata (XAGUSD)",
    "orb_ny_micro_xagusd": "Plata Micro (XAGUSD)",
    "orb_ny_us_oil": "Petróleo (US Oil)",
    "idx_open_indices": "Apertura de Índices Bursátiles",
}

_SELECTION_PROFILES=("SYNTHETICS","FOREX","ORB","IDX_OPEN")

def _selection_profile_for_category(category: str) -> str:
    """Mapea una categoria de instrumento a su perfil de worker."""
    value=str(category or "").lower()
    if value == "forex": return "FOREX"
    if value == "idx_open_indices": return "IDX_OPEN"
    if value.startswith("orb_ny_"): return "ORB"
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
    elif rr >= 1.5:
        score += 20
        reasons.append(f"Precio avanzado a {rr:.2f}R")
    elif rr >= 1.0:
        score += 15
        reasons.append(f"Precio alcanzó zona de protección ({rr:.2f}R)")
    elif rr >= 0.5:
        score += 10
        reasons.append(f"Operación desarrolla beneficio ({rr:.2f}R)")
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
    if score >= 75:
        recommendation = "MANTENER"
    elif score >= 55:
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
        self._account_cache = {"at": now, "payload": payload}
        return payload

    def _trade_audit_detail_payload(self, trade_id, account_payload=None):
        """Detalle completo de un trade y TODOS sus snapshots Entrada vs. Ahora."""
        trade_id = int(trade_id)
        account = account_payload if account_payload is not None else _json_safe(
            build_account_payload(self.repository, source="DEMO", recent_limit=None)
        )
        trades = list(account.get("recent_trades") or [])
        trade = next(
            (
                row for row in trades
                if int(row.get("source_trade_id") or row.get("id") or -1) == trade_id
            ),
            None,
        )
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
                    source="DEMO",
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
        snapshots = list(reversed(valid_snapshots))
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
        if hasattr(self.repository, "trade_visual_audits"):
            try:
                visual_audit = next((
                    row for row in (self.repository.trade_visual_audits(source="DEMO") or [])
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
            }
        payload = _json_safe(payload)
        self._instruments_cache = {"at": now, "payload": payload}
        return payload

    def _invalidate_navigation_caches(self, *, account=False, instruments=False):
        """Descarta las caches indicadas tras un cambio de estado relevante."""
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
                if path == "/assets/blackdaemonfx_logo.jpeg":
                    logo_path = Path(__file__).resolve().parent / "assets" / "blackdaemonfx_logo.jpeg"
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
                if path in ("/account", "/account/"):
                    self._send(ACCOUNT_HTML.encode("utf-8"), "text/html; charset=utf-8")
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
            return {
                "ok": False,
                "error": "El coordinador no admite controlar workers en esta ejecución",
            }
        return self._worker_controller(profile, enabled)

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
        catalog.sort(key=lambda r: ({"SYNTHETICS":0,"FOREX":1,"ORB":2,"IDX_OPEN":3}.get(r["selection_profile"],9),r["label"].casefold()))
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
        combined=_normalize_symbol_list(selections["SYNTHETICS"]+selections["FOREX"]+selections["ORB"]+selections["IDX_OPEN"])
        with self._lock:
            self._state["instrument_catalog"]=catalog; self._state["selection_profiles"]=selections
            self._state["selection_profile_versions"]=versions; self._state["selected_symbols"]=combined
            self._state["selection_version"]=int(self._state.get("selection_version") or 0)+1
            self._state["selection_message"]=(f"Sintéticos: {len(selections['SYNTHETICS'])} · Forex: {len(selections['FOREX'])} · ORB: {len(selections['ORB'])} · Apertura Índices: {len(selections['IDX_OPEN'])} · selecciones independientes")
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
            if persisted: versions[profile]=persisted.get("version")
            combined=_normalize_symbol_list(profiles.get("SYNTHETICS",[])+profiles.get("FOREX",[])+profiles.get("ORB",[])+profiles.get("IDX_OPEN",[]))
            self._state["selection_profiles"]=profiles; self._state["selection_profile_versions"]=versions
            self._state["selected_symbols"]=combined; self._state["selection_version"]=int(self._state.get("selection_version") or 0)+1
            self._state["selection_message"]=f"{profile}: {len(requested)} instrumentos guardados de manera independiente. Se aplicará en el próximo ciclo de ese bot."
            self._state["updated_at"]=_now_iso(); self._persist_state_locked()
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

            latest = current_strategy_view
            if not latest:
                try:
                    latest = (
                        self.repository.latest_symbol_process_result(symbol, source="DEMO")
                        if hasattr(self.repository, "latest_symbol_process_result")
                        else {}
                    )
                except Exception:
                    latest = {}
            if not latest:
                latest = recent_by_symbol.get(symbol, {})

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
                "score": metadata.get("trade_score"),
                "grade": metadata.get("trade_grade"),
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
            persisted_current = (
                market.get("current_strategy_view")
                if isinstance(market.get("current_strategy_view"), dict)
                else {}
            )
            if persisted_current:
                position["latest_strategy_view"] = dict(persisted_current)
            else:
                position["latest_strategy_view"] = {
                    "decision": latest.get("decision") or latest.get("action"),
                    "state": latest.get("state") or latest.get("action"),
                    "reason": latest.get("reason"),
                    "direction": latest.get("direction"),
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

        catalog = self._state.get("instrument_catalog") or []
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
            profiles.get("SYNTHETICS", []) + profiles.get("FOREX", []) + profiles.get("ORB", []) + profiles.get("IDX_OPEN", [])
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
                            source="DEMO", limit=120, per_profile=12, scan_limit=2500,
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
            payload = _json_safe(state)
            self._dashboard_snapshot_cache = {
                "at": time.monotonic(),
                "payload": payload,
            }
            return payload


_HTML = r'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>DaemonBlackFx - Calidad en tiempo real</title>
<style>
:root{color-scheme:dark;--bg:#071018;--panel:#0d1822;--panel2:#122231;--text:#e9f1f7;--muted:#8fa2b3;--line:#233647;--good:#31c48d;--warn:#f5b942;--bad:#ef6a6a;--accent:#53a7ff}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px/1.45 system-ui,-apple-system,Segoe UI,sans-serif}.wrap{max-width:1480px;margin:auto;padding:18px}.top{display:flex;gap:16px;justify-content:space-between;align-items:center;flex-wrap:wrap;margin-bottom:16px}.title{font-size:22px;font-weight:800}.sub{color:var(--muted)}.badge{padding:7px 10px;border:1px solid var(--line);border-radius:999px;background:var(--panel)}.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:14px}.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:14px;min-width:0}.kpi{grid-column:span 3}.wide{grid-column:span 8}.side{grid-column:span 4}.full{grid-column:1/-1}.label{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.06em}.value{font-size:24px;font-weight:800;margin-top:5px}.progress{height:9px;background:#172633;border-radius:99px;overflow:hidden;margin-top:10px}.bar{height:100%;background:var(--accent);width:0;transition:width .25s}.quality{display:flex;align-items:center;gap:18px}.ring{--p:0;display:grid;place-items:center;width:126px;height:126px;border-radius:50%;background:conic-gradient(var(--good) calc(var(--p)*1%),#213241 0)}.ring:after{content:"";width:94px;height:94px;border-radius:50%;background:var(--panel);position:absolute}.ring span{position:relative;z-index:1;font-size:25px;font-weight:800}.checks{display:grid;grid-template-columns:1fr 1fr;gap:10px}.checklist{max-height:250px;overflow:auto;border:1px solid var(--line);border-radius:10px;padding:10px}.ok{color:var(--good)}.miss{color:var(--warn)}.critical{color:var(--bad)}table{width:100%;border-collapse:collapse}th,td{text-align:left;padding:9px 8px;border-bottom:1px solid var(--line);vertical-align:top}th{color:var(--muted);font-size:11px;text-transform:uppercase;position:sticky;top:0;background:var(--panel)}.tablebox{overflow:auto;max-height:440px}.score{font-weight:800}.pill{display:inline-block;padding:3px 7px;border-radius:999px;background:var(--panel2);border:1px solid var(--line);font-size:11px}.good{color:var(--good)}.warn{color:var(--warn)}.bad{color:var(--bad)}.neutral{color:var(--muted)}.statusPill{display:inline-block;padding:4px 8px;border-radius:999px;border:1px solid var(--line);font-size:11px;font-weight:800;white-space:nowrap}.statusPill.good{background:rgba(49,196,141,.10)}.statusPill.warn{background:rgba(245,185,66,.10)}.statusPill.bad{background:rgba(239,106,106,.10)}.statusPill.neutral{background:var(--panel2)}.technical{display:block;color:var(--muted);font-size:10px;margin-top:3px;font-family:ui-monospace,SFMono-Regular,Consolas,monospace}.empty{color:var(--muted);padding:20px 0}.row{display:flex;gap:10px;flex-wrap:wrap}.metric{background:var(--panel2);padding:9px 10px;border-radius:10px;min-width:110px}.metric b{display:block;margin-top:3px}.selectorHead{display:flex;justify-content:space-between;gap:12px;align-items:center;flex-wrap:wrap}.actions{display:flex;gap:8px;flex-wrap:wrap}.btn{border:1px solid var(--line);background:var(--panel2);color:var(--text);border-radius:9px;padding:8px 11px;cursor:pointer}.btn.primary{background:var(--accent);color:#06111b;border-color:transparent;font-weight:800}.profileTab.active{background:var(--accent);color:#06111b;font-weight:800}.btn:disabled{opacity:.45;cursor:not-allowed}.instrumentGrid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-top:12px}.instrumentGroup{border:1px solid var(--line);border-radius:12px;padding:10px;background:var(--panel2)}.instrumentGroup h3{margin:0 0 8px;font-size:13px}.instrumentItem{display:flex;align-items:flex-start;gap:8px;padding:5px 2px}.instrumentItem input{margin-top:3px}.selectionMsg{margin-top:10px;color:var(--muted)}@media(max-width:1100px){.instrumentGrid{grid-template-columns:repeat(2,minmax(0,1fr))}}.chartWrap{margin-top:12px;border:1px solid var(--line);border-radius:12px;background:#08131c;padding:10px;overflow:hidden}.chartSvg{width:100%;height:auto;display:block;min-height:300px}.chartHead{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;align-items:flex-start}.chartMeta{display:flex;gap:7px;flex-wrap:wrap}.chartLegend{display:flex;gap:12px;flex-wrap:wrap;margin:8px 0;color:var(--muted);font-size:12px}.dot{width:9px;height:9px;border-radius:50%;display:inline-block;margin-right:4px}.chartGrid{display:grid;grid-template-columns:1fr;gap:12px}.auditPanel{width:100%}.auditPanel{border:1px solid var(--line);border-radius:10px;background:var(--panel2);padding:11px}.auditPanel h4{margin:0 0 8px}.auditPanel #chartAudit{display:block}.auditPanel .compareGrid{grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.auditPanel .compareBox{min-height:100%}.auditList{margin:0;padding-left:18px}.auditList li{margin:4px 0}.viewBtn{white-space:nowrap}.selectedRow{background:#112536}.priceLabel{font-size:11px;font-weight:700}.layerBar{display:flex;gap:8px;flex-wrap:wrap;margin:10px 0}.layerToggle{display:flex;align-items:center;gap:6px;border:1px solid var(--line);background:var(--panel2);padding:6px 9px;border-radius:999px;cursor:pointer;font-size:12px}.layerToggle input{accent-color:var(--accent)}.compareGrid{display:grid;grid-template-columns:1fr 1fr;gap:9px;margin-bottom:10px}.compareBox{border:1px solid var(--line);border-radius:9px;padding:9px;background:#0a1620}.compareBox h5{margin:0 0 6px;font-size:12px;text-transform:uppercase;color:var(--muted)}.entryTag{font-size:11px;font-weight:700}.rsiLabel{font-size:10px;fill:#8fa2b3}@media(max-width:700px){.compareGrid{grid-template-columns:1fr}}@media(max-width:900px){.chartGrid{grid-template-columns:1fr}}@media(max-width:900px){.kpi{grid-column:span 6}.wide,.side{grid-column:1/-1}}@media(max-width:520px){.kpi{grid-column:1/-1}.checks,.instrumentGrid{grid-template-columns:1fr}.wrap{padding:10px}.value{font-size:20px}}

/* BlackDaemonFX visual identity v17 */
:root{--bg:#050708;--panel:#090d10;--panel2:#10161a;--text:#f5f5f2;--muted:#9fa5aa;--line:#5b4514;--good:#00db79;--warn:#f4b71b;--bad:#ff453a;--accent:#d79b19;--gold:#d79b19;--gold2:#f6cb57}
body{background:radial-gradient(circle at 78% 0,rgba(215,155,25,.08),transparent 28%),#050708}
.appShell{display:grid;grid-template-columns:270px minmax(0,1fr);min-height:100vh}.brandSidebar{border-right:1px solid #6b4d13;background:linear-gradient(180deg,#050708,#070b0d 65%,#090806);padding:18px 14px;display:flex;flex-direction:column;gap:14px;position:sticky;top:0;height:100vh}.brandLogo{width:100%;aspect-ratio:1/1;object-fit:cover;border-radius:14px;border:1px solid #7b5816;box-shadow:0 0 28px rgba(215,155,25,.12)}.brandName{font-size:20px;font-weight:950;letter-spacing:.05em;text-align:center}.brandName span{color:var(--gold2)}.brandTag{text-align:center;color:#c9a34a;font-size:11px;letter-spacing:.18em;text-transform:uppercase}.sideNav{display:grid;gap:7px;margin-top:4px}.sideNav a{color:#d9dde0;text-decoration:none;padding:11px 12px;border:1px solid transparent;border-radius:9px;font-weight:650}.sideNav a:hover,.sideNav a.active{background:linear-gradient(90deg,rgba(215,155,25,.24),rgba(215,155,25,.05));border-color:#6f5015;color:#ffd465}.sideStatus{margin-top:auto;border:1px solid #725116;background:#0d1214;border-radius:12px;padding:12px}.sideStatus b{color:var(--good)}.wrap{max-width:none;margin:0;padding:18px 20px 28px}.top{border-bottom:1px solid #513b12;padding-bottom:14px}.title{font-size:27px;letter-spacing:.02em}.title strong{color:var(--gold2)}.card{background:linear-gradient(145deg,#0b1013,#080b0d);border-color:#564014;box-shadow:inset 0 1px 0 rgba(255,214,111,.025)}.card:hover{border-color:#765719}.label{color:#c8a14a}.btn{border-color:#5b4514;background:#0d1215}.btn:hover{border-color:#b17e18;color:#ffd465}.btn.primary{background:linear-gradient(180deg,#f2c34b,#c58a11);color:#171000}.badge{border-color:#5b4514;background:#0c1114}.metric,.instrumentGroup,.auditPanel,.compareBox{background:#0d1215;border-color:#463711}.progress{background:#171b1d}.bar{background:linear-gradient(90deg,#9b690d,#f4c74c)}.ring{background:conic-gradient(var(--gold2) calc(var(--p)*1%),#202326 0)}.ring:after{background:#0a0e10}.pill{border-color:#4f3d14;background:#12171a}.chartWrap{background:#050809;border-color:#4f3d14}th{background:#0a0e10;color:#c6a14e}td,th{border-bottom-color:#25220f}.selectedRow{background:#18150b}.qualityKpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;grid-column:1/-1}.acctKpi{padding:16px}.acctKpi .value{font-size:26px}.acctKpi .trend{font-size:12px;margin-top:5px;color:var(--muted)}
@media(max-width:1050px){.appShell{grid-template-columns:1fr}.brandSidebar{position:relative;height:auto;display:grid;grid-template-columns:90px 1fr;align-items:center}.brandLogo{width:90px}.sideNav{grid-column:1/-1;grid-template-columns:repeat(4,1fr)}.sideStatus{display:none}.qualityKpis{grid-template-columns:repeat(2,1fr)}}
@media(max-width:620px){.sideNav{grid-template-columns:1fr 1fr}.qualityKpis{grid-template-columns:1fr}.brandSidebar{grid-template-columns:72px 1fr;padding:10px}.brandLogo{width:72px}.wrap{padding:10px}}
.workerGrid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-top:12px}.workerCard{border:1px solid #564014;border-radius:12px;background:#0d1215;padding:12px}.workerHead{display:flex;justify-content:space-between;gap:8px;align-items:center}.workerName{font-size:18px;font-weight:900;color:#f6cb57}.workerMeta{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:7px;margin-top:10px}.workerMeta div{background:#10161a;border-radius:8px;padding:7px}.workerMeta span{display:block;color:var(--muted);font-size:10px;text-transform:uppercase}.workerMeta b{display:block;margin-top:2px}.workerProgress{height:7px;background:#171b1d;border-radius:99px;overflow:hidden;margin-top:10px}.workerProgress>div{height:100%;background:linear-gradient(90deg,#9b690d,#f4c74c)}.workerReason{margin-top:8px;color:var(--muted);font-size:11px;min-height:30px}.workerControl{margin-top:10px;width:100%}.workerStale{opacity:.58}.botTabs{display:flex;gap:7px;flex-wrap:wrap;margin-top:10px}.botTab{border:1px solid #564014;background:#0d1215;color:var(--text);border-radius:999px;padding:6px 10px;cursor:pointer;font-size:11px;font-weight:800}.botTab.active{background:#d6a62d;color:#081015;border-color:#d6a62d}.candidateContext{display:flex;gap:7px;flex-wrap:wrap;margin-top:7px}@media(max-width:1100px){.workerGrid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:650px){.workerGrid{grid-template-columns:1fr}}
/* v25: visor de auditoría expandible */
.chartViewerActions{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-left:auto}.chartViewerActions .btn{display:inline-flex;align-items:center;gap:6px;font-weight:750}.chartViewerActions .icon{font-size:15px;line-height:1}.chartCollapsible{display:block}.chartCollapsed .chartCollapsible{display:none}.chartCollapsed{padding-bottom:12px}.chartCollapsed .chartHead{align-items:center}.chartCollapsed #chartSubtitle{display:none}.chartCollapsed .chartMeta{margin-top:4px}.chartCollapsed #chartMinimizeBtn .minText:after{content:"Restaurar"}.chartCollapsed #chartMinimizeBtn .minText{font-size:0}.chartCollapsed #chartMinimizeBtn .minText:after{font-size:14px}.chartCollapsed #chartMinimizeBtn .icon{transform:rotate(180deg)}
.chartFallbackFullscreen{position:fixed!important;inset:0!important;width:100vw!important;height:100vh!important;margin:0!important;border-radius:0!important;padding:16px 18px!important;background:#050708!important;overflow:auto!important;display:flex!important;flex-direction:column!important;z-index:99999}.chartFallbackFullscreen .chartCollapsible{display:flex;flex:1;min-height:0;flex-direction:column}.chartFallbackFullscreen .chartGrid{flex:1;min-height:0;grid-template-columns:1fr}.chartFallbackFullscreen .chartWrap{height:100%;min-height:0;overflow:auto}.chartFallbackFullscreen .chartSvg{width:100%;height:100%;min-height:620px}.chartFallbackFullscreen .auditPanel{overflow:auto;max-height:calc(100vh - 235px)}
#positionChartCard:fullscreen,#positionChartCard:-webkit-full-screen{width:100vw;height:100vh;max-width:none;margin:0;border-radius:0;padding:16px 18px;background:#050708;overflow:auto;display:flex;flex-direction:column;z-index:99999}#positionChartCard:fullscreen .chartCollapsible,#positionChartCard:-webkit-full-screen .chartCollapsible{display:flex;flex:1;min-height:0;flex-direction:column}#positionChartCard:fullscreen .chartGrid,#positionChartCard:-webkit-full-screen .chartGrid{flex:1;min-height:0;grid-template-columns:1fr}#positionChartCard:fullscreen .chartWrap,#positionChartCard:-webkit-full-screen .chartWrap{min-height:0;height:100%;overflow:auto}#positionChartCard:fullscreen .chartSvg,#positionChartCard:-webkit-full-screen .chartSvg{width:100%;height:100%;min-height:620px}#positionChartCard:fullscreen .auditPanel,#positionChartCard:-webkit-full-screen .auditPanel{overflow:auto;max-height:calc(100vh - 235px)}#positionChartCard:fullscreen #chartFullscreenBtn,#positionChartCard:-webkit-full-screen #chartFullscreenBtn{border-color:#b17e18;color:#ffd465}.chartFullscreenHint{display:none;color:var(--muted);font-size:11px;margin-left:4px}#positionChartCard:fullscreen .chartFullscreenHint,#positionChartCard:-webkit-full-screen .chartFullscreenHint{display:inline}
@media(max-width:900px){#positionChartCard:fullscreen .chartGrid,#positionChartCard:-webkit-full-screen .chartGrid{grid-template-columns:1fr}#positionChartCard:fullscreen .auditPanel,#positionChartCard:-webkit-full-screen .auditPanel{max-height:none}}

/* v26: controles aplicados únicamente al gráfico + navegación temporal */
.chartPlotColumn{min-width:0}.chartViewportShell{border:1px solid #4f3d14;border-radius:12px;background:#050809;overflow:hidden;min-width:0}.chartPlotToolbar{display:flex;justify-content:space-between;gap:10px;align-items:center;flex-wrap:wrap;padding:9px 10px;border-bottom:1px solid #342a12;background:#090d10}.timeframeBar,.chartNavTools{display:flex;gap:6px;align-items:center;flex-wrap:wrap}.tfBtn{min-width:44px;padding:6px 10px;font-weight:850}.tfBtn.active,.auditModeBtn.active{background:linear-gradient(180deg,#f2c34b,#c58a11);color:#171000;border-color:#d9a11d}.chartNavTools .btn{padding:6px 9px}.chartViewportShell .chartWrap{margin-top:0;border:0;border-radius:0;min-height:390px;cursor:grab;touch-action:none;user-select:none}.chartViewportShell .chartWrap.dragging{cursor:grabbing}.chartPlotCollapsed .chartWrap{display:none}.chartPlotCollapsed .chartPlotToolbar{border-bottom:0}.chartPlotCollapsed #chartMinimizeBtn .minText{font-size:0}.chartPlotCollapsed #chartMinimizeBtn .minText:after{content:"Restaurar";font-size:14px}.chartPlotCollapsed #chartMinimizeBtn .icon{transform:rotate(180deg)}.chartViewportShell:fullscreen,.chartViewportShell:-webkit-full-screen{width:100vw;height:100vh;background:#050708;border-radius:0;border:0;display:flex;flex-direction:column}.chartViewportShell:fullscreen .chartPlotToolbar,.chartViewportShell:-webkit-full-screen .chartPlotToolbar{flex:0 0 auto;padding:12px 16px}.chartViewportShell:fullscreen .chartWrap,.chartViewportShell:-webkit-full-screen .chartWrap{display:block!important;flex:1;min-height:0;height:calc(100vh - 62px);overflow:hidden}.chartViewportShell:fullscreen .chartSvg,.chartViewportShell:-webkit-full-screen .chartSvg{width:100%;height:100%;min-height:0}.chartManipHint{font-size:11px;color:var(--muted)}.chartZoomBadge{min-width:72px;text-align:center;font-variant-numeric:tabular-nums}.chartWrap.zooming{cursor:zoom-in}.chartWrap[data-zoomed="true"]{cursor:grab}.chartTfMode{font-size:11px}.chartTfMode.aux{color:var(--warn)}.chartTfMode.strategy{color:var(--good)}
</style></head><body><div class="appShell"><aside class="brandSidebar"><img class="brandLogo" src="/assets/blackdaemonfx_logo.jpeg" alt="Logo BlackDaemonFX"><div><div class="brandName">BLACKDAEMON<span>FX</span></div><div class="brandTag">Estrategia · Disciplina · Resultados</div></div><nav class="sideNav"><a class="active" href="/">▦ Dashboard</a><a href="/instruments">▥ Instrumentos</a><a href="/account">▣ Cuenta activa</a><a href="#openPositions">◈ Posiciones abiertas</a><a href="#recentAnalysis">◷ Análisis recientes</a></nav><div class="sideStatus"><b>● Daemon Online</b><div class="sub">Panel local conectado al motor</div></div></aside><main class="wrap">
<div class="top"><div><div class="title">BLACKDAEMON<strong>FX</strong> · Control operativo</div><div class="sub">ESTRATEGIA · DISCIPLINA · RESULTADOS · Dashboard en tiempo real</div></div><div class="actions"><a class="btn" href="/account">Cuenta activa</a><a class="btn" href="/instruments">Instrumentos</a><div class="badge" id="status">Conectando…</div></div></div>
<div class="grid">
<div class="qualityKpis"><div class="card acctKpi"><div class="label">Balance</div><div class="value" id="accountBalance">—</div><div class="trend">Saldo de la cuenta activa</div></div><div class="card acctKpi"><div class="label">Equity</div><div class="value" id="accountEquity">—</div><div class="trend">Capital incluyendo P&amp;L flotante</div></div><div class="card acctKpi"><div class="label">P&amp;L flotante</div><div class="value" id="accountProfit">—</div><div class="trend">Resultado de posiciones abiertas</div></div><div class="card acctKpi"><div class="label">Margen libre</div><div class="value" id="accountFreeMargin">—</div><div class="trend">Disponible para operar</div></div></div>
<div class="card kpi"><div class="label">Workers activos</div><div class="value" id="cycle">—</div><div class="sub">Familias en ejecución</div></div>
<div class="card kpi"><div class="label">Progreso agregado</div><div class="value" id="progressText">—</div><div class="progress"><div class="bar" id="progressBar"></div></div></div>
<div class="card kpi"><div class="label">Actividad más reciente</div><div class="value" id="current" style="font-size:18px">—</div></div>
<div class="card kpi"><div class="label">Operaciones abiertas</div><div class="value" id="openCount">0</div><div class="sub" id="healthSummary">Sin posiciones</div></div>
<div class="card full"><div class="label">Procesos sintéticos por familia</div><div class="sub">Cada tarjeta representa un worker independiente y su ciclo real persistido en SQLAlchemy.</div><div class="workerGrid" id="workerGrid"><div class="empty">Esperando estado de los workers…</div></div></div>
<div class="card full"><div class="selectorHead"><div><div class="label">Configuración de instrumentos</div><div class="sub">La selección para nuevas entradas fue separada del dashboard operativo.</div></div><div class="actions"><a class="btn primary" href="/instruments">Administrar instrumentos</a></div></div><div class="selectionMsg" id="selectionSummary">Cargando selección actual…</div></div>
<div class="card wide"><div class="label">Último candidato analizado · contexto por bot</div><div class="sub">Selecciona el worker cuya lectura quieres auditar. TODOS muestra el worker con actividad más reciente.</div><div class="botTabs" id="candidateBotTabs"></div><div class="candidateContext" id="candidateContext"></div><div class="quality" style="margin-top:12px"><div class="ring" id="ring"><span id="score">—</span></div><div style="flex:1;min-width:220px"><div class="value" id="lastSymbol">Sin datos</div><div class="row" id="lastMeta"></div><div style="margin-top:10px" id="decision" class="sub"></div></div></div></div>
<div class="card side"><div class="label">Confluencias</div><div class="row" style="margin-top:12px"><div class="metric"><span class="sub">Divergencia</span><b id="divergence">—</b></div><div class="metric"><span class="sub">Armónico</span><b id="harmonic">—</b></div><div class="metric"><span class="sub">Doji H1 extremo</span><b id="h1doji">—</b></div><div class="metric"><span class="sub">Estructura</span><b id="structure">—</b></div><div class="metric"><span class="sub">Zona</span><b id="zone">—</b></div></div></div>
<div class="card full"><div class="label">Confirmaciones del último candidato</div><div class="checks" style="margin-top:12px"><div><div class="sub">Cumplidas</div><div class="checklist" id="passed"></div></div><div><div class="sub">Faltantes / críticas</div><div class="checklist" id="missing"></div></div></div></div>
<div class="card full" id="openPositions"><div class="label">Salud de posiciones abiertas · telemetría por owner/worker</div><div class="sub" style="margin:4px 0 10px">La salud sólo se calcula con telemetría suficiente. Posiciones externas o inconsistentes quedan como NO EVALUABLE.</div><div class="tablebox"><table><thead><tr><th>Instrumento</th><th>Bot / Owner</th><th>Dir.</th><th>Salud</th><th>Recomendación</th><th>R actual</th><th>BE</th><th>Score entrada</th><th>Confirm.</th><th>Precio actual</th><th>Razones</th><th>Gráfico</th></tr></thead><tbody id="openBody"></tbody></table></div></div>
<div class="card full" id="positionChartCard"><div class="chartHead"><div><div class="label">Auditoría visual SMC de la posición abierta</div><div class="value" id="chartTitle" style="font-size:19px">Selecciona una posición</div><div class="sub" id="chartSubtitle">Navega M1 / M5 / M15 / H1; el gráfico usa todo el ancho y la comparación Entrada vs. Ahora queda debajo.</div></div><div class="chartMeta" id="chartMeta"></div></div><div class="chartCollapsible" id="chartCollapsible"><div class="layerBar" id="chartLayers"><label class="layerToggle"><input type="checkbox" data-layer="trade" checked>Trade / SL / TP / BE</label><label class="layerToggle"><input type="checkbox" data-layer="swings" checked>Swings HH/HL/LH/LL</label><label class="layerToggle"><input type="checkbox" data-layer="structure" checked>CHOCH / BOS</label><label class="layerToggle"><input type="checkbox" data-layer="liquidity" checked>Liquidez · BSL / SSL / Sweeps</label><label class="layerToggle"><input type="checkbox" data-layer="orderblock" checked>Order Blocks</label><label class="layerToggle"><input type="checkbox" data-layer="fvg" checked>FVG / Imbalances*</label><label class="layerToggle"><input type="checkbox" data-layer="premiumdiscount" checked>Premium / Discount</label><label class="layerToggle"><input type="checkbox" data-layer="confluence" checked>Divergencia / Doji / Armónico</label><label class="layerToggle"><input type="checkbox" data-layer="rsi" checked>RSI 14</label></div><div class="chartLegend"><span><i class="dot" style="background:#53a7ff"></i>Entrada</span><span><i class="dot" style="background:#ef6a6a"></i>SL</span><span><i class="dot" style="background:#31c48d"></i>TP</span><span><i class="dot" style="background:#f5b942"></i>BE / SL actual</span><span>△/▽ eventos · zonas sombreadas = OB/FVG · *FVG es contexto auxiliar</span></div><div class="chartGrid"><div class="chartPlotColumn"><div class="chartViewportShell" id="chartViewportShell"><div class="chartPlotToolbar"><div class="timeframeBar" id="chartTimeframes"><span class="sub">Vista</span><button type="button" class="btn auditModeBtn active" data-audit-mode="ENTRY">ENTRADA</button><button type="button" class="btn auditModeBtn" data-audit-mode="CURRENT">ACTUAL</button><span class="sub">Temporalidad</span><button type="button" class="btn tfBtn" data-tf="M1">M1</button><button type="button" class="btn tfBtn active" data-tf="M5">M5</button><button type="button" class="btn tfBtn" data-tf="M15">M15</button><button type="button" class="btn tfBtn" data-tf="H1">H1</button><span class="pill chartTfMode strategy" id="chartTfMode">ESTRATEGIA</span></div><div class="chartNavTools"><span class="chartManipHint">Scroll ↑/↓ = escala vertical · arrastrar = mover gráfico completo X/Y · Ctrl+scroll = zoom de velas · doble clic = autoescala · M1 = contexto SMC auxiliar</span><span class="pill chartZoomBadge" id="chartZoomBadge">Y 1.0× · X 1.0×</span><button type="button" class="btn" id="chartZoomOutBtn" title="Reducir escala vertical">−</button><button type="button" class="btn" id="chartZoomInBtn" title="Ampliar escala vertical">+</button><button type="button" class="btn" id="chartResetViewBtn" title="Restaurar autoescala y velas recientes">Autoescala</button><button type="button" class="btn" id="chartFullscreenBtn" title="Ampliar sólo el gráfico"><span class="icon">⛶</span><span id="chartFullscreenText">Pantalla completa</span></button><button type="button" class="btn" id="chartMinimizeBtn" title="Minimizar sólo el gráfico"><span class="icon">⌃</span><span class="minText">Minimizar</span></button></div></div><div class="chartWrap" id="chartWrap"><div class="empty">Selecciona “Ver gráfico” en una posición abierta.</div></div></div></div><aside class="auditPanel"><h4>Entrada vs. ahora</h4><div id="chartAudit" class="sub">Sin posición seleccionada.</div></aside></div></div></div>
<div class="card full" id="financialNews"><div class="label">Agenda económica y noticias financieras</div><div class="sub" style="margin:4px 0 10px">Próximos eventos macroeconómicos en horario de Chile (Santiago). Los titulares RSS se muestran en español y se priorizan por impacto.</div><div id="economicCalendar" class="sub">Cargando agenda económica…</div><div class="label" style="margin-top:14px">Titulares recientes</div><div id="dashboardNews" class="sub">Cargando noticias…</div></div><div class="card full" id="recentAnalysis"><div class="label">Análisis recientes</div><div class="sub" style="margin:4px 0 10px">Los textos principales están traducidos a lenguaje operativo. El código técnico se conserva debajo para auditoría. La vista se equilibra por worker para que ORB, FOREX y sintéticos tengan representación.</div><div class="tablebox"><table><thead><tr><th>Bot</th><th>Instrumento</th><th>Estado</th><th>Acción</th><th>Score</th><th>% confirm.</th><th>Grado</th><th>Dirección</th><th>Divergencia</th><th>Armónico</th><th>Tiempo</th><th>Motivo explicado</th></tr></thead><tbody id="recentBody"></tbody></table></div></div>
</div></div><script>
const $=id=>document.getElementById(id);const esc=v=>String(v??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function pct(v){return v==null?'—':Number(v).toFixed(1)+'%'}function n(v,d=1){return v==null?'—':Number(v).toFixed(d)}function scoreClass(v){return v>=75?'good':v>=60?'warn':'bad'}
function renderList(el,items,cls){el.innerHTML=(items&&items.length)?items.map(x=>`<div class="${cls}">${cls==='ok'?'✓':'•'} ${esc(x)}</div>`).join(''):'<div class="empty">Ninguna</div>'}
let selectionDirty=false;let lastSelectionVersion=null;
function renderCatalog(s){const summary=$('selectionSummary');if(summary){const selected=(s.selected_symbols||[]);summary.textContent=`${selected.length} instrumentos habilitados para nuevas entradas · cambios disponibles en /instruments`;return}const grid=$('instrumentGrid');if(!grid)return;}
function currentSelection(){const grid=$('instrumentGrid');if(!grid)return [];return [...grid.querySelectorAll('input[data-symbol]:checked')].map(x=>x.dataset.symbol).sort((a,b)=>a.localeCompare(b,'es'));}
async function saveSelection(){const selected=currentSelection();if(!selected.length){$('selectionMsg').textContent='Debes mantener al menos un instrumento seleccionado.';return}$('saveSelection').disabled=true;try{const r=await fetch('/api/instruments/selection',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({selected_symbols:selected})});const data=await r.json();if(!r.ok||!data.ok)throw new Error(data.error||'No se pudo guardar');selectionDirty=false;lastSelectionVersion=data.selection_version;$('selectionMsg').textContent=data.message||'Selección guardada';}catch(e){$('selectionMsg').textContent='Error: '+e.message}finally{$('saveSelection').disabled=false}}
let latestState=null;let selectedTradeId=null;let selectedCandidateBot='TODOS';
function priceFmt(v){if(v==null||!Number.isFinite(Number(v)))return '—';const x=Number(v);return Math.abs(x)>=10000?x.toFixed(2):Math.abs(x)>=100?x.toFixed(3):x.toFixed(5)}
function svgEl(tag,attrs,text=''){const a=Object.entries(attrs||{}).map(([k,v])=>`${k}="${esc(v)}"`).join(' ');return `<${tag} ${a}>${text}</${tag}>`}
const chartLayerState={trade:true,swings:true,structure:true,liquidity:true,orderblock:true,fvg:true,premiumdiscount:true,confluence:true,rsi:true};
const chartViewState={timeframe:'M5',auditMode:'ENTRY',zoom:1,offset:0,priceZoom:1,pricePan:0,dragging:false,dragStartX:0,dragStartY:0,dragStartOffset:0,dragStartPricePan:0,maxZoom:12,maxPriceZoom:20,minVisible:8};
function chartCard(){return $('chartViewportShell')}
function isChartFullscreen(){const el=chartCard();return document.fullscreenElement===el||document.webkitFullscreenElement===el}
function updateChartViewerButtons(){const full=isChartFullscreen(),shell=chartCard(),btn=$('chartFullscreenBtn'),txt=$('chartFullscreenText');if(txt)txt.textContent=full?'Salir':'Pantalla completa';if(btn)btn.setAttribute('aria-pressed',full?'true':'false');const min=$('chartMinimizeBtn');if(min)min.setAttribute('aria-expanded',shell&&!shell.classList.contains('chartPlotCollapsed')?'true':'false')}
async function toggleChartFullscreen(){const el=chartCard();if(!el)return;try{if(isChartFullscreen()){if(document.exitFullscreen)await document.exitFullscreen();else if(document.webkitExitFullscreen)document.webkitExitFullscreen()}else{el.classList.remove('chartPlotCollapsed');if(el.requestFullscreen)await el.requestFullscreen();else if(el.webkitRequestFullscreen)el.webkitRequestFullscreen()}}catch(e){console.warn('No se pudo ampliar el gráfico',e)}finally{updateChartViewerButtons()}}
function toggleChartMinimized(){const el=chartCard();if(!el)return;if(isChartFullscreen()){const exit=document.exitFullscreen||document.webkitExitFullscreen;if(exit){try{exit.call(document)}catch(e){}}}el.classList.toggle('chartPlotCollapsed');updateChartViewerButtons();if(!el.classList.contains('chartPlotCollapsed'))rerenderSelectedChart()}
function rerenderSelectedChart(){if(!selectedTradeId)return;const t=(latestState?.open_positions||[]).find(x=>String(x.id)===String(selectedTradeId));if(t)requestAnimationFrame(()=>renderPositionChart(t))}
function setAuditMode(mode){mode=String(mode||'ENTRY').toUpperCase();if(!['ENTRY','CURRENT'].includes(mode))return;chartViewState.auditMode=mode;chartViewState.zoom=1;chartViewState.offset=0;chartViewState.priceZoom=1;chartViewState.pricePan=0;document.querySelectorAll('.auditModeBtn[data-audit-mode]').forEach(b=>b.classList.toggle('active',b.dataset.auditMode===mode));rerenderSelectedChart()}
function setChartTimeframe(tf){tf=String(tf||'M5').toUpperCase();if(!['M1','M5','M15','H1'].includes(tf))return;chartViewState.timeframe=tf;chartViewState.zoom=1;chartViewState.offset=0;chartViewState.priceZoom=1;chartViewState.pricePan=0;updateChartZoomBadge();document.querySelectorAll('.tfBtn[data-tf]').forEach(b=>b.classList.toggle('active',b.dataset.tf===tf));rerenderSelectedChart()}
function updateChartZoomBadge(){const b=$('chartZoomBadge');if(b)b.textContent='Y '+chartViewState.priceZoom.toFixed(1)+'× · X '+chartViewState.zoom.toFixed(1)+'×';const w=$('chartWrap');if(w)w.dataset.zoomed=(chartViewState.zoom>1.01||chartViewState.priceZoom>1.01||Math.abs(chartViewState.pricePan)>.001)?'true':'false'}
function changeChartZoom(multiplier,anchorRatio=null){const t=(latestState?.open_positions||[]).find(x=>String(x.id)===String(selectedTradeId));const ec=t?.entry_chart||{},c=(chartViewState.auditMode==='ENTRY'&&Object.keys(ec).length)?ec:(t?.chart||{}),tf=(c.timeframes||{})[chartViewState.timeframe]||c,all=tf.candles||[],total=all.length;if(!total)return;const oldZoom=chartViewState.zoom,oldVisible=Math.max(chartViewState.minVisible,Math.min(total,Math.round(Math.min(total,80)/oldZoom))),oldMax=Math.max(0,total-oldVisible),oldOffset=Math.max(0,Math.min(oldMax,chartViewState.offset));const ratio=(anchorRatio==null)?0.5:Math.max(0,Math.min(1,anchorRatio));const oldEnd=total-oldOffset,oldStart=Math.max(0,oldEnd-oldVisible),anchorIndex=oldStart+ratio*Math.max(0,oldVisible-1);chartViewState.zoom=Math.max(1,Math.min(chartViewState.maxZoom,oldZoom*multiplier));const newVisible=Math.max(chartViewState.minVisible,Math.min(total,Math.round(Math.min(total,80)/chartViewState.zoom)));let newStart=anchorIndex-ratio*Math.max(0,newVisible-1);newStart=Math.max(0,Math.min(Math.max(0,total-newVisible),newStart));chartViewState.offset=Math.max(0,total-(newStart+newVisible));updateChartZoomBadge();rerenderSelectedChart()}
function changePriceZoom(multiplier,anchorRatioY=.5){const oldZoom=chartViewState.priceZoom,oldSpan=1/oldZoom,ratio=Math.max(0,Math.min(1,anchorRatioY==null?0.5:anchorRatioY)),anchor=chartViewState.pricePan+(0.5-ratio)*oldSpan;chartViewState.priceZoom=Math.max(1,Math.min(chartViewState.maxPriceZoom,oldZoom*multiplier));const newSpan=1/chartViewState.priceZoom;chartViewState.pricePan=anchor-(0.5-ratio)*newSpan;chartViewState.pricePan=Math.max(-3,Math.min(3,chartViewState.pricePan));updateChartZoomBadge();rerenderSelectedChart()}
function resetChartView(){chartViewState.zoom=1;chartViewState.offset=0;chartViewState.priceZoom=1;chartViewState.pricePan=0;updateChartZoomBadge();rerenderSelectedChart()}
function chartWindow(allCandles){const total=allCandles.length;if(!total)return {candles:[],start:0,end:0};const base=Math.min(total,80);const visible=Math.max(chartViewState.minVisible,Math.min(total,Math.round(base/chartViewState.zoom)));const maxOffset=Math.max(0,total-visible);chartViewState.offset=Math.max(0,Math.min(maxOffset,Math.round(chartViewState.offset)));const end=total-chartViewState.offset;const start=Math.max(0,end-visible);return {candles:allCandles.slice(start,end),start,end}}
function bindChartManipulation(){const wrap=$('chartWrap');if(!wrap||wrap.dataset.navBound==='1')return;wrap.dataset.navBound='1';wrap.addEventListener('wheel',e=>{if(!selectedTradeId)return;e.preventDefault();const rect=wrap.getBoundingClientRect();if(e.ctrlKey){const anchorX=rect.width>0?(e.clientX-rect.left)/rect.width:.5;changeChartZoom(e.deltaY<0?1.18:1/1.18,anchorX);return}const anchorY=rect.height>0?(e.clientY-rect.top)/rect.height:.5;changePriceZoom(e.deltaY<0?1.16:1/1.16,anchorY)},{passive:false});wrap.addEventListener('dblclick',e=>{if(!selectedTradeId)return;e.preventDefault();resetChartView()});wrap.addEventListener('pointerdown',e=>{if(!selectedTradeId||e.button!==0)return;chartViewState.dragging=true;chartViewState.dragStartX=e.clientX;chartViewState.dragStartY=e.clientY;chartViewState.dragStartOffset=chartViewState.offset;chartViewState.dragStartPricePan=chartViewState.pricePan;wrap.classList.add('dragging');try{wrap.setPointerCapture(e.pointerId)}catch(_){}});wrap.addEventListener('pointermove',e=>{if(!chartViewState.dragging)return;const dx=e.clientX-chartViewState.dragStartX,dy=e.clientY-chartViewState.dragStartY,width=Math.max(1,wrap.clientWidth),height=Math.max(1,wrap.clientHeight);const t=(latestState?.open_positions||[]).find(x=>String(x.id)===String(selectedTradeId));const ec=t?.entry_chart||{},c=(chartViewState.auditMode==='ENTRY'&&Object.keys(ec).length)?ec:(t?.chart||{}),tf=(c.timeframes||{})[chartViewState.timeframe]||c,all=tf.candles||[],total=all.length,baseVisible=Math.min(total,80);const visible=Math.max(chartViewState.minVisible,Math.min(total,Math.round(baseVisible/Math.max(1,chartViewState.zoom))));const pxPerCandle=width/Math.max(1,visible);const maxOffset=Math.max(0,total-visible);chartViewState.offset=Math.max(0,Math.min(maxOffset,chartViewState.dragStartOffset+dx/Math.max(1,pxPerCandle)));chartViewState.pricePan=chartViewState.dragStartPricePan+(dy/height)/Math.max(1,chartViewState.priceZoom);chartViewState.pricePan=Math.max(-3,Math.min(3,chartViewState.pricePan));updateChartZoomBadge();rerenderSelectedChart()});const stop=e=>{if(!chartViewState.dragging)return;chartViewState.dragging=false;wrap.classList.remove('dragging');if(e&&e.pointerId!=null){try{wrap.releasePointerCapture(e.pointerId)}catch(_){}}};wrap.addEventListener('pointerup',stop);wrap.addEventListener('pointercancel',stop);updateChartZoomBadge()}
function eventLayer(ev){if(ev&&ev.layer)return String(ev.layer);const t=String(ev?.type||ev||'');if(t.includes('swing'))return 'swings';if(t.includes('choch')||t.includes('bos'))return 'structure';if(t.includes('liquidity')||t.includes('sweep'))return 'liquidity';if(t.includes('order_block'))return 'orderblock';if(t.includes('fvg'))return 'fvg';return 'confluence'}
function nearestCandleIndex(candles,time,clamp=false){if(!time||!candles.length)return null;const target=new Date(time).getTime();if(!Number.isFinite(target))return null;const first=new Date(candles[0].time).getTime(),last=new Date(candles[candles.length-1].time).getTime();if(!clamp&&Number.isFinite(first)&&Number.isFinite(last)&&(target<first||target>last))return null;let best=null,dist=Infinity;candles.forEach((q,i)=>{const d=Math.abs(new Date(q.time).getTime()-target);if(d<dist){dist=d;best=i}});return best}
function chartObjectX(allCandles,win,time,plotW,padLeft){const gi=nearestCandleIndex(allCandles,time,true);if(gi==null)return null;return padLeft+((gi-win.start)+.5)*plotW/Math.max(1,win.end-win.start)}
function viewBoxHtml(title,v){const passed=(v.passed||[]).slice(0,9),missing=[...(v.missing||[]),...(v.critical_failures||[]).map(x=>'CRÍTICA: '+x)].slice(0,7),stamp=v.evaluated_at?`<div class="sub">Actualizado ${new Date(v.evaluated_at).toLocaleTimeString('es-CL')}</div>`:'';const cf=[];if(v.divergence_confirmed)cf.push('Divergencia: '+(v.divergence_type||'confirmada'));if(v.h1_doji_confirmed)cf.push('Doji H1: '+(v.h1_doji_type||'confirmado')+(v.h1_doji_zone?' · '+v.h1_doji_zone:''));if(v.harmonic_confirmed)cf.push('Armónico: '+(v.harmonic_pattern||'confirmado'));if(v.chart_pattern_confirmed)cf.push('Chartista: '+(v.chart_pattern_name||'confirmado')+' · fuerza '+(v.chart_pattern_strength==null?'—':n(Number(v.chart_pattern_strength)*100,0)+'%'));if(v.chart_pattern_conflict){const sp=v.chart_pattern_supporting_pattern,sd=v.chart_pattern_supporting_direction,ss=v.chart_pattern_supporting_strength,cp=v.chart_pattern_conflicting_pattern,cd=v.chart_pattern_conflicting_direction,cs=v.chart_pattern_conflicting_strength;cf.push('Conflicto chartista: '+(v.chart_pattern_conflict_reason||'patrones opuestos detectados'));if(sp)cf.push('A favor: '+String(sp).replaceAll('_',' ')+' · '+(sd||'—')+' · '+(ss==null?'—':n(Number(ss)*100,0)+'%'));if(cp)cf.push('En contra: '+String(cp).replaceAll('_',' ')+' · '+(cd||'—')+' · '+(cs==null?'—':n(Number(cs)*100,0)+'%'));if(v.chart_pattern_conflict_level)cf.push('Nivel conflicto: '+String(v.chart_pattern_conflict_level).replaceAll('_',' '));}return `<section class="compareBox"><h5>${esc(title)}</h5>${stamp}<div><b>${esc(v.decision||v.state||'Sin registro')}</b></div><div>${esc(v.direction||'—')} · score ${v.score==null?'—':n(v.score,0)} · ${pct(v.confirmation_percentage)}</div>${v.h1_trend?`<div>H1 ${esc(v.h1_trend)} · ${esc(v.structure_break||'—')} · ${esc(v.zone||'—')}</div>`:''}${cf.length?`<div class="warn">${cf.map(esc).join('<br>')}</div>`:''}${passed.length?`<div class="good" style="margin-top:5px">✓ ${passed.map(esc).join(' · ')}</div>`:''}${missing.length?`<div class="warn" style="margin-top:5px">• ${missing.map(esc).join(' · ')}</div>`:''}</section>`}
function mtfAuditHtml(mtf){const order=['H1','M15','M5','M1'];return `<div style="margin-top:10px"><b>Contexto SMC multi-timeframe:</b>${order.map(tf=>{const q=mtf?.[tf]||{},c=q.context||{},ev=(q.recent_events||[]).slice(-4);return `<div class="compareBox" style="margin-top:6px"><h5>${tf}</h5><div>Zona: <b>${esc(c.zone||'—')}</b> · EQ: ${priceFmt(c.equilibrium)}</div><div>Rango: ${priceFmt(c.range_low)} → ${priceFmt(c.range_high)}</div>${ev.length?`<div style="margin-top:4px">${ev.map(x=>`<span class="pill">${esc(x.label)}</span>`).join(' ')}</div>`:'<div class="sub">Sin eventos recientes publicados.</div>'}</div>`}).join('')}</div>`}
function renderPositionChart(t){
 if(!t){$('chartTitle').textContent='Selecciona una posición';$('chartSubtitle').textContent='Navega M1 / M5 / M15 / H1; el gráfico usa todo el ancho y la comparación Entrada vs. Ahora queda debajo.';$('chartMeta').innerHTML='';$('chartWrap').innerHTML='<div class="empty">Selecciona “Ver gráfico” en una posición abierta.</div>';$('chartAudit').innerHTML='Sin posición seleccionada.';return}
 const requestedEntry=chartViewState.auditMode==='ENTRY',entryChart=t.entry_chart||{},hasEntry=Object.keys(entryChart).length>0,c=(requestedEntry&&hasEntry)?entryChart:(t.chart||{}),tfMap=c.timeframes||{},tf=tfMap[chartViewState.timeframe]||c,allCandles=(tf.candles||[]),win=chartWindow(allCandles),candles=win.candles,events=(tf.events||[]),zones=(tf.zones||[]),liqLevels=(tf.levels||[]),smc=tf.smc_context||{},mtf=c.multi_timeframe||{},sv=t.latest_strategy_view||{},entryView=t.entry_strategy_view||{};
 const activeTf=tf.timeframe||chartViewState.timeframe||'M5',mode=tf.context_mode||((activeTf==='M1')?'AUXILIAR':'ESTRATEGIA');
 document.querySelectorAll('.tfBtn[data-tf]').forEach(b=>b.classList.toggle('active',b.dataset.tf===chartViewState.timeframe));const modeEl=$('chartTfMode');if(modeEl){modeEl.textContent=mode;modeEl.className='pill chartTfMode '+(mode==='AUXILIAR'?'aux':'strategy')}
 $('chartTitle').textContent=`${t.symbol} · ${t.direction} · ${t.leg||'POSICIÓN'} · ${t.owner_profile||'OWNER ?'}`;const auditLabel=(requestedEntry&&hasEntry)?'EVIDENCIA DE ENTRADA PERSISTIDA':'ESTADO ACTUAL';const auditTime=(requestedEntry&&hasEntry)?t.entry_chart_captured_at:t.visual_audit_updated_at;$('chartSubtitle').textContent=`${auditLabel} · ${activeTf} · ${mode==='AUXILIAR'?'contexto visual auxiliar':'capas SMC de estrategia'} · auditoría ${auditTime?new Date(auditTime).toLocaleTimeString():'pendiente'} · owner ${t.chart_owner_profile||t.owner_profile||'—'} · recomendación ${t.recommendation||'—'}`;$('chartMeta').innerHTML=`<span class="pill ${t.health_score==null?'neutral':scoreClass(t.health_score)}">Salud ${t.health_score==null?'N/D':n(t.health_score,0)+'/100'}</span><span class="pill">${esc(t.managed_by_daemon?'GESTIONADA':'SOLO VISUAL')}</span><span class="pill">Magic ${esc(t.owner_magic||'—')}</span><span class="pill">${esc(t.current_rr==null?'R —':n(t.current_rr,2)+'R')}</span><span class="pill">Entrada ${priceFmt(t.entry_price)}</span><span class="pill">Actual ${priceFmt(t.current_price)}</span><span class="pill">${activeTf} · ${candles.length}/${allCandles.length} velas</span>`;
 const audit=[];audit.push(`<div class="compareGrid">${viewBoxHtml('Tesis al abrir',entryView)}${viewBoxHtml('Lo que ve ahora',sv)}</div>`);audit.push(`<div><b>Recomendación:</b> <span class="${t.recommendation==='MANTENER'?'good':t.recommendation==='VIGILAR'?'warn':'bad'}">${esc(t.recommendation||'—')}</span></div>`);audit.push(`<div style="margin-top:7px"><b>Mapa SMC ${esc(activeTf)}:</b> ${events.length} eventos · ${liqLevels.length} niveles de liquidez · ${zones.filter(z=>z.layer==='orderblock').length} OB · ${zones.filter(z=>z.layer==='fvg').length} FVG</div>`);audit.push(mtfAuditHtml(mtf));audit.push(`<div style="margin-top:7px"><b>Razones de salud:</b><ul class="auditList">${(t.reasons||[]).map(x=>`<li>${esc(x)}</li>`).join('')||'<li>Sin razones suficientes.</li>'}</ul></div>`);audit.push(`<div class="sub" style="margin-top:8px">M1 es navegación auxiliar y no modifica las condiciones de entrada. M5/M15/H1 muestran las capas SMC publicadas por el pipeline cuando están disponibles.</div>`);$('chartAudit').innerHTML=audit.join('');
 if(!candles.length){$('chartWrap').innerHTML=`<div class="empty">Auditoría visual pendiente para ${esc(t.symbol)} · owner ${esc(t.owner_profile||'no identificado')}. El worker debe publicar un snapshot persistente ${esc(activeTf)}.${tf.error?' · '+esc(tf.error):''}</div>`;return}
 const W=1000,H=540,pad={l:18,r:94,t:18,b:28},rsiH=100,rsiGap=22;const priceBottom=H-pad.b-rsiH-rsiGap,priceH=priceBottom-pad.t;const lows=candles.map(x=>Number(x.low)),highs=candles.map(x=>Number(x.high));const levelVals=[t.entry_price,t.stop_loss,t.take_profit,t.current_stop_loss,t.current_price,smc.range_high,smc.range_low,smc.equilibrium].map(Number).filter(Number.isFinite);let min=Math.min(...lows,...levelVals),max=Math.max(...highs,...levelVals);let span=max-min;if(!(span>0))span=Math.max(1,Math.abs(max)*.01);min-=span*.08;max+=span*.08;const autoCenter=(min+max)/2,autoSpan=Math.max(1e-12,max-min),visibleSpan=autoSpan/Math.max(1,chartViewState.priceZoom),visibleCenter=autoCenter+chartViewState.pricePan*autoSpan;min=visibleCenter-visibleSpan/2;max=visibleCenter+visibleSpan/2;const plotW=W-pad.l-pad.r;const x=i=>pad.l+(i+.5)*plotW/candles.length;const y=v=>pad.t+(max-Number(v))/(max-min)*priceH;const cw=Math.max(2,plotW/candles.length*.55);const rsiTop=priceBottom+rsiGap,rsiY=v=>rsiTop+(100-Number(v))/100*rsiH;
 let out=`<svg class="chartSvg" viewBox="0 0 ${W} ${H}" role="img" aria-label="Auditoría SMC ${esc(activeTf)} de ${esc(t.symbol)}"><defs><clipPath id="chartPriceClip"><rect x="${pad.l}" y="${pad.t}" width="${plotW}" height="${priceH}"/></clipPath></defs>`;
 for(let i=0;i<=5;i++){const yy=pad.t+i*priceH/5,val=max-i*(max-min)/5;out+=`<line x1="${pad.l}" y1="${yy}" x2="${W-pad.r}" y2="${yy}" stroke="#18303f" stroke-width="1"/><text x="${W-pad.r+7}" y="${yy+4}" fill="#8fa2b3" font-size="11">${priceFmt(val)}</text>`}
 if(chartLayerState.premiumdiscount&&smc.premium_discount_available){const eq=Number(smc.equilibrium),rh=Number(smc.range_high),rl=Number(smc.range_low);if([eq,rh,rl].every(Number.isFinite)){const top=y(Math.min(rh,max)),mid=y(eq),bot=y(Math.max(rl,min));out+=`<rect x="${pad.l}" y="${top}" width="${plotW}" height="${Math.max(0,mid-top)}" fill="#ef6a6a" opacity=".035"/><rect x="${pad.l}" y="${mid}" width="${plotW}" height="${Math.max(0,bot-mid)}" fill="#31c48d" opacity=".035"/><line x1="${pad.l}" y1="${mid}" x2="${W-pad.r}" y2="${mid}" stroke="#d6a62d" stroke-width="1" stroke-dasharray="5 5" opacity=".7"/><text x="${W-pad.r-58}" y="${Math.max(pad.t+11,top+12)}" fill="#ef9d9d" font-size="10">PREMIUM</text><text x="${W-pad.r-62}" y="${Math.min(priceBottom-4,bot-5)}" fill="#8dd8bc" font-size="10">DISCOUNT</text><text x="${W-pad.r-42}" y="${mid-4}" fill="#d6a62d" font-size="10">EQ 50%</text>`}}
 zones.filter(z=>chartLayerState[z.layer]).forEach(z=>{const xx=chartObjectX(allCandles,win,z.time,plotW,pad.l);if(xx==null)return;const lo=Number(z.low),hi=Number(z.high);if(!Number.isFinite(lo)||!Number.isFinite(hi))return;const yy1=y(hi),yy2=y(lo),zoneTop=Math.min(yy1,yy2),zoneHeight=Math.max(2,Math.abs(yy2-yy1)),zoneRight=W-pad.r,w=zoneRight-xx;if(w<=0)return;const bullish=z.direction==='BUY',col=z.layer==='fvg'?(bullish?'#7c6cff':'#bb6cff'):(bullish?'#31c48d':'#ef6a6a'),opacity=z.status==='INVALIDADA'||z.status==='RELLENADA'?'.035':'.10',zoneName=z.layer==='fvg'?'FVG':'OB';out+=`<g clip-path="url(#chartPriceClip)"><rect x="${xx}" y="${zoneTop}" width="${w}" height="${zoneHeight}" fill="${col}" opacity="${opacity}" stroke="${col}" stroke-width=".7" stroke-dasharray="${z.layer==='fvg'?'4 3':'0'}"><title>${esc(z.label)} · ${esc(z.status||'')}</title></rect><text class="zoneChartLabel" x="${xx+6}" y="${zoneTop+12}" fill="${col}" font-size="9" font-weight="700">${esc(zoneName)} ${esc(z.status||'')}</text></g>`});
 liqLevels.filter(()=>chartLayerState.liquidity).forEach(l=>{const xx=chartObjectX(allCandles,win,l.time,plotW,pad.l),pv=Number(l.price);if(xx==null||!Number.isFinite(pv))return;const yy=y(pv),col=l.type==='buy_side_liquidity'?'#f5b942':'#53a7ff';if(xx>=W-pad.r)return;out+=`<g clip-path="url(#chartPriceClip)"><line x1="${xx}" y1="${yy}" x2="${W-pad.r}" y2="${yy}" stroke="${col}" stroke-width="1" stroke-dasharray="2 5" opacity=".65"><title>${esc(l.label)}</title></line><text x="${xx+5}" y="${yy-4}" fill="${col}" font-size="9">${l.type==='buy_side_liquidity'?'BSL':'SSL'}</text></g>`});
 candles.forEach((q,i)=>{const xx=x(i),yo=y(q.open),yc=y(q.close),yh=y(q.high),yl=y(q.low),up=Number(q.close)>=Number(q.open),col=up?'#31c48d':'#ef6a6a';out+=`<line x1="${xx}" y1="${yh}" x2="${xx}" y2="${yl}" stroke="${col}" stroke-width="1.2"/>`;out+=`<rect x="${xx-cw/2}" y="${Math.min(yo,yc)}" width="${cw}" height="${Math.max(1,Math.abs(yc-yo))}" fill="${col}" opacity=".88"/>`});
 if(chartLayerState.trade){const tradeLevels=[['Entrada',t.entry_price,'#53a7ff'],['SL',t.stop_loss,'#ef6a6a'],['TP',t.take_profit,'#31c48d'],['SL actual / BE',t.current_stop_loss,'#f5b942'],['Precio',t.current_price,'#d7e5ef']];tradeLevels.forEach(([lab,val,col])=>{val=Number(val);if(!Number.isFinite(val))return;const yy=y(val);out+=`<line x1="${pad.l}" y1="${yy}" x2="${W-pad.r}" y2="${yy}" stroke="${col}" stroke-width="1.5" stroke-dasharray="6 5" opacity=".9"/><text class="priceLabel" x="${pad.l+5}" y="${yy-4}" fill="${col}">${esc(lab)} ${priceFmt(val)}</text>`});const ei=nearestCandleIndex(candles,t.entry_time);if(ei!=null){const ex=x(ei);out+=`<line x1="${ex}" y1="${pad.t}" x2="${ex}" y2="${priceBottom}" stroke="#53a7ff" stroke-width="1.5" stroke-dasharray="3 4" opacity=".85"/><text class="entryTag" x="${Math.min(ex+5,W-pad.r-170)}" y="${pad.t+14}" fill="#53a7ff">ENTRADA · ${entryView.score==null?'score —':'score '+n(entryView.score,0)} · ${pct(entryView.confirmation_percentage)}</text>`}}
 const timeIndex=new Map(candles.map((q,i)=>[String(q.time).slice(0,16),i]));events.filter(e=>chartLayerState[eventLayer(e)]).forEach(e=>{let i=timeIndex.get(String(e.time).slice(0,16));if(i==null)return;const xx=x(i),py=y(e.price!=null?e.price:(e.direction==='BUY'?candles[i].low:candles[i].high)),bull=e.direction==='BUY';if(e.layer==='swings'){const col=bull?'#80bfff':'#ffd36b',dy=bull?15:-7;out+=`<text x="${xx}" y="${py+dy}" text-anchor="middle" fill="${col}" font-size="9" font-weight="800"><title>${esc(e.label)}</title>${esc(e.label)}</text>`;return}const col=bull?'#53a7ff':'#f5b942',pts=bull?`${xx},${py-13} ${xx-6},${py-3} ${xx+6},${py-3}`:`${xx},${py+13} ${xx-6},${py+3} ${xx+6},${py+3}`;out+=`<polygon points="${pts}" fill="${col}"><title>${esc(e.label)}</title></polygon>`});
 if(chartLayerState.confluence){const ei=nearestCandleIndex(candles,t.entry_time);if(ei!=null){let ty=pad.t+31;const con=[];if(entryView.divergence_confirmed)con.push('DIV RSI');if(entryView.h1_doji_confirmed)con.push('DOJI H1');if(entryView.harmonic_confirmed)con.push('ARMÓNICO');if(entryView.chart_pattern_confirmed)con.push('PATRÓN '+String(entryView.chart_pattern_name||'CHARTISTA').replaceAll('_',' '));con.forEach(label=>{out+=`<text x="${Math.min(x(ei)+5,W-pad.r-100)}" y="${ty}" fill="#f5b942" font-size="10" font-weight="700">+ ${esc(label)}</text>`;ty+=13})}if(entryView.h1_doji_confirmed&&entryView.h1_doji_time){const di=nearestCandleIndex(candles,entryView.h1_doji_time);if(di!=null){const xx=x(di),py=y(candles[di].low);out+=`<circle cx="${xx}" cy="${py+11}" r="5" fill="#f5b942"><title>${esc(entryView.h1_doji_type||'Doji H1 en extremo')}</title></circle>`}}}
 if(chartLayerState.confluence&&entryView.chart_pattern_confirmed){const pe=entryView.chart_pattern_evidence||{},anchors=pe.anchors||[],pts=[];anchors.forEach(a=>{const ai=nearestCandleIndex(candles,a.time),pv=Number(a.price);if(ai==null||!Number.isFinite(pv))return;pts.push([x(ai),y(pv)]);out+=`<circle cx="${x(ai)}" cy="${y(pv)}" r="5" fill="none" stroke="#f5b942" stroke-width="2"><title>${esc(pe.pattern||entryView.chart_pattern_name||'Patrón chartista')}</title></circle>`});if(pts.length>1)out+=`<polyline points="${pts.map(p=>p.join(',')).join(' ')}" fill="none" stroke="#f5b942" stroke-width="1.6" stroke-dasharray="5 4" opacity=".9"/>`;if(pts.length)out+=`<text x="${Math.min(pts[pts.length-1][0]+7,W-pad.r-220)}" y="${Math.max(pad.t+15,pts[pts.length-1][1]-8)}" fill="#f5b942" font-size="10" font-weight="800">${esc(String(pe.pattern||entryView.chart_pattern_name||'PATRÓN').replaceAll('_',' '))}</text>`}
 if(chartLayerState.rsi){[30,50,70].forEach(v=>{const yy=rsiY(v);out+=`<line x1="${pad.l}" y1="${yy}" x2="${W-pad.r}" y2="${yy}" stroke="${v===50?'#294052':'#523d28'}" stroke-width="1" stroke-dasharray="4 4"/><text class="rsiLabel" x="${W-pad.r+7}" y="${yy+3}">RSI ${v}</text>`});let pts=[];candles.forEach((q,i)=>{const rv=Number(q.rsi14);if(Number.isFinite(rv))pts.push(`${x(i)},${rsiY(rv)}`)});if(pts.length>1)out+=`<polyline points="${pts.join(' ')}" fill="none" stroke="#b6c9d7" stroke-width="1.6"/><text x="${pad.l+4}" y="${rsiTop+12}" fill="#8fa2b3" font-size="11">RSI 14 · evidencia visual para divergencias</text>`}
 const ticks=[0,Math.floor((candles.length-1)/2),candles.length-1];ticks.forEach(i=>{const d=new Date(candles[i].time);out+=`<text x="${x(i)}" y="${H-7}" text-anchor="middle" fill="#8fa2b3" font-size="11">${d.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'})}</text>`});out+='</svg>';$('chartWrap').innerHTML=out
}
function selectTrade(id){selectedTradeId=String(id);const t=(latestState?.open_positions||[]).find(x=>String(x.id)===selectedTradeId);renderPositionChart(t);renderOpenRows(latestState?.open_positions||[])}
function renderOpenRows(rows){
 $('openBody').innerHTML=(rows||[]).map(t=>{
   const rec=t.recommendation||'SIN DATOS';
   const cls=rec==='MANTENER'?'good':rec==='VIGILAR'?'warn':rec==='SIN VALIDACIÓN EN VIVO'||rec==='SIN TELEMETRÍA DEL WORKER'||rec==='WORKER SIN ACTIVIDAD'?'neutral':'bad';
   const rs=(t.reasons||[]).slice(0,5).map(x=>`• ${esc(x)}`).join('<br>');
   const sel=String(t.id)===String(selectedTradeId)?'selectedRow':'';
   const persisted=t.persistence_status==='PERSISTED'?'<span class="statusPill warn">PERSISTIDA · SIN CONEXIÓN</span>':'<span class="statusPill good">EN VIVO</span>';
   const health=t.health_score==null?'—':n(t.health_score,0)+'/100';
   const owner=t.owner_profile||'NO IDENTIFICADO';
   const ownerStatus=t.ownership_status||'—';
   const ownerCls=t.managed_by_daemon?'good':'warn';
   const chartAvailable=t.chart&&Object.keys(t.chart).length;
   return `<tr class="${sel}">
    <td><b>${esc(t.symbol)}</b><br><span class="sub">${esc(t.execution_mode)} · ${esc(t.leg)}</span><br>${persisted}<span class="technical">${esc(t.broker_verification)}</span></td>
    <td><b class="${ownerCls}">${esc(owner)}</b><br><span class="technical">Magic ${esc(t.owner_magic||'—')} · ${esc(ownerStatus)}</span><br><span class="technical">Worker ${esc(t.worker_status||'—')}${t.worker_pid?' · PID '+esc(t.worker_pid):''}</span></td>
    <td>${esc(t.direction)}</td>
    <td class="score ${t.health_score==null?'neutral':scoreClass(t.health_score)}">${health}<br><span class="pill">${esc(t.health_grade||'—')}</span></td>
    <td class="${cls}"><b>${esc(rec)}</b></td>
    <td>${t.current_rr==null?'—':n(t.current_rr,2)+'R'}</td>
    <td class="${t.break_even_confirmed?'good':'warn'}">${t.break_even_confirmed?'ACTIVO':'Pendiente'}</td>
    <td>${esc(t.quality_score)}</td>
    <td>${pct(t.confirmation_percentage)}</td>
    <td>${esc(t.current_price)}</td>
    <td class="sub">${rs||'Sin razones suficientes todavía'}</td>
    <td><button type="button" class="btn viewBtn" data-trade-id="${esc(t.id)}">${chartAvailable?'Ver gráfico':'Esperando gráfico'}</button></td>
   </tr>`;
 }).join('')||'<tr><td colspan="12" class="empty">No hay operaciones abiertas registradas</td></tr>';
 $('openBody').querySelectorAll('button[data-trade-id]').forEach(b=>b.addEventListener('click',()=>selectTrade(b.dataset.tradeId)));
}
function candidateFromWorker(worker){
 if(!worker)return {};
 const details=worker.details||{},result=(details.result&&typeof details.result==='object')?details.result:{};
 return {...result,symbol:worker.current_symbol||result.symbol,_worker_profile:worker.bot_profile,_worker_magic:worker.daemon_magic,_worker_cycle:worker.cycle_number,_worker_time:worker.last_event_time,_worker_action:worker.last_action};
}
function renderCandidateTabs(s){
 const workers=s.worker_states||[],profiles=['TODOS',...workers.map(w=>String(w.bot_profile||'').toUpperCase()).filter(Boolean)];
 const unique=[...new Set(profiles)];
 if(!unique.includes(selectedCandidateBot))selectedCandidateBot='TODOS';
 const box=$('candidateBotTabs');if(!box)return;
 box.innerHTML=unique.map(p=>`<button type="button" class="botTab ${p===selectedCandidateBot?'active':''}" data-bot="${esc(p)}">${esc(p)}</button>`).join('');
 box.querySelectorAll('button[data-bot]').forEach(b=>b.addEventListener('click',()=>{selectedCandidateBot=b.dataset.bot;render(latestState)}));
}
function selectedCandidate(s){
 const workers=s.worker_states||[];
 if(!workers.length)return {};
 let worker=null;
 if(selectedCandidateBot==='TODOS'){
   worker=[...workers].sort((a,b)=>new Date(b.last_event_time||0)-new Date(a.last_event_time||0))[0];
 }else{
   worker=workers.find(w=>String(w.bot_profile||'').toUpperCase()===selectedCandidateBot);
 }
 return candidateFromWorker(worker);
}
function renderCandidateContext(last){
 const box=$('candidateContext');if(!box)return;
 if(!last||!last._worker_profile){box.innerHTML='<span class="pill">Sin worker seleccionado</span>';return}
 box.innerHTML=`<span class="pill good">BOT ${esc(last._worker_profile)}</span><span class="pill">Magic ${esc(last._worker_magic||'—')}</span><span class="pill">Ciclo ${esc(last._worker_cycle||0)}</span><span class="pill">${esc(last._worker_action||'En espera')}</span><span class="pill">${last._worker_time?'Actualizado '+new Date(last._worker_time).toLocaleTimeString():'Sin timestamp'}</span>`;
}
function renderWorkers(s){
 const rows=(s.worker_states||[]),grid=$('workerGrid');if(!grid)return;
 const order=['BOOM','CRASH','VOLATILITY','STEP','JUMP','FLIP','FOREX','ORB','IDX_OPEN'];
 const workerLabels={'IDX_OPEN':'Apertura Bursátiles'};
 const now=Date.now();
 const sorted=[...rows].sort((a,b)=>{const ai=order.indexOf(String(a.bot_profile||'').toUpperCase()),bi=order.indexOf(String(b.bot_profile||'').toUpperCase());return (ai<0?99:ai)-(bi<0?99:bi)});
 grid.innerHTML=sorted.map(w=>{
   const total=Number(w.symbols_total||0),done=Number(w.symbols_processed||0),pctv=total?Math.min(100,done/total*100):0;
   const age=w.last_event_time?Math.max(0,(now-new Date(w.last_event_time).getTime())/1000):999999;
   const disabled=String(w.status||'').toUpperCase()==='DISABLED';
   const stale=!disabled&&age>120,status=disabled?'DISABLED':(stale?'SIN ACTIVIDAD':(w.status||'RUNNING'));
   const cls=status==='RUNNING'?'good':status==='STARTING'?'warn':'bad';
   const displayName=workerLabels[String(w.bot_profile||'').toUpperCase()]||(w.bot_profile||'WORKER');
   return `<section class="workerCard ${stale?'workerStale':''}">
    <div class="workerHead"><div class="workerName">${esc(displayName)}</div><span class="statusPill ${cls}">${esc(status)}</span></div>
    <div class="workerMeta">
      <div><span>PID</span><b>${esc(w.pid||'—')}</b></div>
      <div><span>Magic</span><b>${esc(w.daemon_magic||'—')}</b></div>
      <div><span>Ciclo</span><b>${esc(w.cycle_number||0)}</b></div>
      <div><span>Progreso</span><b>${done} / ${total}</b></div>
      <div><span>Instrumento</span><b>${esc(w.current_symbol||'En espera')}</b></div>
      <div><span>Última acción</span><b>${esc(w.last_action_es||'—')}</b><span class="technical">${esc(w.last_action||'')}</span></div>
    </div>
    <div class="workerProgress"><div style="width:${pctv}%"></div></div>
    <div class="workerReason">${esc(w.last_reason_es||'Sin motivo adicional')}<span class="technical">${esc(w.last_reason||'')}${w.last_event_time?' · Actualizado '+new Date(w.last_event_time).toLocaleTimeString():' · Sin timestamp'}</span></div>
    <button class="btn workerControl ${disabled?'primary':''}" data-worker-profile="${esc(w.bot_profile||'')}" data-worker-enabled="${disabled?'true':'false'}">${disabled?'Reactivar worker':'Desactivar worker'}</button>
   </section>`}).join('')||'<div class="empty">Aún no hay workers registrados en SQLAlchemy.</div>';
  grid.querySelectorAll('[data-worker-profile]').forEach(button=>button.addEventListener('click',async()=>{const profile=button.dataset.workerProfile,enabled=button.dataset.workerEnabled==='true';if(!enabled&&!confirm(`¿Desactivar ${profile}? No se puede desactivar si mantiene posiciones abiertas.`))return;button.disabled=true;try{const response=await fetch(`/api/workers/${encodeURIComponent(profile)}/enabled`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled})});const result=await response.json();if(!response.ok||!result.ok)throw new Error(result.error||'No se pudo actualizar el worker');await refresh();}catch(error){alert(error.message);button.disabled=false;}}));
}
function renderDashboardNews(s){const n=s.financial_news||{},items=n.items||[],calendar=(n.calendar||{}),events=calendar.events||[],agenda=$('economicCalendar'),target=$('dashboardNews');if(agenda){agenda.innerHTML=events.length?events.slice(0,10).map(x=>{const when=x.event_at?new Intl.DateTimeFormat('es-CL',{dateStyle:'short',timeStyle:'short',timeZone:'America/Santiago'}).format(new Date(x.event_at)):'Hora por confirmar';const values=[x.forecast?'Pronóstico: '+x.forecast:'',x.previous?'Anterior: '+x.previous:''].filter(Boolean).join(' · ');return `<div style="padding:7px 0;border-bottom:1px solid var(--line)"><span class="pill">${esc(x.impact||'MEDIO')}</span> <span class="pill">${esc(x.country||'GLOBAL')}</span> <b>${esc(when)} CLT/CLST</b> · ${esc(x.title)}${values?`<div class="sub">${esc(values)}</div>`:''}</div>`}).join(''):`Sin eventos próximos (${esc(calendar.status||n.status||'SIN DATOS')}).`;}if(!target)return;target.innerHTML=items.length?items.slice(0,6).map(x=>`<div style="padding:6px 0;border-bottom:1px solid var(--line)"><span class="pill">${esc(x.impact||'MEDIO')}</span> <a href="${esc(x.link)}" target="_blank" rel="noopener" style="color:var(--text)">${esc(x.title)}</a></div>`).join(''):`Sin noticias disponibles (${esc(n.status||'SIN DATOS')}).`}
function render(s){latestState=s;renderDashboardNews(s);renderCatalog(s);renderWorkers(s);renderCandidateTabs(s);const ax=(s.account||{}).snapshot||{};const money=v=>v==null?'—':Number(v).toLocaleString('es-CL',{minimumFractionDigits:2,maximumFractionDigits:2});$('accountBalance').textContent=money(ax.balance);$('accountEquity').textContent=money(ax.equity);$('accountProfit').textContent=money(ax.profit);$('accountProfit').className='value '+(Number(ax.profit||0)>0?'good':Number(ax.profit||0)<0?'bad':'');$('accountFreeMargin').textContent=money(ax.free_margin);$('status').textContent=(s.status||'—')+' · '+(s.daemon_version||'version ?')+' · '+(s.connection_mode==='LIVE'?'DATOS EN VIVO':'ÚLTIMO ESTADO CONOCIDO')+' · '+new Date(s.updated_at).toLocaleTimeString();const workers=s.worker_states||[];const activeWorkers=workers.filter(w=>String(w.status||'').toUpperCase()!=='STOPPED');$('cycle').textContent=activeWorkers.length;const total=workers.reduce((a,w)=>a+Number(w.symbols_total||0),0),done=workers.reduce((a,w)=>a+Number(w.symbols_processed||0),0);$('progressText').textContent=done+' / '+total;$('progressBar').style.width=(total?Math.min(100,done/total*100):0)+'%';const latestWorker=[...workers].sort((a,b)=>new Date(b.last_event_time||0)-new Date(a.last_event_time||0))[0];$('current').textContent=latestWorker?((latestWorker.bot_profile||'')+' · '+(latestWorker.current_symbol||'En espera')):'En espera';$('openCount').textContent=(s.open_positions||[]).length;let last=selectedCandidate(s);renderCandidateContext(last);const sc=last.score;$('score').textContent=sc==null?'—':Math.round(sc);$('ring').style.setProperty('--p',Math.max(0,Math.min(100,sc||0)));$('lastSymbol').textContent=last.symbol||'Sin datos';$('lastMeta').innerHTML=`<span class="pill ${scoreClass(sc)}">${esc(last.grade||'SIN SCORE')}</span><span class="pill">Confirmaciones ${pct(last.confirmation_percentage)}</span><span class="pill">${esc(last.direction||'SIN DIRECCIÓN')}</span>`;$('decision').innerHTML=`<b>${esc(last.decision_es||'No confirmada')}</b>${last.reason_es?` · ${esc(last.reason_es)}`:''}${last.reason?`<span class="technical">${esc(last.reason)}</span>`:''}`;$('divergence').textContent=last.divergence_confirmed?(last.divergence_type||'Sí'):'No';$('harmonic').textContent=last.harmonic_confirmed?(last.harmonic_pattern||'Sí'):'No';$('h1doji').textContent=last.h1_doji_confirmed?((last.h1_doji_type||'Sí')+(last.h1_doji_zone?' · '+last.h1_doji_zone:'')):'No';$('structure').textContent=last.structure_break||'—';$('zone').textContent=last.zone||'—';renderList($('passed'),last.passed,'ok');const critical=(last.critical_failures||[]).map(x=>'CRÍTICA: '+x);renderList($('missing'),[...(last.missing||[]),...critical],critical.length?'critical':'miss');
const hs=s.position_health_summary||{};$('healthSummary').textContent=`Mantener ${hs.mantener||0} · Vigilar ${hs.vigilar||0} · Proteger ${hs.proteger||0} · Salida ${hs.salida||0} · Sin datos ${hs.sin_datos||0} · Visual ${hs.solo_visual||0}`;
renderOpenRows(s.open_positions||[]);if(selectedTradeId){const selected=(s.open_positions||[]).find(x=>String(x.id)===String(selectedTradeId));if(selected)renderPositionChart(selected);else{selectedTradeId=null;renderPositionChart(null)}}
$('recentBody').innerHTML=(s.recent||[]).map(r=>{const st=r.operational_state||{};return `<tr><td><span class="pill">${esc(r._bot_profile||'—')}</span></td><td><b>${esc(r.symbol)}</b></td><td><span class="statusPill ${esc(st.severity||'neutral')}">${esc(st.label||'INFORMATIVO')}</span></td><td><b>${esc(r.action_es||r.action||'Sin acción')}</b><span class="technical">${esc(r.action||'')}</span></td><td class="score ${scoreClass(r.score)}">${r.score==null?'—':n(r.score,0)}</td><td>${pct(r.confirmation_percentage)}</td><td>${esc(r.grade)}</td><td>${esc(r.direction)}</td><td>${r.divergence_confirmed?'Sí':'No'}</td><td>${r.harmonic_confirmed?'Sí':'No'}</td><td>${n(r.elapsed_seconds,2)}s</td><td>${esc(r.reason_es||'Sin motivo adicional informado.')} ${r.decision_es?`<span class="technical">Decisión: ${esc(r.decision_es)}</span>`:''}${r.reason?`<span class="technical">Código: ${esc(r.reason)}</span>`:''}</td></tr>`}).join('')||'<tr><td colspan="12" class="empty">Esperando el primer análisis…</td></tr>'}
async function refresh(){if(document.hidden)return;try{const r=await fetch('/api/state?ts='+Date.now(),{cache:'no-store'});if(!r.ok)throw new Error('HTTP '+r.status);render(await r.json())}catch(e){$('status').textContent='Dashboard sin conexión: '+e.message}}const selectAllBtn=$('selectAll'),clearAllBtn=$('clearAll'),saveSelectionBtn=$('saveSelection');if(selectAllBtn)selectAllBtn.addEventListener('click',()=>{});if(clearAllBtn)clearAllBtn.addEventListener('click',()=>{});if(saveSelectionBtn)saveSelectionBtn.addEventListener('click',saveSelection);document.querySelectorAll('#chartLayers input[data-layer]').forEach(cb=>cb.addEventListener('change',()=>{chartLayerState[cb.dataset.layer]=cb.checked;rerenderSelectedChart()}));document.querySelectorAll('.auditModeBtn[data-audit-mode]').forEach(b=>b.addEventListener('click',()=>setAuditMode(b.dataset.auditMode)));document.querySelectorAll('.tfBtn[data-tf]').forEach(b=>b.addEventListener('click',()=>setChartTimeframe(b.dataset.tf)));const chartFullscreenBtn=$('chartFullscreenBtn'),chartMinimizeBtn=$('chartMinimizeBtn'),chartZoomInBtn=$('chartZoomInBtn'),chartZoomOutBtn=$('chartZoomOutBtn'),chartResetViewBtn=$('chartResetViewBtn');if(chartFullscreenBtn)chartFullscreenBtn.addEventListener('click',toggleChartFullscreen);if(chartMinimizeBtn)chartMinimizeBtn.addEventListener('click',toggleChartMinimized);if(chartZoomInBtn)chartZoomInBtn.addEventListener('click',()=>changePriceZoom(1.25,.5));if(chartZoomOutBtn)chartZoomOutBtn.addEventListener('click',()=>changePriceZoom(1/1.25,.5));if(chartResetViewBtn)chartResetViewBtn.addEventListener('click',resetChartView);document.addEventListener('fullscreenchange',()=>{updateChartViewerButtons();rerenderSelectedChart()});document.addEventListener('webkitfullscreenchange',()=>{updateChartViewerButtons();rerenderSelectedChart()});bindChartManipulation();updateChartViewerButtons();refresh();setInterval(refresh,6000);document.addEventListener('visibilitychange',()=>{if(!document.hidden)refresh()});
</script></main></div></body></html>'''


_INSTRUMENTS_HTML = r'''<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>DaemonBlackFx · Instrumentos</title>
<style>
:root{color-scheme:dark;--bg:#050708;--panel:#0a0e10;--panel2:#10161a;--text:#f5f5f2;--muted:#9fa2a5;--line:#5b4514;--good:#00db79;--accent:#d79b19}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:14px/1.45 system-ui,-apple-system,Segoe UI,sans-serif}.wrap{max-width:1220px;margin:auto;padding:20px}.top{display:flex;justify-content:space-between;align-items:flex-start;gap:14px;flex-wrap:wrap;margin-bottom:16px}.title{font-size:24px;font-weight:800}.sub{color:var(--muted)}.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px}.head{display:flex;justify-content:space-between;gap:12px;align-items:center;flex-wrap:wrap}.actions{display:flex;gap:8px;flex-wrap:wrap}.btn{display:inline-block;border:1px solid var(--line);background:var(--panel2);color:var(--text);text-decoration:none;border-radius:9px;padding:9px 12px;cursor:pointer}.btn.primary{background:var(--accent);color:#06111b;border-color:transparent;font-weight:800}.btn:disabled{opacity:.5;cursor:not-allowed}.stats{display:flex;gap:10px;flex-wrap:wrap;margin:14px 0}.metric{background:var(--panel2);border-radius:10px;padding:10px 12px;min-width:150px}.metric b{display:block;font-size:18px}.instrumentGrid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin-top:14px}.group{border:1px solid var(--line);border-radius:12px;padding:11px;background:var(--panel2)}.group h3{margin:0 0 8px;font-size:14px}.item{display:flex;gap:8px;align-items:flex-start;padding:6px 2px}.item input{margin-top:3px}.msg{margin-top:12px;color:var(--muted);min-height:22px}.search{width:min(420px,100%);background:#08131c;border:1px solid var(--line);color:var(--text);border-radius:9px;padding:10px 12px;font-size:16px}.note{margin-top:14px;padding:11px;border-left:3px solid var(--accent);background:var(--panel2);border-radius:8px}@media(max-width:950px){.instrumentGrid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:600px){.instrumentGrid{grid-template-columns:1fr}.wrap{padding:10px}.actions{width:100%}.actions .btn{flex:1;text-align:center}}
.brandStrip{display:flex;align-items:center;gap:14px;margin-bottom:16px;padding-bottom:14px;border-bottom:1px solid #5b4514}.brandStrip img{width:72px;height:72px;object-fit:cover;border-radius:12px;border:1px solid #765719}.brandStrip b{font-size:22px}.brandStrip b span{color:#f3c64c}.card{box-shadow:inset 0 1px 0 rgba(255,211,102,.03)}
</style></head><body><main class="wrap"><div class="brandStrip"><img src="/assets/blackdaemonfx_logo.jpeg" alt="Logo BlackDaemonFX"><div><b>BLACKDAEMON<span>FX</span></b><div class="sub">Gestión modular de instrumentos</div></div></div>
<div class="top"><div><div class="title">Instrumentos para nuevas entradas</div><div class="sub">Módulo independiente · catálogo dinámico desde MT5/Deriv · orden alfabético por categoría.</div></div><a class="btn" href="/">← Volver al dashboard</a></div>
<section class="card"><div class="head"><div class="actions" id="profileTabs"><button class="btn profileTab active" data-profile="SYNTHETICS" type="button">SINTÉTICOS</button><button class="btn profileTab" data-profile="FOREX" type="button">FOREX</button><button class="btn profileTab" data-profile="ORB" type="button">ORB NEW YORK</button><button class="btn profileTab" data-profile="IDX_OPEN" type="button">APERTURA ÍNDICES BURSÁTILES</button></div><div class="actions"><button class="btn" id="selectAll" type="button">Seleccionar todos</button><button class="btn" id="clearAll" type="button">Limpiar</button><button class="btn primary" id="save" type="button">Aplicar selección</button></div></div><div style="margin-top:12px"><input id="search" class="search" type="search" placeholder="Buscar instrumento…" aria-label="Buscar instrumento"></div>
<div class="stats"><div class="metric"><span class="sub">Seleccionados</span><b id="selectedCount">0</b></div><div class="metric"><span class="sub">Disponibles</span><b id="totalCount">0</b></div><div class="metric"><span class="sub">Aplicación</span><b>Próximo ciclo</b></div></div>
<div id="grid" class="instrumentGrid"><div class="sub">Cargando catálogo…</div></div><div id="msg" class="msg"></div>
<section class="card" style="margin-top:14px"><div class="head"><div><b>Noticias financieras relevantes</b><div class="sub">Fuente RSS en español · prioridad a impacto alto</div></div><span class="sub" id="newsStatus">Cargando…</span></div><div id="newsList" class="msg">Cargando noticias…</div></section>
<div class="note" id="profileNote"><b>Persistencia independiente:</b> Sintéticos, Forex, ORB y Apertura de Índices Bursátiles se guardan por separado.</div><div class="note"><b>Seguridad operativa:</b> desmarcar un instrumento impide nuevas entradas desde el próximo ciclo. Las posiciones ya abiertas continúan con monitoreo, SL/TP y Break Even.</div></section>
</main><script>
const $=id=>document.getElementById(id), esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));let state=null,dirty=false,activeProfile='SYNTHETICS';
function groups(s){return (s.instrument_catalog||[]).filter(g=>String(g.selection_profile||'SYNTHETICS').toUpperCase()===activeProfile)}
function selected(){return [...document.querySelectorAll('input[data-symbol]:checked')].map(x=>x.dataset.symbol).sort((a,b)=>a.localeCompare(b,'es'))}
function updateCount(){$('selectedCount').textContent=selected().length}
function renderNews(s){const n=s.financial_news||{},items=n.items||[];$('newsStatus').textContent=`${n.status||'SIN DATOS'} · ${n.updated_at?new Date(n.updated_at).toLocaleTimeString():'sin actualización'}`;$('newsList').innerHTML=items.length?items.slice(0,8).map(x=>`<div style="padding:7px 0;border-bottom:1px solid var(--line)"><span class="pill">${esc(x.impact||'MEDIO')}</span> <a href="${esc(x.link)}" target="_blank" rel="noopener" style="color:var(--text)">${esc(x.title)}</a><div class="sub">${x.published_at?new Date(x.published_at).toLocaleString('es-ES'):''}</div></div>`).join(''):'No hay noticias disponibles; se conserva el último estado conocido.'}
function render(s){state=s;renderNews(s);const chosen=new Set((s.selection_profiles||{})[activeProfile]||[]),q=$('search').value.trim().toLocaleLowerCase('es'),gs=groups(s);$('grid').innerHTML=gs.map(g=>{const items=(g.symbols||[]).filter(x=>x.toLocaleLowerCase('es').includes(q));return items.length?`<section class="group"><h3>${esc(g.label)} <span class="sub">(${items.length})</span></h3>${items.map(sym=>`<label class="item"><input type="checkbox" data-symbol="${esc(sym)}" ${chosen.has(sym)?'checked':''}><span>${esc(sym)}</span></label>`).join('')}</section>`:''}).join('')||'<div class="sub">No se encontraron instrumentos para este perfil.</div>';$('totalCount').textContent=gs.reduce((n,g)=>n+(g.symbols||[]).length,0);$('msg').textContent=s.selection_message||'';$('profileNote').innerHTML=`<b>${activeProfile}:</b> selección persistente independiente.`;document.querySelectorAll('.profileTab').forEach(b=>b.classList.toggle('active',b.dataset.profile===activeProfile));document.querySelectorAll('input[data-symbol]').forEach(cb=>cb.addEventListener('change',()=>{dirty=true;updateCount();$('msg').textContent=`Cambios pendientes para ${activeProfile}.`}));updateCount()}
async function load(){if(document.hidden)return;try{const r=await fetch('/api/instruments?ts='+Date.now(),{cache:'no-store'});if(!r.ok)throw new Error('HTTP '+r.status);const s=await r.json();if(!dirty)render(s)}catch(e){$('msg').textContent='Sin conexión con el daemon: '+e.message}}
async function save(){const values=selected();$('save').disabled=true;try{const r=await fetch('/api/instruments/selection',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({selection_profile:activeProfile,selected_symbols:values})});const data=await r.json();if(!r.ok||!data.ok)throw new Error(data.error||'No se pudo guardar');dirty=false;$('msg').textContent=data.message||`${activeProfile} guardado`;await load()}catch(e){$('msg').textContent='Error: '+e.message}finally{$('save').disabled=false}}
$('search').addEventListener('input',()=>{if(state)render(state)});document.querySelectorAll('.profileTab').forEach(b=>b.addEventListener('click',()=>{if(dirty&&!confirm('Hay cambios sin guardar. ¿Descartarlos?'))return;dirty=false;activeProfile=b.dataset.profile;if(state)render(state)}));$('selectAll').addEventListener('click',()=>{document.querySelectorAll('input[data-symbol]').forEach(x=>x.checked=true);dirty=true;updateCount()});$('clearAll').addEventListener('click',()=>{document.querySelectorAll('input[data-symbol]').forEach(x=>x.checked=false);dirty=true;updateCount()});$('save').addEventListener('click',save);load();setInterval(load,6000);document.addEventListener('visibilitychange',()=>{if(!document.hidden)load()});
</script></body></html>'''
