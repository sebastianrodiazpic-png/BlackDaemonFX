# Separación de responsabilidades SMC

Implementación para el analizador con H1 LOCATION_ONLY (Forex, GOLD SMC y sintéticos).

- H1 conserva la dirección permitida por ubicación premium/discount.
- M15 identifica una vela contraria al impulso y un cierre posterior fuera de su rango. El impulso debe cumplir el cuerpo mínimo y el multiplicador de rango configurados, calculados con velas anteriores. No exige además tendencia local ni BOS/CHoCH M15.
- La zona del bloque debe ser discount para compra o premium para venta. Se descartan límites inválidos, bloques invalidados por cierre posterior y bloques caducados. El setup está disponible solo al cierre de la vela M15 del impulso.
- M5 recibe ese setup M15 directamente. Conserva confirmación favorable, retesteo, frescura, desplazamiento y los restantes controles existentes. La estructura se comprueba con BOS/CHoCH M5. El barrido de liquidez continúa obligatorio, comprobado entre disponibilidad del setup y confirmación M5. Los nombres históricos h1_trend y m15_structure del checklist representan, en esta ruta, ubicación H1 y estructura M5 respectivamente.
- No se modifican las fórmulas de objetivos ni las reglas de cierre de operaciones.

## Auditoría

SYMBOL_PROCESS_RESULT conserva m15_block_audit con origen, disponibilidad, dirección, límites, zona, aceptación y motivos. Los motivos incluyen M15_OB_DISPLACEMENT_REQUIRED, M15_OB_INVALID_BOUNDS, M15_OB_LOCATION_MISMATCH, M15_OB_INVALIDATED_BY_CLOSE, M15_OB_EXPIRED y M15_DIRECTION_DIFFERS_FROM_H1_LOCATION.

El estado smc_trial conserva también estos campos. Un candidato M5 histórico rechazado queda en historical_m5_rejection y ya no sustituye la dirección ni el score del análisis actual.

## Alcance y activación

ORB y GOLD_QUARTERS no usan esta nueva ruta de setups. No se han reiniciado workers ni enviado órdenes. Reiniciar los procesos SMC para cargar el código. Esta corrección no demuestra por sí sola que Step 200 o Step 500 hubieran superado todos los controles en sus movimientos anteriores.
