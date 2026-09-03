# DaemonBlackFx - Split Risk + Break Even protector + SMC Harmonics

Fecha: 2026-08-28

## Objetivo

La gestión de una operación lógica mantiene un riesgo máximo total del 1% y se divide en dos posiciones independientes:

- TP1: 0.5% de riesgo y objetivo 1:1.
- RUNNER: 0.5% de riesgo y objetivo 1:2.
- Riesgo agregado máximo de la operación: 1.0%.

El volumen de cada pierna se calcula de forma independiente usando las restricciones reales del símbolo. Si el broker no permite aproximarse al riesgo objetivo de cada pierna sin excederlo, la operación se rechaza.

## Break Even protector

Al alcanzar 1R, el daemon protege únicamente la pierna RUNNER y mueve el Stop Loss a favor de la posición:

- BUY: `entry + (2 * point)`
- SELL: `entry - (2 * point)`

`point` se obtiene de las restricciones reales del símbolo MT5, por lo que "2 puntos" se adapta correctamente a cada instrumento. La modificación se confirma releyendo la posición desde MT5 antes de persistir el nuevo SL en SQLite.

TP1 no recibe Break Even porque su salida natural es el Take Profit a 1R.

## Estrategia SMC + patrones armónicos

El daemon usa patrones armónicos como confirmación de confluencia del setup Smart Money Concepts, no como estrategia aislada.

Patrones soportados actualmente:

- Gartley
- Bat
- Butterfly
- Crab

La confirmación utiliza los últimos pivotes X-A-B-C-D confirmados y valida relaciones Fibonacci, dirección del patrón, antigüedad del punto D y proximidad del punto D a la zona del Order Block/PRZ.

En modo daemon la confluencia armónica queda habilitada y requerida por defecto (`require_harmonic=True`). El patrón debe acompañar las validaciones SMC existentes: tendencia H1, setup M15, liquidity sweep, ruptura de estructura, premium/discount, Order Block y confirmación M5.

## Límites de posiciones

Para soportar las dos piernas de una misma operación:

- máximo por símbolo: 2 posiciones;
- máximo global por defecto: 6 posiciones = hasta 3 operaciones lógicas simultáneas.

El daemon reserva los dos slots antes de intentar abrir una operación dividida.

## Archivos principales modificados

- `strategy/execution/live_trading_engine.py`
- `strategy/smc/harmonic_patterns.py`
- `strategy/smc/confirmation_engine.py`
- `strategy/execution/trade_pipeline.py`
- `config/strategy_config.py`
- pruebas relacionadas en `tests/`

## Pruebas

Pruebas específicas nuevas/actualizadas:

- split de 1% -> 0.5% + 0.5%;
- TP1 a 1R y RUNNER a 2R;
- Break Even a entry +2 puntos;
- confluencia armónica requerida por el daemon;
- integración de dos lifecycles de ejecución;
- rechazo cuando el volumen máximo del broker impide alcanzar el riesgo objetivo.

Resultado en el entorno de validación Linux: 158 pruebas independientes de MT5 aprobadas. Las pruebas que importan directamente `MetaTrader5` no pueden recolectarse aquí porque ese paquete del proyecto es binario para Windows; deben ejecutarse en el PC Windows con MT5 instalado/conectado.

## Comando daemon

El comando operativo puede mantenerse:

```bash
python -m app.main --mode demo-daemon --execute --interval 30 --risk-percent 1.0 --min-rr 1.5
```

Con `risk-percent 1.0`, el motor interpreta el valor como riesgo TOTAL de la operación lógica y lo reparte entre TP1 y RUNNER; no aplica 1% a cada posición.
