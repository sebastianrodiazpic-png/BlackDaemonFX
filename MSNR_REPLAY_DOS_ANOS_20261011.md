# Malaysian SNR: replay comparativo de dos años

Periodo de señales: **2024-10-11 a 2026-10-11**, 730 días. Datos nativos del terminal, con calentamiento desde agosto de 2024.
Universo: 195 instrumentos visibles/configurados y del replay anterior; 193 evaluados, 151 con historia desde el inicio y 42 parciales. 2 no disponibles.

**En este replay, v2.1 supera el WinRate de v2.0 en el grupo con dos años completos, excluyendo contratos micro.** Diferencia: 0.56 puntos porcentuales. Este resultado histórico no acredita un WinRate futuro.
El intervalo descriptivo de la diferencia incluye cero: no se acredita una mejora estable del WinRate.
La selección actual sin contratos micro pasa de 32.26% a 31.89% en los activos con dos años. El agregado principal todavía tiene expectativa -0.0933 R/trade y factor de beneficio 0.866.

| Universo | Operaciones anterior / v2.1 | WinRate anterior | WinRate v2.1 | Diferencia pp | R/trade v2.1 | Factor beneficio v2.1 |
|---|---:|---:|---:|---:|---:|---:|
| Todos los históricos, incluidos parciales | 2980 / 2036 | 31.04% | 30.94% | -0.10 | -0.0838 | 0.878 |
| Dos años completos | 2363 / 1596 | 30.09% | 30.51% | 0.42 | -0.0932 | 0.866 |
| Dos años, excluyendo contratos micro | 2216 / 1506 | 29.92% | 30.48% | 0.56 | -0.0933 | 0.866 |
| Dos años sin micro: sólo salidas SL/TP del mismo replay | 2176 / 1474 | 28.91% | 29.10% | 0.19 | -0.1188 | 0.833 |
| Sólo históricos parciales | 617 / 440 | 34.68% | 32.50% | -2.18 | -0.0497 | 0.926 |
| Selección actual, incluidos parciales | 523 / 392 | 32.31% | 33.42% | 1.11 | -0.0084 | 0.987 |
| Selección actual con dos años | 458 / 356 | 32.10% | 33.15% | 1.05 | -0.0158 | 0.976 |
| Selección actual con dos años, sin contratos micro | 403 / 323 | 32.26% | 31.89% | -0.37 | -0.0481 | 0.929 |
| Selección actual sin micro, incluidos parciales | 463 / 358 | 32.40% | 32.40% | 0.00 | -0.0342 | 0.949 |
| Sintéticos con dos años | 1419 / 1050 | 31.71% | 30.67% | -1.04 | -0.0774 | 0.888 |
| Otros instrumentos con dos años | 944 / 546 | 27.65% | 30.22% | 2.57 | -0.1236 | 0.823 |

## Interpretación y referencia histórica

Intervalo Wilson 95% del WinRate v2.1, grupo con dos años: [28.205, 32.85]. Intervalo descriptivo de la diferencia con bloques semanales: [-1.61, 2.857] pp.
R total v2.1: -140.488; drawdown máximo agregado: 174.338 R. El agregado suma riesgos unitarios de pruebas por símbolo: no representa una cuenta con límites de cartera ni rentabilidad en dólares.
Los estimados anteriores de 42,1% para activos ACTIVE, 34,43% o 31,91% proceden de otros detectores, universos o simulaciones. El replay de 207.520 trades fue señalado por anticipar información futura. Se conservan como referencias, pero no sirven como comparación controlada de estos cambios.
El escenario 1 de continuación sigue deshabilitado en los parámetros actuales. Este experimento evalúa el retest persistente, los dos gatillos, obstáculos vigentes, invalidación y deduplicación para QM/fractal; no demuestra el efecto aislado de admitir un nivel probado una vez.

## Estabilidad por año

