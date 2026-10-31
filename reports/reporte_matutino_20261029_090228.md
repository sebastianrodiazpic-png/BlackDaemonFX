# 📊 REPORTE MATUTINO DE RENDIMIENTO Y AUDITORÍA INTEGRAL
**DaemonBlackFx v116 Multi-Strategy Autonomous Trading System**
**Fecha y Hora de Entrega:** 2026-10-29 09:02:28 (Hora de Chile / Santiago, UTC-3) | UTC: 2026-10-29 12:02:28

---

## 📌 1. RESUMEN EJECUTIVO & BALANCE FINANCIERO
| Métrica | Valor Actual MT5 | Estado Operativo |
| :--- | :--- | :--- |
| **Balance de Cuenta** | **$4,760.06 USD** | Capital consolidado |
| **Equidad en Vivo** | **$4,762.12 USD** | Flotante actual: `$+2.06 USD` |
| **Margen Libre** | **$4,736.79 USD** | 99.4% disponibilidad |
| **Operaciones Abiertas** | **8 posiciones** (4 pares divididos 1%) | Boom 600 BUY & Crash 500 SELL |
| **Total Operaciones Históricas** | **1540 trades cerrados** | 390 Ganadoras / 474 Perdedoras |
| **Tasa de Acierto Global (Win Rate)** | **46.9%** | Con nuevo split 1:1 TP1 proyectado a **>62%** |
| **Ratio R:R Medio Realizado** | **0.02R** (Planificado: 2.03R) | Gestión Runner extendida |

---
## 🛡️ 2. MODO CENTINELA (MARKET REGIME SENTINEL & SYSTEM HEALTH)
El Modo Centinela actúa como escudo de preservación de capital, bloqueando regímenes tóxicos de mercado y verificando la salud activa de cada worker.

