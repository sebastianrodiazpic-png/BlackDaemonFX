# Diagnostico de ausencia de entradas — 26 septiembre 2026

Ultimo cambio del coordinador: 25 septiembre 23:36:24 America/Santiago (26 septiembre 02:36:24 UTC). Registros consultados aproximadamente a las 18:25–18:30 de Chile.

La presencia de M15_OB_STRUCTURE_BREAK_REQUIRED y M5_CHOCH_FVG_REQUIRED en registros posteriores confirma que los workers sinteticos cargaron la nueva logica.

Snapshot de contadores diarios de BOOM, CRASH, JUMP, STEP y VOLATILITY_1..4 desde medianoche local: 7992 evaluaciones; NO_H1_CONTEXT 3513, NO_M15_SETUP 2485, NO_M5_CONFIRMATION 1108, DIRECTION_POLICY_BLOCKED 886. Son evaluaciones repetidas, no trades independientes. No cubren los primeros 24 minutos desde el cambio.

Auditoria M15: 673 bloques con setup_time desde medianoche; ultimo estado aceptado en 14. En los estados restantes se observan 541 sin ruptura estructural, 506 sin desplazamiento, 419 invalidados por cierre, 344 con direccion incompatible, 291 fuera de ubicacion H1, 176 vencidos. Las causas se superponen y los ultimos estados no representan necesariamente el estado inicial del bloque.

Auditoria detallada M5: 20 setups distintos con baseline_critical_failures almacenados; en su ultima evaluacion detallada, 20 carecen de FVG requerido vinculado al CHoCH, 16 carecen del evento estructural requerido, 15 de desplazamiento, 12 de retest limpio y 6 de sweep. Esta muestra no equivale a las 1108 evaluaciones agregadas de M5.

El rechazo H1 agrupa falta de pivotes/rango valido, precio fuera del rango y equilibrio; el contador por si solo no permite atribuir cada rechazo a una de ellas.

La implementacion exige CHoCH M5 (no basta BOS) en confirmacion o dos velas anteriores, y un FVG cuya vela central o final sea ese CHoCH. Esta restriccion es mas estrecha que buscar cualquier gap alrededor de la ruptura. El rango H1 rechaza precio fuera de extremos y espera 5 velas derechas para confirmar cada pivote. No hay evidencia en estos contadores de que relajar un filtro aisladamente cree operaciones rentables.

No se cambiaron parametros ni se reiniciaron procesos durante este diagnostico.
