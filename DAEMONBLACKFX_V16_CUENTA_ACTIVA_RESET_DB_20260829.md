# DaemonBlackFx v16 — Cuenta activa y limpieza segura de SQLAlchemy

## Nueva pestaña Cuenta activa

Con el dashboard habilitado:

- Dashboard principal: `http://127.0.0.1:8765/`
- Instrumentos: `http://127.0.0.1:8765/instruments`
- Cuenta activa: `http://127.0.0.1:8765/account`

La pestaña Cuenta activa lee el mismo `TradingRepository` del daemon. Muestra el último `AccountSnapshot`, balance, equity, margen libre, profit flotante, trades registrados, abiertos/cerrados, win rate, PnL neto, TP1, TP2, Stop Loss, Break Even/Otros y cierres de emergencia. También lista los últimos 50 registros de trades.

Los cierres de emergencia de riesgo se mantienen separados de Stop Loss para no mezclar fallas/protecciones operativas con pérdidas normales de estrategia.

## Limpieza segura de la base

Detener el daemon antes de limpiar.

Comando normal:

```bash
python -m app.main --mode reset-db --confirm-reset-database
```

Antes de vaciar las tablas se copia automáticamente la SQLite actual a `database/backups/trading_bot_before_reset_YYYYMMDD_HHMMSS.sqlite3`.

Se vacían, conservando el esquema:

- `trades`
- `signals`
- `account_snapshots`

Si existen trades `OPEN` en SQLite, el reset se bloquea. Esta protección evita perder las referencias persistidas de posiciones que potencialmente siguen abiertas en MT5.

Sólo después de comprobar manualmente que MT5 no tiene posiciones del bot activas puede forzarse:

```bash
python -m app.main --mode reset-db --confirm-reset-database --force-reset-open-trades
```

Después del reset, las tablas siguen disponibles y las secuencias de IDs se reinician.

## Inicio del daemon

```bash
python -m app.main --mode demo-daemon --execute --interval 30 --risk-percent 1.0 --min-rr 1.5 --dashboard
```

La consola imprime las tres URLs locales.
