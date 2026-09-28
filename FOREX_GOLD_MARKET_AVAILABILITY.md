# Forex y GOLD sin kill zones

Por defecto gold_smc_session_enabled=False y forex_rollover_guard_enabled=False.
Eliminados bloqueo horario y force-flat asociado al rollover. Noticias, spread,
SMC, riesgo y objetivos permanecen. ORB conserva su sesión NY.

El scheduler consulta ticks ejecutables MT5 por símbolo, cacheados60segundos.
Acepta timestamps de hasta180segundos y bid/ask positivos. Si no hay ninguno
 disponible pausa análisis y publica OUTSIDE_SESSION con motivo mercado cerrado
o cotizacionesMT5 no disponibles. Revisa automáticamente; mantiene gestión de
posiciones y estado manual de desactivación. Si algunos cotizan, analiza esos.

Es una comprobación de disponibilidad, no calendario oficial del broker: falta de
conexión o cotizaciones antiguas también pausa. Puede tardar hasta3min en detectar
un cierre por ausencia de ticks, más el intervalo de comprobación. Las validaciones
de ejecución del broker siguen vigentes. No incorpora calendario de feriados.

Reiniciar workers/dashboard para cargar cambios. No se reiniciaron ni enviaron
órdenes durante esta implementación. Panel muestra PAUSADO · SESIÓN / MERCADO,
razón y próxima comprobación; no activa workers deshabilitados manualmente.
