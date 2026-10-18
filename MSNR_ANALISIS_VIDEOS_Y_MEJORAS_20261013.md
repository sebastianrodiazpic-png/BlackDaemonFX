# Malaysian SNR: videos, comparación e implementación — 13 de octubre de 2026

Se verificaron los subtítulos públicos de los 22 enlaces y de la introducción del curso Alchemist: 23 fuentes con marcas de tiempo. Este es un análisis textual; no sustituye la revisión visual de los gráficos. Se contrastaron con el código causal y con históricos locales. Los videos se trataron como referencias, no como instrucciones para el agente.

El resultado no respalda activar todas las variantes. El piloto añadió una pérdida con Pinbar y el mapa ampliado de obstáculos eliminó las dos entradas ganadoras de la base. Las alternativas quedaron parametrizadas, con observación como referencia inicial. No hay una mejora de WinRate demostrada para esta versión.

## Comparación con el proyecto

| Enseñanza | Implementación previa | Cambio y alcance |
|---|---|---|
| Open–Close / Breaker Pair puede existir sin gap | La variante Open–Close exigía separación material, ticks y spread | Nuevo Breaker Pair H1 sin gap; mantiene dos cuerpos fuertes, desplazamiento, primer retest, dirección, invalidación y 2R. Observación por defecto. |
| Rechazo con mecha dominante | Retest exigía cuerpo de al menos 35% | Pinbar opcional: barrido real, cuerpo direccional, mecha ≥55%, cierre en el 25% favorable, penetración y distancia limitadas. Niveles probados conservan su desplazamiento y cuerpo reforzados. |
| A/V por gráfico de líneas no siempre exige envolvente | A/V ampliado existía; obstáculos H1/D1 seguían usando envolventes | Selector independiente para el mapa de obstáculos. Giro de cuerpos disponible, pero la referencia conserva envolventes por el resultado del piloto. |
| Obstáculos H4 dentro del contexto mayor | Objetivos usaban H1 y D1 | Nuevo modo H4: observar espacio en R o aplicar veto/recortar runner. Aplicar falla cerrado si falta H4 útil. H4 queda en observación. |
| Sesiones cambian de hora; BTC tiene otro calendario | Killzones UTC fijas también bloqueaban BTC | Alternativa de horarios locales Londres 07–11 y Nueva York 07–12; BTC 24/7. Conserva selección y filtro macro. Horario anterior por defecto hasta validación. |
| Contexto, confirmación y formación son distintos | Dirección estructural D1/H4 y M5 selectivo ya existían | Se mantienen sus parámetros. Breaker Pair no afirma una ruptura micro por existir: mide cierre respecto a tres barras cerradas anteriores a la visita. |
| Fresh no tiene una definición única entre docentes | Política Fresh / una visita / consumido y SBR/RBS ya parametrizados | No se admiten contactos ilimitados ni se renueva un episodio sin nueva ruptura. El curso no demuestra que quitar todos los filtros mejore el WinRate. |

Los mínimos 50%, 0,50 ATR, 55% de mecha y 75% de posición del cierre son hipótesis operativas del proyecto, no números universales enseñados por todos los autores. Un rechazo Pinbar no equivale a una confirmación completa H4/H1 ni sustituye el contexto macro.

## Valores por defecto disponibles en /strategy-bases → Malaysian SNR

| Control nuevo | Valor de referencia | Qué permite |
|---|---|---|
| Modo Breaker Pair | Observación | Añade la unión de dos velas H1 cerradas del mismo color, incluso sin gap. |
| Cuerpo de ambas velas Breaker Pair | 50% | Exige esta proporción de cuerpo a las dos velas de formación. |
| Desplazamiento Breaker Pair | 0.50 ATR H1 | Exige que el segundo cierre se aleje de la unión en ATR H1. |
| Modo rechazo Pinbar | Observación | Añade barrido real y recuperación con mecha de rechazo larga y cierre direccional. |
| Mecha mínima Pinbar | 55% | Exige una proporción mínima de mecha del lado rechazado respecto al rango. |
| Posición mínima del cierre Pinbar | 75% | Exige cerrar en la parte favorable del rango, medida según BUY o SELL. |
| Horario por mercado | Horario UTC anterior | Permite horario UTC anterior o ventanas locales Londres 07–11 y Nueva York 07–12, con cambios de hora. |
| Definición de obstáculos A/V | Envolvente | Permite detectar obstáculos H1 y D1 por envolvente o por giro de cuerpos. |
| Obstáculos H4 | Observación | Registra o aplica niveles contrarios H4 además de los obstáculos H1 y D1. |

