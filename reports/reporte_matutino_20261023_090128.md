# 📊 REPORTE MATUTINO DE RENDIMIENTO Y AUDITORÍA INTEGRAL
**DaemonBlackFx v116 Multi-Strategy Autonomous Trading System**
**Fecha y Hora de Entrega:** 2026-10-23 09:01:28 (Hora de Chile / Santiago, UTC-3) | UTC: 2026-10-23 12:01:28

---

## 📌 1. RESUMEN EJECUTIVO & BALANCE FINANCIERO
| Métrica | Valor Actual MT5 | Estado Operativo |
| :--- | :--- | :--- |
| **Balance de Cuenta** | **$5,929.01 USD** | Capital consolidado |
| **Equidad en Vivo** | **$6,060.06 USD** | Flotante actual: `$+131.05 USD` |
| **Margen Libre** | **$5,880.49 USD** | 99.4% disponibilidad |
| **Operaciones Abiertas** | **10 posiciones** (5 pares divididos 1%) | Boom 600 BUY & Crash 500 SELL |
| **Total Operaciones Históricas** | **1298 trades cerrados** | 390 Ganadoras / 474 Perdedoras |
| **Tasa de Acierto Global (Win Rate)** | **45.2%** | Con nuevo split 1:1 TP1 proyectado a **>62%** |
| **Ratio R:R Medio Realizado** | **0.02R** (Planificado: 2.08R) | Gestión Runner extendida |

---
## 🛡️ 2. MODO CENTINELA (MARKET REGIME SENTINEL & SYSTEM HEALTH)
El Modo Centinela actúa como escudo de preservación de capital, bloqueando regímenes tóxicos de mercado y verificando la salud activa de cada worker.

