# Forex: ventana diaria y cierre preventivo

Referencia configurable: America/New_York, rollover/reapertura 17:00.
Entradas desde la reapertura hasta 14:00 exclusiva; cierre automático de
posiciones Forex propias desde 16:45 hasta 17:00 exclusiva, sin condición de PnL.
Domingo abre a las 17:00; viernes desde 17:00 y sábado no se permiten entradas.
Se respetan la disponibilidad real del broker y los filtros existentes de spread.
Esto es una referencia horaria configurada, no un calendario de festivos del broker.

El monitor sigue activo aunque se pause el análisis a las 14:00. Registra cada
intento en FOREX_SCHEDULED_CLOSE y reintenta fallos en las siguientes pasadas dentro
de la ventana. Utiliza el ejecutor de órdenes del lifecycle. No toca posiciones
externas/manuales, oro ni sintéticos. La ventana no garantiza una ejecución si
el broker o la conexión no están disponibles. Un worker apagado no puede cerrar.

Configuración: forex_rollover_guard_enabled=True, cutoff 14:00,
forex_force_flat 16:45, forex_market_reopen 17:00, timezone America/New_York.
La hora UTC cambia automáticamente con DST. Se revalida el horario justo antes
del envío, además del filtro inicial. SL/TP y otras reglas de gestión no se alteran.

GBPCAD 192: el historial local muestra salida 1.87826 con SL 1.87800 a las
21:10 UTC del 22-09-2026 (17:10 NY), exit_reason=mt5_history_sync. No hay evidencia
registrada de cierre por invalidación. Ese dato no prueba por sí solo que el
spread causara la activación; se necesita el motivo del deal y las cotizaciones.

Requiere reiniciar workers Forex. No se enviaron órdenes ni se reiniciaron procesos.
Pruebas de límites horarios, DST, fin de semana, exclusión de símbolos/propietarios,
cierres en pérdida/ganancia y reintentos. Política ORB fija se conserva.
