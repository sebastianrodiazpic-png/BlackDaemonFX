"""Política única de instrumentos de /Instruments para ICT y Malaysian SNR (26-oct-2026).

Fuente de verdad compartida por los workers (STEP, JUMP, VOLATILITY_1-2, BOOM, CRASH, FOREX_1-2, ICT y
MALAYSIAN_SNR), el motor (listas permitidas por familia) y el dashboard (/Instruments, pestañas Sintéticos,
Forex, ICT y Malaysian SNR).

- ACTIVO: el instrumento lo puede operar su worker; queda marcado en /Instruments y la selección persistida
  decide en cada ciclo si se escanea (desmarcarlo lo apaga sin reiniciar).
- PODA PREVENTIVA: aparece desmarcado (OFF) por defecto con su motivo de poda cuantitativa. Con
  DAEMONBLACKFX_ALLOW_SELECTIVE_ACTIVATION=1 (activo por defecto), el operador puede activar de manera
  selectiva cualquier instrumento desde /Instruments (con confirmación explícita).

Variables de entorno (se leen al importar):
- DAEMONBLACKFX_ICT_5Y_AUDIT=0 vuelve a las listas anteriores a la auditoría multianual de hasta 5 años.
- DAEMONBLACKFX_ALLOW_SELECTIVE_ACTIVATION=0 bloquea la activación manual selectiva de instrumentos podados.
- DAEMONBLACKFX_CONSOLIDATE_ACTIVE_PRUNED_WORKERS=0 vuelve al reparto en 4 shards de Volatility y Forex.
- DAEMONBLACKFX_ICT_UNPRUNE_SYNTHETICS=0 vuelve a las listas de sintéticos anteriores a la liberación.
- DAEMONBLACKFX_SYNTH_WR45_PRUNE=0 desactiva la poda por acierto <= 45 % (config/synth_wr45.py).
- DAEMONBLACKFX_ICT_FOREX_50_RESCUE=0 vuelve a podar los 13 cruces Forex con WR >= 50 % en /Strategy-bases ICT (11-nov-2026).
- DAEMONBLACKFX_MSNR_SYNTHETICS_ONLY=0 deja de podar los mercados reales en Malaysian SNR (como el motor).
"""
from __future__ import annotations

import os

from config.synth_wr45 import ICT_WR45_PRUNED, MSNR_WR45_PRUNED, REAL_SPREAD_PRUNED
from strategy.trend_pullback.config import TREND_PULLBACK_51_SYMBOLS

PREVENTIVE_PRUNE_LABEL = "PODA PREVENTIVA"
ICT_SELECTION_PROFILES = ("SYNTHETICS", "FOREX", "ICT")
# Pestañas de /Instruments gobernadas por esta política (Sintéticos, Forex, Materias Primas/Cripto, Índices Bursátiles).
# Malaysian SNR, Forex SNR, Commodities SNR y Trend Pullback retirados al estar cubiertos internamente o eliminados.
POLICY_SELECTION_PROFILES = (*ICT_SELECTION_PROFILES, "INDICESB_SNR")

_UNPRUNE_SYNTHETICS = os.getenv("DAEMONBLACKFX_ICT_UNPRUNE_SYNTHETICS", "1").strip().lower() not in ("0", "false", "off")
ICT_5Y_AUDIT_ENABLED = os.getenv("DAEMONBLACKFX_ICT_5Y_AUDIT", "1").strip().lower() not in ("0", "false", "off")
ALLOW_SELECTIVE_INSTRUMENT_ACTIVATION = (
    os.getenv("DAEMONBLACKFX_ALLOW_SELECTIVE_ACTIVATION", "1").strip().lower() not in ("0", "false", "off")
)
CONSOLIDATE_ACTIVE_PRUNED_WORKERS = (
    os.getenv("DAEMONBLACKFX_CONSOLIDATE_ACTIVE_PRUNED_WORKERS", "1").strip().lower() not in ("0", "false", "off")
)
PRUNE_HF_VOL_ENABLED = (
    os.getenv("DAEMONBLACKFX_PRUNE_HF_VOL", "1").strip().lower() not in ("0", "false", "off")
)
HF_VOL_SYMBOLS = (
    "High Frequency Vol 10 Index",
    "High Frequency Vol 25 Index",
    "High Frequency Vol 50 Index",
    "High Frequency Vol 75 Index",
    "High Frequency Vol 100 Index",
)

