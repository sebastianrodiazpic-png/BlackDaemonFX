# DaemonBlackFx v45 — Forex visible y seleccionable

## Objetivo
Forex ya forma parte del universo operativo visible del daemon.

## Cambios
- Nueva categoría `forex` en el catálogo de instrumentos.
- Descubrimiento dinámico desde el MT5 conectado.
- Se utilizan `currency_base` y `currency_profit` del símbolo cuando están disponibles.
- Fallback por nombre para sufijos de broker como `EURUSDm`, `GBPUSD.a` o `USDJPYm`.
- Sólo se muestran símbolos habilitados para trading.
- Forex aparece como grupo `Forex` en `/instruments`.
- La selección utiliza el mismo mecanismo persistente de SQLAlchemy/dashboard ya existente.
- Al estar seleccionado, el par entra al pipeline SMC H1 -> M15 -> M5.

## Restricciones preservadas
Que un par aparezca seleccionado NO evita las protecciones Forex:
- Desde 16:30 New York: no nuevas entradas.
- Desde 16:45 New York: cierre de posiciones Forex del daemon.
- Asia: Forex permanece bloqueado.
- 08:00 Europe/London: reinicia el ciclo Forex.
- Fin de semana bloqueado.

## Estrategias independientes
- Sintéticos: continúan con su comportamiento 24/7.
- ORB New York: conserva su router y sesión.
- Forex: SMC con guard horario Londres/rollover.
