# DaemonBlackFx v95 — salida defensiva por análisis actual inválido

## Evidencia que motivó el cambio

El trade 4 de Volatility 50 Index conservó durante 865 snapshots la decisión
histórica `ADAPTIVE_80_CONFIRMED`, aunque la reevaluación estaba marcada
`STALE_M5_SIGNAL`, `valid=false` y `M5_CONFIRMATION_TOO_OLD_FOR_LIVE_ENTRY`.

## Regla implementada

- La tesis de entrada continúa siendo evidencia inmutable.
- La gestión activa usa exclusivamente `current_strategy_view`.
- Sólo se cuentan evaluaciones distintas mediante `evaluated_at`; el monitor de
  dos segundos no puede inflar confirmaciones repitiendo el mismo análisis.
- Tras 10 minutos y dos reevaluaciones inválidas consecutivas:
  - se cierra si la pérdida llega a `-0.35R`;
  - si previamente alcanzó al menos `+0.20R`, se cierra al retroceder a `-0.10R`.
- El cierre, RR, MFE, estado actual y resultado del broker quedan persistidos en
  metadata y en el evento append-only `ANALYSIS_INVALIDATION_EXIT`.
- Nunca se abre una entrada desde `STALE_M5_SIGNAL`: una nueva operación exige
  una confirmación M5 nueva y `valid=true`.
- El Excel ahora expone en columnas separadas el estado actual, `valid` y el
  motivo de la reevaluación, sin obligar a inspeccionar el JSON completo.

Los umbrales son configurables en `LiveTradingConfig`.
