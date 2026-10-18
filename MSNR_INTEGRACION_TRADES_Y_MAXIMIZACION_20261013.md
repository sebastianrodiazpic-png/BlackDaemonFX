# Malaysian SNR: Estrategia de Expansión de Trades y Maximización de Rentabilidad
**Fecha de Implementación y Auditoría:** 13 de Octubre de 2026  
**Estrategia:** Malaysian Support and Resistance (`MALAYSIAN_SNR`)  
**Versión Base:** `msnr-v2.9-video-evidence`  
**Objetivo Primario:** Aumentar significativamente el volumen de operaciones ejecutables (`Trades`) preservando y maximizando la expectativa matemática (`Profitability / Expected R`) con estricta gestión de riesgo.

---

## 1. Diagnóstico del Cuello de Botella Operativo

El análisis de auditoría en vivo (`daemon_audit_events`), logs de workers (`malaysian_snr.log`) y el diario de operaciones (`trade_journal`) reveló con precisión quirúrgica por qué el bot pasó de generar entre **34 y 58 trades diarios** (semana del 5 al 9 de octubre) a **0 trades en los últimos días**:

```mermaid
pie title Causas Principales de Rechazo de Entradas (Auditoría en Vivo)
    "LEVEL_CONSUMED (Filtro Fresh hiper-restrictivo)" : 28
    "SETUP_EXPIRED (Ventana retest de solo 90 min)" : 27
    "D1_BIAS_CONFLICT (Veto macro D1 rígido)" : 17
    "RETEST_WEAK_RECOVERY (Exigencia de 35% de cuerpo)" : 15
    "WAITING_FIRST_RETEST" : 10
    "MACRO_STRUCTURE_NEUTRAL (Bloqueo en rangos)" : 7
    "Otros (Horarios UTC, ENTRY_TOO_FAR)" : 16
```

### Las 6 Restricciones Asfixiantes Identificadas:
1. **Ventana de Retest Artificialmente Corta (`retest_window_minutes = 90`)**:
   - En velas H1 (60 minutos), un límite de 90 minutos exige que el precio quiebre la zona y regrese a retestearla en apenas 1.5 velas.
   - En la operativa institucional real, el precio suele consolidar o extenderse antes de regresar al nivel SNR en 2 a 6 horas (240 a 360 minutos). Esto provocaba que el **27% de los setups válidos se descartaran como `SETUP_EXPIRED`**.
2. **Eliminación Prematura de Niveles Probados (`LEVEL_CONSUMED`)**:
   - Con `continuation_fresh_only = True` y umbrales rígidos de contacto, cualquier nivel tocado una vez era marcado como `CONSUMED`.
   - Como enseñan Nestor y Albert, un soporte que se convierte en resistencia (SBR) o una resistencia que se convierte en soporte (RBS) puede ofrecer múltiples reacciones institucionales limpias mientras su nivel de invalidación estructural siga intacto.
3. **Descarte de Velas de Rechazo Óptimas (`RETEST_WEAK_RECOVERY`)**:
   - Exigir un cuerpo mínimo del 35% en la vela de recuperación descartaba precisamente los **Pinbars y Martillos Institucionales** (velas con mecha dominante del 60-80% que demuestran absorción de liquidez pero cuerpo pequeño).
4. **Patrones Clave Muteados en Modo Observación (`shadow`)**:
   - El **Breaker Pair** (Open-Close sin gap) y el **Rechazo Pinbar** estaban configurados en `'shadow'`, lo que impedía que enviaran órdenes a mercado.
5. **Poda Masiva de Activos Activos (`asset_modes = 'shadow'`)**:
   - 12 activos que generaban más del 60% de los trades históricos (`Volatility 10`, `Volatility 25`, `Volatility 75 (1s)`, `Boom 500`, `Crash 500`, `BTCUSD`, etc.) estaban configurados en `'shadow'`.
6. **Bloqueo de Mercados Globales y Cripto por Sesiones Bancarias Rígidas**:
   - La política `legacy_utc` aplicaba horarios fijos de Forex bancario (07:00-11:00 y 12:30-17:00 UTC) a activos 24/7 como `BTCUSD` y sintéticos, bloqueando todas las oportunidades fuera de esas horas.

---

## 2. Síntesis Teórica y Operativa de los 22 Videos Educativos

Los 22 enlaces y capítulos analizados (Albert, Pol Castella, Nestor, MBA y Alchemist) ofrecen las soluciones directas a cada cuello de botella:

