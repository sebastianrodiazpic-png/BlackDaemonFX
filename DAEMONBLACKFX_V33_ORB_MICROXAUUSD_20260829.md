# DaemonBlackFx v33 — ORB New York con microXAUUSD

## Cambio
La estrategia ORB New York deja de clasificar `XAUUSD` como mercado ORB y utiliza exclusivamente `microXAUUSD` para Oro.

Mercados ORB:
- microXAUUSD
- Wall Street 30
- US Tech 100
- US500

`XAUUSD` estándar queda fuera del router ORB.

## Impacto técnico
El nombre real `microXAUUSD` se propaga al proveedor MT5, por lo que el cálculo de volumen, `point`, `digits`, `trade_stops_level`, SL/TP y límites de lote se obtienen de las especificaciones del contrato micro, no de XAUUSD estándar.

No se modificaron:
- horario ORB 09:30–09:45 America/New_York;
- ventana de ruptura posterior;
- VWAP;
- POC;
- lógica BUY/SELL;
- gestión TP1/RUNNER;
- Break Even;
- estrategia SMC para los demás instrumentos.
