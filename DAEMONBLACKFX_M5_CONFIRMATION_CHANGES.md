# DaemonBlackFx – Cambios completos de confirmación M5

## Nueva arquitectura
H1 define el contexto, M15 valida el setup SMC y M5 ejecuta un motor de confirmación de calidad antes de permitir una entrada.

## Nuevo archivo
- `strategy/smc/confirmation_engine.py`

## Archivos modificados
- `strategy/smc/entry_confirmation.py`
- `strategy/execution/trade_pipeline.py`
- `strategy/execution/multi_timeframe.py`
- `strategy/execution/live_trading_engine.py`
- `config/strategy_config.py`
- `tests/test_confirmation_engine.py`

## Flujo de entrada
1. H1 trend aligned.
2. M15 setup valid.
3. Liquidity sweep.
4. CHOCH/BOS M15.
5. Premium/Discount.
6. Order Block fresh.
7. Retest.
8. Rejection wick.
9. Displacement.
10. Micro structure break.
11. Momentum when enabled.
12. Confirmation mode.
13. Trade score >= configured threshold.

## Defaults
`minimum_trade_score=80`, rejection/displacement/micro structure required, momentum optional, body >= 60%, rejection wick >= 30%, displacement >= 1.20x average range, max 1 OB touch, midpoint confirmation, M5 signal freshness 2 candles.

## Rejection diagnostics
Rejected candidates expose explicit reasons such as:
- `ORDER_BLOCK_NOT_FRESH`
- `CONFIRMATION_MODE_NOT_SATISFIED`
- `REJECTION_NOT_CONFIRMED`
- `DISPLACEMENT_NOT_CONFIRMED`
- `MICRO_STRUCTURE_NOT_CONFIRMED`
- `MOMENTUM_NOT_CONFIRMED`
- `INSUFFICIENT_TRADE_SCORE`

## Validation
Non-MT5 test subset: `42 passed`.
Full suite could not be executed in the build environment because the `MetaTrader5` Python package is not installed there; this does not replace validation in the user's Windows MT5 environment.
