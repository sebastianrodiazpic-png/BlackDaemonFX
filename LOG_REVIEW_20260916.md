# Revisión de entradas — 16 septiembre 2026

Corte de lectura aproximado: 13:32 UTC / 10:32 America/Santiago.
Fuente: ciclos fechados 2026-09-16 en storage/logs/bots y auditoría SQLite
consultada en modo lectura. Los conteos son evaluaciones repetidas, no señales únicas.
No se cambiaron reglas ni se enviaron órdenes.

3026 evaluaciones contabilizadas:
- 1121 sin contexto direccional H1.
- 1008 sin confirmación M5.
- 505 sin setup M15.
- 205 con señal M5 antigua.
- 101 por política direccional Boom/Crash.
- 70 esperando M5 posterior al setup M15.
- 7 formando el rango ORB.
- 6 por ubicación premium/discount.
- 3 errores técnicos.

No se encontraron nuevas operaciones con entry_time del día en trades al consultar.
El archivo de cuarentena está vacío. Los workers activos publican ciclos recientes.
Los ciclos sin símbolos alternan con evaluaciones al cierre M5; no prueban una falla.

ORB a las 13:30 UTC estaba formando su rango 09:30–09:45 de Nueva York.
No debía tener entradas de la sesión actual antes de las 13:45 UTC.

Errores técnicos confirmados por SQLite:
- 02:15:15 UTC, XAGUSDmicro, GOLD: [Errno 13] Permission denied.
- 04:00:35 UTC, EURJPY, FOREX_3: [Errno 13] Permission denied.
- 12:08:06 UTC, Volatility 100 Index, VOLATILITY_4:
  You have reached the rate limit for ticks_history.
Evaluaciones posteriores vuelven a aparecer; no hay evidencia de parada global.
Los errores de permisos no contienen traceback ni ruta en la auditoría:
no puede atribuirse su causa a un archivo o lock concreto con esta evidencia.

También aparecen rechazos de preflight por símbolos sin equivalente Deriv Charts.
Impiden usar esos instrumentos con el proveedor actual; no detienen los universos
compatibles que siguen apareciendo en los ciclos. El parser de logs conserva la
fecha del último ciclo; los mensajes preflight entre reinicios no deben interpretarse
como fallos de cada ciclo ni como conteos exactos de incidentes del día.

Señales antiguas: 205 rechazos; Volatility 75 Index presenta 48 de ellos.
La auditoría resumida consultada no conserva signal_age ni timestamps de velas.
Por tanto no está demostrado si se trata de candidatas históricas normales,
datos retrasados o un defecto de caché. Debe instrumentarse edad de señal,
última vela cerrada, fuente y cache-hit antes de relajar la caducidad.

Latencia: máximos de ciclos entre ~39 y 80 segundos según worker SMC.
Superan intervalos objetivo de 10/30 segundos, pero son menores que una vela M5;
no demuestran que hayan causado por sí solos los rechazos de antigüedad.

Prioridad:
1. Persistir traceback/ruta en excepciones de símbolos para localizar permisos.
2. Medir y limitar consultas compartidas a ticks_history; backoff con jitter.
3. Persistir señal/última vela/edad/caché para auditar STALE_M5_SIGNAL.
4. Desglosar NO_H1_CONTEXT y NO_M5_CONFIRMATION por condiciones faltantes.
No reducir umbrales de riesgo ni eliminar confirmaciones únicamente para aumentar entradas.
