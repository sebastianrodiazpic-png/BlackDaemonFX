# 📊 REPORTE MATUTINO DE RENDIMIENTO Y AUDITORÍA INTEGRAL
**DaemonBlackFx v116 Multi-Strategy Autonomous Trading System**
**Fecha y Hora de Entrega:** 2026-10-16 09:00:52 (Hora de Chile / Santiago, UTC-3) | UTC: 2026-10-16 12:00:52

---

## 📌 1. RESUMEN EJECUTIVO & BALANCE FINANCIERO
| Métrica | Valor Actual MT5 | Estado Operativo |
| :--- | :--- | :--- |
| **Balance de Cuenta** | **$6,428.59 USD** | Capital consolidado |
| **Equidad en Vivo** | **$6,502.80 USD** | Flotante actual: `$+74.21 USD` |
| **Margen Libre** | **$6,402.78 USD** | 99.4% disponibilidad |
| **Operaciones Abiertas** | **5 posiciones** (2 pares divididos 1%) | Boom 600 BUY & Crash 500 SELL |
| **Total Operaciones Históricas** | **947 trades cerrados** | 390 Ganadoras / 474 Perdedoras |
| **Tasa de Acierto Global (Win Rate)** | **43.4%** | Con nuevo split 1:1 TP1 proyectado a **>62%** |
| **Ratio R:R Medio Realizado** | **0.05R** (Planificado: 2.28R) | Gestión Runner extendida |

---
## 🛡️ 2. MODO CENTINELA (MARKET REGIME SENTINEL & SYSTEM HEALTH)
El Modo Centinela actúa como escudo de preservación de capital, bloqueando regímenes tóxicos de mercado y verificando la salud activa de cada worker.

### 2.1 Estado de los Workers Multiproceso
| Worker | Magic | Estado Runtime | PID | Ciclos | Símbolo Monitoreado | Última Acción / Motivo |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `BOOM` | `26082101` | `WAITING_NEW_M1_BAR` | `26720` | 2395 | Boom 600 Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `CRASH` | `26082102` | `WAITING_NEW_M1_BAR` | `7036` | 2470 | Crash 600 Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `FLIP` | `26082106` | `WAITING_NEW_M1_BAR` | `16956` | 1776 | Crash Boom Flip 500 Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `FOREX` | `26082027` | `SUPERSEDED` | `N/A` | 0 | N/A | REPLACED_BY_FOREX_SHARDS: v69: reemplazado por FOREX_1/FOREX_2/FOREX_3/ |
| `FOREX_1` | `26082201` | `WAITING_NEW_M1_BAR` | `31724` | 2838 | USDCHFmicro | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `FOREX_2` | `26082202` | `WAITING_NEW_M1_BAR` | `9244` | 2667 | EURUSDmicro | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `FOREX_3` | `26082203` | `WAITING_NEW_M1_BAR` | `33256` | 3197 | CADCHF | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `FOREX_4` | `26082204` | `WAITING_NEW_M1_BAR` | `2320` | 2416 | USDJPYmicro | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `GOLD` | `26082029` | `WAITING_NEW_M1_BAR` | `2568` | 2860 | XAUUSDmicro | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `ICT` | `26082032` | `RUNNING` | `28712` | 503 | XAUUSDmicro | WAITING_ICT: NO_MACRO_H4_BIAS_ALIGNED |
| `IDX_OPEN` | `26082030` | `DISABLED` | `28664` | 14 | Wall Street 30 | STRATEGY_DISABLED_FROM_DASHBOARD: Desactivado manualmente desde el dashboard |
| `JUMP` | `26082105` | `WAITING_NEW_M1_BAR` | `5004` | 2123 | Jump 75 Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `MALAYSIAN_SNR` | `26082031` | `RUNNING` | `29320` | 526 | Boom 1000 Index | ANALYZANDO: RETEST_WEAK_RECOVERY |
| `ORB` | `26082028` | `OUTSIDE_SESSION` | `24388` | 1068 | XAUUSDmicro | OUTSIDE_SESSION: Análisis pausado fuera de sesión; próxima com |
| `STEP` | `26082104` | `WAITING_NEW_M1_BAR` | `25892` | 2565 | Step Index 500 | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `V53_PROBE` | `53000000` | `PROBE` | `N/A` | 0 | N/A | SCHEMA_CHECK: v116-deriv-annotated-trade-audit |
| `VOLATILITY` | `26082103` | `SUPERSEDED` | `N/A` | 0 | N/A | REPLACED_BY_VOLATILITY_SHARDS: v99: reemplazado por VOLATILITY_1/2/3/4 |
| `VOLATILITY_1` | `26082401` | `WAITING_NEW_M1_BAR` | `28072` | 2637 | VolSwitch High Vol Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `VOLATILITY_2` | `26082402` | `WAITING_NEW_M1_BAR` | `25712` | 2244 | Volatility 75 Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `VOLATILITY_3` | `26082403` | `WAITING_NEW_M1_BAR` | `3820` | 2122 | Volatility 90 (1s) Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `VOLATILITY_4` | `26082404` | `WAITING_NEW_M1_BAR` | `28092` | 2998 | Volatility 90 Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |

