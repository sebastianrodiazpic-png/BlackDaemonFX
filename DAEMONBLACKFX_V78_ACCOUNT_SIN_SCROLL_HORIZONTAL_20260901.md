# DaemonBlackFx v78 — /account sin scroll horizontal

## Mejora visual
La tabla del historial de Cuenta activa ahora usa `table-layout: fixed` y
distribución porcentual de sus 13 columnas.

- El contenedor sólo permite scroll vertical.
- Fechas, clasificación y auditoría pueden envolver texto.
- Confirmaciones persistentes ocupan 28% del ancho disponible.
- Se eliminó el `min-width: 360px` del bloque de auditoría.
- Pills y detalles largos pueden partir línea sin ampliar la tabla.
- En pantallas menores a 900 px se reduce tipografía/padding.

La información no se elimina ni se ocultan columnas: cambia únicamente la
forma en que se distribuye verticalmente.
