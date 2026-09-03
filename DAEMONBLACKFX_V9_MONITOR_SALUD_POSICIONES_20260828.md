# DaemonBlackFx v9 - Monitor de salud de posiciones abiertas

## Objetivo
Añadir una capa de observación en tiempo real para posiciones abiertas sin modificar de forma automática la gestión del trade.

## Principio de seguridad
El monitor es asesor. No cierra posiciones ni modifica SL/TP. Las decisiones automáticas existentes (TP, SL y Break Even) continúan separadas.

## Señales evaluadas
- Precio actual de la posición leído desde MT5 por el monitor existente.
- Progreso actual expresado en R respecto al riesgo estructural inicial.
- Estado de Break Even.
- Score y porcentaje de confirmaciones originales de la entrada.
- Último análisis disponible del mismo instrumento.
- Dirección del último candidato confirmado.
- Condiciones críticas faltantes.
- Divergencia reciente favorable o contraria.

## Recomendaciones
- MANTENER: salud >= 75.
- VIGILAR: salud entre 55 y 74.9.
- PROTEGER: salud entre 35 y 54.9.
- SALIDA A EVALUAR: salud < 35.

Estas categorías son recomendaciones visuales. No provocan cierres automáticos.

## Dashboard
La tabla de posiciones abiertas muestra:
- instrumento y dirección;
- score de salud 0-100 y grado;
- recomendación;
- R actual;
- Break Even;
- score y porcentaje de confirmaciones de entrada;
- precio actual;
- razones principales de la recomendación.

## Arquitectura
El dashboard no crea una segunda conexión MT5. El LiveTradingEngine publica snapshots del monitor de posiciones y la interfaz combina esos snapshots con el análisis más reciente ya calculado por el daemon.

## Validación
Regresión disponible: 170 pruebas aprobadas en entorno sin MetaTrader5 nativo. Las pruebas dependientes de MetaTrader5 continúan requiriendo Windows + terminal MT5.
