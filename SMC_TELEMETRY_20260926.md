# Telemetria del score adaptativo SMC

Implementacion: strategy/smc/telemetry_logger.py, clase SMCTelemetryTracker.

LiveTradingEngine asigna bot_profile como identidad al PipelineConfig, tambien cuando recibe una configuracion externa sin identidad. Trade pipeline propaga identidad y simbolo a M5ConfirmationConfig. confirmation_engine registra el resultado real de calculate_adaptive_score cuando la ruta adaptativa esta activa; no se crea un pipeline alternativo con funciones ficticias.

## Metricas
- STRICT_APPROVED, ADAPTIVE_APPROVED, REJECTED_CRITICAL_VETO y REJECTED_LOW_SCORE. El REJECTED original se normaliza como veto. Estados inconsistentes se cuentan como REJECTED_OTHER para que la suma coincida con total.
- Total, tasa de aprobacion, puntuacion media acumulada, conteos por simbolo y los tres motivos principales.
- Una etapa se cuenta una sola vez por candidato. Un candidato puede fallar varias etapas, por lo que los porcentajes entre etapas no forman una distribucion exclusiva.
- La media usa suma y contador, independientemente del historial acotado de las ultimas 1000 puntuaciones.
- La unidad es simbolo + setup + direccion + limites OB + retest + vela de confirmacion. Se cuenta la primera evaluacion de esa identidad en la cache; recalculos no vuelven a sumarla. La deduplicacion guarda hasta 50000 identidades por worker/proceso; tras eviction o reinicio una identidad puede volver a contarse.

## Alcance
Son candidatos que llegaron al score, no todos los ciclos ni operaciones ejecutadas. Los bloqueos anteriores H1/M15 no entran en el denominador del score; ahora se registran tambien en pipeline_funnel, descrito al final. Los rechazos de riesgo/ejecucion posteriores no se conectaron a este contador: RISK_EXECUTION permanece en cero salvo registro explicito. No interpretar ese cero como ausencia de bloqueos posteriores.

## Reporte
Cada 100 evaluaciones nuevas se escribe SMC TELEMETRY en logging INFO, usando los handlers del worker. No se fuerza stdout. JSON atomico en storage/runtime/smc_telemetry/<worker>_<pid>.json: primera evaluacion, cada 30 segundos con nueva evaluacion, cada 100 y al salir normalmente. flush() permite guardar expresamente. No existe un temporizador independiente; una terminacion forzada puede perder los ultimos contadores no guardados.

Contadores de sesion en UTC, no restaurados del archivo al arrancar ni reiniciados automaticamente a medianoche. reset_counters() reinicia explicitamente la sesion. La ruta se crea al primer uso real. Fallos de observabilidad se registran sin alterar aprobacion, score, riesgo ni ejecucion.

## Uso directo
from strategy.smc.telemetry_logger import SMCTelemetryTracker
tracker = SMCTelemetryTracker(bot_name="SMC_Synthetic_Worker_01")
tracker.log_evaluation(eval_result, symbol, evaluation_id="identidad-del-candidato")
report = tracker.get_summary_report()
tracker.print_telemetry_dashboard()

Sin evaluation_id, cada llamada se cuenta. Sin output_dir, el uso directo no escribe archivos. El registro del motor usa el tracker compartido por worker con persistencia habilitada.

No se reiniciaron bots ni se enviaron ordenes durante la implementacion.


## Ampliacion: embudo completo del analizador

Se conecta MultiTimeframeAnalyzer._build_result, por donde pasan todas las salidas. El JSON incorpora pipeline_funnel con total, stage_counts, stage_pct, action_counts, symbol_stage_counts, top_3_rejection_reasons y last_result. H1, M15 y M5 son etapas terminales exclusivas. SIGNAL_READY significa señal lista del analizador, no orden enviada. Politica de instrumento, ubicacion final y otras salidas tienen categorias propias.

El denominador del embudo es distinto al de los candidatos puntuados. No sumar ambos totales: una misma cadena de analisis puede contribuir a ambos. Los scores conservan las aprobaciones estrictas/adaptativas y motivos detallados del confirmation_engine. El embudo conserva el motivo terminal del analizador; NO_DIRECTIONAL_M15_SETUP no atribuye falsamente el bloqueo a una unica causa entre todos los bloques historicos examinados.

La unidad del embudo es una observacion terminal por simbolo, accion, direccion, setup, motivo y bloque de 5 minutos de reloj UTC. Los ciclos repetidos dentro del bloque no se suman; una nueva observacion posterior si. No son operaciones ni oportunidades independientes. La cache acotada tiene las mismas limitaciones de reinicio/eviccion que el score.

Cada 100 nuevas observaciones del embudo se emite un reporte, incluso si ningun candidato llego al score. Se conserva tambien el reporte cada 100 candidatos puntuados. Los motivos H1 distinguen H1_RANGE_UNAVAILABLE, H1_PRICE_UNAVAILABLE, H1_PRICE_OUTSIDE_RANGE y H1_PRICE_AT_EQUILIBRIUM. Riesgo/ejecucion posteriores siguen fuera del alcance de este hook.