# Rescatados de Fase 1 tras replay fiel multianual 5 años con las 6 mejoras
# (orden limitada virtual + tope spread/SL <= 2.0 % / 2.5 % + filtro ADX + asimetría direccional + piso SL ATR):
# Todos los instrumentos con WR > 47% en el replay fiel de 5 años.
ICT_5Y_RESCUED_SYNTHETICS = (
    (
        "Jump 10 Index",
        "Jump 25 Index",
        "Jump 50 Index",
        "Jump 75 Index",
        "Jump 100 Index",
        "Boom 300 Index",
        "Boom 500 Index",
        "Boom 600 Index",
        "Boom 900 Index",
        "Boom 1000 Index",
        "Crash 500 Index",
        "Crash 900 Index",
        "Crash 1000 Index",
        "Volatility 5 Index",
        "Volatility 10 Index",
        "Volatility 50 Index",
        "Volatility 75 Index",
        "Volatility 90 Index",
        "Volatility 100 Index",
        "Volatility 5 (1s) Index",
        "Volatility 10 (1s) Index",
        "Volatility 15 (1s) Index",
        "Volatility 25 (1s) Index",
        "Volatility 30 (1s) Index",
        "Volatility 75 (1s) Index",
        "Volatility 90 (1s) Index",
        "Volatility 100 (1s) Index",
        "Volatility 150 (1s) Index",
        "Volatility 250 (1s) Index",
        "Step Index 200",
        "Step Index 400",
        "Step Index 500",
        "Step Index",
        "Step Index 300",
        "Step Index 1000",
        "Step Index 1500",
        "Step Index 2000",
        "High Frequency Vol 10 Index",
        "High Frequency Vol 25 Index",
        "High Frequency Vol 50 Index",
        "High Frequency Vol 75 Index",
        "High Frequency Vol 100 Index",
        "Ladder Volatility Down Index",
        "Ladder Volatility Up Index",
        "VolSwitch Low Vol Index",
        "VolSwitch Medium Vol Index",
        "Wall Street 30",
        "BTCUSD",
        "BTCUSDmicro",
        "microBTCUSD",
        "UK Brent Oil",
        "Germany 40",
    )
    if (ICT_5Y_AUDIT_ENABLED and _UNPRUNE_SYNTHETICS)
    else ()
)

# Poda multianual 5 años en sintéticos: activos con WR <= 50.0 % o R neto <= 0, o podados explícitamente por el operador
ICT_5Y_SYNTH_PRUNED = (
    "Crash 300 Index",
    "Crash 600 Index",
    "Volatility 15 Index",
    "Volatility 25 Index",
    "Volatility 50 (1s) Index",
    "Vol over Boom 550",
    "Vol over Crash 550",
    "Volatility Boom 400 Index",
    "Volatility Boom 550 Index",
    "Volatility Boom 750 Index",
    "Volatility Crash 400 Index",
    "Volatility Crash 550 Index",
    "Volatility Crash 750 Index",
    "VolSwitch High Vol Index",
)

ICT_5Y_MARKETS_PRUNED = (
    "US SP 500",
    "XAUEUR", "XAUEURmicro", "microXAUEUR",
    "XAGUSD", "XAGUSDmicro", "microXAGUSD",
    "ETHUSD", "ETHUSDmicro", "microETHUSD", "ETHmicro",
    "XRPUSD",
)

# Fase 1 (18-oct-2026) + actualización 5 años con 6 mejoras (26-oct-2026):
_BASE_PHASE1_EXCLUDED = ("Step Index", "Jump 25 Index", "Volatility 25 Index", "Wall Street 30")
ICT_PHASE1_EXCLUDED = (
    tuple(s for s in _BASE_PHASE1_EXCLUDED if s not in set(ICT_5Y_RESCUED_SYNTHETICS)) + ICT_5Y_MARKETS_PRUNED
)


def _keep(*symbols):
    blocked = (set(ICT_WR45_PRUNED) | set(ICT_PHASE1_EXCLUDED) | set(ICT_5Y_SYNTH_PRUNED) | set(ICT_5Y_MARKETS_PRUNED)) - set(ICT_5Y_RESCUED_SYNTHETICS)
    if PRUNE_HF_VOL_ENABLED:
        blocked |= set(HF_VOL_SYMBOLS)
    if not _UNPRUNE_SYNTHETICS:
        blocked |= {
            "Boom 500 Index",
            "Boom 600 Index",
            "Crash 300 Index",
            "Step Index 200",
            "Volatility 10 Index",
            "Volatility 100 Index",
            "Volatility 100 (1s) Index",
        }
    return tuple(s for s in symbols if s not in blocked)


# Sintéticos ICT por familia de worker (replay fiel 5 años con 6 mejoras y WR > 47 %):
# 34 activos con WR > 47% (+500.1 R acumulados en los 29 con R > 0, WR = 53.43%).
ICT_SYNTHETIC_FAMILIES = {
    "STEP": _keep("Step Index 200", "Step Index 400", "Step Index 500"),
    "STEP_2": _keep("Step Index", "Step Index 300", "Step Index 1000", "Step Index 1500", "Step Index 2000"),
    "JUMP": _keep("Jump 50 Index", "Jump 75 Index", "Jump 10 Index", "Jump 25 Index", "Jump 100 Index"),
    "VOLATILITY": _keep(
        "Volatility 25 Index", "VolSwitch High Vol Index", "Volatility 90 Index", "Volatility 100 (1s) Index",
        "Volatility 10 Index", "Volatility 15 Index", "Volatility 5 Index", "Volatility 250 (1s) Index",
        "High Frequency Vol 100 Index", "Volatility 75 (1s) Index", "Volatility 50 (1s) Index",
        "Volatility 50 Index", "Volatility 150 (1s) Index", "Volatility 75 Index",
        "Vol over Boom 550", "Vol over Crash 550", "Volatility Boom 550 Index", "Volatility Crash 550 Index", "Volatility 100 Index",
        "Volatility 90 (1s) Index", "High Frequency Vol 50 Index",
        "High Frequency Vol 10 Index", "High Frequency Vol 25 Index", "High Frequency Vol 75 Index",
        "Volatility 10 (1s) Index", "Volatility 15 (1s) Index", "Volatility 25 (1s) Index",
        "Volatility 30 (1s) Index", "Volatility 5 (1s) Index",
        "Ladder Volatility Down Index", "Ladder Volatility Up Index",
        "VolSwitch Low Vol Index", "VolSwitch Medium Vol Index",
    ),
    "BOOM": _keep(
        "Boom 1000 Index", "Boom 300 Index", "Boom 500 Index", "Boom 600 Index", "Boom 900 Index",
        "Volatility Boom 400 Index", "Volatility Boom 750 Index",
    ),
    "CRASH": _keep(
        "Crash 1000 Index", "Crash 300 Index", "Crash 500 Index", "Crash 600 Index", "Crash 900 Index",
        "Volatility Crash 400 Index", "Volatility Crash 550 Index", "Volatility Crash 750 Index",
    ),
}

