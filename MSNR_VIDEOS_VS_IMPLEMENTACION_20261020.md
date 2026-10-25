# Malaysian SNR: vídeos frente a la implementación — 20 de octubre de 2026

Fuentes:
- Los 22 vídeos indicados por el usuario más la introducción del curso Alchemist (parte 1 de la lista de reproducción).
- Transcripciones ya descargadas el 13-oct en `storage/analysis/msnr_videos_20261013/captions`, unas 212.000 palabras.
- Los vídeos cortos en español se leyeron completos. De las sesiones largas en inglés (1-3 h cada una) se extrajeron
  los pasajes que definen reglas.
- Análisis textual: no sustituye ver los gráficos.
- Las cifras de acierto que dan los autores (55 %, "95 % de las veces"...) son afirmaciones suyas, sin validar.

Comparado con: `strategy/malaysian_snr/` (versión `msnr-v3.1-synthetics`), los ajustes vivos de la base (v28) y los
replays fieles de 2 años (`tools/replay_msnr_variants.py`).

## Lo que coincide

| Enseñanza | Implementación |
|---|---|
| Niveles en **cierres de vela** (gráfico de líneas), no en mechas | `av_levels` usa el cierre de la 1.ª vela; la mecha solo es límite de invalidación |
| A = vela alcista + bajista; V = bajista + alcista | Igual |
| RBS/SBR (el nivel roto cambia de función) | `ESC_1_ROLE_FLIP` (variante) |
| QM / QML / hombro izquierdo | `ESC_3_QUASIMODO`, `ESC_3_QMC`, `ESC_3_QM_EXTENDED` |
| Open-Close / Breaker Pair (2 velas del mismo color) | `ESC_1_BREAKER_PAIR`, `ESC_4_OPEN_CLOSE` |
| Fresh = nivel sin tocar; el primer toque es el más fuerte (Alchemist, Nestor) | `level_freshness` cuenta visitas: FRESH / TESTED_ONCE / CONSUMED |
| SL detrás del patrón o del extremo barrido | SL en el extremo de invalidación ± 0,15 ATR H1 |
| No entrar en la vela en formación | Solo velas cerradas (Fase 1) |

## Principales diferencias