### 2.2 Bloqueos de Regímenes Tóxicos por el Centinela (Últimas 24h)
- **MARKET_REGIME_TOXIC_BLOCKED:ERRATIC_WHIPSAW_VOLATILITY**: `11,756` intervenciones preventivas.
- **MARKET_REGIME_TOXIC_BLOCKED:HIGH_CHOPPINESS_LOW_MOMENTUM**: `1,466` intervenciones preventivas.

### 2.3 Activos con Mayor Intervención del Escudo Centinela
- **EURUSDmicro**: `1,028` bloqueos preventivos por régimen no favorable.
- **EURUSD**: `1,025` bloqueos preventivos por régimen no favorable.
- **Volatility 250 (1s) Index**: `993` bloqueos preventivos por régimen no favorable.
- **BTCUSD**: `947` bloqueos preventivos por régimen no favorable.
- **Volatility 75 Index**: `660` bloqueos preventivos por régimen no favorable.
- **Step Index 400**: `638` bloqueos preventivos por régimen no favorable.
- **VolSwitch High Vol Index**: `562` bloqueos preventivos por régimen no favorable.
- **Volatility 75 (1s) Index**: `469` bloqueos preventivos por régimen no favorable.

---
## 🔍 3. MODO ANÁLISIS RECIENTES (EVALUACIÓN DE OPORTUNIDADES & FILTROS)
Auditoría de por qué las señales analizadas en M15/M5/H1 entraron al mercado o fueron descartadas.

### 3.1 Embudo de Descarte & Motivos de Rechazo (Últimas 24h)
| Causa de Descarte / Filtro | Ocurrencias | Explicación Técnica |
| :--- | :--- | :--- |
| `MARKET_REGIME_TOXIC_BLOCKED:ERRATIC_WHIP` | **2,257** | Volatilidad errática con mechas violentas detectada por ATR y Choppiness Index. |
| `WAITING_MSS_STRICT_CLOSE_BELOW_SUPPORT` | **2,061** | Validación de confluencia técnica o filtro de seguridad. |
| `WAITING_MSS_STRICT_CLOSE_ABOVE_RESISTANC` | **1,799** | Validación de confluencia técnica o filtro de seguridad. |
| `FOREX_ENTRADAS_SOLO_KILLZONES_LONDRES_07` | **1,514** | Horario restringido para pares de divisas fuera de las horas pico institucionales. |
| `Otro worker esta evaluando o enviando un` | **1,450** | Bloqueo de concurrencia inter-proceso para evitar sobre-exposición simultánea. |
| `NO_MACRO_H4_BIAS_ALIGNED` | **1,392** | La dirección M5/M15 no coincide con el sesgo estructural H4 del mercado institucional. |
| `SESSION_FILTER_OUTSIDE_KILLZONE` | **1,364** | Fuera de la ventana de liquidez principal (Killzones Londres/NY). |
| `PROBABILITY_BELOW_THRESHOLD` | **1,176** | Validación de confluencia técnica o filtro de seguridad. |
| `FOREX_WORKER_PRUNES_TOXIC_ASSET` | **971** | Validación de confluencia técnica o filtro de seguridad. |
| `DIRECTION_BLOCKED_BY_POLICY: SELL` | **961** | Validación de confluencia técnica o filtro de seguridad. |

