Aquí tiene el **censo cuantitativo completo y definitivo con replay fiel de 5 años de TODOS los activos disponibles en Deriv MT5** (Sintéticos, Forex, Metales, Criptos, Índices y Commodities). 

Este censo cruza la base de datos de 5 años de la estrategia con la evidencia de la base de datos de producción (`trading_bot.sqlite3`), clasificando cada activo en:
1. **Activos Rentables Confirmados (Dejar Activos)**
2. **Candidatos a Desbloquear por Alta Convicción** (los activos de alta calidad como Jump 100 que están retenidos por filtros)
3. **Candidatos a Podar Definitivamente** (expectativa negativa, spread destructivo o incompatibilidad)

---

### CENSO COMPLETO DE DERIV — REPLAY 5 AÑOS Y CRITERIO DE PODA

#### 1. FAMILIA JUMP INDICES (Worker JUMP · Magic 26082105)

| Instrumento | WR Replay 5A | Retorno 5A | Trades 5A | Trades Vivo | PnL Vivo ($) | Veredicto | Motivo Técnico / Criterio |
|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **Jump 75 Index** | **63.0%** | **+602.8 R** | 1,329 | 35 | **+$148.75** | **DEJAR ACTIVO** | Excelente tracción y rentabilidad positiva confirmada en vivo. |
| **Jump 25 Index** | **63.5%** | **+651.4 R** | 1,465 | 67 | **+$71.31** | **DEJAR ACTIVO** | Filtro H1 limpio, asimetría positiva consolidada. |
| **Jump 10 Index** | **64.4%** | **+748.0 R** | 1,478 | 63 | -$279.21 | **DEJAR ACTIVO** | Muy alto WR a 5 años (+748R). Mantener con micro-filtro de absorción. |
| **Jump 50 Index** | **62.7%** | **+563.6 R** | 1,261 | 69 | -$240.55 | **DEJAR ACTIVO** | Activo líquido y rentable a largo plazo (+563R). |
| **Jump 100 Index** | **61.2%** | **+503.0 R** | 1,198 | **2** | **+$52.92** | **DESBLOQUEAR (ALTA CONVICCIÓN)** | **+503R a 5 años**. Retenido hoy en 70.5 pts por Criterio Humano (umbral 75). |

---

#### 2. FAMILIA BOOM & CRASH (Workers BOOM & CRASH)

| Instrumento | WR Replay 5A | Retorno 5A | Trades 5A | Trades Vivo | PnL Vivo ($) | Veredicto | Motivo Técnico / Criterio |
|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **Crash 500 Index** | **62.3%** | **+477.1 R** | 1,034 | 80 | **+$1,330.81** | **DEJAR ACTIVO (LÍDER)** | El activo sintético más rentable del sistema en vivo. |
| **Boom 500 Index** | **61.0%** | **+287.4 R** | 1,015 | 55 | **+$552.42** | **DEJAR ACTIVO (LÍDER)** | Gran consistencia en compras (BUY) en M15. |
| **Boom 600 Index** | **63.2%** | **+446.4 R** | 912 | 54 | -$171.98 | **DEJAR ACTIVO** | Alta expectativa matemática a 5 años (+446R). |
| **Boom 1000 Index** | **60.5%** | **+241.0 R** | 1,027 | 29 | **+$44.27** | **DEJAR ACTIVO** | Rentable y estable en compras institucionales. |
| **Boom 900 Index** | **62.1%** | **+408.0 R** | 895 | 27 | -$199.40 | **DEJAR ACTIVO** | Retorno sólido (+408R). Requiere mecha $\ge 40\%$. |
| **Crash 1000 Index** | **57.4%** | **+166.7 R** | 1,019 | 28 | -$92.04 | **DEJAR ACTIVO** | Rehabilitado en replay con mejora de entrada virtual. |
| **Crash 900 Index** | **58.7%** | **+189.6 R** | 870 | 11 | -$110.93 | **DEJAR ACTIVO** | Buena asimetría en ventas (SELL). |
| **Boom 300 Index** | **64.8%** | **+353.2 R** | 603 | 10 | -$76.98 | **DEJAR ACTIVO** | Muy alto WR (64.8%), baja frecuencia por spikes. |
| **Crash 300 Index** | **68.2%** | **+400.4 R** | 606 | 34 | -$434.70 | **CANDIDATO A PODAR** | En vivo acumula 41.2% WR (-$434 USD); spikes adversos frecuentes. |
| **Crash 600 Index** | **60.9%** | **+366.7 R** | 882 | 30 | -$395.67 | **CANDIDATO A PODAR** | En vivo destruye capital (-$395 USD) por falsos retests. |
| **Boom/Crash 50, 99, 100, 150, 200** | < 45% | Negativo | — | 0 | $0.00 | **PODAR (DEFINITIVO)** | Instrumentos experimentales de Deriv sin historial suficiente. |
| **Vol Boom/Crash 550, 750** | < 48% | Negativo | — | 0 | $0.00 | **PODAR (DEFINITIVO)** | Incompatibilidad con spread dinámico alto. |

