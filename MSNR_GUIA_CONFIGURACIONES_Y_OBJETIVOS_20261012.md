# Malaysian SNR: configuraciones para ampliar entradas y evaluar su efectividad

Configuración guardada el 2026-10-12T22:48:15.248392, versión 13. Esta guía documenta los valores aplicados, no una promesa de WinRate. Está disponible también dentro de `/strategy-bases`, pestaña Malaysian SNR, en **Guía de cada acción**.

## Qué quedó aplicado

La versión 12 ya tenía los cuatro Step con activo, Continuación y M5 en Operar. El perfil conserva M5 en Operar para **Step Index, Step Index 200, Step Index 400, Step Index 500**. El modo general M5 permanece en Observación. Se expuso el filtro adicional de ejecución de Step, con referencia general 25 y excepción **23 solo para Step Index**. Los otros Step siguen en 25. Esto no altera los motores STEP o SYNTHETICS. Es una hipótesis DEMO elegida después de observar estos datos; no existe validación independiente de ventaja. Continuación, A/V ampliado, cambio de función, QM ampliado y Open–Close mantienen sus modos Operar previos. Se conservaron Fractal 45%, distancias de 0,50 ATR H1, mecha de 25%, ADX de formación 20, recuperación de 35% y ventanas de 90/45 minutos.

Se añadieron a Observación Volatility 15 Index, Volatility 75 (1s) Index, CADCHF, USDCAD y CHFJPY. Son candidatos con algún resultado positivo en la prueba anterior de siete días, con muestras de solo una o dos operaciones; eso no justifica habilitar sus órdenes. Sus controles M5 quedaron explícitamente en Observación. Los otros siete recuperados que seguían en Observación se conservaron; Step 500 ya había sido pasado a Operar. El catálogo permite cambiar el modo de cualquiera de los 60 instrumentos sin modificar código.

Se ajustaron los criterios de investigación para exigir conjuntamente **105% de las entradas de la base, mejora de WinRate de al menos un punto porcentual, 50 resultados resueltos por variante, expectativa positiva y beneficio total superior**. La frecuencia admite objetivos superiores al 100%. Un punto porcentual significa, por ejemplo, pasar del 40% al 41%, no una mejora relativa del 1%. Estos criterios no filtran las órdenes actuales ni activan variantes automáticamente.

No se flexibilizaron cuerpo, mecha, retest o distancia. La relajación elegida afecta exclusivamente el ADX adicional de Step Index. La primera comparación sin filtros compartidos sugería apagar M5 en Step 400, pero al aplicar el filtro del motor esa conclusión cambió: algunos candidatos M15 favorables también estaban bloqueados. Por eso se conservaron los modos M5 existentes. Ninguno de los cuatro perfiles de expansión Crash cumplió todos los objetivos; M5 de Crash permanece en observación. Todos los perfiles comparados figuran en `configuration_candidates.json`, incluidos los desfavorables. La selección del umbral 23 es retrospectiva y debe probarse en fechas nuevas.

## Resultado de la comprobación de 30 días

Período: **11 de septiembre de 2026, 00:00 UTC, a 11 de octubre de 2026, 00:00 UTC**. Cuatro Step y dos Crash. Es una muestra parcial de seis instrumentos; no representa todos los activos ni la cartera del bot. Los resultados corresponden a la configuración operativa de la versión 12; los criterios nuevos no cambian la formación de sus entradas. Cada variante reutiliza el mismo feed, período y configuración base. M5 y la alternativa H4 son hipótesis del replay, no órdenes enviadas. BASE_GUARDADA_V12 usa M5 en los cuatro Step y M15 en los dos Crash. La fila de modos aplicados conserva esa selección y por eso da el mismo resultado en la capa SNR: esta tabla omite el filtro adicional de ejecución Step. El efecto del ajuste ADX 23 se comprueba en el diagnóstico siguiente.

