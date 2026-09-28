# Forex: protección de ejecución y auditoría de spread — 23/09/2026

## Política

Se conserva la ventana existente basada en America/New_York: nuevas entradas hasta 14:00 exclusiva, cierre preventivo desde 16:45 hasta 17:00 exclusiva y reapertura calendario desde 17:00, con fines de semana y DST. El supervisor ya conserva workers con posiciones propias abiertas; el monitor puede cerrar aunque el análisis esté pausado. No se altera el calendario ni se añade un cierre por spread a posiciones existentes.

Al iniciar el worker se registra FOREX_EXECUTION_POLICY_ACTIVE con el horario y los límites realmente cargados. Esto permite verificar la activación tras el reinicio.

## Nuevo control de entrada

Aplicable a workers FOREX y símbolos Forex. Comprueba horario y cotización MT5 antes de ejecutar y nuevamente antes de cada tramo. Si un tramo posterior falla el control, no se envía; el tramo ya abierto conserva su gestión y sus barreras. El resultado informa partial_execution.

Valores iniciales configurables en LiveTradingConfig:

- forex_spread_guard_enabled=True.
- forex_spread_baseline_samples=20.
- forex_spread_max_multiple=2.0: spread máximo relativo a la mediana habitual.
- forex_spread_max_pips=5.0: límite absoluto; pip 0,01 para pares JPY y 0,0001 para los demás.
- forex_spread_max_risk_ratio=0.10: spread / distancia desde el precio ejecutable al SL.
- forex_spread_stable_samples=5: cinco observaciones normales separadas aproximadamente 15 segundos.

Estos umbrales son iniciales, no una calibración histórica por instrumento. Se registran admisiones y rechazos como FOREX_EXECUTION_SPREAD, con razón, bid/ask, fechas, ratio y baseline. El control no mueve SL ni TP.

## Normalización y aprendizaje del spread habitual

El monitor toma cotizaciones cada 15 segundos, independientemente de que exista una señal M5. Usa símbolos Forex configurados y posiciones propias. El baseline guarda hasta 720 muestras durante un máximo de siete días por símbolo; excluye 16:00–18:00 NY, cotizaciones inválidas, spreads superiores al máximo absoluto y picos sobre 2x la mediana ya establecida.

Las primeras 20 muestras son calentamiento. Se necesitan luego cinco observaciones normales: con muestreo continuo, aproximadamente seis minutos desde un arranque sin historial. No se permite entrar mientras falta baseline. Si el arranque ocurre dentro del intervalo excluido, deberá esperar muestras válidas fuera de él.

La estabilidad se reinicia al cambiar la sesión de las 17:00 NY, ante spread anormal, cotización ausente o pausa de muestreo superior a 45 segundos. La mediana persiste entre reinicios. Varias llamadas consecutivas antes de enviar órdenes no cuentan como varias observaciones independientes. A las 17:00 no se reabre operativa por reloj solamente: debe normalizarse el spread.

Persistencia: storage/runtime/forex_spread/<worker>.json. El dashboard muestra la razón actual, pips, muestras, observaciones estables y fecha en el panel de diagnóstico SMC del worker.

## Evidencia de posiciones y cierres

Las operaciones Forex propias conservan las últimas 80 observaciones en details.metadata.forex_execution_quotes. Los eventos FOREX_POSITION_QUOTE conservan cada muestra auditada y los IDs de operaciones. FOREX_SCHEDULED_CLOSE incluye la cotización previa al intento de cierre.

Al reconciliar MT5, broker_exit mantiene su motivo y añade last_sampled_quote y last_sample_age_seconds. Solo selecciona muestras capturadas antes del deal. bid_ask_at_exit sigue desconocido cuando no existe tick exacto de salida; una muestra cercana no se atribuye falsamente al momento del SL.

No se reconstruye el spread histórico de GBPCAD ni se afirma que fuera la única causa de su pérdida. El cambio aporta protección y evidencia futura.

## Validación y activación

91 pruebas aprobadas: calentamiento, límites absoluto/relativo y respecto al SL, normalización tras rollover, continuidad y persistencia, timestamps inválidos/antiguos, cotizaciones ausentes, JPY, exclusión de GOLD, conservación de barreras, registro SQLite y regresiones de horarios Forex/ORB/SMC/GOLD. JavaScript del dashboard validado con Node.

Requiere reiniciar workers y dashboard. Esta tarea no reinició procesos ni envió órdenes. Los procesos activos no cargan automáticamente los cambios de Python. El cierre preventivo continúa dependiendo de que el worker, el terminal y la conexión estén disponibles dentro de su ventana configurada.