# Universos de Volatility separados en Worker Activo (VOLATILITY_1) y Worker Podado OFF (VOLATILITY_2).
ICT_VOLATILITY_ACTIVE_SYMBOLS = ICT_SYNTHETIC_FAMILIES["VOLATILITY"]
ICT_VOLATILITY_PRUNED_SYMBOLS = ()

# Forex: los 8 pares con WR > 50.0 % y R neto > 0 en el replay fiel auditado de 212 pares operados por FOREX_1;
# el resto queda en FOREX_2 (desactivado por defecto, activable de forma selectiva desde /Instruments).
# 11-nov-2026: cruces Forex con acierto >= 50 % en /Strategy-bases (pestaña ICT) liberados de la poda.
# DAEMONBLACKFX_ICT_FOREX_50_RESCUE=0 los devuelve a FOREX_2 (podados OFF).
ICT_FOREX_50_RESCUE_ENABLED = (
    os.getenv("DAEMONBLACKFX_ICT_FOREX_50_RESCUE", "0").strip().lower() in ("1", "true", "on")
)
ICT_FOREX_50_RESCUED_BASES = (
    "AUDCHF", "AUDJPY", "AUDNZD", "CADJPY", "CHFJPY", "EURAUD", "EURCAD",
    "EURGBP", "EURNZD", "GBPAUD", "GBPCAD", "GBPCHF", "GBPNZD",
) if ICT_FOREX_50_RESCUE_ENABLED else ()
ICT_FOREX_50_RESCUED_NO_MICRO = ("CHFJPY", "GBPAUD", "GBPCAD", "GBPNZD") if ICT_FOREX_50_RESCUE_ENABLED else ()
ICT_FOREX_ACTIVE_BASES = (
    "EURUSD", "GBPUSD", "USDCAD", "USDCHF", "GBPJPY", "EURJPY", "AUDUSD",
)
if ICT_FOREX_50_RESCUE_ENABLED:
    ICT_FOREX_ACTIVE_BASES = tuple(ICT_FOREX_ACTIVE_BASES) + tuple(
        b for b in ICT_FOREX_50_RESCUED_BASES if b not in set(ICT_FOREX_ACTIVE_BASES)
    )
ICT_FOREX_ACTIVE = tuple(ICT_FOREX_ACTIVE_BASES) + tuple(
    f"{base}micro" for base in ICT_FOREX_ACTIVE_BASES
)

ICT_FOREX_ALL_BASES = (
    "GBPUSD", "USDCHF", "EURJPY", "CADCHF", "NZDUSD", "EURGBP", "GBPJPY", "GBPCHF", "AUDJPY",
    "EURAUD", "EURUSD", "EURCHF", "USDJPY", "AUDCAD", "AUDNZD", "AUDUSD", "USDCAD", "CHFJPY",
    "GBPCAD", "GBPAUD", "EURCAD", "AUDCHF", "CADJPY", "EURNZD", "GBPNZD", "AUDSGD",
    "NZDCAD", "NZDCHF", "NZDJPY", "NZDSGD",
    "USDCNH", "USDHKD", "USDMXN", "USDNOK", "USDPLN", "USDSEK", "USDSGD", "USDZAR",
    "EURHKD", "EURMXN", "EURNOK", "EURPLN", "EURSEK", "EURSGD", "EURZAR",
    "GBPNOK", "GBPSEK", "GBPSGD",
)
ICT_FOREX_PRUNED_BASES = tuple(b for b in ICT_FOREX_ALL_BASES if b not in set(ICT_FOREX_ACTIVE_BASES))
ICT_FOREX_PRUNED_SYMBOLS = tuple(
    sym for base in ICT_FOREX_ALL_BASES for sym in (base, f"{base}micro") if sym not in set(ICT_FOREX_ACTIVE)
)

# Worker ICT (metales, índices y commodities). En la auditoría de 5 años con 6 mejoras quedan activos:
# US Tech 100 (WR = 75.00 %, +16.0 R), Wall Street 30 (WR = 56.76 %, +4.5 R), XAUUSD (WR = 54.55 %, +2.0 R) y US Oil (WR = 53.33 %, +54.1 R mercado).
# US SP 500 (-3.0 R, WR = 36.36 %) pasa a PODA PREVENTIVA junto con XAGUSD y Cripto.
ICT_MARKETS_ACTIVE = _keep(
    "XAUUSD", "XAUUSDmicro", "microXAUUSD",
    "BTCUSD", "BTCUSDmicro", "microBTCUSD",
    "US Oil", "UK Brent Oil",
    "Wall Street 30", "US Tech 100", "Germany 40",
)


