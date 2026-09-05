"""Adaptadores de broker (MetaTrader 5).

Aisla todo el contacto con el terminal MT5 para que el resto del proyecto
trabaje con estructuras propias en lugar de con la API nativa.

Modulos vivos:
    - `mt5_connector` / `mt5_connection`: sesion con el terminal.
    - `mt5_data`: lectura de velas y de informacion de simbolos.
    - `mt5_execution`: envio, modificacion y cierre de ordenes.
    - `mt5_trade_executor`: fachada de ejecucion usada por el motor.
    - `symbol_discovery`: catalogo de instrumentos operables.

Auxiliares sin consumidores: `symbols.py` (diagnostico manual) y
`mt5_execution.back.py` (copia de seguridad de una version anterior).
"""
