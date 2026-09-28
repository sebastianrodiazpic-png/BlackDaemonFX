# H1 ubicación y M5 estructura — 21 septiembre2026

H1 no veta por tendencia: h1_location_only=True en liveSMC. Conserva tendencia
observada como diagnóstico, usa rangoH1 y último cierreM5 para preseleccionar
BUYdiscount o SELLpremium. Equilibrio/fuera de rango/datos incompletos bloquean.
El guard final verifica cotización ejecutable. M15 aún exige setup/OB/liquidez
válidos alineados; no se eliminó su lógica interna de construcción de setups.

M5 exige evento bos_bullish/choch_bullish para compra o equivalente bearish para
venta en la vela de confirmación. Microestructura de dos velas no lo sustituye.
Mantiene patrón chartista o agotamiento favorable y desplazamiento.

RecuperaciónOB al cierre: vela distinta hasta2barras después del retest, contacto
con mismoOB, cierre direccional fuerte más allá del extremo del retest y bordeOB.
Alternativa al rechazo por mecha; mantiene límite de penetración y OBfresco.
Objetivos, SL estructural, RR y sizing no modificados. ORB no cambia su contexto.

Configuraciones live: h1_location_only, require_m5_structure_event,
allow_ob_close_recovery=True. Analizadores aislados mantienen flagsFalse por
compatibilidad. Auditoría conserva h1_context.role/location_direction,
m5_structure_event y ob_close_recovery. Dashboard distingue reglas nuevas y
flexibilidades pendientes (desplazamiento y recuperación de setups antiguos).
No se habilitaron esas flexibilidades sin validación.

Validación72pruebas. Reiniciar workers/dashboard para cargar. No se reiniciaron ni
se enviaron órdenes. No se afirma mejora de rentabilidad sin validación histórica.
