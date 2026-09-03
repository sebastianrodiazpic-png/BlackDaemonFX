# DaemonBlackFx v54 — Contexto por bot + Salud + Auditoría visual persistente

## 1. Último candidato por bot
El dashboard central incorpora selector contextual:
- TODOS
- BOOM
- CRASH
- VOLATILITY
- STEP
- JUMP
- FLIP
- FOREX
- ORB

El candidato ya no depende del último heartbeat del worker. Se reconstruye desde
`daemon_audit_events` (`SYMBOL_PROCESS_RESULT`) por `bot_profile`, conservando:
- instrumento;
- bot/worker;
- magic;
- ciclo;
- score;
- confirmaciones;
- dirección;
- decisión;
- confluencias;
- timestamp.

## 2. Salud de posiciones
Se incorpora ownership explícito:
- `owner_profile`
- `owner_magic`
- `ownership_status`
- estado/PID del worker responsable.

Una posición gestionada sólo recibe score de salud si existe telemetría de mercado
suficiente. Si no hay current_price/current_rr:
- salud = SIN DATOS;
- no se muestra un 50/100 artificial;
- recomendación = SIN TELEMETRÍA DEL WORKER o WORKER SIN ACTIVIDAD.

Para `MT5_EXTERNAL`:
- no se calcula salud;
- queda como NO EVALUABLE;
- si contiene un magic conocido del daemon se marca inconsistencia para reconciliar,
  en vez de afirmar incorrectamente que “no tiene magic de DaemonBlackFx”.

Posiciones legacy del magic 26082026 pueden inferir owner por familia del símbolo.

## 3. Auditoría visual multi-bot
Nueva tabla:
`position_visual_audits`

Cada worker persiste aproximadamente cada 30 segundos, por posición propia:
- snapshot gráfico M1/M5/M15/H1;
- contexto SMC;
- velas/eventos/zonas;
- snapshot de mercado;
- bot_profile;
- daemon_magic;
- timestamp.

Esto ocurre aunque el worker no tenga dashboard HTTP propio.

El dashboard coordinador lee la auditoría visual desde SQLAlchemy, por lo que el
botón “Ver gráfico” deja de depender de `last_state.json` del coordinador.

## 4. Seguridad
No se modifican:
- reglas de entrada SMC;
- ORB;
- Forex;
- sizing/riesgo;
- Break Even;
- Runner TP3/TP4;
- cierres automáticos.

Los cambios son de telemetría, auditoría y representación.
