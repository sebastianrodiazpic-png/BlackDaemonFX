# DaemonBlackFx v46 — Persistencia total DB + XLSX

## Principio
La base SQLAlchemy/SQLite es la fuente de verdad. El archivo
`deriv_demo_trading_report.xlsx` se reconstruye desde datos persistentes y nunca
debe ser la única copia de una entrada.

## Persistencia de operaciones
Cada trade creado o actualizado continúa sincronizándose a:
- `trades`: estado operativo actual;
- `trade_journal`: historial permanente append/upsert que sobrevive a resets.

La exportación XLSX de v46 lee `trade_journal` cuando está disponible, por lo que
una operación histórica no desaparece del reporte aunque la tabla operativa se
reinicie.

## Nueva bitácora `daemon_audit_events`
Se añadió una tabla append-only para eventos operativos:
- resultado de cada símbolo procesado;
- señales/decisiones aceptadas o rechazadas a través del resultado del símbolo;
- EXECUTION_FILLED / EXECUTION_REJECTED;
- POSITION_UPDATED;
- LIFECYCLE_FINALIZED;
- monitor de posiciones;
- Break Even / Runner dentro del payload del monitor;
- rollover Forex;
- errores del ciclo;
- errores de exportación XLSX;
- recuperación automática MT5 -> DB;
- cambios de selección de instrumentos.

## Auto-reparación
Antes del monitor de posiciones, el daemon compara posiciones abiertas MT5 con
SQLite. Si encuentra una posición con el magic del daemon que no existe en DB,
la adopta automáticamente y la persiste.

Después de un FILLED se verifica que exista el trade por `execution_key`.
Si no existe, se reintenta mediante el servicio de reporting y finalmente se
realiza una persistencia defensiva directa.

## XLSX
El reporte agrega la hoja `Audit Log` además de:
- Trades
- Open Positions
- Summary
- Instruments
- Account
- Metadata

Si Excel está abierto o el archivo está bloqueado, el error se registra en DB y
NO invalida la operación ni su persistencia. Una exportación posterior reconstruye
el XLSX desde la base.

## Garantía de diseño
Una falla del XLSX nunca debe provocar que una entrada válida desaparezca de DB.
