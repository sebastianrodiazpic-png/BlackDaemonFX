# DaemonBlackFx v41 — Critical Gates + RUNNER dinámico TP3/TP4

## Objetivo
Mejorar la calidad de entrada observada en DEMO sin aumentar el riesgo inicial,
y permitir capturar movimientos excepcionales protegiendo ganancias.

## 1. Gates estructurales
El modo adaptativo >=80% ya no puede compensar:

- BOS sin rechazo M5.
- CHOCH sin microestructura M5.

Códigos:
- `BOS_REJECTION_NOT_CONFIRMED`
- `CHOCH_MICRO_STRUCTURE_NOT_CONFIRMED`

## 2. Score
`trade_score` queda limitado a 100.
Se conserva `raw_trade_score` para auditoría, pero 105/110 ya no se muestran
como si representaran una probabilidad superior al 100%.

## 3. Jump en modo estricto
Jump sigue habilitado, pero en `demo/demo-daemon` exige:
- confirmación >= 90%;
- score >= 90;
- rechazo;
- microestructura;
- desplazamiento;
- cierre fuerte.

Además no usa fallback SINGLE: debe ser posible dividir el riesgo en TP1 + RUNNER.

## 4. RUNNER dinámico
El riesgo inicial sigue siendo:
- TP1: 0.5% a 1R.
- RUNNER: 0.5%.

Cuando la función está activa, el RUNNER lleva TP broker máximo a 4R para que no
sea cerrado mecánicamente en 2R antes de poder evaluar continuación.

Flujo:

1R:
- TP1 cierra.
- RUNNER -> BE + offset.

2R:
- primero SL RUNNER -> +1R.
- después se evalúa continuidad estructural M5.
- si no continúa: cierre del RUNNER.
- si continúa: `EXTENDED_TO_3R`.

3R:
- primero SL RUNNER -> +2R.
- después se reevalúa estructura.
- si no continúa: cierre.
- si continúa: `EXTENDED_TO_4R`.

4R:
- objetivo máximo; el TP broker puede cerrar la posición.

El profit lock se aplica ANTES de analizar, de modo que un error de datos no
permita devolver la ganancia hasta Break Even.

## 5. Evaluación de continuación
El módulo `strategy/execution/runner_extension_manager.py` comprueba:
- CHOCH contrario reciente;
- último evento estructural;
- respeto del swing protector;
- momentum reciente o estructura alineada.

## 6. MFE / MAE
Durante el monitor se registran en `details_json.metadata`:
- `max_favorable_excursion_rr`;
- `max_adverse_excursion_rr`;
- precio/hora de MFE y MAE.

La persistencia se actualiza por pasos de 0.05R para evitar escrituras excesivas.

## 7. Reportes y Cuenta activa
El XLSX incorpora:
- `mfe_max_rr`;
- `mae_max_rr`;
- `etapa_runner`;
- `profit_lock_runner_rr`;
- `motivo_salida_runner`.

Cuenta activa reconoce TP1, TP2, TP3 y TP4.

## Nota experimental
TP3/TP4 no garantizan mayor rentabilidad. La finalidad de v41 es generar datos
medibles para comparar expectancy, MFE/MAE, Win Rate lógico y profit factor
después de acumular una muestra mayor de operaciones.
