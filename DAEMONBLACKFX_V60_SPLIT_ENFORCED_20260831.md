# v60 — Separación sintética obligatoria

La captura v59 mostró `SYNTHETICS / magic 26082026 / 1 worker`, demostrando que
se estaba ejecutando la ruta legacy agregada y no el coordinador split.

Corrección:
- `synthetics-split-daemon` -> 6 procesos.
- `synthetic-daemon` -> alias protegido del split de 6 procesos.
- `demo-daemon` -> alias protegido del split de 6 procesos.
- Se elimina `synthetic-daemon -> SYNTHETICS` del mapa de workers individuales.
- Al iniciar split, el runtime legacy `SYNTHETICS / 26082026` se marca SUPERSEDED.
- El dashboard central conserva v58.
- Persistencia independiente de instrumentos conserva v57.
- No cambia SMC, riesgo, BE, runner, ORB ni Forex.
