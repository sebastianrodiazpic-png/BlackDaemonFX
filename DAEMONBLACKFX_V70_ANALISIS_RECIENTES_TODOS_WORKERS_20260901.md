# DaemonBlackFx v70 — Análisis recientes de todos los workers

## Problema
El dashboard central mostraba en "Análisis recientes" principalmente resultados ORB.
La causa era que ese panel usaba `_recent`, una cola en memoria del proceso HTTP.
Los workers coordinados (BOOM/CRASH/VOLATILITY/STEP/JUMP/FLIP y FOREX_1..4)
no tienen dashboard propio, por lo que sus análisis no llegaban a esa cola.

## Solución
- Nuevo repositorio `recent_symbol_process_results()` desde `daemon_audit_events`.
- El dashboard central usa SQLAlchemy como fuente de "Análisis recientes".
- Se conservan múltiples resultados por worker/símbolo, no sólo el último por perfil.
- Se agrega columna `Bot` para distinguir familia/worker.
- Los registros `SUPERSEDED` de SYNTHETICS y FOREX legacy dejan de mostrarse
  en las tarjetas de procesos.
- Los registros históricos permanecen en SQLAlchemy; sólo se ocultan visualmente.
