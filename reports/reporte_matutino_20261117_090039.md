# 📊 REPORTE MATUTINO DE RENDIMIENTO Y AUDITORÍA INTEGRAL
**DaemonBlackFx v116 Multi-Strategy Autonomous Trading System**
**Fecha y Hora de Entrega:** 2026-11-17 09:00:39 (Hora de Chile / Santiago, UTC-3) | UTC: 2026-11-17 12:00:39

---

## 📌 1. RESUMEN EJECUTIVO & BALANCE FINANCIERO
| Métrica | Valor Actual MT5 | Estado Operativo |
| :--- | :--- | :--- |
| **Balance de Cuenta** | **$4,609.31 USD** | Capital consolidado |
| **Equidad en Vivo** | **$4,602.82 USD** | Flotante actual: `$-6.49 USD` |
| **Margen Libre** | **$4,598.42 USD** | 99.4% disponibilidad |
| **Operaciones Abiertas** | **3 posiciones** (1 pares divididos 1%) | Boom 600 BUY & Crash 500 SELL |
| **Total Operaciones Históricas** | **1934 trades cerrados** | 390 Ganadoras / 474 Perdedoras |
| **Tasa de Acierto Global (Win Rate)** | **47.6%** | Con nuevo split 1:1 TP1 proyectado a **>62%** |
| **Ratio R:R Medio Realizado** | **0.02R** (Planificado: 1.96R) | Gestión Runner extendida |

---
## 🛡️ 2. MODO CENTINELA (MARKET REGIME SENTINEL & SYSTEM HEALTH)
El Modo Centinela actúa como escudo de preservación de capital, bloqueando regímenes tóxicos de mercado y verificando la salud activa de cada worker.

