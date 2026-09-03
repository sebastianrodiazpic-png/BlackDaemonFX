# DaemonBlackFx v26 — Gráfico interactivo multi-timeframe

## Objetivo
Mejorar exclusivamente el área gráfica de la auditoría de posiciones abiertas, sin ampliar/minimizar el panel completo de auditoría y sin modificar la lógica de trading.

## Cambios
- Pantalla completa aplicada únicamente al gráfico (`chartViewportShell`).
- Minimizar/restaurar aplicado únicamente al gráfico.
- Navegación de temporalidades: M1, M5, M15 y H1.
- Zoom mediante rueda del mouse y botones + / -.
- Desplazamiento horizontal mediante arrastre del mouse/puntero.
- Botón `Últimas` para regresar a las velas más recientes.
- Estado del zoom y temporalidad conservado mientras la posición siga seleccionada.
- Capas SMC se redibujan según la temporalidad seleccionada.
- M5/M15/H1 usan las capas publicadas por el pipeline SMC cuando están disponibles.
- M1 se etiqueta como contexto SMC auxiliar y no interviene en las reglas de entrada.
- El navegador nunca consulta MT5 directamente; el daemon publica snapshots de M1/M5/M15/H1 desde el mismo hilo cooperativo.
- Compatibilidad hacia atrás: el snapshot principal conserva M5 en los campos existentes y añade `timeframes` y `available_timeframes`.

## Seguridad funcional
No se modificaron:
- mínimo de confirmaciones (80%),
- sizing/riesgo,
- split TP1/RUNNER,
- Break Even,
- reglas SMC de entrada,
- reconciliación MT5/SQLAlchemy,
- Cuenta activa y journal histórico.

## Uso
1. Abrir una posición en `Posiciones abiertas` y pulsar `Ver gráfico`.
2. Seleccionar M1, M5, M15 o H1.
3. Usar la rueda para acercar/alejar.
4. Arrastrar el gráfico para revisar velas anteriores.
5. Pulsar `Últimas` para volver al extremo derecho.
6. Pulsar `Pantalla completa` para ampliar sólo el gráfico.
7. Pulsar `Minimizar` para ocultar únicamente el gráfico, manteniendo visible la auditoría.

## Validación
- `tests/test_realtime_dashboard.py`: 18 passed.
- Regresión no-MT5 disponible: 197 passed.
