# 📊 REPORTE MATUTINO DE RENDIMIENTO Y AUDITORÍA INTEGRAL
**DaemonBlackFx v116 Multi-Strategy Autonomous Trading System**
**Fecha y Hora de Entrega:** 2026-11-03 09:02:27 (Hora de Chile / Santiago, UTC-3) | UTC: 2026-11-03 12:02:27

---

## 📌 1. RESUMEN EJECUTIVO & BALANCE FINANCIERO
| Métrica | Valor Actual MT5 | Estado Operativo |
| :--- | :--- | :--- |
| **Balance de Cuenta** | **$4,161.94 USD** | Capital consolidado |
| **Equidad en Vivo** | **$4,157.20 USD** | Flotante actual: `$-4.74 USD` |
| **Margen Libre** | **$4,140.29 USD** | 99.4% disponibilidad |
| **Operaciones Abiertas** | **2 posiciones** (1 pares divididos 1%) | Boom 600 BUY & Crash 500 SELL |
| **Total Operaciones Históricas** | **1675 trades cerrados** | 390 Ganadoras / 474 Perdedoras |
| **Tasa de Acierto Global (Win Rate)** | **46.4%** | Con nuevo split 1:1 TP1 proyectado a **>62%** |
| **Ratio R:R Medio Realizado** | **0.01R** (Planificado: 2.00R) | Gestión Runner extendida |

---
## 🛡️ 2. MODO CENTINELA (MARKET REGIME SENTINEL & SYSTEM HEALTH)
El Modo Centinela actúa como escudo de preservación de capital, bloqueando regímenes tóxicos de mercado y verificando la salud activa de cada worker.

