# Puntuacion adaptativa SMC 25/30/35/10

Esta revision sustituye los requisitos de FVG y retest limpio de las revisiones estructural y flexible anteriores para la ruta H1_LOCATION_ONLY del coordinador multi-temporal. No reinicia procesos ni envia ordenes.

## Tabla
- H1: pivotes 25; fallback de 24 velas 15. Ubicacion invalida veto. Fuente desconocida veto adicional de integridad de datos.
- M15: BOS 30; SWEEP 20; solo desplazamiento 10. OB invalidado por cierre M15 posterior veto. Sin ruptura ni desplazamiento veto.
- M5: CHoCH real del mismo setup y barrido de liquidez obligatorios, 20 puntos; FVG desacoplado +10; retest limpio +5.
- Confluencias: volumen confirmado +5; agotamiento o divergencia detectada +5 (no se suman dos veces).
- Sin vetos: >=85 STRICT_APPROVED; >=70 ADAPTIVE_APPROVED; <70 REJECTED_LOW_SCORE.

La puntuacion maxima es 100, sin bonuses chartistas/armonicos extra ni penalizacion chartista. El porcentaje de confirmaciones queda como diagnostico, no umbral adicional. fvg_missing_but_allowed informa una aprobacion sin FVG, incluso STRICT si alcanza 85. El desglose se publica en adaptive_score junto al trade_score principal.

## Integracion
El constructor M15 acepta ruptura O desplazamiento en esta ruta y conserva limites de OB, caducidad, ubicacion macro y el proceso existente de formacion del bloque. Conserva causalidad: solo considera ruptura disponible en el prefijo cerrado. M5 recibe fuente y limites reales H1, evidencia M15, CHoCH y sweep calculados en velas cerradas hasta la confirmacion. La fuente H1 se distingue entre PIVOT y FALLBACK_24H.

El retest sigue siendo necesario para generar candidatos; su calidad clean_retest pasa a bonus. Las comprobaciones geometricas iniciales de candidato y los controles posteriores de riesgo, spread, obstaculos y ejecucion permanecen. Los controles especiales de instrumento (por ejemplo calidad Jump) pueden bloquear una señal ya aprobada por este score. No se ha modificado su politica.

El esquema anterior permanece disponible cuando adaptive_smc_score_enabled=False; el coordinador activa True para los setups M15 y su confirmacion M5. Se sustituye la decision y sus rechazos en esta ruta; no se exige simultaneamente el antiguo porcentaje adaptativo o FVG obligatorio.

## Validacion
Pruebas de fronteras 65/70/85/100, fallback y pivotes, BOS/SWEEP/desplazamiento, vetos independientes, aprobacion sin FVG y sin retest limpio, integracion del motor y regresiones de ubicacion y riesgo. No constituye backtest de rentabilidad.
