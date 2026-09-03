# DaemonBlackFx v61 — ORB M5 + Retest + protección 50% ORB

## Entrada ORB
- Opening Range NY: 09:30–09:45 America/New_York.
- Timeframe ORB: M5.
- No entra en el breakout inmediatamente.
- Secuencia obligatoria: vela M5 de breakout -> siguiente vela M5 retestea el borde roto -> cierre nuevamente fuera del ORB.
- VWAP y POC continúan siendo confirmaciones obligatorias.

## Protección
- SL estructural en el 50% exacto del Opening Range (midpoint).
- Objetivo base del runner: 2R.

## Riesgo y toma de ganancias
- Riesgo total ORB: 1% de equity/balance configurado.
- TP1: 0.5% del riesgo, cierre automático a 1R.
- RUNNER: 0.5% del riesgo, busca 2R.
- Si a 2R existe continuación: asegura +1R y permite extensión a 3R.
- Si a 3R existe continuación: asegura +2R y permite extensión a 4R.
- Si no existe continuación en 2R/3R, cierra el runner automáticamente para materializar la ganancia.
- 4R es el máximo de extensión configurado.

No se modifican SMC, Forex, sintéticos, persistencia v57 ni arquitectura/dashboard v58-v60.
