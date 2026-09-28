# DaemonBlackFx v111 — reversión SMC por agotamiento

## Alcance seguro

Se añadió `SMC_EXHAUSTION_REVERSAL` para GOLD, FOREX y familias sintéticas
SMC. Funciona obligatoriamente en `SHADOW`: detecta y persiste candidatos, pero
no modifica la decisión principal ni envía órdenes.

## Secuencia exigida

- Extremo del dealing range H1: 75% premium para SELL o 25% discount para BUY.
- Barrido de la liquidez de las 20 M5 anteriores y recuperación del nivel.
- Vela de agotamiento con mecha de al menos 45% y cuerpo máximo de 35%.
- La M5 siguiente rompe el extremo del agotamiento (micro CHOCH).
- Cuerpo de desplazamiento mínimo 65%, rango mínimo 1.20 veces el promedio y
  cierre dentro del 30% fuerte de la vela.
- Volumen de agotamiento mínimo 1.20 veces el promedio cuando MT5 entrega una
  serie de volumen confiable; la ausencia técnica de volumen no genera un
  falso rechazo.

## Restricciones conservadas

- BOOM sigue admitiendo únicamente BUY.
- CRASH sigue admitiendo únicamente SELL.
- GOLD conserva su ventana Asia/Tokio hasta apertura de Nueva York.
- FOREX conserva rollover, noticias y exposición por moneda.
- El scheduler sigue evaluando una sola vez por M5 cerrada.
- No cambian score, riesgo, SL/TP ni gestión de posiciones existentes.

Los candidatos se guardan dentro de `SYMBOL_PROCESS_RESULT` bajo
`exhaustion_reversal_shadow`. Cuando la secuencia completa es válida también
se persiste el evento `EXHAUSTION_REVERSAL_SHADOW`.
