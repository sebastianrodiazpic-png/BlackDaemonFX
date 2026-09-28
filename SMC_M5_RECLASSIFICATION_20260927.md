# M5 v2: reclasificacion de estructura de entrada

El evaluador unificado utiliza la version actualizada de evaluate_m5_confirmation_detailed; evaluate_m5_details y evaluate_m5_details_v2 exponen aliases score/vetos/tag. La salida conserva diagnostic_tag, m5_score, veto_codes, freshness y effective_has_choch/native_has_choch.

## Puntaje y etiquetas
- CHoCH nativo con sweep: 20 base, NONE.
- BOS con giro posterior al sweep: 15 base, RECLASSIFIED_BOS_TO_CHOCH.
- Ruptura por mecha y FVG asociado: 15 base, VALIDATED_WICK_CHOCH_WITH_FVG.
- Sweep sin ninguna evidencia aceptada: TRUE_MISSING_CHOCH y veto.
- Senal vencida: EXPIRED, veto y 0 puntos M5; timestamp invalido/futuro: INVALID_TIMESTAMP.
- FVG +10 y retest limpio +5 se conservan. Ningun bonus compensa un veto. La edad de una reclasificacion parte de la vela BOS/mecha, nunca del momento en que se evalua.

## Evidencia real del motor
strategy/smc/m5_reclassification.py examina exclusivamente el prefijo hasta confirmation_index y la ventana configurada del setup. Requiere sweep direccional ANTERIOR al evento y movimiento adverso hacia el sweep (cierre inferior al previo para BUY, superior para SELL).

BOS: bandera direccional del detector, nivel structure_break_level finito, cierre mas alla de ese nivel y del extremo opuesto de la vela sweep. No se reclasifica cualquier BOS ni uno anterior al barrido.

Mecha: pivote fractal 2/2 confirmado al momento del sweep, no consumido por cierre antes de la ruptura; la vela cruza con mecha y cierra del lado interior. Ademas debe superar el extremo opuesto del sweep. El detector FVG existente debe validar un gap alineado en la ventana de esa ruptura, conservando antiguedad y reglas de relleno existentes.

Se prefiere CHoCH nativo; sin el, BOS tiene precedencia sobre mecha. Se publica m5_reclassification_evidence con indices, timestamps y nivel. El detector global choch_bos no se modifica: las salidas de posiciones y la estructura base conservan su semantica.

## Telemetria
m5_diagnostic_tags contabiliza NONE, RECLASSIFIED_BOS_TO_CHOCH, VALIDATED_WICK_CHOCH_WITH_FVG, TRUE_MISSING_CHOCH, EXPIRED e INVALID_TIMESTAMP. m5_detail expone la evidencia efectiva y nativa. Se mantienen las causas desagregadas y las politicas de deduplicacion existentes.

## Validacion
142 pruebas de evidencia BUY/SELL, causalidad, ausencia de sweep/FVG, timestamp faltante/caducado, puntuacion y motor real. Las reglas H1, el riesgo y el preflight no cambian. No se reiniciaron workers ni se enviaron ordenes.
