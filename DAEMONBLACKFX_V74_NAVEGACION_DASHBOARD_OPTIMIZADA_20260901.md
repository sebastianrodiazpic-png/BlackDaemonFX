# DaemonBlackFx v74 — Navegación rápida Dashboard / Account / Instruments

## Problema
`/instruments` pedía `/api/state`, lo que reconstruía posiciones, cuenta, últimos
análisis y workers aunque esa página sólo necesita catálogo y selección.
`/api/account` reconstruía el payload SQLAlchemy completo en cada request.
Además `/api/state` repetía varias consultas auxiliares en cada poll.

## Optimización
- Nuevo endpoint ligero `/api/instruments`.
- `/instruments` ya no solicita `/api/state`.
- Caché de Account: TTL 3 segundos.
- Caché de instrumentos: TTL 2 segundos.
- Caché de análisis/workers/candidatos del snapshot: TTL 2 segundos.
- Las selecciones invalidan inmediatamente la caché de instrumentos.
- SQLAlchemy sigue siendo la fuente de verdad; las cachés sólo evitan lecturas
  redundantes consecutivas.
- Las páginas HTML continúan sirviéndose inmediatamente y cargan datos por API.

## Resultado esperado
- Cambio a `/instruments`: mucho más rápido al no cargar gráficos, trades,
  account ni 2500 eventos de auditoría.
- Cambio a `/account`: la primera reconstrucción puede consultar DB, pero
  refrescos/navegaciones consecutivas reutilizan 3 s de caché.
- Dashboard: menor contención de SQLite al refrescar cada pocos segundos.
