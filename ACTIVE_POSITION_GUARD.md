# Control de posición activa del worker

El flujo central `LiveTradingEngine.process_symbol` consulta posiciones y órdenes pendientes reales antes de analizar H1/M15/M5/M1. La consulta no filtra por magic: también bloquean posiciones manuales y de otros workers en el mismo símbolo exacto del broker. Otros símbolos continúan.

- `BLOCKED_ACTIVE_TRADE`: una o más posiciones siguen abiertas. Mover el SL a BE o cerrar parcialmente no libera el símbolo.
- `BLOCKED_PENDING_ORDER`: existe una orden pendiente; se espera ejecución o cancelación.
- `BLOCKED_POSITION_STATE_UNAVAILABLE`: consulta fallida, respuesta None, datos inválidos o adaptador sin interfaz de snapshots. No se interpreta como cuenta vacía.
- `BLOCKED_SYMBOL_CYCLE`: otro ciclo local mantiene la exclusión para ese símbolo.
- Sin posiciones ni órdenes: continúa el evaluador existente, con contexto H1 rango/expansión, OB M15, dual M5/M1 y límites 85/70.

El bloqueo se consulta otra vez después del análisis y antes del lote lógico de entrada. Un archivo de exclusión por símbolo serializa los ciclos de los workers de este proyecto, hasta terminar el envío/persistencia. La exclusión no coordina terminales externos ni bloquea acciones manuales en MT5.

Las piernas configuradas de una misma operación siguen formando un único lote de entrada. Mientras quede cualquier pierna abierta, no se inicia otra operación. Una cancelación o cierre manual también permite continuar cuando MT5 confirma que el símbolo está libre; no se deduce TP/SL/BE por ausencia del ticket.

La gestión de posiciones y sus protecciones continúa independientemente. El refresco visual de posiciones gestionadas muestra espera en lugar de ejecutar otra vez la estrategia de entradas. No se han cambiado las políticas de salida ni se han reiniciado workers.

## Telemetría

Los bloqueos se registran en el evento `ACTIVE_POSITION_GUARD` y en `pipeline_funnel.stage_counts.POSITION_GUARD`, conservando el estado específico, tickets y motivo. No incrementan el denominador de candidatos puntuados ni aparecen como rechazos H1/M15/M5.

## Adaptadores y pruebas

Los adaptadores MT5 implementan `get_open_positions()` y `get_pending_orders()` con consultas sin caché ni filtro de magic. Los ejecutores simulados deben implementar explícitamente ambos métodos; no disponer de ellos bloquea el ciclo por diseño.

Se verificaron 50 pruebas focalizadas: posiciones/órdenes, BE abierto, cierre parcial, estado inválido, exclusión local, desbloqueo tras resolución, orden surgida durante el análisis, pausa del análisis visual, riesgo dividido, gatillo dual y preflight.

La revisión adicional detectó fixtures antiguos de dry-run/fallback sin la nueva interfaz de snapshots (y sin contexto de ubicación H1 completo). Esa suite antigua no queda validada por las 50 pruebas focalizadas.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_active_position_guard.py tests/test_daemon_split_risk_management.py tests/test_dual_trigger.py -q -p no:cacheprovider
```
