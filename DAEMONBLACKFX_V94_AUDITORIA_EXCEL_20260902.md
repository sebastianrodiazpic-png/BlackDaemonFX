# DaemonBlackFx v94 — descarga robusta de auditoría Excel

## Error corregido

La descarga desde `/account/trade/{id}/audit` podía fallar con
`AUDIT_INTEGRITY_ERROR` cuando un trade histórico no tenía tesis visual o cuando
la base contenía snapshots antiguos reutilizando el mismo `trade_id`.

## Comportamiento nuevo

- Combina la vista estadística con la fila operativa original del mismo trade.
- Filtra snapshots por trade ID, instrumento, ticket, perfil y magic.
- Los snapshots incompatibles se excluyen y se informan en el Excel; nunca se
  mezclan con la operación solicitada.
- La tesis se recupera, en orden, desde snapshot append-only, auditoría visual,
  confirmación persistida, details del trade o ficha contractual histórica.
- Una ficha contractual histórica declara expresamente que las confirmaciones
  visuales completas no estaban disponibles; no inventa evidencia.
- Las exportaciones usan un archivo temporal único por solicitud, evitando
  colisiones entre descargas simultáneas.
- Una contradicción no recuperable devuelve HTTP 422 con JSON controlado en vez
  de imprimir un traceback del servidor.

La base de datos permanece inmutable durante la descarga.
