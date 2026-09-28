# DaemonBlackFx v113.2

## Corrección Deriv Charts

- `active_symbols` usa el contrato estricto del endpoint público de Deriv.
- Se eliminó el campo legado `product_type`, rechazado por la API con
  `Properties not allowed: product_type`.
- No requiere token, `app_id` ni cuenta OANDA para consultar símbolos y velas.
- MT5 se mantiene exclusivamente para metadatos, validación pre-fill y ejecución.

## Control de workers

- Un worker que finaliza con código 2 queda como `BLOCKED_PREFLIGHT`.
- El coordinador no lo reinicia cada cinco segundos.
- Tras corregir la causa puede reactivarse desde el dashboard o reiniciando el
  coordinador.

## Verificación segura

Con MT5 conectado a la cuenta DEMO:

```cmd
python -m app.main --mode market-data-preflight --market-data-mode external --symbol "Boom 99 Index"
```

Sólo inicie el daemon con `--execute` cuando el resumen muestre `ERROR=0`.

