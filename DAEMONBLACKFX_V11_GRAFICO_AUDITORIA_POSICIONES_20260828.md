# DaemonBlackFx v11 - gráfico de auditoría de posiciones abiertas

## Objetivo
La pestaña de salud de posiciones abiertas incorpora una auditoría visual M5 para revisar si la tesis que originó una posición sigue vigente mientras el trade permanece abierto.

## Qué muestra el gráfico
- Últimas velas M5 del instrumento (hasta 90 solicitadas; se visualizan las 80 más recientes).
- Precio de entrada.
- Stop Loss original.
- Take Profit.
- Stop Loss actual / Break Even cuando el broker ya lo movió.
- Precio actual.
- Marcadores de eventos SMC disponibles en el pipeline M5: CHOCH alcista/bajista, BOS alcista/bajista, liquidity sweep alcista/bajista y Order Block alcista/bajista.
- Panel lateral con la recomendación de salud, R actual, última decisión del analizador, score, porcentaje de confirmaciones, tendencia H1, estructura, zona, divergencia y confirmaciones cumplidas/faltantes.

## Seguridad de arquitectura
El navegador no consulta MetaTrader5. El mismo hilo cooperativo del daemon obtiene las velas y el estado de la posición y publica un snapshot JSON al dashboard. De esta manera el gráfico no introduce una segunda conexión MT5 ni concurrencia sobre la gestión de órdenes.

## Frecuencia
El gráfico se refresca cuando corre el monitor cooperativo de posiciones. El navegador consulta el estado local aproximadamente cada segundo, pero no fuerza consultas adicionales al broker.

## Comportamiento al seleccionar instrumentos
Una posición que ya está abierta puede seguir mostrándose y monitoreándose aunque su instrumento haya sido deshabilitado para nuevas entradas desde la selección dinámica.

## Importante
La visualización es una herramienta de auditoría y la recomendación sigue siendo asesora. En v11 no se cierra ninguna posición automáticamente a partir del gráfico o del score de salud. Esto permite medir primero si las señales de deterioro realmente anticipan cierres que mejoren el resultado.

## Uso
Ejecutar normalmente:

    python -m app.main --mode demo-daemon --execute --interval 30 --risk-percent 1.0 --min-rr 1.5 --dashboard

Abrir:

    http://127.0.0.1:8765

En "Salud de posiciones abiertas", pulsar "Ver gráfico" sobre la posición deseada.
