"""Resumen compacto del `order_check` de MT5 para la auditoría de rechazos.

Hasta el 12-nov-2026, cuando MT5 rechazaba una orden en la validación previa (`ORDEN_RECHAZADA_EN_VALIDACION_MT5`),
la compactación del resultado guardaba sólo `code` y `leg`: el `retcode` y el comentario del broker se perdían, y no
había forma de saber si el rechazo era por stops, volumen, precio o margen.

Este módulo es lógica pura (sin MT5 ni base de datos):
- `summarize_order_check`: deja retcode, comentario, precio/SL/TP/volumen pedidos y los retcode de cada filling probado.
- `order_check_failures`: extrae los resúmenes de `split_failure` / `single_failure` / `risk_failure` de una fila.
- `format_order_check_line`: línea corta para la consola del worker.

Interruptor: DAEMONBLACKFX_PERSIST_ORDER_CHECK_DETAIL=0 vuelve al comportamiento anterior (no se guarda ni se imprime).
"""
from __future__ import annotations

import os
from typing import Any

RETCODE_DESCRIPTIONS = {
    10004: "recotización",
    10006: "solicitud rechazada",
    10013: "solicitud inválida",
    10014: "volumen inválido",
    10015: "precio inválido",
    10016: "stops inválidos",
    10017: "trading deshabilitado",
    10018: "mercado cerrado",
    10019: "sin fondos suficientes",
    10020: "precios cambiados",
    10021: "sin cotización",
    10022: "expiración inválida",
    10026: "autotrading deshabilitado en el servidor",
    10027: "autotrading deshabilitado en el terminal",
    10030: "modo de llenado no soportado",
    10031: "sin conexión",
    10033: "límite de órdenes pendientes",
    10034: "límite de volumen del símbolo",
    10040: "límite de posiciones",
    10044: "sólo cierre permitido",
}

_REQUEST_FIELDS = ("action", "type", "volume", "price", "sl", "tp", "deviation", "type_filling")
_RESULT_FIELDS = ("retcode", "comment", "balance", "equity", "margin", "margin_free", "margin_level", "profit")
FAILURE_KEYS = ("split_failure", "single_failure", "risk_failure")


def persist_enabled() -> bool:
    return os.getenv("DAEMONBLACKFX_PERSIST_ORDER_CHECK_DETAIL", "1").strip().lower() not in ("0", "false", "off", "no")


def _scalar(value: Any):
    if value is None or isinstance(value, (bool, int, float, str)):
        return value if not isinstance(value, str) else value[:120]
    try:
        return float(value)
    except (TypeError, ValueError):
        return str(value)[:120]


def _retcode(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def summarize_order_check(order_check: Any) -> dict | None:
    """Reduce el diccionario de `check_market_order` a los campos que explican un rechazo."""
    if not isinstance(order_check, dict) or not order_check:
        return None
    retcode = _retcode(order_check.get("retcode"))
    summary: dict[str, Any] = {
        "valid": bool(order_check.get("valid")),
        "retcode": retcode,
        "retcode_description": RETCODE_DESCRIPTIONS.get(retcode) if retcode is not None else None,
        "comment": _scalar(order_check.get("comment")),
        "reason": _scalar(order_check.get("reason")),
    }
    request = order_check.get("request")
    if isinstance(request, dict):
        summary["request"] = {k: _scalar(request.get(k)) for k in _REQUEST_FIELDS if request.get(k) is not None}
    attempts = order_check.get("attempts")
    if isinstance(attempts, (list, tuple)):
        compact_attempts = []
        for attempt in list(attempts)[:6]:
            if not isinstance(attempt, dict):
                continue
            item = {
                "filling": _scalar(attempt.get("filling_name") or attempt.get("filling")),
                "retcode": _retcode(attempt.get("retcode")),
                "comment": _scalar(attempt.get("comment")),
            }
            if attempt.get("mt5_last_error") is not None:
                item["mt5_last_error"] = _scalar(attempt.get("mt5_last_error"))
            result = attempt.get("result")
            if isinstance(result, dict):
                fields = {k: _scalar(result.get(k)) for k in _RESULT_FIELDS if result.get(k) is not None}
                if fields:
                    item["result"] = fields
            compact_attempts.append(item)
        if compact_attempts:
            summary["attempts"] = compact_attempts
    return {k: v for k, v in summary.items() if v is not None}


def order_check_failures(row: Any) -> dict:
    """Devuelve {nombre_fallo: resumen} para los fallos de la fila que traen `order_check`."""
    out: dict[str, dict] = {}
    if not isinstance(row, dict):
        return out
    for name in FAILURE_KEYS:
        failure = row.get(name)
        if not isinstance(failure, dict):
            continue
        summary = summarize_order_check(failure.get("order_check"))
        if summary:
            out[name] = summary
    return out


def format_order_check_line(row: Any) -> str | None:
    """Línea de consola: `MT5 order_check: TP1 retcode=10016 (stops inválidos) "Invalid stops"`."""
    if not persist_enabled():
        return None
    parts = []
    for name, summary in order_check_failures(row).items():
        failure = row.get(name) or {}
        leg = failure.get("leg") or name
        code = summary.get("retcode")
        desc = summary.get("retcode_description")
        text = f"{leg} retcode={code if code is not None else '-'}"
        if desc:
            text += f" ({desc})"
        comment = summary.get("comment") or summary.get("reason")
        if comment:
            text += f' "{comment}"'
        parts.append(text)
    if not parts:
        return None
    return "MT5 order_check: " + " | ".join(parts)
