# Calidad de registros y selección — 25/09/2026

## Cambios

- Auditoría SMC: escritura con temporal único y reemplazo atómico; hasta cuatro intentos ante PermissionError (esperas 50/100/200 ms). Si falla, conserva el último archivo válido y propaga el error al registro AUDIT_DEGRADED existente. Se aplica al estado y al archivo histórico; no son una transacción conjunta.
- MetaEtiquetado: CLIENT/MOBILE/WEB quedan fuera de las etiquetas autónomas. Una intervención en una pierna excluye todo el setup del entrenamiento. Los resultados contables permanecen. Las comparaciones muestran cantidad de setups manuales y beneficio realizado por separado.
- Observación externa: primera captura inmutable; si carece de riesgo válido, se guarda una única FIRST_VALID_RISK_OBSERVATION posterior cuando aparece el SL. El aprendizaje usa precio, riesgo y contexto de esa segunda captura; continúa separado como MT5_OBSERVATION. No reconstruye capturas para operaciones históricas ya cerradas.
- Corredor de entrada: distingue mínimo aprobado con obstáculos de recorrido completamente libre. Registra R hasta primer obstáculo y R de cada objetivo. El detalle del trade muestra esos datos cuando existen; datos antiguos no se inventan.
- Dashboard: motivos explícitos de cierre manual excluido, nueva evidencia de observación y contador de cierres manuales separado de comparación autónoma.

## Condiciones preservadas

No se cambiaron premium/discount H1, Order Blocks M15, confirmaciones M5, umbrales de recorrido, riesgo, SL/TP ni reglas de cierre. Ninguna variante de sombra se promociona automáticamente.

## Verificación y activación

80 pruebas focalizadas de persistencia, aprendizaje, observación externa, SMC y Cuartos. JavaScript extraído de las dos páginas validado con node --check.

Cambios en disco. No se reiniciaron workers/dashboard ni se modificó la base de datos operativa. Se cargarán al reiniciar los procesos correspondientes. La nueva observación necesita un ciclo de auditoría mientras la operación siga abierta; los informes existentes se actualizan en el siguiente ciclo de aprendizaje con este código cargado.