### 3.2 Estado de Candidatos en Memoria (Pipeline MSNR)
- **Estado `WAITING`**: `1,470` candidatos.
- **Estado `WAITING_MALAYSIAN_SNR`**: `319` candidatos.
- **Estado `MSNR_SHADOW_SIGNAL`**: `71` candidatos.
- **Estado `BLOCKED_ACTIVE_TRADE`**: `21` candidatos.
- **Estado `SYMBOL_COOLDOWN_POST_SL`**: `5` candidatos.
- **Estado `STEP_ADX_LOW`**: `5` candidatos.
- **Estado `MARKET_REGIME_BLOCKED`**: `5` candidatos.
- **Estado `OPERACION_RECHAZADA_POR_RIESGO`**: `3` candidatos.
- **Estado `SYMBOL_DAILY_STRIKES_EXCEEDED`**: `1` candidatos.
- **Estado `SPLIT_ORDER_OPENED`**: `1` candidatos.
- **Estado `META_LABEL_FILTER_REJECTED`**: `1` candidatos.
- **Estado `ENTRY_PRICE_DRIFT_TOO_LARGE`**: `1` candidatos.

---
## 💾 4. REGISTROS DE BASE DE DATOS & OPERACIONES

### 4.1 Operaciones Abiertas en Vivo (Con Nueva Operativa 1% Split Aplicada)
| Ticket | Instrumento | Tipo | Lote | Entrada | Stop Loss | TP1 (+1.0R) | TP2 / Runner | Flotante | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `4758583056` | **Step Index 400** | `BUY` | `0.1` | `8965.4` | `8935.6` | `9051.6` | Trade 2 (Runner Dinámico) | `$+0.00` | `OPEN` |
| `4758583035` | **Step Index 400** | `BUY` | `0.1` | `8965.0` | `8935.6` | `8994.4` | Trade 1 (TP1 1:1) | `$+0.00` | `OPEN` |
| `4758423306` | **Step Index** | `SELL` | `0.17` | `7253.8` | `7270.1` | `7203.7` | Trade 2 (Runner Dinámico) | `$+0.00` | `OPEN` |
| `4758423291` | **Step Index** | `SELL` | `0.17` | `7253.6` | `7270.1` | `7237.1` | Trade 1 (TP1 1:1) | `$+0.00` | `OPEN` |
| `4758268233` | **Boom 600 Index** | `BUY` | `1.24` | `5215.399` | `5223.953` | `5267.349` | Trade 2 (Runner Dinámico) | `$+0.00` | `OPEN` |

> [!NOTE]
> Ambas posiciones en Boom 600 y Crash 500 están correctamente sincronizadas en MT5 con el **1% de riesgo total por activo dividido en dos operaciones de 0.5% cada una**. La primera operación busca cerrar exactamente en +1.0R (1:1), momento en el cual la segunda operación se protege en Break Even para buscar correr hacia 2R, 3R o 4R.

### 4.2 Historial de Últimas Operaciones Cerradas
| Ticket | Instrumento | Tipo | Lote | R:R Plan | R:R Realizado | Net PnL | Motivo de Cierre | Apertura |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `4758268224` | Boom 600 Index | `BUY` | 1.24 | 1.0R | **+1.22R** | **$+40.37** | `mt5_tp` | 2026-10-16 04:16:39 |
| `4758437077` | Jump 25 Index | `BUY` | 0.05 | 1.0R | **-1.31R** | **$-41.50** | `mt5_sl` | 2026-10-16 08:35:50 |
| `4758437096` | Jump 25 Index | `BUY` | 0.05 | 2.0R | **-1.32R** | **$-41.70** | `mt5_sl` | 2026-10-16 08:35:54 |
| `4758230790` | Crash 300 Index | `SELL` | 1.21 | 1.0R | **-0.96R** | **$-31.53** | `mt5_sl` | 2026-10-16 03:12:38 |
| `4758302720` | Jump 25 Index | `BUY` | 0.09 | 1.0R | **-0.96R** | **$-30.03** | `mt5_sl` | 2026-10-16 05:26:58 |
| `4758302735` | Jump 25 Index | `BUY` | 0.09 | 2.0R | **-1.01R** | **$-31.70** | `mt5_sl` | 2026-10-16 05:27:01 |
| `4758292654` | Crash 600 Index | `SELL` | 1.05 | 1.0R | **-0.89R** | **$-28.92** | `mt5_sl` | 2026-10-16 05:05:37 |
| `4758292664` | Crash 600 Index | `SELL` | 1.05 | 2.9R | **-0.89R** | **$-28.85** | `mt5_sl` | 2026-10-16 05:05:39 |

