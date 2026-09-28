# Persistencia y auditoría fiable

Cambios de observabilidad; no se modifican los umbrales de spread, antigüedad de señal, estrategia, SL/TP ni promoción de modelos.

## Spread

Reemplazo atómico con temporal único y hasta tres intentos ante PermissionError (esperas de 50 y 100 ms). Si los intentos fallan se conserva el JSON anterior y se propaga el error al registro operativo existente. Un archivo health separado indica OK/DEGRADED y el dashboard muestra los fallos. Si también falla la escritura del estado de salud, el error original sigue disponible en los eventos del worker. La observación fallida no autoriza una entrada.

## Bloques y señales

Identidad del bloque: símbolo, M15, vela de origen, dirección y límites. El archivo diario guarda una ficha por bloque, contador de reevaluaciones y hasta 32 cambios recientes de estado. SQLite recibe los bloques nuevos/cambiados y un resumen, no toda la lista histórica en cada ciclo. El historial diario conserva las fichas. Los registros anteriores no se reescriben.

Primera observación de señal: FIRST_SEEN_FRESH / FIRST_SEEN_STALE. Observaciones posteriores: REPEATED_HISTORICAL_SIGNAL. Se conserva la primera hora y la distancia al cierre de la vela M5, más el trabajo medido por etapas. Esta primera observación se limita al registro diario: no demuestra por sí sola latencia del motor, particularmente tras un reinicio o inicio del seguimiento. No altera la caducidad utilizada para operar.

## Aprendizaje visible

Separación explícita cuenta / familia / worker: ejecuciones, setups agrupados, setups cerrados, capturas de entrada y motivos de elegibilidad por ejecución. El entrenamiento y la comparación existentes continúan por familia; la lista de elegibilidad visible se limita a esa familia. Las métricas de cuenta no se deben sumar entre workers.

Embudo de entrenamiento: setups cerrados elegibles por familia y candidatos entrenados. No se migran capturas antiguas rellenando valores: se exige evidencia original causal. Las variantes continúan utilizando resultados cerrados emparejados; sin resultados netos validados no se promueven automáticamente.

## Activación

Los cambios requieren recargar los workers y el dashboard. No se reiniciaron procesos ni se modificaron operaciones abiertas. Las nuevas métricas aparecerán con los próximos ciclos y refrescos del informe de aprendizaje; los informes antiguos se mantienen hasta entonces.
