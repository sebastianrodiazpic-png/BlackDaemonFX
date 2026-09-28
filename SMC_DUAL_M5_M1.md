# Gatillo dual M5/M1

Implementado en el flujo SMC adaptativo H1/M15. No se han reiniciado workers ni enviado órdenes durante la implementación.

## Secuencia

1. H1 mantiene ubicación discount/premium y expansión direccional.
2. M15 mantiene el OB y su validación/invalidation.
3. Se exige sweep direccional M5. Prioridad: CHoCH M5 (20 puntos), CHoCH M1 posterior al cierre del sweep M5 (20), BOS flip M5 (15), mecha M5 con FVG (15).
4. FVG aporta 10 y retest limpio 5. El componente de gatillo sigue limitado a 35. Se mantienen H1 25/15, M15 30/20/10, confluencias opcionales 10 y umbrales 85 estricto / 70 adaptativo.
5. La confirmación seleccionada debe tener timestamp válido, no futuro y antigüedad <=10 minutos. Producción convierte las aperturas de velas a sus cierres antes de medir antigüedad. El dato de otra temporalidad no rejuvenece el gatillo elegido.
6. El camino M1 utiliza velas cerradas y la estructura direccional del detector existente; no convierte cualquier BOS M1 en CHoCH. Sólo consume sweeps M5 cerrados antes de su CHoCH. Sin feed M1, conserva el camino M5.

Los workers SMC adaptativos pasan a consultar nuevos cierres M1; H1/M15/M5 conservan sus cachés por temporalidad. El camino M1 conserva el retest de OB y el cierre direccional; considera primero la candidata más reciente. No es entrada intravela.

## Ejecución y diagnóstico

`LiveTradingConfig.dual_m5_m1_trigger_enabled=True` activa la integración cuando `h1_location_only=True`; ORB conserva su programación. Puede desactivarse con `False`. El analizador standalone conserva el valor predeterminado False por compatibilidad.

La señal publica `confirmation_timeframe` y `m5_detailed_confirmation`: etiqueta, hora real de confirmación, hora de sweep M5 y latencia. El preflight usa la temporalidad que disparó la señal; para M1 vuelve a revisar además el contexto M5. Se mantienen stop, precio ejecutable, límite de velas posteriores y obstáculo mínimo a 1R. Por eso aprobar el score no equivale a abrir una operación. El límite de velas posteriores se aplica a la temporalidad del gatillo y puede ser más restrictivo que los 10 minutos.

Etiquetas principales: `M5_SWEEP_M5_CHOCH_STANDARD`, `M5_SWEEP_M1_CHOCH_EARLY_TRIGGER`, `RECLASSIFIED_BOS_TO_CHOCH`, `VALIDATED_WICK_CHOCH_WITH_FVG`, `TRUE_MISSING_CHOCH`, `MISSING_SWEEP_ONLY`, `EXPIRED_SIGNAL`, `INVALID_TIMESTAMP`, `M1_CHOCH_NOT_AFTER_M5_SWEEP`.

La telemetría existente conserva estas etiquetas en `m5_diagnostic_tags` y separa aprobaciones estrictas/adaptativas de órdenes ejecutadas.

## Pruebas locales

Desde C:/TradingBoot/smc_synthetic_bot:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_dual_trigger.py -q -p no:cacheprovider
.\.venv\Scripts\python.exe tools/analyze_smc_telemetry.py
```

Las nuevas etiquetas sólo aparecerán en procesos que hayan cargado este código. Los registros de procesos anteriores no demuestran el comportamiento del gatillo dual. Las pruebas automatizadas verifican lógica e integración, no rentabilidad ni funcionamiento con cotizaciones en vivo.
