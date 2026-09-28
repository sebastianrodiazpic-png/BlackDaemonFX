# SMC: H1 como contexto principal

Cambio solicitado: eliminar H4 de las decisiones SMC de GOLD, Forex y sintéticos.

Configuración activa por defecto:
- LiveTradingConfig.require_h4_h1_convergence=False.
- Dirección estructural: H1.
- Premium/discount: H1, M15 y M5, tanto al validar como al precio ejecutable.
- Preparación previa de datos SMC: H1/M15/M5.
- H4 no bloquea ni autoriza una señal SMC en esta configuración.
- Se conserva el parámetro de convergencia como compatibilidad opt-in.
- ORB configura explícitamente H4/H1 y conserva sus reglas de momentum.
- Los gráficos y registros históricos H4 no se borran.

Secuencia:
H1 direccional → zona compatible H1/M15/M5 → setup M15 → confirmación M5
→ controles de ejecución y riesgo.
Se conservan liquidez, CHOCH/BOS, order block, retesteo, confluencias,
frescura, políticas Boom/Crash, horarios y controles de riesgo.
Si falta H1, rangos H4 de señales antiguas no sustituyen ese dato.

Consecuencia: SMC puede evaluar oportunidades que antes bloqueaba H4,
pero continúa rechazando BUY en premium y SELL en discount de los marcos activos.
No se garantiza una frecuencia ni rentabilidad mayores.

Este documento sustituye las referencias H4/H1 obligatorias para SMC en
SMC_ENTRY_LOCATION_ALL_MARKETS.md y VOLATILITY_ENTRY_LOCATION_FIX.md.
No modifica la descripción de ORB.
El daemon debe recargar el código. No se reinició ni se enviaron órdenes.
