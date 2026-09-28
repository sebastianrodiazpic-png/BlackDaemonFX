# Confirmación favorable compartida SMC

LiveTradingConfig.require_favorable_confirmation=True se propaga a PipelineConfig
y M5ConfirmationConfig para GOLD, FOREX y todos los perfiles sintéticos.
El analizador aislado mantiene flagFalse por compatibilidad; live lo activa.

Se exige patrón chartista confirmado dentro de la ventana setup-confirmación,
o agotamiento del mismo OB: cuerpo<=35%, mecha favorable>=45%, contacto conOB,
cierre respetando su borde y una vela posterior (máximo2velas) direccional que
cierre más allá del máximo del rechazo para BUY o mínimo para SELL.
Sólo datos hasta la confirmación; el proveedor live entrega velas cerradas.

Es gate crítico: score alto no compensa su ausencia. Se conservan OBfresco,
reteste limpio, desplazamiento, microestructura requerida y veto chartista material.
No se usa el módulo independiente exhaustion_reversal_shadow para abrir operaciones.
Patrones se detectan desde setup_time para evitar reutilizar patrones anteriores.
Si require_chart_pattern se configuraTrue explícitamente, sigue exigiendo patrón;
la configuración live predeterminadaFalse permite la alternativa de agotamiento.

Zona H1 permanece obligatoria: premiumSELL y discountBUY; objetivos, SL, RR,
tamaño de posición y gestión posterior no se modifican.
Auditoría favorable_confirmation y panel indican patrón/agotamiento/sin evidencia.
Aplicar mediante reinicio de workers y dashboard. No se reiniciaron ni enviaron
órdenes durante esta implementación. No implica aumentar frecuencia ni rentabilidad:
agrega una condición que puede rechazar señales antes aceptadas.