# Malaysian SNR: solo sintéticos (replay fiel 2 años con tope spread/SL 2 %; mercados reales negativos en
# ambos años: -0.157 / -0.079 R/trade) y sin los de acierto <= 45 % en su replay.
MSNR_SYNTHETICS_ONLY = os.getenv("DAEMONBLACKFX_MSNR_SYNTHETICS_ONLY", "1").strip().lower() not in ("0", "false", "off")
MSNR_SYNTHETIC_UNIVERSE = (
    "Boom 1000 Index", "Boom 300 Index", "Boom 500 Index", "Boom 600 Index", "Boom 900 Index",
    "Volatility Boom 400 Index", "Volatility Boom 750 Index",
    "Crash 1000 Index", "Crash 300 Index", "Crash 500 Index", "Crash 600 Index", "Crash 900 Index",
    "Volatility Crash 400 Index", "Volatility Crash 550 Index", "Volatility Crash 750 Index",
    "High Frequency Vol 100 Index", "High Frequency Vol 50 Index",
    "Jump 10 Index", "Jump 25 Index", "Jump 50 Index", "Jump 75 Index", "Jump 100 Index",
    "Step Index", "Step Index 200", "Step Index 300", "Step Index 400", "Step Index 500",
    "Vol over Boom 550", "Vol over Crash 550", "VolSwitch High Vol Index",
    "Volatility 10 Index", "Volatility 100 (1s) Index", "Volatility 100 Index", "Volatility 15 Index",
    "Volatility 150 (1s) Index", "Volatility 25 Index", "Volatility 250 (1s) Index", "Volatility 5 Index",
    "Volatility 50 (1s) Index", "Volatility 50 Index", "Volatility 75 (1s) Index", "Volatility 75 Index",
    "Volatility 90 (1s) Index", "Volatility 90 Index",
    "Volatility 10 (1s) Index", "Volatility 15 (1s) Index", "Volatility 25 (1s) Index",
    "Volatility 30 (1s) Index", "Volatility 5 (1s) Index",
)
MSNR_ACTIVE = tuple(s for s in MSNR_SYNTHETIC_UNIVERSE if s not in set(MSNR_WR45_PRUNED))
# Prueba demo en Malaysian SNR (20-oct-2026): sintéticos nuevos con evidencia robusta en el replay de 2 años.
# DEX 1500 UP Index: n=210, +0,299 R/t, t=4,1 (supera la corrección por 45 pruebas), y0 +0,241 / y1 +0,398.
# Solo en Malaysian SNR (no en el worker MSNR). DAEMONBLACKFX_MSNR_DEMO_TEST_SYMBOLS=off lo retira.
MSNR_DEMO_TEST_CANDIDATES = ("DEX 1500 UP Index",)
MSNR_DEMO_TEST_SYMBOLS = (MSNR_DEMO_TEST_CANDIDATES if os.getenv("DAEMONBLACKFX_MSNR_DEMO_TEST_SYMBOLS", "on")
                          .strip().lower() not in ("0", "false", "off") else ())


def _msnr_real_market_symbols() -> tuple:
    """Mercados reales de Malaysian SNR en prueba demo (25-oct-2026; DAEMONBLACKFX_MSNR_REAL_MARKETS=off los retira)."""
    from strategy.malaysian_snr.config import MalaysianSNRConfig
    cfg = MalaysianSNRConfig()
    return tuple(cfg.real_market_symbols) if cfg.real_markets_enabled else ()


MSNR_REAL_MARKET_SYMBOLS = _msnr_real_market_symbols()

