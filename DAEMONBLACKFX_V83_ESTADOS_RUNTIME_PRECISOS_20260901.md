# DaemonBlackFx v83 — estados runtime precisos

Los ciclos Forex sin una nueva vela M5 ya no se confunden con una selección
vacía. Los estados son ahora:

- `WAITING_NEW_M5_BAR`: instrumentos y datos disponibles; espera una nueva M5.
- `WAITING_FOREX_DATA`: MT5 no entregó velas; posible mercado cerrado o datos pendientes.
- `DEGRADED_NO_SYMBOLS`: selección/configuración realmente vacía.
- `RUNNING`: existen instrumentos pendientes de análisis.

El inicio del ciclo se registra después de resolver la selección y el scheduler,
y limpia `current_symbol` para no mostrar el último par como análisis actual.
