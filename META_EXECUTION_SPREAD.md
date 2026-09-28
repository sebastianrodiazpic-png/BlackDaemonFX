# Spread ejecutable para MetaEtiquetado — 23/09/2026

El motor consulta executor.get_current_tick para capturar el bid/ask de MT5 al evaluar una señal. Ya no calcula el spread de aprendizaje a partir del último precio indicativo de Deriv.

- Se aceptan precios finitos y positivos, ask >= bid, con timestamp disponible y antigüedad máxima de 180 segundos. Se rechazan timestamps más de 60 segundos en el futuro. Estos márgenes coinciden con el control de disponibilidad existente.
- Un spread cero observado en una cotización válida de MT5 sigue siendo válido.
- Si no hay cotización válida, spread=None y spread_available=0. La extracción no sustituye ese desconocido por un spread contenido en la señal.
- El evento META_LABEL_SIGNAL_SCORED y la captura entry_learning_snapshot conservan market_snapshot: spread, fuente MT5_EXECUTION, fecha de cotización, fecha de consulta, bid/ask válidos y estado/motivo de indisponibilidad.
- El valor numérico de la feature ausente permanece en cero por compatibilidad del vector; su máscara spread_available=0 lo distingue de un cero observado.

No se alteran SL, TP, reglas de entrada ni salidas. La consulta se realiza en el punto de evaluación de MetaEtiquetado, no pretende reconstruir el spread exacto del fill posterior. Los registros históricos no se reescriben: un cero antiguo sin procedencia ejecutable sigue siendo un dato no verificado y no debe interpretarse como coste nulo.

Validación: 41 pruebas aprobadas en test_meta_execution_spread.py, test_audit_quality_improvements.py y test_v101_meta_labeling_engine.py. Incluyen feed indicativo prohibido, broker desconectado, precios no finitos/invertidos, timestamps ausentes/antiguos/futuros, cero real y persistencia de procedencia en el evento de auditoría.

Aplicación: requiere reiniciar los workers que ya están ejecutándose. Esta tarea no reinició procesos ni modificó operaciones abiertas.
