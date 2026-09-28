# SMC: riesgo, setups únicos y variantes en sombra — 2026-09-22

## Cambios operativos
El cálculo del lote en el plan de entrada usa el precio adverso con 20 puntos de desviación, igual al límite previo al envío del proveedor MT5. BUY suma ese margen y SELL lo resta. El TP/SL y el límite monetario no aumentan. El volumen normalizado sigue pasando por los controles existentes de lote mínimo, riesgo y ejecución; no se garantiza entrada cuando el broker impide un lote viable. La cotización puede volver a cambiar antes del envío y el control final sigue rechazando un exceso.

Una excepción PRE_SEND_RISK_CAP_BREACH en el ciclo activa 300 segundos de espera por instrumento, registrados como RISK_RETRY_COOLDOWN. Después se vuelve a analizar la señal; no se reenvía una orden almacenada. El temporizador es de memoria y se pierde al reiniciar. No aumenta el cap ni modifica posiciones existentes.

## Auditoría por setup y secuencia
La identidad es símbolo + dirección + fecha del setup + límites del OB. Las evaluaciones de una misma candidata actualizan su contador y una secuencia de estados distintos (últimos 64). No equivalen a trades ni a resultados de backtest. El estado del día se recupera desde el archivo al reiniciar. Los setups sin candidata M5 evaluada pueden no aparecer en este contador.

El dashboard de prueba SMC muestra el número de setups únicos y dos comparaciones:
- STRUCTURE_WITHIN_3_BARS: BOS/CHOCH favorable dentro de las últimas tres velas de la misma tesis, en vez de únicamente la vela de confirmación.
- STRUCTURE_AND_DISPLACEMENT_WITHIN_3_BARS: añade desplazamiento favorable ocurrido en esa ventana.

La ventana no cruza el inicio del setup, no supera diez minutos y exige que los cierres respeten el OB. No consulta velas posteriores. Cada comparación enumera fallos críticos resueltos y pendientes; no recalcula una autorización completa, no sustituye score/filtros ni representa una operación hipotética rentable. H1 premium/discount, OB, confirmación favorable y objetivos de la operativa actual se conservan. Las variantes están en SHADOW_ONLY y no cambian confirmation_valid.

## MetaEtiquetado: FOREX_3
Consulta del journal durante esta revisión: FOREX_3 tenía seis registros cerrados históricos sin entry_learning_snapshot; la familia Forex completa tenía trece. Las 253 evaluaciones en sombra de la captura no son 253 operaciones cerradas ni 253 etiquetas independientes. No se fabrica ni activa un modelo a partir de ese contador.

La pantalla Cuenta ahora distingue evaluaciones de señales, uso histórico de un modelo en dichas evaluaciones y candidatos por estrategia con setups elegibles/mínimo y fecha del informe. El rótulo refleja evaluaciones registradas, no una inspección instantánea del archivo del modelo operativo. La formación de candidatos continúa con el mínimo configurado y ambas clases de resultado, sin promoción automática.

## Activación y comprobación
Reiniciar workers y dashboard para cargar los cambios. No se reiniciaron procesos ni enviaron órdenes reales durante esta implementación. 33 pruebas aprobadas en riesgo previo al envío, enfriamiento, estructura M5, confirmación favorable, deduplicación y ejecución simulada. JavaScript de Cuenta y dashboard verificado.
