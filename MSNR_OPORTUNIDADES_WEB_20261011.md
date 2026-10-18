# Malaysian SNR: oportunidades encontradas en la web y contraste con el proyecto

Revisión del 11 de octubre de 2026. Investigación y diagnóstico offline: no se cambiaron parámetros operativos, no se reinició el worker y no se enviaron órdenes.

## Resultado

La primera investigación debería comparar nuestra definición A/V envolvente con una definición por giro de cuerpos. La segunda debería probar un ciclo explícito de cambio de función SBR/RBS. Ambas amplían las estructuras que podemos evaluar manteniendo ruptura cerrada, retest confirmado, límites de entrada y riesgo.

Las fuentes consultadas son publicaciones de los autores de indicadores, documentación del proveedor y un trabajo académico. Describen implementaciones distintas de Malaysian SNR; no constituyen una norma única ni acreditan un WinRate para nuestro bot. Las propuestas de controles y pruebas de este documento son decisiones de investigación propias, todavía sin implementar.

## Referencia actual verificada

La API devolvió la preferencia **7**, actualizada a las 23:26:30 del 11 de octubre:

- Cuerpo Fractal H1: **45%**; distancia máxima: **0,50 ATR H1**.
- Veto direccional D1 en sintéticos: desactivado.
- Activos adicionales: lista vacía y modo desactivado.
- Continuación A/V: observación, cuerpo mínimo 50%, ADX mínimo 20.
- Exigir continuación exclusivamente Fresh: desactivado. Los controles existentes de niveles consumidos y de una visita previa siguen aplicando.
- Ventana de retest: 90 minutos; diagnóstico, caché, prioridad y análisis fuera del bloqueo habilitados.

Esta referencia sustituye a la preferencia 5 de la implementación anterior. Las nuevas hipótesis deben compararse contra ella. Los valores por defecto del panel siguen siendo un preset distinto de lo actualmente guardado.

## 1. Separar el nivel A/V de la exigencia de vela envolvente — primera prioridad

