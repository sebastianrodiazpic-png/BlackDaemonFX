# Malaysian SNR: investigación de logs, base de datos y fuentes web

Fecha local: **12 de octubre de 2026**. Corte de ciclos: **13:17 Santiago / 16:17 UTC**. Las consultas de historial ampliado se completaron alrededor de las 13:23 Santiago. Investigación en lectura: no se modificaron los parámetros activos, los modelos ni las tablas operativas.

## Resultado principal

La prioridad actual es reparar la disponibilidad del historial y comprobar la compatibilidad de la IA. Hay evidencia de una señal completa detenida por el filtro de probabilidad, de un instrumento excluido por historial insuficiente y de errores del proveedor. Agregar más escenarios o bajar indiscriminadamente cuerpo, distancia y frescura no corrige esos problemas.

No puede garantizarse aumentar simultáneamente cantidad y WinRate. Se pueden formular y comparar variantes que recuperen oportunidades completas, medir su calidad y aceptar solo las que mejoren la evidencia fuera de muestra. La versión actual no tiene entradas nuevas en el período de ciclos revisado; su WinRate realizado no se puede estimar con cero operaciones.

## Evidencia actual del proyecto

La preferencia 9 sigue activa: Fractal 45%, distancia Fractal 0,50 ATR, veto D1 sintético desactivado, continuación y cinco variantes en Operar. La lista de activos adicionales está vacía.

Desde 00:52:49 hasta 16:16:20 UTC se registraron **1.498 ciclos completos**, **34.454 evaluaciones** y **cero órdenes nuevas**.

| Estado relevante | Lecturas de ciclo |
|---|---:|
| Sin setup completo | 13.612 |
| Fuera de sesión | 9.955 |
| Setup vencido | 3.233 |
| Nivel consumido | 1.563 |
| Sesgo estructural neutral o no disponible | 1.183 |
| Velas cerradas insuficientes | 592 |
| Distancia excesiva | 309 |
| Recuperación débil | 267 |
| Recuperación vencida | 258 |
| Obstáculo antes de TP1 | 52 |
| Rechazo por probabilidad de IA | 29 |
| Error de proveedor por `complete` | 17 |

Son lecturas repetidas, no oportunidades únicas. El resumen del daemon muestra cero errores en su contador de excepciones, pero **sí hubo 17 resultados con error de proveedor**: los errores que el analizador devuelve como estados de espera no incrementan necesariamente aquel contador.

La mediana de ciclo fue 27,985 s; p95 55,55 s y máximo 93,16 s. 622 ciclos superaron el objetivo de 30 s. Esta demora puede ser relevante cerca de cierres y vencimientos, pero el conteo no demuestra por sí mismo cuántas operaciones se perdieron por latencia.

Los logs cubren todo el período de la preferencia 9. La primera extracción de diagnósticos de la base cubre solo las últimas seis horas; una consulta adicional de decisiones de IA y resultados cubrió desde la activación. Se mantienen separados esos alcances.

## 1. Reparar el historial y el contrato de datos — prioridad inmediata

**Prueba reproducida:** Wall Street 30 recibe **23 velas H1 cerradas** al solicitar 80. SNR exige al menos 28. En sesiones operables, ese instrumento quedó en `INSUFFICIENT_CLOSED_CANDLES` durante 592 lecturas. Solicitar 160 produjo **69 velas cerradas**, superando el mínimo sin aflojar ningún filtro de entrada. MT5 entregó 79 velas cerradas para una petición de 80.

AUDNZD y USDJPY recibieron 29 velas H1 cerradas en vez de las 79 del historial MT5. Al pedir 160 se obtuvieron 109. D1 entregó 28 velas al solicitar 40, frente a 39 en MT5. No debe equipararse la cantidad solicitada con la cantidad de barras útiles recibidas, especialmente alrededor de cierres de mercado y fines de semana.

Se observaron también primeras aperturas parciales sin alineación H1/D1, por ejemplo H1 a 08:23 y D1 a 16:23. Es necesario distinguir esas barras de las barras completas del marco; no redondearlas ni convertirlas artificialmente en completas.

