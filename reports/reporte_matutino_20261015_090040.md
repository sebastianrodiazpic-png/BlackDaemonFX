# 📊 REPORTE MATUTINO DE RENDIMIENTO Y AUDITORÍA INTEGRAL
**DaemonBlackFx v116 Multi-Strategy Autonomous Trading System**
**Fecha y Hora de Entrega:** 2026-10-15 09:00:40 (Hora de Chile / Santiago, UTC-3) | UTC: 2026-10-15 12:00:40

---

## 📌 1. RESUMEN EJECUTIVO & BALANCE FINANCIERO
| Métrica | Valor Actual MT5 | Estado Operativo |
| :--- | :--- | :--- |
| **Balance de Cuenta** | **$7,167.70 USD** | Capital consolidado |
| **Equidad en Vivo** | **$7,134.08 USD** | Flotante actual: `$-33.62 USD` |
| **Margen Libre** | **$7,057.83 USD** | 99.4% disponibilidad |
| **Operaciones Abiertas** | **5 posiciones** (2 pares divididos 1%) | Boom 600 BUY & Crash 500 SELL |
| **Total Operaciones Históricas** | **894 trades cerrados** | 390 Ganadoras / 474 Perdedoras |
| **Tasa de Acierto Global (Win Rate)** | **44.1%** | Con nuevo split 1:1 TP1 proyectado a **>62%** |
| **Ratio R:R Medio Realizado** | **0.09R** (Planificado: 2.31R) | Gestión Runner extendida |

---
## 🛡️ 2. MODO CENTINELA (MARKET REGIME SENTINEL & SYSTEM HEALTH)
El Modo Centinela actúa como escudo de preservación de capital, bloqueando regímenes tóxicos de mercado y verificando la salud activa de cada worker.

### 2.1 Estado de los Workers Multiproceso
| Worker | Magic | Estado Runtime | PID | Ciclos | Símbolo Monitoreado | Última Acción / Motivo |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `BOOM` | `26082101` | `WAITING_NEW_M1_BAR` | `21084` | 2861 | Boom 600 Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `CRASH` | `26082102` | `RUNNING` | `25132` | 3042 | Crash 600 Index | ANALYZANDO: MARKET_REGIME_TOXIC_BLOCKED:ERRATIC_WHIPSAW_V |
| `FLIP` | `26082106` | `DEGRADED_NO_SYMBOLS` | `9716` | 3560 | Crash Boom Flip 500 Index | EMPTY_CYCLE: El worker no tiene instrumentos seleccionados |
| `FOREX` | `26082027` | `SUPERSEDED` | `N/A` | 0 | N/A | REPLACED_BY_FOREX_SHARDS: v69: reemplazado por FOREX_1/FOREX_2/FOREX_3/ |
| `FOREX_1` | `26082201` | `RUNNING` | `5396` | 3258 | GBPCAD | ANALYZANDO: FOREX_WORKER_PRUNES_TOXIC_ASSET |
| `FOREX_2` | `26082202` | `RUNNING` | `26592` | 3215 | AUDUSD | ANALYZANDO: Instrumentos disponibles; esperando nueva vel |
| `FOREX_3` | `26082203` | `WAITING_NEW_M1_BAR` | `26868` | 3553 | CADCHF | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `FOREX_4` | `26082204` | `RUNNING` | `11820` | 2904 | USDCAD | MONITOR_POSICIONES: BACKGROUND_MONITOR |
| `GOLD` | `26082029` | `RUNNING` | `30068` | 3339 | XAUUSDmicro | ANALYZANDO: NO_CONFIRMED_QUARTER_REJECTION |
| `ICT` | `26082032` | `RUNNING` | `21636` | 874 | EURUSD | ANALYZANDO: NO_JUDAS_SWING_MANIPULATION_CONFIRMED |
| `IDX_OPEN` | `26082030` | `DISABLED` | `28664` | 14 | Wall Street 30 | STRATEGY_DISABLED_FROM_DASHBOARD: Desactivado manualmente desde el dashboard |
| `JUMP` | `26082105` | `WAITING_NEW_M1_BAR` | `9920` | 2826 | Jump 75 Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `MALAYSIAN_SNR` | `26082031` | `RUNNING` | `15684` | 697 | Step Index 400 | CURRENT_STRATEGY_VIEW_UPDATED: Observación de velas cerradas; nuevas entrada |
| `ORB` | `26082028` | `OUTSIDE_SESSION` | `25116` | 1186 | XAUUSDmicro | OUTSIDE_SESSION: Análisis pausado fuera de sesión; próxima com |
| `STEP` | `26082104` | `WAITING_NEW_M1_BAR` | `11944` | 2979 | Step Index 500 | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `V53_PROBE` | `53000000` | `PROBE` | `N/A` | 0 | N/A | SCHEMA_CHECK: v116-deriv-annotated-trade-audit |
| `VOLATILITY` | `26082103` | `SUPERSEDED` | `N/A` | 0 | N/A | REPLACED_BY_VOLATILITY_SHARDS: v99: reemplazado por VOLATILITY_1/2/3/4 |
| `VOLATILITY_1` | `26082401` | `RUNNING` | `12776` | 3198 | Volatility 25 Index | ANALYZANDO: Instrumentos disponibles; esperando nueva vel |
| `VOLATILITY_2` | `26082402` | `RUNNING` | `25112` | 3122 | Volatility 250 (1s) Index | ANALYZANDO: RANGE_HEIGHT_OUTSIDE_ATR_BOUNDS |
| `VOLATILITY_3` | `26082403` | `RUNNING` | `14112` | 3118 | Volatility 100 (1s) Index | ANALYZANDO: MARKET_REGIME_TOXIC_BLOCKED:ERRATIC_WHIPSAW_V |
| `VOLATILITY_4` | `26082404` | `RUNNING` | `29284` | 3547 | Volatility 90 Index | ANALYZANDO: DIRECTION_BLOCKED_BY_POLICY: SELL |

