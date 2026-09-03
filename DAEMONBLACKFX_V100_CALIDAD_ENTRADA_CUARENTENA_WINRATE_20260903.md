# DaemonBlackFx v100 — calidad de entrada, cuarentena y win rate

## Diagnóstico de los logs (02–03 septiembre 2026)

- GOLD no estaba detenido: realizó 172 evaluaciones de XAUUSD. Hubo 138 ciclos
  sin confirmación M5, 10 esperando una confirmación M5 posterior al setup M15
  y 24 fuera de la ventana de nuevas entradas. No abrió órdenes.
- En las cuatro particiones FOREX se evaluaron 4.993 símbolos. Hubo 4.848
  rechazos por ausencia de setup M15 o confirmación M5 y 997 evaluaciones
  bloqueadas correctamente durante rollover. No hubo órdenes.
- En GOLD, las 138 candidatas M5 rechazadas carecían del desplazamiento
  obligatorio y también fueron marcadas con conflicto chartista. El
  desplazamiento se conserva como gate duro; el detector chartista sí se
  corrigió porque usaba un 0,6% fijo excesivo para Forex/Oro M5.
- Los cuatro registros de `risk_quarantine.json` fueron breaches marginales:
  sólo 0,11%–0,74% por encima del hard cap. Son compatibles con granularidad de
  volumen y desplazamiento entre cálculo y fill, no con un descontrol material.
- Las auditorías contienen 21 XLSX, pero sólo 20 `source_trade_id` únicos; uno
  está duplicado. El PnL único suma exactamente -161,16, igual al panel de
  cuenta. El panel registra 22 trades, por lo que faltan dos auditorías en el
  ZIP entregado.
- Atribuyendo las piernas MT5 recuperadas a su setup original, ARPS quedó cerca
  de equilibrio/ligeramente positivo (aprox. +2,11), mientras el SMC sintético
  concentró aproximadamente -163,27. La muestra es demasiado pequeña para
  optimizar umbrales estadísticos sin sobreajuste.

## Cambios implementados

1. **Patrones chartistas normalizados por volatilidad.** El 0,6% ahora es un
   techo y la tolerancia efectiva se ajusta al rango mediano reciente. Se evita
   fabricar dobles/triples techos y pisos opuestos en M5 de Forex y Oro.
2. **Conflicto con fuerzas similares como penalización.** `FUERZAS_SIMILARES`
   resta score, pero no bloquea por sí solo. `DOMINANT_CONTRA` y
   `CONTRA_MAS_FUERTE` siguen siendo gates duros.
3. **Armónico realmente opcional.** Cuando `require_harmonic=False`, su ausencia
   ya no aumenta el denominador ni reduce el porcentaje de confirmación. Si
   existe, conserva su bonus; si se configura obligatorio, vuelve al denominador.
4. **Reserva pre-fill del 1%.** Los daemons productivos dimensionan al 99% del
   presupuesto y aceptan una banda inferior segura de 97%. El hard cap post-fill
   permanece en 102%; no se aumentó el riesgo permitido.
5. **Cuarentena recuperable y concurrente.** Breaches marginales de hasta 3%
   sobre el objetivo se cierran por seguridad, entran en cooldown de 60 minutos
   y se liberan automáticamente. Incidentes mayores, datos inválidos o posición
   ausente siguen requiriendo revisión manual. El JSON usa lock entre
   hilos/procesos y reemplazo atómico con temporales únicos.
6. **Fallback de volumen reparado.** Si el lote mínimo hace inviable una pierna
   TP1/Runner, el error se convierte en un rechazo estructurado y se intenta la
   entrada única segura. Antes la excepción terminaba como `ERROR` y nunca
   alcanzaba el fallback.
7. **Defensa ARPS al minuto.** Una salida anticipada puede actuar desde el
   minuto 1, pero sólo con pérdida, MFE menor a 0,05R y dos invalidaciones M1
   distintas. Los filtros de régimen, tendencia, ADX y estructura no se relajaron.