| Variante | Entradas simuladas | Resueltas | Incompletas | WinRate resuelto | Resultado en R |
|---|---:|---:|---:|---:|---:|
| BASE_GUARDADA_V12 | 47 | 45 | 2 | 35.556% | 2.79747R |
| M15 | 18 | 17 | 1 | 23.529% | -3.70551R |
| M15_M5 | 59 | 57 | 2 | 35.088% | 2.13153R |
| M15_H4 | 18 | 17 | 1 | 23.529% | -3.70551R |
| MODOS_APLICADOS_SIN_FILTRO_STEP | 47 | 45 | 2 | 35.556% | 2.79747R |

| Activo | Variante | Entradas | Resueltas | WinRate | Resultado R |
|---|---|---:|---:|---:|---:|
| Step Index | M15 | 2 | 2 | 0.0% | -2.00000R |
| Step Index | M15_M5 | 10 | 10 | 50.0% | 4.05923R |
| Step Index 200 | M15 | 1 | 1 | 0.0% | -1.00000R |
| Step Index 200 | M15_M5 | 12 | 11 | 36.364% | 0.77933R |
| Step Index 400 | M15 | 5 | 5 | 40.0% | 0.59867R |
| Step Index 400 | M15_M5 | 11 | 11 | 36.364% | 0.03452R |
| Step Index 500 | M15 | 5 | 4 | 50.0% | 3.69583R |
| Step Index 500 | M15_M5 | 9 | 8 | 37.5% | 2.92440R |
| Crash 600 Index | M15 | 2 | 2 | 0.0% | -2.00000R |
| Crash 600 Index | M15_M5 | 8 | 8 | 25.0% | -3.99549R |
| Crash 1000 Index | M15 | 3 | 3 | 0.0% | -3.00000R |
| Crash 1000 Index | M15_M5 | 9 | 9 | 22.222% | -1.67045R |

Evaluación con los objetivos actuales:

- Step Index: no cumple; motivos: INSUFFICIENT_RESOLVED_SAMPLE. Sin promoción automática.
- Step Index 200: no cumple; motivos: INSUFFICIENT_RESOLVED_SAMPLE, INCOMPLETE_OR_AMBIGUOUS_OUTCOMES. Sin promoción automática.
- Step Index 400: no cumple; motivos: INSUFFICIENT_RESOLVED_SAMPLE, WIN_RATE_IMPROVEMENT_BELOW_TARGET, NO_NET_REWARD_IMPROVEMENT. Sin promoción automática.
- Step Index 500: no cumple; motivos: INSUFFICIENT_RESOLVED_SAMPLE, INCOMPLETE_OR_AMBIGUOUS_OUTCOMES, WIN_RATE_IMPROVEMENT_BELOW_TARGET, NO_NET_REWARD_IMPROVEMENT. Sin promoción automática.
- Crash 600 Index: no cumple; motivos: INSUFFICIENT_RESOLVED_SAMPLE, NON_POSITIVE_EXPECTANCY, NO_NET_REWARD_IMPROVEMENT. Sin promoción automática.
- Crash 1000 Index: no cumple; motivos: INSUFFICIENT_RESOLVED_SAMPLE, NON_POSITIVE_EXPECTANCY. Sin promoción automática.
- combined: no cumple; motivos: INSUFFICIENT_RESOLVED_SAMPLE, INCOMPLETE_OR_AMBIGUOUS_OUTCOMES. Sin promoción automática.

Comparación de los modos de la capa SNR, todavía sin el filtro de ejecución Step: no cumple; motivos: FREQUENCY_LOSS_EXCEEDS_LIMIT, INSUFFICIENT_RESOLVED_SAMPLE, INCOMPLETE_OR_AMBIGUOUS_OUTCOMES, WIN_RATE_IMPROVEMENT_BELOW_TARGET, NO_NET_REWARD_IMPROVEMENT. Sensibilidad a coste adicional de 0,10R por resultado resuelto: -1.70253R. Esta comparación no mide el efecto del nuevo umbral ADX y el coste hipotético no sustituye costes de ejecución verificados.