| # | Vídeos | Implementación | Qué dicen nuestros datos |
|---|---|---|---|
| 1 | **Dirección por "storyline" en Mensual/Semanal/Diario**. Storyline diaria = el diario **rechaza** un nivel diario y **H4** rompe estructura o forma un QM; semanal = el semanal rechaza y el diario rompe. "Sin storyline no hay dirección". Nunca storylines en H4/H1. | Sin semanal ni mensual. El filtro D1 es un "sesgo estructural" y en sintéticos está **desactivado** (`enable_synthetic_daily_storyline_filter=False`). | No medido. Es la regla central del curso y la que más falta. |
| 2 | **Entrada de confirmación en H4/H1**: H4 cierra rechazando un nivel H4 y H1 rompe un nivel open-close. Alchemist pide **eliminar M1-M15**. Albert, MBA y Nestor sí refinan en M15/M5/M1. | Nivel en H1 y confirmación en **M15** (CRT sweep, rechazo de zona, fakeout), M5 opcional. | El replay sí distingue tipos de confirmación: `SNR_FAKEOUT_TRAP_SWEEP` es la peor (−0,29 / −0,05 R/t). |
| 3 | **Objetivo = siguiente nivel contrario del marco de la storyline**, con **parciales de ~70 %** en el primer objetivo y el resto corriendo. **BE** tras romper estructura o +50 pips. Ratios 1:3-1:10. | TP1 fijo a 1R y runner a 2R (hasta 4R con obstáculos), BE tras TP1. Es el contrato operativo del usuario. | Con nuestras señales, el objetivo del runner apenas cambia el resultado (1,5R / 2R / 3R ≈ igual). Bajar el TP1 a 0,5R sube el acierto al 67 % pero deja el R/t negativo. |
| 4 | **Obstáculos un marco por debajo de la storyline** (H4 para la diaria, diario para la semanal) | Obstáculos H1/D1; H4 en `observe` (`h4_obstacle_mode='off'` por defecto) | No medido con H4 activo. |
| 5 | **Refinar**: zona del marco mayor → nivel del marco menor dentro de ella (en ventas, refinar hacia arriba). Entrada limitada en el nivel refinado. | El nivel se toma del propio H1; no hay jerarquía de zonas. | La **entrada limitada empeora MSNR** (+0,120 → +0,083/+0,095 R/t con los 30 activos y el filtro de régimen). |
| 6 | **Confluencias**: línea de tendencia de "ruptura y retest" que se cruza con el nivel; liquidez de sesión (máximo/mínimo de Asia, día y semana previos); horario (killzones de Londres y Nueva York, nunca Asia; cierres de H4). | Sin líneas de tendencia (hay confluencia EMA H1). Sesiones solo en mercados reales; los sintéticos operan 24/7. `track_session_liquidity` existe. | No medido. En sintéticos no hay sesiones reales, pero sí cierres de H4. |
| 7 | **MBA**: el punto de interés debe tener un **desequilibrio (FVG/imbalance) sin rellenar**; evitar zonas con **exceso de liquidez** (máximos/mínimos iguales, acumulaciones); operar solo **a favor** del rango fuerte (strong high → strong low). | Sin requisito de imbalance ni de exceso de liquidez. | No medido. |
| 8 | **Definición de Fresh (Albert)**: "fresh" = el precio cruza el nivel con cuerpo; "no fresh" = lo toca con mecha y vuelve (barrido), señal de giro hacia el lado contrario. | Fresh = nivel sin visitar. La idea de Albert se parece a la confirmación fakeout-trap. | La confirmación fakeout-trap es la peor del replay. |
| 9 | **A/V sin envolvente**: Alchemist y Nestor marcan A/V con cualquier par alcista-bajista; Albert exige envolvente. | Por defecto **envolvente** (`definition='engulfing'`); `body_turns` disponible. | No medido. Con `body_turns` saldrían más niveles y por tanto más trades. |
| 10 | **Riesgo escalonado**: entradas de riesgo alto 0,3 % repartidas entre varias zonas; riesgo completo solo con confirmación. | 1 % fijo en 2 patas (contrato). | — |
| 11 | Activos: oro, Nasdaq, EURUSD. **No hablan de sintéticos.** | Solo sintéticos: en mercados reales el replay fue negativo (−0,157 / −0,079 R/t). | El replay en mercados reales no respalda el método. |

### Ajustes vivos de la base frente a la referencia del 13-oct
El análisis del 13-oct dejó Breaker Pair y Pinbar en **observación**, porque no había evidencia: 2-3 trades en 2 semanas.
En la base viva (v28) están en **live** (`breaker_pair_mode=live`, `retest_pinbar_mode=live`).
La ablación de 2 años para medirlos (A/B/C) se interrumpió y está pendiente.

## Qué se puede medir con el replay fiel (por orden de interés)

1. **Storyline D1 con confirmación H4** (diferencia 1) como filtro de dirección en sintéticos.
   - Regla causal: la última vela D1 cerrada rechazó un nivel A/V/open-close diario y H4 rompió estructura en ese
     sentido. Comparar R/t y acierto con y sin ella, por año.
2. **Confirmación H4→H1 del curso** (diferencia 2) como escenario nuevo: H4 cierra rechazando un nivel H4 y H1 rompe
   un open-close. Su frecuencia y su R/t frente a las confirmaciones M15 actuales.
3. **A/V `body_turns` frente a envolvente** (diferencia 9): más niveles y más trades. Mantener solo si no baja el R/t.
4. **Obstáculos H4 en `apply`** (diferencia 4) y **requisito de imbalance** (diferencia 7).
5. Terminar la **ablación de Breaker Pair y Pinbar en live** (ajustes de la base).

Criterio, como siempre: positivo en ambos años, test de azar y, si la evidencia es justa, prueba demo con criterio fijado.

## Resultado de la medición (20-oct-2026, `tools/research_msnr_storyline_h4h1.py`)

| Regla de los vídeos | Resultado en 37 sintéticos, 2 años | Decisión |
|---|---|---|
| Storyline D1+H4 como filtro de dirección | A favor +0,015 R/t (y0 +0,031 / y1 −0,000); en contra +0,102; sin storyline −0,024 | **Descartada**: a favor no es mejor de forma estable |
| Confirmación H4→H1 como escenario nuevo | 18.595 operaciones, **+0,029 R/t**, t = 3,75, y0 +0,026 / y1 +0,031, 8 de 9 trimestres positivos | **Prometedora**: implementarla en prueba demo |