8. **Menos latencia sin perder estructura.** H1 conserva 500 velas; M15 usa 500
   y M5 350. Esto cubre holgadamente los lookbacks máximos (100 + retest 50) y
   evita recalcular 1.000 velas por etapa y símbolo.
9. **Telemetría sin falso 0/0.** `WAITING_NEW_M5_BAR/M1_BAR` muestra `0/N`
   instrumentos disponibles. Esperar una vela nueva ya no parece ausencia de
   símbolos o falta total de análisis.
10. **Win rate explicable.** `/account` separa el win rate por piernas del win
    rate por setups lógicos, excluye emergencias sin PnL del segundo y muestra
    PnL/win rate/emergencias por estrategia.
11. **Auditoría accesible para todos los trades.** El enlace de auditoría ya no
    depende de que existan snapshots periódicos. Para cierres inmediatos o de
    emergencia, la página/API usa el contrato persistente del mismo trade como
    fallback identificado; así también se puede abrir y descargar su Excel.

## Guardrails preservados

- GOLD: desde Tokio 09:00 hasta apertura de Nueva York 09:30, con DST por zona.
- FOREX: desde Tokio 09:00; corte de entradas 16:30 NY y force-flat 16:45 NY.
- Sólo velas cerradas, M5 posterior al M15 vigente y máximo 2 velas de antigüedad.
- Secuencia H1 → M15 → M5, desplazamiento obligatorio y gates BOS/CHOCH.
- BOOM sólo BUY, CRASH sólo SELL y Flip en ambas direcciones.
- ORB y su control de correlación no fueron modificados.

## Validación

- Compilación completa de `strategy`, `dashboard`, `app`, `database` y
  `reporting`: correcta.
- Suite focal v100 + regresiones relacionadas: 60 pruebas aprobadas.
- Suite completa: 487 aprobadas y 16 fallos heredados ya presentes en v99; no se
  añadió ningún fallo nuevo y se corrigió una regresión heredada de interfaz de
  auditoría. Los 7 tests v100 cubren armónico opcional, conflicto
  similar, tolerancia por volatilidad, fallback por lote mínimo, expiración de
  cuarentena, progreso del scheduler y métricas de win rate lógico.

## Qué observar en la próxima sesión

- GOLD/FOREX deben seguir rechazando candidatas sin desplazamiento; la mejora no
  garantiza entradas, sólo elimina falsos conflictos y errores de conteo.
- Comparar `chart_pattern_configured_price_tolerance` con
  `chart_pattern_effective_price_tolerance` en la auditoría.
- Confirmar que los registros antiguos marginales desaparecen de
  `risk_quarantine.json` tras ser consultados y que no reaparecen con la reserva
  pre-fill.
- Evaluar win rate por setup y por estrategia sobre al menos 30–50 setups
  decisivos antes de modificar ADX, score o desplazamiento.

## Instalación sobre la carpeta existente

1. Detener el coordinador y confirmar que no queden procesos `app.main`.
2. Respaldar `%LOCALAPPDATA%\BlackDaemonFx\trading_bot.sqlite3`.
3. Copiar el contenido del ZIP v100 sobre el proyecto. El paquete no incluye
   `.venv`, `.env`, bases de datos, cuarentenas ni exports; por lo tanto conserva
   el entorno y la persistencia local existentes.
4. Verificar la versión:

   ```powershell
   python -c "from daemon_version import DAEMONBLACKFX_VERSION; print(DAEMONBLACKFX_VERSION)"
   ```

5. Iniciar con el comando habitual:

   ```powershell
   python -m app.main --mode multi-bot-daemon --execute --interval 30 --position-monitor-interval 2 --risk-percent 1.0 --min-rr 1.5 --dashboard --dashboard-port 8765
   ```

No es necesario borrar manualmente `risk_quarantine.json`: v100 reconoce y
expira los cuatro incidentes marginales antiguos al consultar cada símbolo.
