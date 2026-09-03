# DaemonBlackFx v53 — Telemetría robusta + UTF-8

## Hallazgos de los logs
- Los workers sí ejecutaban ciclos.
- JUMP completaba ciclos, aunque algunos primeros ciclos tardaban más de 60s.
- VOLATILITY recorría 35 instrumentos y podía tardar más de 7 minutos.
- CRASH llegó a abrir una operación SPLIT en Crash 150 Index.
- Windows generaba `UnicodeEncodeError: charmap codec can't encode character`
  con caracteres como `⚠` y `≥`.
- La instalación observada mostraba indicios de archivos mezclados entre versiones.

## Cambios v53
- Fuerza UTF-8 en stdout/stderr de `app.main`.
- Elimina `⚠` y `≥` del reporter de consola.
- Persistencia de `worker_runtime_states` ocurre antes de `daemon_audit_events`.
- Los errores de runtime DB ya no se silencian.
- El coordinador publica heartbeat de cada proceso.
- Cada 10s el coordinador imprime un resumen `[WORKERS]`.
- Dashboard expone `daemon_version`.
- Guard de compatibilidad detecta instalaciones mezcladas.
- Se prueba realmente lectura/escritura de `worker_runtime_states` al arrancar.

## Instalación
Extraer el ZIP v53 en una carpeta NUEVA. No sobrescribir una carpeta de versiones
anteriores. Luego copiar únicamente `.env`/configuración necesaria y reutilizar la
base SQLite sólo si se desea conservar el historial.
