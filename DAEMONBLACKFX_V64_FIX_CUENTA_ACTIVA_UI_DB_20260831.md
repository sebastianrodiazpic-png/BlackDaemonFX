# DaemonBlackFx v64 — Fix Cuenta activa

## Causa real
La v63 introdujo un error de sintaxis JavaScript en `auditHtml()` al agregar
las confirmaciones persistentes. Debido a eso el navegador no ejecutaba `go()`,
por lo que `/api/account` nunca se consultaba y toda la página quedaba con los
valores iniciales (0 / — / "verificando ruta").

## Corrección
- `auditHtml()` reescrito con JavaScript válido y más simple.
- Validación de sintaxis con `node --check`.
- `fetch('/api/account')` ahora comprueba HTTP status.
- Si la API falla, la ruta DB muestra el error real.
- Se mantiene v63: DB estable, recuperación histórica automática y diagnóstico de ruta.
- Se mantiene v62: confirmaciones/patrones persistentes en Account.
