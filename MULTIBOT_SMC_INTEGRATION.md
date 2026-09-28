# Integración SMC en multi-bot-daemon

La configuración compartida está en `strategy/execution/worker_rules.py`. La usan el arranque individual de cada worker (invocado por multi-bot-daemon) y el modo experimental unified-multibot-daemon.

Para perfiles SMC establece explícitamente H1 adaptativo, política H1_PRIMARY y gatillo dual M5/M1 manteniendo M5 como marco de liquidez. Se conserva el control de posiciones/pendientes del motor común y su telemetría por worker. El coordinador limita el intervalo de consulta SMC a 10 segundos; el scheduler decide cuándo hay nueva vela M1. Los riesgos, magics y permisos de ejecución del usuario se conservan.

ORB conserva su estrategia independiente y M5. IDX_OPEN no se reactiva.

Cada worker imprime `WORKER_RULES_LOADED` al arrancar: perfil, versión de reglas, temporalidad de eventos, parámetros H1, antigüedad máxima, control de posiciones, identidad de telemetría y permiso de ejecución. Esta línea comprueba qué configuración cargó el proceso; modificar archivos no actualiza procesos que ya estaban abiertos.

Corregido el contrato de Jump: el motor entrega `price_action_confirmations` con rechazo, microestructura, desplazamiento y cierre fuerte. Jump consume esta evidencia conservando sus umbrales y vetos. No se modifica el denominador de confirmación adaptativo.

Corregida la hora `confirmation_closed_at`: M1 suma un minuto y M5 cinco, de acuerdo con el gatillo seleccionado.

No se iniciaron ni reiniciaron workers ni se enviaron órdenes. El código se carga al próximo arranque habitual del daemon. Las mejoras propuestas sobre breakout H1 y calibración estadística no se convierten automáticamente en reglas nuevas mediante esta integración.

Prueba offline:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_multibot_worker_rules.py tests/test_active_position_guard.py tests/test_dual_trigger.py tests/test_worker_telemetry_sandbox.py -q -p no:cacheprovider
```
