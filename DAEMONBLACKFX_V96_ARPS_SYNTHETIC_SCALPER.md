# DaemonBlackFx v96 — ARPS Synthetic Scalper paralelo

## Identidad persistente

- Estrategia: `ARPS_SYNTHETIC_SCALPER`
- Versión: `arps-synthetic-v1`
- Perfiles: `SCALP_BOOM`, `SCALP_CRASH`, `SCALP_VOLATILITY`, `SCALP_STEP`, `SCALP_JUMP`, `SCALP_FLIP`
- Magic MT5: `26082301` a `26082306`

Los perfiles SMC originales, sus magics y sus reglas no fueron reemplazados.
El comando normal `multi-bot-daemon` inicia ambos conjuntos dentro del mismo
coordinador y continúa usando una sola base persistente y un solo escritor XLSX.

## Reglas de entrada ARPS

1. M15: EMA50/EMA200, pendiente de EMA50 y ADX mínimo 20.
2. M5: ATR entre percentiles 30–85, BOS y retroceso a EMA20/EMA50 o nivel roto.
3. M1: rechazo direccional y cuerpo mínimo del 45% del rango de la vela.
4. Spread: máximo 12% del ATR M5 cuando el tick está disponible.
5. Boom sólo BUY; Crash sólo SELL; Flip y las demás familias permiten ambos lados.

## Riesgo y gestión

- Riesgo total por setup: 0,25%.
- Dos piernas: TP1 0,8R y runner 1,5R.
- Break-even del runner: 0,60R con el offset protector existente.
- Time stop: después de 5 minutos se cierra si el MFE no alcanzó 0,25R.
- Las extensiones TP3/TP4 y la invalidación defensiva SMC no se aplican a ARPS.
- Los límites globales y por símbolo ya existentes siguen vigentes; por ello SMC
  y ARPS no pueden duplicar exposición en un símbolo que ya ocupa sus dos slots.

## Persistencia y reportes

Cada trade conserva en metadata `strategy_name`, `strategy_version`,
`bot_profile` y `daemon_magic`. El Excel consolidado expone además:

- `estrategia_id`
- `version_estrategia`
- `perfil_bot`
- `magic_estrategia`

El Excel de auditoría visual también incluye la estrategia y versión en Resumen
y Timeline Completo.

## Ejecución

Se mantiene el mismo comando:

```powershell
python -m app.main --mode multi-bot-daemon --execute --interval 30 --position-monitor-interval 2 --risk-percent 1.0 --min-rr 1.5 --dashboard --dashboard-port 8765
```

`--risk-percent 1.0` continúa correspondiendo a SMC/Forex/Gold/ORB. ARPS usa su
riesgo interno independiente de 0,25%.
