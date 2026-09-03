# DaemonBlackFx v90 — instancia única de MultiBot

## Problema corregido

Windows podía iniciar dos veces el mismo comando `multi-bot-daemon`. Cada
coordinador generaba sus 12 workers, duplicando análisis, lecturas MT5, acceso a
SQLite y el riesgo de enviar una misma orden en una carrera entre procesos.

## Protección implementada

- El coordinador adquiere un bloqueo atómico antes de abrir el dashboard o crear workers.
- En Windows se utiliza un mutex del sistema operativo por carpeta de proyecto.
- Una segunda ejecución finaliza con `MULTIBOT_ALREADY_RUNNING` e informa el PID propietario.
- El bloqueo se libera normalmente al cerrar el coordinador.
- Si el proceso termina abruptamente, Windows libera automáticamente el mutex;
  el archivo JSON de diagnóstico no impide el siguiente arranque.
- Linux/macOS usan un bloqueo `flock` equivalente.

## Resultado esperado

Una ejecución correcta mantiene 13 procesos Python: un coordinador y 12 workers.
Aunque el comando sea ejecutado dos veces, el segundo no crea procesos hijos.