| Periodo | Universo | Versión | Operaciones | WinRate | R/trade |
|---|---|---|---:|---:|---:|
| Primer año | Dos años, excluyendo contratos micro | baseline | 1086 | 31.03% | -0.0951 |
| Primer año | Dos años, excluyendo contratos micro | v21 | 779 | 31.58% | -0.0673 |
| Primer año | Selección actual con dos años, sin contratos micro | baseline | 194 | 34.02% | 0.0061 |
| Primer año | Selección actual con dos años, sin contratos micro | v21 | 170 | 30.59% | -0.0641 |
| Segundo año | Dos años, excluyendo contratos micro | baseline | 1130 | 28.85% | -0.1316 |
| Segundo año | Dos años, excluyendo contratos micro | v21 | 727 | 29.30% | -0.1211 |
| Segundo año | Selección actual con dos años, sin contratos micro | baseline | 209 | 30.62% | -0.1280 |
| Segundo año | Selección actual con dos años, sin contratos micro | v21 | 153 | 33.33% | -0.0304 |

## Desglose de entradas v2.1

Estos subgrupos describen operaciones realizadas; no aíslan el efecto causal de cada cambio.
- Entradas recuperadas entre 60 y 90 minutos: 191 operaciones, WinRate 23.56%, expectativa -0.3031 R/trade.
- Entradas entre 15 y 45 minutos: 1845 operaciones, WinRate 31.71%, expectativa -0.0611 R/trade.
- CRT_M15_SWEEP_AND_ABSORPTION_CLOSE: 1574 operaciones, WinRate 30.37%, expectativa -0.1039 R/trade.
- M15_ZONE_REJECTION_CLOSE: 462 operaciones, WinRate 32.90%, expectativa -0.0154 R/trade.

## Resultado por instrumento

