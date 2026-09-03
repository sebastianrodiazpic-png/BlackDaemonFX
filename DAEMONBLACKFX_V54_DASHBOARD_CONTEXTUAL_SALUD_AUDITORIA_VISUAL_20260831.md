# DaemonBlackFx v54 — Dashboard contextual + salud + auditoría visual multi-bot

## 1. Último candidato por bot
El bloque `Último candidato analizado` deja de ser global/ambiguo.

Selector:
- TODOS
- BOOM
- CRASH
- VOLATILITY
- STEP
- JUMP
- FLIP
- FOREX
- ORB

Cada lectura muestra bot, magic, ciclo, acción y timestamp. `TODOS` usa el worker
con actividad más reciente.

## 2. Salud de posiciones
La salud ya no asume que toda fila distinta de `MT5_EXTERNAL` es equivalente ni
asigna un 50/100 cuando no existe telemetría real.

Se incorporan:
- owner_profile;
- owner_magic;
- ownership_status;
- estado/PID del worker;
- reconciliación de legacy magic `26082026` por familia;
- detección de filas `MT5_EXTERNAL` cuyo magic sí corresponde a un bot;
- `SIN TELEMETRÍA DEL WORKER` cuando falta snapshot de mercado;
- `SOLO VISUALIZACIÓN` para posiciones realmente externas;
- score `N/D` cuando no hay datos suficientes.

El resumen distingue:
Mantener / Vigilar / Proteger / Salida / Sin datos / Visual.

## 3. Auditoría visual multi-bot
Problema anterior: los workers coordinados no tenían `dashboard_service`, por lo que
`_dashboard_chart_snapshots()` devolvía vacío y el coordinador no recibía gráficos.

v54:
- genera snapshots visuales aunque el worker no tenga servidor HTTP;
- sólo genera auditoría para posiciones propiedad de ese worker;
- persiste cada 30s en `position_visual_audits`;
- guarda gráfico M1/M5/M15/H1 + snapshot de mercado/R;
- el dashboard central reconstruye el gráfico desde SQLAlchemy;
- muestra owner/magic y hora de última auditoría visual;
- el análisis actual del símbolo se obtiene desde `daemon_audit_events`, no desde
  un estado global stale.

## Principio de seguridad
La interfaz no inventa salud. Si no existe telemetría reciente, muestra N/D y el
motivo. Ningún cambio de esta versión modifica las reglas de entrada, riesgo,
Break Even, Runner o cierres.
