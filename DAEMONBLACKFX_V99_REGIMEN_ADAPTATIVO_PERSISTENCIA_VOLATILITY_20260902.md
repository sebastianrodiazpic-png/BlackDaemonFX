# DaemonBlackFx v99 — régimen adaptativo, persistencia y Volatility por shards

## Diagnóstico de `ARPS_REGIME_BLOCKED`

`ARPS_REGIME_BLOCKED` no representa una excepción del aplicativo. Significa que
ARPS descartó la entrada porque M15 todavía no acredita un régimen direccional
operable. En los registros revisados se repitieron principalmente dos motivos:

- `ADX_M15_INSUFICIENTE`: el ADX actual estaba por debajo del umbral de fuerza.
- `SIN_TENDENCIA_M15`: EMA 50/200 y la pendiente de EMA 50 no definían una
  tendencia consistente.

La versión anterior usaba un ADX fijo de 20 para todos los índices. Ese valor
podía ser demasiado rígido para instrumentos cuyo rango normal de ADX es menor,
aun cuando su estructura direccional era utilizable. Además, los análisis leídos
desde SQLite llegaban a la vista sin la traducción y las métricas de diagnóstico,
por lo que la pantalla podía mostrar `Sin motivo adicional informado`.

## Corrección aplicada

ARPS conserva todas sus confirmaciones estructurales, pero el umbral ADX ahora es
adaptativo por instrumento:

- referencia: percentil 35 de hasta 160 velas M15 cerradas anteriores;
- mínimo de historia: 30 observaciones válidas;
- umbral efectivo limitado entre 16 y 20;
- separación absoluta EMA 50/200 mínima: `0.08 × ATR(M15)`;
- pendiente absoluta de EMA 50 en tres velas mínima: `0.02 × ATR(M15)`.

Por tanto, la estrategia no entra sólo porque el ADX bajó de 20. También debe
existir dirección EMA, pendiente, régimen ATR M5, spread aceptable, BOS y
pullback M5, rechazo M1 y continuación confirmada por la siguiente vela M1.
Boom conserva sólo BUY, Crash sólo SELL y las demás familias permiten ambos
sentidos según el régimen detectado.

El dashboard ahora presenta `ESPERANDO RÉGIMEN` y explica:

- ADX actual y umbral adaptativo efectivo; o
- separación EMA/ATR y pendiente EMA/ATR;
- cada confirmación M5/M1 que todavía falta cuando el régimen ya es válido.

Es normal que algunos instrumentos continúen mostrando
`ARPS_REGIME_BLOCKED` durante mercados laterales. El cambio reduce bloqueos
artificiales del umbral fijo; no elimina el filtro de seguridad.

## Persistencia protegida

- La ventana crítica entre fill MT5 y commit SQLite está serializada frente al
  recuperador de posiciones del monitor.
- `broker_position_ticket` actúa como tercera clave idempotente, además de
  `execution_key` y `external_ticket`.
- Si el monitor alcanzó a importar primero una posición, la misma fila se
  promueve con la identidad y tesis completas del trade, sin crear un duplicado.
- El monitor omite filas repetidas del mismo ticket antes de aplicar gestión de
  break-even o cierre.

## Reducción de latencia en Volatility

El universo SMC de Volatility se reparte de forma determinista entre cuatro
workers independientes:

| Perfil | Modo | Magic |
|---|---|---:|
| `VOLATILITY_1` | `volatility-1-daemon` | 26082401 |
| `VOLATILITY_2` | `volatility-2-daemon` | 26082402 |
| `VOLATILITY_3` | `volatility-3-daemon` | 26082403 |
| `VOLATILITY_4` | `volatility-4-daemon` | 26082404 |

Cada símbolo pertenece a un solo shard. El perfil antiguo `VOLATILITY` queda
disponible para ejecución manual, pero `multi-bot-daemon` ya no lo inicia para
evitar doble análisis y doble gestión.

## Arranque

Detenga completamente el daemon anterior, instale esta versión en una carpeta
limpia, conserve sus variables de entorno y active el entorno virtual. Luego:

```powershell
python -m app.main --mode multi-bot-daemon --execute --interval 30 --position-monitor-interval 2 --risk-percent 1.0 --min-rr 1.5 --dashboard --dashboard-port 8765
```

La consola debe informar:

```text
DAEMONBLACKFX VERSION: v99-persistence-guard-volatility-shards-adaptive-arps
```

En el administrador de procesos debe existir un coordinador y una sola instancia
por modo worker. Los cuatro modos `volatility-1-daemon` a
`volatility-4-daemon` son procesos distintos esperados, no duplicados.

## Validación técnica

- Compilación de `app`, `dashboard`, `database`, `strategy` y `reporting`: OK.
- Pruebas específicas v49/v70/v88/v98/v99: 27 aprobadas.
- Suite completa v99: 479 aprobadas y 17 fallos heredados.
- Suite completa del ZIP base: 464 aprobadas y 19 fallos. Los 17 casos que aún
  fallan en v99 ya fallaban en el ZIP base; esta implementación no agregó una
  regresión a la suite existente.
