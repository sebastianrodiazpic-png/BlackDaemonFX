# Auditoría externa MT5 y estrategia adicional de Cuartos — 2026-09-22

## Auditoría, sin gestión de órdenes

La propiedad de una posición sigue gobernando exclusivamente su gestión. `managed_by_daemon=False` excluye expresamente de la gestión, incluso si su magic coincide. Un observador asignado al worker BOOM (activo normalmente 24/7) importa y observa posiciones externas. Esto evita que cada worker repita la misma auditoría. No crea otro proceso. Si BOOM está detenido/deshabilitado, este seguimiento no se ejecuta.

El observador consulta también el origen MT5_EXTERNAL, sincroniza cierres y guarda primera observación inmutable y snapshots posteriores. La página de auditoría consulta el origen real del trade y muestra evidencia y elegibilidad. Conserva velas M5 cerradas, dirección, precio observado, rango, ATR, SL/TP registrados y fechas. Los errores del proveedor generan MT5_OBSERVATION_ERROR. No infiere patrones SMC que no calculó.

La primera observación NO sustituye el momento original de entrada ni un gráfico de entrada ausente. El gráfico posterior muestra las velas observadas; los datos originales siguen en el journal. Los trades que ya estaban cerrados antes del despliegue no se reconstruyen retrospectivamente ni adquieren una captura ficticia. Reconstruirlos requeriría un proceso histórico separado y etiquetado explícitamente como tal.

La importación del observador excluye los magics conocidos de los otros workers para no adjudicarse fills del daemon pendientes de persistencia. Si se usan magics personalizados, revisar esa lista. Cada posición externa conserva su origen y su marca de no gestionada.

## MetaEtiquetado y procedencia

- ENTRY_CAPTURE: vector capturado por el motor al evaluar una nueva entrada. Entrena su estrategia original una vez cerrado el setup completo.
- FIRST_OBSERVATION: observación posterior de una posición externa. Su dataset separado MT5_OBSERVATION empieza en esa fecha y aprende el movimiento de precio hasta el cierre, dividido por la distancia al SL observada. No usa como etiqueta el resultado desde la entrada original.
- NO_ENTRY_EVIDENCE: historial sin evidencia contemporánea ni primera observación. Solo estadística; no se inventan señales.

Los modelos MT5_OBSERVATION son candidatos separados del modelo SMC, con la misma validación temporal y mínimo configurado. Necesitan SL válido en el lado de riesgo al observar, precio de salida, fecha posterior al inicio y ambas clases. Su resultado es variación de precio, no PnL neto después de comisiones/swap. Ningún candidato se promociona automáticamente. La tabla del dashboard muestra elegibilidad de los últimos 100 registros, incluidos setups esperando cierre completo.

## GOLD_QUARTERS

Estrategia independiente adicional, dentro del worker GOLD, exclusivamente para oro. SMC tiene prioridad; si no produce una señal válida, se evalúa Cuartos. La señal se registra como GOLD_QUARTERS y los intentos generan GOLD_QUARTERS_EVALUATED. No se incrementa el riesgo configurado del worker.

Reglas iniciales elegidas:
1. Niveles cada 25 unidades de precio, tolerancia 2 (configuración compartida con la confluencia existente).
2. Primera vela M5 cerrada: mecha favorable de al menos 45% de su rango, próxima al cuarto, y cierre al lado favorable.
3. Siguiente vela M5 cerrada: cuerpo en la dirección de entrada y cierre más allá del extremo de la vela de rechazo. Se exige continuidad de cinco minutos y datos recientes.
4. H1 solo ubicación: compra en discount, venta en premium; no veto de tendencia H1. Rango de hasta 100 velas cerradas (mínimo 20 disponibles).
5. SL detrás del rechazo con margen 0,10 ATR. TP en el cuarto siguiente. Se rechaza si el RR no alcanza el mínimo, también recalculándolo al precio ejecutable con el stop normalizado.
6. Una sola posición, sin TP1/runner ni fallback de objetivos. El monitor de break-even omite GOLD_QUARTERS: mantiene SL/TP definidos. Persisten los controles de riesgo y protección técnica del motor, incluidos los controles posteriores al fill.

Ejemplo conceptual: rechazo alcista cerca de 4.300, confirmación M5 en discount H1 y TP 4.325; solo entra si el SL y el precio ejecutable dejan el RR mínimo. Venta simétrica desde un cuarto hacia el siguiente inferior, en premium H1.

`gold_quarters_strategy_enabled=True` habilita la alternativa; la confluencia de cuartos original de SMC no se cambia.

## Activación y pruebas

Se requiere reiniciar los procesos para cargar esta versión: BOOM para observación externa, GOLD para Cuartos y dashboard para la nueva información. No se reiniciaron workers ni se abrieron/modificaron operaciones reales durante el trabajo.

48 pruebas de almacenamiento, auditoría, aprendizaje y Cuartos aprobadas; sintaxis JavaScript del dashboard y auditoría verificada. Pruebas incluyen persistencia inmutable, separación de permisos, resultado posterior a la observación, BUY/SELL con velas cerradas y ejecución simulada con un único TP fijo.
