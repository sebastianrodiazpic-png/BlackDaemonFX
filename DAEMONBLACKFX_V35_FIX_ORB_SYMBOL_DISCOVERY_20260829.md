# DaemonBlackFx v35 — Corrección descubrimiento ORB Deriv

## Problema detectado en preflight
El clasificador ORB aceptaba la palabra genérica `gold` como alias de XAUUSD.
Esto incorporaba productos Deriv ajenos a la estrategia, por ejemplo:
- Gold BB Pullback Index
- Gold BB Rebound Index
- Gold MACO Long Term Index
- Gold MACO Short Term Index

Varios de esos instrumentos tienen `trade_mode = 0`, por lo que el preflight
marcaba correctamente `SYMBOL_TRADING_DISABLED` y dejaba todo el daemon en
`STATUS: NOT READY`.

## Corrección
- Oro ORB estándar: `XAUUSD`.
- Oro ORB micro real en la cuenta observada: `XAUUSDmicro`.
- Se conserva `microXAUUSD` como alias legado de clasificación, pero no se
  presupone que exista con ese nombre en MT5.
- Se eliminó `gold` como alias genérico.
- El descubrimiento ORB filtra `trade_mode == 0` antes de incorporar un símbolo.
- Gold BB/MACO y otros productos derivados dejan de formar parte del universo ORB.

## Gestión de riesgo
No cambia:
- 1% total por operación lógica.
- TP1 = 0,5% a 1R.
- RUNNER = 0,5% a 2R.
- Break Even del RUNNER a entrada ± 2 puntos.
- Selector XAUUSD vs XAUUSDmicro por precisión de riesgo, spread y margen.