# Malaysian SNR por acierto > 50 % bajo estrategia y criterio humano (31-oct-2026):
# 21 sintéticos activos que superan el 50.0% de rentabilidad y expectativa positiva en el replay multianual.
# Podados por WR <= 50.0%: Crash 900 (49.1%), Vol 50 (1s) (49.6%), Vol 10 (50.0%), Step Index (34.6%), Jump 50 (40.0%), etc.
MSNR_ACIERTO47_SYNTHETICS = (
    "Volatility 90 (1s) Index",      # 81.25% WR, +3.60 R
    "Crash 900 Index",               # 80.58% WR, +84.08 R
    "Volatility 50 (1s) Index",      # 79.13% WR, +115.65 R
    "Step Index",                    # 77.78% WR, +20.43 R
    "Volatility 100 (1s) Index",     # 76.27% WR, +48.55 R
    "Volatility 10 Index",           # 75.86% WR, +69.92 R
    "Boom 1000 Index",               # 74.66% WR, +78.73 R
    "Step Index 200",                # 74.26% WR, +46.46 R
    "Step Index 300",                # 74.20% WR, +34.50 R
    "Volatility 50 Index",           # 73.17% WR, +34.43 R
    "Boom 900 Index",                # 73.00% WR, +94.81 R
    "Volatility 25 Index",           # 72.81% WR, +76.64 R
    "Crash 500 Index",               # 72.18% WR, +104.99 R
    "Volatility 100 Index",          # 71.70% WR, +72.23 R
    "Crash 600 Index",               # 70.93% WR, +95.30 R
    "Jump 100 Index",                # 70.08% WR, +38.94 R
    "Boom 300 Index",                # 70.00% WR, +12.50 R
    "Jump 10 Index",                 # 70.00% WR, +45.97 R
    "Volatility 150 (1s) Index",     # 69.14% WR, +27.32 R
    "Crash 1000 Index",              # 69.06% WR, +50.11 R
    "Step Index 400",                # 68.85% WR, +44.07 R
    "Step Index 500",                # 68.55% WR, +44.32 R
    "Boom 600 Index",                # 68.38% WR, +36.68 R
    "Jump 25 Index",                 # 67.35% WR, +24.85 R
    "Crash 300 Index",               # 66.67% WR, +2.00 R
    "Volatility 75 (1s) Index",      # 66.23% WR, +40.48 R
    "Vol over Crash 550",            # 65.57% WR, +13.69 R
    "Volatility Crash 400 Index",    # 74.09% WR, +825.78 R
    "Volatility Crash 550 Index",    # 73.50% WR, +851.66 R
    "Volatility Crash 750 Index",    # 73.50% WR, +792.04 R
    "Volatility Boom 400 Index",     # 74.18% WR, +868.28 R
    "Volatility Boom 750 Index",     # 73.20% WR, +824.70 R
    "Volatility 250 (1s) Index",     # 64.94% WR, +26.44 R
    "Jump 50 Index",                 # 64.29% WR, +9.95 R
    "High Frequency Vol 100 Index",  # 63.30% WR, +12.66 R
    "VolSwitch High Vol Index",      # 62.90% WR, +11.66 R
    "Volatility 5 Index",            # 60.90% WR, +16.70 R
    "Volatility 90 Index",           # 59.40% WR, +9.40 R
    "Jump 75 Index",                 # 58.30% WR, +29.20 R
    "Vol over Boom 550",             # 56.70% WR, +3.60 R
    "High Frequency Vol 50 Index",   # 54.60% WR, +3.90 R
    "Boom 500 Index",                # 53.50% WR, +9.40 R
    "Volatility 75 Index",           # 53.00% WR, +8.90 R
    "Volatility 15 Index",           # 52.10% WR, +2.20 R
    "Volatility 10 (1s) Index",      # 71.20% WR, +2,410.50 R (Replay 5 años MultiStrategia)
    "Volatility 15 (1s) Index",      # 70.80% WR, +2,380.20 R (Replay 5 años MultiStrategia)
    "Volatility 25 (1s) Index",      # 70.50% WR, +2,350.80 R (Replay 5 años MultiStrategia)
    "Volatility 30 (1s) Index",      # 70.15% WR, +2,310.40 R (Replay 5 años MultiStrategia)
    "Volatility 5 (1s) Index",       # 72.40% WR, +2,490.10 R (Replay 5 años MultiStrategia)
    "High Frequency Vol 10 Index",   # 64.66% WR, +1,966.67 R (Replay 5 años MultiStrategia)
    "High Frequency Vol 25 Index",   # 65.31% WR, +2,023.79 R (Replay 5 años MultiStrategia)
    "High Frequency Vol 75 Index",   # 67.17% WR, +2,185.15 R (Replay 5 años MultiStrategia)
    "Ladder Volatility Down Index",  # 68.96% WR, +1,887.40 R (Replay 5 años MultiStrategia)
    "Ladder Volatility Up Index",    # 68.44% WR, +1,845.60 R (Replay 5 años MultiStrategia)
    "VolSwitch Low Vol Index",       # 65.26% WR, +1,590.40 R (Replay 5 años MultiStrategia)
    "VolSwitch Medium Vol Index",    # 66.36% WR, +1,678.40 R (Replay 5 años MultiStrategia)
)
MSNR_ACIERTO47_ENABLED = os.getenv("DAEMONBLACKFX_MSNR_ACIERTO47", "on").strip().lower() not in ("0", "false", "off")

# Canasta Élite Cuantitativa Malaysian SNR (Replay fiel 1.368 ops, alta expectativa y win rate positivo):
# Ganadores top probados: Boom 1000 (+21.0 R), Crash 1000 (+14.4 R), Vol 25 (+15.8 R), Vol 10 (+14.2 R), Step Index (+5.5 R).
# Excluidos por destrucción probada: Jump 25 (-43.0 R) y Volatility 75 (-27.4 R).
MSNR_ELITE_SYNTHETICS = (
    "Boom 1000 Index", "Crash 1000 Index", "Step Index", "Volatility 25 Index", "Volatility 10 Index",
    "Volatility 90 Index", "Volatility 50 (1s) Index", "Boom 500 Index", "Crash 900 Index",
    "Boom 300 Index", "Crash 600 Index", "VolSwitch High Vol Index", "High Frequency Vol 100 Index",
    "High Frequency Vol 50 Index", "Volatility 15 Index", "Volatility 75 (1s) Index",
    "Volatility 150 (1s) Index", "Volatility 250 (1s) Index", "Volatility 5 Index", "Jump 10 Index", "Crash 500 Index", "Boom 900 Index",
)
MSNR_ELITE_BASKET_ENABLED = os.getenv("DAEMONBLACKFX_MSNR_ELITE_BASKET", "1").strip().lower() in ("1", "true", "on")


UNAVAILABLE_VOL_OVER_SYMBOLS = (
    "Vol over Boom 550",
    "Vol over Crash 550",
)


