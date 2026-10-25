"""Defensa del dashboard local frente a peticiones de otras webs (CSRF y DNS rebinding).

El dashboard escucha en 127.0.0.1 sin autenticación. Sin estas comprobaciones, cualquier página abierta en el
navegador del usuario podía enviar un POST "simple" (sin preflight CORS, p. ej. `text/plain`) a
`http://127.0.0.1:8765` y detener workers, cambiar la selección de instrumentos, el objetivo diario o los ajustes de
Malaysian SNR; y con DNS rebinding (un dominio que resuelve a 127.0.0.1) también leer la cuenta.

Reglas (`DAEMONBLACKFX_DASHBOARD_STRICT_REQUESTS`, por defecto 1; 0 las desactiva):
- `Host` debe ser un nombre de bucle local (o el host de escucha configurado) cuando se escucha en local.
- En POST: `Content-Type: application/json` (obliga al navegador a hacer preflight, que el servidor no autoriza),
  `Origin` del mismo sitio si viene informado, nada de `Sec-Fetch-Site: cross-site` y cuerpo ≤ 1 MiB.
"""

from __future__ import annotations

import os
from urllib.parse import urlparse

LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})
MAX_POST_BYTES = 1024 * 1024


def strict_requests_enabled() -> bool:
    return os.getenv("DAEMONBLACKFX_DASHBOARD_STRICT_REQUESTS", "1").strip().lower() not in ("0", "false", "off", "no")


def _hostname(value: str | None) -> str | None:
    """Nombre de host (sin puerto, en minúsculas) de una cabecera `Host` u `Origin`."""
    text = str(value or "").strip()
    if not text:
        return None
    parsed = urlparse(text if "://" in text else f"//{text}")
    return (parsed.hostname or "").lower() or None


def unsafe_request_reason(headers, method: str, bind_host: str | None = None) -> str | None:
    """Motivo por el que se rechaza la petición, o None si es aceptable."""
    if not strict_requests_enabled():
        return None
    allowed = set(LOOPBACK_HOSTS)
    bind = _hostname(bind_host)
    if bind:
        allowed.add(bind)
    loopback_bind = bind is None or bind in LOOPBACK_HOSTS
    host = _hostname(headers.get("Host"))
    if loopback_bind and host is not None and host not in allowed:
        return "HOST_NOT_ALLOWED"
    if str(method).upper() != "POST":
        return None
    if str(headers.get("Sec-Fetch-Site") or "").strip().lower() == "cross-site":
        return "CROSS_SITE_REQUEST"
    origin = headers.get("Origin")
    if origin is not None and str(origin).strip().lower() != "null":
        if _hostname(origin) not in allowed:
            return "ORIGIN_NOT_ALLOWED"
    elif origin is not None:
        return "ORIGIN_NOT_ALLOWED"
    content_type = str(headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
    if content_type != "application/json":
        return "CONTENT_TYPE_MUST_BE_JSON"
    try:
        length = int(headers.get("Content-Length") or 0)
    except (TypeError, ValueError):
        return "INVALID_CONTENT_LENGTH"
    if length < 0 or length > MAX_POST_BYTES:
        return "PAYLOAD_TOO_LARGE"
    return None
