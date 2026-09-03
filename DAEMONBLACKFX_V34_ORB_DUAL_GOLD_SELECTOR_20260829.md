# DaemonBlackFx v34 — ORB Oro dual: XAUUSD + XAUUSDmicro

## Objetivo
La estrategia ORB New York acepta tanto `XAUUSD` como `XAUUSDmicro`, pero los trata como dos contratos alternativos de la misma exposición al Oro.

El daemon no abre simultáneamente ambos contratos por la misma tesis ORB.

## Selección automática
Cuando ambos contratos están disponibles, antes de ejecutar se evalúa cada candidato con la señal ORB y las especificaciones reales del broker.

Criterios, en orden de prioridad:
1. Precisión del riesgo de cada pierna respecto del objetivo de 0,5%.
2. Costo del spread respecto del riesgo objetivo.
3. Margen requerido respecto del margen libre.

Menor score = mejor ejecución.

Si sólo uno puede representar de forma segura el 0,5% por pierna, se utiliza ese.
Si ninguno puede respetar el riesgo, la operación se rechaza.

## Gestión de la operación
La operación lógica mantiene riesgo objetivo total de 1%:
- `TP1`: 0,5%, objetivo 1R.
- `RUNNER`: 0,5%, objetivo 2R.

Al alcanzarse 1R o confirmarse que TP1 cerró en beneficio:
- TP1 queda cerrado.
- RUNNER mueve su SL a entrada + 2 puntos en BUY.
- RUNNER mueve su SL a entrada - 2 puntos en SELL.

Los 2 puntos se calculan usando el `point` real del contrato elegido.

## Auditoría
Se registra `gold_contract_selection` con:
- candidatos;
- contrato seleccionado;
- motivo;
- riesgo objetivo y real;
- volumen por pierna;
- spread;
- costo monetario del spread;
- margen requerido;
- score de calidad.

## Alcance ORB
- XAUUSD / XAUUSDmicro
- Wall Street 30
- US Tech 100
- US500
- exclusivamente sesión New York según `America/New_York`.

La estrategia SMC para el resto de instrumentos permanece sin cambios.
