# DaemonBlackFx v110 — riesgo ORB y búsqueda de señales

## Riesgo ORB

La prueba contractual de v61 fue reproducida sobre este paquete y pasa: una
señal `ORB_NEW_YORK` toma `orb_risk_percent` (1% lógico), no el porcentaje SMC
general. Se añadió una prueba independiente que mantiene esa separación aunque
`risk_percent` tenga otro valor.

## Optimización del scheduler

Antes, cada worker sondeaba tres velas de cada instrumento cada 10 segundos,
aunque una señal SMC sólo puede cambiar al cerrar la siguiente M5. Ahora, tras
comprobar correctamente todos sus símbolos, el worker espera hasta la próxima
frontera M5 más dos segundos de gracia. Esto reduce hasta seis sondeos por
instrumento y vela a uno, sin saltarse velas cerradas.

Si un símbolo no entrega datos o genera error, la espera optimizada no se arma:
el worker reintenta en el ciclo siguiente.

## Caché single-flight

El scanner y el monitor pueden pedir simultáneamente H1/M15/M5 para un mismo
instrumento justo al vencer la caché. v110 usa un candado independiente por
`(símbolo, timeframe)`: una hebra calcula y la otra reutiliza el resultado. Los
demás símbolos no se bloquean entre sí.

No se cambiaron confirmaciones, score, estructura H1/M15/M5, frescura M5,
horarios, riesgo real ni monitor de posiciones.
