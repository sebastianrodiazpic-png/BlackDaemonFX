# DaemonBlackFx v22 — Historial permanente en Cuenta activa

## Objetivo

La vista **Cuenta activa** conserva ahora un journal histórico independiente de la tabla operativa `trades`.

## Nueva tabla

`trade_journal`

Se actualiza automáticamente cuando un trade:

- es creado por DaemonBlackFx;
- es recuperado/importado desde MT5;
- cambia de estado;
- se cierra y recibe PnL/RR/resultado final.

La clave de journal prioriza `broker_position_ticket`, `execution_key` y `external_ticket`, evitando duplicados al reiniciar el daemon.

## Migración de instalaciones anteriores

Al construir `TradingRepository`, los trades existentes en `trades` se sincronizan automáticamente hacia `trade_journal`. Esto permite actualizar desde v21 sin perder los registros que aún estén en la base.

## Reset operativo

`python -m app.main --mode reset-db --confirm-reset-database`

continúa eliminando:

- `trades`;
- `signals`;
- `account_snapshots`.

Pero **NO elimina `trade_journal`**.

El comando informa cuántos registros históricos fueron conservados.

## Cuenta activa

Las estadísticas y la tabla de operaciones de `/account` se construyen desde `trade_journal`, no desde la tabla operativa. Por eso los trades cerrados continúan visibles aunque el daemon se reinicie o se reconstruya la tabla `trades`.

## Validación

Suite no-MT5: 193 pruebas aprobadas.