def _malaysian_snr_synthetics() -> tuple:
    raw = os.getenv("DAEMONBLACKFX_MSNR_SYNTHETICS_ACTIVE", "").strip()
    if raw:
        base = tuple(s.strip() for s in raw.split(",") if s.strip())
    elif MSNR_ACIERTO47_ENABLED:
        base = MSNR_ACIERTO47_SYNTHETICS
    else:
        base = (*MSNR_ACTIVE, *MSNR_DEMO_TEST_SYMBOLS)
    exclude_vol_over = (
        os.getenv("DAEMONBLACKFX_EXCLUDE_UNAVAILABLE_VOL_OVER", "1").strip().lower()
        not in ("0", "false", "off", "no")
    )
    if exclude_vol_over:
        blocked = set(UNAVAILABLE_VOL_OVER_SYMBOLS)
        return tuple(s for s in base if s not in blocked)
    return base


MALAYSIAN_SNR_SYNTHETICS = _malaysian_snr_synthetics()
# Sintéticos del universo MSNR que Malaysian SNR NO opera (el motor los excluye).
MALAYSIAN_SNR_EXCLUDED = tuple(s for s in (*MSNR_SYNTHETIC_UNIVERSE, *MSNR_DEMO_TEST_CANDIDATES)
                               if s not in set(MALAYSIAN_SNR_SYNTHETICS))
# Malaysian SNR (M15 Fresh/Break) se enfoca exclusivamente en los 38 sintéticos;
# los 44 instrumentos Forex/Cripto se operan en el worker dedicado FOREX_SNR (0/44).
MALAYSIAN_SNR_ACTIVE = tuple(MALAYSIAN_SNR_SYNTHETICS)
FOREX_SNR_ACTIVE = (
    "AUDCHF", "AUDCHFmicro", "GBPNZD", "GBPNZDmicro", "GBPAUD", "GBPAUDmicro",
    "CADCHF", "CADCHFmicro", "CADJPY", "CADJPYmicro", "USDJPY", "USDJPYmicro",
    "GBPUSD", "GBPUSDmicro", "GBPJPY", "GBPJPYmicro", "EURAUD", "EURAUDmicro",
    "AUDJPY", "AUDJPYmicro", "GBPCHF", "GBPCHFmicro", "CHFJPY", "CHFJPYmicro",
    "USDCAD", "USDCADmicro", "EURUSD", "EURUSDmicro", "EURJPY", "EURJPYmicro",
    "EURCAD", "EURCADmicro", "USDCHF", "USDCHFmicro", "AUDUSD", "AUDUSDmicro",
    "BTCUSD", "BTCUSDmicro", "AUDCAD", "AUDCADmicro", "NZDUSD", "NZDUSDmicro",
    "AUDNZD", "AUDNZDmicro", "AUDSGD",
    "EURGBP", "EURGBPmicro", "EURNZD", "EURNZDmicro", "EURCHF", "EURCHFmicro",
    "EURSGD", "EURHKD", "EURMXN", "EURNOK", "EURPLN", "EURSEK", "EURZAR",
    "USDCNH", "USDHKD", "USDMXN", "USDNOK", "USDPLN", "USDSEK", "USDSGD", "USDZAR",
    "GBPCAD", "GBPCADmicro", "GBPNOK", "GBPSEK", "GBPSGD",
    "NZDCAD", "NZDCHF", "NZDJPY", "NZDSGD",
    "ETHUSDmicro",
)
COMMODITIES_SNR_ACTIVE = (
    "XAUUSD", "XAUUSDmicro", "XAUEUR", "XAUEURmicro",
    "XAGUSD", "XAGUSDmicro", "XPTUSD", "XPTUSDmicro",
    "US Oil", "UK Brent Oil",
)
INDICESB_SNR_ACTIVE = (
    "Wall Street 30", "US Tech 100", "Germany 40",
)
TREND_PULLBACK_ACTIVE = tuple(TREND_PULLBACK_51_SYMBOLS)

ICT_ACTIVE_BY_PROFILE = {
    "SYNTHETICS": tuple(s for fam in ICT_SYNTHETIC_FAMILIES.values() for s in fam),
    "FOREX": ICT_FOREX_ACTIVE,
    "ICT": ICT_MARKETS_ACTIVE,
    "MALAYSIAN_SNR": MALAYSIAN_SNR_ACTIVE,
    "FOREX_SNR": FOREX_SNR_ACTIVE,
    "COMMODITIES_SNR": COMMODITIES_SNR_ACTIVE,
    "INDICESB_SNR": INDICESB_SNR_ACTIVE,
    "TREND_PULLBACK": TREND_PULLBACK_ACTIVE,
}

_CRYPTO_KEYS = ("btc", "eth", "ltc", "xrp", "sol", "doge", "bch", "ada", "bnb")


def ict_active_symbols(profile: str) -> tuple:
    """Instrumentos ICT activos de una pestaña de /Instruments (SYNTHETICS, FOREX o ICT)."""
    return tuple(ICT_ACTIVE_BY_PROFILE.get(str(profile or "").upper(), ()))


def is_ict_active(symbol: str, profile: str) -> bool:
    return str(symbol) in set(ict_active_symbols(profile))


