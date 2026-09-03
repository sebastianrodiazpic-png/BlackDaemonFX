# DaemonBlackFx v68 — Dataset persistente Entrada vs. Ahora

## Objetivo
Convertir la auditoría visual `Entrada vs. Ahora` en un dataset longitudinal útil
para investigación, sin sobrescribir la tesis original del trade.

## SQLAlchemy
Nueva tabla append-only: `trade_audit_snapshots`.

Cada observación guarda:
- trade_id, instrumento, bot, magic y ticket MT5;
- fecha/hora del snapshot;
- tesis de entrada persistida;
- evaluación SMC actual;
- score y porcentaje de confirmación actual;
- confirmaciones/patrones/estructura actuales;
- estado de mercado (precio, R actual, SL, TP cuando estén disponibles);
- metadatos de auditoría visual/timeframes disponibles.

La tabla `trade_visual_audits` sigue conservando la entrada inmutable + último estado.
`trade_audit_snapshots` conserva TODA la evolución histórica.

## Frecuencia
Se crea una observación cada vez que v67 actualiza `Lo que ve ahora` (~10 s para
posiciones SMC abiertas). No ejecuta trades adicionales.

## /account
Cada operación incorpora:
- cantidad total de snapshots Entrada vs. Ahora;
- última comparación;
- últimos 20 snapshots visibles en un detalle desplegable.

La base SQLAlchemy conserva todos los snapshots; el límite de 20 es sólo de UI para
no inflar la respuesta HTTP.

## XLSX
El reporte automático agrega la hoja `Entrada vs Ahora` con una fila por snapshot.
Incluye columnas planas útiles para análisis y columnas JSON compactas para conservar
el detalle completo. Las celdas JSON se limitan de forma segura para Excel, mientras
SQLAlchemy conserva el contenido estructurado completo.

## Compatibilidad
Se mantienen v57-v67, incluida selección persistente, multiproceso sintético,
Cuenta activa, patrones chartistas, ORB, TP4 SMC, BE+2 y auditoría actual en vivo.