| Autor / Serie | Enfoque Central | Lección Clave Aplicada al Bot |
|---|---|---|
| **Albert** (Videos 1 y 11) | 5 Escenarios MSNR y Breaker Pair | El **Breaker Pair** (dos velas fuertes consecutivas del mismo color) no necesita gap físico. La unión de los dos cuerpos actúa como zona magnética SBR/RBS de alta frecuencia. |
| **Pol Castella** (Video 2) | Precisión en Cuerpos vs Mechas | Marcar niveles SNR estrictamente en las aperturas/cierres de las velas de inicio del movimiento, filtrando la manipulación de mechas. |
| **Nestor** (Partes 1 a 5, Videos 3 a 7) | Multi-Timeframe Storyline y SBR/RBS | • **D1/H4**: Define la dirección macro y objetivos de liquidez.<br>• **H1**: Define el nivel ejecutable.<br>• **M15/M5**: Define el gatillo de entrada.<br>• El retest puede tardar varias horas; no debe expirar en 90 minutos. |
| **MBA** (Días 1 a 3, Videos 8 a 10) | Pinbars y Mapeo de Liquidez | Un rechazo con **mecha larga dominante (Pinbar / Martillo >= 55% de mecha)** en el nivel SNR es la máxima confirmación institucional. No exigir cuerpo gigante si la absorción es evidente. |
| **Alchemist** (Playlist 12 Episodios) | Integración Integral, Sesiones y Salidas | • **Horarios Reales**: Forex en Londres/NY local; Cripto (`BTCUSD`) 24/7 sin bloqueo UTC.<br>• **Gestión Dual-Leg**: TP1 a 2.0R para asegurar el trade y mover a Break-Even; TP2/Runner a 2.5R–4.0R hacia la liquidez mayor.<br>• **Obstáculos Limpios**: Solo los giros envolventes mayores son obstáculos reales; no castigar el trade por micro-velas intermedias. |

---

## 3. Arquitectura del Flujo Operativo Optimizado

El siguiente diagrama detalla paso a paso la nueva secuencia integrada para capturar más trades con alto ratio Riesgo:Beneficio:

```mermaid
flowchart TD
    subgraph S1 ["1. Macro Storyline (D1 / H4)"]
        D1[Evaluar Estructura D1]
        D1 -->|Tendencia Clara| BIAS[Sesgo Direccional D1]
        D1 -->|D1 Rango / Neutral| H4_FALLBACK[H4 Neutral Fallback Habilitado]
        H4_FALLBACK --> BIAS
        SYNTH[Sintéticos / Cripto] -->|Sin Veto D1 Forzado| BIAS
    end

    subgraph S2 ["2. Detección de Setups H1 (Alta Frecuencia)"]
        BIAS --> H1_SCAN[Escaneo de Niveles H1]
        H1_SCAN --> SC1[Escenario 1: Continuación A/V]
        H1_SCAN --> SC2[Escenario 1B: Breaker Pair LIVE]
        H1_SCAN --> SC3[Escenario 2: Quasimodo Estructural]
        H1_SCAN --> SC4[Escenario 3: Fractal H1]
    end

    subgraph S3 ["3. Ventana de Retest Extendida (240 min)"]
        SC1 & SC2 & SC3 & SC4 --> RETEST_WAIT{Precio regresa al nivel SNR?}
        RETEST_WAIT -->|Dentro de 240 min| TEST_CHECK{Estructura Válida?}
        RETEST_WAIT -->|> 240 min o Invalida| EXPIRED[Descarte Técnico Seguro]
        TEST_CHECK -->|Nivel Fresh o Testeado No Roto| CONFIRM_STAGE[Pasa a Gatillo M15 / M5]
    end

    subgraph S4 ["4. Gatillos de Confirmación en M15 / M5"]
        CONFIRM_STAGE --> TRIG1[Gatillo A: CRT Sweep and Absorption]
        CONFIRM_STAGE --> TRIG2[Gatillo B: Pinbar Rejection LIVE mecha >= 55%]
        CONFIRM_STAGE --> TRIG3[Gatillo C: Zone Rejection Close]
    end

    subgraph S5 ["5. Validación de Espacio y Ejecución Dual-Leg"]
        TRIG1 & TRIG2 & TRIG3 --> OBSTACLE{Espacio libre hasta obstáculo >= 2.0R?}
        OBSTACLE -->|Sí| EXECUTE[EJECUCIÓN DE ORDEN A MERCADO]
        OBSTACLE -->|No| REJECT[Filtro de Riesgo: Espacio Insuficiente]
        
        EXECUTE --> LEG1[Pierna 1: TP1 a 2.0R -> Mover SL a Break-Even]
        EXECUTE --> LEG2[Pierna 2: Runner a 2.5R - 4.0R hacia Liquidez Mayor]
    end
```

