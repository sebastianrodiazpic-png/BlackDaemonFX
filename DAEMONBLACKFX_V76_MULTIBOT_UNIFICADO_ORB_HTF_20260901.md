# DaemonBlackFx v76 — MultiBot unificado + contexto HTF para ORB

## MultiBot unificado
`multi-bot-daemon` ahora usa un solo proceso Python.

Se mantienen como workers lógicos:
- BOOM
- CRASH
- VOLATILITY
- STEP
- JUMP
- FLIP
- FOREX_1..FOREX_4
- ORB

Cada perfil conserva:
- magic independiente;
- ownership de posiciones;
- selección persistente;
- reglas de riesgo;
- scheduler Forex M5;
- estrategia ORB independiente;
- auditoría SQLAlchemy;
- Entrada vs. Ahora;
- dashboard único.

Se comparte:
- una conexión MT5;
- un TradingRepository;
- un exportador XLSX;
- un dashboard;
- un proceso/PID.

Los modos split antiguos permanecen por compatibilidad, pero `multi-bot-daemon`
es la ruta recomendada.

## ORB con contexto superior
La entrada sigue siendo ORB M5:
breakout + retest + VWAP + POC + SL al 50% del rango.

Antes de autorizar la entrada se consulta contexto H1/M15 del pipeline MTF:
- H1 alineado: permite continuar.
- H1 neutral/no concluyente: no bloquea.
- H1 contrario: bloque crítico.
- H1 + M15 contrarios: conflicto reforzado.

Nuevos motivos:
- ORB_BREAKOUT_CONTRA_TENDENCIA_H1
- ORB_BREAKOUT_CONTRA_H1_Y_M15

El contexto se adjunta a la auditoría de entrada y al refresco Entrada vs. Ahora.
