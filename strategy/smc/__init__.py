"""Paquete de analisis Smart Money Concepts (SMC).

Mapa del paquete y ORDEN REAL en que se encadenan los modulos dentro de
`strategy.execution.trade_pipeline.run_pipeline`:

  1. `swings`            -> marca pivotes (swing_high / swing_low)
  2. `market_structure`  -> clasifica HH/HL/LH/LL y deduce la tendencia
  3. `liquidity`         -> localiza zonas de maximos/minimos iguales
  4. `liquidity_sweeps`  -> detecta el barrido de esas zonas
  5. `choch_bos`         -> detecta CHOCH (giro) y BOS (continuacion)
  6. `order_blocks`      -> deriva la zona de entrada de la ruptura
  7. `premium_discount`  -> exige comprar barato / vender caro
  8. `entry_confirmation`-> espera el retest del OB
  9. `confirmation_engine` -> valida la vela y calcula score y grado
 10. `risk_reward`       -> proyecta Stop Loss y Take Profit

Confluencias opcionales, que suman o restan puntos pero no crean senales:
- `chart_patterns`: patrones chartistas y conflicto entre ellos. Un patron
  contrario mas fuerte puede BLOQUEAR la entrada.
- `harmonic_patterns`: Gartley, Bat, Butterfly y Crab.
- `h1_doji_extremes`: doji H1 en extremos de rango.
- La divergencia RSI vive dentro de `confirmation_engine`.

Modulos SIN USO en produccion, conservados como referencia historica:
- `ob_quality`: scoring de OB anterior al de `confirmation_engine`. Sus
  umbrales de grado NO coinciden con los vigentes.
- `micro_confirmation`: confirmacion simplificada previa al motor M5.
- `setup_detector` y `trade_simulator`: solo los usan los tests. En vivo, la
  deteccion la hace `trade_pipeline` y el resultado lo marca el broker.

Este `__init__` esta intencionadamente vacio de codigo: cada modulo se importa
por su ruta completa.
"""
