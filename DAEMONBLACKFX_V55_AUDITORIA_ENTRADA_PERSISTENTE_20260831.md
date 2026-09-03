# DaemonBlackFx v55 — Auditoría de entrada persistente por trade

## Objetivo
Conservar para siempre la evidencia de por qué se abrió cada operación.

## Nueva tabla
`trade_visual_audits`

Cada `trade_id` mantiene dos capas independientes:

### Entrada — inmutable
Se captura una sola vez:
- gráfico M1/M5/M15/H1;
- velas y capas SMC;
- score;
- porcentaje de confirmación;
- confirmaciones cumplidas;
- faltantes;
- fallos críticos;
- divergencia;
- patrón armónico;
- Doji H1;
- tendencia H1;
- estructura M15;
- zona Premium/Discount;
- dirección;
- entry/SL/TP;
- RR planificado;
- riesgo;
- bot_profile;
- magic;
- estrategia;
- pierna TP1/RUNNER/SINGLE.

Una vez almacenado, `entry_chart_json` y `entry_context_json` no se sobrescriben.

### Actual — dinámico
Mientras el trade permanezca abierto:
- `latest_chart_json`;
- `latest_market_json`;
- R actual;
- precio;
- SL/BE;
- contexto visual actualizado.

## Dashboard
En la auditoría visual aparecen dos modos:
- `ENTRADA`: evidencia persistida de la decisión original.
- `ACTUAL`: lectura actual del mercado.

Cambiar temporalidad M1/M5/M15/H1 funciona en ambas vistas.

## Persistencia histórica
Cerrar una operación no elimina `trade_visual_audits`. La evidencia permanece en
SQLAlchemy para revisiones posteriores y futuras pantallas históricas.

## Seguridad
Este cambio no modifica reglas de entrada, riesgo, Break Even, Runner, SMC, Forex
ni ORB. Sólo mejora persistencia y auditoría.
