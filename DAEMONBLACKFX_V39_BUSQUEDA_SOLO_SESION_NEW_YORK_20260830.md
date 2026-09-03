# DaemonBlackFx v39 — Búsqueda de trades sólo durante New York

## Regla global
El motor de NUEVAS entradas sólo analiza oportunidades durante:

- Zona horaria: `America/New_York`
- Inicio: `09:30`
- Fin: `16:00` (16:00 ya está fuera)
- Días: lunes a viernes

La zona horaria IANA ajusta automáticamente horario de verano/invierno.

## Fuera de sesión
Antes de 09:30, después de 16:00 y fines de semana:
- no se ejecuta análisis SMC H1/M15/M5;
- no se ejecuta análisis ORB;
- no se calcula selector XAUUSD vs XAUUSDmicro;
- no se calcula sizing de nuevas señales;
- no se buscan nuevas entradas.

Estado:
`OUTSIDE_NEW_YORK_SESSION`

Motivo:
`NEW_ENTRY_SEARCH_ONLY_DURING_NEW_YORK_SESSION`

## Lo que sigue activo 24/7 mientras el daemon está ejecutándose
El filtro aplica únicamente a la búsqueda de nuevas operaciones. Continúan:
- sincronización de posiciones/cierres con MT5;
- Break Even;
- protección de riesgo;
- SL/TP existentes;
- persistencia SQLAlchemy;
- actualización del estado de posiciones abiertas.

Esto evita abandonar una posición por haber terminado la sesión.

## ORB
ORB conserva su lógica:
- 09:30–09:45: construcción del Opening Range;
- desde 09:45: búsqueda de ruptura;
- hasta antes de 16:00.

El filtro global garantiza que ni ORB ni SMC busquen operaciones fuera de la sesión New York.
