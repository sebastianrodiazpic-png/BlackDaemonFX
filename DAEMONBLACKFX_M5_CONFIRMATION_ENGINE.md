# DaemonBlackFx – Motor de Confirmación M5

## Objetivo
Evitar entradas por un simple toque del Order Block. Cada operación conserva un diagnóstico reproducible.

## Confirmaciones implementadas
1. Contexto H1 alineado.
2. Setup M15 válido.
3. Liquidity sweep.
4. CHOCH/BOS M15.
5. Premium/Discount.
6. Order Block fresco y con máximo de toques configurable.
7. Retest del Order Block.
8. Rejection wick direccional.
9. Vela de displacement con cuerpo y rango mínimo.
10. Micro BOS/CHOCH M5 contra las dos velas previas.
11. Momentum opcional.
12. Modo de confirmación: `inside`, `midpoint` o `break_ob`.
13. Score y grade: A+, A, B, REJECT.

## Configuración DEMO inicial
- Score mínimo: 80.
- Rejection: obligatorio.
- Displacement: obligatorio.
- Micro confirmation: obligatoria.
- Momentum: opcional para no sobre-filtrar al inicio.
- Body ratio mínimo: 0.60.
- Rejection wick ratio: 0.30.
- Displacement: rango >= 1.20x promedio de 20 velas.
- Máximo de toques del OB: 1.
- Confirmación: cierre en/por encima del midpoint para LONG; en/por debajo para SHORT.
- Señal M5 máxima: 2 velas.

## Datos guardados en la señal
`trade_score`, `trade_grade`, `confirmation_valid`, `rejection_reasons`, `ob_touches`, `ob_fresh`, ratios de cuerpo/mechas y detalle completo de confirmaciones.
