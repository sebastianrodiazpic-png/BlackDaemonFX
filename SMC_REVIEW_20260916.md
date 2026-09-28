# Auditoría SMC — 16 septiembre 2026 (Santiago)

Corte: 22:46:58 Santiago / 17 septiembre 01:46:58 UTC.
Se filtraron ciclos por fecha local (UTC-3), excluyendo ORB, FLIP e IDX_OPEN.
10153 evaluaciones repetidas; no son señales únicas ni oportunidades perdidas.
NO_H1_CONTEXT 3605; NO_M5_CONFIRMATION 3301; NO_M15_SETUP 1479;
política direccional 649; STALE_M5_SIGNAL 634; WAITING_M5_AFTER_M15 395;
noticias Forex 70; zona premium/discount 15; ERROR 5.
Datos agregados: storage/analysis/smc_day_20260916.json.

SQLite consultado mode=ro: una entrada XAUUSDmicro BUY a 15:10:55 UTC,
12:10:55 Santiago, ya CLOSED; eventos de auditoría la identifican como ORB.
No entradas SMC en los resultados de los workers consultados.

Hallazgos de código:
- H1 exige tendencia direccional; NEUTRAL no usa fallback BOS/CHOCH.
- M15 exige setup alineado; se exige el último setup y M5 posterior.
- M5 tiene porcentaje adaptativo 80%, pero gates críticos independientes.
- clean_retest exige rechazo, respeto del OB y overshoot <=50% de su tamaño.
- BOS exige rechazo; CHOCH microestructura; desplazamiento requerido es crítico.
- El guard final exige discount BUY / premium SELL simultáneamente H1/M15/M5,
  usando máximos/mínimos móviles de 100 velas, no swings estructurales.
- H4 no es obligatorio por defecto para SMC; ORB conserva su lógica independiente.

Ejemplo Boom 1000: 11/13, calidad90, rechazo por retest limpio/rechazo ausentes.
Los grupos críticos impresos más frecuentes: retest+BOS rejection+displacement423;
retest+displacement339; displacement194; retest+BOS rejection165.
No son todas las causas de NO_M5: algunos casos no tienen candidato diagnosticado.

Recomendaciones, sujetas a replay y pruebas antes de cambiar reglas:
1. Auditar swings H1 y clasificación NEUTRAL. No convertir automáticamente
   contexto mixto en una dirección por un BOS antiguo.
2. Revisar retest respecto del ATR/spread y tamaño del OB por familia de activos;
   comparar rechazo por mecha con alternativas objetivas de recuperación al cierre.
3. Registrar timestamp M15 seleccionado, M5, vela más reciente y edad/cache;
   verificar que un nuevo setup no sustituya injustificadamente uno aún válido.
4. Aclarar política de zona: hoy tres marcos obligatorios; evaluar H1 estructural
   como ubicación y M15/M5 como confirmación. El guard final sólo bloqueó15,
   pero se ejecuta después de otros filtros: eso no mide su impacto contrafactual.
5. Comparar variantes en histórico fuera de muestra incluyendo spread, ejecución,
   drawdown y expectativa; no elegir sólo por número de entradas.

No se modificaron reglas ni se enviaron órdenes durante esta auditoría.