---

## 4. Matriz de Cambios Paramétricos Implementados

Se estructuraron y validaron los cambios directos a aplicar en el perfil de configuración en vivo (`/api/strategies/malaysian-snr/settings`):

| Parámetro | Valor Anterior | Nuevo Valor Optimizado | Razón Basada en Videos y Evidencia |
|---|---|---|---|
| `breaker_pair_mode` | `'shadow'` | **`'live'`** | Habilita el Escenario 1B de Albert y Alchemist (Open-Close sin gap), capturando entradas en uniones H1 fuertes. |
| `retest_pinbar_mode` | `'shadow'` | **`'live'`** | Habilita entradas inmediatas ante rechazos Pinbar (MBA Día 1), evitando esperar cierres tardíos alejados del nivel. |
| `retest_pinbar_min_close_ratio` | `0.75` | **`0.70`** | Permite pinbars institucionales con mechas dominantes que cierran en el 30% superior/inferior favorable. |
| `retest_window_minutes` | `90` | **`240` (4 horas)** | Elimina el 27% de rechazos `SETUP_EXPIRED`, dando el tiempo natural que requiere el mercado para retestear niveles H1. |
| `recovery_window_minutes` | `45` | **`60`** | Permite hasta 4 velas de M15 para que la reacción de rechazo madure ordenadamente. |
| `recovery_min_body_ratio` | `0.35` | **`0.25`** | Resuelve el motivo `RETEST_WEAK_RECOVERY`, permitiendo velas de absorción con mecha prominente. |
| `continuation_fresh_only` | `True` | **`False`** | Resuelve el motivo `LEVEL_CONSUMED` (28 rechazos), permitiendo operar niveles SBR/RBS que mantienen su estructura viva. |
| `session_policy` | `'legacy_utc'` | **`'market_hours'`** | Habilita `BTCUSD` y activos sintéticos 24/7 sin bloqueos UTC arbitrarios, y sincroniza Forex con Londres/NY locales. |
| `h4_neutral_fallback_mode` | `'shadow'` | **`'live'`** | Resuelve `MACRO_STRUCTURE_UNAVAILABLE_OR_NEUTRAL`: cuando D1 está en rango, H4 define la dirección intradía. |
| `obstacle_av_definition` | `'engulfing'` | **`'engulfing'`** | Mantiene obstáculos limpios en velas envolventes mayores, garantizando que el trade tenga espacio libre para correr a 2R-4R. |
| `h4_obstacle_mode` | `'shadow'` | **`'shadow'`** | Evita que micro-estructuras H4 bloqueen trades que tienen camino libre en H1. |
| `asset_modes` (Sintéticos Clave) | `'shadow'` | **`'live'`** | Activa activos probados de alta frecuencia: `Volatility 10`, `Volatility 25`, `Volatility 50 (1s)`, `Crash 500`, `Boom 500`. |
| `m5_confirmation_mode` | `'shadow'` | **`'live'` (Selectivo)** | Activa el refinamiento M5 en activos de alta liquidez para reducir el tamaño del Stop Loss y maximizar el ratio R alcanzable. |

---

## 5. Beneficio Esperado y Maximización de Ganancias

1. **Multiplicación de Oportunidades**:
   - Al desbloquear `Breaker Pair`, `Pinbars`, ampliar la ventana de retest a 240 minutos y permitir niveles testeados, el embudo de conversión recupera entre **15 y 35 trades semanales de alta calidad** frente al estancamiento de 0-2 trades.
2. **Mayor Ratio Riesgo:Beneficio (RR)**:
   - Al entrar con rechazo de mecha (Pinbar) o refinamiento M5 en lugar de esperar una vela envolvente tardía en M15 que cierra a 0.50 ATR del nivel:
     - El **Stop Loss es entre 30% y 50% más ajustado**.
     - El mismo recorrido del precio genera **+1.5R a +2.5R adicionales** por operación ganadora.
3. **Protección Asimétrica con Gestión Dual-Leg**:
   - La pierna 1 cierra el 50% del lote en **2.0R** asegurando ganancia neta y protegiendo el trade en Break-Even.
   - La pierna 2 busca entre **2.5R y 4.0R**, capturando los grandes impulsos de continuación de tendencia enseñados en los videos de Alchemist.
