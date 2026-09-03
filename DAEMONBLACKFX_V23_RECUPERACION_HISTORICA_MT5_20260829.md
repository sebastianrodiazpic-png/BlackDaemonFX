# DaemonBlackFx v23 — Recuperación histórica MT5 para Cuenta activa

## Problema corregido

La v22 conservaba de forma permanente los trades que ya habían sido vistos por SQLite/SQLAlchemy, pero no podía reconstruir por sí sola operaciones antiguas que sólo existían en el historial de MetaTrader 5. Por eso Cuenta activa podía mostrar únicamente una parte del pasado de la cuenta.

## Nueva sincronización histórica

Al iniciar el modo `demo-daemon` con MT5 conectado, DaemonBlackFx ahora consulta `history_deals_get` desde el año 2000 hasta el momento actual (sujeto al historial realmente disponible en el servidor/terminal MT5), agrupa los deals por `position_id` y reconstruye cada posición cerrada.

Para cada trade recuperado se conserva, cuando MT5 lo ofrece:

- position ticket y deal tickets;
- instrumento y dirección;
- hora y precio medio de entrada;
- hora y precio medio de salida;
- volumen;
- profit, comisión, swap y fee consolidados en PnL neto;
- motivo de cierre MT5 (TP, SL, etc.);
- comentario/magic de la operación;
- pierna TP1/RUNNER/SINGLE cuando puede inferirse del comentario.

Los registros se escriben directamente en `trade_journal`, por lo que no dependen de que el trade siga existiendo en la tabla operativa `trades`.

## Identificación de trades del daemon

Se considera una operación de DaemonBlackFx cuando cumple al menos uno de estos criterios:

- magic actual `26082026`;
- comentario histórico que contenga `SMC-`;
- comentario que contenga `DBFX` o `DAEMONBLACKFX`.

Esto permite recuperar operaciones de versiones anteriores aunque hubieran usado otro magic.

## Idempotencia

La clave histórica se basa principalmente en `broker_position_ticket`. Reiniciar el daemon o volver a ejecutar la sincronización no crea copias del mismo trade: el registro ya existente se actualiza.

## Posiciones todavía abiertas

Las posiciones abiertas no se importan como trades históricos cerrados. Siguen usando la reconciliación MT5 -> SQLAlchemy de v21, evitando que un cierre parcial sea interpretado erróneamente como cierre total.

## Cuenta activa

`/account` continúa leyendo `trade_journal`, pero ahora el journal puede reconstruirse también desde el historial real de MT5. Los TP históricos cuyo tipo de pierna no puede inferirse se muestran como `TAKE PROFIT` / `TP histórico` en vez de clasificarlos artificialmente como TP1 o TP2.

## Mensaje esperado al iniciar

Cuando se recuperen operaciones antiguas, la consola mostrará un mensaje similar a:

```text
Historial MT5/Cuenta activa: 17 trade(s) histórico(s) recuperado(s), 3 registro(s) actualizado(s) desde 42 deal(s) disponibles en MT5.
```

## Limitación real

DaemonBlackFx sólo puede recuperar aquello que el broker/servidor MT5 expone mediante el historial de la cuenta actualmente conectada. Si un trade pertenece a otra cuenta, fue eliminado del historial por el broker o no posee magic/comentario que permita atribuirlo al proyecto, no puede reconstruirse con certeza automáticamente.

## Validación

Suite disponible sin dependencias nativas de MetaTrader5: **195 tests aprobados**.