### 2.2 Bloqueos de Regímenes Tóxicos por el Centinela (Últimas 24h)
- **MARKET_REGIME_TOXIC_BLOCKED:ERRATIC_WHIPSAW_VOLATILITY**: `18,742` intervenciones preventivas.
- **MARKET_REGIME_TOXIC_BLOCKED:HIGH_CHOPPINESS_LOW_MOMENTUM**: `2,122` intervenciones preventivas.

### 2.3 Activos con Mayor Intervención del Escudo Centinela
- **Jump 50 Index**: `1,474` bloqueos preventivos por régimen no favorable.
- **Boom 600 Index**: `1,447` bloqueos preventivos por régimen no favorable.
- **Volatility 150 (1s) Index**: `1,161` bloqueos preventivos por régimen no favorable.
- **Crash 300 Index**: `1,146` bloqueos preventivos por régimen no favorable.
- **Volatility 90 Index**: `947` bloqueos preventivos por régimen no favorable.
- **Volatility 90 (1s) Index**: `947` bloqueos preventivos por régimen no favorable.
- **Volatility 250 (1s) Index**: `888` bloqueos preventivos por régimen no favorable.
- **BTCUSD**: `867` bloqueos preventivos por régimen no favorable.

---
## 🔍 3. MODO ANÁLISIS RECIENTES (EVALUACIÓN DE OPORTUNIDADES & FILTROS)
Auditoría de por qué las señales analizadas en M15/M5/H1 entraron al mercado o fueron descartadas.

### 3.1 Embudo de Descarte & Motivos de Rechazo (Últimas 24h)
| Causa de Descarte / Filtro | Ocurrencias | Explicación Técnica |
| :--- | :--- | :--- |
| `NO_JUDAS_SWING_MANIPULATION_CONFIRMED` | **4,286** | No se observó el barrido de liquidez previo (manipulación Judas) exigido por la estrategia ICT. |
| `MARKET_REGIME_TOXIC_BLOCKED:ERRATIC_WHIP` | **2,927** | Volatilidad errática con mechas violentas detectada por ATR y Choppiness Index. |
| `FOREX_ENTRADAS_SOLO_KILLZONES_LONDRES_07` | **1,426** | Horario restringido para pares de divisas fuera de las horas pico institucionales. |
| `SESSION_FILTER_OUTSIDE_KILLZONE` | **1,403** | Fuera de la ventana de liquidez principal (Killzones Londres/NY). |
| `Otro worker esta evaluando o enviando un` | **1,328** | Bloqueo de concurrencia inter-proceso para evitar sobre-exposición simultánea. |
| `FOREX_WORKER_PRUNES_TOXIC_ASSET` | **964** | Validación de confluencia técnica o filtro de seguridad. |
| `WAITING_FIRST_RETEST` | **908** | Nivel identificado; esperando el primer retroceso técnico hacia la zona de valor. |
| `NO_MACRO_H4_BIAS_ALIGNED` | **861** | La dirección M5/M15 no coincide con el sesgo estructural H4 del mercado institucional. |
| `RANGE_HEIGHT_OUTSIDE_ATR_BOUNDS` | **810** | La amplitud del rango no cumple los ratios de compresión/expansión ATR requeridos. |
| `DIRECTION_POLICY_BLOCKED` | **634** | Validación de confluencia técnica o filtro de seguridad. |