Un resultado favorable en este período sigue siendo investigación: las fechas se eligieron después de observar una semana contenida en ellas. No es un período independiente ni una validación de dos años. Las métricas se calculan sobre resultados resueltos; los incompletos y la ambigüedad impiden aprobar los criterios. El replay aproxima spread con datos históricos, no verifica todas las comisiones, slippage, swap, redondeos o límites simultáneos de cartera. También omite los filtros compartidos del ejecutor de Step y Boom/Crash: mide candidatos de la capa SNR, no reproduce todas las decisiones del motor en vivo. No se usa para entrenar modelos. Un WinRate alto con pérdida neta no satisface el objetivo.

## Diagnóstico del filtro de ejecución antes y después

Se reconstruyeron los candidatos ya capturados y se comprobaron los filtros reales de Step y Boom/Crash. Para Step Index, bajar el mínimo adicional de 25 a 23 hace pasar cinco candidatos M5 frente a cuatro, conservando los demás requisitos. El candidato añadido tenía ADX 23,57 y un resultado simulado de +1,01451R. Es una sola observación elegida retrospectivamente: no demuestra que el umbral 23 sea superior en el futuro.

La tabla siguiente es un **subconjunto diagnóstico**, no un replay completo del motor. Rechazar una posición cambiaría las ventanas en las que se admiten otras señales; filtrar filas no reproduce ese efecto. Se mantienen las variantes operativas previas: M5 para los cuatro Step y M15 para los dos Crash.

| Filtro | Candidatos capturados que pasan | Resueltos | WinRate del subconjunto | Resultado del subconjunto |
|---|---:|---:|---:|---:|
| Antes: ADX 25 | 21 | 20 | 35.0% | 0.70204R |
| Después: Step Index ADX 23 | 22 | 21 | 38.095% | 1.71655R |

La cantidad de este subconjunto aumenta de 21 a 22, un 4,76%; todavía no alcanza el objetivo de 5%, ni el mínimo de 50 resultados por variante. No se debe presentar como cumplimiento de todos los objetivos. La ganancia aparente de WinRate tampoco tiene validación independiente ni todos los costes verificados. El perfil queda como ensayo DEMO y requiere seguimiento en fechas nuevas.

## Qué permite cada acción

La columna Guardado corresponde a la configuración aplicada. El efecto de cualquier ajuste sobre WinRate debe medirse; un filtro más estricto no garantiza mayor acierto.

