# Mejoras de calidad de ejecución y auditoría — 2026-09-24.1

## Cambios implementados, en orden

1. **ORB:** corregida la vinculación de `_trade_has_confirmed_break_even`; los errores del worker ORB llevan su estrategia real. Se conserva el control de exposición correlacionada.
2. **Precio ejecutable:** cada pata ORB vuelve a validar RR justo antes de `order_send`, con la última cotización y sus SL/TP normalizados. El mínimo es el RR previsto de esa pata (por ejemplo, 1R TP1 y 2R runner). Si el precio lo degrada, se devuelve `EXECUTABLE_RR_BLOCKED`. No se desplazan los objetivos. Un rechazo de la segunda pata conserva la primera; el primer fill ya consume la señal ORB para evitar duplicación. Se registra RR cotizado y tiempo de procesamiento entre patas.
3. **SL/TP:** la reconciliación de posiciones abiertas actualiza los niveles observados en MT5 y guarda un evento `TRADE_TARGET_CHANGE` en la misma transacción. El evento conserva antes/después, procedencia y hora de observación, sin inventar autor ni hora real de modificación. Al cierre se compara el comentario SL/TP de MT5 con lo persistido. Las discrepancias quedan pendientes de revisión y excluyen el setup completo del aprendizaje y comparaciones.
4. **Volumen:** ORB deja de convertir ausencia de volumen en una serie ficticia de unos para confirmar rupturas. Solo usa información disponible hasta la vela de ruptura. La política existente se conserva: retest no penaliza ausencia; momentum requiere volumen confirmado. La auditoría muestra fuente, volumen, promedio, ratio y umbral. El modelo distingue ratio cero de dato ausente.
5. **Capturas y aprendizaje:** nuevas capturas `entry-learning-v4` / `meta-features-v4` conservan setup, versión, tiempos e indicadores. Se rechazan capturas posteriores a ejecución. Las observaciones externas se agrupan en `EXTERNAL / MT5_OBSERVATION`, sin atribuirlas al colector BOOM; sus retornos siguen midiendo observación-a-cierre, no entrada-a-cierre. Un cierre solicita actualizar el informe de aprendizaje.
6. **Comparación y visibilidad:** resultados cerrados desglosados por versión, contador de reconciliaciones pendientes y elegibilidad visibles en el panel. Se conserva el modo candidato/sombra y no se promociona ninguna variante ni modelo. Los ciclos vacíos repetidos generan un evento por minuto o al cambiar de estado, manteniendo el heartbeat del worker.

## Límites y reglas preservadas

- H1 premium/discount; setup y Order Block M15; confirmación favorable M5. No se relajaron estas condiciones.
- ORB conserva objetivos y no usa estas mejoras para cerrar posiciones anticipadamente. La excepción Forex de cierre de mercado ya configurada no cambia.
- La validación previa no garantiza el precio final del broker: puede haber slippage posterior. Se audita, sin ampliar objetivos ni cerrar ORB por ese motivo.
- No se rellenan capturas antiguas con información futura. Los vectores anteriores se conservan, pero no se mezclan con v4 ni se reutilizan modelos incompatibles.
- La exclusión por discrepancia no modifica ganancias/pérdidas históricas. Se conserva el resultado real y el nivel original para investigar.
- No se eliminó historia de workers ni se mapearon instrumentos no soportados a otros proveedores. Su disponibilidad sigue bajo el catálogo y preflight existentes.

## Reconciliación histórica

`python -m tools.audit_target_reconciliation --db RUTA` previsualiza; `--apply` crea primero una copia SQLite consistente y registra evidencia en metadatos/eventos. Nunca envía órdenes ni modifica precios de operaciones históricas.

Evidencia de esta ejecución: `storage/analysis/target_reconciliation_applied_20260924.json`. El trade 206 de US Tech 100 es el caso discrepante identificado; no se afirma quién cambió su TP.

## Validación

Pruebas de regresión de ORB, volumen, exposición, riesgo, plata, persistencia, capturas y aprendizaje; pruebas nuevas en `tests/test_trade_quality_20260924.py`, incluyendo ejecución de dos patas con rechazo en la segunda y prohibición de cierre de la primera. JavaScript de los dos HTML verificado con `node --check`.

La activación en procesos existentes requiere recarga. El resultado operativo de la recarga se guarda por separado; editar archivos por sí solo no actualiza los workers ya iniciados.

## Resultado de esta aplicación

- 125 pruebas pasaron; verificación de sintaxis JavaScript y `git diff --check` completadas.
- Reconciliación histórica aplicada tras copia SQLite: 14 registros examinados con evidencia comparable, 13 coincidencias y 1 discrepancia (trade 206). Se conservaron precios y resultados originales.
- Recarga del coordinador iniciada con los mismos parámetros de ejecución y riesgo, después de verificar 0 posiciones abiertas en MT5. Evidencia de activación: `storage/analysis/quality_reload_20260924.json`; estado posterior: `storage/analysis/quality_runtime_verified_20260924.json`.
- No se promovieron modelos ni se relajaron filtros SMC. La siguiente evaluación de modelos usará el esquema v4 y hará explícita la incompatibilidad de capturas anteriores; no se rellenan artificialmente para alcanzar el mínimo de entrenamiento.

El dashboard activo respondió HTTP 200 y confirmó la presencia de volumen detallado, comparación por versión y contador de revisión SL/TP. La recarga conserva ORB fuera de sesión cuando corresponde.

Verificación final de activación: 24/09/2026 23:37 UTC (20:37 Chile). Los 14 workers emitieron eventos con `quality_release=2026-09-24.1`; Forex completó el preflight y evaluó instrumentos. ORB permanece correctamente fuera de sesión. No se encontraron eventos de error posteriores a la recarga en la consulta final. Esta comprobación de arranque no equivale a evidencia de rentabilidad ni de resultados futuros.
