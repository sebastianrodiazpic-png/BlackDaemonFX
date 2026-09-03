# DaemonBlackFx v51 — Dashboard central para arquitectura Multi-Bot

## Problema
`synthetics-split-daemon` creaba workers con `--coordinated-worker`, por lo que cada
worker deshabilitaba correctamente su dashboard individual. Sin embargo, el
coordinador no iniciaba un dashboard propio y los flags `--dashboard` y
`--dashboard-port` quedaban sin efecto.

## Solución
El coordinador inicia un único `RealtimeDashboardService` cuando se utiliza
`--dashboard`.

Ejemplo:
`python -m app.main --mode synthetics-split-daemon --execute --interval 30 --position-monitor-interval 2 --risk-percent 1.0 --min-rr 1.5 --report-interval 30 --dashboard --dashboard-port 8765`

URLs:
- Dashboard: `http://127.0.0.1:8765`
- Instrumentos: `http://127.0.0.1:8765/instruments`
- Cuenta activa: `http://127.0.0.1:8765/account`

## Diseño
- Un solo servidor HTTP.
- Los workers BOOM/CRASH/VOLATILITY/STEP/JUMP/FLIP no abren puertos.
- El dashboard usa la DB compartida.
- El catálogo se reconstruye para los perfiles coordinados.
- La selección persistente continúa en SQLAlchemy.
- Al detener el coordinador, el dashboard queda marcado offline y el servidor se cierra.

Esto evita conflictos de puerto y conserva una vista consolidada de la arquitectura.
