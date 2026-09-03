# DaemonBlackFx - Corrección Break Even del RUNNER

## Objetivo

Cuando una operación lógica se divide en dos piernas:

- TP1: 0.5% de riesgo, objetivo 1R.
- RUNNER: 0.5% de riesgo, objetivo 2R.

al alcanzarse 1R y cerrarse TP1, el RUNNER debe mover su Stop Loss a Break Even con 2 puntos a favor:

- BUY: `SL = entry + (2 * point)`
- SELL: `SL = entry - (2 * point)`

## Problema detectado

La implementación anterior evaluaba el Break Even principalmente usando el precio actual observado por el monitor. Si TP1 tocaba 1R, cerraba y el precio retrocedía antes de la siguiente lectura, el RUNNER podía dejar de cumplir `current_price >= trigger_price` / `current_price <= trigger_price` y el evento 1R se perdía.

## Corrección implementada

1. El monitor sincroniza primero los cierres reales de MT5 con SQLite.
2. El RUNNER busca su TP1 hermano mediante `parent_execution_key`.
3. Si TP1 está CLOSED y cerró en beneficio, ese hecho se considera evidencia persistente de que 1R fue alcanzado.
4. El RUNNER queda elegible para BE+2 incluso si el precio ya retrocedió por debajo de 1R.
5. También se mantiene el camino normal de activación por precio observado >=1R.
6. La confirmación del SL usa tolerancia basada en `point/tick_size` real del símbolo para evitar falsos negativos por redondeo de MT5.
7. Se registra `break_even_activation_reason` para auditoría:
   - `PRICE_REACHED_TRIGGER_RR`
   - `TP1_CLOSED_IN_PROFIT`

## Validación

Pruebas cubiertas:

- BUY: BE en entry +2 puntos.
- SELL: BE en entry -2 puntos.
- RUNNER: BE se activa aunque el precio retroceda después de que TP1 haya cerrado en 1R.
- Idempotencia: no reenvía modificaciones si el broker ya tiene el SL correcto.
- No persiste BE si el broker no confirma el nuevo SL.

Regresión disponible en entorno Linux: 162 pruebas aprobadas.

Las pruebas que importan directamente MetaTrader5 requieren Windows/MT5 y deben validarse en la cuenta Deriv Demo.
