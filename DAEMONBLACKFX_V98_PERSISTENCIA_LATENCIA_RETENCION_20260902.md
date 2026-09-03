# DaemonBlackFx v98 — persistencia, latencia y retención

> Revisión v98.1: cierre explícito de las dos conexiones SQLite del respaldo
> antes de renombrar el archivo temporal. Corrige `WinError 32` en Windows.

## Objetivo

Esta versión reduce contención SQLite y evita que un monitor lento envejezca
las señales. No modifica la frescura M5, los gates estructurales SMC, los
umbrales ARPS ni `min_actual_risk_ratio`.

## Cambios

- Backup SQLite consistente mediante la API `backup`, incluyendo transacciones WAL.
- PRAGMA homogéneos por conexión: `busy_timeout`, WAL autocheckpoint,
  `journal_size_limit`, cache y `PRAGMA optimize`.
- Índices compuestos para auditoría, trades OPEN y runtime de workers.
- Auditoría operacional compacta: deja de repetir el árbol H1/M15/M5 completo.
- Muestreo de estados repetidos ARPS/SMC cada cinco minutos; cambios de estado,
  señales y rechazos de riesgo se guardan inmediatamente.
- Retención automática de 14 días y máximo 250.000 eventos operacionales.
- Trades, journal, entradas/salidas, incidentes, auditorías visuales y snapshots
  de operaciones no forman parte de la eliminación.
- Monitor de posiciones en hilo de fondo por worker. El scanner de nuevas velas
  ya no espera a que termine sincronización, Break Even, gráficos o persistencia.
- Break Even y cierres siguen revisándose cada 2 segundos; la reconstrucción
  visual M1/M5/M15/H1 se limita a una vez cada 30 segundos y reutiliza snapshots.
- La caché multi-timeframe permite lecturas concurrentes seguras del monitor sin
  serializar el pipeline de señales.
- `WAITING_NEW_M1_BAR` diferencia correctamente los workers ARPS de M5.
- Exportación XLSX periódica cambia de 30 a 300 segundos para evitar reconstruir
  el libro completo sin necesidad.
- Reporte bajo demanda para evaluar filtros y riesgo con datos compactos.

## Primer mantenimiento recomendado

Detener completamente el daemon y ejecutar:

```powershell
python -m app.main --mode db-maintenance --confirm-db-maintenance --vacuum
```

El comando crea primero un respaldo consistente, aplica retención, trunca WAL,
compacta el archivo con `VACUUM` y valida `integrity_check`.

No debe ejecutarse mientras exista un `multi-bot-daemon` activo; el bloqueo de
instancia cancela el mantenimiento si detecta otro coordinador.

## Arranque normal

El comando operativo no cambia:

```powershell
python -m app.main --mode multi-bot-daemon --execute --interval 30 --position-monitor-interval 2 --risk-percent 1.0 --min-rr 1.5 --dashboard --dashboard-port 8765
```

La consola debe mostrar `monitor_mode: BACKGROUND_DECOUPLED` en los workers.

## Evaluación ARPS y riesgo

Después de acumular al menos 24 horas:

```powershell
python -m reporting.strategy_evaluation --hours 24
```

Salida:

`storage/analysis/strategy_evaluation.json`

El archivo resume:

- acciones por estrategia;
- confirmaciones faltantes de ARPS;
- distribución de ADX y spread/ATR;
- latencia por estrategia;
- señales M5 antiguas;
- riesgo solicitado, riesgo ejecutable y proporción alcanzada.

Con esos datos se podrá decidir si conviene ajustar ARPS o el riesgo mínimo sin
debilitar anticipadamente los filtros de estructura/frescura.