| Acción | Guardado | Qué permite | Qué cambia al ajustarlo |
|---|---|---|---|
| ADX de ejecución Step para SNR | 25.0 | Define el mínimo del filtro adicional del motor, solo para Step del perfil Malaysian SNR. | Es distinto del ADX de formación de Continuación. Bajarlo admite señales antes bloqueadas; 25 es la referencia. No altera otros motores. El ADX puede venir de H1 en la señal SNR. |
| ADX de ejecución por Step | Step Index: 23.0 | Sobrescribe el mínimo Step para un instrumento; vacío hereda el mínimo general. | Permite ensayar 23 en Step estándar conservando 25 en los demás. Cada excepción cambia la población de señales y requiere nueva validación. |
| Dirección D1 en sintéticos | Desactivado | Activa el veto direccional D1 para sintéticos. No elimina obstáculos D1 ni la dirección permitida de Boom/Crash. | Desactivarlo admite operaciones contrarias a ese sesgo; activarlo reduce el universo de entradas. Medir el resultado por familia. |
| Cuerpo Fractal H1 | 45% | Exige una proporción mínima de cuerpo en la vela H1 del Fractal. | Bajarlo admite velas menos decisivas. Subirlo filtra más patrones; no implica mayor WinRate automáticamente. |
| Distancia Fractal | 0.5 | Limita cuánto puede separarse la entrada del nivel, en ATR H1. | Ampliarla admite entradas más alejadas y cambia el riesgo y el espacio hasta objetivos; se verifica también al enviar la orden. |
| Ventana de retest | 90 | Mantiene vivo el setup durante esta cantidad de minutos después de su ruptura. | Ampliarla permite retornos más tardíos, pero no revive niveles invalidados, consumidos o ya retesteados. |
| Selección adicional histórica | Sin activos | Añade los Jump y Volatility 1s elegidos al escaneo habitual. | Solo actúa si su modo adicional está habilitado. Un modo propio por activo tiene prioridad. |
| Modo adicional histórico | Operar | Desactivado excluye; Observación registra; Operar permite evaluar órdenes para esa lista. | Una lista vacía no añade activos aunque figure Operar. Operar no sustituye los filtros de entrada. |
| Modo Continuación | Operar | Habilita rupturas de niveles H1 seguidas de primer retest. | Operar permite entradas de este escenario; Observación mide sin órdenes; Desactivado retira el escenario. El modo del activo tiene prioridad. |
| Distancia Continuación / A/V | 0.5 | Separa la tolerancia de entrada de Continuación de la del Fractal y QM. | Ampliarla puede recuperar confirmaciones alejadas, a costa de peor precio o menos espacio útil hasta obstáculos. |
| Mecha máxima Continuación | 25% | Limita la mecha de rechazo direccional de la vela de ruptura H1. | Subirla admite rupturas con más rechazo; bajarla exige una ruptura más limpia y puede reducir la frecuencia. |
| Distancia Quasimodo | 0.5 | Limita la distancia de entrada al nivel del escenario QM. | Ampliarla tolera mayor alejamiento del hombro. No altera las distancias Fractal o Continuación. |
| Modo propio del activo | Step Index: Operar<br>Step Index 200: Operar<br>Step Index 400: Operar<br>Step Index 500: Operar<br>Volatility 10 Index: Observación<br>Volatility 15 Index: Observación<br>Volatility 25 Index: Observación<br>Volatility 75 Index: Observación<br>Volatility 75 (1s) Index: Observación<br>Boom 500 Index: Observación<br>Boom 600 Index: Observación<br>Crash 500 Index: Observación<br>USDCAD: Observación<br>CADCHF: Observación<br>CHFJPY: Observación<br>BTCUSD: Observación | Sobrescribe la selección habitual: Desactivado, Observación u Operar. | Observación impide todas las órdenes del activo, incluso si M5 o Continuación dicen Operar. Heredar elimina la excepción. |
| M5 por activo | Step Index: Operar<br>Step Index 200: Operar<br>Step Index 400: Operar<br>Step Index 500: Operar<br>Volatility 10 Index: Observación<br>Volatility 15 Index: Observación<br>Volatility 25 Index: Observación<br>Volatility 75 Index: Observación<br>Volatility 75 (1s) Index: Observación<br>Boom 500 Index: Observación<br>Boom 600 Index: Observación<br>Crash 500 Index: Observación<br>USDCAD: Observación<br>CADCHF: Observación<br>CHFJPY: Observación<br>BTCUSD: Observación | Sobrescribe exclusivamente el modo general M5 de cada instrumento. | Permite extender M5 a un grupo pequeño conservando el resto en observación. Comparar por episodio para evitar contar dos veces la oportunidad. |
| Continuación por activo | Step Index: Operar<br>Step Index 200: Operar<br>Step Index 400: Operar<br>Step Index 500: Operar | Sobrescribe exclusivamente el modo general Continuación. | Permite observar o desactivar Continuación en un instrumento sin apagar el Fractal ni QM. |
| Frecuencia mínima comparada | 105% | Define la proporción mínima de entradas frente a la base en el replay. | 100% evita aprobar una variante con menos entradas; más de 100% exigiría crecimiento. No es un filtro de órdenes en vivo. |
| Muestra mínima comparada | 50 | Exige resultados resueltos en ambas variantes para evaluar una comparación. | Subirla evita decidir con muestras diminutas, pero no asegura significación estadística. No limita las entradas en vivo. |
| Mejora mínima de WinRate | 1 puntos porcentuales | Exige que el WinRate candidato supere al de la base por estos puntos porcentuales. | 1 punto significa pasar, por ejemplo, de 40% a por lo menos 41%. Se evalúa junto a frecuencia y beneficio; no activa variantes automáticamente. |
| Cuerpo Continuación H1 | 50% | Exige cuerpo mínimo a las rupturas de Continuación y escenarios que comparten ese requisito. | Bajarlo amplía los quiebres aceptados; subirlo descarta cuerpos pequeños. Cambia también algunas variantes A/V, SBR/RBS y Open–Close. |
| ADX Continuación H1 | 20.0 | Exige un mínimo de ADX en la estructura H1. ADX mide intensidad, no dirección. | Bajarlo admite estructuras menos tendenciales; subirlo reduce entradas. Su utilidad debe comprobarse en cada instrumento. |
| Exigir Fresh en Continuación | Desactivado | Exige niveles sin contacto previo según la política Fresh. | Desactivarlo admite niveles no Fresh, pero mantiene el bloqueo de niveles consumidos y la exigencia de primer retest del episodio. |
| Diagnóstico de rechazo H1 | Activado | Registra por qué un Fractal u otro setup no pasó sus requisitos. | Ayuda a elegir el filtro responsable de la pérdida de frecuencia; no mejora por sí mismo las entradas. |
| Reutilizar estructura H1 | Activado | Reutiliza estructura calculada mientras no cambien velas relevantes ni ajustes. | Reduce trabajo repetido. No permite usar información futura ni reutilizar una estructura tras cambiar sus controles. |
| Priorizar retests pendientes | Activado | Analiza antes los setups vivos dentro de cada grupo de ejecución u observación. | Puede reducir oportunidades perdidas por demora del escaneo; no flexibiliza la confirmación. |
| Separar análisis y envío | Activado | Permite analizar mientras el bloqueo de envío de órdenes está ocupado. | Reduce demoras del análisis; el envío mantiene su bloqueo y validaciones. |
| Modo A/V ampliado | Operar | Añade niveles de giro A/V según la definición seleccionada. | Operar habilita este escenario y Observación registra alternativas. Mantiene cuerpo, ADX, mecha, Fresh y retest. |
| Definición A/V | Giro de cuerpos | Elige envolvente o giro de cuerpos para las variantes A/V y cambio de función. | Giro de cuerpos puede formar más niveles que envolvente; cambiarlo modifica el patrón y requiere comparación nueva. |
| Modo cambio de función | Operar | Admite un nuevo episodio cuando soporte pasa a resistencia o viceversa tras ruptura cerrada. | Recupera oportunidades de reutilización estructural sin aceptar un segundo toque del mismo episodio. |
| Cambios máximos de función | 1 | Limita cuántos cambios estructurales se admiten por nivel. | Subirlo admite más reutilizaciones y mayor riesgo de desgaste. Cada episodio sigue necesitando ruptura y primer retest. |
| Desplazamiento cambio de función | 0.2 | Exige una separación mínima de la ruptura para renovar el nivel. | Bajarlo acepta cambios menos pronunciados; subirlo filtra rupturas pequeñas. |
| Modo QM ampliado | Operar | Busca hombro, cabeza y neckline entre una ventana más amplia de swings confirmados. | Añade configuraciones QM que no son consecutivas. Conserva ruptura, invalidación de cabeza y retest del hombro. |
| Ventana de swings QM | 8 | Controla cuántos swings confirmados examina QM ampliado. | Ampliarla permite estructuras con más swings intermedios; puede añadir patrones más antiguos. |
| Profundidad de cabeza QM | 0.2 | Exige una profundidad mínima del barrido respecto al hombro. | Bajarla admite barridos pequeños; subirla puede excluir patrones poco definidos y reducir trades. |
| Modo dirección macro | Operar | Desactivado usa color D1; Observación compara; Operar usa pivotes y rupturas confirmadas. | Afecta activos cuyo filtro macro es obligatorio. Si la estructura queda neutral, espera; no reactiva D1 en sintéticos con veto desactivado. |
| Método macro | Estructura D1 | Elige estructura D1, H4 o confluencia D1/H4. | H4 responde a otro horizonte; confluencia puede filtrar más entradas. No equivale a desactivar el filtro direccional. |
| Confirmación de pivotes | 2 | Exige esta cantidad de velas a cada lado del pivote antes de usarlo. | Bajarla confirma antes con swings menores; subirla añade demora y estructura más amplia. Nunca usa pivotes aún sin confirmar. |
| Modo Open–Close | Operar | Habilita niveles de separación entre cuerpos y su retorno confirmado. | Añade un escenario; Operar permite ejecución y Observación mide. Sin tick o spread verificable no forma esa variante. |
| Marco Open–Close | H1 | Define si el nivel se forma en H1 o H4. | H4 requiere sus propias velas cerradas y usa otra escala estructural; no es una simple multiplicación de frecuencia. |
| Separación Open–Close en ATR | 0.05 | Define uno de los tres mínimos de separación de la banda. | Bajarla solo tendrá efecto si no dominan los mínimos de ticks o spread. El motor usa el mayor de los tres. |
| Separación Open–Close en ticks | 2 | Descarta bandas menores a esta cantidad de ticks del instrumento. | Bajarla admite bandas más pequeñas si también pasan ATR y spread; subirla puede eliminar microseparaciones. |
| Separación Open–Close respecto al spread | 2.0 | Exige una banda suficientemente grande respecto al coste de entrada observado. | Bajarla admite separaciones con peor relación respecto al spread. No reduce el spread real. |
| Ampliar historial útil | Activado | Solicita más velas cuando las cerradas disponibles no alcanzan el mínimo. | Recupera análisis bloqueados por falta de datos; no fabrica historial ni convierte errores en sesgo neutral. |
| Mínimo de velas H1 | 28 | Exige historial suficiente para estructura e indicadores H1. | Subirlo requiere más datos y puede demorar instrumentos nuevos; bajarlo no elimina otros mínimos del cálculo. |
| Mínimo de velas D1 | 30 | Exige suficiente contexto diario para sesgo y obstáculos. | Más velas permiten más contexto; no se deben confundir datos faltantes con permiso para operar. |
| Límite de consulta histórica | 320 | Acota cuántas velas puede solicitar la ampliación adaptativa. | Subirlo puede resolver escasez de historial a costa de latencia. No aumenta la retención disponible del proveedor. |
| Modo M5 general | Observación | Añade confirmación M5 dentro del mismo setup H1 y después de su ruptura cerrada. | Puede confirmar antes que M15. Las excepciones por activo prevalecen; se conserva una sola ejecución por episodio. |
| Ventana de recuperación | 45 | Da tiempo al precio para recuperarse después del primer contacto con el nivel. | Ampliarla admite recuperaciones tardías, dentro de la caducidad total; no autoriza contactos previos a la ruptura. |
| Cuerpo mínimo de recuperación | 35% | Exige cuerpo mínimo a la vela que confirma la recuperación M15 o M5. | Bajarlo admite rebotes débiles; subirlo reduce confirmaciones. Afecta ambos marcos, no solo M5. |
| Alternativa H4 con D1 neutral | Observación | Permite comparar o usar H4 solamente cuando el contexto D1 es neutral y el caso es elegible. | Operar puede recuperar entradas macro bloqueadas; Observación no envía esas alternativas. No sustituye errores de datos por permiso. |
| Modo IA | Filtro compatible | Desactivado omite IA; Observación registra su puntuación; Filtro aplica una IA compatible. | El filtro solo aporta una selección interpretable si el modelo tiene validación compatible con la estrategia y sus ajustes. |
| IA incompatible | Observar solo DEMO | Bloquear impide nuevas entradas; Observar permite evaluar sin el veto del modelo incompatible solo en DEMO. | En Observar DEMO, los umbrales de IA no acreditan ni aseguran la calidad. En cuenta real, esta excepción no autoriza operar. |
| Probabilidad IA general | 55% | Fija el umbral general de aceptación de una IA compatible en modo Filtro. | Subirlo reduce candidatos aceptados; bajarlo admite puntuaciones menores. Su efecto debe medirse con calibración independiente. |
| Probabilidad IA Forex y plata | 60% | Fija el umbral específico de Forex y plata de la IA compatible. | Tiene prioridad sobre el general en esas categorías; no funciona como filtro de calidad cuando se observa un modelo incompatible. |
| Probabilidad IA oro | 60% | Fija el umbral específico de oro de la IA compatible. | Subirlo filtra más señales de oro; no permite trasladar un porcentaje de probabilidad a un WinRate garantizado. |
| Probabilidad IA Volatility | 52% | Fija el umbral específico de Volatility de la IA compatible. | Permite calibrar esta familia por separado; requiere muestras y validación de esa familia. |
| Expectativa mínima IA | 0.1 | Exige expectativa neta mínima estimada por una IA compatible en modo Filtro. | Subirla exige mayor retorno esperado por riesgo, pero una estimación incompatible o mal calibrada no es evidencia de ventaja. |
| Registrar candidatos | Activado | Persiste episodios, variantes, confirmaciones y motivos de bloqueo. | Permite distinguir lecturas repetidas de oportunidades únicas y analizar qué filtro reduce entradas. |
| Seguir resultados observados | Activado | Evalúa resultados de candidatos sin enviar órdenes. | Permite estudiar alternativas, manteniendo separados resultados observados y operaciones reales. |
| Horizonte observado | 24 | Acota la duración de seguimiento de resultados sin órdenes. | Ampliarlo permite observar recorridos más largos; un candidato no resuelto no debe contarse como victoria o pérdida confirmada. |

