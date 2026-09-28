# Monitor M5 v3 y consolidacion

Etiquetas activas: STANDARD_CHOCH_SWEEP, RECLASSIFIED_BOS_TO_CHOCH, VALIDATED_WICK_CHOCH_WITH_FVG, MISSING_BOTH_CHOCH_AND_SWEEP, TRUE_MISSING_CHOCH, MISSING_SWEEP_ONLY, EXPIRED_SIGNAL. INVALID_TIMESTAMP permanece para datos temporales invalidos o futuros. evaluate_m5_details_v3 comparte el evaluador activo; no es una implementacion aislada.

No cambian los pesos, evidencias causales ni limite de 10 minutos de v2. Se usa el timestamp real del BOS/mecha si hubo reclasificacion. Sigue siendo obligatorio el FVG real para rescate por mecha. La telemetria schema 3 publica m5_diagnostic_tags y veto_reason_counts completos, ademas del top 3.

## Script
.\.venv\Scripts\python.exe tools/analyze_smc_telemetry.py --output storage/analysis/m5_detector/manual_summary.json

Ruta predeterminada: storage/runtime/smc_telemetry. Modo snapshots selecciona la sesion mas reciente por bot_name y suma total_evaluations/status_counts/m5_diagnostic_tags; nunca cuenta un JSON acumulado como una evaluacion. Solo considera BOOM, CRASH, JUMP, STEP y VOLATILITY_1..4. Muestra fechas por worker, workers faltantes y errores de lectura. Los reportes anteriores a v3 se incluyen con advertencia; su top de motivos es parcial, pues solo guardaban tres razones.

--input-mode events permite procesar objetos/listas de eventos individuales de otro export. Es un modo separado; los snapshots nunca se suman con eventos individuales. Las etiquetas historicas no se renombran como si fueran resultados de v3.

## Primer bloque
Al terminar el primer process_symbols con resultados y actividad SMC del worker, se fuerza flush y se genera automaticamente storage/analysis/m5_detector/<worker>_<pid>_first_cycle.json. Cubre tambien la ruta de ranking previo a ejecucion. No se ejecuta para ciclos vacios o perfiles ajenos a los ocho sinteticos. Cada proceso genera una vez su reporte; si falla, se registra y puede reintentar en el siguiente ciclo.

Es un corte al completar el primer ciclo de ESE worker, no una barrera sincronizada de ocho procesos. El informe muestra cuales sesiones estan presentes y sus fechas: durante un reinicio escalonado puede incluir workers de la sesion anterior. Se puede volver a ejecutar el script tras terminar todos los primeros ciclos. El reporte no es una automatizacion externa ni reinicia procesos.

Las tasas se refieren a candidatos puntuados, no a trades ejecutados. Los conteos del embudo usan otro denominador. Los archivos consolidados se guardan fuera de la carpeta de entrada para no recontarlos.
