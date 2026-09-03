# DaemonBlackFx v82 — recuperación de selección sintética

El perfil persistente `SYNTHETICS` podía quedar vacío. Los seis workers seguían
vivos, pero todos ejecutaban ciclos con cero instrumentos y el supervisor los
mostraba como `RUNNING Cn 0/0`.

Al iniciar un coordinador con familias sintéticas, v82 recupera una preferencia
vacía usando el catálogo sintético disponible en MT5, persiste la corrección y
registra `EMPTY_SYNTHETIC_SELECTION_RECOVERED`.

Además, cualquier ciclo que reciba cero instrumentos se publica como
`DEGRADED_NO_SYMBOLS`; el heartbeat conserva ese estado y no lo reemplaza por
un falso `RUNNING`.
