# DaemonBlackFx v49 — Sintéticos divididos por proceso

## Objetivo
Reducir el tiempo efectivo entre análisis de una misma familia sintética evitando que
un único proceso deba recorrer todo el universo de instrumentos.

## Workers sintéticos
- BOOM — magic `26082101`
- CRASH — magic `26082102`
- VOLATILITY — magic `26082103`
- STEP — magic `26082104`
- JUMP — magic `26082105`
- FLIP — magic `26082106`

Cada worker:
- descubre sólo instrumentos de su categoría;
- procesa únicamente la selección persistente que corresponda a su familia;
- tiene ciclo independiente;
- tiene magic independiente;
- administra únicamente sus posiciones;
- persiste en la DB compartida.

## Ejecución independiente
Ejemplos:

`python -m app.main --mode boom-daemon --execute --interval 30 --position-monitor-interval 2 --risk-percent 1.0 --min-rr 1.5`

`python -m app.main --mode crash-daemon --execute --interval 30 --position-monitor-interval 2 --risk-percent 1.0 --min-rr 1.5`

`python -m app.main --mode volatility-daemon --execute --interval 30 --position-monitor-interval 2 --risk-percent 1.0 --min-rr 1.5`

## Ejecución coordinada de todos los sintéticos
`python -m app.main --mode synthetics-split-daemon --execute --interval 30 --position-monitor-interval 2 --risk-percent 1.0 --min-rr 1.5 --report-interval 30`

El coordinador levanta BOOM, CRASH, VOLATILITY, STEP, JUMP y FLIP como procesos Python separados.

## Reporter
Los workers v49 escriben DB, no XLSX directamente. Para ejecución manual independiente:
`python -m app.main --mode report-daemon --report-interval 30`

Así existe un único escritor de `deriv_demo_trading_report.xlsx`.

## Compatibilidad
El modo agregado `synthetic-daemon` se mantiene por compatibilidad, pero para optimizar
latencia se recomienda usar los workers divididos.

Las posiciones legacy del magic histórico `26082026` pueden ser administradas por el
nuevo worker de su propia familia, pero nunca por otra familia.

## Full multi-bot
`multi-bot-daemon` ahora puede coordinar:
BOOM + CRASH + VOLATILITY + STEP + JUMP + FLIP + FOREX + ORB.

Todos comparten SQLite en WAL y el reporte consolidado.