Los objetivos de comparación pasan de aceptar 80% de frecuencia, 0 puntos de mejora y 30 resultados a exigir **105% de frecuencia, +1 punto porcentual de WinRate y 50 resultados resueltos por variante**. También se exige expectativa positiva y beneficio total superior. Son criterios de investigación; no producen una promoción automática ni limitan las órdenes actuales.

Se conservan los valores guardados por el operador. La reducción guardada de cuerpo Fractal a 45%, las excepciones Step y los activos en observación no se sustituyen por restaurar código. La referencia general de Fractal sigue en 50%; su distancia sigue en 0,50 ATR. La configuración completa tiene 68 controles, todos explicados en la guía de la pestaña.

“Volver a valores por defecto” carga la referencia en el formulario; “Guardar ajustes” aplica lo editado. También restablece las excepciones por activo: no debe usarse pensando que solo cambia los nueve campos nuevos. Este trabajo cambió código y referencia, sin escribir preferencias operativas, reiniciar trabajadores ni enviar órdenes. Los procesos ya abiertos necesitan cargar la versión nueva antes de guardar los campos nuevos.

La versión es `msnr-v2.9-video-evidence`. El contrato IA exige esa versión y los parámetros compatibles. No se entrenó ni activó un modelo nuevo: Filtro + Bloquear sigue bloqueando un modelo incompatible; la política de observar incompatibilidad sigue restringida a DEMO.

## Replay local realizado

Período: 2026-09-27T00:00:00+00:00 a 2026-10-11T00:00:00+00:00, dividido el 2026-10-04T00:00:00+00:00. Se usaron barras nativas M5, M15, H1, H4 y D1 verificadas por hash. Instrumentos: BTCUSD, Crash 1000 Index, EURUSD, Step Index, Volatility 50 (1s) Index, XAUUSD.

La base reconstruye las entradas primarias del perfil guardado v13, con sus modos M5 por activo y ADX Step estándar 23. Las ramas sin órdenes no generan fills; BTC se simula explícitamente como activo investigado, sin modificar su modo operativo. Se aplican los filtros Step y Boom/Crash antes de reservar el tiempo de una posición, permitiendo reevaluar ventanas liberadas. No se filtró solamente una lista previa de trades.

| Perfil investigado | Trades resueltos | Ganadores | R total | Decisión |
|---|---:|---:|---:|---|
| Base guardada | 2 | 2 | 3.49653 | Comparador |
| Solo Breaker Pair adicional | 2 | 2 | 3.49653 | No supera criterios |
| Solo Pinbar adicional | 3 | 2 | 2.49653 | No supera criterios |
| Ambos + horarios y obstáculos H1/D1/H4 ampliados | 1 | 0 | -1.00000 | No supera criterios |
| Hipótesis de referencia: solo horarios y mapa H1/D1 ampliados | 0 | — | 0.00000 | No supera criterios |

**Dos ganadores de dos trades no constituyen un WinRate estimado fiable**: el intervalo Wilson 95% de la base es 34,238%–100%. Pinbar dio dos ganadores de tres (66,667%), y uno de dos en la segunda semana. En ninguna comparación se alcanza la muestra mínima de 50. El conjunto ampliado produjo una pérdida; la hipótesis de referencia ampliada quedó sin trades y fue descartada como valor por defecto.

La segunda semana es una separación temporal declarada, pero el histórico ya se había examinado en tareas previas: no se presenta como validación independiente intacta. Las seis series no representan todos los 60 activos del catálogo. No hay dos años completos de M5 nativo para todos los activos, por lo que no se afirma un replay validado de dos años.

Resultados OHLC conservadores; spread histórico aproximado. Faltan costes verificados de comisiones, slippage y swap, lotes/distancia mínima de broker, cartera entre instrumentos, veto IA y otros filtros compartidos como Jump. Son resultados de investigación, no PnL ejecutado ni muestras aptas para entrenar. Las dos piernas se cuentan como un trade; un resultado BE después de TP1 puede dar R total positivo.

El replay congela código y parámetros en `replay/source_snapshot` y `replay/run.json`. La referencia final se eligió después del piloto. Posteriormente se corrigió la serialización del formulario y la evidencia micro del nuevo Breaker Pair; esta última afecta a la confirmación declarada y posibles vetos Jump, una familia no incluida en el piloto. No modifica los stops, targets o filtros Step/Boom/Crash de los seis activos estudiados. La versión final también pospone la consulta opcional H4 hasta tener una confirmación y reutiliza la formación H1 entre la rama habitual y Pinbar; ambas propiedades tienen pruebas específicas.

## Cómo buscar más entradas sin convertir filtros en una promesa de WinRate