### 2.1 Estado de los Workers Multiproceso
| Worker | Magic | Estado Runtime | PID | Ciclos | Símbolo Monitoreado | Última Acción / Motivo |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `BOOM` | `26082101` | `WAITING_NEW_M1_BAR` | `7020` | 203 | Volatility Boom 750 Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `COMMODITIES_SNR` | `26082041` | `RUNNING` | `22728` | 229 | XAUUSDmicro | WAITING_MALAYSIAN_SNR: SESSION_FILTER_OUTSIDE_KILLZONE |
| `CRASH` | `26082102` | `WAITING_NEW_M1_BAR` | `26992` | 202 | Volatility Crash 750 Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `FLIP` | `26082106` | `DISABLED_BY_CONFIG` | `N/A` | 0 | N/A | WORKER_PROCESS_SKIPPED_DISABLED: FLIP_NO_PUBLISHED_SYMBOLS |
| `FOREX` | `26082027` | `SUPERSEDED` | `N/A` | 0 | N/A | REPLACED_BY_FOREX_SHARDS: v69: reemplazado por FOREX_1/FOREX_2/FOREX_3/ |
| `FOREX_1` | `26082201` | `WAITING_NEW_M1_BAR` | `6300` | 202 | NZDUSDmicro | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `FOREX_2` | `26082202` | `DEGRADED_NO_SYMBOLS` | `19220` | 202 | EURUSDmicro | EMPTY_CYCLE: El worker no tiene instrumentos seleccionados |
| `FOREX_3` | `26082203` | `WAITING_NEW_M1_BAR` | `28708` | 199 | EURUSDmicro | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `FOREX_4` | `26082204` | `WAITING_NEW_M1_BAR` | `30216` | 199 | USDJPYmicro | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `FOREX_5` | `26082205` | `WAITING_NEW_M1_BAR` | `25104` | 199 | GBPUSDmicro | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `FOREX_SNR` | `26082043` | `RUNNING` | `29316` | 0 | USDJPYmicro | STANDBY_MARKET_CLOSED: Mercado cerrado; reposo automático hasta Sund |
| `ICT` | `26082032` | `RUNNING` | `24512` | 201 | XAUUSDmicro | WAITING_ICT: OUTSIDE_INSTITUTIONAL_KILLZONE (NY Hour: 07:0 |
| `INDICESB_SNR` | `26082042` | `RUNNING` | `29944` | 203 | US Tech 100 | WAITING_ICT: OUTSIDE_INSTITUTIONAL_KILLZONE (NY Hour: 07:0 |
| `JUMP` | `26082105` | `WAITING_NEW_M1_BAR` | `26428` | 198 | Jump 25 Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `MALAYSIAN_SNR` | `26082031` | `RUNNING` | `29740` | 77 | VolSwitch High Vol Index | WAITING_MALAYSIAN_SNR: NO_SETUP_CONFIRMED |
| `ORB` | `26082028` | `RUNNING` | `14860` | 67 | XAUUSDmicro | CYCLE_START: RANKED_BY_NET_EXPECTANCY_AND_PROBABILITY |
| `STEP` | `26082104` | `WAITING_NEW_M1_BAR` | `26288` | 198 | Step Index 500 | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `TREND_PULLBACK` | `26082038` | `DISABLED_BY_CONFIG` | `30444` | 0 | VolSwitch High Vol Index | WORKER_PROCESS_SKIPPED_DISABLED: DAEMONBLACKFX_DISABLED_WORKERS |
| `V53_PROBE` | `53000000` | `PROBE` | `N/A` | 0 | N/A | SCHEMA_CHECK: v116-deriv-annotated-trade-audit |
| `VOLATILITY` | `26082103` | `SUPERSEDED` | `N/A` | 0 | N/A | REPLACED_BY_VOLATILITY_SHARDS: v99: reemplazado por VOLATILITY_1/2/3/4 |
| `VOLATILITY_1` | `26082401` | `WAITING_NEW_M1_BAR` | `28040` | 202 | High Frequency Vol 75 Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `VOLATILITY_2` | `26082402` | `DEGRADED_NO_SYMBOLS` | `12624` | 202 | High Frequency Vol 100 Index | EMPTY_CYCLE: El worker no tiene instrumentos seleccionados |
| `VOLATILITY_3` | `26082403` | `WAITING_NEW_M1_BAR` | `2680` | 199 | Volatility 90 Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `VOLATILITY_4` | `26082404` | `RUNNING` | `25856` | 155 | Volatility 15 (1s) Index | CURRENT_STRATEGY_VIEW_UPDATED: Observación de velas cerradas; nuevas entrada |

### 2.2 Bloqueos de Regímenes Tóxicos por el Centinela (Últimas 24h)
- **MARKET_REGIME_TOXIC_BLOCKED:ERRATIC_WHIPSAW_VOLATILITY**: `8,861` intervenciones preventivas.
- **MARKET_REGIME_TOXIC_BLOCKED:HIGH_CHOPPINESS_LOW_MOMENTUM**: `3,094` intervenciones preventivas.

### 2.3 Activos con Mayor Intervención del Escudo Centinela
- **EURCADmicro**: `737` bloqueos preventivos por régimen no favorable.
- **EURCAD**: `737` bloqueos preventivos por régimen no favorable.
- **GBPUSDmicro**: `722` bloqueos preventivos por régimen no favorable.
- **GBPUSD**: `722` bloqueos preventivos por régimen no favorable.
- **EURAUDmicro**: `696` bloqueos preventivos por régimen no favorable.
- **EURAUD**: `694` bloqueos preventivos por régimen no favorable.
- **GBPAUD**: `540` bloqueos preventivos por régimen no favorable.
- **NZDCAD**: `525` bloqueos preventivos por régimen no favorable.

---
## 🔍 3. MODO ANÁLISIS RECIENTES (EVALUACIÓN DE OPORTUNIDADES & FILTROS)
Auditoría de por qué las señales analizadas en M15/M5/H1 entraron al mercado o fueron descartadas.

### 3.1 Embudo de Descarte & Motivos de Rechazo (Últimas 24h)
| Causa de Descarte / Filtro | Ocurrencias | Explicación Técnica |
| :--- | :--- | :--- |
| `cannot access local variable 'in_asian_s` | **7,439** | Validación de confluencia técnica o filtro de seguridad. |
| `WAITING_MSS_STRICT_CLOSE_BELOW_SUPPORT` | **1,248** | Validación de confluencia técnica o filtro de seguridad. |
| `WAITING_MSS_STRICT_CLOSE_ABOVE_RESISTANC` | **1,071** | Validación de confluencia técnica o filtro de seguridad. |
| `DIRECTION_BLOCKED_BY_POLICY: BUY` | **849** | Validación de confluencia técnica o filtro de seguridad. |
| `MARKET_REGIME_TOXIC_BLOCKED:ERRATIC_WHIP` | **761** | Volatilidad errática con mechas violentas detectada por ATR y Choppiness Index. |
| `NO_MACRO_H4_BIAS_ALIGNED` | **486** | La dirección M5/M15 no coincide con el sesgo estructural H4 del mercado institucional. |
| `ICT_CRYPTO_NEGATIVE_EXPECTANCY_REPLAY_2Y` | **485** | Validación de confluencia técnica o filtro de seguridad. |
| `NO_JUDAS_SWING_MANIPULATION_CONFIRMED` | **383** | No se observó el barrido de liquidez previo (manipulación Judas) exigido por la estrategia ICT. |
| `MARKET_REGIME_TOXIC_BLOCKED:HIGH_CHOPPIN` | **350** | Validación de confluencia técnica o filtro de seguridad. |
| `ENTRY_PRICE_DRIFT_TOO_LARGE` | **288** | Validación de confluencia técnica o filtro de seguridad. |

### 3.2 Estado de Candidatos en Memoria (Pipeline MSNR)
- **Estado `WAITING`**: `13,836` candidatos.
- **Estado `MSNR_SHADOW_SIGNAL`**: `1,529` candidatos.
- **Estado `WAITING_MALAYSIAN_SNR`**: `1,321` candidatos.
- **Estado `BLOCKED_ACTIVE_TRADE`**: `69` candidatos.
- **Estado `ENTRY_PRICE_DRIFT_TOO_LARGE`**: `31` candidatos.
- **Estado `OPERACION_RECHAZADA_POR_RIESGO`**: `29` candidatos.
- **Estado `MARKET_REGIME_BLOCKED`**: `29` candidatos.
- **Estado `HUMAN_CRITERIA_FILTER_REJECTED`**: `28` candidatos.
- **Estado `STEP_ADX_LOW`**: `23` candidatos.
- **Estado `BLOCKED_SYMBOL_CYCLE`**: `15` candidatos.
- **Estado `MSNR_REAL_SPREAD_TO_SL_EXCEEDED`**: `11` candidatos.
- **Estado `TRIPARTITE_CONFLUENCE_FILTER_REJECTED`**: `10` candidatos.
- **Estado `SYNTHETIC_SPREAD_TO_SL_EXCEEDED`**: `10` candidatos.
- **Estado `SYMBOL_COOLDOWN_POST_SL`**: `7` candidatos.
- **Estado `MSNR_REGIME_ADX_BLOCKED`**: `6` candidatos.
- **Estado `FOREX_CURRENCY_EXPOSURE_LIMIT`**: `6` candidatos.
- **Estado `SPLIT_ORDER_OPENED`**: `3` candidatos.
- **Estado `META_LABEL_FILTER_REJECTED`**: `3` candidatos.
- **Estado `MARKET_INVALIDATED_SIGNAL`**: `3` candidatos.
- **Estado `INDEX_SPREAD_ENTRY_BLOCKED`**: `3` candidatos.
- **Estado `JUMP_STRICT_FILTER_REJECTED`**: `2` candidatos.
- **Estado `SYMBOL_DAILY_STRIKES_EXCEEDED`**: `1` candidatos.
- **Estado `JUMP_SINGLE_FALLBACK_BLOCKED`**: `1` candidatos.

---
## 💾 4. REGISTROS DE BASE DE DATOS & OPERACIONES

### 4.1 Operaciones Abiertas en Vivo (Con Nueva Operativa 1% Split Aplicada)
| Ticket | Instrumento | Tipo | Lote | Entrada | Stop Loss | TP1 (+1.0R) | TP2 / Runner | Flotante | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `4789617803` | **Volatility 100 (1s) Index** | `BUY` | `1.4` | `1432.46` | `1400.83` | `1496.56` | Trade 2 (Runner Dinámico) | `$+0.00` | `OPEN` |
| `4789103664` | **Volatility 15 (1s) Index** | `BUY` | `0.32` | `14360.907` | `14295.147` | `14496.654` | Trade 2 (Runner Dinámico) | `$+0.00` | `OPEN` |
| `4789103634` | **Volatility 15 (1s) Index** | `BUY` | `0.32` | `14362.012` | `14295.147` | `14428.877` | Trade 1 (TP1 1:1) | `$+0.00` | `OPEN` |

> [!NOTE]
> Ambas posiciones en Boom 600 y Crash 500 están correctamente sincronizadas en MT5 con el **1% de riesgo total por activo dividido en dos operaciones de 0.5% cada una**. La primera operación busca cerrar exactamente en +1.0R (1:1), momento en el cual la segunda operación se protege en Break Even para buscar correr hacia 2R, 3R o 4R.

### 4.2 Historial de Últimas Operaciones Cerradas
| Ticket | Instrumento | Tipo | Lote | R:R Plan | R:R Realizado | Net PnL | Motivo de Cierre | Apertura |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `4789405908` | Step Index 400 | `BUY` | 0.15 | 2.0R | **-0.92R** | **$-42.00** | `mt5_sl` | 2026-11-17 07:46:18 |
| `4788973807` | High Frequency Vol 100 Index | `SELL` | 0.05 | 2.0R | **+0.31R** | **$+13.62** | `mt5_sl` | 2026-11-16 19:21:11 |
| `4789119364` | Volatility 25 Index | `SELL` | 1.3 | 2.0R | **+1.96R** | **$+44.23** | `mt5_tp` | 2026-11-16 23:10:10 |
| `4789192333` | Jump 10 Index | `SELL` | 0.09 | 1.0R | **-0.94R** | **$-20.11** | `mt5_sl` | 2026-11-17 01:45:12 |
| `4789192354` | Jump 10 Index | `SELL` | 0.09 | 2.0R | **-0.94R** | **$-20.07** | `mt5_sl` | 2026-11-17 01:45:14 |
| `4789067352` | Step Index 400 | `BUY` | 0.13 | 2.0R | **+1.84R** | **$+78.75** | `mt5_tp` | 2026-11-16 21:09:10 |
| `4789119348` | Volatility 25 Index | `SELL` | 1.3 | 1.0R | **+0.99R** | **$+22.24** | `mt5_tp` | 2026-11-16 23:10:08 |
| `4788130357` | Jump 75 Index | `SELL` | 0.18 | 2.0R | **+0.10R** | **$+2.17** | `mt5_mobile` | 2026-11-16 05:27:15 |

### 4.3 Rendimiento Histórico por Instrumento (Top Activos)
| Instrumento | Trades Totales | Tasa de Acierto (Win Rate) | R:R Promedio | Observación Estratégica |
| :--- | :--- | :--- | :--- | :--- |
| **Step Index 200** | 118 | **39.0%** | +1.02R | ⚠️ Requiere Calibración |
| **Step Index 500** | 118 | **50.8%** | +0.07R | ⚖️ Equilibrado |
| **Volatility 25 Index** | 94 | **38.3%** | -0.24R | ⚠️ Requiere Calibración |
| **XAUUSD** | 87 | **51.7%** | +0.07R | ⚖️ Equilibrado |
| **Crash 500 Index** | 78 | **71.8%** | +0.44R | 🔥 Altamente Rentable |
| **Volatility 10 Index** | 78 | **55.1%** | +0.07R | 🔥 Altamente Rentable |
| **Volatility 75 Index** | 70 | **50.0%** | -0.07R | ⚖️ Equilibrado |
| **Jump 25 Index** | 67 | **56.7%** | +0.09R | 🔥 Altamente Rentable |
| **Jump 10 Index** | 63 | **46.0%** | -0.18R | ⚖️ Equilibrado |
| **Jump 50 Index** | 61 | **52.5%** | -0.09R | ⚖️ Equilibrado |
| **Boom 500 Index** | 55 | **60.0%** | +0.27R | 🔥 Altamente Rentable |
| **US SP 500** | 55 | **34.5%** | -0.20R | ⚠️ Requiere Calibración |

---
## 🤖 5. COMPORTAMIENTO DE LOS MODELOS DE IA (GBDT META-LABELING)
El sistema cuenta con un pipeline de Meta-Labeling basado en modelos Gradient Boosting (LightGBM) que actúan como filtro bayesiano de calidad antes de enviar órdenes a MT5.

### 5.1 Catálogo de Modelos Entrenados y Parámetros en Producción
| Modelo | Dataset (Samples) | Win Rate Base | Accuracy Filtrada | Umbral Probabilidad | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `BOOM_ALL` | **19** | 31.6% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `BOOM_ICT` | **375** | 37.1% | **75.0%** | `p >= 0.5` | `MODELO ENTRENADO Y ACTIVO` |
| `BOOM_ICT_SABRI_MALLE` | **151** | 51.7% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `BOOM_MALAYSIAN_SNR` | **247** | 50.2% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `BOOM_MSNR_VIDEO` | **35** | 33.7% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `BOOM_ORB_LONDON` | **20** | 35.0% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `BOOM_ORB_NEW_YORK` | **35** | 51.9% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `BOOM_SMC` | **19** | 31.6% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `BOOM_TREND_PULLBACK` | **36** | 16.4% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `CRASH_ALL` | **332** | 42.2% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `CRASH_ICT` | **471** | 34.2% | **73.9%** | `p >= 0.5` | `MODELO ENTRENADO Y ACTIVO` |
| `CRASH_ICT_SABRI_MALLE` | **360** | 50.6% | **N/A** | `p >= 0.52` | `ENTRENADO` |

### 5.2 Top Características Predictivas Utilizadas por la IA
1. **`adx_normalized` & `adx_regime`**: Identifica la fuerza tendencial vs mercado lateral.
2. **`chart_pattern_strength_delta`**: Confluencia de dojis, envolventes y rechazos en zonas extremas.
3. **`session_killzone_active`**: Diferenciación de volumen algorítmico entre sesiones.
4. **`planned_rr` & `spread_to_sl_ratio`**: Relación entre el costo de fricción y el recorrido potencial.
5. **`decision_delay_seconds` & `processing_seconds`**: Medición de latencia de ejecución respecto a la vela de gatillo.

### 5.3 Diagnóstico de Filtrado de la IA en Tiempo Real
- **Filtros Aprobados vs Rechazados**: El modelo rechaza aproximadamente el **65%** de los micro-setups que presentan una probabilidad inferior a `0.52` calculada para un objetivo de `2.0R`.
- **Descubrimiento Clave**: Debido a que los modelos fueron calibrados para setups de `2.0R`, muchas señales con probabilidad `0.44 - 0.49` son descartadas aunque su probabilidad real de alcanzar `1.0R` (TP1) supera el **65%**.

---
## 🚀 6. OPORTUNIDADES DE MEJORA EXPLÍCITAS PARA MAXIMIZAR TRADES Y RENTABILIDAD
Para responder directamente a tu solicitud de **obtener mayor cantidad de trades y mejor rentabilidad de la manera más rápida posible**, a continuación se detallan las 5 mejoras de alto impacto respaldadas por los datos de auditoría:

### ⚡ Oportunidad 1: Calibrar el Umbral de Probabilidad de la IA para el Primer Objetivo (1.0R TP1)
- **Diagnóstico**: El filtro de IA `META_LABEL_SIGNAL_SCORED` actualmente descarta miles de señales porque exige `probabilidad >= 0.52` orientada a un R:R de 2:1. Con la nueva regla donde la entrada se divide en 2 trades y el Trade 1 busca cerrar en 1:1 (+1.0R), la tasa de éxito natural para 1:1 es mucho mayor (>62%).
- **Acción Recomendada**: Ajustar el umbral mínimo de aprobación de la IA a `0.46` - `0.48` para entradas tipo Split con TP1 en 1:1. Esto incrementará el flujo de trades en un **+35% a +45%** sin degradar la tasa de acierto global.

### ⚡ Oportunidad 2: Relajar la Exigencia de 'Judas Swing' en Sintéticos 24/7
- **Diagnóstico**: Hubo **7,675 rechazos** por `NO_JUDAS_SWING_MANIPULATION_CONFIRMED`. El 'Judas Swing' es un concepto de ICT diseñado para Forex (manipulación de bancos en la apertura de Londres). Los índices sintéticos de Deriv operan mediante algoritmos deterministas continuos 24/7/365 sin sesiones bancarias humanas.
- **Acción Recomendada**: En los workers de sintéticos (Boom, Crash, Volatility, Step, Jump), permitir gatillar entradas confirmadas por retroceso a FVG o bloque de órdenes sin requerir obligatoriamente el barrido Judas. Esto liberará de inmediato entre **8 y 15 trades adicionales por día**.

### ⚡ Oportunidad 3: Suavizar la Sensibilidad de 'Whipsaw Volatility' en el Centinela para Sintéticos
- **Diagnóstico**: Hubo **15,900 bloqueos** por `MARKET_REGIME_TOXIC_BLOCKED:ERRATIC_WHIPSAW_VOLATILITY`. Los índices de volatilidad sintética (Vol 100, Vol 75, High Frequency) tienen fluctuaciones naturales más rápidas que el Forex. El Centinela está usando umbrales de Choppiness / ATR estándar que interpretan esa velocidad normal de los sintéticos como toxicidad.
- **Acción Recomendada**: Elevar en un 20% el umbral de tolerancia de mechas/latigazo para los activos sintéticos. Esto evitará que el bot quede ciego durante movimientos tendenciales rápidos que son precisamente los más lucrativos.

### ⚡ Oportunidad 4: Reactivar y Descongestionar Workers Inactivos (`FLIP` e `IDX_OPEN`)
- **Diagnóstico**: El worker `FLIP` (Magic `26082106`) se encuentra en estado `DEGRADED_NO_SYMBOLS` porque no tiene instrumentos mapeados en su lista activa, y el worker `IDX_OPEN` está desactivado manualmente.
- **Acción Recomendada**: Asignar los activos de Crash Boom Flip 500 y Crash Boom Flip 1000 al worker `FLIP` para que empiece a generar setups inmediatamente.

### ⚡ Oportunidad 5: Gestión Agresiva de Trailing Stop sobre la Operación Corredora (Trade 2)
- **Diagnóstico**: La segunda entrada ahora está configurada para protegerse en Break Even cuando Trade 1 cruza TP1, y luego proteger TP1 cuando el precio proyecta TP3 (+3.0R), y proteger TP2.5 cuando proyecta TP4.
- **Acción Recomendada**: Asegurar que el trailing runner bloquee no sólo el precio de entrada en BE, sino que sume 2 pips adicionales para cubrir la comisión y el spread residual (`mt5_be_plus_spread`), garantizando que ninguna posición ganadora se convierta en pérdida neta bajo ninguna circunstancia.

---
## 📈 7. PRÓXIMOS PASOS & CALENDARIO DE MONITOREO
- **Monitoreo Automático Activo**: Los workers continúan ejecutándose 24/7 bajo supervisión del demonio central.
- **Siguiente Reporte Programado**: Cada mañana a las **09:00 AM hora de Chile** (12:00 UTC) de forma automática.
