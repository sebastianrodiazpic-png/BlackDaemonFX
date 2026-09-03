# DaemonBlackFx v77 — MultiBot híbrido + front liviano

## Motivo del rollback
El MultiBot de un solo proceso serializaba demasiadas tareas:
- 6 familias sintéticas;
- 4 shards Forex;
- ORB;
- monitor de posiciones;
- Break Even / runner;
- auditoría visual;
- lecturas MT5 H1/M15/M5/M1;
- persistencia SQLAlchemy.

Una operación lenta dentro del proceso retrasaba las demás.

## Arquitectura recomendada v77
`multi-bot-daemon` vuelve al coordinador multiproceso:
- workers de cálculo independientes;
- un único dashboard central;
- una única exportación XLSX coordinada;
- SQLAlchemy compartido con WAL;
- magics y ownership independientes.

El modo `unified-multibot-daemon` queda disponible sólo como experimental.

## Optimización del front
- snapshot completo del dashboard: caché 1,5 s;
- polling dashboard: 2 s;
- polling instruments: 2,5 s;
- polling account: 2,5 s;
- se conservan las cachés v74 de Account, Instruments y consultas auxiliares.

Esto desacopla el ritmo de cálculo de los workers del ritmo de lectura del
navegador y reduce consultas repetidas a SQLite.

## Se conserva
- ORB Entrada vs. Ahora v75;
- ORB contexto H1/M15 v76;
- Forex TP2 -> TP3 -> TP4 progresivo;
- sintéticos separados por familia;
- selecciones independientes;
- auditoría SQLAlchemy/XLSX;
- riesgo y ownership por magic.
