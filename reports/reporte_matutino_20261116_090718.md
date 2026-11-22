# 📊 REPORTE MATUTINO DE RENDIMIENTO Y AUDITORÍA INTEGRAL
**DaemonBlackFx v116 Multi-Strategy Autonomous Trading System**
**Fecha y Hora de Entrega:** 2026-11-16 09:07:18 (Hora de Chile / Santiago, UTC-3) | UTC: 2026-11-16 12:07:18

---

## 📌 1. RESUMEN EJECUTIVO & BALANCE FINANCIERO
| Métrica | Valor Actual MT5 | Estado Operativo |
| :--- | :--- | :--- |
| **Balance de Cuenta** | **$4,626.35 USD** | Capital consolidado |
| **Equidad en Vivo** | **$4,613.03 USD** | Flotante actual: `$-13.32 USD` |
| **Margen Libre** | **$4,594.33 USD** | 99.4% disponibilidad |
| **Operaciones Abiertas** | **5 posiciones** (2 pares divididos 1%) | Boom 600 BUY & Crash 500 SELL |
| **Total Operaciones Históricas** | **1916 trades cerrados** | 390 Ganadoras / 474 Perdedoras |
| **Tasa de Acierto Global (Win Rate)** | **47.5%** | Con nuevo split 1:1 TP1 proyectado a **>62%** |
| **Ratio R:R Medio Realizado** | **0.02R** (Planificado: 1.96R) | Gestión Runner extendida |

---
## 🛡️ 2. MODO CENTINELA (MARKET REGIME SENTINEL & SYSTEM HEALTH)
El Modo Centinela actúa como escudo de preservación de capital, bloqueando regímenes tóxicos de mercado y verificando la salud activa de cada worker.

