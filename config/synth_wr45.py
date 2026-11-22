"""Poda por acierto <= 45 % en sintéticos (replay fiel). DAEMONBLACKFX_SYNTH_WR45_PRUNE=0 la desactiva."""
import os as _os

SYNTH_WR45_PRUNE_ENABLED = _os.getenv("DAEMONBLACKFX_SYNTH_WR45_PRUNE", "1").strip().lower() not in ("0", "false", "off")
# Poda por spread real (23-oct-2026): la mediana del spread de ticks es ~4,3× el campo spread de las velas M15 y
# supera siempre el tope spread/SL 2 % del motor (0 operaciones posibles en ICT y MSNR).
# DAEMONBLACKFX_REAL_SPREAD_PRUNE=0 la desactiva.
REAL_SPREAD_PRUNE_ENABLED = _os.getenv("DAEMONBLACKFX_REAL_SPREAD_PRUNE", "1").strip().lower() not in ("0", "false", "off")
REAL_SPREAD_PRUNED = ("VolSwitch High Vol Index",) if REAL_SPREAD_PRUNE_ENABLED else ()
_ICT_5Y_AUDIT = _os.getenv("DAEMONBLACKFX_ICT_5Y_AUDIT", "1").strip().lower() not in ("0", "false", "off")
if _ICT_5Y_AUDIT:
    # 26-oct-2026: Replay fiel 5 años con 6 mejoras rescata Boom 300 (52.49%) y Vol over Boom 550 (50.00%).
    # 20-nov-2026: Poda solicitada por operador: Crash 300, Crash 600, Vol 15, Vol 25, Vol 50 (1s). Jump 10 rehabilitado como activo. High Frequency Vol 50 Index rehabilitado activo en MultiStrategia.
    ICT_WR45_PRUNED = (("Volatility 90 (1s) Index", "Crash 300 Index", "Crash 600 Index", "Volatility 15 Index", "Volatility 25 Index", "Volatility 50 (1s) Index")
                       if SYNTH_WR45_PRUNE_ENABLED else ()) + REAL_SPREAD_PRUNED
else:
    ICT_WR45_PRUNED = (("Boom 300 Index", "Vol over Boom 550", "Volatility 90 (1s) Index", "Crash 300 Index", "Crash 600 Index", "Volatility 15 Index", "Volatility 25 Index", "Volatility 50 (1s) Index")
                       if SYNTH_WR45_PRUNE_ENABLED else ()) + REAL_SPREAD_PRUNED
MSNR_WR45_PRUNED = (("Step Index", "Volatility 100 Index", "Jump 50 Index", "Crash 300 Index", "Crash 600 Index",
                     "Boom 1000 Index", "Volatility 90 (1s) Index", "Volatility 25 Index", "Volatility 15 Index",
                     "Volatility 50 (1s) Index", "Boom 900 Index") if SYNTH_WR45_PRUNE_ENABLED else ()) + REAL_SPREAD_PRUNED