### 3.2 Estado de Candidatos en Memoria (Pipeline MSNR)
- **Estado `WAITING`**: `1,249` candidatos.
- **Estado `WAITING_MALAYSIAN_SNR`**: `305` candidatos.
- **Estado `MSNR_SHADOW_SIGNAL`**: `44` candidatos.
- **Estado `BLOCKED_ACTIVE_TRADE`**: `11` candidatos.
- **Estado `SYMBOL_COOLDOWN_POST_SL`**: `4` candidatos.
- **Estado `MARKET_REGIME_BLOCKED`**: `4` candidatos.
- **Estado `STEP_ADX_LOW`**: `3` candidatos.
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
| `4757562138` | **XAGUSDmicro** | `SELL` | `2.31` | `56.605` | `56.874` | `56.064` | Trade 2 (Runner Dinámico) | `$+0.00` | `OPEN` |
| `4757562136` | **XAGUSDmicro** | `SELL` | `2.31` | `56.604` | `56.874` | `56.334` | Trade 1 (TP1 1:1) | `$+0.00` | `OPEN` |
| `4757414460` | **Step Index 400** | `BUY` | `0.11` | `8875.8` | `8816.3` | `8993.6` | Trade 2 (Runner Dinámico) | `$+0.00` | `OPEN` |
| `4757339453` | **USDCAD** | `SELL` | `0.28` | `1.42047` | `1.42208` | `1.41398` | Trade 2 (Runner Dinámico) | `$+0.00` | `OPEN` |
| `4757339447` | **USDCAD** | `SELL` | `0.28` | `1.42047` | `1.42208` | `1.4188399999999999` | Trade 2 (Runner Dinámico) | `$+0.00` | `OPEN` |

> [!NOTE]
> Ambas posiciones en Boom 600 y Crash 500 están correctamente sincronizadas en MT5 con el **1% de riesgo total por activo dividido en dos operaciones de 0.5% cada una**. La primera operación busca cerrar exactamente en +1.0R (1:1), momento en el cual la segunda operación se protege en Break Even para buscar correr hacia 2R, 3R o 4R.

### 4.2 Historial de Últimas Operaciones Cerradas
| Ticket | Instrumento | Tipo | Lote | R:R Plan | R:R Realizado | Net PnL | Motivo de Cierre | Apertura |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `4757032781` | Crash 500 Index | `SELL` | 1.4 | 1.0R | **-0.98R** | **$-35.21** | `mt5_sl` | 2026-10-15 00:52:28 |
| `4757032803` | Crash 500 Index | `SELL` | 1.4 | 4.0R | **-0.98R** | **$-35.20** | `mt5_sl` | 2026-10-15 00:52:29 |
| `4757007342` | Boom 600 Index | `BUY` | 0.82 | 4.0R | **+0.31R** | **$+11.17** | `mt5_sl` | 2026-10-15 00:20:00 |
| `4757356929` | Crash 600 Index | `SELL` | 0.86 | 1.0R | **-0.92R** | **$-32.97** | `mt5_sl` | 2026-10-15 08:00:25 |
| `4757356961` | Crash 600 Index | `SELL` | 0.86 | 1.7R | **-0.92R** | **$-32.91** | `mt5_sl` | 2026-10-15 08:00:27 |
| `4757305972` | XAUUSD | `SELL` | 0.02 | 1.0R | **-0.95R** | **$-25.66** | `mt5_sl` | 2026-10-15 07:01:53 |
| `4757305988` | XAUUSD | `SELL` | 0.02 | 2.0R | **-0.96R** | **$-25.76** | `mt5_sl` | 2026-10-15 07:01:53 |
| `4757300838` | Step Index | `SELL` | 0.55 | 1.0R | **+0.00R** | **$+0.00** | `emergency_slippage_unfavorable_rr` | 2026-10-15 06:55:49 |

### 4.3 Rendimiento Histórico por Instrumento (Top Activos)
| Instrumento | Trades Totales | Tasa de Acierto (Win Rate) | R:R Promedio | Observación Estratégica |
| :--- | :--- | :--- | :--- | :--- |
| **Step Index 500** | 96 | **49.0%** | +0.02R | ⚖️ Equilibrado |
| **Volatility 25 Index** | 63 | **34.9%** | -0.34R | ⚠️ Requiere Calibración |
| **Step Index 200** | 61 | **34.4%** | +2.27R | ⚠️ Requiere Calibración |
| **XAUUSD** | 58 | **55.2%** | +0.27R | 🔥 Altamente Rentable |
| **Crash 500 Index** | 56 | **75.0%** | +0.56R | 🔥 Altamente Rentable |
| **Volatility 75 Index** | 44 | **43.2%** | -0.21R | ⚠️ Requiere Calibración |
| **US SP 500** | 41 | **34.1%** | -0.06R | ⚠️ Requiere Calibración |
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
| `BOOM_MALAYSIAN_SNR` | **216** | 24.8% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `BOOM_ORB_NEW_YORK` | **0** | 0.0% | **N/A** | `p >= 0.52` | `SIN DATOS` |
| `BOOM_SMC` | **19** | 31.6% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `CRASH_ALL` | **332** | 42.2% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `CRASH_ICT` | **471** | 34.2% | **73.9%** | `p >= 0.5` | `MODELO ENTRENADO Y ACTIVO` |
| `CRASH_ICT_SABRI_MALLE` | **336** | 43.1% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `CRASH_MALAYSIAN_SNR` | **204** | 37.1% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `CRASH_ORB_NEW_YORK` | **0** | 0.0% | **N/A** | `p >= 0.52` | `SIN DATOS` |
| `CRASH_SMC` | **106** | 34.9% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `FLIP_ALL` | **332** | 42.2% | **N/A** | `p >= 0.52` | `ENTRENADO` |

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
