# DaemonBlackFx v88 — GOLD integrado al MultiBot persistente

- Un único comando `--mode multi-bot-daemon` inicia coordinador, dashboard y todos
  los workers: seis sintéticos, cuatro Forex, GOLD y ORB.
- GOLD conserva magic exclusivo `26082029` y se inicia antes de ORB.
- El coordinador resuelve una sola ruta SQLite y la pasa explícitamente a todos
  los procesos mediante `DAEMONBLACKFX_DB_PATH`.
- SQLite continúa en WAL, con timeout de escritura y base estable fuera del ZIP.
- Los workers no exportan Excel; sólo el coordinador genera el consolidado.
- GOLD conserva tesis inmutable en `trade_visual_audits`, timeline append-only en
  `trade_audit_snapshots`, runtime en `worker_runtime_states` y acceso desde
  `/account/trade/<id>/audit` con exportación Excel.
- El arranque falla temprano si falta GOLD/ORB/Forex/sintéticos o se repite un
  mode/magic, evitando instalaciones parcialmente mezcladas.
