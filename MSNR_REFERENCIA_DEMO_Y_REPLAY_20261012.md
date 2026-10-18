# Malaysian SNR: referencia DEMO y comparación de confirmaciones

La configuración de referencia está aplicada en DEMO. M5 y el apoyo H4 continúan en observación en el bot. El experimento es offline y no envía órdenes ni activa activos descartados.

## Configuración aplicada

- Versión de preferencias: 10; estrategia: msnr-v2.7-data-ai-confirmations.
- IA en Filtro; ante un modelo incompatible, Observar solo en DEMO. REAL conserva el bloqueo.
- Fractal H1: cuerpo 45%; distancia 0.50 ATR.
- Retest: 90 minutos; recuperación: 45 minutos y cuerpo 35%.
- Selección operativa de Malaysian SNR: los 23 activos actuales. Los otros 37 se evalúan en una cohorte aparte.
- Los controles siguen disponibles en /strategy-bases, pestaña Malaysian SNR; restaurar carga el formulario y Guardar aplica los valores.

## Contraste de la auditoría adjunta

El CSV histórico reproduce 357 operaciones y +81.55 R para los 23 activos. Su WinRate ponderado, usando porcentajes redondeados del CSV, es 43.693%.

Para los 37 restantes, el archivo suma -203.11 R, frente a −189,7 R citados en el documento. El conjunto de 60 suma 987 operaciones y -121.56 R. Esta diferencia debe reconciliarse antes de usar el documento como certificación.

La selección de 23 activos se hizo usando esos resultados históricos. Por tanto, el 43,7% no es una prueba independiente de las reglas actuales ni una garantía de resultados futuros.

Además, el generador histórico disponible (tools/replay_malaysian_snr_full_universe.py) identifica setups usando el cierre H1, les asigna la hora de apertura H1 y empieza la simulación M15 desde esa hora. Eso puede incluir recorrido anterior a la disponibilidad de la señal. Sus runners de 2,5/3,5/5 R también difieren de los actuales. Sin una fuente causal congelada que respalde el CSV, sus cifras no deben considerarse una validación del bot actual.

## Cobertura comprobada

Ventana solicitada: 2024-10-11T00:00:00+00:00 a 2026-10-11T00:00:00+00:00. Límite de MetaTrader observado: 100,000 barras. Activos con inicio de dos años cubierto en todos los marcos: 0/60.

No se reconstruye M5 desde M15. Cada archivo contiene velas nativas con una huella SHA-256. Una sola vela antigua devuelta por el terminal no cuenta como cobertura.

| Activo operativo | Inicio M5 nativo | Inicio común de los cinco marcos |
|---|---|---|
| AUDNZD | 2025-06-10 | 2025-06-10 |
| Boom 1000 Index | 2025-10-30 | 2025-10-30 |
| Boom 300 Index | 2025-10-30 | 2025-10-30 |
| Crash 1000 Index | 2025-10-30 | 2025-10-30 |
| Crash 600 Index | 2025-10-30 | 2025-10-30 |
| EURCHF | 2025-06-09 | 2025-06-09 |
| EURGBP | 2025-06-10 | 2025-06-10 |
| EURUSD | 2025-06-10 | 2025-06-10 |
| GBPAUD | 2025-06-10 | 2025-06-10 |
| GBPJPY | 2025-06-10 | 2025-06-10 |
| GBPUSD | 2025-06-10 | 2025-06-10 |
| Jump 10 Index | 2025-10-30 | 2025-10-30 |
| Jump 25 Index | 2025-10-30 | 2025-10-30 |
| Step Index | 2025-10-30 | 2025-10-30 |
| Step Index 200 | 2025-10-30 | 2025-10-30 |
| Step Index 400 | 2025-10-30 | 2025-10-30 |
| USDJPY | 2025-06-10 | 2025-06-10 |
| Volatility 250 (1s) Index | 2025-10-30 | 2025-10-30 |
| Volatility 50 (1s) Index | 2025-10-30 | 2025-10-30 |
| Volatility 90 Index | 2026-02-13 | 2026-02-13 |
| Wall Street 30 | 2025-05-14 | 2025-05-14 |
| XAGUSD | 2025-05-14 | 2025-05-14 |
| XAUUSD | 2025-05-14 | 2025-05-14 |

Para completar la comparación de dos años falta ampliar el historial M5 nativo desde octubre de 2024 y volver a capturar los datos. Un límite de 500.000 barras permite solicitar esa cantidad, pero no garantiza que el broker conserve toda la historia. Step Index 400 y Volatility 90 también tienen comienzos posteriores en los otros marcos y deben conservar su etiqueta de cobertura parcial.

