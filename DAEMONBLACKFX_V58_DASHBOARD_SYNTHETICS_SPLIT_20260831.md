# DaemonBlackFx v58 — Dashboard central synthetics-split

## Diagnóstico
`run_synthetics_split.bat` iniciaba:
`--mode synthetics-split-daemon`
pero no incluía `--dashboard`.

Además, `run_multi_bot_daemon()` sólo creaba el dashboard central cuando
`args.dashboard == True`. Por eso los seis workers podían estar operando y
persistiendo telemetría mientras el dashboard no quedaba disponible.

## Corrección
- `synthetics-split-daemon` y `multi-bot-daemon` mantienen siempre un único
  `RealtimeDashboardService` central.
- Los workers BOOM/CRASH/VOLATILITY/STEP/JUMP/FLIP siguen usando
  `--coordinated-worker`, por lo que no abren dashboards individuales.
- `run_synthetics_split.bat` incluye explícitamente:
  `--dashboard --dashboard-port 8765`.
- Se conserva la persistencia independiente v57 para SYNTHETICS/FOREX/ORB.
- No se modifica lógica SMC, riesgo, BE, runner, ORB ni Forex.
