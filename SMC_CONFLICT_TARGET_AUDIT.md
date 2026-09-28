# Conflictos y auditoría de objetivos

FUERZAS_SIMILARES bloquea confirmación de nuevas entradas cuando
block_similar_chart_pattern_forces=True, incluido delta0 y fuerzas0.78/0.78.
No depende del umbral separado para oposición dominante. No se añadieron órdenes
de cierre ni modificaciones de SL/TP. La gestión previa existente no se reescribió.

Auditoría M15 informativa: OB contrarios producidos por el pipeline, excluidos si
hubo cierre posterior a su formación más allá del borde contrario. Añade extremo
del rango M15 disponible. Cada TP se evalúa con entrada/SL/objetivo planificados,
zonas atravesadas y distanciaR. No equivale a copiar LuxAlgo ni detecta toda
resistencia/soporte. Ausencia de obstáculos detectados no garantiza recorrido libre.
No veta órdenes, ajusta objetivos ni gestiona salidas. Panel Prueba SMC muestra
los obstáculos cuando el candidato alcanza planificación de ejecución.

Metadata de cada nueva orden conserva todos los campos chart_pattern_* y
target_path_audit para comparación entrada/ahora. No se reconstruye evidencia
histórica ausente en operaciones previas. Los cambios se cargan reiniciando
workers/dashboard. No se enviaron órdenes ni reiniciaron servicios.

Validación:28pruebas dirigidas aprobadas y scriptsJS válidos. Una prueba antigua
adicional test_account_page_exposes_persistent_confirmations falla porque exige
el texto Confirmaciones persistentes en account_page.py; no afecta a las pruebas
del motor ejecutadas y no se modificó esa pantalla durante este trabajo.
