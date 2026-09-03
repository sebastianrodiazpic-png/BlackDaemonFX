# DaemonBlackFx v62 — Patrones chartistas + auditoría persistente SMC

## Objetivo
Agregar patrones chartistas como confluencia a la estrategia Smart Money original,
sin reemplazar sus gates estructurales.

## Patrones de referencia incorporados
Basados en el PDF entregado por el usuario:
- Double/Triple Top y Bottom.
- Head & Shoulders / Inverted H&S.
- Ascending, Descending y Symmetrical Triangle.
- Broadening Triangle.
- Falling/Rising Wedge y broadening wedges.
- Bullish/Bearish Flag.
- Bullish/Bearish Rectangle.
- Cup & Handle / Rounding Bottom.
- El detector conserva soporte para clasificación/extensión de pennants y diamantes
  en su vocabulario de auditoría.

## Política de trading
- Por defecto es una confluencia SOFT.
- No sustituye H1 trend, liquidity sweep, BOS/CHOCH, Order Block,
  Premium/Discount, retest ni gates M5.
- Patrón alineado y fuerza >= 72% suma hasta 8 puntos al raw score.
- El score visible sigue limitado a 100.
- La ausencia de patrón NO reduce el porcentaje de confirmación legacy.
- Existe `require_chart_pattern=False` para mantener compatibilidad; puede activarse
  más adelante tras medir resultados.

## Auditoría
Cada trade persiste en `trade_visual_audits.entry_context_json`:
- decisión;
- score y porcentaje;
- confirmaciones aprobadas;
- confirmaciones faltantes;
- fallos críticos;
- diccionario completo de confirmaciones;
- divergencia;
- armónico;
- Doji H1;
- patrón chartista, dirección, fuerza, bonus, conflicto;
- anchors temporales/precio utilizados para visualizar el patrón.

El `entry_context` continúa siendo inmutable tras la primera captura.

## Dashboard
La auditoría visual dibuja:
- etiqueta del patrón;
- puntos/anchors reconocidos;
- líneas de evidencia;
- nombre y fuerza en el panel “Tesis al abrir”.

## Cuenta activa
`/account` reconstruye las confirmaciones desde SQLAlchemy y muestra una columna
“Confirmaciones persistentes”, incluyendo el detalle técnico. Esto permanece
disponible después de cerrar el trade y reiniciar el daemon.
