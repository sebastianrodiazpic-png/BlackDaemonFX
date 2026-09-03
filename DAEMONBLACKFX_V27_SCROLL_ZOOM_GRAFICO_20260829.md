# DaemonBlackFx v27 — Scroll/zoom avanzado del gráfico de auditoría

## Objetivo
Mejorar la inspección visual del gráfico de auditoría sin modificar la lógica de trading.

## Cambios
- Scroll hacia arriba sobre el gráfico: acerca el zoom.
- Scroll hacia abajo: aleja el zoom.
- El zoom se centra en la zona/vela ubicada bajo el cursor, evitando saltos hacia el extremo derecho.
- Profundidad máxima ampliada hasta 12x.
- La ventana mínima puede llegar a 8 velas para inspección fina.
- Shift + scroll: navegación horizontal por el histórico visible.
- Arrastre con mouse/puntero: navegación horizontal.
- Doble clic: restaura la vista a las velas recientes y zoom 1x.
- Indicador visible `Zoom X.X×` en la barra del gráfico.
- Los controles +, -, Últimas, pantalla completa y temporalidades M1/M5/M15/H1 se conservan.

## Seguridad
Este cambio afecta exclusivamente la visualización/auditoría. No modifica condiciones SMC, umbral de 80%, riesgo, ejecución, Break Even ni persistencia.

## Validación
- Tests dashboard: 18 passed.
- Regresión no-MT5: 197 passed.
