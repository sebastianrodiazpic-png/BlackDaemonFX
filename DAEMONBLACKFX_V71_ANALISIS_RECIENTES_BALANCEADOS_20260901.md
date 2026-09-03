# DaemonBlackFx v71 — Análisis recientes equilibrados

## Problema observado
Aunque v70 leyó `SYMBOL_PROCESS_RESULT` desde SQLAlchemy, ORB podía generar
muchos `WAITING_NEW_YORK_OPEN` y ocupar las últimas 120 filas. Eso desplazaba
visualmente los análisis de BOOM/CRASH/VOLATILITY/STEP/JUMP/FLIP y FOREX_1..4.

## Corrección
- Se escanean hasta 2500 eventos recientes.
- Se infiere el perfil para eventos históricos sin `bot_profile`.
- Se deduplica por `profile + symbol + action`.
- Cada perfil dispone de hasta 12 filas antes de mezclar el resultado.
- El resultado final vuelve a ordenarse cronológicamente.
- No se elimina historial SQLAlchemy.
- La columna BOT identifica el worker.
- Los perfiles legacy SUPERSEDED continúan ocultos visualmente.
