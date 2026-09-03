# DaemonBlackFx v48 — Break Even no altera Win Rate

## Problema corregido
Una operación con `realized_rr` muy cercana a cero, por ejemplo:
- RR real: `+0.01R`
- PnL: `+0.33 USDT`

se estaba clasificando como `GANANCIA PARCIAL` y además incrementaba el contador
de ganadores porque el dashboard usaba `PnL > 0`.

## Nueva política estadística
Se define una banda neutral configurable en código:

`BREAK_EVEN_RR_TOLERANCE = 0.25`

Por lo tanto:
- `-0.25R <= RR real <= +0.25R` => BREAK EVEN
- `RR real > +0.25R` => WIN
- `RR real < -0.25R` => LOSS

Cuando no existe RR real, se mantiene fallback por PnL.

Los Break Even:
- sí suman en trades cerrados;
- sí suman su PnL al PnL neto;
- NO incrementan `wins`;
- NO incrementan `losses`;
- NO participan en el denominador del Win Rate.

## Ejemplo de la captura
Antes:
- Wins: 3
- Losses: 3
- Win Rate: 50%

Después:
- Wins: 2
- Losses: 3
- Break Even: 1
- Win Rate: 40%

## Áreas corregidas
- Cuenta activa / dashboard.
- Clasificación de cierres.
- Resumen SQLAlchemy.
- Sincronización futura de cierres MT5.
- Exportador `deriv_demo_trading_report.xlsx`.
- KPIs del XLSX.

La base de datos conserva el PnL monetario real. La reclasificación estadística no
borra ni altera el beneficio de +0.33 USDT; sólo evita considerarlo una victoria.
