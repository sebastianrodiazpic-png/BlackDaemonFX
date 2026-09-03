# DaemonBlackFx v32 — ORB New York + VWAP + POC

## Objetivo

Agregar una segunda estrategia independiente del pipeline SMC: **Opening Range Breakout (ORB)** para operar exclusivamente los siguientes mercados de Deriv/MT5:

- microXAUUSD (Oro)
- Wall Street 30 / US30 / Dow Jones 30
- US Tech 100 / USTEC / NASDAQ 100
- US500 / S&P 500

La estrategia sólo opera durante la sesión cash de Nueva York y usa `America/New_York`, por lo que el cambio DST se resuelve automáticamente.

## Router de estrategias

- Mercados ORB autorizados -> `ORB_NEW_YORK` exclusivamente.
- Resto de instrumentos -> pipeline SMC H1/M15/M5 existente.
- Un mercado ORB fuera de horario **no hace fallback a SMC**.

Esto evita mezclar dos tesis diferentes sobre el mismo instrumento.

## Horario ORB

Zona horaria: `America/New_York`.

- 09:30 NY: apertura.
- 09:30 <= vela < 09:45: construcción del Opening Range con 15 velas M1 cerradas.
- 09:45 <= hora < 16:00: ventana autorizada para ruptura.
- Desde 16:00: bloqueado.
- Sábados y domingos: bloqueado.

## Opening Range

Se calcula:

- `OR_HIGH`: máximo de las 15 velas M1 09:30-09:44.
- `OR_LOW`: mínimo de las mismas velas.
- `OR_MID`: punto medio.
- `OR_SIZE`: OR_HIGH - OR_LOW.

No existe señal mientras falte alguna de las 15 velas requeridas.

## Ruptura BUY

La última vela M1 cerrada debe realizar un cruce fresco:

1. cierre previo <= OR_HIGH;
2. cierre actual > OR_HIGH;
3. cierre actual > VWAP de sesión;
4. cierre actual > POC de sesión.

Sólo entonces se crea `ORB_SIGNAL_CONFIRMED` BUY.

## Ruptura SELL

La última vela M1 cerrada debe realizar un cruce fresco:

1. cierre previo >= OR_LOW;
2. cierre actual < OR_LOW;
3. cierre actual < VWAP de sesión;
4. cierre actual < POC de sesión.

Sólo entonces se crea `ORB_SIGNAL_CONFIRMED` SELL.

## VWAP

Se calcula desde 09:30 NY hasta la vela candidata mediante precio típico:

`(high + low + close) / 3`

ponderado por volumen.

Prioridad de volumen:

1. `real_volume` si el broker entrega valores reales > 0;
2. `tick_volume` como fallback;
3. peso uniforme sólo si no existe información de volumen.

## POC

El POC se calcula mediante un perfil de volumen aproximado de la sesión, con 24 bins de precio por defecto. El volumen de cada vela se asigna al bin de su precio típico y el bin con mayor volumen acumulado define el Point of Control.

**Importante:** este POC utiliza el volumen disponible en el feed MT5 de Deriv. Si el broker sólo entrega `tick_volume`, no equivale a un perfil de volumen centralizado de CME/COMEX. Se conserva `volume_source` en los diagnósticos para auditarlo.

## Stop Loss y objetivos

Configuración v1:

- `stop_mode = OPPOSITE_RANGE`.
- BUY: SL debajo de OR_LOW + buffer defensivo externo.
- SELL: SL encima de OR_HIGH + buffer defensivo externo.
- buffer por defecto: 2% del tamaño del Opening Range.
- objetivo lógico inicial: 2R.

El motor de riesgo existente sigue dimensionando volumen con el mismo presupuesto de riesgo configurado en el daemon. La gestión TP1/RUNNER, límites de riesgo y Break Even continúan perteneciendo al motor común de ejecución.

## Diagnósticos ORB

El análisis expone, entre otros:

- strategy_name / strategy_version
- orb_market
- session_date_ny
- session_open_ny
- opening_range_end_ny
- session_close_ny
- opening_range_high / low / midpoint / size
- breakout_candle_time / breakout_candle_time_ny
- previous_close / breakout_close
- crossed_up / crossed_down
- session_vwap
- session_poc
- vwap_buy_ok / vwap_sell_ok
- poc_buy_ok / poc_sell_ok
- volume_source

Estados explicables:

- `SYMBOL_NOT_ORB_ELIGIBLE`
- `WAITING_NEW_YORK_OPEN`
- `BUILDING_OPENING_RANGE`
- `WAITING_BREAKOUT`
- `ORB_BREAKOUT_FILTERED`
- `ORB_SIGNAL_CONFIRMED`
- `NO_ORB_SESSION`
- `INVALID_OPENING_RANGE`

## Descubrimiento de instrumentos

Cuando el daemon se ejecuta sin `--symbol` y sin un filtro explícito `--categories`, además del catálogo sintético existente intenta descubrir en MT5 los cuatro mercados ORB mediante alias seguros.

Los símbolos encontrados se agregan también al catálogo del dashboard bajo grupos `orb_ny_*`.

## Archivos principales

- `strategy/orb/new_york_orb.py`
- `strategy/orb/__init__.py`
- `strategy/execution/live_trading_engine.py`
- `app/main.py`
- `tests/test_orb_new_york_strategy.py`

## Validación

- 6 pruebas específicas ORB.
- 204 pruebas no-MT5 aprobadas en la regresión completa disponible.

No se modificó el algoritmo SMC para los instrumentos que siguen bajo SMC.