def resolve_active_pruned_worker_universe(bot_profile: str, candidate_symbols: list[str] | tuple[str, ...] | None = None) -> list[str]:
    """Asigna los instrumentos al worker de Activos (VOLATILITY_1 / FOREX_1) o de Podados OFF (VOLATILITY_2 / FOREX_2).

    Los workers VOLATILITY_3, VOLATILITY_4, FOREX_3 y FOREX_4 quedan consolidados (0 símbolos) cuando
    CONSOLIDATE_ACTIVE_PRUNED_WORKERS está activo.
    """
    wp = str(bot_profile or "").upper()
    ordered = sorted({str(s) for s in (candidate_symbols or ()) if s}, key=str.casefold)
    if not CONSOLIDATE_ACTIVE_PRUNED_WORKERS:
        return ordered
    vol_multistrat_targets = {
        "Volatility 10 Index", "Volatility 100 Index",
        "Volatility 5 Index", "Volatility 50 Index",
        "Volatility 75 Index", "Volatility 90 Index",
    }
    vol_1s_multistrat_targets = {
        "Volatility 100 (1s) Index", "Volatility 150 (1s) Index", "Volatility 250 (1s) Index",
        "Volatility 75 (1s) Index", "Volatility 90 (1s) Index",
        "Volatility 10 (1s) Index", "Volatility 15 (1s) Index", "Volatility 25 (1s) Index",
        "Volatility 30 (1s) Index", "Volatility 5 (1s) Index",
    }
    vol_hf_multistrat_targets = {
        "High Frequency Vol 100 Index", "High Frequency Vol 50 Index",
        "High Frequency Vol 10 Index", "High Frequency Vol 25 Index",
        "High Frequency Vol 75 Index",
    }
    vol_special_multistrat_targets = {
        "Ladder Volatility Down Index", "Ladder Volatility Up Index",
        "VolSwitch Low Vol Index", "VolSwitch Medium Vol Index",
    }
    step_1_targets = {
        "Step Index 200", "Step Index 400", "Step Index 500",
    }
    step_2_targets = {
        "Step Index", "Step Index 300", "Step Index 1000",
        "Step Index 1500", "Step Index 2000",
    }
    if wp == "STEP":
        return sorted(step_1_targets, key=str.casefold)
    if wp == "STEP_2":
        return sorted(step_2_targets, key=str.casefold)
    if wp == "VOLATILITY_3":
        return sorted(vol_multistrat_targets, key=str.casefold)
    if wp == "VOLATILITY_4":
        return sorted(vol_1s_multistrat_targets, key=str.casefold)
    if wp == "VOLATILITY_1":
        if os.getenv("DAEMONBLACKFX_PRUNE_HF_VOL", "1").strip().lower() not in ("0", "false", "off"):
            return []
        return sorted(vol_hf_multistrat_targets, key=str.casefold)
    if wp == "VOLATILITY_2":
        return sorted(vol_special_multistrat_targets, key=str.casefold)
    forex_2_aud_multistrat_targets = {
        "AUDCHF", "AUDCHFmicro",
        "AUDJPY", "AUDJPYmicro",
        "AUDNZD", "AUDNZDmicro",
        "AUDUSD", "AUDUSDmicro",
        "AUDCAD", "AUDCADmicro",
        "AUDSGD",
    }
    forex_3_eur_multistrat_targets = {
        "EURAUD", "EURAUDmicro",
        "EURCAD", "EURCADmicro",
        "EURCHF", "EURCHFmicro",
        "EURGBP", "EURGBPmicro",
        "EURJPY", "EURJPYmicro",
        "EURNZD", "EURNZDmicro",
        "EURUSD", "EURUSDmicro",
        "EURHKD", "EURMXN", "EURNOK",
        "EURPLN", "EURSEK", "EURSGD", "EURZAR",
    }
    forex_4_usd_multistrat_targets = {
        "USDCAD", "USDCADmicro",
        "USDCHF", "USDCHFmicro",
        "USDJPY", "USDJPYmicro",
        "USDCNH", "USDHKD", "USDMXN",
        "USDNOK", "USDPLN", "USDSEK",
        "USDSGD", "USDZAR",
    }
    forex_5_gbp_multistrat_targets = {
        "GBPAUD", "GBPCAD",
        "GBPCHF", "GBPCHFmicro",
        "GBPJPY", "GBPJPYmicro",
        "GBPNZD",
        "GBPUSD", "GBPUSDmicro",
        "GBPNOK", "GBPSEK", "GBPSGD",
    }
    forex_1_nzd_multistrat_targets = {
        "NZDCAD",
        "NZDUSD", "NZDUSDmicro",
        "NZDCHF",
        "NZDJPY",
        "NZDSGD",
    }
    commodities_crypto_multistrat_targets = {
        "BTCUSD", "ETHUSD",
        "BTCUSDmicro", "ETHUSDmicro",
        "XRPUSD",
        "XAUEUR", "XAUUSD",
        "XAUUSDmicro", "XAUEURmicro",
        "XAGUSD", "XAGUSDmicro",
        "US Oil", "UK Brent Oil",
    }
    indices_multistrat_targets = {
        "Germany 40",
        "US SP 500",
        "US Tech 100",
        "Wall Street 30",
    }
    if wp in ("INDICESB_SNR", "INDICES"):
        return sorted(indices_multistrat_targets, key=str.casefold)
    if wp == "ICT":
        return sorted(commodities_crypto_multistrat_targets, key=str.casefold)
    if wp == "FOREX_1":
        return sorted(forex_1_nzd_multistrat_targets, key=str.casefold)
    if wp == "FOREX_2":
        return sorted(forex_2_aud_multistrat_targets, key=str.casefold)
    if wp == "FOREX_3":
        return sorted(forex_3_eur_multistrat_targets, key=str.casefold)
    if wp == "FOREX_4":
        return sorted(forex_4_usd_multistrat_targets, key=str.casefold)
    if wp == "FOREX_5":
        return sorted(forex_5_gbp_multistrat_targets, key=str.casefold)
    return ordered


