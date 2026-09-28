# Control de ubicación para todas las entradas SMC

Ampliación del filtro de Volatility a GOLD, Forex y todos los sintéticos.
LiveTradingConfig.smc_entry_location_enabled=True se transmite al analizador.

Reglas adicionales, acumulativas con las confirmaciones ya establecidas:
- BUY: precio en discount en H4, M15 y M5.
- SELL: precio en premium en H4, M15 y M5.
- Cada rango usa las últimas 100 velas cerradas, según premium_discount_lookback.
- Equilibrio, precio fuera del rango o historial insuficiente bloquean.
- Se valida el cierre M5 actual y, antes de ejecutar, ask para BUY / bid para SELL.
- Se conservan la convergencia H4/H1, liquidez, CHOCH/BOS, order block,
  retesteo, confirmación M5, frescura, puntuación y controles de ejecución.
- Patrones chartistas, divergencias y otras confluencias mantienen sus requisitos
  y bonus existentes: no se exige que todas aparezcan simultáneamente.
- Boom continúa solo BUY; Crash continúa solo SELL.
- ORB y NY_INDEX_OPEN mantienen sus reglas propias.

El bloqueo se identifica como ENTRY_LOCATION_BLOCKED y conserva la evidencia
por temporalidad en los diagnósticos y metadatos ya implementados.
Los rangos pueden diferir de los del indicador TradingView.

Compatibilidad: volatility_entry_location_enabled conserva el control anterior
si se desactiva el interruptor general. El analizador aislado mantiene el
interruptor general desactivado por defecto para consumidores H1/M15/M5;
el motor live lo activa con su configuración, que también exige H4/H1.

Validación: 79 pruebas de ubicación, confirmación, dirección Boom/Crash,
secuencia multitemporal y regresión ORB aprobadas.
El daemon no se reinició durante esta ampliación: debe recargar el código.