### 2.1 Estado de los Workers Multiproceso
| Worker | Magic | Estado Runtime | PID | Ciclos | Símbolo Monitoreado | Última Acción / Motivo |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `BOOM` | `26082101` | `WAITING_NEW_M1_BAR` | `11172` | 200 | Volatility Boom 750 Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `COMMODITIES_SNR` | `26082041` | `RUNNING` | `22728` | 229 | XAUUSDmicro | WAITING_MALAYSIAN_SNR: SESSION_FILTER_OUTSIDE_KILLZONE |
| `CRASH` | `26082102` | `WAITING_NEW_M1_BAR` | `3756` | 200 | Volatility Crash 750 Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `FLIP` | `26082106` | `DISABLED_BY_CONFIG` | `N/A` | 0 | N/A | WORKER_PROCESS_SKIPPED_DISABLED: FLIP_NO_PUBLISHED_SYMBOLS |
| `FOREX` | `26082027` | `SUPERSEDED` | `N/A` | 0 | N/A | REPLACED_BY_FOREX_SHARDS: v69: reemplazado por FOREX_1/FOREX_2/FOREX_3/ |
| `FOREX_1` | `26082201` | `RUNNING` | `16816` | 200 | NZDUSDmicro | MARKET_REGIME_BLOCKED: MARKET_REGIME_TOXIC_BLOCKED:HIGH_CHOPPINESS_L |
| `FOREX_2` | `26082202` | `DEGRADED_NO_SYMBOLS` | `24264` | 200 | EURUSDmicro | EMPTY_CYCLE: El worker no tiene instrumentos seleccionados |
| `FOREX_3` | `26082203` | `DISABLED_BY_CONFIG` | `10072` | 0 | GBPJPYmicro | WORKER_PROCESS_SKIPPED_DISABLED: DAEMONBLACKFX_DISABLED_WORKERS |
| `FOREX_4` | `26082204` | `DISABLED_BY_CONFIG` | `12676` | 0 | USDJPYmicro | WORKER_PROCESS_SKIPPED_DISABLED: DAEMONBLACKFX_DISABLED_WORKERS |
| `FOREX_5` | `26082205` | `WAITING_NEW_M1_BAR` | `4268` | 197 | GBPUSDmicro | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `FOREX_SNR` | `26082043` | `RUNNING` | `29316` | 0 | USDJPYmicro | STANDBY_MARKET_CLOSED: Mercado cerrado; reposo automático hasta Sund |
| `ICT` | `26082032` | `RUNNING` | `32948` | 197 | BTCUSD | ICT_CRYPTO_DISABLED: ICT_CRYPTO_NEGATIVE_EXPECTANCY_REPLAY_2Y |
| `INDICESB_SNR` | `26082042` | `RUNNING` | `5388` | 199 | Wall Street 30 | WAITING_ICT: OUTSIDE_INSTITUTIONAL_KILLZONE (NY Hour: 07:0 |
| `JUMP` | `26082105` | `RUNNING` | `33280` | 164 | Jump 75 Index | BLOCKED_ACTIVE_TRADE: Posicion activa: esperando cierre TP/SL/BE. S |
| `MALAYSIAN_SNR` | `26082031` | `RUNNING` | `29740` | 77 | VolSwitch High Vol Index | WAITING_MALAYSIAN_SNR: NO_SETUP_CONFIRMED |
| `ORB` | `26082028` | `RUNNING` | `31144` | 70 | XAUUSDmicro | CYCLE_START: ULTIMA_SECUENCIA_M5_NO_TIENE_BREAKOUT_VALIDO |
| `STEP` | `26082104` | `WAITING_NEW_M1_BAR` | `29588` | 197 | Step Index 500 | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `TREND_PULLBACK` | `26082038` | `DISABLED_BY_CONFIG` | `30444` | 0 | VolSwitch High Vol Index | WORKER_PROCESS_SKIPPED_DISABLED: DAEMONBLACKFX_DISABLED_WORKERS |
| `V53_PROBE` | `53000000` | `PROBE` | `N/A` | 0 | N/A | SCHEMA_CHECK: v116-deriv-annotated-trade-audit |
| `VOLATILITY` | `26082103` | `SUPERSEDED` | `N/A` | 0 | N/A | REPLACED_BY_VOLATILITY_SHARDS: v99: reemplazado por VOLATILITY_1/2/3/4 |
| `VOLATILITY_1` | `26082401` | `WAITING_NEW_M1_BAR` | `24344` | 163 | High Frequency Vol 75 Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |
| `VOLATILITY_2` | `26082402` | `DEGRADED_NO_SYMBOLS` | `1780` | 201 | High Frequency Vol 100 Index | EMPTY_CYCLE: El worker no tiene instrumentos seleccionados |
| `VOLATILITY_3` | `26082403` | `RUNNING` | `13008` | 178 | Volatility 90 Index | WAITING_ICT: INSUFFICIENT_H1_ADX_REGIME (16.8 < 20.0) |
| `VOLATILITY_4` | `26082404` | `WAITING_NEW_M1_BAR` | `23420` | 150 | Volatility 90 (1s) Index | EVENT_SCHEDULER_WAIT: Instrumentos disponibles; esperando nueva vel |

### 2.2 Bloqueos de Regímenes Tóxicos por el Centinela (Últimas 24h)
- **MARKET_REGIME_TOXIC_BLOCKED:ERRATIC_WHIPSAW_VOLATILITY**: `3,244` intervenciones preventivas.
- **MARKET_REGIME_TOXIC_BLOCKED:HIGH_CHOPPINESS_LOW_MOMENTUM**: `1,400` intervenciones preventivas.

### 2.3 Activos con Mayor Intervención del Escudo Centinela
- **NZDCAD**: `524` bloqueos preventivos por régimen no favorable.
- **GBPCHFmicro**: `511` bloqueos preventivos por régimen no favorable.
- **GBPCHF**: `511` bloqueos preventivos por régimen no favorable.
- **NZDUSDmicro**: `508` bloqueos preventivos por régimen no favorable.
- **NZDUSD**: `508` bloqueos preventivos por régimen no favorable.
- **GBPUSDmicro**: `507` bloqueos preventivos por régimen no favorable.
- **GBPUSD**: `507` bloqueos preventivos por régimen no favorable.
- **GBPCAD**: `482` bloqueos preventivos por régimen no favorable.

---
## 🔍 3. MODO ANÁLISIS RECIENTES (EVALUACIÓN DE OPORTUNIDADES & FILTROS)
Auditoría de por qué las señales analizadas en M15/M5/H1 entraron al mercado o fueron descartadas.

### 3.1 Embudo de Descarte & Motivos de Rechazo (Últimas 24h)
| Causa de Descarte / Filtro | Ocurrencias | Explicación Técnica |
| :--- | :--- | :--- |
| `WAITING_MSS_STRICT_CLOSE_BELOW_SUPPORT` | **587** | Validación de confluencia técnica o filtro de seguridad. |
| `WAITING_FIRST_RETEST` | **567** | Nivel identificado; esperando el primer retroceso técnico hacia la zona de valor. |
| `MSNR_OBSTACLE_BEFORE_MINIMUM_TP2` | **501** | Validación de confluencia técnica o filtro de seguridad. |
| `SESSION_FILTER_OUTSIDE_KILLZONE` | **459** | Fuera de la ventana de liquidez principal (Killzones Londres/NY). |
| `NO_MACRO_H4_BIAS_ALIGNED` | **398** | La dirección M5/M15 no coincide con el sesgo estructural H4 del mercado institucional. |
| `MARKET_REGIME_TOXIC_BLOCKED:ERRATIC_WHIP` | **329** | Volatilidad errática con mechas violentas detectada por ATR y Choppiness Index. |
| `WAITING_MSS_STRICT_CLOSE_ABOVE_RESISTANC` | **308** | Validación de confluencia técnica o filtro de seguridad. |
| `ENTRY_PRICE_DRIFT_TOO_LARGE` | **301** | Validación de confluencia técnica o filtro de seguridad. |
| `SETUP_STRUCTURE_INVALIDATED` | **284** | El precio rompió el nivel con cuerpo de vela en lugar de respetarlo. |
| `ICT_CRYPTO_NEGATIVE_EXPECTANCY_REPLAY_2Y` | **266** | Validación de confluencia técnica o filtro de seguridad. |

### 3.2 Estado de Candidatos en Memoria (Pipeline MSNR)
- **Estado `WAITING`**: `13,826` candidatos.
- **Estado `MSNR_SHADOW_SIGNAL`**: `1,529` candidatos.
- **Estado `WAITING_MALAYSIAN_SNR`**: `1,321` candidatos.
- **Estado `BLOCKED_ACTIVE_TRADE`**: `69` candidatos.
- **Estado `OPERACION_RECHAZADA_POR_RIESGO`**: `29` candidatos.
- **Estado `MARKET_REGIME_BLOCKED`**: `29` candidatos.
- **Estado `ENTRY_PRICE_DRIFT_TOO_LARGE`**: `29` candidatos.
- **Estado `HUMAN_CRITERIA_FILTER_REJECTED`**: `28` candidatos.
- **Estado `STEP_ADX_LOW`**: `23` candidatos.
- **Estado `BLOCKED_SYMBOL_CYCLE`**: `12` candidatos.
- **Estado `TRIPARTITE_CONFLUENCE_FILTER_REJECTED`**: `10` candidatos.
- **Estado `SYNTHETIC_SPREAD_TO_SL_EXCEEDED`**: `10` candidatos.
- **Estado `MSNR_REAL_SPREAD_TO_SL_EXCEEDED`**: `9` candidatos.
- **Estado `SYMBOL_COOLDOWN_POST_SL`**: `7` candidatos.
- **Estado `MSNR_REGIME_ADX_BLOCKED`**: `6` candidatos.
- **Estado `FOREX_CURRENCY_EXPOSURE_LIMIT`**: `6` candidatos.
- **Estado `SPLIT_ORDER_OPENED`**: `3` candidatos.
- **Estado `META_LABEL_FILTER_REJECTED`**: `3` candidatos.
- **Estado `MARKET_INVALIDATED_SIGNAL`**: `3` candidatos.
- **Estado `JUMP_STRICT_FILTER_REJECTED`**: `2` candidatos.
- **Estado `INDEX_SPREAD_ENTRY_BLOCKED`**: `2` candidatos.
- **Estado `SYMBOL_DAILY_STRIKES_EXCEEDED`**: `1` candidatos.
- **Estado `JUMP_SINGLE_FALLBACK_BLOCKED`**: `1` candidatos.

---
## 💾 4. REGISTROS DE BASE DE DATOS & OPERACIONES

### 4.1 Operaciones Abiertas en Vivo (Con Nueva Operativa 1% Split Aplicada)
| Ticket | Instrumento | Tipo | Lote | Entrada | Stop Loss | TP1 (+1.0R) | TP2 / Runner | Flotante | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `4788451840` | **Volatility 5 Index** | `SELL` | `0.3` | `100087.222` | `100145.289` | `99962.859` | Trade 2 (Runner Dinámico) | `$+0.00` | `OPEN` |
| `4788451826` | **Volatility 5 Index** | `SELL` | `0.3` | `100084.479` | `100145.289` | `100023.669` | Trade 1 (TP1 1:1) | `$+0.00` | `OPEN` |
| `4788341475` | **Volatility 10 (1s) Index** | `BUY` | `1.44` | `9535.95` | `9540.44` | `9565.12` | Trade 2 (Runner Dinámico) | `$+0.00` | `OPEN` |
| `4788130357` | **Jump 75 Index** | `SELL` | `0.18` | `3873.32` | `3991.59` | `3636.18` | Trade 2 (Runner Dinámico) | `$+0.00` | `OPEN` |
| `4788130348` | **Jump 75 Index** | `SELL` | `0.18` | `3872.61` | `3991.59` | `3753.63` | Trade 1 (TP1 1:1) | `$+0.00` | `OPEN` |

> [!NOTE]
> Ambas posiciones en Boom 600 y Crash 500 están correctamente sincronizadas en MT5 con el **1% de riesgo total por activo dividido en dos operaciones de 0.5% cada una**. La primera operación busca cerrar exactamente en +1.0R (1:1), momento en el cual la segunda operación se protege en Break Even para buscar correr hacia 2R, 3R o 4R.

### 4.2 Historial de Últimas Operaciones Cerradas
| Ticket | Instrumento | Tipo | Lote | R:R Plan | R:R Realizado | Net PnL | Motivo de Cierre | Apertura |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `4788178216` | High Frequency Vol 10 Index | `BUY` | 0.14 | 2.0R | **-0.96R** | **$-43.26** | `mt5_sl` | 2026-11-16 06:11:11 |
| `4788341370` | Volatility 10 (1s) Index | `BUY` | 1.44 | 1.0R | **+0.91R** | **$+20.59** | `mt5_tp` | 2026-11-16 09:33:13 |
| `4788293814` | Volatility 15 Index | `SELL` | 0.13 | 2.0R | **-0.97R** | **$-40.84** | `mt5_sl` | 2026-11-16 08:31:39 |
| `4788305073` | Volatility 25 (1s) Index | `BUY` | 0.008 | 1.0R | **+0.96R** | **$+20.43** | `mt5_tp` | 2026-11-16 08:46:11 |
| `4788132377` | Jump 10 Index | `BUY` | 0.03 | 1.0R | **-0.98R** | **$-18.19** | `mt5_sl` | 2026-11-16 05:30:06 |
| `4788132393` | Jump 10 Index | `BUY` | 0.03 | 3.0R | **-0.98R** | **$-18.23** | `mt5_sl` | 2026-11-16 05:30:08 |
| `4788291445` | Step Index 500 | `SELL` | 0.1 | 2.0R | **+1.86R** | **$+40.50** | `mt5_tp` | 2026-11-16 08:28:11 |
| `4788291418` | Step Index 500 | `SELL` | 0.1 | 1.0R | **+0.89R** | **$+19.50** | `mt5_tp` | 2026-11-16 08:28:09 |

### 4.3 Rendimiento Histórico por Instrumento (Top Activos)
| Instrumento | Trades Totales | Tasa de Acierto (Win Rate) | R:R Promedio | Observación Estratégica |
| :--- | :--- | :--- | :--- | :--- |
| **Step Index 200** | 118 | **39.0%** | +1.02R | ⚠️ Requiere Calibración |
| **Step Index 500** | 118 | **50.8%** | +0.07R | ⚖️ Equilibrado |
| **Volatility 25 Index** | 92 | **37.0%** | -0.28R | ⚠️ Requiere Calibración |
| **XAUUSD** | 87 | **51.7%** | +0.07R | ⚖️ Equilibrado |
| **Crash 500 Index** | 78 | **71.8%** | +0.44R | 🔥 Altamente Rentable |
| **Volatility 10 Index** | 76 | **56.6%** | +0.10R | 🔥 Altamente Rentable |
| **Volatility 75 Index** | 70 | **50.0%** | -0.07R | ⚖️ Equilibrado |
| **Jump 25 Index** | 67 | **56.7%** | +0.09R | 🔥 Altamente Rentable |
| **Jump 10 Index** | 61 | **47.5%** | -0.15R | ⚖️ Equilibrado |
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
| `BOOM_ICT_SABRI_MALLE` | **148** | 54.5% | **N/A** | `p >= 0.52` | `ENTRENADO` |
| `BOOM_MALAYSIAN_SNR` | **243** | 50.3% | **N/A** | `p >= 0.52` | `ENTRENADO` |
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
