# Malaysian SNR v2.1 — retest persistente y niveles con ciclo de vida

Implementación del 11 de octubre de 2026. El objetivo es permitir retests válidos que antes perdían su ruptura de referencia y mejorar la selección de las entradas adicionales. La mejora del WinRate requiere validación de mercado; las pruebas de software no la demuestran.

## Comportamiento implementado

- La ruptura H1 original se conserva durante **90 minutos**, aunque cierre otra H1. Se reconstruye desde prefijos de velas cerradas, por lo que mantiene su referencia después de reiniciar y utiliza el mismo detector en replay.
- ATR, ADX, nivel e invalidación se fijan con los datos disponibles al cierre de la ruptura. El stop original no se amplía para rescatar un retest.
- El primer contacto puede confirmar por **barrido real y recuperación** o por **contacto dentro de zona y rechazo por cierre**. La tolerancia configurada sí se utiliza.
- Se exige cuerpo direccional de al menos 35% del rango, cierre en la mitad favorable, entrada cercana y penetración máxima de 0,35 ATR H1. La recuperación dispone de tres cierres M15 desde el primer contacto.
- Una nueva visita separada, una penetración excesiva, velas faltantes o la pérdida del extremo estructural invalidan la oportunidad. Una recuperación posterior no borra el incumplimiento.
- El clasificador de continuación distingue **FRESH**, **TESTED_ONCE** y **CONSUMED**. Cuenta visitas consecutivas como un episodio. Un cierre corporal contrario, más de una visita o una mecha más profunda que 0,20 ATR consumen el nivel.
- Un nivel testeado una vez exige adicionalmente cuerpo de al menos 50% y desplazamiento direccional de al menos 0,20 ATR H1. `enable_tested_level_entries` permite desactivar esa excepción.
- Una ruptura por cierre invalida el papel anterior de un obstáculo A/V. Solo los niveles contrarios aún activos limitan TP1 y la corredora, incluidos los de D1 y los recién formados con velas cerradas.
- La señal lleva una identidad `setup_id` basada en instrumento, escenario, ruptura, dirección y nivel. Repetir un cierre no genera una nueva identidad. Un cierre posterior no vuelve a emitir el primer retest ya confirmado.
- El motor comprueba las claves de ejecución persistidas de ambas piernas, entrada única y claves anteriores a esta actualización. El replay también impide ejecutar otra vez el mismo setup.
- Antes de dimensionar las piernas, el motor verifica proximidad con la cotización de ejecución, dirección respecto al nivel, invalidación y vencimiento. Un fallback a una entrada única no puede saltarse este control.

La ventana de 90 minutos limita el **cierre de confirmación**, no exige procesarlo en el milisegundo exacto. Existe una gracia de procesamiento de 60 segundos para esa última vela. No habilita una M15 que cierre después del plazo ni elimina el control de cotización.

La política anterior de instrumentos, dirección, riesgo total, doble pierna, TP1, spread, disponibilidad y sesiones sigue siendo la base de ejecución. El escenario de continuación conserva su estado desactivado por defecto; su clasificador se aplica cuando se habilita ese escenario. No se habilitaron escenarios adicionales ni se reemplazó el modelo IA.

## Panel y auditoría

La matriz distingue ausencia de patrón, primer contacto pendiente, rechazo insuficiente, vencimiento, consumo, conflicto D1, obstáculos y errores de datos. Muestra los minutos restantes y distingue fractal de Quasimodo. La ausencia de contexto deja de presentarse como un rango detectado, y ADX no se convierte en una supuesta probabilidad de éxito.

Los registros resumidos conservan identidad, escenario, niveles, hora original, frescura y evidencia del retest. El muestreo de auditoría distingue setups diferentes aunque compartan el mismo motivo. La herramienta offline informa evaluaciones repetidas y setups únicos por etapa por separado; las etapas pueden solaparse.

## Parámetros principales

| Parámetro | Valor por defecto |
|---|---:|
| `retest_window_minutes` | 90 |
| `entry_execution_grace_seconds` | 60 |
| `retest_recovery_bars` | 3 |
| `retest_tolerance_atr` | 0,35 |
| `max_entry_distance_atr` | 0,50; fractal 0,40 |
| `max_retest_penetration_atr` | 0,35 |
| `retest_min_body_ratio` | 0,35 |
| `max_tested_wick_penetration_atr` | 0,20 |
| `tested_level_displacement_atr` | 0,20 |

Todos los umbrales ATR anteriores utilizan el ATR H1 disponible al cierre de la ruptura. Son reglas iniciales, no valores optimizados por familia ni evidencia de rentabilidad.

## Verificación

Las pruebas controladas cubren retests a +15, +45, +60, +75 y +90 minutos, procesamiento con retraso acotado, reinicio, caducidad a +105, invalidación irreversible, ausencia de velas, consumo del primer retest y rechazo de contactos repetidos. También verifican profundidad, visitas de mecha, recuperación reforzada, obstáculos activos D1, telemetría compacta, identidad de ejecución y controles de cotización con fallback.

Las pruebas de regresión incluyen riesgo compartido, doble pierna, ejecución, frescura de señales, posiciones activas y panel. No requieren abrir operaciones.

**Resultado final: 138 pruebas pasaron.** También se verificaron sintaxis y limpieza del diff de los archivos modificados.

## Replay y alcance

La validación offline se guarda en `storage/analysis/msnr_v21_validation_20261011/`, separada de los informes anteriores. Se ejecuta con:

```text
python tools/validate_msnr_persistent_retest.py --symbol "Step Index" --days 30
```

La herramienta admite también Boom 1000, Crash 1000 y XAUUSD, usa velas locales y no contacta al broker. Cuenta operaciones consolidadas con ambas piernas, spread estimado, fill siguiente y resolución conservadora de velas ambiguas. Reutiliza datos históricos, reconstruye D1 en UTC y no incorpora comisiones, swaps, latencia ni límites conjuntos de cartera.

El resultado cuantitativo final de esta ejecución está en los cuatro archivos `*_metrics.json` y `*_trades.csv` de esa carpeta. Debe compararse con los resultados del diagnóstico previo y después con datos nuevos. Un mayor número de setups observados no equivale a un aumento de operaciones ni de WinRate.

| Activo | Setups únicos observados | Operaciones | Resultado total |
|---|---:|---:|---:|
| Boom 1000 Index | 125 | 1 | −1R |
| Crash 1000 Index | 126 | 1 | −1R |
| Step Index | 106 | 0 | 0R |
| XAUUSD | 50 | 0 | 0R |

Los conjuntos observados incluyen candidatos bloqueados o expirados; no representan entradas autorizadas. La ventana de cada archivo son sus últimos 30 días: los sintéticos terminan el 4 de octubre y XAUUSD el 2 de octubre. Las dos operaciones tuvieron resultado negativo, igual que en la configuración anterior sobre estos cuatro archivos. La muestra es insuficiente para medir WinRate o acreditar una mejora. El cambio temporal sí quedó demostrado con casos controlados de retests tardíos.

## Carga de la actualización

Los procesos Python ya iniciados conservan el código cargado anteriormente. La versión `msnr-v2.1-persistent-retest` se carga al iniciar nuevamente el worker y el dashboard. No se reiniciaron procesos ni se enviaron órdenes durante esta implementación. Las posiciones existentes conservan su gestión y sus registros.