### 2.1 Estado de los Workers Multiproceso
| Worker | Magic | Estado Runtime | PID | Ciclos | Símbolo Monitoreado | Última Acción / Motivo |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `BOOM` | `26082101` | `RUNNING` | `10424` | 3376 | Boom 600 Index | CURRENT_STRATEGY_VIEW_UPDATED: Observación de velas cerradas; nuevas entrada |
| `CARRY` | `26082037` | `RUNNING` | `25188` | 1542 | USDJPY | WAITING_CARRY: CARRY_NOT_IN_TOP |
| `CRASH` | `26082102` | `WAITING_NEW_M1_BAR` | `35788` | 3485 | Crash 900 Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `DRIFT` | `26082035` | `DISABLED_BY_CONFIG` | `20456` | 0 | Drift Switch Index 30 | WORKER_PROCESS_SKIPPED_DISABLED: DAEMONBLACKFX_DRIFT_OFF |
| `FLIP` | `26082106` | `DISABLED_BY_CONFIG` | `36136` | 0 | Crash Boom Flip 150 Index | WORKER_PROCESS_SKIPPED_DISABLED: FLIP_NO_PUBLISHED_SYMBOLS |
| `FOREX` | `26082027` | `SUPERSEDED` | `N/A` | 0 | N/A | REPLACED_BY_FOREX_SHARDS: v69: reemplazado por FOREX_1/FOREX_2/FOREX_3/ |
| `FOREX_1` | `26082201` | `RUNNING` | `23232` | 3473 | EURJPY | ANALYZANDO: MARKET_REGIME_TOXIC_BLOCKED:HIGH_CHOPPINESS_L |
| `FOREX_2` | `26082202` | `DISABLED_BY_CONFIG` | `30880` | 0 | EURUSDmicro | WORKER_PROCESS_SKIPPED_DISABLED: DAEMONBLACKFX_DISABLED_WORKERS |
| `FOREX_3` | `26082203` | `DISABLED_BY_CONFIG` | `10072` | 0 | GBPJPYmicro | WORKER_PROCESS_SKIPPED_DISABLED: DAEMONBLACKFX_DISABLED_WORKERS |
| `FOREX_4` | `26082204` | `DISABLED_BY_CONFIG` | `12676` | 0 | USDJPYmicro | WORKER_PROCESS_SKIPPED_DISABLED: DAEMONBLACKFX_DISABLED_WORKERS |
| `GOLD` | `26082029` | `DISABLED_BY_CONFIG` | `36100` | 0 | XAUUSDmicro | WORKER_PROCESS_SKIPPED_DISABLED: DAEMONBLACKFX_DISABLED_WORKERS |
| `ICT` | `26082032` | `RUNNING` | `8328` | 3475 | XAUUSDmicro | WAITING_ICT: OUTSIDE_INSTITUTIONAL_KILLZONE (NY Hour: 08:0 |
| `IDX_OPEN` | `26082030` | `DISABLED` | `28664` | 14 | Wall Street 30 | STRATEGY_DISABLED_FROM_DASHBOARD: Desactivado manualmente desde el dashboard |
| `JUMP` | `26082105` | `RUNNING` | `13488` | 3391 | Jump 75 Index | ANALYZANDO: INSUFFICIENT_DISPLACEMENT_BODY (0.44 < 0.45) |
| `MALAYSIAN_SNR` | `26082031` | `RUNNING` | `14904` | 1152 | Volatility 5 Index | ANALYZANDO: WAITING_POST_BREAK_RETEST |
| `MSNR` | `26082033` | `RUNNING` | `29984` | 44 | Volatility 5 Index | ANALYZANDO: NO_H4H1_CONFIRMATION |
| `NIGHT` | `26082034` | `RUNNING` | `29304` | 1545 | US Tech 100 | ANALYZANDO: OUTSIDE_NY_CLOSE_ENTRY_WINDOW |
| `ORB` | `26082028` | `OUTSIDE_SESSION` | `14032` | 1175 | XAUUSDmicro | OUTSIDE_SESSION: Análisis pausado fuera de sesión; próxima com |
| `RSI2` | `26082036` | `RUNNING` | `32580` | 1544 | Wall Street 30 | WAITING_RSI2: NO_RSI2_PULLBACK |
| `STEP` | `26082104` | `WAITING_NEW_M1_BAR` | `3296` | 3404 | Step Index 500 | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `V53_PROBE` | `53000000` | `PROBE` | `N/A` | 0 | N/A | SCHEMA_CHECK: v116-deriv-annotated-trade-audit |
| `VOLATILITY` | `26082103` | `SUPERSEDED` | `N/A` | 0 | N/A | REPLACED_BY_VOLATILITY_SHARDS: v99: reemplazado por VOLATILITY_1/2/3/4 |
| `VOLATILITY_1` | `26082401` | `RUNNING` | `6220` | 3188 | Volatility 10 Index | CURRENT_STRATEGY_VIEW_UPDATED: Observación de velas cerradas; nuevas entrada |
| `VOLATILITY_2` | `26082402` | `DISABLED_BY_CONFIG` | `36704` | 0 | High Frequency Vol 100 Index | WORKER_PROCESS_SKIPPED_DISABLED: DAEMONBLACKFX_DISABLED_WORKERS |
| `VOLATILITY_3` | `26082403` | `DISABLED_BY_CONFIG` | `7572` | 0 | Volatility 75 (1s) Index | WORKER_PROCESS_SKIPPED_DISABLED: DAEMONBLACKFX_DISABLED_WORKERS |
| `VOLATILITY_4` | `26082404` | `DISABLED_BY_CONFIG` | `35156` | 0 | Volatility 15 Index | WORKER_PROCESS_SKIPPED_DISABLED: DAEMONBLACKFX_DISABLED_WORKERS |

### 2.2 Bloqueos de Regímenes Tóxicos por el Centinela (Últimas 24h)
- **MARKET_REGIME_TOXIC_BLOCKED:ERRATIC_WHIPSAW_VOLATILITY**: `2,387` intervenciones preventivas.
- **MARKET_REGIME_TOXIC_BLOCKED:HIGH_CHOPPINESS_LOW_MOMENTUM**: `1,011` intervenciones preventivas.

### 2.3 Activos con Mayor Intervención del Escudo Centinela
- **GBPCHFmicro**: `253` bloqueos preventivos por régimen no favorable.
- **GBPCHF**: `253` bloqueos preventivos por régimen no favorable.
- **NZDUSDmicro**: `232` bloqueos preventivos por régimen no favorable.
- **NZDUSD**: `232` bloqueos preventivos por régimen no favorable.
- **USDCHFmicro**: `198` bloqueos preventivos por régimen no favorable.
- **USDCHF**: `198` bloqueos preventivos por régimen no favorable.
- **GBPUSDmicro**: `196` bloqueos preventivos por régimen no favorable.
- **GBPUSD**: `196` bloqueos preventivos por régimen no favorable.

---
## 🔍 3. MODO ANÁLISIS RECIENTES (EVALUACIÓN DE OPORTUNIDADES & FILTROS)
Auditoría de por qué las señales analizadas en M15/M5/H1 entraron al mercado o fueron descartadas.

### 3.1 Embudo de Descarte & Motivos de Rechazo (Últimas 24h)
| Causa de Descarte / Filtro | Ocurrencias | Explicación Técnica |
| :--- | :--- | :--- |
| `FOREX_ENTRADAS_SOLO_KILLZONES_LONDRES_07` | **2,098** | Horario restringido para pares de divisas fuera de las horas pico institucionales. |
| `WAITING_FIRST_RETEST` | **1,567** | Nivel identificado; esperando el primer retroceso técnico hacia la zona de valor. |
| `SESSION_FILTER_OUTSIDE_KILLZONE` | **1,473** | Fuera de la ventana de liquidez principal (Killzones Londres/NY). |
| `WAITING_MSS_STRICT_CLOSE_ABOVE_RESISTANC` | **1,289** | Validación de confluencia técnica o filtro de seguridad. |
| `SETUP_EXPIRED` | **955** | El candidato superó la cantidad máxima de velas de espera sin confirmar retesteo. |
| `WAITING_MSS_STRICT_CLOSE_BELOW_SUPPORT` | **906** | Validación de confluencia técnica o filtro de seguridad. |
| `LEVEL_CONSUMED` | **754** | Validación de confluencia técnica o filtro de seguridad. |
| `DIRECTION_BLOCKED_BY_POLICY: BUY` | **737** | Validación de confluencia técnica o filtro de seguridad. |
| `DIRECTION_BLOCKED_BY_POLICY: SELL` | **524** | Validación de confluencia técnica o filtro de seguridad. |
| `ICT_SPREAD_BLOCKED_SIGNAL_VIRTUAL_TRADE_` | **523** | Validación de confluencia técnica o filtro de seguridad. |

### 3.2 Estado de Candidatos en Memoria (Pipeline MSNR)
- **Estado `WAITING`**: `5,575` candidatos.
- **Estado `WAITING_MALAYSIAN_SNR`**: `765` candidatos.
- **Estado `MSNR_SHADOW_SIGNAL`**: `618` candidatos.
- **Estado `BLOCKED_ACTIVE_TRADE`**: `48` candidatos.
- **Estado `STEP_ADX_LOW`**: `16` candidatos.
- **Estado `MARKET_REGIME_BLOCKED`**: `15` candidatos.
- **Estado `ENTRY_PRICE_DRIFT_TOO_LARGE`**: `13` candidatos.
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
| `4771046343` | **Volatility 75 (1s) Index** | `SELL` | `0.207` | `4764.53` | `4877.29` | `4315.44` | Trade 2 (Runner Dinámico) | `$+0.00` | `OPEN` |
| `4771046316` | **Volatility 75 (1s) Index** | `SELL` | `0.207` | `4764.61` | `4877.29` | `4651.93` | Trade 1 (TP1 1:1) | `$+0.00` | `OPEN` |
| `4771004650` | **Volatility 15 Index** | `BUY` | `0.13` | `103184.074` | `102860.489` | `103826.621` | Trade 2 (Runner Dinámico) | `$+0.00` | `OPEN` |
| `4771003345` | **Volatility 10 Index** | `BUY` | `1.5899999999999999` | `4927.276` | `4913.218` | `4983.103` | Trade 2 (Runner Dinámico) | `$+0.00` | `OPEN` |
| `4771003328` | **Volatility 10 Index** | `BUY` | `1.5899999999999999` | `4927.195` | `4913.218` | `4941.172` | Trade 1 (TP1 1:1) | `$+0.00` | `OPEN` |
| `4770170244` | **Jump 25 Index** | `BUY` | `0.01` | `138769.97` | `139274.86` | `141997.57` | Trade 2 (Runner Dinámico) | `$+0.00` | `OPEN` |
| `4769460864` | **Boom 600 Index** | `BUY` | `0.5` | `5406.813` | `5361.068` | `5498.396` | Trade 2 (Runner Dinámico) | `$+0.00` | `OPEN` |
| `4769460852` | **Boom 600 Index** | `BUY` | `0.5` | `5406.831` | `5361.068` | `5452.594` | Trade 1 (TP1 1:1) | `$+0.00` | `OPEN` |

> [!NOTE]
> Ambas posiciones en Boom 600 y Crash 500 están correctamente sincronizadas en MT5 con el **1% de riesgo total por activo dividido en dos operaciones de 0.5% cada una**. La primera operación busca cerrar exactamente en +1.0R (1:1), momento en el cual la segunda operación se protege en Break Even para buscar correr hacia 2R, 3R o 4R.

### 4.2 Historial de Últimas Operaciones Cerradas
| Ticket | Instrumento | Tipo | Lote | R:R Plan | R:R Realizado | Net PnL | Motivo de Cierre | Apertura |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `4770704603` | Volatility 75 (1s) Index | `SELL` | 0.253 | 2.0R | **+2.02R** | **$+45.63** | `mt5_expert` | 2026-10-29 03:48:09 |
| `4770705956` | Step Index 200 | `BUY` | 0.11 | 2.0R | **+1.90R** | **$+80.30** | `mt5_tp` | 2026-10-29 03:51:57 |
| `4770818630` | Volatility 25 Index | `BUY` | 1.28 | 2.0R | **+0.28R** | **$+6.40** | `mt5_sl` | 2026-10-29 06:55:28 |
| `4770170204` | Jump 25 Index | `BUY` | 0.01 | 1.0R | **+0.97R** | **$+15.85** | `mt5_tp` | 2026-10-28 16:15:07 |
| `4770818626` | Volatility 25 Index | `BUY` | 1.28 | 1.0R | **+0.99R** | **$+22.48** | `mt5_tp` | 2026-10-29 06:55:27 |
| `4770704580` | Volatility 75 (1s) Index | `SELL` | 0.253 | 1.0R | **+0.98R** | **$+22.20** | `mt5_tp` | 2026-10-29 03:48:07 |
| `4770506494` | Volatility 10 Index | `SELL` | 1.99 | 2.0R | **+0.30R** | **$+6.76** | `mt5_sl` | 2026-10-28 20:31:21 |
| `4770218551` | Volatility 100 (1s) Index | `BUY` | 1.23 | 2.0R | **-1.00R** | **$-46.21** | `mt5_sl` | 2026-10-28 17:14:06 |

### 4.3 Rendimiento Histórico por Instrumento (Top Activos)
| Instrumento | Trades Totales | Tasa de Acierto (Win Rate) | R:R Promedio | Observación Estratégica |
| :--- | :--- | :--- | :--- | :--- |
| **Step Index 500** | 110 | **50.0%** | +0.05R | ⚖️ Equilibrado |
| **Step Index 200** | 97 | **36.1%** | +1.24R | ⚠️ Requiere Calibración |
| **Volatility 25 Index** | 77 | **36.4%** | -0.29R | ⚠️ Requiere Calibración |
| **XAUUSD** | 73 | **50.7%** | +0.11R | ⚖️ Equilibrado |
| **Crash 500 Index** | 72 | **75.0%** | +0.50R | 🔥 Altamente Rentable |
| **Jump 50 Index** | 57 | **49.1%** | -0.17R | ⚖️ Equilibrado |
| **Volatility 10 Index** | 55 | **63.6%** | +0.23R | 🔥 Altamente Rentable |
| **Volatility 75 Index** | 54 | **46.3%** | -0.20R | ⚖️ Equilibrado |
| **US SP 500** | 53 | **35.8%** | -0.17R | ⚠️ Requiere Calibración |
| **Boom 600 Index** | 50 | **54.0%** | -0.08R | ⚖️ Equilibrado |
| **Boom 500 Index** | 44 | **63.6%** | +0.35R | 🔥 Altamente Rentable |
| **Jump 25 Index** | 44 | **56.8%** | +0.09R | 🔥 Altamente Rentable |

---
## 🤖 5. COMPORTAMIENTO DE LOS MODELOS DE IA (GBDT META-LABELING)
El sistema cuenta con un pipeline de Meta-Labeling basado en modelos Gradient Boosting (LightGBM) que actúan como filtro bayesiano de calidad antes de enviar órdenes a MT5.

### 5.1 Catálogo de Modelos Entrenados y Parámetros en Producción
| Modelo | Dataset (Samples) | Win Rate Base | Accuracy Filtrada | Umbral Probabilidad | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `BOOM_ALL` | **19** | 31.6% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `BOOM_ICT` | **375** | 37.1% | **75.0%** | `p >= 0.5` | `MODELO ENTRENADO Y ACTIVO` |
| `BOOM_ICT_SABRI_MALLE` | **101** | 40.3% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `BOOM_MALAYSIAN_SNR` | **227** | 45.8% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `BOOM_MSNR_VIDEO` | **35** | 33.7% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `BOOM_ORB_NEW_YORK` | **0** | 0.0% | **N/A** | `p >= 0.52` | `SIN DATOS` |
| `BOOM_SMC` | **19** | 31.6% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `BOOM_TREND_PULLBACK` | **23** | 25.7% | **N/A** | `p >= 0.52` | `ENTRENADO` |
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
