# DaemonBlackFx v15 - Motivos del dashboard en español operativo

## Objetivo

Hacer que la sección **Análisis recientes** sea entendible para el trader sin perder trazabilidad técnica. Los códigos internos de la estrategia se conservan sin cambios y se muestran como referencia secundaria.

## Nuevos campos del snapshot

Cada análisis reciente expone ahora:

- `action`: código técnico original.
- `action_es`: acción explicada en español.
- `reason`: código/motivo técnico original.
- `reason_es`: explicación operativa en español.
- `decision_es`: traducción de la decisión de confirmación.
- `operational_state`: estado visual uniforme (`CONFIRMADO`, `ESPERANDO`, `DESCARTADO`, `PROTECCIÓN / RIESGO`, `ERROR` o `INFORMATIVO`).

## Ejemplo

Código técnico:

`POST_FILL_RISK_HARD_CAP_BREACH`

Presentación:

**PROTECCIÓN / RIESGO**

**Cierre de emergencia por protección de riesgo**

> El riesgo real de la posición, después de ser ejecutada, superó el límite máximo permitido.

El código técnico continúa visible debajo para auditoría.

## Estados visuales

- `CONFIRMADO`: oportunidad confirmada/orden válida.
- `ESPERANDO`: todavía faltan condiciones o no existe señal válida.
- `DESCARTADO`: oportunidad rechazada por una regla de entrada/ejecución.
- `PROTECCIÓN / RIESGO`: el sistema actuó o bloqueó por riesgo, margen, stop o hard cap.
- `ERROR`: error técnico.
- `INFORMATIVO`: evento que no encaja en los anteriores.

## Alcance

La modificación es exclusivamente de presentación/diagnóstico. No cambia:

- estrategia SMC;
- umbral adaptativo del 75%;
- score;
- position sizing;
- Break Even;
- ejecución MT5;
- monitor de salud;
- reglas de cierre.

## Pruebas

- Traducción de `POST_FILL_RISK_HARD_CAP_BREACH`.
- Traducción de `NO_M5_CONFIRMATION`.
- Persistencia del código técnico original.
- Clasificación visual de riesgo y espera.
- Regresión no-MT5: 182 pruebas aprobadas.
