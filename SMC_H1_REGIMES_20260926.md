# H1 rango y expansion

El contexto inicial usa el rango flexible de pivotes 3/1 con fallback de 24 velas cerradas. Dentro del rango: discount BUY, premium SELL y equilibrio invalido. Por encima del maximo: EXPANSION_BUY; por debajo del minimo: EXPANSION_SELL. Se conserva el origen PIVOT/FALLBACK_24H y sus pesos 25/15.

El ejemplo no confirma una tendencia H1 ni un retesteo: compara precio con extremos. La implementacion mantiene ese criterio; una expansion habilita direccion pero no ejecuta una entrada por si sola. M15/M5, sweep, CHoCH, edad y riesgo siguen exigidos.

Para un candidato seleccionado se guarda contexto, limites y tolerancia. EXPANSION_BUY permite volver hasta 0.2% por debajo del maximo roto; EXPANSION_SELL hasta 0.2% por encima del minimo. Una vuelta mas profunda invalida ese candidato, sin reclasificarlo a otra direccion. Un nuevo analisis puede seleccionar modo rango nuevamente. No se incorpora limite maximo de extension por encima/debajo del rango, puesto que el ejemplo no lo define.

El punto medio OB M15 debe corresponder al modo capturado: mitad discount/premium para rango; lado exterior del nivel roto o banda de tolerancia para expansion. La tolerancia valida ubicacion, no demuestra contacto previo con el nivel.

Se comparte la evaluacion entre el coordinador, confirmation_engine y evaluate_entry_location, incluyendo el precio de ejecucion. Solo los rangos marcados adaptive_context_enabled adoptan expansion; consumidores legacy mantienen el comportamiento anterior. Contexto y limites se publican para auditoria. No se reinician bots ni se envian ordenes durante esta implementacion.