| Instrumento | Cobertura | Trades anterior / v2.1 | WR anterior | WR v2.1 | R/trade v2.1 | R total v2.1 |
|---|---|---:|---:|---:|---:|---:|
| AAVUSD | Dos años | 4 / 4 | 25.00% | 50.00% | 0.6201 | 2.480 |
| ADAUSD | Dos años | 16 / 9 | 43.75% | 22.22% | -0.3866 | -3.479 |
| ALGUSD | Dos años | 16 / 10 | 37.50% | 30.00% | -0.0126 | -0.126 |
| APEUSD | Dos años | 4 / 4 | 25.00% | 50.00% | 0.2657 | 1.063 |
| APTUSD | Parcial desde 2024-12-13 | 9 / 10 | 22.22% | 20.00% | -0.4495 | -4.495 |
| AUDCAD | Dos años | 7 / 4 | 14.29% | 25.00% | -0.1886 | -0.754 |
| AUDCADmicro | Dos años | 7 / 4 | 14.29% | 25.00% | -0.1886 | -0.754 |
| AUDCHF | Dos años | 4 / 4 | 25.00% | 0.00% | -1.0000 | -4.000 |
| AUDCHFmicro | Dos años | 4 / 4 | 25.00% | 0.00% | -1.0000 | -4.000 |
| AUDJPY | Dos años | 11 / 9 | 36.36% | 22.22% | -0.2242 | -2.018 |
| AUDJPYmicro | Dos años | 11 / 9 | 36.36% | 22.22% | -0.2242 | -2.018 |
| AUDNZD | Dos años | 6 / 6 | 0.00% | 16.67% | -0.6653 | -3.992 |
| AUDNZDmicro | Dos años | 6 / 6 | 0.00% | 16.67% | -0.6653 | -3.992 |
| AUDSGD | Dos años | 15 / 7 | 20.00% | 14.29% | -0.5357 | -3.750 |
| AUDUSD | Dos años | 8 / 9 | 37.50% | 44.44% | 0.1667 | 1.501 |
| AUDUSDmicro | Dos años | 8 / 9 | 37.50% | 44.44% | 0.1667 | 1.501 |
| AVAUSD | Dos años | 8 / 5 | 25.00% | 20.00% | -0.3000 | -1.500 |
| BATUSD | Dos años | 13 / 9 | 30.77% | 33.33% | 0.1340 | 1.206 |
| BCHUSD | Dos años | 10 / 1 | 30.00% | 100.00% | 2.5000 | 2.500 |
| BNBUSD | Dos años | 10 / 6 | 20.00% | 33.33% | -0.1231 | -0.739 |
| BTCETH | Dos años | 8 / 2 | 25.00% | 0.00% | -1.0000 | -2.000 |
| BTCLTC | Dos años | 13 / 9 | 46.15% | 44.44% | 0.3580 | 3.222 |
| BTCUSD | Dos años | 10 / 10 | 40.00% | 40.00% | 0.3494 | 3.494 |
| BTCUSDmicro | No disponible | — | — | — | — | — |
| Boom 100 Index | Parcial desde 2026-05-20 | 1 / 2 | 0.00% | 0.00% | -1.0000 | -2.000 |
| Boom 1000 Index | Dos años | 9 / 13 | 11.11% | 0.00% | -1.0000 | -13.000 |
| Boom 150 Index | Parcial desde 2025-09-19 | 11 / 7 | 63.64% | 42.86% | 0.2851 | 1.996 |
| Boom 200 Index | Parcial desde 2026-05-20 | 5 / 6 | 40.00% | 33.33% | -0.1238 | -0.743 |
| Boom 300 Index | Dos años | 16 / 14 | 18.75% | 21.43% | -0.3754 | -5.255 |
| Boom 50 Index | Parcial desde 2025-12-24 | 13 / 10 | 23.08% | 30.00% | -0.1401 | -1.401 |
| Boom 500 Index | Dos años | 11 / 8 | 27.27% | 37.50% | 0.2794 | 2.235 |
| Boom 600 Index | Dos años | 28 / 23 | 21.43% | 21.74% | -0.4456 | -10.250 |
| Boom 900 Index | Dos años | 15 / 12 | 20.00% | 16.67% | -0.4385 | -5.262 |
| Boom 99 Index | Parcial desde 2026-05-20 | 7 / 6 | 42.86% | 50.00% | 0.5012 | 3.007 |
| CADCHF | Dos años | 11 / 3 | 9.09% | 0.00% | -1.0322 | -3.096 |
| CADJPY | Dos años | 9 / 9 | 22.22% | 22.22% | -0.4432 | -3.988 |
| CHFJPY | Dos años | 5 / 1 | 40.00% | 100.00% | 1.6430 | 1.643 |
| COMUSD | Parcial desde 2024-12-13 | 14 / 5 | 28.57% | 0.00% | -1.0000 | -5.000 |
| Crash 100 Index | Parcial desde 2026-05-20 | 9 / 4 | 44.44% | 25.00% | -0.1250 | -0.500 |
| Crash 1000 Index | Dos años | 17 / 17 | 29.41% | 29.41% | -0.0942 | -1.602 |
| Crash 150 Index | Parcial desde 2025-09-19 | 11 / 6 | 27.27% | 50.00% | 0.3853 | 2.312 |
| Crash 200 Index | Parcial desde 2026-05-20 | 3 / 4 | 33.33% | 50.00% | 0.7149 | 2.860 |
| Crash 300 Index | Dos años | 24 / 16 | 33.33% | 25.00% | -0.3558 | -5.693 |
| Crash 50 Index | Parcial desde 2025-12-24 | 6 / 6 | 50.00% | 33.33% | -0.0832 | -0.499 |
| Crash 500 Index | Dos años | 22 / 16 | 18.18% | 18.75% | -0.3438 | -5.500 |
| Crash 600 Index | Dos años | 14 / 10 | 50.00% | 20.00% | -0.3000 | -3.000 |
| Crash 900 Index | Dos años | 19 / 15 | 31.58% | 26.67% | -0.2501 | -3.751 |
| Crash 99 Index | Parcial desde 2026-05-20 | 8 / 8 | 37.50% | 25.00% | -0.3118 | -2.495 |
| Crash Boom Flip 1000 Index | Parcial desde 2026-07-17 | 2 / 4 | 100.00% | 50.00% | 0.3742 | 1.497 |
| Crash Boom Flip 150 Index | Parcial desde 2026-07-17 | 4 / 2 | 25.00% | 0.00% | -1.0000 | -2.000 |
| Crash Boom Flip 300 Index | Parcial desde 2026-07-17 | 9 / 6 | 33.33% | 50.00% | 0.0001 | 0.001 |
| Crash Boom Flip 500 Index | Parcial desde 2026-07-17 | 3 / 3 | 66.67% | 33.33% | -0.3331 | -0.999 |
| DOGUSD | Dos años | 8 / 7 | 50.00% | 42.86% | 0.2881 | 2.017 |
| DOTUSD | Dos años | 18 / 13 | 38.89% | 30.77% | -0.0559 | -0.727 |
| DSHUSD | Dos años | 11 / 9 | 9.09% | 22.22% | -0.2354 | -2.119 |
| ETCUSD | Dos años | 14 / 9 | 35.71% | 22.22% | -0.4319 | -3.887 |
| ETHUSD | Dos años | 11 / 9 | 27.27% | 33.33% | 0.1011 | 0.910 |
| EURAUD | Dos años | 7 / 6 | 42.86% | 16.67% | -0.4496 | -2.697 |
| EURAUDmicro | Dos años | 7 / 6 | 42.86% | 16.67% | -0.4496 | -2.697 |
| EURCAD | Dos años | 8 / 3 | 62.50% | 33.33% | -0.1735 | -0.521 |
| EURCADmicro | Dos años | 8 / 3 | 62.50% | 33.33% | -0.1735 | -0.521 |
| EURCHF | Dos años | 4 / 0 | 0.00% | — | — | 0.000 |
| EURCHFmicro | Dos años | 4 / 0 | 0.00% | — | — | 0.000 |
| EURGBP | Dos años | 6 / 4 | 16.67% | 50.00% | 0.1498 | 0.599 |
| EURGBPmicro | Dos años | 6 / 4 | 16.67% | 50.00% | 0.1498 | 0.599 |
| EURHKD | Dos años | 6 / 3 | 33.33% | 66.67% | 1.1037 | 3.311 |
| EURJPY | Dos años | 14 / 6 | 28.57% | 16.67% | -0.4665 | -2.799 |
| EURJPYmicro | Dos años | 14 / 6 | 28.57% | 16.67% | -0.4665 | -2.799 |
| EURMXN | Dos años | 11 / 6 | 18.18% | 16.67% | -0.6647 | -3.988 |
| EURNOK | Dos años | 11 / 3 | 18.18% | 0.00% | -1.0000 | -3.000 |
| EURNZD | Dos años | 6 / 4 | 33.33% | 0.00% | -1.0000 | -4.000 |
| EURNZDmicro | Dos años | 6 / 4 | 33.33% | 0.00% | -1.0000 | -4.000 |
| EURPLN | Dos años | 5 / 3 | 20.00% | 33.33% | -0.2858 | -0.857 |
| EURSEK | Dos años | 7 / 6 | 28.57% | 33.33% | -0.2718 | -1.631 |
| EURSGD | Dos años | 4 / 2 | 0.00% | 0.00% | -1.0000 | -2.000 |
| EURUSD | Dos años | 2 / 2 | 50.00% | 0.00% | -1.0000 | -2.000 |
| EURUSDmicro | Dos años | 2 / 2 | 50.00% | 0.00% | -1.0000 | -2.000 |
| EURZAR | Dos años | 8 / 4 | 37.50% | 0.00% | -1.0945 | -4.378 |
| FILUSD | Dos años | 3 / 1 | 66.67% | 100.00% | 2.5000 | 2.500 |
| GBPAUD | Dos años | 8 / 5 | 25.00% | 20.00% | -0.3500 | -1.750 |
| GBPCAD | Dos años | 3 / 3 | 66.67% | 33.33% | -0.3326 | -0.998 |
| GBPCHF | Dos años | 4 / 0 | 25.00% | — | — | 0.000 |
| GBPCHFmicro | Dos años | 4 / 0 | 25.00% | — | — | 0.000 |
| GBPJPY | Dos años | 6 / 5 | 16.67% | 40.00% | 0.3500 | 1.750 |
| GBPJPYmicro | Dos años | 6 / 5 | 16.67% | 40.00% | 0.3500 | 1.750 |
| GBPNOK | Dos años | 10 / 3 | 10.00% | 33.33% | -0.1976 | -0.593 |
| GBPNZD | Dos años | 11 / 8 | 18.18% | 25.00% | -0.3315 | -2.652 |
| GBPSEK | Dos años | 6 / 3 | 0.00% | 0.00% | -1.0000 | -3.000 |
| GBPSGD | Dos años | 6 / 3 | 33.33% | 66.67% | 0.8444 | 2.533 |
| GBPUSD | Dos años | 9 / 3 | 55.56% | 100.00% | 2.1202 | 6.361 |
| GBPUSDmicro | Dos años | 9 / 3 | 55.56% | 100.00% | 2.1202 | 6.361 |
| Gold Basket | Dos años | 11 / 7 | 36.36% | 28.57% | -0.4254 | -2.977 |
| HKDJPY | Dos años | 8 / 5 | 37.50% | 40.00% | -0.1184 | -0.592 |
| High Frequency Vol 10 Index | Parcial desde 2026-03-19 | 11 / 2 | 27.27% | 0.00% | -1.0000 | -2.000 |
| High Frequency Vol 100 Index | Parcial desde 2026-03-19 | 10 / 5 | 30.00% | 20.00% | -0.3000 | -1.500 |
| High Frequency Vol 25 Index | Parcial desde 2026-03-19 | 16 / 13 | 43.75% | 23.08% | -0.2709 | -3.521 |
| High Frequency Vol 50 Index | Parcial desde 2026-03-19 | 16 / 7 | 25.00% | 57.14% | 0.8933 | 6.253 |
| High Frequency Vol 75 Index | Parcial desde 2026-03-19 | 13 / 10 | 53.85% | 50.00% | 0.5248 | 5.248 |
| IMXUSD | Parcial desde 2024-12-13 | 17 / 9 | 35.29% | 44.44% | 0.4931 | 4.438 |
| IOTUSD | Dos años | 13 / 9 | 38.46% | 44.44% | 0.4721 | 4.249 |
| Jump 10 Index | Dos años | 37 / 37 | 37.84% | 37.84% | 0.0275 | 1.019 |
| Jump 100 Index | Dos años | 49 / 34 | 40.82% | 41.18% | 0.1943 | 6.605 |
| Jump 25 Index | Dos años | 50 / 47 | 42.00% | 38.30% | 0.1752 | 8.236 |
| Jump 50 Index | Dos años | 56 / 30 | 26.79% | 46.67% | 0.4929 | 14.786 |
| Jump 75 Index | Dos años | 55 / 31 | 29.09% | 38.71% | 0.1584 | 4.909 |
| LNKUSD | Dos años | 20 / 12 | 25.00% | 25.00% | -0.1480 | -1.776 |
| LTCUSD | Dos años | 11 / 6 | 27.27% | 16.67% | -0.4843 | -2.906 |
| MLNUSD | Parcial desde 2025-01-23 | 8 / 4 | 25.00% | 0.00% | -1.0000 | -4.000 |
| Multi Step 2 Index | Dos años | 42 / 32 | 40.48% | 37.50% | 0.0890 | 2.847 |
| Multi Step 3 Index | Parcial desde 2025-01-31 | 20 / 17 | 25.00% | 11.76% | -0.6038 | -10.264 |
| Multi Step 4 Index | Dos años | 39 / 35 | 23.08% | 22.86% | -0.3277 | -11.469 |
| NEOUSD | Dos años | 3 / 0 | 33.33% | — | — | 0.000 |
| NERUSD | Parcial desde 2024-12-13 | 16 / 7 | 18.75% | 28.57% | -0.2565 | -1.796 |
| NZDCAD | Dos años | 5 / 3 | 20.00% | 33.33% | 0.1667 | 0.500 |
| NZDCHF | Dos años | 7 / 8 | 28.57% | 25.00% | -0.2194 | -1.755 |
| NZDJPY | Dos años | 8 / 6 | 37.50% | 33.33% | -0.3282 | -1.969 |
| NZDSGD | Dos años | 11 / 4 | 0.00% | 0.00% | -1.0000 | -4.000 |
| NZDUSD | Dos años | 8 / 5 | 37.50% | 40.00% | 0.1095 | 0.547 |
| NZDUSDmicro | Dos años | 8 / 5 | 37.50% | 40.00% | 0.1095 | 0.547 |
| SANUSD | Parcial desde 2024-12-13 | 14 / 5 | 21.43% | 40.00% | 0.3703 | 1.852 |
| SGDJPY | Dos años | 11 / 5 | 9.09% | 40.00% | -0.1547 | -0.774 |
| SHBUSD | Dos años | 4 / 0 | 0.00% | — | — | 0.000 |
| SOLUSD | Dos años | 10 / 5 | 20.00% | 20.00% | -0.3500 | -1.750 |
| SPXS.US | Dos años | 0 / 0 | — | — | — | 0.000 |
| Skew Step Index 4 Down | Dos años | 38 / 25 | 21.05% | 24.00% | -0.2348 | -5.870 |
| Skew Step Index 4 Up | Dos años | 51 / 25 | 35.29% | 44.00% | 0.4286 | 10.715 |
| Skew Step Index 5 Down | Dos años | 42 / 27 | 30.95% | 29.63% | -0.1782 | -4.812 |
| Skew Step Index 5 Up | Dos años | 46 / 27 | 23.91% | 18.52% | -0.4438 | -11.983 |
| Spot Up - Volatility Up Index | Parcial desde 2025-09-12 | 27 / 14 | 44.44% | 57.14% | 0.7471 | 10.460 |
| Step Index | Dos años | 42 / 37 | 38.10% | 40.54% | 0.1631 | 6.034 |
| Step Index 100 | No disponible | — | — | — | — | — |
| Step Index 200 | Dos años | 50 / 34 | 30.00% | 26.47% | -0.1452 | -4.936 |
| Step Index 300 | Parcial desde 2024-11-07 | 36 / 29 | 41.67% | 34.48% | 0.0948 | 2.750 |
| Step Index 400 | Parcial desde 2024-11-07 | 51 / 29 | 33.33% | 37.93% | 0.1405 | 4.074 |
| Step Index 500 | Dos años | 46 / 30 | 26.09% | 36.67% | 0.1706 | 5.117 |
| TRUUSD | Parcial desde 2025-01-23 | 6 / 0 | 16.67% | — | — | 0.000 |
| TRXUSD | Dos años | 10 / 6 | 0.00% | 16.67% | -0.4748 | -2.849 |
| UK Brent Oil | Dos años | 10 / 1 | 20.00% | 0.00% | -1.0000 | -1.000 |
| UNIUSD | Dos años | 12 / 8 | 25.00% | 25.00% | -0.1562 | -1.250 |
| US Oil | Dos años | 15 / 6 | 26.67% | 33.33% | -0.1200 | -0.720 |
| US SP 500 | Dos años | 15 / 9 | 20.00% | 33.33% | -0.1948 | -1.753 |
| US Tech 100 | Dos años | 13 / 5 | 38.46% | 20.00% | -0.3003 | -1.501 |
| USDCAD | Dos años | 9 / 1 | 22.22% | 0.00% | -1.0000 | -1.000 |
| USDCADmicro | Dos años | 9 / 1 | 22.22% | 0.00% | -1.0000 | -1.000 |
| USDCHF | Dos años | 6 / 6 | 33.33% | 16.67% | -0.4167 | -2.500 |
| USDCHFmicro | Dos años | 6 / 6 | 33.33% | 16.67% | -0.4167 | -2.500 |
| USDCNH | Dos años | 6 / 7 | 16.67% | 28.57% | -0.2404 | -1.682 |
| USDHKD | Dos años | 12 / 3 | 0.00% | 33.33% | -0.2914 | -0.874 |
| USDJPY | Dos años | 13 / 7 | 46.15% | 42.86% | 0.2130 | 1.491 |
| USDJPYmicro | Dos años | 13 / 7 | 46.15% | 42.86% | 0.2130 | 1.491 |
| USDMXN | Dos años | 9 / 3 | 22.22% | 0.00% | -1.0000 | -3.000 |
| USDNOK | Dos años | 6 / 4 | 0.00% | 25.00% | -0.1595 | -0.638 |
| USDPLN | Dos años | 4 / 0 | 25.00% | — | — | 0.000 |
| USDSEK | Dos años | 9 / 6 | 33.33% | 33.33% | -0.0788 | -0.473 |
| USDSGD | Dos años | 14 / 2 | 7.14% | 0.00% | -1.0000 | -2.000 |
| USDZAR | Dos años | 7 / 5 | 57.14% | 40.00% | 0.1039 | 0.519 |
| Vol over Boom 400 | Dos años | 12 / 18 | 50.00% | 44.44% | 0.3814 | 6.865 |
| Vol over Boom 550 | Dos años | 20 / 12 | 30.00% | 25.00% | -0.1619 | -1.943 |
| Vol over Boom 750 | Dos años | 21 / 16 | 38.10% | 37.50% | 0.0255 | 0.409 |
| Vol over Crash 400 | Dos años | 24 / 22 | 33.33% | 31.82% | -0.1051 | -2.313 |
| Vol over Crash 550 | Dos años | 21 / 16 | 57.14% | 56.25% | 0.6579 | 10.526 |
| Vol over Crash 750 | Dos años | 16 / 12 | 31.25% | 16.67% | -0.4548 | -5.458 |
| VolSwitch High Vol Index | Parcial desde 2025-07-03 | 32 / 23 | 37.50% | 43.48% | 0.2325 | 5.348 |
| VolSwitch Low Vol Index | Parcial desde 2025-07-03 | 20 / 25 | 20.00% | 24.00% | -0.2645 | -6.611 |
| VolSwitch Medium Vol Index | Parcial desde 2025-07-03 | 21 / 15 | 33.33% | 6.67% | -0.7667 | -11.500 |
| Volatility 10 (1s) Index | Dos años | 37 / 28 | 32.43% | 28.57% | -0.0351 | -0.983 |
| Volatility 10 Index | Dos años | 43 / 33 | 25.58% | 24.24% | -0.2655 | -8.762 |
| Volatility 100 (1s) Index | Dos años | 36 / 30 | 41.67% | 40.00% | 0.1819 | 5.457 |
| Volatility 100 Index | Dos años | 49 / 33 | 24.49% | 24.24% | -0.2156 | -7.114 |
| Volatility 15 (1s) Index | Parcial desde 2025-01-31 | 27 / 25 | 22.22% | 24.00% | -0.4081 | -10.202 |
| Volatility 15 Index | Parcial desde 2026-02-13 | 13 / 8 | 38.46% | 25.00% | -0.4971 | -3.977 |
| Volatility 150 (1s) Index | Dos años | 41 / 27 | 39.02% | 25.93% | -0.3542 | -9.563 |
| Volatility 25 (1s) Index | Dos años | 39 / 32 | 25.64% | 21.88% | -0.4406 | -14.099 |
| Volatility 25 Index | Dos años | 53 / 39 | 30.19% | 30.77% | -0.1164 | -4.540 |
| Volatility 250 (1s) Index | Dos años | 40 / 32 | 17.50% | 28.12% | -0.0823 | -2.634 |
| Volatility 30 (1s) Index | Parcial desde 2025-01-31 | 32 / 19 | 43.75% | 42.11% | 0.0672 | 1.277 |
| Volatility 30 Index | Parcial desde 2026-02-13 | 16 / 19 | 50.00% | 52.63% | 0.7016 | 13.331 |
| Volatility 5 (1s) Index | Parcial desde 2025-12-26 | 16 / 13 | 25.00% | 23.08% | -0.4211 | -5.474 |
| Volatility 5 Index | Parcial desde 2025-12-26 | 15 / 17 | 46.67% | 47.06% | 0.3923 | 6.669 |
| Volatility 50 (1s) Index | Dos años | 39 / 32 | 30.77% | 21.88% | -0.3280 | -10.494 |
| Volatility 50 Index | Dos años | 35 / 18 | 40.00% | 11.11% | -0.6176 | -11.116 |
| Volatility 75 (1s) Index | Dos años | 33 / 24 | 42.42% | 45.83% | 0.4725 | 11.340 |
| Volatility 75 Index | Dos años | 42 / 31 | 35.71% | 25.81% | -0.2258 | -7.001 |
| Volatility 90 (1s) Index | Parcial desde 2025-01-31 | 35 / 29 | 31.43% | 20.69% | -0.4316 | -12.515 |
| Volatility 90 Index | Parcial desde 2026-02-13 | 9 / 6 | 33.33% | 33.33% | -0.1257 | -0.754 |
| Wall Street 30 | Dos años | 15 / 8 | 26.67% | 25.00% | -0.2016 | -1.613 |
| XAGUSD | Dos años | 9 / 6 | 33.33% | 66.67% | 0.9540 | 5.724 |
| XAGUSDmicro | Dos años | 9 / 6 | 33.33% | 66.67% | 0.9540 | 5.724 |
| XAUUSD | Dos años | 11 / 4 | 54.55% | 75.00% | 0.8792 | 3.517 |
| XAUUSDmicro | Parcial desde 2025-06-22 | 5 / 1 | 40.00% | 0.00% | -1.0000 | -1.000 |
| XLMUSD | Dos años | 13 / 8 | 15.38% | 37.50% | -0.0796 | -0.637 |
| XMRUSD | Dos años | 9 / 9 | 22.22% | 22.22% | -0.3028 | -2.725 |
| XRPUSD | Dos años | 12 / 9 | 16.67% | 55.56% | 0.6334 | 5.701 |
| XTZUSD | Dos años | 6 / 1 | 16.67% | 0.00% | -1.0000 | -1.000 |
| ZECUSD | Dos años | 7 / 3 | 0.00% | 33.33% | 0.0773 | 0.232 |

