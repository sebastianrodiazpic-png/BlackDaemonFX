# DaemonBlackFx v97 — ARPS confirmación y salida escalonada

La estrategia conserva el identificador `ARPS_SYNTHETIC_SCALPER`, pero las
operaciones nuevas quedan diferenciadas con la versión
`arps-synthetic-v2-confirmed-follow-through`.

## Entrada M1 reforzada

- La primera vela debe cumplir el rechazo direccional.
- La siguiente vela M1 cerrada debe ser direccional, superar el cierre de la
  vela de rechazo y tener un cuerpo mínimo del 45% de su rango.
- La entrada se calcula al cierre de esta segunda vela.

## Salida defensiva escalonada

1. Desde 2 minutos: cierra si MFE < 0,05R, la posición está bajo 0R y una
   condición M1 permanece inválida durante dos reevaluaciones distintas.
2. Desde 3 minutos: cierra si MFE < 0,10R.
3. Desde 5 minutos: cierra si MFE < 0,25R.

Cada salida guarda `ARPS_DEFENSIVE_EXIT`, etapa, MFE, R actual, racha de
invalidación y resultado del broker en la auditoría persistente.
