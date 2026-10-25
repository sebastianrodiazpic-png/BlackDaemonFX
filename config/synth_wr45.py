"""Poda por acierto <= 45 % en sintéticos (replay fiel). DAEMONBLACKFX_SYNTH_WR45_PRUNE=0 la desactiva."""
import os as _os

SYNTH_WR45_PRUNE_ENABLED = _os.getenv("DAEMONBLACKFX_SYNTH_WR45_PRUNE", "1").strip().lower() not in ("0", "false", "off")
# Poda por spread real (23-oct-2026): la mediana del spread de ticks es ~4,3× el campo spread de las velas M15 y
# supera siempre el tope spread/SL 2 % del motor (0 operaciones posibles en ICT y MSNR).
# DAEMONBLACKFX_REAL_SPREAD_PRUNE=0 la desactiva.
REAL_SPREAD_PRUNE_ENABLED = _os.getenv("DAEMONBLACKFX_REAL_SPREAD_PRUNE", "1").strip().lower() not in ("0", "false", "off")
REAL_SPREAD_PRUNED = ("VolSwitch High Vol Index",) if REAL_SPREAD_PRUNE_ENABLED else ()
ICT_WR45_PRUNED = (("Boom 300 Index", "Crash 1000 Index", "Vol over Boom 550", "Volatility 90 (1s) Index")
                   if SYNTH_WR45_PRUNE_ENABLED else ()) + REAL_SPREAD_PRUNED
MSNR_WR45_PRUNED = (("Step Index", "Volatility 100 Index", "Jump 50 Index", "Crash 300 Index", "Crash 600 Index",
                     "Boom 1000 Index", "Volatility 90 (1s) Index") if SYNTH_WR45_PRUNE_ENABLED else ()) + REAL_SPREAD_PRUNED
