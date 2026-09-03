# DaemonBlackFx v24 — Cuenta activa sólo desde base de datos

## Objetivo
La página **Cuenta activa** deja de reconstruir o mostrar el historial completo de la cuenta MetaTrader 5.

## Comportamiento
- Se eliminó la importación histórica automática `MT5 -> trade_journal` del arranque normal.
- Cuenta activa consulta `account_trade_history_dataframe()`.
- Esa consulta sólo muestra registros del journal que previamente pasaron por la tabla operativa `trades` (`source_trade_id IS NOT NULL`).
- Los registros reconstruidos masivamente por v23 permanecen en la base para auditoría, pero quedan excluidos de Cuenta activa.
- La reconciliación de **posiciones abiertas** MT5 -> SQLAlchemy se mantiene para recuperar operaciones activas del daemon.
- Balance/equity/margen mostrados proceden del último `account_snapshot` persistido en SQLAlchemy, no de una consulta directa del navegador a MT5.

## Resultado
Cuenta activa representa exclusivamente el historial que DaemonBlackFx ha persistido operativamente en su base local.