## Botones y modos: cómo aplicar un cambio

1. **Heredar** elimina la excepción por activo y vuelve a su selección habitual o modo general. Un activo ajeno a la selección no empieza a operar por aparecer en el catálogo.
2. **Observación del activo** impide todas sus órdenes. Poner M5 en Operar no supera esa restricción. **Desactivado** lo retira del escaneo. **Operar** permite evaluar la entrada y añadir el instrumento al escaneo; todavía exige una señal válida.
3. Ajustar un campo deja un cambio pendiente. **Guardar ajustes** persiste la configuración y se aplica al siguiente análisis. La guía muestra los valores guardados, no el borrador aún sin guardar.
4. **Actualizar estado** vuelve a leer la configuración y descarta el borrador. **Volver a valores por defecto** solo carga las referencias en el formulario: hay que guardar para aplicarlas. Vacía excepciones por activo y vuelve a la selección habitual y los candidatos adicionales por defecto; no restaura este perfil personalizado.
5. Para deshacer solo el ensayo de Step Index, borrar su campo **ADX de ejecución** y guardar hace que herede 25. También se puede escribir 25 expresamente. Esto conserva los demás modos y ajustes del perfil.

## Secuencia para buscar más entradas y más efectividad

1. Tomar como base los ajustes guardados y contar episodios únicos, no lecturas repetidas ni las dos piernas como dos oportunidades independientes.
2. Revisar el primer bloqueo: falta de datos se resuelve con historial; espera de retorno no se resuelve apagando ADX; precio alejado no se resuelve ampliando la caducidad; D1 neutral de Forex requiere evaluar contexto, no ignorar errores del proveedor.
3. Cambiar una condición o un grupo pequeño de activos. Mantener una versión de referencia y medir la misma ventana y feed. Registrar cada prueba, incluidas las desfavorables.
4. Exigir los objetivos de frecuencia, WinRate y beneficio a la vez. WinRate aquí significa resultado total positivo en R; los breakeven con beneficio parcial positivo cuentan como ganancia, no equivale necesariamente a tocar TP2.
5. Validar en otro período y con costes de ejecución. El mínimo de 50 no constituye por sí solo una prueba estadística de ventaja. Considerar también incertidumbre, drawdown y resultados por activo y escenario.
6. Pasar una variante a Operar por activo únicamente después de revisar sus resultados. No se activan todos los instrumentos por una sola semana favorable. El registro observado y el WinRate de operaciones ejecutadas siguen separados.

