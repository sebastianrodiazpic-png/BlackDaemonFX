# DaemonBlackFx v113.3

## Compatibilidad con el catálogo público actual de Deriv

- Reconoce `underlying_symbol_name` y `underlying_symbol`, campos publicados
  actualmente por `active_symbols`.
- Mantiene compatibilidad con los campos del contrato anterior.
- Nunca sustituye un instrumento por otro de nombre parecido.
- Los instrumentos exclusivos de MT5 se excluyen del análisis externo.
- Un instrumento no compatible ya no detiene los demás símbolos de su worker.
- El worker queda `BLOCKED_PREFLIGHT` únicamente si ninguno de sus instrumentos
  dispone de datos externos válidos.

`Boom 99 Index` existe como CFD en MT5, pero no aparece actualmente en el
catálogo público de `active_symbols`. No se mapea a Boom 50/150/300/500/600/900
o 1000 porque sus series de precios no son equivalentes.

