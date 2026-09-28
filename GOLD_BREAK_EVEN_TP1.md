# GOLD: break-even sólo después de TP1

El monitor tenía una excepción de transición a Nueva York que movía el SL al precio de entrada con cualquier RR positivo. Esa excepción no cubría spread y podía actuar antes de TP1. Se retiró; el parámetro antiguo gold_break_even_positive_at_new_york ya no habilita esa conducta.

Las posiciones GOLD gestionadas por el monitor normal mantienen el SL antes de alcanzar TP1. La pierna TP1 no recibe BE. Para RUNNER se usa el objetivo TP1 capturado en la operación o el objetivo de su pierna hermana, nunca sólo el estado WIN. Se admite toque observado con precio ejecutable (Bid para BUY; Ask para SELL), cierre de la hermana en el objetivo o evidencia de toque persistida para sobrevivir reinicios. Un cierre manual con poca ganancia no sirve.

Para SINGLE se guarda un TP1 virtual con el plan de entrada; operaciones antiguas sin ese dato usan al menos 1R del riesgo inicial. No se reduce el requisito por un break_even_trigger_rr antiguo inferior a 1.

Después del toque, el stop cubre spread actual, offset configurado y la protección de beneficio ya configurada. Se redondea al tick a favor de la protección y se respetan stops/freeze del broker. Si no cabe por retroceso/spread, se pospone la modificación y se conserva el evento TP1. No se amplían stops previamente protegidos.

ORB con salidas fijas y GOLD_QUARTERS mantienen sus rutas independientes. No se retiraron las protecciones de emergencia de ejecución. No se reiniciaron workers ni se modificaron posiciones reales durante este cambio. No se restaurará automáticamente un SL que otro proceso ya haya ajustado.

Pruebas: tests/test_gold_break_even_tp1.py y tests/test_daemon_break_even_live.py.