El nuevo límite requiere reiniciar la plataforma, según [la documentación de MetaTrader](https://www.metatrader5.com/en/terminal/help/startworking/settings). Ese reinicio no se realizó: otras estrategias mantienen posiciones abiertas.

El control de MetaTrader se detuvo con Escape; no se cambió ese límite ni se reinició el terminal.

## Piloto ejecutado

Período común: 2026-10-04T00:00:00+00:00 a 2026-10-11T00:00:00+00:00. Procesados: 60/60; errores: 0.

| Variante | Cohorte | Cerrados | WinRate estimado | R por operación | PF | Ambiguos | Censurados |
|---|---|---:|---:|---:|---:|---:|---:|
| M15 actual | 23 operativos | 10 | 10.000% | -0.666 | 0.260 | 0 | 1 |
| M15 actual | 37 descartados | 15 | 20.000% | -0.400 | 0.500 | 0 | 2 |
| M15 + M5 | 23 operativos | 29 | 24.138% | -0.303 | 0.601 | 0 | 2 |
| M15 + M5 | 37 descartados | 49 | 14.286% | -0.556 | 0.351 | 0 | 5 |
| M15 + H4 neutral | 23 operativos | 10 | 10.000% | -0.666 | 0.260 | 0 | 1 |
| M15 + H4 neutral | 37 descartados | 16 | 25.000% | -0.310 | 0.587 | 0 | 2 |

Estas cifras son un piloto corto sobre velas OHLC y spread histórico aproximado. No acreditan un incremento sostenido de WinRate ni sustituyen los dos años solicitados. Los intervalos Wilson del JSON son descriptivos y no corrigen la dependencia entre operaciones.

Se conservan una posición por símbolo y la deduplicación del episodio H1; la confirmación M15 tiene prioridad si M15 y M5 coinciden. El fill se toma de la apertura M5, con spread de la última vela cerrada. La simulación divide el riesgo 50/50, apunta a 2R y un runner contextual hasta 4R, y mueve el runner a BE más spread de TP1 y dos puntos. Una colisión intrabar se cuenta de forma conservadora y se etiqueta ambigua; huecos y finales sin resolución se censuran.

Comisiones, swaps, deslizamiento, redondeo a tick, distancia mínima de stop y límites agregados de cartera no están reproducidos. Se publican sensibilidades de coste adicional de 0,05 R y 0,10 R. Ningún resultado de este replay se incorpora como etiqueta de entrenamiento verificada.

## Estado observado del bot

Candidatos únicos: 27; lecturas: 3644; confirmados: 0; ejecutados: 0. El WinRate operativo aún no tiene muestra.

| Último bloqueo del candidato | Candidatos |
|---|---:|
| SETUP_EXPIRED | 8 |
| LEVEL_CONSUMED | 5 |
| DIRECTION_POLICY_BLOCKED | 5 |
| RETEST_PENETRATION_TOO_DEEP | 3 |
| WAITING_RETEST_RECOVERY | 2 |
| RETEST_WEAK_RECOVERY | 2 |
| WAITING_FIRST_RETEST | 1 |
| SETUP_ALREADY_CONFIRMED | 1 |

Estos son estados actuales de candidatos únicos; no son conteos de pérdidas ni pruebas de que quitar un filtro mejore la calidad.

## Validación y siguiente decisión

- 63 pruebas pasan: causalidad, ejecución, cierre de velas, M5, H4, persistencia y política IA.
- Paridad contra la estrategia sin cachés verificada en XAGUSD: señales y motivos idénticos, incluida una entrada M5.
- Las preferencias y el código del experimento quedan congelados con sus huellas; no se reutilizan checkpoints con otras reglas.
- No se promovió M5, H4 ni ninguno de los 37 descartados a operación automática.

Antes de promover una variante: completar la cobertura; dividir el período cronológicamente; evaluar las nuevas operaciones y los episodios compartidos; contrastar expectativa, PF, drawdown, costes y WinRate por familia con incertidumbre que respete la agrupación temporal; confirmar después en DEMO con costes de ejecución reales. Una variante con más entradas y expectativa negativa debe seguir en observación.

Archivos: confirmation_history_manifest.json; live_reference_verified.json; parity_verification.json; pilot_7d_all60/run.json, summary.json y trades.csv, dentro de storage/analysis/msnr_v27_m5_reference_20261012.

Referencia técnica del límite de históricos y tiempos UTC: [MetaTrader 5 copy_rates_range](https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesrange_py).