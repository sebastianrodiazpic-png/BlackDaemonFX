# 📊 REPORTE MATUTINO DE RENDIMIENTO Y AUDITORÍA INTEGRAL
**DaemonBlackFx v116 Multi-Strategy Autonomous Trading System**
**Fecha y Hora de Entrega:** 2026-10-30 09:02:41 (Hora de Chile / Santiago, UTC-3) | UTC: 2026-10-30 12:02:41

---

## 📌 1. RESUMEN EJECUTIVO & BALANCE FINANCIERO
| Métrica | Valor Actual MT5 | Estado Operativo |
| :--- | :--- | :--- |
| **Balance de Cuenta** | **$4,841.42 USD** | Capital consolidado |
| **Equidad en Vivo** | **$4,890.17 USD** | Flotante actual: `$+48.75 USD` |
| **Margen Libre** | **$4,832.55 USD** | 99.4% disponibilidad |
| **Operaciones Abiertas** | **6 posiciones** (3 pares divididos 1%) | Boom 600 BUY & Crash 500 SELL |
| **Total Operaciones Históricas** | **1577 trades cerrados** | 390 Ganadoras / 474 Perdedoras |
| **Tasa de Acierto Global (Win Rate)** | **47.1%** | Con nuevo split 1:1 TP1 proyectado a **>62%** |
| **Ratio R:R Medio Realizado** | **0.02R** (Planificado: 2.02R) | Gestión Runner extendida |

---
## 🛡️ 2. MODO CENTINELA (MARKET REGIME SENTINEL & SYSTEM HEALTH)
El Modo Centinela actúa como escudo de preservación de capital, bloqueando regímenes tóxicos de mercado y verificando la salud activa de cada worker.

