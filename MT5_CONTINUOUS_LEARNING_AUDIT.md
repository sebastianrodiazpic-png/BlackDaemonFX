# Auditoría MT5 y aprendizaje continuo — 2026-09-21

## Flujo
1. La sincronización existente de MT5 importa posiciones y cierres al journal permanente. La auditoría individual sigue disponible en Cuenta → Historial → Ver auditoría completa.
2. Las nuevas entradas del motor guardan `entry_learning_snapshot`: versión del esquema, nombres y valores exactos del vector utilizado al evaluar la entrada, fecha, worker y estrategia. Se conserva en ambas rutas de persistencia y en recuperación posterior al fill.
3. La auditoría compara resultados cerrados con esa evidencia de entrada. No utiliza el análisis actualizado como si hubiera existido al entrar.
4. TP1 y runner se agrupan por ejecución: el setup aporta una muestra cuando todas las piernas han cerrado. No se mezclan piernas abiertas ni se duplica una tesis para entrenar.
5. Cada worker activo solicita una actualización en segundo plano, como máximo una vez por hora, al completar su ciclo. Los workers pausados actualizarán al retomar. No crea procesos Python adicionales.
6. Con el mínimo configurado (30 setups por defecto) y ambas clases de resultado se entrena un modelo candidato por worker/estrategia. Se conserva el agrupamiento existente por familia, por ejemplo FOREX_1 y FOREX_2. La huella del dataset evita repetir el entrenamiento sin cambios.
7. La validación temporal excluye del entrenamiento las operaciones cuyo cierre todavía no era conocido al comenzar el bloque evaluado. Las capturas nuevas exigen fecha de cierre válida. El historial antiguo sin captura mantiene la compatibilidad del entrenamiento manual existente.

## Visibilidad
El dashboard muestra «Auditoría MT5 y aprendizaje candidato»: última actualización, origen, registros con/sin captura, resultados por instrumento, setups elegibles, mínimo, estado de candidato y métricas de validación. Los totales de cuenta se repiten por worker: no deben sumarse entre tarjetas.

Informes: `storage/learning_audit/<source>_<worker>.json`.
Modelos candidatos: `storage/learning_audit/candidate_models/`.
Errores de actualización: evento `LEARNING_AUDIT_ERROR` en la auditoría del daemon. La fecha visible permite detectar un informe antiguo.

## Alcance y límites
- Las operaciones manuales/importadas sin contexto contemporáneo se auditan por resultado, pero no entrenan el modelo de señales SMC: no se inventan OB, CHOCH, BOS ni patrones históricos.
- Las capturas incompletas, incompatibles, abiertas o sin cierre válido quedan fuera del aprendizaje automático.
- Se usa el vector ya establecido del metaetiquetado (score, confirmaciones, estructura, patrones/conflicto, ATR, spread, RR, edad de señal, etc.). No todos los campos del informe de auditoría son variables del modelo.
- La etiqueta mantiene la política existente: RR realizado y, si falta, PnL neto; la tabla de resultados usa PnL neto. Los breakeven sin resultado significativo no entrenan.
- Entrenar un candidato no acredita una mejora. Revisar validación temporal, tamaño de muestra, expectativa, costes y resultados fuera de muestra antes de promoverlo mediante el flujo de entrenamiento operativo existente.
- No se promocionan modelos automáticamente, no cambian reglas SMC y no se añaden cierres anticipados ni modificaciones de SL/TP.
- Es necesario reiniciar workers y dashboard para cargar este código. No se reiniciaron procesos ni se modificaron operaciones abiertas durante la implementación.

## Validación
Pruebas de captura inmutable, importaciones sin contexto, piernas abiertas, datos inválidos, aislamiento de modelos candidatos, reutilización de candidatos y exclusión temporal de cierres futuros; integración de persistencia de la captura en una entrada simulada.
