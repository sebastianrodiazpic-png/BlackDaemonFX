# DaemonBlackFx v10 — Selección dinámica de instrumentos

## Objetivo

Permitir seleccionar desde el dashboard local los instrumentos que el daemon puede analizar para nuevas entradas, sin reiniciar el proceso.

## Funcionamiento

- El catálogo se descubre directamente desde los instrumentos sintéticos tradeables expuestos por MT5/Deriv en la sesión activa.
- Los instrumentos aparecen agrupados por categoría y ordenados alfabéticamente.
- Las categorías también se ordenan alfabéticamente por su nombre visible.
- La selección es múltiple.
- El usuario puede seleccionar todos, limpiar temporalmente la selección y aplicar una nueva lista.
- El sistema exige al menos un instrumento activo.
- Una selección nueva entra en vigor al comienzo del siguiente ciclo de análisis; nunca modifica la lista a mitad de ciclo.
- Las posiciones que ya están abiertas continúan siendo monitoreadas por Break Even y por el monitor de salud aunque su instrumento sea desmarcado para nuevas entradas.

## Endpoint local

El dashboard expone:

- GET `/api/state`: estado completo del dashboard.
- POST `/api/instruments/selection`: actualiza `selected_symbols`.

El servidor permanece enlazado a `127.0.0.1` por defecto.

## Seguridad operacional

El selector no envía órdenes directamente. Solo modifica la lista de símbolos que `LiveTradingEngine.run_daemon()` toma como snapshot al inicio de cada ciclo. La ejecución, gestión de riesgo, Break Even y monitoreo de posiciones continúan dentro del flujo normal del engine y del mismo hilo de MT5.

## Inicio

```bash
python -m app.main --mode demo-daemon --execute --interval 30 --risk-percent 1.0 --min-rr 1.5 --dashboard
```

Dashboard:

`http://127.0.0.1:8765`

## Pruebas

La regresión disponible en el entorno Linux, excluyendo exclusivamente las pruebas que requieren MetaTrader5 nativo/Windows, finalizó con 167 pruebas aprobadas.
