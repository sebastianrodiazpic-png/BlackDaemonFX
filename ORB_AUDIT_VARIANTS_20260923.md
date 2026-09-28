# ORB: diagnóstico y sensibilidad en sombra — 23/09/2026

## Cambios

El resumen persistido de cada evaluación conserva orb_audit: proveedor, zona horaria, inicio/fin del rango, ORH/ORL, buffer, tolerancia de retesteo y las velas OHLC cerradas que formaron el rango. Permite contrastar el mismo día y las mismas velas con TradingView; no certifica por sí mismo que ambas plataformas utilicen datos idénticos.

Momentum registra dirección, hora de vela, cuerpo/rango, ATR previo, extensión/ATR, límites, volumen y media, fuente y disponibilidad. Un volumen cero o media inexistente se identifica UNAVAILABLE_OR_ZERO, separado de la participación insuficiente con datos positivos disponibles. No se reemplaza volumen ausente por un valor inventado ni por volumen de otro proveedor sin validación.

Cuando la vela actual rompe pero momentum falla, el motivo operativo es ORB_MOMENTUM_REJECTED con la lista de fallos; deja de describir ese caso como ausencia de ruptura. La acción WAITING_M5_BREAKOUT_RETEST permanece para compatibilidad y seguimiento del retesteo posterior.

Comparaciones en sombra: máximos 0,50 / 0,75 / 1,00 / 1,50 / 2,00 ATR, con volumen obligatorio y con excepción solamente cuando el dato está ausente/cero. Se mantienen cuerpo mínimo y desplazamiento mínimo. Una variante no puede establecer direction ni autorizar órdenes. momentum_checks_pass no significa que RR, coste, VWAP/POC, riesgo o correlación hayan sido aprobados.

El dashboard muestra un bloque ORB con rango, horas, proveedor, métricas y rechazos. Conserva candidatos únicos por símbolo, dirección y vela; la primera captura no se sobrescribe. Persistencia diaria: storage/runtime/orb_audit/YYYY-MM-DD.json. Los eventos originales también incluyen la evidencia compacta.

## Comparación de las velas históricas ya descargadas

Se repitieron los tres casos con los mismos OHLC guardados, sin conexión al broker ni órdenes:

- SP500: ninguna variante cumple momentum; extensión aproximada 2,62 ATR.
- US Tech 100: ninguna cumple; además de extensión/volumen, el cuerpo aproximado del 54% no supera 65%.
- Wall Street 30: las variantes 1,50 y 2,00 ATR con excepción de volumen ausente cumplen los controles de momentum. Esto no confirma una operación ejecutable ni su resultado.

Evidencia: storage/analysis/ORB_VARIANTES_20260923.json. Es reconstrucción histórica, no una captura original ni un backtest de rentabilidad.

## Validación y activación

45 pruebas aprobadas: diagnóstico, persistencia compacta, candidatos únicos, invariancia de la primera captura, excepción de volumen sin eliminar cuerpo mínimo, entradas existentes y salidas fijas ORB. Sintaxis JavaScript validada con Node.

Requiere reiniciar ORB y dashboard. No se reiniciaron procesos ni se enviaron órdenes. El modo real mantiene el límite de extensión 0,50 ATR, volumen confirmado y los SL/TP existentes. No se activa flexibilidad automáticamente por observar después un movimiento favorable.