## Condiciones que no deben confundirse con estos controles

La señal usa velas cerradas, ruptura H1 ya completada y primer retorno posterior; no usa información futura. Se conservan invalidación, obstáculos y espacio mínimo 2R, dirección permitida de Boom/Crash, stop con riesgo positivo, precio real de entrada y deduplicación del episodio. Forex, metales, índices y BTCUSD conservan las sesiones del proyecto: Londres 07–11 UTC y Nueva York 12:30–17 UTC. Desactivar D1 en sintéticos no elimina esas sesiones de otros instrumentos.

Además, el ejecutor conserva controles adicionales. Step ahora permite configurar su mínimo de ejecución **solo para SNR desde esta pestaña**, con el ADX capturado de la señal o el dato disponible del análisis/proveedor. La excepción de Step Index es 23; los otros Step heredan 25. Una señal SNR puede traer ADX H1, aunque el antiguo motivo mencionaba M15. Los otros motores conservan su umbral previo. El diagnóstico nuevo registra el mínimo aplicado y la versión de ajustes; datos ADX ausentes o no finitos no autorizan una entrada SNR. Boom/Crash siguen comprobando extremos H1 de las últimas 24 horas. También existen comprobaciones de exposición y posiciones de otros motores. Bajar ADX de formación de Continuación no elimina el mínimo de ejecución.