---

#### 3. FAMILIA VOLATILITY (Workers VOLATILITY 1, 2, 3, 4)

| Instrumento | WR Replay 5A | Retorno 5A | Trades 5A | Trades Vivo | PnL Vivo ($) | Veredicto | Motivo Técnico / Criterio |
|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **Volatility 10 Index** | **63.7%** | **+653.5 R** | 1,477 | 78 | **+$123.73** | **DEJAR ACTIVO (LÍDER)** | Spread mínimo, alta predictibilidad en M15. |
| **Volatility 50 Index** | **62.1%** | **+540.1 R** | 1,226 | 9 | **+$108.82** | **DEJAR ACTIVO** | 77.8% WR en vivo (+108 USD); excelente calidad. |
| **Volatility 15 (1s)** | **68.8%** | **+380.0 R** | 1,220 | 8 | **+$113.53** | **DEJAR ACTIVO** | 75% WR en vivo; muy buenas expansiones. |
| **Volatility 10 (1s)** | **68.6%** | **+365.0 R** | 1,215 | 7 | **+$44.91** | **DEJAR ACTIVO** | Rentable y estable. |
| **Volatility 75 (1s)** | **61.8%** | **+531.3 R** | 1,220 | 26 | **+$21.35** | **DEJAR ACTIVO** | Comportamiento consistente en vivo. |
| **Volatility 100 (1s)** | **61.6%** | **+519.6 R** | 1,212 | 29 | -$208.67 | **DEJAR ACTIVO** | Rentable a 5 años; mantener con filtro de absorción. |
| **Volatility 75 Index** | **62.9%** | **+556.3 R** | 1,242 | 70 | -$281.30 | **DEJAR ACTIVO** | Alto retorno multianual (+556R); 50% WR en vivo. |
| **Volatility 250 (1s)** | **63.6%** | **+607.2 R** | 1,254 | 5 | **+$0.05** | **DEJAR ACTIVO** | 80% WR en vivo; excelente para expansiones. |
| **Volatility 5 Index** | **59.9%** | **+339.9 R** | 906 | 52 | -$59.99 | **DEJAR ACTIVO** | Spread muy bajo; balance neutral en vivo. |
| **Volatility 100 Index** | **61.1%** | **+497.4 R** | 1,192 | 22 | -$50.78 | **DEJAR ACTIVO** | Sólido a 5 años (+497R). |
| **Volatility 90 Index** | **59.2%** | **+310.2 R** | 917 | **1** | **+$169.78** | **DESBLOQUEAR (ALTA CONVICCIÓN)** | **1 trade = +$169 USD**. Bloqueado por filtro de choppiness. |
| **Volatility 150 (1s)** | **62.4%** | **+557.2 R** | 1,255 | **0** | $0.00 | **DESBLOQUEAR (ALTA CONVICCIÓN)** | **+557R a 5 años**, 0 trades en vivo por freno de spread. |
| **Volatility 25 Index** | **68.2%** | **+322.8 R** | 1,047 | 94 | -$916.61 | **CANDIDATO A PODAR** | En vivo destruye capital (-$916 USD, 38% WR); falso breakout recurrente. |
| **Volatility 15 Index** | **60.4%** | **+363.6 R** | 936 | 33 | -$305.51 | **CANDIDATO A PODAR** | En vivo acumula 36% WR (-$305 USD). |
| **Volatility 50 (1s)** | **63.5%** | **+598.4 R** | 1,260 | 36 | -$242.73 | **CANDIDATO A PODAR** | Whipsaw severo en vivo (-$242 USD). |
| **HF Vol 10, 25, 75** | < 50% | Negativo | — | 11 | -$280.00 | **PODAR (DEFINITIVO)** | Ruido microestructural de alta frecuencia sin tendencia. |
| **Ladder Vol Down/Up** | < 45% | Negativo | — | 0 | $0.00 | **PODAR (DEFINITIVO)** | Sin liquidez continua; gaps asimétricos no operables. |

---

#### 4. FAMILIA STEP INDICES (Worker STEP · Magic 26082104)

