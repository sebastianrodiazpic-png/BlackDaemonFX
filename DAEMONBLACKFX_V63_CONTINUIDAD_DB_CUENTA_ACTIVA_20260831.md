# DaemonBlackFx v63 — Continuidad persistente de Cuenta activa

## Problema observado
Cada versión extraída en una carpeta nueva utilizaba `database/trading_bot.sqlite3`
dentro de esa carpeta. Si el archivo histórico no se copiaba manualmente, SQLAlchemy
creaba una base nueva vacía y `/account` mostraba 0 trades, sin snapshot y balance vacío.

## Corrección
- La base por defecto pasa a una ubicación estable fuera de la carpeta de versión:
  - Windows: `%LOCALAPPDATA%/BlackDaemonFx/trading_bot.sqlite3`
  - Otros sistemas: `~/.blackdaemonfx/trading_bot.sqlite3`
- Puede fijarse explícitamente con `DAEMONBLACKFX_DB_PATH`.
- En el primer arranque, si la base estable está vacía, se buscan únicamente bases
  `*/database/trading_bot.sqlite3` en carpetas hermanas.
- Sólo se recuperan bases con actividad real (`trade_journal`, `trades`,
  `account_snapshots`).
- Se escoge la base con mayor actividad; una base estable con datos nunca se sobrescribe.
- `/account` muestra la ruta SQLite exacta y los conteos de trades/journal/snapshots.
- La persistencia v62 de confirmaciones continúa usando `trade_visual_audits`.
