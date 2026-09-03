# DaemonBlackFx v52 — Dashboard real por familias

## Corrección
El dashboard central de v51 todavía cargaba `last_state.json`, pensado originalmente
para un único daemon. Esto podía mostrar estados antiguos como GBPUSD aunque el
coordinador actual sólo ejecutara sintéticos.

## v52
Se crea la tabla persistente `worker_runtime_states`.

Cada worker publica en SQLAlchemy:
- familia / bot_profile;
- magic;
- PID;
- estado;
- ciclo actual;
- total de instrumentos;
- instrumentos procesados;
- instrumento actual;
- última acción;
- último motivo;
- tiempo del último análisis;
- timestamp de actividad.

El dashboard central consulta esta tabla en `/api/state` y presenta tarjetas
independientes para BOOM, CRASH, VOLATILITY, STEP, JUMP y FLIP.

Los indicadores superiores ahora son agregados del coordinador:
- workers activos;
- progreso agregado;
- actividad más reciente;
- operaciones abiertas.

El último candidato también prioriza la actividad persistida del worker más reciente,
en lugar del antiguo estado único del dashboard.
