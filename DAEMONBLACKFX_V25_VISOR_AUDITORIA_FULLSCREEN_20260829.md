# DaemonBlackFx v25 — Visor de auditoría en pantalla completa

## Objetivo
Mejorar la visibilidad del gráfico de auditoría SMC de las posiciones abiertas sin modificar la lógica de trading.

## Cambios
- Botón **Pantalla completa** en la auditoría visual.
- Uso de la Fullscreen API del navegador cuando está disponible.
- Botón **Minimizar / Restaurar** para colapsar la auditoría y recuperar espacio en el dashboard.
- `Esc` permite salir del modo pantalla completa del navegador.
- En pantalla completa el gráfico utiliza todo el viewport disponible.
- El panel lateral **Entrada vs. ahora** permanece visible y desplazable.
- Las capas SMC activadas/desactivadas se mantienen al maximizar, restaurar o minimizar.
- La posición seleccionada se conserva durante los cambios de tamaño.
- Diseño responsive: en pantallas estrechas el gráfico y la auditoría lateral se apilan.

## Capas conservadas
- Trade / SL / TP / Break Even
- HH / HL / LH / LL
- CHOCH / BOS
- BSL / SSL / Liquidity Sweeps
- Order Blocks
- FVG / Imbalances
- Premium / Discount / Equilibrium
- Divergencia RSI / Doji H1 / Armónicos
- RSI 14

## Seguridad
Este cambio es únicamente de presentación. No modifica:
- reglas de entrada,
- mínimo de confirmaciones del 80%,
- position sizing,
- riesgo,
- Break Even,
- sincronización MT5/SQLAlchemy,
- persistencia de Cuenta activa.

## Validación
- `tests/test_realtime_dashboard.py`: 18 pruebas aprobadas.
- Suite no dependiente de MetaTrader5 nativo: 197 pruebas aprobadas.
