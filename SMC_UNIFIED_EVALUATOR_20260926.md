# Evaluador unificado H1 / M15 / M5

Punto de entrada: strategy.smc.candidate_evaluator.evaluate_candidate_signal(signal_type, current_price, h1_raw, m15_raw, m5_raw, confluences=None, current_time=None, max_age_minutes=10).

confirmation_engine llama este evaluador con la evidencia real del setup, el precio de la vela candidata, limites/regimen H1 capturados, calidad M15, CHoCH detectado y su timestamp, sweep, FVG y retest. No se inventan detectores ni timestamps. MultiTimeframeAnalyzer inyecta hora UTC real; las llamadas historicas del confirmation_engine usan el cierre de la vela candidata. El evaluador directo sin reloj usa hora real.

H1 distingue RANGE_DISCOUNT, RANGE_PREMIUM, EXPANSION_BUY y EXPANSION_SELL. Equilibrio, datos invalidos y direccion contraria rechazan. El contexto de expansion capturado admite el retest de 0.2% conforme al modulo previo. El control de ubicacion previo al envio usa los mismos limites y contexto.

M5 separa CHoCH ausente, sweep ausente, ambos ausentes y caducidad. Mas de 10 minutos desde apertura de la vela CHoCH da cero puntos M5 y veto. Timestamp invalido/futuro tambien rechaza. Se conservan detalles y codigos estables en m5_detail.

## Adaptaciones frente al adjunto
Se conserva la escala existente 25/30/35/10 y fuentes H1 PIVOT=25, FALLBACK_24H=15; no se convierten todos los rangos a 25. Se conservan confluencias opcionales y estados STRICT_APPROVED >=85 / ADAPTIVE_APPROVED >=70, en lugar del APPROVED generico del adjunto. Los vetos mantienen REJECTED en el resultado compatible y se normalizan a REJECTED_CRITICAL_VETO en telemetria. Con un veto, ningun bonus permite aprobar. Los puntos parciales M5 permanecen informativos cuando falta CHoCH/sweep; en caducidad M5 vale cero.

## Reportes
adaptive_score contiene h1_context, m15_evidence, m5_detail, score_breakdown, veto_codes, reasons y evaluator_version. La telemetria recibe exactamente ese resultado; suma h1_context_counts y m5_rejection_codes, y conserva contexto/edad en last_evaluation. El embudo del analizador sigue separado de los candidatos puntuados. Una aprobacion de estrategia no es una orden ejecutada.

## Validacion
134 pruebas aprobadas en el conjunto de integracion, contexto, timestamps, puntuacion, telemetria, antiguedad y preflight. git diff --check sin errores. No se reiniciaron workers ni se enviaron ordenes. El codigo sera cargado cuando se reinicien los procesos existentes.
