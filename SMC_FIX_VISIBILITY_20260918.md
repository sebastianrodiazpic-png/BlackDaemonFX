# Corrección de entradas y visibilidad SMC — 18 septiembre

Corregida la referencia inexistente diagnostics al preparar metadata antes de
execute_with_executor. Reutiliza el resumen auditado construido desde analysis.
Test integral con lifecycle/executor/repositorio simulados comprueba ejecución
de dos legs, preservación de timestamp M5 y persistencia de ambas operaciones.
No se enviaron órdenes ni se reiniciaron servicios.

Panel Prueba SMC: contadores separados ORO, PLATA, INDICES_Y_OTROS, FOREX y
SINTETICOS; candidatas únicas por símbolo/dirección/hora, primera detección,
última actualización, motivo y caducidad. Se conserva el histórico de rechazo;
no se amplía la vigencia de una señal ni se reutiliza para nuevas entradas.
Las nuevas estadísticas empiezan con el reinicio; no reconstruyen datos anteriores.

Lista visible NO ACTIVADOS: transición H1 neutral con estructura nueva, rechazo
por recuperación al cierre, desplazamiento por familia, vigencia de setups
anteriores y horarios separados. Requieren replay fuera de muestra con costes,
expectativa y drawdown. H1_PRIMARY y ATR_BOUNDED siguen como prueba configurada;
no se flexibilizaron más gates ni RR/riesgo.

Aplicación: reiniciar workers y dashboard, y comprobar fecha de actualización.
Una prueba simulada no demuestra rentabilidad ni garantiza que el mercado genere
candidatos. La corrección elimina el error de código identificado, no los rechazos
legítimos de la estrategia.
