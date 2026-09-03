# DaemonBlackFx v30 — Paneo sincronizado tipo TradingView

## Objetivo
Mejorar la auditoría visual de posiciones abiertas para que el gráfico se desplace como una escena única. Al arrastrar el gráfico, las velas y todas las capas de auditoría se recalculan con el mismo viewport.

## Interacción
- Arrastre horizontal: navega hacia velas anteriores o recientes.
- Arrastre vertical: desplaza la escala de precios.
- Arrastre diagonal: combina ambos movimientos en una sola interacción.
- Scroll: conserva el zoom vertical de precios solicitado en v28.
- Ctrl + scroll: zoom temporal sobre las velas.
- Doble clic / Autoescala: vuelve a la vista reciente y restablece X/Y.
- M1, M5, M15 y H1 continúan disponibles.

## Capas sincronizadas
El mismo viewport se aplica a velas, Entry, SL, TP, BE, HH/HL/LH/LL, CHOCH/BOS, BSL/SSL, sweeps, Order Blocks, FVG, Premium/Discount, Equilibrium, RSI y confluencias.

Los eventos puntuales fuera del rango temporal visible ya no se fijan artificialmente al borde del gráfico. Las zonas persistentes como OB/FVG y niveles de liquidez sí pueden continuar visibles al entrar desde un origen anterior al viewport.

## Alcance
Cambio exclusivo del dashboard/auditoría. No modifica reglas SMC, mínimo de confirmaciones, riesgo, ejecución, TP1/RUNNER, Break Even ni persistencia SQLAlchemy.
