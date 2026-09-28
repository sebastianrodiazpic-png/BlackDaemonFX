# ORB: retesteo y momentum

El worker mantiene ORB_BREAKOUT_RETEST y habilita ORB_BREAKOUT_MOMENTUM
como alternativa sobre la última vela M5 cerrada que cruza el borde.
Para volver a solo retesteo: LiveTradingConfig.orb_momentum_enabled=False
(o ORBConfig.momentum_enabled=False al usar directamente la estrategia).

Momentum exige cuerpo direccional >=65%, cierre a >=0.15 ATR y <=0.50 ATR
del borde, y volumen superior a la media de hasta 20 velas anteriores.
El ATR M5 usa hasta 14 velas anteriores, excluyendo la candidata.
La estrategia construye la candidata; el motor exige H4 y H1 conocidos
y alineados con su dirección, incluso si el filtro HTF opcional está desactivado.
Antes de ejecutar vuelve a comprobar el límite 0.50 ATR usando ask para BUY
y bid para SELL. Conserva los filtros de RR ejecutable, spread, frescura,
exposición y riesgo existentes.

El retesteo acepta distancia max(2*spread, 0.10*ATR_M5), mantiene cierre
fuera del borde con buffer y rechaza mechas que alcanzan el midpoint.
La ventana de retesteo continúa siendo de tres velas posteriores distintas.
Los modos aparecen en orb_entry_mode; los rechazos técnicos de momentum
aparecen en momentum_rejection_reasons. Momentum no registra un retesteo ficticio.

La sesión sigue siendo 09:30–09:45 America/New_York y utiliza velas cerradas.
No se modificaron las órdenes ni se reinició el daemon durante esta actualización.
El proceso debe cargar nuevamente el código para aplicar el cambio.
Las capturas no prueban que estos filtros habrían permitido una ejecución;
la comparación histórica requiere las velas y cotizaciones del proveedor.
