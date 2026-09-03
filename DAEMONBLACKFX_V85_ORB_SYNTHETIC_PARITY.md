# DaemonBlackFx v85 — ORB correlacionado y paridad sintética

## ORB

- Se retiró el techo global compartido de 1% para todos los instrumentos ORB.
- Cada oportunidad conserva su riesgo lógico configurado (por defecto 1%, dividido 0.5% TP1 y 0.5% RUNNER).
- US S&P 500 y US Tech 100/Nasdaq 100 forman un grupo correlacionado.
- Si uno tiene una operación ORB abierta, el otro queda bloqueado hasta que todas las piernas aún abiertas de la primera operación tengan Break Even confirmado.
- La confirmación usa `break_even_confirmed` y, como respaldo verificable, un SL persistido en entrada o en beneficio.
- Oro y Wall Street 30 no quedan afectados por este guard específico.

## Sintéticos

- BOOM, CRASH, VOLATILITY, STEP, JUMP, FLIP y el perfil legacy SYNTHETICS usan el mismo plan progresivo SMC de Forex: TP1 a 1R, RUNNER lógico inicial a 2R, evaluación 2R→3R y 3R→4R con locks protectores.
- Conservan análisis continuo: no heredan el scheduler por vela M5 de Forex.
- No heredan bloqueo de rollover, cierre de sesión ni exposición agregada por divisas.
- Se conservan políticas propias del instrumento, incluido el filtro reforzado de Jump y las direcciones autorizadas por familia.
