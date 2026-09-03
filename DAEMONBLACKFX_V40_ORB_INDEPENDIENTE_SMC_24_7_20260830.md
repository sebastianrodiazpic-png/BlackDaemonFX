# DaemonBlackFx v40 — ORB independiente / SMC sintéticos 24/7

## Corrección respecto de v39
v39 aplicó por error la ventana de Nueva York como filtro global de nuevas entradas.

v40 elimina ese comportamiento.

## SMC / índices sintéticos
Los instrumentos sintéticos continúan siendo analizados en cualquier horario:
- 24 horas;
- sin depender de Asia, Londres o New York;
- mientras el mercado/símbolo esté disponible en Deriv.

No existe un filtro horario global para SMC.

## ORB
La estrategia `ORB_NEW_YORK` mantiene su propia sesión independiente:
- lunes a viernes;
- `America/New_York`;
- 09:30 <= NY < 16:00;
- 09:30–09:45 construcción del Opening Range;
- desde 09:45 se permiten rupturas confirmadas;
- fuera de la sesión ORB no abre trades y no hace fallback a SMC.

Mercados ORB:
- XAUUSD;
- XAUUSDmicro;
- Wall Street 30;
- US Tech 100;
- US500.

## Optimización
Fuera de sesión New York el selector XAUUSD vs XAUUSDmicro tampoco realiza
cálculos costosos de sizing/spread/margen. Sólo vuelve a evaluar ambos contratos
cuando ORB está dentro de su ventana de sesión.

## Gestión de posiciones
La administración de trades abiertos sigue funcionando independientemente del horario:
Break Even, sincronización MT5, SL/TP y persistencia SQLAlchemy.
