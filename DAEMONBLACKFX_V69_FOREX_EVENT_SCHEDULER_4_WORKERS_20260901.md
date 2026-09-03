# DaemonBlackFx v69 — Forex Event Scheduler + 4 workers

## Objetivo
Evitar ciclos Forex secuenciales de 20–30 minutos cuando se seleccionan decenas
de pares.

## Arquitectura
FOREX coordinator:
- FOREX_1 magic 26082201
- FOREX_2 magic 26082202
- FOREX_3 magic 26082203
- FOREX_4 magic 26082204

Los pares seleccionados persistentemente se distribuyen de forma determinista
entre los cuatro workers. Cada par pertenece a un solo shard.

## Scheduler
- Poll del worker: 10 segundos.
- Nuevas entradas sólo se reevaluan cuando aparece una nueva vela M5 cerrada.
- H1/M15/M5 mantienen la caché multi-timeframe ya existente hasta su próxima vela.
- Monitor de posiciones, Break Even, runner y auditoría continúan cada 2 segundos.

## Riesgo global Forex
SQLAlchemy se usa como fuente compartida entre workers.
- Riesgo total lógico máximo Forex por defecto: 4%.
- Exposición máxima por moneda por defecto: 2%.
- TP1 + RUNNER del mismo setup se cuentan como 1% lógico, no como dos riesgos.
- Si una nueva entrada excede el límite de USD/EUR/etc. se bloquea antes de enviar órdenes.

## Compatibilidad
- `forex-daemon` se convierte en alias seguro del coordinador de cuatro workers.
- Nuevo modo explícito: `forex-split-daemon`.
- Persistencia de selección sigue bajo el único perfil `FOREX`.
- Rollover NY / reapertura Londres / Friday flat se conservan.
- v68 SQLAlchemy + XLSX Entrada-vs-Ahora se conserva.
