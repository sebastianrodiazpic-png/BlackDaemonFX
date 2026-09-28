# DaemonBlackFx v114 · Recuperación Deriv y vigilancia de workers

## Objetivo

Evitar que el arranque concurrente de los workers agote temporalmente el
límite de la API pública de Deriv y excluya instrumentos válidos durante toda
la ejecución.

## Cambios

- Limitador de solicitudes compartido entre procesos mediante bloqueo de
  archivo compatible con Windows y Linux.
- Reintentos acotados con backoff exponencial para respuestas de rate limit.
- Arranque escalonado de los workers.
- Preflight reducido a M5 + tick. H1, M15 y M1 se validan en el primer ciclo.
- Fallos transitorios se clasifican como `DEFERRED`: el símbolo permanece en el
  worker y vuelve a intentarse automáticamente.
- `US SP 500` se resuelve de forma segura contra `US 500` (`OTC_SPC`).
- Variantes Forex standard/micro permanecen seleccionables, pero se asignan al
  mismo worker para no duplicar el mercado nativo entre procesos.
- Watchdog del coordinador: detecta un worker vivo sin progreso de log durante
  180 segundos. Si no tiene posiciones abiertas, solicita su reinicio; si
  administra riesgo vivo, conserva el proceso y genera una alerta auditable.

## Sin cambios

- Reglas SMC, GOLD, Forex y ORB.
- Frescura y confirmaciones M5.
- Horarios y exclusividad de ORB.
- Cálculo de lotaje, riesgo total, TP1/runner, SL o cuarentenas.
- MT5 continúa limitado a metadatos, riesgo y ejecución DEMO.

## Variables opcionales

```text
DAEMON_DERIV_MIN_REQUEST_INTERVAL_SECONDS=0.20
DAEMON_DERIV_RATE_LIMIT_RETRIES=4
DAEMON_DERIV_RATE_LIMIT_BACKOFF_SECONDS=0.75
DAEMON_WORKER_START_STAGGER_SECONDS=1.0
DAEMON_WORKER_STALL_TIMEOUT_SECONDS=180
```

Los valores predeterminados ya se aplican aunque no se copien al `.env`.

## Limitaciones reales del catálogo público

Un símbolo que Deriv no publique no se sustituye por otro mercado. En
particular, FLIP permanece bloqueado mientras no exista un equivalente público
correcto. Los índices estadounidenses pueden quedar `DEFERRED` fuera de su
sesión y reingresan automáticamente cuando vuelven a entregar ticks.
