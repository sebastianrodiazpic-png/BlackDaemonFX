# Daemon interval and live progress fix

## Problema corregido

El daemon iniciaba `CICLO #0001` y no mostraba actividad hasta terminar el análisis de todos los símbolos. Con 76 instrumentos, H1/M15/M5 y confirmaciones SMC, esto podía durar varios minutos.

Además, el intervalo configurado debía interpretarse como cadencia objetivo desde el inicio del ciclo, no como una espera adicional después de terminar el análisis.

## Cambios

1. Progreso inmediato por símbolo:
   - `[01/76] START ...`
   - `[01/76] END ... | 1.42s | NO SIGNAL`
2. Medición individual del tiempo de cada símbolo.
3. Medición de duración total del ciclo.
4. Cálculo real del próximo ciclo:
   `next_delay = max(0, interval - cycle_elapsed)`.
5. Si el ciclo tarda más que el intervalo, el siguiente ciclo empieza inmediatamente y se informa el exceso.
6. Monitor de posiciones cooperativo entre símbolos y entre ciclos.
7. MetaTrader5 se mantiene en un único hilo para evitar llamadas concurrentes sobre la misma conexión.

## Limitación importante

`--position-monitor-interval 2` significa que el daemon intentará revisar posiciones cada 2 segundos, pero durante el análisis de un símbolo el monitor no interrumpe una llamada MT5/SMC en curso. El monitor se ejecuta antes y después de cada símbolo, por lo que el retraso práctico queda limitado por la duración de un símbolo y no por todo el ciclo de 76 instrumentos.

## Salida esperada

```text
CICLO #0001 | ... | símbolos=76
[01/76] START Volatility 10 Index
[01/76] END   Volatility 10 Index | 0.83s | NO SIGNAL
[02/76] START Volatility 25 Index
...
RESUMEN DEL CICLO #0001
Duración del ciclo: 82.41s
Intervalo objetivo: 30s
Próximo ciclo en: 0.00s
⚠ Ciclo excedió el intervalo por: 52.41s
```
