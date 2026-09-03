# DaemonBlackFx v43 — Protección de rollover Forex

## Objetivo
Evitar mantener o abrir posiciones Forex durante la franja en la que el spread
puede ampliarse alrededor del rollover diario de las 17:00 de Nueva York.

## Reglas por defecto
Zona horaria: `America/New_York` con DST automático.

- 16:30 NY: se bloquean nuevas entradas Forex.
- 16:45 NY: se cierran las posiciones Forex abiertas del daemon.
- 17:00 NY: rollover.
- 17:15 NY: termina la ventana técnica de protección.

Los viernes también se fuerza el cierre antes del fin de semana.

## Alcance
El guard sólo reconoce pares de divisas Forex.

No afecta:
- índices sintéticos (24/7);
- Boom/Crash/Jump/Volatility/Step;
- XAUUSD;
- US500/Wall Street/US Tech;
- ORB New York.

## Motivo
Spot FX funciona 24/5, pero el rollover diario puede tener menor liquidez y
spreads sensiblemente mayores. La estrategia Forex de DaemonBlackFx se plantea
como intradía, por lo que no se busca capturar exposición durante ese periodo.

## Configuración
En `LiveTradingConfig`:
- `forex_rollover_guard_enabled`
- `forex_new_entry_cutoff_hour/minute`
- `forex_force_flat_hour/minute`
- `forex_rollover_end_hour/minute`
- `forex_force_flat_daily`
- `forex_force_flat_friday`

El cierre se realiza a través del mismo `TradeExecutor` del daemon y queda
registrado en `details_json.metadata` como `forex_rollover_exit`.
