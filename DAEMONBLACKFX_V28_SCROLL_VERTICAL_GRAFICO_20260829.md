# DaemonBlackFx v28 · Scroll vertical del gráfico de auditoría

## Objetivo
La interacción principal del gráfico de auditoría pasa del desplazamiento horizontal a una manipulación vertical de la escala de precios.

## Interacciones
- Rueda del mouse arriba/abajo: amplía o reduce la escala vertical (eje Y), centrada aproximadamente en la zona de precio bajo el cursor.
- Arrastre vertical: desplaza la escala de precios hacia arriba o hacia abajo.
- Ctrl + rueda: conserva un zoom secundario del eje temporal/velas cuando se necesita inspeccionar menos o más velas.
- Doble clic: restaura autoescala, posición vertical y ventana temporal reciente.
- Botones + / -: amplían o reducen la escala vertical.
- Botón Autoescala: vuelve a Y 1.0x, X 1.0x, sin desplazamiento vertical y a las velas recientes.

## Indicador
La barra muestra dos escalas separadas:
- Y = escala vertical de precios.
- X = densidad/zoom temporal de velas.

Ejemplo: `Y 3.2× · X 1.0×`.

## Alcance
No cambia la estrategia, las confirmaciones mínimas del 80%, el riesgo, TP1/RUNNER, Break Even, la persistencia SQLAlchemy ni las temporalidades operativas. Es exclusivamente una mejora del visor de auditoría.

## Validación
- 18 pruebas específicas del dashboard aprobadas.
- 197 pruebas no-MT5 aprobadas.
- JavaScript principal validado con `node --check`.
