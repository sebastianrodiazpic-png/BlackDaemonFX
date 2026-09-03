# DaemonBlackFx v57 — Persistencia Forex reforzada

## Problema corregido
En v56 la selección FOREX se escribía por versiones históricas y el dashboard mantenía además una copia en memoria/JSON. En determinadas secuencias de reinicio o reconstrucción del catálogo, esa combinación podía mostrar o reutilizar una selección distinta de la última guardada.

## Cambios v57
- SQLAlchemy mantiene una única fila autoritativa por `source + selection_profile`.
- Las filas duplicadas heredadas de v56 se compactan automáticamente al siguiente guardado.
- El historial de cambios continúa preservado en `daemon_audit_events`.
- Cada guardado realiza verificación `read-after-write`; si la lectura no coincide exactamente, la API devuelve error en vez de informar éxito.
- El dashboard recarga `SYNTHETICS`, `FOREX` y `ORB` desde SQLAlchemy en cada `/api/state`.
- El JSON de estado del dashboard deja de ser fuente de verdad para instrumentos.
- Una selección FOREX vacía también es válida y persistente: significa no abrir nuevas entradas Forex.
- FOREX y ORB permanecen completamente independientes.

## Pruebas específicas
- FOREX sobrevive a reinicio del repositorio.
- FOREX sobrevive a reinicio del dashboard incluso con un `last_state.json` obsoleto.
- FOREX y ORB conservan selecciones distintas después de reinicio.
- Múltiples guardados FOREX dejan una sola fila autoritativa.
- Una selección FOREX vacía no vuelve a convertirse automáticamente en el catálogo completo.

## Compatibilidad
Se mantienen todos los cambios acumulados hasta v56, incluyendo workers separados, auditoría visual persistente, runner 2R→3R→4R, Break Even, protección Forex rollover y ORB New York.
