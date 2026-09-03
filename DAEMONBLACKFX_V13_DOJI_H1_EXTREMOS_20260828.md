# DaemonBlackFx v13 - Doji H1 en zonas extremas

## Objetivo

Añadir los Dojis de H1 como confluencia opcional para reforzar setups SMC existentes. El Doji no abre operaciones por sí solo, no es una condición crítica y su ausencia no bloquea una entrada válida.

## Regla de detección

El detector revisa las velas H1 cerradas más recientes (por defecto hasta 2 velas de antigüedad) y exige:

- Cuerpo del Doji <= 10% del rango total de la vela.
- Ubicación dentro del 15% extremo del rango estructural H1 calculado sobre 100 velas.
- Para BUY: zona Discount/extremo inferior y mecha inferior >= 35% del rango de la vela.
- Para SELL: zona Premium/extremo superior y mecha superior >= 35% del rango de la vela.

Un Doji situado en Equilibrium o en el centro del rango no confirma nada.

## Tipos de evidencia

- `DOJI_H1_EXTREMO_ALCISTA`
- `DOJI_LIBELULA_H1_EXTREMO_ALCISTA`
- `DOJI_H1_EXTREMO_BAJISTA`
- `DOJI_LAPIDA_H1_EXTREMO_BAJISTA`

## Integración con la estrategia

Cuando existe una señal M5 ya confirmada y el Doji H1 es compatible con su dirección:

- suma +5 puntos al `trade_score` (con tope 100),
- se registra en `confirmations` como `h1_extreme_doji_confirmation`,
- NO se añade al denominador del porcentaje adaptativo,
- NO se añade a condiciones críticas,
- NO existe `require_h1_doji`.

Por lo tanto, el 75% adaptativo mantiene exactamente la misma lógica previa.

## Ejemplo BUY

Contexto esperado:

1. Precio llega al extremo inferior/Discount de H1.
2. Aparece Doji H1 con cuerpo pequeño y mecha inferior marcada.
3. SMC M15 mantiene sweep + CHOCH/BOS + OB + zona correcta.
4. M5 confirma retest/rechazo/microestructura.
5. El Doji suma confluencia y calidad, pero no reemplaza ninguna de las condiciones SMC.

## Ejemplo SELL

Mismo flujo, invertido: extremo superior/Premium + Doji con rechazo superior + confirmaciones SMC/M5 bajistas.

## Auditoría

La evidencia se guarda junto al trade:

- `h1_doji_confirmation`
- `h1_doji_type`
- `h1_doji_time`
- `h1_doji_zone`
- `h1_doji_reason`
- ratios de cuerpo y mechas

También aparece en consola, dashboard y XLSX explicable.

## Parámetros por defecto

```python
h1_doji_enabled = True
h1_doji_lookback_candles = 100
h1_doji_max_age_candles = 2
h1_doji_max_body_ratio = 0.10
h1_doji_extreme_fraction = 0.15
h1_doji_min_rejection_wick_ratio = 0.35
h1_doji_bonus_points = 5.0
```

Estos valores son deliberadamente conservadores para evitar tratar cualquier vela de cuerpo pequeño como señal de reversión.