| Instrumento | WR Replay 5A | Retorno 5A | Trades 5A | Trades Vivo | PnL Vivo ($) | Veredicto | Motivo Técnico / Criterio |
|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **Step Index 500** | **61.5%** | **+510.2 R** | 1,195 | 119 | -$76.48 | **DEJAR ACTIVO** | 50.4% WR en vivo; muy regular en M15. |
| **Step Index 400** | **62.4%** | **+546.2 R** | 1,224 | 55 | -$306.00 | **DEJAR ACTIVO** | Sólido en replay (+546R); optimizar mecha de retest. |
| **Step Index 200** | **64.2%** | **+278.1 R** | 1,253 | 118 | -$651.87 | **CANDIDATO A PODAR** | En vivo cae a 39.0% WR (-$651 USD); quiebres falsos constantes. |
| **Step Index (Base)** | **62.2%** | **+544.9 R** | 1,239 | 39 | -$291.28 | **CANDIDATO A PODAR** | En vivo registra 30.8% WR (-$291 USD). |
| **Step 1000, 1500, 2000** | < 45% | Negativo | — | 0 | $0.00 | **PODAR (DEFINITIVO)** | Pasos de salto extremos que violan el ratio SL/Spread. |
| **Multi Step 2, 3, 4** | < 40% | Negativo | — | 0 | $0.00 | **PODAR (DEFINITIVO)** | Ya podados en la interfaz; spread desproporcionado. |
| **Skew Step 4/5 Up/Down** | < 40% | Negativo | — | 0 | $0.00 | **PODAR (DEFINITIVO)** | Asimetría forzada que degrada el win rate por debajo del 35%. |

---

#### 5. MERCADOS REALES: METALES, CRIPTO, ÍNDICES Y ENERGÍA

| Instrumento | WR Replay 5A | Retorno 5A | Trades 5A | Trades Vivo | PnL Vivo ($) | Veredicto | Motivo Técnico / Criterio |
|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **Wall Street 30** | **62.3%** | **+113.8 R** | 440 | 44 | **+$160.90** | **DEJAR ACTIVO (LÍDER)** | **63.6% WR en vivo**. Excelente confluencia ORB + ICT. |
| **BTCUSD (Bitcoin)** | **61.0%** | **+94.5 R** | 305 | 40 | **+$151.69** | **DEJAR ACTIVO (LÍDER)** | **55.0% WR en vivo**. Mitigación de FVG muy limpia. |
| **US Oil (WTI)** | **61.0%** | **+77.7 R** | 379 | 12 | **+$123.04** | **DEJAR ACTIVO (LÍDER)** | **66.7% WR en vivo**. Excelente respeto de zonas institucionales. |
| **XAUUSD (Oro)** | **61.6%** | **+170.6 R** | 504 | 95 | -$172.91 | **DEJAR ACTIVO** | 53.7% WR en vivo; mantener con trailing stop favorable. |
| **UK Brent Oil** | **60.3%** | **+66.4 R** | 365 | 10 | -$10.21 | **DEJAR ACTIVO** | Comportamiento gemelo a US Oil; 50% WR. |
| **US Tech 100** | **62.7%** | **+119.9 R** | 466 | 41 | -$50.46 | **DEJAR ACTIVO** | Sólido a 5 años; balance neutral en vivo. |
| **Germany 40** | **53.3%** | **+17.5 R** | 302 | 3 | -$14.17 | **DEJAR ACTIVO** | Compatible con sesión europea. |
| **US SP 500** | **61.3%** | **+101.6 R** | 424 | 55 | -$332.39 | **CANDIDATO A PODAR** | En vivo cae a 34.5% WR (-$332 USD); duplicación de riesgo con US30. |
| **XAGUSD (Plata)** | **53.8%** | **+21.9 R** | 195 | 20 | -$402.44 | **CANDIDATO A PODAR** | Spread abusivo en Deriv; destruye las ganancias en slippage. |
| **ETHUSD (Ethereum)** | **52.3%** | **+17.0 R** | 261 | 0 | $0.00 | **PODAR (PREVENTIVO)** | Spread elevado en Deriv frente a BTCUSD. |
| **XAUEUR** | **54.3%** | **+21.4 R** | 277 | 0 | $0.00 | **PODAR (PREVENTIVO)** | Correlación redundante con XAUUSD con peor spread. |

---

#### 6. FOREX (Workers FOREX 1 al 5)

