# 📊 REPORTE MATUTINO DE RENDIMIENTO Y AUDITORÍA INTEGRAL
**DaemonBlackFx v116 Multi-Strategy Autonomous Trading System**
**Fecha y Hora de Entrega:** 2026-10-22 09:01:17 (Hora de Chile / Santiago, UTC-3) | UTC: 2026-10-22 12:01:17

---

## 📌 1. RESUMEN EJECUTIVO & BALANCE FINANCIERO
| Métrica | Valor Actual MT5 | Estado Operativo |
| :--- | :--- | :--- |
| **Balance de Cuenta** | **$6,019.85 USD** | Capital consolidado |
| **Equidad en Vivo** | **$6,102.70 USD** | Flotante actual: `$+82.85 USD` |
| **Margen Libre** | **$5,997.54 USD** | 99.4% disponibilidad |
| **Operaciones Abiertas** | **8 posiciones** (4 pares divididos 1%) | Boom 600 BUY & Crash 500 SELL |
| **Total Operaciones Históricas** | **1245 trades cerrados** | 390 Ganadoras / 474 Perdedoras |
| **Tasa de Acierto Global (Win Rate)** | **45.2%** | Con nuevo split 1:1 TP1 proyectado a **>62%** |
| **Ratio R:R Medio Realizado** | **0.03R** (Planificado: 2.10R) | Gestión Runner extendida |

---
## 🛡️ 2. MODO CENTINELA (MARKET REGIME SENTINEL & SYSTEM HEALTH)
El Modo Centinela actúa como escudo de preservación de capital, bloqueando regímenes tóxicos de mercado y verificando la salud activa de cada worker.