## Método y límites

Se comparan el código previo conservado desde HEAD y la versión msnr-v2.1-persistent-retest. Ambos observan exclusivamente velas cerradas. La aceleración memoriza prefijos inmutables y descarta horarios sin patrones posibles; se verifica contra el detector sin acelerar.
Se abre en la siguiente vela M15 con spread histórico cuando existe; BUY entra a ask, SELL sale a ask. Se mantiene el SL estructural, se recalculan los objetivos desde el precio de entrada y se verifica el contexto de ejecución de v2.1. TP1=2R y distribución 50/50; la corredora pasa a BE con 1,5 spreads de buffer. En ambigüedad intravela se prioriza el stop. Una operación activa por instrumento.
Se aplica a ambas versiones el límite común del simulador de 200 velas M15 (50 horas de cotización). Las salidas TIMEOUT se valoran a mercado; las abiertas al final del histórico quedan censuradas y no cuentan en WinRate. metrics.json incluye el resultado sólo de las operaciones resueltas sin TIMEOUT.
El simulador vuelve a evaluar en el cierre M15 posterior al cierre de una posición; el worker en vivo puede reevaluar antes. Es una comparación controlada bajo un modelo común de ejecución, no una reproducción de cada decisión del broker.
Antes de abrir, se rechaza un stop ya cruzado por Bid en BUY o Ask en SELL. Esta validación utiliza el lado de cotización correspondiente al cierre de la posición, conforme a las [reglas de MetaTrader](https://www.mql5.com/en/articles/2555). Se reejecutaron 8 instrumentos afectados; sus resultados anteriores quedan archivados para trazabilidad.
No se simulan ticks, latencia, slippage, comisión, swaps, lote mínimo, redondeo, validación de distancia mínima de stops del broker ni restricciones de cartera. La sensibilidad de costos en metrics.json resta 0,05R/0,10R a las operaciones realizadas; no es una reoptimización ni un replay de decisiones diferente.
Corrección común del simulador: 0 operaciones con TP1 y TP2 exactamente iguales se cierran juntas en TP2, antes de mover BE. Sólo corrige R/etiqueta, sin alterar entradas, fecha de salida, WinRate ni disponibilidad para otra operación.
El grupo que excluye TIMEOUT describe un subconjunto de las operaciones del mismo replay: no es un nuevo replay con posiciones mantenidas indefinidamente, y no recalcula las entradas posteriores a esas salidas.
No se modificaron parámetros del bot en vivo, su selección de activos ni modelos IA; no se enviaron órdenes. Los históricos parciales no se extrapolan a dos años. La selección de mejores activos después de ver este resultado requeriría una validación posterior independiente.

Archivos: `per_symbol.csv`, `trades.csv`, `quarterly.csv`, `metrics.json`, `history_manifest.json` y snapshots de velas con hash SHA-256.