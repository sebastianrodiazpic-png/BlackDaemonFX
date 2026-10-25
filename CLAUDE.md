# BlackDaemonFX — instrucciones para agentes

- **Antes de cualquier cambio** lee `REGISTRO_CAMBIOS_ESTRATEGIA.md` (reglas del proyecto, estado actual, historial y pendientes).
- **Después de cada cambio** de estrategia, ejecución, riesgo, filtros, universos o dashboard, añade una entrada nueva arriba
  del "Historial de cambios" de ese fichero (plantilla incluida) y actualiza "Estado actual", "Variables de entorno" y "Pendientes".
- Responde al usuario en español.
- Rentabilidad primero: no relajes filtros ni actives activos sin evidencia de replay fiel (clase real, solo velas cerradas,
  positivo en ambas mitades/años). Lo no concluyente va a prueba demo con criterio fijado.
- Cada cambio debe ser configurable (variable de entorno o campo de config) y llevar tests.
- No reinicies los daemons ni hagas commit sin que el usuario lo pida. La base viva está en
  `C:/Users/sebas/AppData/Local/BlackDaemonFx/trading_bot.sqlite3` (ábrela en solo lectura para analizar).
- Python del proyecto: `.venv/Scripts/python.exe`. Tests: `.venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider`.
