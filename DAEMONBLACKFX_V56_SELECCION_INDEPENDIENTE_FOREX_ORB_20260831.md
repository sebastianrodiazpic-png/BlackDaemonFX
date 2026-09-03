# DaemonBlackFx v56 — Selección independiente FOREX / ORB

## Objetivo
Separar de forma persistente los instrumentos habilitados para SYNTHETICS, FOREX y ORB.

## Persistencia
Nueva tabla SQLAlchemy: `instrument_selection_profile_preferences`.
Cada fila identifica `source`, `selection_profile`, símbolos, versión y fecha.
Perfiles soportados: `SYNTHETICS`, `FOREX`, `ORB`.

La tabla legacy `instrument_selection_preferences` se conserva para compatibilidad con v55. Sólo SYNTHETICS puede heredar esa preferencia durante la transición; FOREX y ORB no comparten la selección legacy.

## Comportamiento
- FOREX: si nunca se guardó una preferencia, habilita todo el universo Forex tradeable descubierto en MT5.
- ORB: si nunca se guardó una preferencia, habilita únicamente su universo ORB descubierto/autorizado por la estrategia.
- Guardar FOREX no modifica ORB.
- Guardar ORB no modifica FOREX.
- BOOM/CRASH/VOLATILITY/STEP/JUMP/FLIP continúan usando el perfil SYNTHETICS.
- Los workers releen su perfil persistente en cada ciclo, por lo que el cambio se aplica sin reiniciar el proceso.
- Una selección vacía de un perfil es válida y significa que ese bot no abrirá nuevas entradas; no afecta la gestión de posiciones ya abiertas.

## Dashboard
`/instruments` incorpora pestañas independientes:
- SINTÉTICOS
- FOREX
- ORB NEW YORK

La API `/api/instruments/selection` acepta `selection_profile` y sólo modifica el perfil solicitado.

## Compatibilidad
Las llamadas antiguas sin `selection_profile` conservan el comportamiento global v55 para no romper tests ni integraciones existentes.

## Validación
Pruebas específicas v56 y regresión de v45/v47/v51/v52/v53/v54/v55/dashboard: 65 pruebas aprobadas.
La suite completa no se ejecuta en este entorno porque MetaTrader5 no está instalado; el intento con stub se detuvo durante colección por constantes MT5 no simuladas. Esto es una limitación del entorno Linux de validación, no un fallo de las pruebas v56.
