"""Paquete de riesgo de referencia: dimensionado, gestión monetaria y límites.

Contenido:
- `position_sizing`: deduce el volumen a partir de la distancia al stop.
- `money_management`: valida capital y calcula estadisticas de drawdown.
- `risk_manager`: aplica los limites de cuenta sobre los dos anteriores.

ESTADO — NO ES EL RIESGO DE PRODUCCION. El motor en vivo
(`strategy.execution.live_trading_engine`) implementa su propio dimensionado
y sus propios topes, incluida la verificacion del riesgo real despues del
fill. Este paquete solo lo consumen los tests.

DUPLICIDAD: existe ademas el paquete `risk/` en la raiz, con
`risk.money_manager`, tambien sin consumidores en produccion. Son
implementaciones distintas de ideas parecidas; no confundirlas.
"""
