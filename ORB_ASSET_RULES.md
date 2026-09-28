# ORB NY: perfiles y auditoría

Las reglas se aplican en `NewYorkORBStrategy` con velas cerradas del proveedor
existente, tanto para BUY como SELL. No abren conexiones MT5 adicionales.

| Perfil | Modalidades | Buffer ATR | Máximo Momentum | Cancelación |
|---|---|---:|---:|---:|
| XAUUSD y micro | RETEST | 0.08 | 1.5 | 1.95 |
| US30 y alias | MOMENTUM, RETEST | 0.05 | 2.0 | 2.6 |
| NAS100 y alias | MOMENTUM, RETEST | 0.05 | 2.0 | 2.6 |
| BTCUSD | MOMENTUM | 0.05 | 1.8 | 2.34 |

`ORBConfig.asset_profiles` permite configurar cada perfil independientemente.
En `multi-bot-daemon`, `LiveTradingConfig.orb_asset_profiles` se copia al motor
ORB de cada worker. La versión declarada es `orb-ny-v4-asset-rules`; el arranque
registra `ORB_RULES_LOADED` con los perfiles efectivos, la ventana de retest y
el destino de métricas. Esto también aplica al modo unificado.
Los demás instrumentos conservan los parámetros generales de ORB y ambos modos.
`momentum_enabled=False` sigue desactivando Momentum globalmente. BTCUSD respeta
la sesión NY y la selección de instrumentos existente; no se selecciona automáticamente.

ATR(14) usa el cierre anterior y requiere al menos 15 velas cerradas. La amplitud
se compara con el ATR actual; superar el máximo elimina Momentum. Superar 1.3 veces
ese máximo cancela la sesión. Se reconstruyen las evaluaciones desde la formación
del rango para mantener la cancelación aunque crezca el ATR o se reinicie el proceso.
Los antiguos parámetros de amplitud que solo informaban ya no desactivan este control.
El buffer de ruptura conserva el máximo entre la fracción del rango y el buffer ATR.

Solo BTCUSD exige volumen entre los cuatro perfiles explícitos. Se auditan diez
velas anteriores a la ruptura, excluyendo la propia vela y las posteriores.
Prioridad: volumen real, ticks, volumen genérico. Momentum exige superar la media;
Retest exige al menos 70%. Un feed inexistente, inválido o sin historial completo
permite bypass neutral y deja evidencia. Un cero actual con historial positivo
sí representa volumen débil. Los filtros de cuerpo, desplazamiento y extensión
de Momentum continúan activos.

El retest admite las velas 1 a 3 posteriores a la ruptura. Calidad alta: velas 1/2
y mecha direccional/cuerpo >= 0.5; estándar: vela 3; baja: los demás casos.
Los pesos 1.0/0.75/0.5 son metadatos de calidad, no multiplicadores del lote ni
cambios del riesgo. Se conservan las protecciones de sesión, SL y salidas existentes.

Las ejecuciones mantienen `strategy_name=ORB_NEW_YORK` para compatibilidad interna,
y guardan `orb_metrics_strategy=ORB_NY_MOMENTUM` o `ORB_NY_RETEST`, calidad,
amplitud y evidencia de volumen en el lifecycle y el journal SQLite existente.
Se utiliza ese registro persistente e idempotente en lugar de otro archivo JSONL
que pudiera duplicar cierres o desincronizarse del PnL.

`TradingRepository.orb_execution_metrics()` entrega resultados separados por
entorno, broker, símbolo y modalidad. El dashboard muestra los resultados con
actualización de hasta 60 segundos. La esperanza es PnL neto cerrado / ejecuciones
cerradas; cada pierna ejecutada cuenta por separado. No se mezclan posiciones
abiertas, señales rechazadas ni operaciones antiguas sin modalidad identificable.

Pruebas: límites ATR, cancelación persistente, perfiles BUY/SELL, volumen real/tick,
ausencia de datos, calidad/expiración del retest, separación de métricas y recorrido
señal → ejecución PAPER → cierre → reapertura del repositorio.
