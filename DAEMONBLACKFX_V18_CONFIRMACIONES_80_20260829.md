# DaemonBlackFx v18 - Umbral mínimo de confirmaciones 80%

## Cambio principal

La estrategia adaptativa ahora exige **al menos 80% de las confirmaciones evaluadas** para considerar viable una entrada.

- `minimum_confirmation_ratio = 0.80` en `LiveTradingConfig`.
- `minimum_confirmation_ratio = 0.80` en `PipelineConfig`.
- `minimum_confirmation_ratio = 0.80` en `M5ConfirmationConfig`.
- Una confirmación adaptativa nueva se registra como `ADAPTIVE_80_CONFIRMED`.
- `STRICT_CONFIRMED` continúa vigente cuando se cumplen todos los requisitos estrictos.

## Condiciones críticas

Alcanzar 80% no permite compensar fallas críticas. Siguen siendo obligatorias las condiciones estructurales/contextuales críticas definidas por la estrategia, incluyendo tendencia H1, setup M15, sweep, estructura M15, Premium/Discount, Order Block fresco, retest, vela direccional y modo de confirmación.

## Confluencias opcionales

Divergencia RSI, patrón armónico y Doji H1 en extremos continúan como confluencias opcionales. Su ausencia no reduce artificialmente el porcentaje adaptativo; pueden aportar calidad/score cuando corresponda.

## Compatibilidad histórica

El dashboard y los reportes mantienen traducción para `ADAPTIVE_75_CONFIRMED` de trades históricos, pero las nuevas entradas usan el umbral 80%.