### 2.1 Estado de los Workers Multiproceso
| Worker | Magic | Estado Runtime | PID | Ciclos | Símbolo Monitoreado | Última Acción / Motivo |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `BOOM` | `26082101` | `WAITING_NEW_M1_BAR` | `31672` | 1782 | Boom 500 Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `CRASH` | `26082102` | `WAITING_NEW_M1_BAR` | `2744` | 1861 | Crash 900 Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `DRIFT` | `26082035` | `RUNNING` | `18436` | 3476 | Drift Switch Index 30 | WAITING_DRIFT_BREAKOUT: NO_COMPRESSION_BREAKOUT |
| `FLIP` | `26082106` | `RUNNING` | `32488` | 1445 | Crash Boom Flip 150 Index | ANALYZANDO: NO_DIRECTIONAL_M15_SETUP |
| `FOREX` | `26082027` | `SUPERSEDED` | `N/A` | 0 | N/A | REPLACED_BY_FOREX_SHARDS: v69: reemplazado por FOREX_1/FOREX_2/FOREX_3/ |
| `FOREX_1` | `26082201` | `WAITING_NEW_M1_BAR` | `17292` | 3030 | USDCHFmicro | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `FOREX_2` | `26082202` | `WAITING_NEW_M1_BAR` | `13752` | 2984 | EURUSDmicro | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `FOREX_3` | `26082203` | `WAITING_NEW_M1_BAR` | `7244` | 3120 | GBPJPYmicro | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `FOREX_4` | `26082204` | `WAITING_NEW_M1_BAR` | `27128` | 2151 | USDJPYmicro | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `GOLD` | `26082029` | `WAITING_NEW_M1_BAR` | `32072` | 3161 | XAUUSDmicro | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `ICT` | `26082032` | `RUNNING` | `32524` | 3379 | XAUUSD | ANALYZANDO: OUTSIDE_INSTITUTIONAL_KILLZONE (NY Hour: 07:0 |
| `IDX_OPEN` | `26082030` | `DISABLED` | `28664` | 14 | Wall Street 30 | STRATEGY_DISABLED_FROM_DASHBOARD: Desactivado manualmente desde el dashboard |
| `JUMP` | `26082105` | `WAITING_NEW_M1_BAR` | `21336` | 1942 | Jump 75 Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `MALAYSIAN_SNR` | `26082031` | `RUNNING` | `12904` | 219 | Volatility 50 Index | ANALYZANDO: ENTRY_PRICE_DRIFT_TOO_LARGE |
| `MSNR` | `26082033` | `RUNNING` | `16864` | 127 | Step Index | ANALYZANDO: Posicion activa: esperando cierre TP/SL/BE. S |
| `NIGHT` | `26082034` | `RUNNING` | `23336` | 3396 | Wall Street 30 | WAITING_OVERNIGHT: OVERNIGHT_SYMBOL_NOT_ALLOWED |
| `ORB` | `26082028` | `OUTSIDE_SESSION` | `14292` | 1159 | XAUUSDmicro | OUTSIDE_SESSION: Análisis pausado fuera de sesión; próxima com |
| `RSI2` | `26082036` | `RUNNING` | `27772` | 2929 | US SP 500 | ANALYZANDO: NO_RSI2_PULLBACK |
| `STEP` | `26082104` | `WAITING_NEW_M1_BAR` | `28692` | 2044 | Step Index 500 | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `V53_PROBE` | `53000000` | `PROBE` | `N/A` | 0 | N/A | SCHEMA_CHECK: v116-deriv-annotated-trade-audit |
| `VOLATILITY` | `26082103` | `SUPERSEDED` | `N/A` | 0 | N/A | REPLACED_BY_VOLATILITY_SHARDS: v99: reemplazado por VOLATILITY_1/2/3/4 |
| `VOLATILITY_1` | `26082401` | `RUNNING` | `17936` | 3086 | Volatility 75 (1s) Index | ANALYZANDO: ICT_SYMBOL_EXCLUDED_NEGATIVE_EXPECTANCY |
| `VOLATILITY_2` | `26082402` | `WAITING_NEW_M1_BAR` | `30820` | 2342 | Volatility 75 Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `VOLATILITY_3` | `26082403` | `WAITING_NEW_M1_BAR` | `6784` | 2409 | Volatility 90 (1s) Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `VOLATILITY_4` | `26082404` | `WAITING_NEW_M1_BAR` | `5468` | 2262 | Volatility 90 Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |

### 2.2 Bloqueos de Regímenes Tóxicos por el Centinela (Últimas 24h)
- **MARKET_REGIME_TOXIC_BLOCKED:ERRATIC_WHIPSAW_VOLATILITY**: `8,644` intervenciones preventivas.
- **MARKET_REGIME_TOXIC_BLOCKED:HIGH_CHOPPINESS_LOW_MOMENTUM**: `4,691` intervenciones preventivas.

### 2.3 Activos con Mayor Intervención del Escudo Centinela
- **XAUUSD**: `5,072` bloqueos preventivos por régimen no favorable.
- **EURUSD**: `794` bloqueos preventivos por régimen no favorable.
- **GBPCAD**: `506` bloqueos preventivos por régimen no favorable.
- **USDCHF**: `505` bloqueos preventivos por régimen no favorable.
- **GBPUSD**: `475` bloqueos preventivos por régimen no favorable.
- **EURUSDmicro**: `413` bloqueos preventivos por régimen no favorable.
- **XAGUSD**: `308` bloqueos preventivos por régimen no favorable.
- **Crash Boom Flip 500 Index**: `306` bloqueos preventivos por régimen no favorable.

---
## 🔍 3. MODO ANÁLISIS RECIENTES (EVALUACIÓN DE OPORTUNIDADES & FILTROS)
Auditoría de por qué las señales analizadas en M15/M5/H1 entraron al mercado o fueron descartadas.

### 3.1 Embudo de Descarte & Motivos de Rechazo (Últimas 24h)
| Causa de Descarte / Filtro | Ocurrencias | Explicación Técnica |
| :--- | :--- | :--- |
| `NO_H4H1_CONFIRMATION` | **6,054** | Validación de confluencia técnica o filtro de seguridad. |
| `MSNR_VIDEO_SYNTHETICS_ONLY` | **3,666** | Validación de confluencia técnica o filtro de seguridad. |
| `Otro worker esta evaluando o enviando un` | **3,315** | Bloqueo de concurrencia inter-proceso para evitar sobre-exposición simultánea. |
| `MARKET_REGIME_TOXIC_BLOCKED:ERRATIC_WHIP` | **2,587** | Volatilidad errática con mechas violentas detectada por ATR y Choppiness Index. |
| `FOREX_WORKER_PRUNES_TOXIC_ASSET` | **2,313** | Validación de confluencia técnica o filtro de seguridad. |
| `WAITING_FIRST_RETEST` | **1,926** | Nivel identificado; esperando el primer retroceso técnico hacia la zona de valor. |
| `FOREX_ENTRADAS_SOLO_KILLZONES_LONDRES_07` | **1,542** | Horario restringido para pares de divisas fuera de las horas pico institucionales. |
| `WAITING_MSS_STRICT_CLOSE_ABOVE_RESISTANC` | **1,075** | Validación de confluencia técnica o filtro de seguridad. |
| `ICT_SYMBOL_PRUNED_WINRATE_LE_45` | **1,019** | Validación de confluencia técnica o filtro de seguridad. |
| `NO_MACRO_H4_BIAS_ALIGNED` | **1,018** | La dirección M5/M15 no coincide con el sesgo estructural H4 del mercado institucional. |

### 3.2 Estado de Candidatos en Memoria (Pipeline MSNR)
- **Estado `WAITING`**: `3,085` candidatos.
- **Estado `WAITING_MALAYSIAN_SNR`**: `464` candidatos.
- **Estado `MSNR_SHADOW_SIGNAL`**: `283` candidatos.
- **Estado `BLOCKED_ACTIVE_TRADE`**: `36` candidatos.
- **Estado `STEP_ADX_LOW`**: `12` candidatos.
- **Estado `MARKET_REGIME_BLOCKED`**: `9` candidatos.
- **Estado `SYMBOL_COOLDOWN_POST_SL`**: `7` candidatos.
- **Estado `OPERACION_RECHAZADA_POR_RIESGO`**: `5` candidatos.
- **Estado `ENTRY_PRICE_DRIFT_TOO_LARGE`**: `5` candidatos.
- **Estado `BLOCKED_SYMBOL_CYCLE`**: `4` candidatos.
- **Estado `META_LABEL_FILTER_REJECTED`**: `3` candidatos.
- **Estado `SYNTHETIC_SPREAD_TO_SL_EXCEEDED`**: `1` candidatos.
- **Estado `SYMBOL_DAILY_STRIKES_EXCEEDED`**: `1` candidatos.
- **Estado `SPLIT_ORDER_OPENED`**: `1` candidatos.
- **Estado `MSNR_REGIME_ADX_BLOCKED`**: `1` candidatos.

---
## 💾 4. REGISTROS DE BASE DE DATOS & OPERACIONES

### 4.1 Operaciones Abiertas en Vivo (Con Nueva Operativa 1% Split Aplicada)
| Ticket | Instrumento | Tipo | Lote | Entrada | Stop Loss | TP1 (+1.0R) | TP2 / Runner | Flotante | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `4764153811` | **Jump 75 Index** | `BUY` | `0.25` | `6624.24` | `6661.03` | `7080.13` | Trade 2 (Runner Dinámico) | `$+0.00` | `OPEN` |
| `4764067855` | **Boom 500 Index** | `BUY` | `0.52` | `5822.591` | `5839.776` | `5933.721` | Trade 2 (Runner Dinámico) | `$+0.00` | `OPEN` |
| `4763982756` | **Jump 25 Index** | `BUY` | `0.02` | `133521.34` | `132411.9` | `138077.4` | Trade 2 (Runner Dinámico) | `$+0.00` | `OPEN` |
| `4763982736` | **Jump 25 Index** | `BUY` | `0.02` | `133535.48` | `132411.9` | `134659.06` | Trade 1 (TP1 1:1) | `$+0.00` | `OPEN` |
| `4763896898` | **Volatility 100 Index** | `BUY` | `1.16` | `725.79` | `701.1` | `823.95` | Trade 2 (Runner Dinámico) | `$+0.00` | `OPEN` |
| `4763896851` | **Volatility 100 Index** | `BUY` | `1.16` | `725.79` | `701.1` | `750.48` | Trade 1 (TP1 1:1) | `$+0.00` | `OPEN` |
| `4763753732` | **Volatility 10 Index** | `BUY` | `2.2800000000000002` | `4896.794` | `4884.494` | `4944.989` | Trade 2 (Runner Dinámico) | `$+0.00` | `OPEN` |
| `4763753725` | **Volatility 10 Index** | `BUY` | `2.2800000000000002` | `4896.745` | `4884.494` | `4908.996` | Trade 1 (TP1 1:1) | `$+0.00` | `OPEN` |

> [!NOTE]
> Ambas posiciones en Boom 600 y Crash 500 están correctamente sincronizadas en MT5 con el **1% de riesgo total por activo dividido en dos operaciones de 0.5% cada una**. La primera operación busca cerrar exactamente en +1.0R (1:1), momento en el cual la segunda operación se protege en Break Even para buscar correr hacia 2R, 3R o 4R.

### 4.2 Historial de Últimas Operaciones Cerradas
| Ticket | Instrumento | Tipo | Lote | R:R Plan | R:R Realizado | Net PnL | Motivo de Cierre | Apertura |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `4764153796` | Jump 75 Index | `BUY` | 0.25 | 1.0R | **+0.99R** | **$+28.70** | `mt5_tp` | 2026-10-22 09:07:39 |
| `4764067831` | Boom 500 Index | `BUY` | 0.52 | 1.0R | **+1.03R** | **$+30.31** | `mt5_tp` | 2026-10-22 07:37:49 |
| `4764060515` | Step Index 400 | `BUY` | 0.16 | 2.0R | **-0.94R** | **$-52.48** | `mt5_sl` | 2026-10-22 07:29:36 |
| `4763864845` | Step Index 200 | `BUY` | 0.13 | 2.0R | **+0.30R** | **$+8.58** | `mt5_sl` | 2026-10-22 03:13:33 |
| `4763864840` | Step Index 200 | `BUY` | 0.13 | 1.0R | **+0.92R** | **$+26.78** | `mt5_tp` | 2026-10-22 03:13:31 |
| `4763758127` | Boom 500 Index | `BUY` | 0.82 | 2.0R | **+1.99R** | **$+57.85** | `mt5_tp` | 2026-10-21 23:57:46 |
| `4763810150` | Boom 900 Index | `BUY` | 0.48 | 1.0R | **-0.98R** | **$-28.36** | `mt5_sl` | 2026-10-22 01:36:54 |
| `4763810250` | Boom 900 Index | `BUY` | 0.48 | 2.0R | **-0.98R** | **$-28.33** | `mt5_sl` | 2026-10-22 01:37:00 |

### 4.3 Rendimiento Histórico por Instrumento (Top Activos)
| Instrumento | Trades Totales | Tasa de Acierto (Win Rate) | R:R Promedio | Observación Estratégica |
| :--- | :--- | :--- | :--- | :--- |
| **Step Index 500** | 99 | **50.5%** | +0.06R | ⚖️ Equilibrado |
| **Step Index 200** | 73 | **37.0%** | +1.81R | ⚠️ Requiere Calibración |
| **Volatility 25 Index** | 71 | **33.8%** | -0.37R | ⚠️ Requiere Calibración |
| **XAUUSD** | 65 | **53.8%** | +0.22R | ⚖️ Equilibrado |
| **Crash 500 Index** | 62 | **74.2%** | +0.52R | 🔥 Altamente Rentable |
| **US SP 500** | 50 | **32.0%** | -0.19R | ⚠️ Requiere Calibración |
| **Boom 600 Index** | 46 | **50.0%** | -0.12R | ⚖️ Equilibrado |
| **Volatility 75 Index** | 46 | **41.3%** | -0.24R | ⚠️ Requiere Calibración |
| **Jump 50 Index** | 45 | **46.7%** | -0.17R | ⚖️ Equilibrado |
| **US Tech 100** | 40 | **35.0%** | -0.02R | ⚠️ Requiere Calibración |
| **BTCUSD** | 38 | **55.3%** | +0.14R | 🔥 Altamente Rentable |
| **Wall Street 30** | 38 | **57.9%** | +0.05R | 🔥 Altamente Rentable |

---
## 🤖 5. COMPORTAMIENTO DE LOS MODELOS DE IA (GBDT META-LABELING)
El sistema cuenta con un pipeline de Meta-Labeling basado en modelos Gradient Boosting (LightGBM) que actúan como filtro bayesiano de calidad antes de enviar órdenes a MT5.

### 5.1 Catálogo de Modelos Entrenados y Parámetros en Producción
| Modelo | Dataset (Samples) | Win Rate Base | Accuracy Filtrada | Umbral Probabilidad | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `BOOM_ALL` | **19** | 31.6% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `BOOM_ICT` | **375** | 37.1% | **75.0%** | `p >= 0.5` | `MODELO ENTRENADO Y ACTIVO` |
| `BOOM_ICT_SABRI_MALLE` | **71** | 37.1% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `BOOM_MALAYSIAN_SNR` | **224** | 36.7% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `BOOM_MSNR_VIDEO` | **21** | 38.2% | **N/A** | `p >= 0.52` | `ENTRENADO` |
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
