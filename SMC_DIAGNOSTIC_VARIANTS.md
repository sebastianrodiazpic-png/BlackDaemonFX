# Diagnóstico y variantes SMC

Implementación tras la revisión del 16 septiembre 2026.

Configuración activa conservada: ALL_TIMEFRAMES y STRICT. No se modificó el
80%, desplazamiento, riesgo, RR, caducidad M5 ni contexto neutral H1.
Reiniciar workers para cargar los nuevos diagnósticos.

LiveTradingConfig.smc_entry_location_policy permite H1_PRIMARY: exige BUY en
discount H1 / SELL en premium H1, tanto en análisis como con cotización ejecutable.
ALL_TIMEFRAMES conserva H1/M15/M5. Los rangos siguen siendo móviles de100 velas;
no se sustituyeron por swings estructurales sin validar ese cambio por separado.
Se registra comparación de ambas políticas cuando se alcanza el guard de zona.

LiveTradingConfig.retest_tolerance_mode permite ATR_BOUNDED: tolerancia máxima
max(límite estricto, min(0.75, 0.10*ATR14/tamañoOB)). ATR usa15 velas anteriores
al retest; sin historia suficiente conserva la tolerancia estricta. Mantiene
rechazo por mecha y respeto del OB. No utiliza spread en puntos sin conversión
confiable a precio. La alternativa de rechazo únicamente por cierre queda
pendiente de estudio, no habilitada.

Auditoría compacta: swings/contexto H1, candidato M5 rechazado y condiciones
críticas, tiempo de última vela, edad de señal, caché por etapa, comparación de
retest y ubicación. Secuencia: número de confirmaciones anteriores al último
setup. No se recuperan automáticamente setups antiguos sin verificar vigencia.

python -m tools.smc_shadow_report --database RUTA --since 2026-09-17
consulta SQLite en modo lectura y compara evaluaciones nuevas. No representa
señales únicas, fills ni beneficio. Los datos antiguos sin campos comparativos
no permiten reconstruir esos resultados.

Validación funcional: pruebas de regresión, compras/ventas, falta de H1, política
inválida, límite de penetración, ausencia de datos futuros y persistencia de
rechazos. Falta replay histórico completo fuera de muestra con costes de
spread/ejecución, expectativa y drawdown antes de promover variantes a default.
No hay evidencia suficiente para afirmar mejora de rentabilidad.
