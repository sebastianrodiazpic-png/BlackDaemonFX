# DaemonBlackFx v92 — guard compatible con launchers Python de Windows

## Falso positivo corregido

Algunos entornos virtuales de Windows mantienen un `python.exe` lanzador y otro
proceso para el intérprete real. Ambos muestran el mismo comando. v91 excluía
sólo el PID del intérprete y podía confundir su lanzador padre con un coordinador
legacy independiente.

## Nueva validación

- Obtiene `ProcessId` y `ParentProcessId` de los procesos Windows.
- Reconstruye toda la cadena de ancestros del intérprete actual.
- Excluye esa cadena del control de coordinadores duplicados.
- Continúa detectando cualquier `multi-bot-daemon` perteneciente a un árbol de
  procesos independiente.
- Mantiene el mutex atómico de v90/v91 como primera barrera.

Con esto, un arranque limpio puede continuar aunque el virtualenv utilice un
launcher, mientras un coordinador realmente independiente sigue siendo bloqueado.