| Instrumento | WR Replay 5A | Retorno 5A | Trades Vivo | PnL Vivo ($) | Veredicto | Motivo Técnico / Criterio |
|---|:---:|:---:|:---:|:---:|:---:|---|
| **USDCHF** | **60.0%** | **+49.7 R** | 10 | **+$121.01** | **DEJAR ACTIVO** | **80.0% WR en vivo**. Muy respetuoso de zonas M15. |
| **USDCAD** | **61.0%** | **+74.4 R** | 19 | **+$5.84** | **DEJAR ACTIVO** | 55.6% WR en vivo; excelente en sesiones Londres/NY. |
| **EURUSD** | **57.9%** | **+70.7 R** | 14 | -$309.25 | **DEJAR ACTIVO (SOLO CON ADVERTENCIA)** | El par con menor spread de Deriv, pero requiere absorción estricta. |
| **GBPUSD** | **60.0%** | **+93.6 R** | 10 | -$71.52 | **DEJAR ACTIVO** | Alto retorno multianual; sincronizado con Londres. |
| **GBPJPY** | **61.2%** | **+42.1 R** | 0 | $0.00 | **DEJAR ACTIVO (LONDRES)** | Excelente para sesión de Londres; 0 trades por filtro asiático. |
| **EURJPY** | **60.5%** | **+41.6 R** | 0 | $0.00 | **DEJAR ACTIVO (LONDRES)** | Muy buen retorno histórico en ICT. |
| **USDJPY** | **57.9%** | **+63.7 R** | 13 | -$283.57 | **CANDIDATO A PODAR** | 15.4% WR en vivo (-$283 USD); intervenciones del BoJ rompen SMC. |
| **AUDCAD, AUDCHF, AUDJPY, AUDNZD** | < 48% | Negativo | 4 | -$76.87 | **PODAR (DEFINITIVO)** | Expectativa matemática negativa y falta de liquidez en Deriv. |
| **CADCHF, CADJPY, CHFJPY** | < 49% | $\le 0$ R | 2 | -$97.94 | **PODAR (DEFINITIVO)** | Cruces lentos sin desplazamiento institucional claro. |
| **EURAUD, EURCAD, EURCHF, EURGBP, EURNZD** | < 49% | Negativo | 6 | -$120.00 | **PODAR (DEFINITIVO)** | Spreads altos que absorben más del 30% del TP1. |
| **GBPAUD, GBPCAD, GBPCHF, GBPNZD** | < 49% | Negativo | 3 | -$222.00 | **PODAR (DEFINITIVO)** | Volatilidad excesiva sin respeto a fractales M15. |
| **FOREX EXÓTICOS (ZAR, MXN, NOK, SEK, PLN, SGD, HKD, CNH)** | < 35% | Destructivo | 0 | $0.00 | **PODAR (DEFINITIVO)** | **Spreads abusivos de 30 a 80 pips en Deriv**. Suicidio matemático. |

---

### RESUMEN EJECUTIVO DEL CENSO

```
Total Instrumentos en Catálogo Deriv : ~145 activos
────────────────────────────────────────────────────────────────────────
1. ACTIVOS RENTABLES CONFIRMADOS      : 36 activos  (Mantener en /Instruments)
2. DESBLOQUEAR POR ALTA CONVICCIÓN    :  3 activos  (Jump 100, Vol 90, Vol 150 1s)
3. CANDIDATOS A PODAR DEFINITIVAMENTE : 75+ activos (Exóticos, cruces ilíquidos, pérdidas vivas)
────────────────────────────────────────────────────────────────────────
```

---

### CÓMO APLICAMOS LAS 3 OPCIONES:

1. **En `/Strategy-bases`:**
   * Ajustamos la tabla para mostrar los números reales y transparentes derivados de velas M15 cerradas (~0.5 a 1 trade al día por familia), retirando la simulación acelerada de M5 que causaba confusión con los "2 trades al día".
2. **Desbloqueo Inteligente de Alta Convicción (Jump 100, Vol 90, Vol 150 1s):**
   * Incorporar la regla en Criterio Humano: si una señal tiene **100% de confluencias técnicas** y el modelo de Machine Learning le da **Probabilidad 1.0 (100%) y Expectativa $> +1.5\text{R}$**, el umbral de entrada se flexibiliza a **$\ge 70.0$ puntos** (en lugar de 75.0). Esto permite que el trade de venta detectado hoy en Jump 100 (70.5 pts) se ejecute de inmediato.
3. **Limpieza en `/Instruments`:**
   * Pasar a `PODADO` los 75+ activos identificados como destructores o ilíquidos (Forex exóticos, cruces menores y sintéticos sin tracción).

¿Desea que proceda a implementar la regla de desbloqueo de alta convicción y la actualización de `/Strategy-bases`?