La IA actual no tiene validación compatible. Con Filtro + Observar modelo incompatible, únicamente en DEMO, sus umbrales no están demostrando una mejora de calidad. En cuenta real esa excepción no permite saltar el bloqueo. El siguiente paso de IA exige capturas causales y resultados reales completos, calibración independiente y una versión compatible; bajar probabilidades de un modelo incompatible no resuelve la ausencia de validación.

## Fuentes y evidencia

La documentación de [Deriv sobre Step](https://traders-academy.deriv.com/trading-guides/step-indices-evolution-step-multi-step-skew-step) describe su mecánica; no valida este bot ni sus parámetros. La investigación [The Probability of Backtest Overfitting](https://www.davidhbailey.com/dhbpapers/backtest-prob.pdf) fundamenta la cautela al seleccionar configuraciones por resultados del mismo historial. Ninguna de esas fuentes demuestra que nuestros valores 105% / 1 punto / 50 sean óptimos: son objetivos explícitos de evaluación.

- Ajustes antes/después y cambio exacto: `storage/analysis/msnr_configuracion_guiada_20261012/`.
- Replays de 30 días: `storage/analysis/msnr_v27_m5_reference_20261012/steps_v28_30d_current/` y `crash_v28_30d_current/`. Las fuentes anteriores de los Step también se conservaron en `source_snapshot/`.
- Evaluación con los objetivos nuevos: `storage/analysis/msnr_configuracion_guiada_20261012/steps_30d_reassessment.json`.
- Guía en la interfaz: sección **Guía de cada acción** en Malaysian SNR.

## Verificación del despliegue

El motor confirmó preferencias 13, estado RUNNING y 36 activos en el ciclo. Se conservaron los demás procesos y el modelo de IA. El ADX propio se registra en la señal con el umbral aplicado y la versión de ajustes. Se verificaron los controles por Step, la validación del formulario y la guía de los 59 ajustes.

El primer intento de recarga se aplazó al detectar una posición SNR abierta. Antes de la recarga definitiva se verificaron stop y objetivo activos en el bróker, ausencia de órdenes pendientes y su registro persistente. El motor recupera esa posición desde el bróker y el diario. Después se comprobó que conservó el mismo ticket, stop y objetivo, y que el monitor emitió eventos nuevos. La recarga no envió órdenes ni modificó esa posición.

Validación: 278 pruebas dirigidas de persistencia, API, IA, causalidad, controles, replay y aislamiento entre motores aprobadas en los conjuntos ejecutados. El conjunto final de 78 incluyó los controles nuevos de ejecución Step. JavaScript validado y formulario comprobado en el navegador. Evidencia en `deployment_verification.json`, `step_reload_before.json` y `step_reload_after.json`.