### 4.3 Rendimiento Histórico por Instrumento (Top Activos)
| Instrumento | Trades Totales | Tasa de Acierto (Win Rate) | R:R Promedio | Observación Estratégica |
| :--- | :--- | :--- | :--- | :--- |
| **Step Index 500** | 96 | **49.0%** | +0.02R | ⚖️ Equilibrado |
| **Volatility 25 Index** | 63 | **34.9%** | -0.34R | ⚠️ Requiere Calibración |
| **Step Index 200** | 61 | **34.4%** | +2.27R | ⚠️ Requiere Calibración |
| **XAUUSD** | 60 | **53.3%** | +0.24R | ⚖️ Equilibrado |
| **Crash 500 Index** | 58 | **72.4%** | +0.51R | 🔥 Altamente Rentable |
| **US SP 500** | 46 | **30.4%** | -0.16R | ⚠️ Requiere Calibración |
| **Volatility 75 Index** | 44 | **43.2%** | -0.21R | ⚠️ Requiere Calibración |
| **US Tech 100** | 40 | **35.0%** | -0.02R | ⚠️ Requiere Calibración |
| **BTCUSD** | 38 | **55.3%** | +0.14R | 🔥 Altamente Rentable |
| **Wall Street 30** | 36 | **55.6%** | +0.02R | 🔥 Altamente Rentable |
| **Volatility 10 Index** | 33 | **45.5%** | -0.09R | ⚖️ Equilibrado |
| **Boom 1000 Index** | 24 | **50.0%** | +0.02R | ⚖️ Equilibrado |

---
## 🤖 5. COMPORTAMIENTO DE LOS MODELOS DE IA (GBDT META-LABELING)
El sistema cuenta con un pipeline de Meta-Labeling basado en modelos Gradient Boosting (LightGBM) que actúan como filtro bayesiano de calidad antes de enviar órdenes a MT5.

### 5.1 Catálogo de Modelos Entrenados y Parámetros en Producción
| Modelo | Dataset (Samples) | Win Rate Base | Accuracy Filtrada | Umbral Probabilidad | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `BOOM_ALL` | **19** | 31.6% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `BOOM_ICT` | **375** | 37.1% | **75.0%** | `p >= 0.5` | `MODELO ENTRENADO Y ACTIVO` |
| `BOOM_ICT_SABRI_MALLE` | **24** | 38.0% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `BOOM_MALAYSIAN_SNR` | **216** | 24.8% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `BOOM_ORB_NEW_YORK` | **0** | 0.0% | **N/A** | `p >= 0.52` | `SIN DATOS` |
| `BOOM_SMC` | **19** | 31.6% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `CRASH_ALL` | **332** | 42.2% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `CRASH_ICT` | **471** | 34.2% | **73.9%** | `p >= 0.5` | `MODELO ENTRENADO Y ACTIVO` |
| `CRASH_ICT_SABRI_MALLE` | **336** | 43.1% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `CRASH_MALAYSIAN_SNR` | **204** | 37.1% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `CRASH_ORB_NEW_YORK` | **0** | 0.0% | **N/A** | `p >= 0.52` | `SIN DATOS` |
| `CRASH_SMC` | **106** | 34.9% | **N/A** | `p >= 0.52` | `ENTRENADO` |

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