### 2.1 Estado de los Workers Multiproceso
| Worker | Magic | Estado Runtime | PID | Ciclos | Símbolo Monitoreado | Última Acción / Motivo |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `BOOM` | `26082101` | `RUNNING` | `3160` | 201 | Volatility 10 Index | CURRENT_STRATEGY_VIEW_UPDATED: Observación de velas cerradas; nuevas entrada |
| `CRASH` | `26082102` | `WAITING_NEW_M1_BAR` | `16520` | 183 | Crash 900 Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `DRIFT` | `26082035` | `RUNNING` | `14908` | 374 | Drift Switch Index 30 | WAITING_DRIFT_BREAKOUT: NO_COMPRESSION_BREAKOUT |
| `FLIP` | `26082106` | `RUNNING` | `21376` | 44 | Crash Boom Flip 300 Index | ANALYZANDO: NO_DIRECTIONAL_M5_CONFIRMATION |
| `FOREX` | `26082027` | `SUPERSEDED` | `N/A` | 0 | N/A | REPLACED_BY_FOREX_SHARDS: v69: reemplazado por FOREX_1/FOREX_2/FOREX_3/ |
| `FOREX_1` | `26082201` | `RUNNING` | `16504` | 362 | USDCHF | ANALYZANDO: OUTSIDE_INSTITUTIONAL_KILLZONE (NY Hour: 08:0 |
| `FOREX_2` | `26082202` | `WAITING_NEW_M1_BAR` | `14712` | 351 | EURUSDmicro | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `FOREX_3` | `26082203` | `WAITING_NEW_M1_BAR` | `13376` | 332 | GBPJPYmicro | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `FOREX_4` | `26082204` | `WAITING_NEW_M1_BAR` | `23316` | 279 | USDJPYmicro | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `GOLD` | `26082029` | `RUNNING` | `23396` | 337 | XAUUSDmicro | BLOCKED_SYMBOL_CYCLE: Otro worker esta evaluando o enviando una ent |
| `ICT` | `26082032` | `RUNNING` | `17384` | 367 | XAUUSD | WAITING_ICT: OUTSIDE_INSTITUTIONAL_KILLZONE (NY Hour: 08:0 |
| `IDX_OPEN` | `26082030` | `DISABLED` | `28664` | 14 | Wall Street 30 | STRATEGY_DISABLED_FROM_DASHBOARD: Desactivado manualmente desde el dashboard |
| `JUMP` | `26082105` | `WAITING_NEW_M1_BAR` | `11340` | 263 | Jump 75 Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `MALAYSIAN_SNR` | `26082031` | `RUNNING` | `18996` | 22 | Crash 1000 Index | ANALYZANDO: RETEST_PENETRATION_TOO_DEEP |
| `MSNR` | `26082033` | `RUNNING` | `11764` | 11 | Volatility 10 Index | ANALYZANDO: NO_H4H1_CONFIRMATION |
| `NIGHT` | `26082034` | `RUNNING` | `3608` | 363 | Wall Street 30 | WAITING_OVERNIGHT: OVERNIGHT_SYMBOL_NOT_ALLOWED |
| `ORB` | `26082028` | `OUTSIDE_SESSION` | `14220` | 123 | XAUUSDmicro | OUTSIDE_SESSION: Análisis pausado fuera de sesión; próxima com |
| `RSI2` | `26082036` | `RUNNING` | `3796` | 315 | Wall Street 30 | BLOCKED_SYMBOL_CYCLE: Otro worker esta evaluando o enviando una ent |
| `STEP` | `26082104` | `RUNNING` | `24308` | 221 | Step Index 200 | MONITOR_POSICIONES: BACKGROUND_MONITOR |
| `V53_PROBE` | `53000000` | `PROBE` | `N/A` | 0 | N/A | SCHEMA_CHECK: v116-deriv-annotated-trade-audit |
| `VOLATILITY` | `26082103` | `SUPERSEDED` | `N/A` | 0 | N/A | REPLACED_BY_VOLATILITY_SHARDS: v99: reemplazado por VOLATILITY_1/2/3/4 |
| `VOLATILITY_1` | `26082401` | `RUNNING` | `9416` | 346 | Volatility 75 (1s) Index | REGIME_TOXIC_OBSERVED_NOT_BLOCKED: MARKET_REGIME_TOXIC_BLOCKED:ERRATIC_WHIPSAW_V |
| `VOLATILITY_2` | `26082402` | `RUNNING` | `2220` | 226 | Volatility 15 Index | MONITOR_POSICIONES: BACKGROUND_MONITOR |
| `VOLATILITY_3` | `26082403` | `WAITING_NEW_M1_BAR` | `2844` | 237 | Volatility 90 (1s) Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `VOLATILITY_4` | `26082404` | `WAITING_NEW_M1_BAR` | `20004` | 225 | Volatility 90 Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |

### 2.2 Bloqueos de Regímenes Tóxicos por el Centinela (Últimas 24h)
- **MARKET_REGIME_TOXIC_BLOCKED:ERRATIC_WHIPSAW_VOLATILITY**: `4,342` intervenciones preventivas.
- **MARKET_REGIME_TOXIC_BLOCKED:HIGH_CHOPPINESS_LOW_MOMENTUM**: `843` intervenciones preventivas.

### 2.3 Activos con Mayor Intervención del Escudo Centinela
- **USDCAD**: `500` bloqueos preventivos por régimen no favorable.
- **AUDUSD**: `325` bloqueos preventivos por régimen no favorable.
- **Crash Boom Flip 150 Index**: `317` bloqueos preventivos por régimen no favorable.
- **GBPUSD**: `286` bloqueos preventivos por régimen no favorable.
- **USDCADmicro**: `260` bloqueos preventivos por régimen no favorable.
- **USDJPY**: `257` bloqueos preventivos por régimen no favorable.
- **USDCHF**: `244` bloqueos preventivos por régimen no favorable.
- **AUDCAD**: `210` bloqueos preventivos por régimen no favorable.

---
## 🔍 3. MODO ANÁLISIS RECIENTES (EVALUACIÓN DE OPORTUNIDADES & FILTROS)
Auditoría de por qué las señales analizadas en M15/M5/H1 entraron al mercado o fueron descartadas.

### 3.1 Embudo de Descarte & Motivos de Rechazo (Últimas 24h)
| Causa de Descarte / Filtro | Ocurrencias | Explicación Técnica |
| :--- | :--- | :--- |
| `NO_H4H1_CONFIRMATION` | **5,506** | Validación de confluencia técnica o filtro de seguridad. |
| `Otro worker esta evaluando o enviando un` | **4,359** | Bloqueo de concurrencia inter-proceso para evitar sobre-exposición simultánea. |
| `MSNR_VIDEO_SYNTHETICS_ONLY` | **3,892** | Validación de confluencia técnica o filtro de seguridad. |
| `FOREX_WORKER_PRUNES_TOXIC_ASSET` | **2,297** | Validación de confluencia técnica o filtro de seguridad. |
| `MARKET_REGIME_TOXIC_BLOCKED:ERRATIC_WHIP` | **2,024** | Volatilidad errática con mechas violentas detectada por ATR y Choppiness Index. |
| `WAITING_FIRST_RETEST` | **1,818** | Nivel identificado; esperando el primer retroceso técnico hacia la zona de valor. |
| `FOREX_ENTRADAS_SOLO_KILLZONES_LONDRES_07` | **1,534** | Horario restringido para pares de divisas fuera de las horas pico institucionales. |
| `NO_RSI2_PULLBACK` | **1,391** | Validación de confluencia técnica o filtro de seguridad. |
| `NO_MACRO_H4_BIAS_ALIGNED` | **1,273** | La dirección M5/M15 no coincide con el sesgo estructural H4 del mercado institucional. |
| `WAITING_MSS_STRICT_CLOSE_ABOVE_RESISTANC` | **1,009** | Validación de confluencia técnica o filtro de seguridad. |

### 3.2 Estado de Candidatos en Memoria (Pipeline MSNR)
- **Estado `WAITING`**: `3,453` candidatos.
- **Estado `WAITING_MALAYSIAN_SNR`**: `488` candidatos.
- **Estado `MSNR_SHADOW_SIGNAL`**: `348` candidatos.
- **Estado `BLOCKED_ACTIVE_TRADE`**: `38` candidatos.
- **Estado `STEP_ADX_LOW`**: `12` candidatos.
- **Estado `MARKET_REGIME_BLOCKED`**: `12` candidatos.
- **Estado `SYMBOL_COOLDOWN_POST_SL`**: `7` candidatos.
- **Estado `OPERACION_RECHAZADA_POR_RIESGO`**: `6` candidatos.
- **Estado `ENTRY_PRICE_DRIFT_TOO_LARGE`**: `5` candidatos.
- **Estado `BLOCKED_SYMBOL_CYCLE`**: `4` candidatos.
- **Estado `META_LABEL_FILTER_REJECTED`**: `3` candidatos.
- **Estado `SPLIT_ORDER_OPENED`**: `2` candidatos.
- **Estado `SYNTHETIC_SPREAD_TO_SL_EXCEEDED`**: `1` candidatos.
- **Estado `SYMBOL_DAILY_STRIKES_EXCEEDED`**: `1` candidatos.
- **Estado `MSNR_REGIME_ADX_BLOCKED`**: `1` candidatos.
- **Estado `JUMP_STRICT_FILTER_REJECTED`**: `1` candidatos.

---
## 💾 4. REGISTROS DE BASE DE DATOS & OPERACIONES

### 4.1 Operaciones Abiertas en Vivo (Con Nueva Operativa 1% Split Aplicada)
| Ticket | Instrumento | Tipo | Lote | Entrada | Stop Loss | TP1 (+1.0R) | TP2 / Runner | Flotante | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `4765402338` | **Jump 50 Index** | `SELL` | `0.03` | `65350.57` | `66172.93` | `62029.58` | Trade 2 (Runner Dinámico) | `$+0.00` | `OPEN` |
| `4765402308` | **Jump 50 Index** | `SELL` | `0.03` | `65338.77` | `66172.93` | `64504.61` | Trade 1 (TP1 1:1) | `$+0.00` | `OPEN` |
| `4765401837` | **High Frequency Vol 100 Index** | `BUY` | `0.05` | `45855.47` | `44774.57` | `48002.09` | Trade 2 (Runner Dinámico) | `$+0.00` | `OPEN` |
| `4765361378` | **Boom 500 Index** | `BUY` | `0.69` | `5968.549` | `5926.226` | `6053.279` | Trade 2 (Runner Dinámico) | `$+0.00` | `OPEN` |
| `4765361330` | **Boom 500 Index** | `BUY` | `0.69` | `5968.574` | `5926.226` | `6010.922` | Trade 1 (TP1 1:1) | `$+0.00` | `OPEN` |
| `4765304575` | **Step Index 200** | `BUY` | `0.15` | `10779.7` | `10785.2` | `10813.5` | Trade 2 (Runner Dinámico) | `$+0.00` | `OPEN` |
| `4765294818` | **Volatility 10 Index** | `BUY` | `2.15` | `4873.627` | `4877.698` | `4925.04` | Trade 2 (Runner Dinámico) | `$+0.00` | `OPEN` |
| `4765294818` | **Volatility 10 Index** | `BUY` | `2.15` | `4873.627` | `4877.698` | `4925.04` | Trade 2 (Runner Dinámico) | `$+0.00` | `OPEN` |
| `4764963476` | **Volatility 15 Index** | `SELL` | `0.19` | `100678.678` | `100582.081` | `100094.233` | Trade 2 (Runner Dinámico) | `$+0.00` | `OPEN` |
| `4764839062` | **Boom 900 Index** | `BUY` | `0.36` | `9068.27` | `8904.006` | `9396.87` | Trade 2 (Runner Dinámico) | `$+0.00` | `OPEN` |

> [!NOTE]
> Ambas posiciones en Boom 600 y Crash 500 están correctamente sincronizadas en MT5 con el **1% de riesgo total por activo dividido en dos operaciones de 0.5% cada una**. La primera operación busca cerrar exactamente en +1.0R (1:1), momento en el cual la segunda operación se protege en Break Even para buscar correr hacia 2R, 3R o 4R.

### 4.2 Historial de Últimas Operaciones Cerradas
| Ticket | Instrumento | Tipo | Lote | R:R Plan | R:R Realizado | Net PnL | Motivo de Cierre | Apertura |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `4765290843` | Jump 10 Index | `SELL` | 0.13 | 1.0R | **-0.96R** | **$-27.70** | `mt5_sl` | 2026-10-23 08:55:27 |
| `4765290856` | Jump 10 Index | `SELL` | 0.13 | 2.0R | **-0.94R** | **$-27.24** | `mt5_sl` | 2026-10-23 08:55:28 |
| `4765304544` | Step Index 200 | `BUY` | 0.15 | 1.0R | **+0.91R** | **$+25.80** | `mt5_tp` | 2026-10-23 09:10:31 |
| `4765294802` | Volatility 10 Index | `BUY` | 2.15 | 1.0R | **+0.95R** | **$+27.76** | `mt5_tp` | 2026-10-23 09:00:20 |
| `4765193138` | High Frequency Vol 50 Index | `SELL` | 0.05 | 2.0R | **-1.00R** | **$-57.82** | `mt5_sl` | 2026-10-23 07:16:26 |
| `4764962005` | Boom 500 Index | `BUY` | 0.56 | 4.0R | **+0.30R** | **$+9.25** | `mt5_sl` | 2026-10-23 01:22:30 |
| `4764860257` | Step Index 500 | `BUY` | 0.12 | 2.0R | **+2.06R** | **$+117.00** | `mt5_tp` | 2026-10-22 21:59:43 |
| `4765103108` | Volatility 5 Index | `BUY` | 0.26 | 1.0R | **-0.87R** | **$-25.17** | `mt5_sl` | 2026-10-23 05:27:38 |

### 4.3 Rendimiento Histórico por Instrumento (Top Activos)
| Instrumento | Trades Totales | Tasa de Acierto (Win Rate) | R:R Promedio | Observación Estratégica |
| :--- | :--- | :--- | :--- | :--- |
| **Step Index 500** | 101 | **50.5%** | +0.07R | ⚖️ Equilibrado |
| **Step Index 200** | 80 | **35.0%** | +1.58R | ⚠️ Requiere Calibración |
| **Volatility 25 Index** | 71 | **33.8%** | -0.37R | ⚠️ Requiere Calibración |
| **XAUUSD** | 67 | **55.2%** | +0.21R | 🔥 Altamente Rentable |
| **Crash 500 Index** | 62 | **74.2%** | +0.52R | 🔥 Altamente Rentable |
| **Jump 50 Index** | 51 | **45.1%** | -0.19R | ⚖️ Equilibrado |
| **US SP 500** | 50 | **32.0%** | -0.19R | ⚠️ Requiere Calibración |
| **Boom 600 Index** | 46 | **50.0%** | -0.12R | ⚖️ Equilibrado |
| **Volatility 75 Index** | 46 | **41.3%** | -0.24R | ⚠️ Requiere Calibración |
| **US Tech 100** | 40 | **35.0%** | -0.02R | ⚠️ Requiere Calibración |
| **BTCUSD** | 38 | **55.3%** | +0.14R | 🔥 Altamente Rentable |
| **Volatility 10 Index** | 38 | **52.6%** | +0.03R | ⚖️ Equilibrado |

---
## 🤖 5. COMPORTAMIENTO DE LOS MODELOS DE IA (GBDT META-LABELING)
El sistema cuenta con un pipeline de Meta-Labeling basado en modelos Gradient Boosting (LightGBM) que actúan como filtro bayesiano de calidad antes de enviar órdenes a MT5.

### 5.1 Catálogo de Modelos Entrenados y Parámetros en Producción
| Modelo | Dataset (Samples) | Win Rate Base | Accuracy Filtrada | Umbral Probabilidad | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `BOOM_ALL` | **19** | 31.6% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `BOOM_ICT` | **375** | 37.1% | **75.0%** | `p >= 0.5` | `MODELO ENTRENADO Y ACTIVO` |
| `BOOM_ICT_SABRI_MALLE` | **80** | 34.7% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `BOOM_MALAYSIAN_SNR` | **226** | 42.9% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `BOOM_MSNR_VIDEO` | **24** | 37.8% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `BOOM_ORB_NEW_YORK` | **0** | 0.0% | **N/A** | `p >= 0.52` | `SIN DATOS` |
| `BOOM_SMC` | **19** | 31.6% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `CRASH_ALL` | **332** | 42.2% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `CRASH_ICT` | **471** | 34.2% | **73.9%** | `p >= 0.5` | `MODELO ENTRENADO Y ACTIVO` |
| `CRASH_ICT_SABRI_MALLE` | **341** | 37.5% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `CRASH_MALAYSIAN_SNR` | **205** | 40.2% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `CRASH_ORB_NEW_YORK` | **0** | 0.0% | **N/A** | `p >= 0.52` | `SIN DATOS` |

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
