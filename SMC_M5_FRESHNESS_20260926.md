# Antiguedad y desglose M5

validate_m5_signal_freshness y evaluate_m5_confirmation_detailed viven en strategy/smc/m5_freshness.py. El score adaptativo usa el desglose, y confirmation_engine obtiene el timestamp del ultimo CHoCH detectado dentro de la ventana del setup. No se inventa un CHoCH con la penultima vela.

## Tiempo
Maximo 10 minutos, inclusivo; 10 minutos y 1 segundo ya rechaza. Se compara el valor exacto antes de redondear. Se mide desde la apertura de la vela CHoCH, coherente con time del proveedor; no es una medicion de duracion de CPU/red. Timestamps sin zona se interpretan como UTC; offsets explicitos se convierten. Datos invalidos, faltantes cuando se declara CHoCH, o tiempos futuros rechazan.

El coordinador vivo inyecta una hora UTC actual por evaluacion del pipeline. Uso historico del confirmation_engine sin reloj explicito usa el cierre de la vela candidata (time+5 minutos), evitando comparar enero con el reloj real de septiembre. El helper de freshness usado directamente sin reloj utiliza UTC actual. Una llamada directa antigua al scorer sin timestamp conserva compatibilidad; la ruta activa siempre exige freshness.

## Desglose
M5_SIGNAL_EXPIRED: rechazo temprano, score M5=0, sin bonus FVG/retest.
M5_CHOCH_MISSING: falta CHoCH.
M5_SWEEP_MISSING: falta sweep.
M5_CHOCH_AND_SWEEP_MISSING: faltan ambos.
M5_CHOCH_TIMESTAMP_INVALID / M5_CHOCH_TIME_IN_FUTURE: problemas de timestamp.

Segun el codigo solicitado, si falta evidencia estructural pero no hay caducidad, FVG/retest pueden sumar 10/5 puntos al diagnostico, pero el veto impide aprobar. Se conserva la escala maxima y los umbrales 85/70.

## Telemetria
adaptive_score.m5_detail y m5_detailed_confirmation publican m5_score, veto_codes, veto_reasons, latency_rejected y freshness (timestamps, edad, limite). El JSON por worker incorpora m5_rejection_codes, con contadores estables independientes del texto variable de minutos. La identidad de deduplicacion añade veto_codes: una transicion aprobado→caducado se registra aunque sea la misma vela; revisiones sucesivas del mismo estado no se suman.

El embudo sigue reflejando el resultado terminal del analizador. Los guards posteriores de preflight, vigencia y riesgo no se eliminan. Esta revision no cambia parametros de riesgo, no reinicia procesos y no envia ordenes.