**Fallo localizado:** `DerivOnlyMarketDataRouter.get_candles()` intenta acceder a la columna `complete` después de recurrir al proveedor MT5. El DataFrame MT5 habitual no incluye esa columna. El fallback necesita el mismo contrato canónico, con estado de cierre calculado por apertura, duración del marco y hora UTC. La [documentación de MT5](https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesrange_py) describe las columnas y el uso de UTC; `complete` es una extensión propia del proyecto.

**Mejora propuesta:** carga progresiva hasta conseguir suficientes velas cerradas, completas y alineadas; mantener origen y trazabilidad; normalizar el fallback sin anticipar velas. Registrar barras solicitadas, recibidas, útiles, parciales y la edad de la última barra.

Controles propuestos: `Historial mínimo útil H1/D1`, `Carga progresiva`, `Límite de historial` y `Fallback normalizado`. Los límites de seguridad de la señal se conservan. El beneficio demostrado es recuperar datos para analizar; todavía no se demostró un aumento de trades rentables.

## 2. Revalidar la IA de SNR — prioridad inmediata

Se registraron **29 evaluaciones rechazadas de una sola oportunidad**, Boom 300, setup `24cdf639e1884e05f6412636`, continuación BUY confirmada a las **04:30 UTC**. No fueron 29 trades diferentes.

La señal completó el retest: cuerpo M15 68,21%, distancia 0,1164 ATR y las comprobaciones estructurales previas. El filtro de IA aplicó probabilidad mínima 55%. La primera puntuación fue **11,50%**; las posteriores llegaron a **2,66%**. Esa salida del clasificador no demuestra que su probabilidad esté calibrada para la versión v2.6.

**Diferencias verificadas entre entrenamiento y ejecución:**

- El script específico de entrenamiento asigna fuerza de patrón y confluencia a partir del nombre del escenario. En la captura real esas variables son cero porque se obtienen de otra representación.
- El RR planeado del entrenamiento específico se fija en 2,0; en la señal real observada es 2,3951.
- Los spreads del entrenamiento específico se asignan por familia; la captura real utiliza el spread ejecutable MT5.
- El modelo activo registra media de edad de señal igual a cero y escala uno, pero tiene peso negativo para esa variable. La ejecución registra segundos reales transcurridos. La distribución y semántica temporal requieren verificación.
- No hay sello de compatibilidad con la estrategia v2.6 en el artefacto leído; coincidir en los 44 nombres de variables no acredita que signifiquen lo mismo.

Una prueba de sensibilidad, variando solo la edad de la primera captura, produjo 18,73% con 0 s, 11,50% con 19,27 s y 2,94% con 60 s. No es un método para corregir la señal ni una probabilidad válida de éxito: demuestra dependencia fuerte de una variable que necesita validación.

**Problema adicional de evidencia:** `tools/update_msnr_ai_model.py` escribe como constantes cifras de muestras, accuracy y WinRates filtrados en los JSON de métricas. El script específico de entrenamiento calibra con el conjunto que luego usa para presentar resultados de prueba. Estas métricas no deben utilizarse como prueba independiente de rentabilidad. Esto no permite inferir que cada peso sea inválido, pero exige reconstruir la procedencia y validar de nuevo.