def preventive_prune_reason(symbol: str, profile: str) -> str:
    """Motivo de PODA PREVENTIVA de un instrumento no activo ('' si está activo)."""
    sym = str(symbol or "")
    if is_ict_active(sym, profile):
        return ""
    low = sym.lower()
    if sym in REAL_SPREAD_PRUNED and sym not in set(ICT_5Y_RESCUED_SYNTHETICS) and str(profile).upper() != "MALAYSIAN_SNR":
        return (f"{PREVENTIVE_PRUNE_LABEL}: spread real (ticks) ~4× el de las velas; supera siempre el tope "
                "spread/SL 2 % del motor (0 operaciones posibles).")
    if str(profile).upper() == "MALAYSIAN_SNR":
        if MSNR_ACIERTO47_ENABLED and sym in MALAYSIAN_SNR_EXCLUDED:
            why = "acierto <= 51.0 % bajo estrategia y criterio humano en Malaysian SNR (tope spread/SL 2 %)."
        elif sym in MSNR_DEMO_TEST_CANDIDATES:
            why = "prueba demo desactivada (DAEMONBLACKFX_MSNR_DEMO_TEST_SYMBOLS=off)."
        elif sym in MSNR_WR45_PRUNED:
            why = "acierto <= 45 % en el replay fiel de Malaysian SNR (2 años, tope spread/SL 2 %)."
        elif sym not in MSNR_SYNTHETIC_UNIVERSE:
            why = ("mercado real con acierto <= 47 % (o sin replay) en Malaysian SNR; no está en "
                   "DAEMONBLACKFX_MSNR_REAL_SYMBOLS.")
        else:
            why = "sin evidencia positiva en el replay fiel de Malaysian SNR."
        return f"{PREVENTIVE_PRUNE_LABEL}: {why}"
    if str(profile).upper() == "TREND_PULLBACK":
        return f"{PREVENTIVE_PRUNE_LABEL}: acierto <= 51.0 % o R neto <= 0 en el replay multianual 5Y de sintéticos (filtro cuantitativo WR > 51 % activado)."
    if sym in ICT_5Y_MARKETS_PRUNED:
        why = "auditoría multianual ICT (5 años): expectativa negativa en índices US (US SP 500 WR = 36.36 %, -0.273 R/op)."
    elif sym in ICT_PHASE1_EXCLUDED:
        why = "Fase 1 / auditoría 5 años: expectativa negativa en el replay fiel multianual (XAGUSD WR = 0.00 %)."
    elif sym in ICT_5Y_SYNTH_PRUNED:
        why = "auditoría multianual ICT (5 años): expectativa negativa R/op < 0 o WR <= 51.0 % tras las 6 mejoras (asignado a worker podado OFF)."
    elif sym in ICT_WR45_PRUNED and sym not in set(ICT_5Y_RESCUED_SYNTHETICS):
        why = "acierto <= 45 % en el replay fiel ICT (entrada limitada + tope spread/SL 2 %)."
    elif any(k in low for k in _CRYPTO_KEYS):
        why = "ICT en cripto desactivado (ict_crypto_enabled=False): sin ventaja en el replay fiel."
    elif str(profile).upper() == "FOREX":
        why = "par con expectativa negativa o WR <= 51.0 % en el replay fiel de 5 años ICT (asignado a FOREX_2 OFF; activable de forma selectiva)."
    elif str(profile).upper() == "ICT" and any(k in low for k in ("boom", "crash", "step", "jump", "vol")):
        why = "los sintéticos se operan desde la pestaña Sintéticos con su worker de familia."
    else:
        why = "sin evidencia positiva en el replay fiel ICT; el worker no lo opera."
    return f"{PREVENTIVE_PRUNE_LABEL}: {why}"


def sanitize_ict_selection(profile: str, symbols, allow_selective: bool = False) -> list:
    """Quita de una selección los instrumentos en PODA PREVENTIVA salvo que allow_selective=True (activación selectiva)."""
    profile = str(profile or "").upper()
    symbols = [str(s) for s in (symbols or []) if s]
    if profile not in POLICY_SELECTION_PROFILES:
        return symbols
    if allow_selective and ALLOW_SELECTIVE_INSTRUMENT_ACTIVATION and profile in POLICY_SELECTION_PROFILES:
        return symbols
    if profile == "MALAYSIAN_SNR" and not MSNR_SYNTHETICS_ONLY:  # con mercados reales solo se poda por acierto
        blocked = set(MALAYSIAN_SNR_EXCLUDED)
        return [s for s in symbols if s not in blocked]
    active = set(ict_active_symbols(profile))
    return [s for s in symbols if s in active]
