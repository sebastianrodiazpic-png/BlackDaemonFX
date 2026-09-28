# ORB independiente de SMC — 2026-09-21

ORB ya no consulta el analizador SMC ni requiere contexto H1/M15/H4 para validar sus entradas. Aplica tanto a ORB_BREAKOUT_RETEST como a ORB_BREAKOUT_MOMENTUM. La convergencia H4/H1 de momentum se retira junto con su dependencia de H1.

Se conserva el rango de apertura de Nueva York, las velas M5 cerradas, los filtros propios de retesteo/momentum, VWAP/POC según configuración, vigencia de señales y todos los controles de ejecución, exposición y riesgo. No se cambian SL/TP ni gestión de posiciones.

El score ya no suma confirmaciones H1/M15 desconocidas como verdaderas. La auditoría de posiciones ORB tampoco consulta SMC: registra contexto desactivado con política ORB_NATIVE_ONLY y razón ORB_HTF_NOT_REQUIRED. Las opciones antiguas orb_htf_context_enabled, orb_require_h1_alignment, orb_use_m15_context y orb_require_known_htf_context se conservan por compatibilidad, pero no reactivan esa dependencia.

La estrategia SMC de Forex, GOLD y sintéticos conserva sus reglas. Los registros históricos de rechazos ORB no se reescriben. Este cambio permite que las señales ORB avancen hacia los controles de ejecución sin el veto de contexto; no garantiza una orden si falla otro filtro.

Requiere reiniciar el worker ORB para cargar el código. No se reiniciaron procesos ni se enviaron órdenes durante la implementación.
