# DaemonBlackFx v47 — Arquitectura Multi-Bot

## Objetivo
Separar la ejecución en tres procesos independientes:

1. `SYNTHETICS`
2. `FOREX`
3. `ORB`

Los tres comparten la misma base SQLAlchemy/SQLite y el mismo historial permanente,
pero cada proceso tiene universo de instrumentos y propiedad de posiciones independientes.

## Magic numbers
- SYNTHETICS: `26082026`
- FOREX: `26082027`
- ORB: `26082028`

Una posición sólo puede ser administrada (Break Even, Runner, rollover, cierres)
por el bot cuyo magic coincide con `details.metadata.daemon_magic`.

Las operaciones legacy previas a v47 sin `daemon_magic` se consideran propiedad
del bot SYNTHETICS únicamente, porque ese era el magic histórico `26082026`.

## Modos
### Sólo sintéticos
`python -m app.main --mode synthetic-daemon --execute --interval 30 --position-monitor-interval 2 --risk-percent 1.0 --min-rr 1.5`

### Sólo Forex
`python -m app.main --mode forex-daemon --execute --interval 30 --position-monitor-interval 2 --risk-percent 1.0 --min-rr 1.5`

### Sólo ORB
`python -m app.main --mode orb-daemon --execute --interval 30 --position-monitor-interval 2 --risk-percent 1.0 --min-rr 1.5`

### Los tres coordinados
`python -m app.main --mode multi-bot-daemon --execute --interval 30 --position-monitor-interval 2 --risk-percent 1.0 --min-rr 1.5 --report-interval 30`

## Coordinador
`multi-bot-daemon` inicia tres procesos Python independientes y:
- reinicia un worker si se cae;
- escribe logs separados en `storage/logs/bots/`;
- mantiene DB compartida;
- es el único escritor periódico de `deriv_demo_trading_report.xlsx`;
- registra start/stop/error de workers en `daemon_audit_events`.

Los workers coordinados tienen `auto_export=False`, por lo que no compiten por
el mismo XLSX.

## SQLite concurrente
La base se configura con:
- `PRAGMA journal_mode=WAL`
- `PRAGMA synchronous=NORMAL`
- `PRAGMA busy_timeout=30000`

Esto permite mejor convivencia de varios procesos sobre la misma SQLite.

## Selección de instrumentos
Cada bot filtra la selección persistente del dashboard por su universo:
- SYNTHETICS: Volatility/Boom/Crash/Step/Jump/Flip
- FOREX: pares FX
- ORB: instrumentos ORB New York

Si un perfil no tiene instrumentos seleccionados, el worker queda activo en modo
idle para auditoría/monitor, sin buscar nuevas entradas.

## Restricciones preservadas
- Sintéticos: operación 24/7.
- Forex: reinicia 08:00 Londres, bloqueo rollover y cierre preventivo.
- ORB: exclusivamente sesión New York.
- Persistencia v46: DB + trade_journal + daemon_audit_events.
- Runner 2R -> 3R -> 4R.
