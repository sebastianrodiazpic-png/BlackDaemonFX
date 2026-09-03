# DaemonBlackFx v36 — Cuenta activa 100% persistente desde SQLAlchemy

## Objetivo
La página `/account` ya no depende de `/api/state` ni de `storage/dashboard/last_state.json`
para ninguno de sus indicadores.

## Fuente de cada bloque
- Balance / Equity / Margen libre / Profit flotante: último registro de `account_snapshots`.
- Trades / Abiertos / Cerrados: `trade_journal`.
- Win rate: cierres persistidos en `trade_journal`, calculado sobre wins + losses.
- PnL neto: suma de `net_pnl` de operaciones cerradas persistidas.
- TP1 / TP2 / TP histórico / Stop Loss / Break Even / Emergencia: clasificación de cierres del journal.
- Tabla histórica: `trade_journal`.

## Endpoint
`GET /api/account`

Cada request vuelve a consultar SQLAlchemy. Reiniciar:
- el navegador,
- el servidor del dashboard,
- el daemon,
- o borrar/perder `last_state.json`

no reinicia los datos visualizados mientras sigan existiendo en SQLite.

## Separación de responsabilidades
`/api/state` continúa manejando información temporal/operativa del dashboard en tiempo real.
`/api/account` es exclusivamente persistente y DB-only.

No se consulta el historial completo de MT5 para construir Cuenta activa.
