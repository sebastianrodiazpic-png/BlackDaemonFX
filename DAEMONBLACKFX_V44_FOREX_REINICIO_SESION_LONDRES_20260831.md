# DaemonBlackFx v44 — Forex reinicia en sesión de Londres

La protección Forex ahora funciona así:

- 16:30 New York: bloquear nuevas entradas.
- 16:45 New York: cerrar posiciones Forex del daemon.
- 17:00 New York: rollover.
- Asia: Forex permanece bloqueado.
- 08:00 Europe/London: vuelve a habilitarse el ciclo Forex.

Se utilizan simultáneamente:
- `America/New_York`
- `Europe/London`

`zoneinfo` resuelve automáticamente DST (EDT/EST y BST/GMT), por lo que no se
usan horas UTC fijas.

Los sintéticos continúan 24/7 y ORB conserva su comportamiento independiente.
El fin de semana permanece bloqueado y el lunes Forex no comienza antes de la
apertura de Londres.
