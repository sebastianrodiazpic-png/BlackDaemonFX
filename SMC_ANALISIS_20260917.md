# Análisis SMC posterior a instrumentación

Corte: 17 septiembre 2026 11:40:37 Santiago (14:40:37 UTC).
Ventana: desde medianoche local. SQLite consultado mode=ro. Sin cambios a estrategia.

No hay operaciones registradas hoy. Desde el16 se observa una compra XAUUSDmicro
el16 a12:10:55 Santiago, identificada anteriormente por eventos como ORB. Su
strategy_version en trades dice smc-v1: no usar ese campo solo para clasificar.

La auditoría nueva está presente desde el primer registro del día.6044 evaluaciones
SMC: H1 neutral2324; sin M5 1502; sin M15 972; política Boom/Crash545;
señal antigua415; esperando M5 posterior254; noticias28; ubicación4.
Son evaluaciones repetidas, no señales únicas. No hay ERROR en SYMBOL_PROCESS_RESULT
hoy hasta el corte; no implica ausencia absoluta de errores en otros subsistemas.
Cuarentena vacía.

H1: los2324 casos son NEUTRAL, no UNKNOWN. Ejemplo AUDJPY último máximoHH y mínimoLL:
pareja mixta. No implica falta de datos ni justifica imponer automáticamente dirección.

M5: fallos críticos registrados (pueden solaparse): desplazamiento412, retest limpio412,
BOS sin rechazo283, modo de confirmación125, conflicto chartista69, CHOCH sin microestructura5.

Antigüedad:415 rechazos corresponden a10 pares únicos instrumento/hora de señal.
Edad mínima15min, mediana845min, máxima1480min. La última vela M5 tenía5.1–6.3min desde
su apertura (coherente con vela cerrada de5min); no aparece congelamiento M5 en estos casos.
Ejemplo V25 a11:40 local: candidata01:55 local, última vela11:35;116 velas de edad,
límite2. No aumentar límite para recuperar candidatas de muchas horas.
Una candidata detectada retrospectivamente no prueba que fuese operable en tiempo real.

Comparación retest:953 registros, modo STRICT; ATR_BOUNDED no añadió ningún retest
limpio en esos registros. No demuestra comportamiento de candidatos no registrados.
Comparación ubicación:4 registros; H1_PRIMARY aprobaría2, ambos la misma candidata
BUY NZDJPY08:20 local reevaluada08:25/08:30. Precio89.377, equilibrioH1 89.479:
discount H1. EquilibriosM15 89.2455 yM5 89.282: premium en ambos. Calidad90,
confirmación92.31%, señal reciente. H1_PRIMARY permitiría seguir a filtros posteriores,
no garantiza ejecución ni resultado rentable. V10(1s) SELL siguió incompatible enH1.

Las variantes están en comparación, no activadas para operar. Instrumentar no aumenta
por sí mismo la frecuencia. SMC mantiene contexto H1, setupM15, confirmaciónM5 reciente
y ubicación en los tres marcos.

ORB aparte:76 evaluaciones (14formando rango,7espera inicial,53espera ruptura/retest,
2contextoHTF). Sus bloqueos no proceden del cambio H4 deSMC.

Prioridades: replay de NZDJPY para H1_PRIMARY con cotización ejecutable, RR/spread y
riesgo; auditar duración/contexto neutralH1 sin sustituirlo por BOS antiguo; mejorar
expiración y agrupación de candidatas antiguas en pantalla; conservar tolerancia ATR
actual hasta evidencia de utilidad; revisar confirmaciones de rechazo/desplazamiento
por instrumento antes de flexibilizarlas. No se prueba rentabilidad de variantes aquí.