La [documentación oficial de calibración](https://scikit-learn.org/stable/modules/calibration.html) exige separar datos al calibrar modelos ya ajustados y permite evaluar fiabilidad de probabilidades. Nuestra propuesta es separar entrenamiento, calibración y prueba final por tiempo, respetando también las fechas de cierre de las etiquetas; utilizar Brier, log-loss y curvas de fiabilidad, además de resultados netos de la estrategia.

**Mejora propuesta:** una única extracción canónica de variables para replay y ejecución, modelo compatible por versión y objetivos, procedencia verificable y control propio de IA SNR en `/strategy-bases`. Comparar primero la IA en observación con el filtro actual, mediante candidatos simulados y demo controlada. No bajar 55% ni desactivar el veto global como sustituto de la validación.

Controles propuestos: `Modo IA SNR`, `Política ante modelo incompatible`, `Umbral por familia` y `Expectativa mínima`. La puntuación heurística 88,31 de la señal tampoco equivale a probabilidad de ganar.

## 3. Confirmación M5 condicionada a un setup H1 válido — siguiente experimento

El autor de [AR Malaysian SNR](https://www.tradingview.com/script/HbX9ZFBb-AR-Malaysian-SNR/) describe H4/H1 para confirmación estructural y M15/M5 para refinar entradas. Es una propuesta metodológica de ese autor; no un WinRate transferible a nuestro bot.

Los logs acumulan 309 rechazos por distancia, 267 por recuperación débil y 258 por recuperación vencida. Deben deduplicarse por setup y reconstruirse sus primeras visitas antes de estimar oportunidades recuperables. El caso anterior de Boom 1000 ya demostró que aumentar distancia podía revelar un segundo bloqueo por obstáculo.

**Hipótesis:** esperar el cierre M5 dentro de un setup H1 ya congelado puede captar una recuperación cercana antes de que M15 cierre lejos. Mantener ATR H1, barrido o rechazo confirmado, penetración limitada, invalidación estructural, precio Bid/Ask y espacio de objetivos. Una visita tiene una identidad compartida entre M5/M15 para evitar dos entradas por el mismo evento.

Controles propuestos: `Marco de confirmación M15/M5`, `Recuperación máxima en minutos`, `Cuerpo mínimo de recuperación` y `Distancia por escenario`. Cambiar tres barras M15 por tres M5 alteraría de 45 a 15 minutos la ventana: debe parametrizarse en tiempo físico.

Se necesitan datos M5 nativos y un replay nuevo; M15 OHLC no reconstruye el orden intrabar. Empezar en observación. No se propone operar una vela abierta ni reducir automáticamente el stop.

## 4. Contexto H4 cuando D1 sea neutral — experimento separado

AUDNZD tuvo 591 y USDJPY 592 lecturas de sesgo estructural neutral durante sesiones. En la prueba de datos, ambos tenían H4 alcista confirmado. AUDNZD siguió neutral en D1 tanto en Deriv como en MT5. USDJPY era neutral en D1 Deriv, mientras D1 MT5 resultaba alcista; ampliar el pedido D1 de 40 a 80 no eliminó esa diferencia.

Por eso deben repararse y contrastarse los datos primero. Después puede compararse una política `Esperar` con `H4 confirmado si D1 neutral`, conservando obstáculos D1 y ruptura H1. No se debe tratar un error de datos como neutralidad ni permitir H4 contra un D1 claramente contrario sin otra investigación.

La [publicación de Storyline](https://www.tradingview.com/script/zHJLrkfS-Malaysian-SnR-Storyline/) distingue contexto macro, intradía y ejecución. La regla concreta de fallback que proponemos es una hipótesis propia, pendiente de evidencia.

## 5. Base de datos de candidatos y resultados — requisito para comparar calidad

El journal de operaciones ejecutadas no puede explicar el resultado de candidatos que nunca llegaron a orden. Propongo registrar tres entidades separadas:

1. **Candidato único:** símbolo, versión, hash de parámetros, episodio, escenario, dirección y cierre de confirmación; claves que eviten contar ciclos o piernas como oportunidades distintas.
2. **Transición y rechazo:** primer bloqueo, bloqueo actual y condiciones independientes de estructura, macro, retest, obstáculos, IA, cartera y envío. Falta de datos debe ser un estado distinto de setup ausente. El contador del resumen debe incluir errores devueltos por el proveedor.
3. **Resultado observado:** MFE/MAE, SL/TP por dos piernas, costes, Bid/Ask, vencimiento, datos faltantes y ambigüedad intrabar. Marcar explícitamente simulación, observación y ejecución; nunca insertar una simulación como trade real.

Añadir un registro de modelos con hash de datos, esquema y semántica de variables, versiones de estrategia admitidas, objetivos, ventanas de entrenamiento/calibración/prueba y métricas verificadas. Los datos de estas tablas permitirían comparar candidatos aceptados y rechazados, evitando entrenar solamente sobre el subconjunto que el filtro anterior dejó operar.

Controles de panel propuestos: `Auditoría por candidato`, `Simular candidatos rechazados` y un embudo con oportunidades únicas, confirmadas, vetadas por IA y ejecutadas.

## 6. MISS y tolerancia de retest — investigación posterior

AR Malaysian SNR describe niveles Fresh que el precio aproxima y abandona sin tocar como MISS. [ChillOut](https://www.tradingview.com/script/vXv9ToAv-Malaysian-SnR-ChillOut/) describe conteo de contactos por el marco de origen. Son convenciones diferentes de indicadores, sin validación de resultados.

Nuestro código cuenta visitas contiguas H1 para frescura y utiliza una banda M15 de 0,35 ATR para retest. Conviene distinguir toque exacto, acercamiento a la banda, separación y regreso. Un MISS podría priorizar un nivel todavía intacto sin consumirlo; no debe convertirse en una entrada por proximidad ni reutilizar un retest consumido.

No propondría aún elevar la cantidad de visitas permitidas. Medir antes cuántos primeros rechazos dependen de una banda demasiado amplia y cómo afecta a calidad, especialmente cuando M5 ofrece una resolución diferente.

## Orden de trabajo y criterio de aceptación

Primero, historial suficiente/alineado y fallback; luego compatibilidad/validación de IA y auditoría por candidato. Después, M5 y H4 ante neutralidad como comparaciones independientes. Finalmente, ampliar activos o variantes solo con evidencia nueva.

Mantener cuerpo Fractal 45%, distancia 0,50 y protecciones de penetración, obstáculos, deduplicación y Boom/Crash como referencia. Los nuevos límites no se eligen para rescatar retrospectivamente un único caso.

Comparar pocos experimentos predefinidos con objetivos y costes reales del worker. Medir cantidad de setups ejecutables, WinRate de R neto positivo por dos piernas, expectativa, factor de beneficio, drawdown, costes y aceptación de cartera. Usar ventanas temporales sucesivas y datos posteriores nuevos; considerar cuántas alternativas se probaron. [Bailey y colaboradores](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf) explican por qué repetir pruebas y seleccionar la mejor cifra puede sobreajustar el resultado.

Deriv advierte que la aplicabilidad de patrones técnicos a sus sintéticos es limitada y que no existe libro de órdenes; [FAQ del proveedor](https://deriv.com/markets/derived-indices/synthetic-indices). Las etiquetas Fresh, MISS o liquidez no acreditan por sí mismas una ventaja empírica.

Para afirmar que una variante aumenta el WinRate hace falta evidencia con incertidumbre suficiente; para afirmar que aumenta cantidad manteniendo calidad, comprobar además que los trades nuevos no aportan expectativa negativa. Si la muestra es pequeña o los intervalos se solapan, el resultado debe declararse inconcluso.

## Artefactos de esta revisión

Directorio: `storage/analysis/msnr_no_entries_20261012_161718/`.

- `summary.json`: ciclos desde la preferencia 9 y resumen de diagnósticos muestreados de seis horas.
- `details.json`: logs y diagnósticos de esa extracción inicial.
- `entry_gate_audit.json`: decisiones IA y resultados desde la activación; identifica una oportunidad rechazada 29 veces.
- `feature_compatibility.json`: escalas del modelo, contribuciones y sensibilidad de edad, sin modificar el modelo.
- `macro_data_probes.json`: lecturas de H1/M15/D1/H4 y consultas ampliadas.
- Archivos de velas de las consultas: preservados para reproducir la comparación.

No se ejecutó un replay de rendimiento nuevo ni se cambió configuración, política de riesgo, modelos, proveedor activo o ejecución. Las propuestas están listas para convertirse en cambios parametrizados y experimentos revisables.
