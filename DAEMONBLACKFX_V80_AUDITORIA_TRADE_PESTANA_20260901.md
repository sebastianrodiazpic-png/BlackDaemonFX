# v80 — Auditoría Entrada vs. Ahora por trade

/account deja de desplegar los últimos snapshots dentro de la tabla.
Cada trade con snapshots muestra `Abrir auditoría visual completa ↗`.

La acción abre una pestaña nueva:
`/account/trade/<source_trade_id>/audit`

La pestaña consulta un endpoint dedicado y carga TODOS los snapshots persistidos
de ese trade desde SQLAlchemy, en orden cronológico.

Incluye:
- instrumento, dirección, estado/cierre, RR real y PnL;
- tesis de entrada;
- último estado observado;
- cantidad de snapshots;
- MFE/MAE observados a partir del histórico;
- timeline completo;
- decisión, score, confirmación, R, H1, estructura y patrón chartista;
- contexto técnico persistido expandible por snapshot.

La tabla principal /account queda más limpia y rápida.
