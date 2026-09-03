# DaemonBlackFx v50 — Audit Log compacto en XLSX

## Problema
Excel admite como máximo 32.767 caracteres por celda. Algunos eventos persistidos
en `daemon_audit_events.payload_json` superan ese tamaño porque contienen el diagnóstico
completo de un ciclo.

## Solución
La base de datos conserva el payload íntegro. El XLSX ya no exporta `payload` ni
`payload_json` completos.

La hoja `Audit Log` muestra:
- id
- fecha
- source
- bot_profile
- daemon_magic
- event_type
- instrumento
- acción
- motivo
- execution_key
- position ticket
- ciclo
- resumen
- `payload_completo_en_db = SÍ`

El resumen tiene un máximo de 4.000 caracteres y ninguna celda textual puede superar
30.000 caracteres como defensa adicional.

## Resultado
- No se pierde información en SQLAlchemy.
- El XLSX permanece legible.
- Se elimina el warning `Cell contents too long`.
- La arquitectura multi-proceso continúa usando un único escritor XLSX.