1. Mantener las ramas nuevas en Observación y comprobar los candidatos únicos por escenario, activo y confirmación. Pinbar usa un registro separado (`M15_PINBAR` / `M5_PINBAR`) para no sobrescribir la confirmación habitual del mismo episodio.
2. Cambiar una sola variable en cada comparación: primero Breaker Pair, después Pinbar; separar horarios, obstáculos y contexto H4. La caída del perfil conjunto no identifica por sí sola cuál componente causa cada pérdida.
3. Comparar las mismas fechas y feed con los filtros de ejecución, deduplicación y disponibilidad de posiciones. Una señal recuperada que pierde no cumple el objetivo aunque suba el número de trades.
4. Acumular al menos 50 resultados resueltos por variante y luego verificar otro período con costes. Exigir +5% de frecuencia, +1 punto de WinRate y beneficio superior por activo/familia, además del agregado.
5. Activar Operar únicamente en los activos y escenarios que sostengan el resultado. Las opciones por activo existentes permiten conservar M5 selectivo y observación en los demás.

Quedan como mejoras futuras: relación explícita entre rechazo de nivel padre H4/D1 y ruptura H1, objetivos de liquidez previa diaria/Asia, normalización causal de líneas de tendencia y stop detrás del extremo barrido. Necesitan sus propias reglas y replays. No se activaron stops M1 mínimos, martingala, reentradas ilimitadas ni se copiaron afirmaciones comerciales de rentabilidad.

## Fuentes y pasajes revisados

