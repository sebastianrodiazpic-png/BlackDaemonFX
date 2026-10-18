# Malaysian SNR: mejoras implementadas y controles dinámicos

Implementación del 12 de octubre de 2026: `msnr-v2.7-data-ai-confirmations`.

Los controles están disponibles en [Strategy-bases](http://127.0.0.1:8765/strategy-bases), pestaña Malaysian SNR. Se conserva la preferencia 9: Fractal 45%, distancia 0,50 ATR, continuación y variantes anteriores en Operar, y veto D1 sintético desactivado. Las preferencias anteriores reciben los campos nuevos sin reiniciar sus valores.

**Estado de IA:** el modelo anterior no tiene la procedencia y validación compatibles con esta configuración. La política inicial es **Filtro + Bloquear candidato**. Esto impide nuevas entradas que alcancen IA hasta disponer de un modelo compatible o elegir expresamente observación. La alternativa **Observar IA — solo DEMO** permite medir las reglas sin el veto de ese modelo; no autoriza esa excepción en REAL. Observación de M5/H4, en cambio, registra variantes sin abrir órdenes.

No se sustituyó el modelo activo ni se certificó una mejora de WinRate. El exportador encontró cero capturas con resultados netos verificados disponibles para este entrenamiento nuevo. No se reutilizan las cifras del entrenamiento anterior como evidencia de la versión actual.

## Historial útil y errores de datos

- Carga progresiva hasta conseguir el mínimo real de velas cerradas: 80 → 160 → límite configurado. Se conserva la identidad del proveedor.
- Las primeras barras parciales de Deriv con apertura fuera del marco se excluyen; no se redondean ni se fabrican velas.
- El respaldo MT5 incorpora el estado de cierre calculado mediante apertura, duración y hora UTC. Una vela abierta permanece abierta.
- Se registran barras solicitadas, recibidas, útiles, parciales, origen y último cierre.
- Los errores de proveedor devueltos como espera ahora aparecen en el resumen de errores y en auditoría.
- Los marcos comunes se reutilizan durante la misma evaluación M15/M5/H4; el seguimiento de resultados se ejecuta fuera del ciclo de entrada, en una cola separada.

**Prueba con mercado actual:** Wall Street 30 entregó 22 velas H1 útiles en la consulta inicial y **70** al ampliarla. D1 pasó de 27 a **55** velas útiles. También se verificaron velas M5 nativas para Wall Street 30, AUDNZD y USDJPY. Esto demuestra disponibilidad para analizar; no demuestra rentabilidad.

## Confirmación M5 y contexto H4

M5 utiliza el mismo setup H1, ATR, primer retest, invalidación estructural, dirección permitida y obstáculos. Exige velas nativas cerradas y continuidad temporal del retest. La recuperación se mide en minutos: 45 minutos equivalen a tres barras M15 o nueve M5.

M15 conserva la prioridad cuando existe un candidato operable. M5 comparte el `setup_id` y la clave de ejecución del episodio, evitando una segunda entrada por confirmar también en M15. Los candidatos en observación mantienen el bloqueo de órdenes.

H4 se usa como alternativa únicamente con dirección macro obligatoria, método estructural D1, D1 suficiente y neutral, y H4 suficiente con dirección confirmada. No sustituye un D1 claramente contrario ni convierte falta de datos en neutralidad. Los obstáculos D1 siguen vigentes.

## IA y entrenamiento reproducible

La extracción canónica utiliza los valores reales del candidato y su captura de mercado. No asigna fuerza de patrón, spread o RR a partir del nombre del escenario. Las variables se congelan respecto a la confirmación; la latencia real se registra por separado.

La compatibilidad exige versión de estrategia, firma de ajustes relevantes, esquema y semántica de variables, objetivo de resultado neto de dos piernas, calibración y evaluación independientes. También se verifican dimensiones, escalas y valores finitos del modelo. Los umbrales y controles de auditoría no invalidan por sí solos la firma de geometría.

El entrenamiento usa particiones temporales 60%/20%/20% para entrenamiento/calibración/prueba. Excluye etiquetas cuyo cierre cruza al bloque siguiente, agrupa el episodio para evitar duplicados M5/M15 y no reajusta el clasificador sobre la calibración ni la prueba final. Calcula Brier, log-loss, fiabilidad, selección, WinRate y expectativa a partir de esas muestras. El resultado es un **modelo candidato**, sin promoción automática.

Se reemplazaron los scripts específicos que construían variables aproximadas o escribían métricas constantes. El entrenamiento genérico y las actualizaciones online no sobrescriben el modelo SNR con una validación antigua. Los otros workers conservan su política de IA.

Para preparar un candidato cuando existan suficientes resultados cerrados:

```powershell
.venv\Scripts\python.exe tools/export_msnr_canonical_captures.py --output storage/analysis/msnr_canonical_captures.jsonl
.venv\Scripts\python.exe tools/train_msnr_canonical.py --captures storage/analysis/msnr_canonical_captures.jsonl --settings storage/analysis/msnr_v27_settings.json
```

El segundo comando exige al menos 120 capturas verificadas y suficiente tamaño/clases en los bloques tras excluir solapamientos. Guarda el candidato fuera de `storage/ai_models`, registra su procedencia y deja intacto el modelo activo. La evaluación independiente no implica que el candidato supere el WinRate de referencia ni que deba desplegarse.

## Base de datos, resultados y panel

Tablas nuevas, separadas del journal:

- `msnr_candidates`: episodio, variante, configuración, primer bloqueo, estado actual y número de lecturas. La primera captura confirmada es inmutable.
- `msnr_candidate_transitions`: cambios de estado y decisión.
- `msnr_candidate_outcomes`: observación posterior, MFE/MAE, dos piernas, ambigüedad, cobertura de datos y costes.
- `msnr_model_registry`: huella del artefacto y procedencia del entrenamiento.

El seguimiento usa barras Bid M1 del broker y spread por barra, con la cotización ejecutable capturada. El break-even observado incorpora spread en TP1 y offset en puntos del worker; redondeo de tick, swap y demoras de protección siguen siendo aproximaciones no verificadas. Separa SL/TP, retorno a break-even, datos faltantes, horizonte vencido y orden intrabar ambiguo. Sin costes adicionales verificados, informa R ajustado por spread y mantiene el resultado fuera del entrenamiento; nunca lo inserta como trade real.

El exportador de entrenamiento enlaza la captura con TP1 y Runner cerrados del journal. Calcula R neto con el beneficio monetario neto y el riesgo real total; excluye operaciones incompletas, cierres externos y reconciliaciones pendientes. Una simulación no sustituye esos resultados ejecutados.

El panel muestra setups únicos, confirmados, ejecutados, variantes y lecturas en siete días, además del estado de compatibilidad del modelo. Los resultados de observación no se presentan como WinRate realizado. Los valores históricos de la página están identificados como correspondientes a configuraciones anteriores.

## Referencias iniciales de los controles nuevos

| Control | Valor inicial |
|---|---:|
| Ampliar historial | Activado |
| Mínimo H1 útil | 28 velas |
| Mínimo D1 para contexto | 30 velas |
| Límite por consulta | 320 velas |
| Confirmación M5 | Observación sin órdenes |
| Recuperación máxima | 45 minutos |
| Cuerpo mínimo de recuperación | 35% |
| H4 con D1 neutral | Observación sin órdenes |
| IA SNR | Filtro |
| Modelo incompatible | Bloquear candidato |
| Probabilidad general | 55% |
| Probabilidad Forex/plata | 60% |
| Probabilidad oro | 60% |
| Probabilidad Volatility | 52% |
| Expectativa mínima | 0,10 R |
| Auditoría de candidatos | Activada |
| Seguimiento de resultados | Activado |
| Horizonte de observación | 24 horas |

**Volver a valores por defecto** carga las referencias en el formulario. Solo se aplican al pulsar **Guardar ajustes**. **Actualizar estado** descarta cambios no guardados. Ambas operaciones se comprobaron en la interfaz; los ajustes activos conservan Fractal 45%.

## Verificación y activación

- **360 pruebas aprobadas**: proveedores, causalidad y retest SNR, controles HTTP, M5/H4, deduplicación, auditoría, resultados netos, IA y compatibilidad con replay y otras estrategias.
- Sintaxis del panel comprobada; la interfaz cargó los controles sin errores y conservó los valores existentes.
- Recarga exclusiva del worker SNR después de comprobar cero posiciones propias en broker y base de datos. Las dos posiciones de otro worker permanecieron bajo su gestión. Se comprobó que la instancia anterior terminó antes de iniciar la nueva.
- Versión v2.7 confirmada en los resultados del worker. Al corte de las 17:16 UTC: worker activo, ciclo 5, ocho setups únicos, 36 lecturas, cero confirmados/ejecutados y sin errores nuevos de auditoría/proveedor en la consulta revisada.

Los cambios están activos y listos para recoger evidencia. No se ejecutó un nuevo replay de rendimiento de dos años; aún no se puede afirmar que esta versión aumente el WinRate.