El autor de [Malaysian SnR + Storyline](https://www.tradingview.com/script/zHJLrkfS-Malaysian-SnR-Storyline/) describe niveles por unión del cierre y apertura entre velas alcistas y bajistas, junto a contexto de pivotes confirmados. Otra [implementación publicada por su autor](https://github.com/mdavidjeremiah/Malaysian-SnR-Storyline-TradingView-Indicator/blob/main/README.md) utiliza pivotes sobre cierres. Son variantes diferentes: no debe suponerse que cada cambio de color constituye un pivote significativo.

En `validation.py`, `av_levels()` exige cambio de color y, además, que el cierre de la segunda vela alcance o atraviese la apertura de la primera. Esto introduce una exigencia envolvente de cuerpos antes de evaluar la ruptura. La continuación utiliza estos niveles y después aplica cuerpo H1, mecha, ADX, frescura y retest M15.

**Propuesta:** comparar `Envolvente actual` con `Giro de cuerpos`, conservando los filtros posteriores. El segundo modo permitiría investigar niveles excluidos por la envolvente. No eliminar la confirmación estructural para compensar el aumento del mapa.

Un inventario de los H1 disponibles de los 23 activos, dentro de 2024-10-11 a 2026-10-11, encontró **166.357 cambios de color** y **82.586 que cumplen la envolvente**. Quedan 83.771 uniones adicionales para investigar. Esto cuenta pares de velas, no niveles Fresh, setups, señales ejecutables ni operaciones. No predice duplicar trades. La cobertura tampoco es completa en todos los símbolos: Volatility 90 tiene 5.749 barras y Step 400, 16.862.

**Control propuesto:** `Definición de niveles A/V para entradas`, inicialmente `Envolvente actual`; el modo alternativo empezaría en observación. Separar esta elección del mapa de obstáculos: agregar niveles a ese mapa también podría bloquear entradas o acortar objetivos. Medir su efecto en otro experimento.

## 2. Ciclo explícito de cambio de función SBR/RBS — segunda prioridad

[LuxAlgo](https://www.luxalgo.com/library/indicator/malaysian-snr/) describe que un cierre de cuerpo a través del nivel cambia su función y renueva su frescura. El autor de [DoN Decision Levels](https://www.tradingview.com/script/iWgxW7bW/) también conserva los niveles rotos como soporte convertido en resistencia o resistencia convertida en soporte. Son reglas de esos indicadores, sin resultados transferibles al proyecto.

Nuestro `level_freshness()` clasifica como consumido un nivel con ruptura previa del cuerpo, más de una visita o penetración excesiva. `active_av_levels()` deja de incluir el nivel en su función original tras una ruptura. La continuación ya permite operar el primer breakout elegible y su retest: ese caso **ya existe** y no debe contabilizarse otra vez.

**Propuesta adicional:** representar cada cambio de función como un episodio nuevo, únicamente después de una ruptura estructural cerrada y verificable. Congelar dirección, hora, nivel e invalidación; exigir el primer retest del nuevo episodio y limitar cambios repetidos. No marcar cualquier nivel consumido como Fresh ni borrar su historia. Si coincide con una continuación existente, deduplicar por evento estructural.

**Controles propuestos:** `Modo SBR/RBS` y `Máximo de cambios de función por nivel`. Empezar en observación, con un cambio como hipótesis inicial, conservando el límite de entrada y el espacio mínimo de 2R.

## 3. Quasimodo con swings intermedios — investigación secundaria

El autor de [Wonra Alchemist SNR Engine](https://tr.tradingview.com/script/ANCSINu0-Wonra-Alchemist-SNR-Engine/) explica que busca combinaciones de swings para reconocer un Quasimodo aunque haya un swing menor intermedio. Es una descripción del detector, no una demostración de rentabilidad.

Nuestro detector utiliza tríos consecutivos de swings alternados después de comprimir extremos del mismo tipo. Puede omitir una relación hombro–cabeza–neckline cuando aparece una oscilación intermedia.

**Propuesta:** comparar combinaciones dentro de una ventana acotada, con profundidad mínima de cabeza normalizada por ATR. Todos los pivotes deben estar confirmados antes de la ruptura; conservar la primera ruptura de neckline, el retest del hombro y la invalidación de cabeza. No anticipar pivotes usando barras futuras.

**Controles propuestos:** `Modo Quasimodo ampliado`, `Ventana máxima de swings` y `Profundidad mínima de cabeza`. Observación primero. El QM sintético del replay anterior tuvo solo siete operaciones: esa muestra no permite valorar esta variante.

## 4. Storyline estructural para instrumentos tradicionales

La publicación [Malaysian SnR + Storyline](https://www.tradingview.com/script/zHJLrkfS-Malaysian-SnR-Storyline/) describe sesgos de pivotes confirmados en varios marcos y confluencias opcionales. En nuestro proyecto, el veto diario utiliza el color de la última vela D1 cerrada, como confirma el campo `LAST_CLOSED_D1_CANDLE_DIRECTION`.

**Hipótesis:** una vela diaria bajista puede representar un retroceso dentro de una estructura alcista. Comparar el método actual con un sesgo definido por swings y rupturas D1/H4 podría recuperar algunas entradas hoy rechazadas; también podría descartar otras. No hay evidencia todavía de aumento neto de cantidad o calidad.

**Control propuesto:** `Método de dirección macro`, con referencia actual `Última vela D1`. Mantener el interruptor de veto sintético independiente. Medir primero cuántos setups tradicionales completos quedan rechazados por conflicto D1 durante sesiones operables; no inferirlo de lecturas del domingo fuera de sesión.

## 5. Open–Close / Decision Levels — prioridad condicionada a los datos

Los autores de [Fixed Range](https://www.tradingview.com/script/KKLcgG6L-Malaysian-SNR-Levels-Fixed-Range/) y [DoN](https://www.tradingview.com/script/iWgxW7bW/) contemplan niveles Open–Close, este último en H4. Nuestro detector causal activo no tiene esta familia; tampoco equivale a un FVG de tres velas.

El inventario H1 encontró **19.919 separaciones direccionales entre cierre y siguiente apertura de al menos 0,01 ATR**, pero solo **817 de al menos 0,05 ATR**. Estos umbrales son categorías del inventario, no parámetros recomendados. Step, Step 200 y Step 400 no tienen casos de 0,05 ATR en los datos consultados; Jump 25 tiene dos. Muchas separaciones pequeñas podrían reflejar la granularidad del siguiente tick.

**Propuesta:** evaluar primero si existe una separación material respecto a ATR, tamaño de tick y spread. Solo después desarrollar un escenario de retorno y rechazo, inicialmente en observación. Para estudiar Decision Levels H4 se requiere preparar H4 causal; el conteo presentado es H1 y no demuestra la disponibilidad de setups H4.

## Confirmación M5: experimento posterior

Una confirmación M5 cerrada podría detectar recuperaciones que M15 representa demasiado tarde o demasiado lejos. Es una hipótesis propia, no un aumento de WinRate acreditado por las fuentes.

No basta con cambiar una etiqueta: se deben adaptar el suministro de barras, la continuidad, las tres barras de recuperación expresadas en minutos, las etiquetas de evidencia y la revalidación de ejecución que hoy usa cierres de 15 minutos. El replay de referencia dispone de M15/H1/D1 y no puede reconstruir fielmente la secuencia M5. Hacen falta barras M5 nativas o ticks adecuados. La [documentación de MT5](https://www.mql5.com/en/docs/python_metatrader5/mt5copyticksrange_py) permite consultar ticks Bid/Ask en UTC, sujetos al historial realmente disponible.

## Cómo decidir qué incorporar

1. Congelar la preferencia 7 y los objetivos reales del worker como referencia reproducible.
2. Probar una variante por vez: definición A/V y luego cambio de función. Registrar todas las variantes intentadas.
3. Mantener costes, precio ejecutable, stop, objetivos, horario, política Boom/Crash y restricciones de cartera iguales entre comparaciones.
4. Contar un setup con sus dos piernas como una operación. Separar señales nuevas, duplicadas y sustituidas por ocupación de posiciones.
5. Medir trades ejecutables, WinRate de R neto positivo, expectativa neta, factor de beneficio y drawdown. Separar también el resultado de las operaciones adicionales: un agregado favorable puede ocultar que las nuevas pierden dinero.
6. Revisar ventanas temporales y activos por separado, con intervalos de incertidumbre. Los dos años ya examinados sirven para investigación, pero no son una muestra final intacta. Congelar la variante antes de evaluar nuevos datos demo; controlar la selección entre múltiples pruebas, como plantea [Bailey y colaboradores](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf).
7. Incorporar a Operar únicamente una variante con evidencia suficiente de más operaciones y calidad sostenida. Si los intervalos no permiten sostener una mejora de WinRate, declarar el resultado inconcluso.

Deriv explica que los sintéticos carecen de libro de órdenes y advierte que, salvo Range Break, los patrones históricos observables pueden ser coincidencias; [FAQ del proveedor](https://deriv.com/markets/derived-indices/synthetic-indices). Por eso, etiquetas como “Fresh” o “liquidez” no sustituyen la validación empírica específica por instrumento.

## Evidencia reproducible

- `storage/analysis/msnr_web_review_20261011/settings_snapshot.json`: configuración consultada, sin escritura de preferencias.
- `storage/analysis/msnr_web_review_20261011/structure_inventory.json`: conteos por instrumento y advertencia de alcance.
- `scratch/msnr_web_structure_inventory.py`: inventario offline de los históricos locales; no conecta al broker.
- Código contrastado: `strategy/malaysian_snr/validation.py`, `malaysian_snr_strategy.py`, `config.py`, `runtime_settings.py` y revalidación de señales del motor de ejecución.

No se ejecutó un replay de rendimiento nuevo. Este trabajo identifica hipótesis y su diseño de evaluación; no estima un nuevo WinRate ni una ganancia porcentual de trades.