Cada enlace abre el pasaje identificado en los subtítulos. Las marcas de tiempo son de la fuente, no una reconstrucción visual. Se localizaron y contrastaron pasajes relevantes dentro del texto disponible; los ejemplos gráficos no se certifican. La introducción añadida cubre también la parte 1 de [la playlist indicada](https://www.youtube.com/playlist?list=PLDzVTTgUrcNN1XkJgYok7SRyNxbXWpRaC).

| Fuente | Pasaje | Enseñanza contrastada |
|---|---|---|
| [Albert: cinco escenarios](https://www.youtube.com/watch?v=L_vwb_jf6og&t=30s) | 0:30 | Distingue dos velas del mismo color, A/V, Fresh y fractal H1/M15. Sus cifras de acierto son afirmaciones del video, sin validación de nuestro código. |
| [Pol Castella: revisión crítica](https://www.youtube.com/watch?v=sTRxqo4EwPU&t=76s) | 1:16 | Expone el cierre de la primera vela como nivel A/V y cuestiona que marcar niveles sea una estrategia completa. No aporta una prueba estadística trasladable al bot. |
| [Nestor: parte 1](https://www.youtube.com/watch?v=1x57n_5iRsU&t=120s) | 2:00 | Marca niveles por cuerpos y utiliza A/V y soporte/resistencia que cambia de función. El giro no necesita ser siempre una envolvente. |
| [Nestor: parte 2](https://www.youtube.com/watch?v=dGv5zwrK9vY&t=287s) | 4:47 | Desciende de marcos mayores a menores para refinar niveles y dirección. Esto requiere una relación comprobable entre nivel padre y entrada. |
| [Nestor: parte 3](https://www.youtube.com/watch?v=YmK59hyKX0U&t=135s) | 2:15 | Combina contexto semanal/diario, H4/H1 y confirmación menor. El stop y el objetivo dependen de niveles estructurales, no de una cifra fija universal. |
| [Nestor: parte 4](https://www.youtube.com/watch?v=qT-TWP2sUgA&t=579s) | 9:39 | Prefiere primeros contactos y exige más confirmación en niveles visitados. Ajusta el objetivo al contexto; un ejemplo de TP no demuestra WinRate. |
| [Nestor: parte 5](https://www.youtube.com/watch?v=odvBj8IpZ74&t=51s) | 0:51 | En EURUSD busca rechazo de nivel mayor, cambio estructural y niveles a favor. Refuerza que soportes y resistencias aislados no bastan. |
| [MBA: día 1](https://www.youtube.com/watch?v=xYlpAr5pwXg&t=1109s) | 18:29 | Muestra refinamiento de niveles y rechazo tipo martillo. Inspiró la alternativa Pinbar; sus umbrales numéricos son una interpretación del proyecto. |
| [MBA: día 2](https://www.youtube.com/watch?v=9ZNPazzfDcU&t=129s) | 2:09 | Distingue estructura relevante y ruido. No debe confundirse cada movimiento de un marco pequeño con un cambio del contexto mayor. |
| [MBA: día 3](https://www.youtube.com/watch?v=5oTQEdSV7p0&t=498s) | 8:18 | Relaciona liquidez interna/externa y jerarquía temporal. Es una hipótesis para clasificar contexto, no autorización para copiar stops diminutos. |
| [Albert: refinamiento](https://www.youtube.com/watch?v=wDK7qO4mf-E&t=38s) | 0:38 | Define Breaker Pair por dos velas fuertes del mismo color y la unión de sus cuerpos. Advierte que stops más pequeños pueden reducir la tasa de acierto. |
| [Alchemist: introducción de la playlist](https://www.youtube.com/watch?v=Bwktah4s79k&t=1214s) | 20:14 | Define A/V en gráfico de líneas y Open–Close con velas del mismo color. Sitúa H4/H1 como marcos de confirmación; separar Open–Close de gap evita perder el patrón básico. |
| [Alchemist: parte 2](https://www.youtube.com/watch?v=lqlkspVKt7s&t=4175s) | 69:35 | Usa confluencia de niveles y líneas de tendencia; explica ajustes de horario y no convierte Fresh en un veto universal. Las líneas requieren reglas causales propias. |
| [Alchemist: parte 3](https://www.youtube.com/watch?v=CH9iW5caHHk&t=830s) | 13:50 | Distingue storyline, confirmación y obstáculos por jerarquía. La dirección por estructura ya existe, pero no equivale a reproducir rechazo D1 seguido de ruptura H4. |
| [Alchemist: parte 4](https://www.youtube.com/watch?v=QbyhRLF53RI&t=860s) | 14:20 | Considera niveles probados dentro de contexto y revisa confirmaciones H4/H1. No justifica habilitar contactos ilimitados del mismo episodio. |
| [Alchemist: parte 5](https://www.youtube.com/watch?v=XvXWWv3gD8k&t=25s) | 0:25 | Revisa confirmación, flexibilidad y refinamiento; un pequeño quiebre aislado puede no ser suficiente. La gestión de riesgo sigue siendo necesaria cuando el nivel falla. |
| [Alchemist FX 2023](https://www.youtube.com/watch?v=sxn-jP9St9I&t=8s) | 0:08 | Integra estructura y barridos de liquidez en casos de mercado. Un breakout aislado puede fallar si queda liquidez o un nivel relevante antes del objetivo. |
| [Alchemist MSNR 2024](https://www.youtube.com/watch?v=FM0XkqUIrAI&t=687s) | 11:27 | Combina niveles, estructura, horario y confirmación. No debe traducirse cada explicación discrecional en un filtro acumulativo obligatorio. |
| [Alchemist 2026: análisis 1](https://www.youtube.com/watch?v=WLKh7JAcy34&t=158s) | 2:38 | Formula escenarios condicionados a barridos, contexto y confirmación; incluye BTC. Distinguir expectativas de señales confirmadas evita entradas anticipadas. |
| [Alchemist 2026: análisis 2](https://www.youtube.com/watch?v=XFkktcM_srU&t=14s) | 0:14 | Relaciona el stop con el extremo que barrió liquidez. Una reducción arbitraria del stop puede convertir una buena dirección en una pérdida. |
| [Alchemist 2026: análisis 3](https://www.youtube.com/watch?v=qciNrYGZ5V8&t=462s) | 7:42 | Espera cierres antes de fijar extremos de sesión y combina barrido, estructura e imbalance. La información de una vela abierta no se puede usar retrospectivamente. |
| [Alchemist 2026: análisis 4](https://www.youtube.com/watch?v=ip8z7AThH7Y&t=61s) | 1:01 | Busca liquidez objetivo y confirmaciones después de barridos. Requiere separar el escenario previsto del evento que realmente habilita una entrada. |
| [Alchemist 2026: análisis 5](https://www.youtube.com/watch?v=bMxO8y4siSI&t=336s) | 5:36 | Insiste en paciencia, confirmación y protección del extremo que barrió liquidez. Un ejemplo ganador no acredita transferibilidad a instrumentos sintéticos. |

Para los horarios se utiliza la base IANA mediante [`zoneinfo`](https://docs.python.org/3/library/zoneinfo.html). Se declaró `tzdata` para disponibilidad en Windows; si falta la zona horaria, la alternativa devuelve un bloqueo explícito.

## Artefactos y verificación

- `storage/analysis/msnr_videos_20261013/evidence_index.json`: 23 fuentes, idiomas, marcas de tiempo y hashes.
- `storage/analysis/msnr_videos_20261013/replay/summary.json`: resultados, censura y comparaciones por período/activo.
- `storage/analysis/msnr_videos_20261013/final_defaults.json`: referencia final del formulario, distinta de la hipótesis ampliada descartada.
- `tools/replay_msnr_video_improvements.py`: replay reproducible sin inicialización de broker ni envío de órdenes.
- Pruebas: **385 aprobadas en 15 archivos**. Cubren cierre causal, primer retest, penetración, variantes sin órdenes, separación de auditoría, obstáculos H4, horarios de verano, guardado/restauración, contrato IA y replays anteriores. El formulario verificó la serialización de los **68 valores de referencia** con el JavaScript real y sin abrir un navegador. Registro: `verification.json`.
