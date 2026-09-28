# Pausa automática del análisis por sesión

Los workers permanecen vivos para conservar conexiones y permitir el monitoreo
de posiciones. No se reduce su número de procesos.

LiveTradingConfig:
- session_analysis_pause_enabled=True
- session_warmup_minutes=3.0 (0 desactiva la preparación anticipada)

ORB: calendario de ORBConfig, por defecto 09:30–16:00 America/New_York.
Forex: ventana existente Tokio 09:00 hasta el corte 16:30 de Nueva York.
GOLD: ventana existente Tokio hasta NY 09:30 o Londres 08:00–12:00.
Sintéticos: sin pausa por sesión.
Se reutilizan las zonas horarias configuradas, incluyendo DST y fines de semana.
No se añade un calendario de festivos bursátiles.

Fuera de sesión el scheduler devuelve cero símbolos sin consultar velas.
En los tres minutos previos prepara un símbolo por ciclo, una sola vez:
SMC precalienta la caché H4/H1/M15/M5; ORB solicita velas cerradas como preflight
de disponibilidad (su estrategia no conserva caché propia).
La preparación no genera señales ni envía órdenes. Un fallo se registra
y el análisis normal puede reintentar al abrir. No se garantiza completar
todo el universo dentro de los tres minutos.

Al abrir se elimina la espera de polling previa y se aplica el scheduler
normal. Los filtros por sesión y todos los controles de entrada permanecen.
La pausa no detiene el monitor ni modifica reglas de SL/TP, BE o cierres.
El coordinador sigue controlando la desactivación manual; el calendario no
llama a activar workers ni modifica preferencias.

Estados visibles: OUTSIDE_SESSION / SESSION_WARMUP con próxima apertura UTC.
Se conservan en el heartbeat del coordinador. La comprobación se realiza
en la cadencia de cada ciclo, sin sleeps hasta el día siguiente.
Los ciclos vacíos no ejecutan ranking, selección ORB ni sincronización de
entrada; la supervisión de posiciones continúa por su ruta existente.
La sincronización, auditoría y consultas necesarias para posiciones abiertas
pueden seguir consumiendo recursos fuera de sesión.

Validación: 41 pruebas de calendario, DST, fin de semana, warmup, reactivación
y regresiones Forex/GOLD/scheduler aprobadas. No se reinició el daemon.
