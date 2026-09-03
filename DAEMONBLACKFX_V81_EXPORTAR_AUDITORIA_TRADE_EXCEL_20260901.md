# DaemonBlackFx v81 — Exportación Excel de auditoría por trade

La pestaña `/account/trade/<trade_id>/audit` incorpora el botón:

`Exportar Excel ↓`

Endpoint:
`/api/account/trade/<trade_id>/audit/excel`

El XLSX se genera desde la misma información SQLAlchemy utilizada por la
auditoría web y contiene:

- Resumen
- Tesis Entrada
- Ultimo Estado
- Mercado Final
- Timeline Completo

Timeline Completo contiene una fila por snapshot histórico con fecha Chile,
R, precio, SL/TP, BE, MFE/MAE, runner, H1, estructura, patrón chartista,
conflictos, divergencia, Doji H1, ORB/VWAP/POC, contexto HTF y los JSON
estructurados persistidos para tratamiento posterior.

Los archivos también quedan guardados localmente en:
`storage/exports/trade_audits/`
