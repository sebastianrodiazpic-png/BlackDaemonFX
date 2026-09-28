# GOLD Cuartos: validación previa de obstáculos — 23/09/2026

La operación 200 fue GOLD_QUARTERS; no había pasado por el control SMC de obstáculos. Se añade una protección de entrada específica para Cuartos sin convertirla en SMC ni alterar ORB.

Antes de ejecutar, incluyendo la evaluación dry-run, se consultan hasta 350 velas M15 y M5 del proveedor primario. Solo se usan velas cerradas, con historial mínimo y última vela cerrada vigente. El pipeline calcula OB contrarios y extremos de rango en ambas temporalidades. Los obstáculos llevan su timeframe en la evidencia.

La distancia al primer obstáculo se calcula desde ask MT5 para compra y bid MT5 para venta, con el SL y los objetivos originales. El mínimo reutiliza smc_obstacle_min_distance_r (actualmente 1R). Si la cotización está dentro de un OB contrario, la distancia es cero y se rechaza. Un obstáculo situado después de 1R no garantiza éxito, pero cumple este control.

La confirmación M5 se revalida con el límite de antigüedad existente: señal presente, feed actualizado, sin BOS/CHOCH contrario posterior ni cierre posterior/precio actual más allá del extremo adverso de la confirmación. También se rechaza una cotización que ya haya atravesado el SL o alcanzado el objetivo.

Si falta historial, columnas para evaluar OB o cotización ejecutable MT5, el recorrido permanece no evaluado (clear_path=null). Nunca se interpreta una captura ausente como recorrido despejado. El evento GOLD_QUARTERS_ENTRY_PREFLIGHT guarda la evidencia por timeframe, cotización, confirmación y recorrido; la señal/trade conserva entry_preflight y target_path_audit. El rechazo operativo se identifica como GOLD_QUARTERS_ENTRY_BLOCKED.

No modifica SL, TP, tamaño de los cuartos, reglas de ubicación H1, ni gestión de posiciones abiertas. No añade cierres anticipados. No demuestra retrospectivamente que el trade 200 hubiera sido bloqueado: requiere reconstruir sus velas causales, no usar los OB dibujados posteriormente en una captura de otro proveedor.

Validación: 55 pruebas aprobadas. Se cubren compras y ventas bloqueadas por obstáculos M15/M5 a 0,4R, recorrido evaluado sin obstáculos, datos antiguos, quote ausente, extremo de confirmación roto, bloqueo sin envío de orden y conservación del objetivo de Cuartos. Incluye regresión de SMC, ORB y auditoría.

Aplicación: requiere reiniciar el worker GOLD para cargar el código. No se reiniciaron procesos ni se enviaron órdenes en esta tarea.