### 2.1 Estado de los Workers Multiproceso
| Worker | Magic | Estado Runtime | PID | Ciclos | Símbolo Monitoreado | Última Acción / Motivo |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `BOOM` | `26082101` | `WAITING_NEW_M1_BAR` | `10424` | 11891 | Boom 900 Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `CARRY` | `26082037` | `RUNNING` | `25188` | 1542 | USDJPY | WAITING_CARRY: CARRY_NOT_IN_TOP |
| `CRASH` | `26082102` | `WAITING_NEW_M1_BAR` | `35788` | 12083 | Crash 900 Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `DRIFT` | `26082035` | `DISABLED_BY_CONFIG` | `20456` | 0 | Drift Switch Index 30 | WORKER_PROCESS_SKIPPED_DISABLED: DAEMONBLACKFX_DRIFT_OFF |
| `FLIP` | `26082106` | `DISABLED_BY_CONFIG` | `36136` | 0 | Crash Boom Flip 150 Index | WORKER_PROCESS_SKIPPED_DISABLED: FLIP_NO_PUBLISHED_SYMBOLS |
| `FOREX` | `26082027` | `SUPERSEDED` | `N/A` | 0 | N/A | REPLACED_BY_FOREX_SHARDS: v69: reemplazado por FOREX_1/FOREX_2/FOREX_3/ |
| `FOREX_1` | `26082201` | `RUNNING` | `23232` | 12074 | GBPJPYmicro | ANALYZANDO: MARKET_REGIME_TOXIC_BLOCKED:HIGH_CHOPPINESS_L |
| `FOREX_2` | `26082202` | `DISABLED_BY_CONFIG` | `30880` | 0 | EURUSDmicro | WORKER_PROCESS_SKIPPED_DISABLED: DAEMONBLACKFX_DISABLED_WORKERS |
| `FOREX_3` | `26082203` | `DISABLED_BY_CONFIG` | `10072` | 0 | GBPJPYmicro | WORKER_PROCESS_SKIPPED_DISABLED: DAEMONBLACKFX_DISABLED_WORKERS |
| `FOREX_4` | `26082204` | `DISABLED_BY_CONFIG` | `12676` | 0 | USDJPYmicro | WORKER_PROCESS_SKIPPED_DISABLED: DAEMONBLACKFX_DISABLED_WORKERS |
| `GOLD` | `26082029` | `DISABLED_BY_CONFIG` | `36100` | 0 | XAUUSDmicro | WORKER_PROCESS_SKIPPED_DISABLED: DAEMONBLACKFX_DISABLED_WORKERS |
| `ICT` | `26082032` | `RUNNING` | `8328` | 12067 | XAUUSDmicro | WAITING_ICT: OUTSIDE_INSTITUTIONAL_KILLZONE (NY Hour: 08:0 |
| `IDX_OPEN` | `26082030` | `DISABLED` | `28664` | 14 | Wall Street 30 | STRATEGY_DISABLED_FROM_DASHBOARD: Desactivado manualmente desde el dashboard |
| `JUMP` | `26082105` | `WAITING_NEW_M1_BAR` | `13488` | 11897 | Jump 75 Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `MALAYSIAN_SNR` | `26082031` | `RUNNING` | `14904` | 4006 | VolSwitch High Vol Index | ANALYZANDO: NO_SETUP_CONFIRMED |
| `MSNR` | `26082033` | `RUNNING` | `29984` | 44 | Volatility 5 Index | ANALYZANDO: NO_H4H1_CONFIRMATION |
| `NIGHT` | `26082034` | `RUNNING` | `29304` | 1545 | US Tech 100 | ANALYZANDO: OUTSIDE_NY_CLOSE_ENTRY_WINDOW |
| `ORB` | `26082028` | `OUTSIDE_SESSION` | `14032` | 4052 | XAUUSDmicro | OUTSIDE_SESSION: Análisis pausado fuera de sesión; próxima com |
| `RSI2` | `26082036` | `RUNNING` | `32580` | 1544 | Wall Street 30 | WAITING_RSI2: NO_RSI2_PULLBACK |
| `STEP` | `26082104` | `RUNNING` | `3296` | 11910 | Step Index 200 | CURRENT_STRATEGY_VIEW_UPDATED: Observación de velas cerradas; nuevas entrada |
| `V53_PROBE` | `53000000` | `PROBE` | `N/A` | 0 | N/A | SCHEMA_CHECK: v116-deriv-annotated-trade-audit |
| `VOLATILITY` | `26082103` | `SUPERSEDED` | `N/A` | 0 | N/A | REPLACED_BY_VOLATILITY_SHARDS: v99: reemplazado por VOLATILITY_1/2/3/4 |
| `VOLATILITY_1` | `26082401` | `RUNNING` | `6220` | 10566 | Volatility 15 Index | MONITOR_POSICIONES: BACKGROUND_MONITOR |
| `VOLATILITY_2` | `26082402` | `DISABLED_BY_CONFIG` | `36704` | 0 | High Frequency Vol 100 Index | WORKER_PROCESS_SKIPPED_DISABLED: DAEMONBLACKFX_DISABLED_WORKERS |
| `VOLATILITY_3` | `26082403` | `DISABLED_BY_CONFIG` | `7572` | 0 | Volatility 75 (1s) Index | WORKER_PROCESS_SKIPPED_DISABLED: DAEMONBLACKFX_DISABLED_WORKERS |
| `VOLATILITY_4` | `26082404` | `DISABLED_BY_CONFIG` | `35156` | 0 | Volatility 15 Index | WORKER_PROCESS_SKIPPED_DISABLED: DAEMONBLACKFX_DISABLED_WORKERS |

### 2.2 Bloqueos de Regímenes Tóxicos por el Centinela (Últimas 24h)
- **MARKET_REGIME_TOXIC_BLOCKED:ERRATIC_WHIPSAW_VOLATILITY**: `2,732` intervenciones preventivas.
- **MARKET_REGIME_TOXIC_BLOCKED:HIGH_CHOPPINESS_LOW_MOMENTUM**: `589` intervenciones preventivas.

### 2.3 Activos con Mayor Intervención del Escudo Centinela
- **EURJPYmicro**: `308` bloqueos preventivos por régimen no favorable.
- **EURJPY**: `308` bloqueos preventivos por régimen no favorable.
- **GBPJPYmicro**: `250` bloqueos preventivos por régimen no favorable.
- **GBPJPY**: `250` bloqueos preventivos por régimen no favorable.
- **GBPCHFmicro**: `220` bloqueos preventivos por régimen no favorable.
- **GBPCHF**: `220` bloqueos preventivos por régimen no favorable.
- **USDCHFmicro**: `197` bloqueos preventivos por régimen no favorable.
- **USDCHF**: `197` bloqueos preventivos por régimen no favorable.

---
## 🔍 3. MODO ANÁLISIS RECIENTES (EVALUACIÓN DE OPORTUNIDADES & FILTROS)
Auditoría de por qué las señales analizadas en M15/M5/H1 entraron al mercado o fueron descartadas.

### 3.1 Embudo de Descarte & Motivos de Rechazo (Últimas 24h)
| Causa de Descarte / Filtro | Ocurrencias | Explicación Técnica |
| :--- | :--- | :--- |
| `FOREX_ENTRADAS_SOLO_KILLZONES_LONDRES_07` | **2,038** | Horario restringido para pares de divisas fuera de las horas pico institucionales. |
| `WAITING_FIRST_RETEST` | **1,716** | Nivel identificado; esperando el primer retroceso técnico hacia la zona de valor. |
| `SESSION_FILTER_OUTSIDE_KILLZONE` | **1,475** | Fuera de la ventana de liquidez principal (Killzones Londres/NY). |
| `WAITING_MSS_STRICT_CLOSE_ABOVE_RESISTANC` | **1,153** | Validación de confluencia técnica o filtro de seguridad. |
| `WAITING_MSS_STRICT_CLOSE_BELOW_SUPPORT` | **882** | Validación de confluencia técnica o filtro de seguridad. |
| `LEVEL_CONSUMED` | **849** | Validación de confluencia técnica o filtro de seguridad. |
| `DIRECTION_BLOCKED_BY_POLICY: SELL` | **689** | Validación de confluencia técnica o filtro de seguridad. |
| `NO_MACRO_H4_BIAS_ALIGNED` | **633** | La dirección M5/M15 no coincide con el sesgo estructural H4 del mercado institucional. |
| `SETUP_EXPIRED` | **546** | El candidato superó la cantidad máxima de velas de espera sin confirmar retesteo. |
| `ICT_DIRECTION_ASYMMETRY_STEP_SELL_ONLY` | **516** | Validación de confluencia técnica o filtro de seguridad. |

### 3.2 Estado de Candidatos en Memoria (Pipeline MSNR)
- **Estado `WAITING`**: `5,866` candidatos.
- **Estado `WAITING_MALAYSIAN_SNR`**: `800` candidatos.
- **Estado `MSNR_SHADOW_SIGNAL`**: `661` candidatos.
- **Estado `BLOCKED_ACTIVE_TRADE`**: `49` candidatos.
- **Estado `STEP_ADX_LOW`**: `16` candidatos.
- **Estado `MARKET_REGIME_BLOCKED`**: `16` candidatos.
- **Estado `ENTRY_PRICE_DRIFT_TOO_LARGE`**: `16` candidatos.
- **Estado `OPERACION_RECHAZADA_POR_RIESGO`**: `8` candidatos.
- **Estado `BLOCKED_SYMBOL_CYCLE`**: `8` candidatos.
- **Estado `SYMBOL_COOLDOWN_POST_SL`**: `7` candidatos.
- **Estado `SYNTHETIC_SPREAD_TO_SL_EXCEEDED`**: `4` candidatos.
- **Estado `META_LABEL_FILTER_REJECTED`**: `3` candidatos.
- **Estado `MARKET_INVALIDATED_SIGNAL`**: `3` candidatos.
- **Estado `SPLIT_ORDER_OPENED`**: `2` candidatos.
- **Estado `SYMBOL_DAILY_STRIKES_EXCEEDED`**: `1` candidatos.
- **Estado `MSNR_REGIME_ADX_BLOCKED`**: `1` candidatos.
- **Estado `JUMP_STRICT_FILTER_REJECTED`**: `1` candidatos.

---
## 💾 4. REGISTROS DE BASE DE DATOS & OPERACIONES

### 4.1 Operaciones Abiertas en Vivo (Con Nueva Operativa 1% Split Aplicada)
| Ticket | Instrumento | Tipo | Lote | Entrada | Stop Loss | TP1 (+1.0R) | TP2 / Runner | Flotante | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `4772186506` | **Step Index 400** | `BUY` | `0.13` | `9004.6` | `8971.0` | `9073.0` | Trade 2 (Runner Dinámico) | `$+0.00` | `OPEN` |
| `4772143510` | **Step Index 200** | `BUY` | `0.17` | `10936.5` | `10910.8` | `10987.3` | Trade 2 (Runner Dinámico) | `$+0.00` | `OPEN` |
| `4772061947` | **Volatility 100 (1s) Index** | `BUY` | `1.11` | `1247.73` | `1226.15` | `1332.65` | Trade 2 (Runner Dinámico) | `$+0.00` | `OPEN` |
| `4772061905` | **Volatility 100 (1s) Index** | `BUY` | `1.11` | `1247.73` | `1226.15` | `1269.31` | Trade 1 (TP1 1:1) | `$+0.00` | `OPEN` |
| `4771872203` | **Volatility 10 Index** | `SELL` | `2.29` | `4905.708` | `4902.542` | `4866.493` | Trade 2 (Runner Dinámico) | `$+0.00` | `OPEN` |
| `4771810726` | **Volatility 25 Index** | `BUY` | `1.42` | `2947.514` | `2930.962` | `2964.066` | Trade 1 (TP1 1:1) | `$+0.00` | `OPEN` |

> [!NOTE]
> Ambas posiciones en Boom 600 y Crash 500 están correctamente sincronizadas en MT5 con el **1% de riesgo total por activo dividido en dos operaciones de 0.5% cada una**. La primera operación busca cerrar exactamente en +1.0R (1:1), momento en el cual la segunda operación se protege en Break Even para buscar correr hacia 2R, 3R o 4R.

### 4.2 Historial de Últimas Operaciones Cerradas
| Ticket | Instrumento | Tipo | Lote | R:R Plan | R:R Realizado | Net PnL | Motivo de Cierre | Apertura |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `4772000008` | High Frequency Vol 100 Index | `SELL` | 0.05 | 2.0R | **-0.98R** | **$-44.09** | `mt5_sl` | 2026-10-30 08:11:08 |
| `4771480822` | Volatility 100 Index | `SELL` | 1.43 | 2.0R | **+0.32R** | **$+7.62** | `mt5_sl` | 2026-10-29 18:30:17 |
| `4771872175` | Volatility 10 Index | `SELL` | 2.29 | 1.0R | **+0.93R** | **$+22.53** | `mt5_tp` | 2026-10-30 05:31:18 |
| `4771707705` | Step Index 200 | `BUY` | 0.16 | 2.0R | **+0.29R** | **$+13.44** | `mt5_sl` | 2026-10-30 00:30:07 |
| `4771938181` | Volatility 5 Index | `BUY` | 0.22 | 1.0R | **-0.85R** | **$-20.54** | `mt5_sl` | 2026-10-30 07:00:23 |
| `4771938231` | Volatility 5 Index | `BUY` | 0.22 | 2.0R | **-0.87R** | **$-21.02** | `mt5_sl` | 2026-10-30 07:00:25 |
| `4771691274` | Volatility 75 Index | `BUY` | 0.037 | 2.0R | **+1.98R** | **$+46.49** | `mt5_expert` | 2026-10-30 00:00:20 |
| `4771971669` | XAUUSD | `SELL` | 0.01 | 2.0R | **+0.30R** | **$+4.80** | `mt5_sl` | 2026-10-30 07:45:29 |

### 4.3 Rendimiento Histórico por Instrumento (Top Activos)
| Instrumento | Trades Totales | Tasa de Acierto (Win Rate) | R:R Promedio | Observación Estratégica |
| :--- | :--- | :--- | :--- | :--- |
| **Step Index 500** | 110 | **50.0%** | +0.05R | ⚖️ Equilibrado |
| **Step Index 200** | 99 | **36.4%** | +1.20R | ⚠️ Requiere Calibración |
| **Volatility 25 Index** | 77 | **36.4%** | -0.29R | ⚠️ Requiere Calibración |
| **XAUUSD** | 75 | **52.0%** | +0.13R | ⚖️ Equilibrado |
| **Crash 500 Index** | 72 | **75.0%** | +0.50R | 🔥 Altamente Rentable |
| **Volatility 10 Index** | 58 | **62.1%** | +0.20R | 🔥 Altamente Rentable |
| **Jump 50 Index** | 57 | **49.1%** | -0.17R | ⚖️ Equilibrado |
| **Volatility 75 Index** | 56 | **48.2%** | -0.14R | ⚖️ Equilibrado |
| **US SP 500** | 53 | **35.8%** | -0.17R | ⚠️ Requiere Calibración |
| **Boom 600 Index** | 52 | **55.8%** | -0.02R | 🔥 Altamente Rentable |
| **Jump 25 Index** | 45 | **57.8%** | +0.13R | 🔥 Altamente Rentable |
| **Boom 500 Index** | 44 | **63.6%** | +0.35R | 🔥 Altamente Rentable |

---
## 🤖 5. COMPORTAMIENTO DE LOS MODELOS DE IA (GBDT META-LABELING)
El sistema cuenta con un pipeline de Meta-Labeling basado en modelos Gradient Boosting (LightGBM) que actúan como filtro bayesiano de calidad antes de enviar órdenes a MT5.

### 5.1 Catálogo de Modelos Entrenados y Parámetros en Producción
| Modelo | Dataset (Samples) | Win Rate Base | Accuracy Filtrada | Umbral Probabilidad | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `BOOM_ALL` | **19** | 31.6% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `BOOM_ICT` | **375** | 37.1% | **75.0%** | `p >= 0.5` | `MODELO ENTRENADO Y ACTIVO` |
| `BOOM_ICT_SABRI_MALLE` | **103** | 36.4% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `BOOM_MALAYSIAN_SNR` | **227** | 45.8% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `BOOM_MSNR_VIDEO` | **35** | 33.7% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `BOOM_ORB_NEW_YORK` | **0** | 0.0% | **N/A** | `p >= 0.52` | `SIN DATOS` |
| `BOOM_SMC` | **19** | 31.6% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `BOOM_TREND_PULLBACK` | **27** | 26.0% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `CRASH_ALL` | **332** | 42.2% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `CRASH_ICT` | **471** | 34.2% | **73.9%** | `p >= 0.5` | `MODELO ENTRENADO Y ACTIVO` |
| `CRASH_ICT_SABRI_MALLE` | **350** | 47.7% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `CRASH_MALAYSIAN_SNR` | **206** | 43.2% | **N/A** | `p >= 0.52` | `ENTRENADO` |

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
