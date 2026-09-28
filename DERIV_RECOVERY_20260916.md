# Recuperación de datos y diagnóstico — 16 septiembre 2026

Se corrigió una carrera en marketdata/rate_limit.py: la inicialización escribía
antes de adquirir el bloqueo interproceso. En Windows otro proceso podía tener
bloqueado ese byte. Toda lectura/escritura ahora ocurre dentro del bloqueo.
Las esperas ocurren fuera del bloqueo y vuelven a comprobar el estado compartido.

Deriv publica una pausa compartida cuando recibe rate limit, incluso al agotar
reintentos. Backoff por defecto: 3, 6, 12, 24, 30 segundos, más jitter; cuatro
reintentos. DAEMON_DERIV_RATE_LIMIT_BACKOFF_SECONDS y
DAEMON_DERIV_RATE_LIMIT_RETRIES conservan sus overrides. No garantiza eliminar
límites impuestos por el proveedor o tráfico de otras aplicaciones.

Los resultados ERROR de process_symbols conservan tipo, errno, filename y
traceback en SYMBOL_PROCESS_RESULT.exception_details. No se reintenta una
operación completa ni se repite una orden de trading por errores genéricos.
La causa exacta de los dos Permission denied históricos sigue sin demostrarse.

Validación: 26 pruebas pasan, incluyendo cuatro procesos concurrentes, cooldown
entre instancias, agotamiento de reintentos y persistencia del diagnóstico con
continuidad del siguiente símbolo. La suite antigua test_v113_external_market_data
no se puede recolectar: importa ExternalMarketDataRouter, que ya no existe;
se ejecutó la suite vigente test_v113_1_deriv_only_market_data.

Activación: reiniciar coordinadamente todos los workers para cargar el código y
retirar procesos con la implementación antigua. No se reinició el daemon durante
esta corrección. No se modificaron reglas SMC/ORB ni límites de riesgo.