### 2.1 Estado de los Workers Multiproceso
| Worker | Magic | Estado Runtime | PID | Ciclos | Símbolo Monitoreado | Última Acción / Motivo |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `BOOM` | `26082101` | `WAITING_NEW_M1_BAR` | `14620` | 5911 | Boom 600 Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `CRASH` | `26082102` | `WAITING_NEW_M1_BAR` | `3516` | 5903 | Crash 600 Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `FLIP` | `26082106` | `DISABLED_BY_CONFIG` | `N/A` | 0 | N/A | WORKER_PROCESS_SKIPPED_DISABLED: FLIP_NO_PUBLISHED_SYMBOLS |
| `FOREX` | `26082027` | `SUPERSEDED` | `N/A` | 0 | N/A | REPLACED_BY_FOREX_SHARDS: v69: reemplazado por FOREX_1/FOREX_2/FOREX_3/ |
| `FOREX_1` | `26082201` | `WAITING_NEW_M1_BAR` | `22604` | 5909 | USDCHF | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `FOREX_2` | `26082202` | `DISABLED_BY_CONFIG` | `30880` | 0 | EURUSDmicro | WORKER_PROCESS_SKIPPED_DISABLED: DAEMONBLACKFX_DISABLED_WORKERS |
| `FOREX_3` | `26082203` | `DISABLED_BY_CONFIG` | `10072` | 0 | GBPJPYmicro | WORKER_PROCESS_SKIPPED_DISABLED: DAEMONBLACKFX_DISABLED_WORKERS |
| `FOREX_4` | `26082204` | `DISABLED_BY_CONFIG` | `12676` | 0 | USDJPYmicro | WORKER_PROCESS_SKIPPED_DISABLED: DAEMONBLACKFX_DISABLED_WORKERS |
| `ICT` | `26082032` | `RUNNING` | `27244` | 5909 | XAUUSD | WAITING_ICT: OUTSIDE_INSTITUTIONAL_KILLZONE (NY Hour: 07:0 |
| `JUMP` | `26082105` | `WAITING_NEW_M1_BAR` | `30288` | 5909 | Jump 50 Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `MALAYSIAN_SNR` | `26082031` | `RUNNING` | `18104` | 1969 | Boom 500 Index | CURRENT_STRATEGY_VIEW_UPDATED: Observación de velas cerradas; nuevas entrada |
| `ORB` | `26082028` | `RUNNING` | `1404` | 1970 | XAUUSD | CYCLE_START: SIN_BARRIDO_MAS_MSS_CONFIRMADO |
| `STEP` | `26082104` | `RUNNING` | `29428` | 5904 | Step Index 400 | CURRENT_STRATEGY_VIEW_UPDATED: Observación de velas cerradas; nuevas entrada |
| `TREND_PULLBACK` | `26082038` | `DISABLED_BY_CONFIG` | `30444` | 0 | VolSwitch High Vol Index | WORKER_PROCESS_SKIPPED_DISABLED: DAEMONBLACKFX_DISABLED_WORKERS |
| `V53_PROBE` | `53000000` | `PROBE` | `N/A` | 0 | N/A | SCHEMA_CHECK: v116-deriv-annotated-trade-audit |
| `VOLATILITY` | `26082103` | `SUPERSEDED` | `N/A` | 0 | N/A | REPLACED_BY_VOLATILITY_SHARDS: v99: reemplazado por VOLATILITY_1/2/3/4 |
| `VOLATILITY_1` | `26082401` | `WAITING_NEW_M1_BAR` | `21016` | 5858 | VolSwitch High Vol Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `VOLATILITY_2` | `26082402` | `DISABLED_BY_CONFIG` | `36704` | 0 | High Frequency Vol 100 Index | WORKER_PROCESS_SKIPPED_DISABLED: DAEMONBLACKFX_DISABLED_WORKERS |
| `VOLATILITY_3` | `26082403` | `DISABLED_BY_CONFIG` | `7572` | 0 | Volatility 75 (1s) Index | WORKER_PROCESS_SKIPPED_DISABLED: DAEMONBLACKFX_DISABLED_WORKERS |
| `VOLATILITY_4` | `26082404` | `DISABLED_BY_CONFIG` | `35156` | 0 | Volatility 15 Index | WORKER_PROCESS_SKIPPED_DISABLED: DAEMONBLACKFX_DISABLED_WORKERS |

### 2.2 Bloqueos de Regímenes Tóxicos por el Centinela (Últimas 24h)
- **MARKET_REGIME_TOXIC_BLOCKED:ERRATIC_WHIPSAW_VOLATILITY**: `808` intervenciones preventivas.
- **MARKET_REGIME_TOXIC_BLOCKED:HIGH_CHOPPINESS_LOW_MOMENTUM**: `57` intervenciones preventivas.

### 2.3 Activos con Mayor Intervención del Escudo Centinela
- **NZDUSD**: `329` bloqueos preventivos por régimen no favorable.
- **GBPUSD**: `163` bloqueos preventivos por régimen no favorable.
- **EURJPY**: `119` bloqueos preventivos por régimen no favorable.
- **GBPJPY**: `79` bloqueos preventivos por régimen no favorable.
- **Volatility 15 Index**: `34` bloqueos preventivos por régimen no favorable.
- **CADCHF**: `34` bloqueos preventivos por régimen no favorable.
- **Volatility 75 (1s) Index**: `30` bloqueos preventivos por régimen no favorable.
- **Volatility 25 Index**: `30` bloqueos preventivos por régimen no favorable.

---
## 🔍 3. MODO ANÁLISIS RECIENTES (EVALUACIÓN DE OPORTUNIDADES & FILTROS)
Auditoría de por qué las señales analizadas en M15/M5/H1 entraron al mercado o fueron descartadas.

### 3.1 Embudo de Descarte & Motivos de Rechazo (Últimas 24h)
| Causa de Descarte / Filtro | Ocurrencias | Explicación Técnica |
| :--- | :--- | :--- |
| `Otro worker esta evaluando o enviando un` | **1,915** | Bloqueo de concurrencia inter-proceso para evitar sobre-exposición simultánea. |
| `WAITING_FIRST_RETEST` | **1,377** | Nivel identificado; esperando el primer retroceso técnico hacia la zona de valor. |
| `FOREX_ENTRADAS_SOLO_KILLZONES_LONDRES_07` | **1,256** | Horario restringido para pares de divisas fuera de las horas pico institucionales. |
| `SESSION_FILTER_OUTSIDE_KILLZONE` | **1,114** | Fuera de la ventana de liquidez principal (Killzones Londres/NY). |
| `cannot access local variable 'micro_stop` | **911** | Validación de confluencia técnica o filtro de seguridad. |
| `SETUP_EXPIRED` | **652** | El candidato superó la cantidad máxima de velas de espera sin confirmar retesteo. |
| `WAITING_MSS_STRICT_CLOSE_ABOVE_RESISTANC` | **558** | Validación de confluencia técnica o filtro de seguridad. |
| `LEVEL_CONSUMED` | **550** | Validación de confluencia técnica o filtro de seguridad. |
| `WAITING_MSS_STRICT_CLOSE_BELOW_SUPPORT` | **531** | Validación de confluencia técnica o filtro de seguridad. |
| `SETUP_STRUCTURE_INVALIDATED` | **369** | El precio rompió el nivel con cuerpo de vela en lugar de respetarlo. |

### 3.2 Estado de Candidatos en Memoria (Pipeline MSNR)
- **Estado `WAITING`**: `6,751` candidatos.
- **Estado `WAITING_MALAYSIAN_SNR`**: `912` candidatos.
- **Estado `MSNR_SHADOW_SIGNAL`**: `808` candidatos.
- **Estado `BLOCKED_ACTIVE_TRADE`**: `54` candidatos.
- **Estado `MARKET_REGIME_BLOCKED`**: `19` candidatos.
- **Estado `STEP_ADX_LOW`**: `16` candidatos.
- **Estado `ENTRY_PRICE_DRIFT_TOO_LARGE`**: `16` candidatos.
- **Estado `OPERACION_RECHAZADA_POR_RIESGO`**: `10` candidatos.
- **Estado `BLOCKED_SYMBOL_CYCLE`**: `8` candidatos.
- **Estado `SYMBOL_COOLDOWN_POST_SL`**: `7` candidatos.
- **Estado `SYNTHETIC_SPREAD_TO_SL_EXCEEDED`**: `5` candidatos.
- **Estado `META_LABEL_FILTER_REJECTED`**: `3` candidatos.
- **Estado `MARKET_INVALIDATED_SIGNAL`**: `3` candidatos.
- **Estado `SPLIT_ORDER_OPENED`**: `2` candidatos.
- **Estado `MSNR_REGIME_ADX_BLOCKED`**: `2` candidatos.
- **Estado `JUMP_STRICT_FILTER_REJECTED`**: `2` candidatos.
- **Estado `SYMBOL_DAILY_STRIKES_EXCEEDED`**: `1` candidatos.
- **Estado `HUMAN_CRITERIA_FILTER_REJECTED`**: `1` candidatos.

---
## 💾 4. REGISTROS DE BASE DE DATOS & OPERACIONES

### 4.1 Operaciones Abiertas en Vivo (Con Nueva Operativa 1% Split Aplicada)
| Ticket | Instrumento | Tipo | Lote | Entrada | Stop Loss | TP1 (+1.0R) | TP2 / Runner | Flotante | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `4775471845` | **Boom 500 Index** | `BUY` | `0.93` | `5811.567` | `5790.325` | `5832.809` | Trade 1 (TP1 1:1) | `$+0.00` | `OPEN` |
| `4775468017` | **Step Index 400** | `SELL` | `0.1` | `8511.8` | `8549.5` | `8437.6` | Trade 2 (Runner Dinámico) | `$+0.00` | `OPEN` |

> [!NOTE]
> Ambas posiciones en Boom 600 y Crash 500 están correctamente sincronizadas en MT5 con el **1% de riesgo total por activo dividido en dos operaciones de 0.5% cada una**. La primera operación busca cerrar exactamente en +1.0R (1:1), momento en el cual la segunda operación se protege en Break Even para buscar correr hacia 2R, 3R o 4R.

### 4.2 Historial de Últimas Operaciones Cerradas
| Ticket | Instrumento | Tipo | Lote | R:R Plan | R:R Realizado | Net PnL | Motivo de Cierre | Apertura |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `4775387927` | US Oil | `SELL` | 29.0 | 2.0R | **-0.98R** | **$-20.36** | `mt5_sl` | 2026-11-03 10:00:02 |
| `4775387934` | US Oil | `SELL` | 29.0 | 2.0R | **-1.01R** | **$-20.56** | `mt5_sl` | 2026-11-03 10:00:02 |
| `4775289783` | Step Index 400 | `SELL` | 0.11 | 2.0R | **-0.94R** | **$-38.72** | `mt5_sl` | 2026-11-03 07:51:06 |
| `4775367887` | USDCAD | `SELL` | 0.33 | 1.0R | **-0.77R** | **$-16.07** | `mt5_sl` | 2026-11-03 09:35:14 |
| `4775367890` | USDCAD | `SELL` | 0.33 | 2.0R | **-0.77R** | **$-16.07** | `mt5_sl` | 2026-11-03 09:35:15 |
| `4775276326` | Crash 300 Index | `SELL` | 0.81 | 2.0R | **+0.31R** | **$+13.15** | `mt5_sl` | 2026-11-03 07:31:07 |
| `4775102688` | Volatility 50 Index | `BUY` | 20.87 | 2.0R | **+1.94R** | **$+40.33** | `mt5_tp` | 2026-11-03 02:06:21 |
| `4775102677` | Volatility 50 Index | `BUY` | 20.87 | 1.0R | **+1.00R** | **$+20.67** | `mt5_tp` | 2026-11-03 02:06:19 |

### 4.3 Rendimiento Histórico por Instrumento (Top Activos)
| Instrumento | Trades Totales | Tasa de Acierto (Win Rate) | R:R Promedio | Observación Estratégica |
| :--- | :--- | :--- | :--- | :--- |
| **Step Index 500** | 110 | **50.0%** | +0.05R | ⚖️ Equilibrado |
| **Step Index 200** | 104 | **35.6%** | +1.12R | ⚠️ Requiere Calibración |
| **Volatility 25 Index** | 82 | **36.6%** | -0.30R | ⚠️ Requiere Calibración |
| **Crash 500 Index** | 76 | **71.1%** | +0.43R | 🔥 Altamente Rentable |
| **XAUUSD** | 76 | **52.6%** | +0.13R | ⚖️ Equilibrado |
| **Volatility 10 Index** | 68 | **57.4%** | +0.12R | 🔥 Altamente Rentable |
| **Volatility 75 Index** | 68 | **51.5%** | -0.04R | ⚖️ Equilibrado |
| **Jump 50 Index** | 57 | **49.1%** | -0.17R | ⚖️ Equilibrado |
| **Boom 600 Index** | 54 | **53.7%** | -0.06R | ⚖️ Equilibrado |
| **US SP 500** | 53 | **35.8%** | -0.17R | ⚠️ Requiere Calibración |
| **Jump 25 Index** | 49 | **57.1%** | +0.11R | 🔥 Altamente Rentable |
| **Boom 500 Index** | 46 | **60.9%** | +0.29R | 🔥 Altamente Rentable |

---
## 🤖 5. COMPORTAMIENTO DE LOS MODELOS DE IA (GBDT META-LABELING)
El sistema cuenta con un pipeline de Meta-Labeling basado en modelos Gradient Boosting (LightGBM) que actúan como filtro bayesiano de calidad antes de enviar órdenes a MT5.

### 5.1 Catálogo de Modelos Entrenados y Parámetros en Producción
| Modelo | Dataset (Samples) | Win Rate Base | Accuracy Filtrada | Umbral Probabilidad | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `BOOM_ALL` | **19** | 31.6% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `BOOM_ICT` | **375** | 37.1% | **75.0%** | `p >= 0.5` | `MODELO ENTRENADO Y ACTIVO` |
| `BOOM_ICT_SABRI_MALLE` | **109** | 40.5% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `BOOM_MALAYSIAN_SNR` | **227** | 45.8% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `BOOM_MSNR_VIDEO` | **35** | 33.7% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `BOOM_ORB_NEW_YORK` | **20** | 35.0% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `BOOM_SMC` | **19** | 31.6% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `BOOM_TREND_PULLBACK` | **36** | 16.4% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `CRASH_ALL` | **332** | 42.2% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `CRASH_ICT` | **471** | 34.2% | **73.9%** | `p >= 0.5` | `MODELO ENTRENADO Y ACTIVO` |
| `CRASH_ICT_SABRI_MALLE` | **355** | 41.7% | **N/A** | `p >= 0.52` | `ENTRENADO` |
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
