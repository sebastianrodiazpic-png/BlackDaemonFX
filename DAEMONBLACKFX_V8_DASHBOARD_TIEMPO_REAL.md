# DaemonBlackFx v8 - Dashboard de calidad en tiempo real

## Objetivo

Agregar una interfaz web local de solo lectura para observar la calidad de los setups y trades mientras el daemon continúa ejecutando la estrategia y MetaTrader5 en su hilo normal.

## Seguridad arquitectónica

El dashboard NO envía órdenes, NO modifica SL/TP y NO consulta MetaTrader5 desde un segundo hilo. Solo recibe snapshots creados por `LiveTradingEngine` y consulta las operaciones OPEN persistidas por el repositorio SQLite.

## Activación

Ejemplo:

```bash
python -m app.main --mode demo-daemon --execute --interval 30 --risk-percent 1.0 --min-rr 1.5 --dashboard
```

La consola mostrará:

```text
Dashboard de calidad en tiempo real: http://127.0.0.1:8765
```

Abrir esa dirección en el navegador del mismo equipo.

Puerto alternativo:

```bash
python -m app.main --mode demo-daemon --execute --interval 30 --risk-percent 1.0 --min-rr 1.5 --dashboard --dashboard-port 9000
```

## Información visible

- Estado del daemon y número de ciclo.
- Instrumento analizado actualmente.
- Progreso del ciclo (símbolos procesados / total).
- Score de calidad 0-100 y grado A+/A/B+/B/C/D.
- Porcentaje de confirmaciones.
- Decisión de confirmación.
- Dirección BUY/SELL.
- Confirmaciones cumplidas.
- Confirmaciones faltantes y críticas.
- Divergencia y tipo detectado.
- Patrón armónico y score, si existe.
- CHOCH/BOS disponible en el resultado.
- Premium/Discount cuando está disponible.
- Operaciones abiertas, modalidad SPLIT/SINGLE_FALLBACK, pierna, riesgo y estado de Break Even.
- Historial reciente de análisis por símbolo.

## Actualización

El navegador consulta `/api/state` cada segundo. El daemon actualiza el snapshot después de cada símbolo y de cada pasada del monitor de posiciones.

## Archivos principales

- `dashboard/realtime_dashboard.py`
- `dashboard/__init__.py`
- `strategy/execution/live_trading_engine.py`
- `app/main.py`
- `tests/test_realtime_dashboard.py`

## Pruebas

Regresión no-MT5: 168 pruebas aprobadas.
