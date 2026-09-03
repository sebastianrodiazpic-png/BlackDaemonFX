# DaemonBlackFx v6 - Entrada única alternativa + divergencias

Fecha: 2026-08-28

## 1. Gestión de riesgo

La operación lógica mantiene un riesgo máximo configurado de 1%.

### Modalidad normal
- TP1: 0,5% de riesgo, objetivo 1R.
- RUNNER: 0,5% de riesgo, objetivo 2R.
- Al alcanzar 1R, el RUNNER mueve el Stop Loss a entrada +2 puntos en BUY o entrada -2 puntos en SELL.

### Entrada única alternativa
Si las restricciones de volumen/lote del broker hacen imposible dividir el riesgo en dos entradas sin superar el máximo permitido, el motor intenta una sola entrada:
- Riesgo máximo: 1%.
- Objetivo: 2R.
- Break Even: se activa en 1R.
- Protección BE: +2 puntos a favor de la dirección.

Si la entrada única también supera el riesgo máximo, la operación se rechaza.

Campos de diagnóstico:
- `execution_mode=SPLIT`: dos entradas.
- `execution_mode=SINGLE_FALLBACK`: entrada única alternativa.
- `split_failure`: motivo por el que no fue viable dividir la operación.

## 2. Divergencias

Se agregó detección de divergencia regular precio/RSI usando pivotes SMC recientes.

### Divergencia alcista regular
- El precio forma un mínimo más bajo.
- RSI forma un mínimo más alto.
- Puede anticipar pérdida de presión vendedora.

### Divergencia bajista regular
- El precio forma un máximo más alto.
- RSI forma un máximo más bajo.
- Puede anticipar pérdida de presión compradora.

La divergencia NO abre operaciones por sí sola y NO es obligatoria.
Sólo se considera confluencia válida cuando además existe evidencia de presión estructural mediante:
- desplazamiento, o
- microestructura M5 en la dirección esperada.

Cuando se confirma, suma 5 puntos al score de calidad del trade.
No reduce el porcentaje de confirmaciones cuando no existe, para evitar convertirla en un filtro obligatorio.

Configuración por defecto:
- `divergence_enabled=True`
- `divergence_rsi_period=14`
- `divergence_lookback_candles=80`
- `divergence_bonus_points=5.0`

## 3. Consola en español

Se tradujeron los principales estados visibles y motivos de rechazo. La consola también muestra:
- modalidad de ejecución,
- porcentaje de confirmaciones,
- calidad/score,
- confirmaciones faltantes,
- confirmaciones críticas faltantes,
- divergencia confirmada cuando corresponda.

## 4. Pruebas

Regresión disponible en este entorno: 161 pruebas aprobadas.
Las pruebas que requieren el paquete nativo MetaTrader5 quedan para ejecución en Windows + MT5/Deriv Demo.
