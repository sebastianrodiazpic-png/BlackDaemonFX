# DaemonBlackFx v86 — auditoría durable y Excel

## Garantías

- El fill confirmado crea inmediatamente la tesis inmutable en `trade_visual_audits`.
- En la misma operación lógica se crea el primer registro append-only en
  `trade_audit_snapshots`, sin esperar el refresco periódico.
- Los refrescos posteriores siguen agregando observaciones Entrada vs. Ahora.
- Un reintento de persistencia no duplica el snapshot inicial.
- La página `/account/trade/<trade_id>/audit` lee la serie histórica desde la DB.
- Para trades históricos sin serie, usa como respaldo seguro la tesis inmutable
  de `trade_visual_audits`.
- La identidad se valida por trade, instrumento y ticket antes de mostrar o exportar.
- `/api/account/trade/<trade_id>/audit/excel` exporta Resumen, Tesis Entrada,
  Último Estado, Mercado Final y Timeline Completo.
- La base predeterminada permanece fuera de la carpeta versionada mediante
  `%LOCALAPPDATA%\\BlackDaemonFx\\trading_bot.sqlite3` en Windows.
