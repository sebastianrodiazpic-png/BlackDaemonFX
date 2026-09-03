# DaemonBlackFx v91 — bloqueo de coordinadores heredados

## Hallazgo

El mutex incorporado en v90 impide dos coordinadores v90, pero un proceso v89 o
anterior que ya estaba activo no posee ese mutex. v90 podía advertir su presencia
y continuar, creando un segundo conjunto de workers.

## Corrección

El inicio de `multi-bot-daemon` ahora aplica dos barreras antes del dashboard:

1. Mutex atómico para impedir carreras entre versiones v90/v91.
2. Inspección de procesos Windows para detectar cualquier coordinador legacy
   cuyo comando contenga `--mode multi-bot-daemon`.

Si encuentra un coordinador heredado, libera el mutex recién adquirido, informa
el PID anterior y aborta antes de crear dashboard, escritor XLSX o workers.

El escaneo falla de forma segura: si PowerShell/CIM no puede validar procesos,
el bot no opera hasta resolver el diagnóstico, evitando una ejecución duplicada.
