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
- DAEMONBLACKFX_MSNR_SYNTHETICS_ONLY=0 deja de podar los mercados reales en Malaysian SNR (como el motor).
"""
from __future__ import annotations

import os

from config.synth_wr45 import ICT_WR45_PRUNED, MSNR_WR45_PRUNED, REAL_SPREAD_PRUNED
from strategy.trend_pullback.config import TREND_PULLBACK_51_SYMBOLS

PREVENTIVE_PRUNE_LABEL = "PODA PREVENTIVA"
ICT_SELECTION_PROFILES = ("SYNTHETICS", "FOREX", "ICT")
# Pestañas de /Instruments gobernadas por esta política (ICT + Malaysian SNR + Trend Pullback).
POLICY_SELECTION_PROFILES = (*ICT_SELECTION_PROFILES, "MALAYSIAN_SNR", "TREND_PULLBACK")

_UNPRUNE_SYNTHETICS = os.getenv("DAEMONBLACKFX_ICT_UNPRUNE_SYNTHETICS", "1").strip().lower() not in ("0", "false", "off")
ICT_5Y_AUDIT_ENABLED = os.getenv("DAEMONBLACKFX_ICT_5Y_AUDIT", "1").strip().lower() not in ("0", "false", "off")
ALLOW_SELECTIVE_INSTRUMENT_ACTIVATION = (
    os.getenv("DAEMONBLACKFX_ALLOW_SELECTIVE_ACTIVATION", "1").strip().lower() not in ("0", "false", "off")
)
CONSOLIDATE_ACTIVE_PRUNED_WORKERS = (
    os.getenv("DAEMONBLACKFX_CONSOLIDATE_ACTIVE_PRUNED_WORKERS", "1").strip().lower() not in ("0", "false", "off")
)

# Rescatados de Fase 1 tras replay fiel multianual 5 años con las 6 mejoras
# (orden limitada virtual + tope spread/SL <= 2.0 % / 2.5 % + filtro ADX + asimetría direccional + piso SL ATR):
# Todos los instrumentos con WR > 47% en el replay fiel de 5 años.
ICT_5Y_RESCUED_SYNTHETICS = (
    (
        "Jump 25 Index",
        "Volatility 25 Index",
        "Step Index",
        "Crash 300 Index",
        "Crash 600 Index",
        "Boom 300 Index",
        "Boom 1000 Index",
        "Vol over Boom 550",
        "Vol over Crash 550",
        "Volatility Boom 550 Index",
        "Volatility Crash 550 Index",
        "Volatility 50 Index",
        "Jump 50 Index",
        "Wall Street 30",
        "VolSwitch High Vol Index",  # Rescatado por decisión del usuario (WR = 61.1 % con Criterio Humano)
    )
    if (ICT_5Y_AUDIT_ENABLED and _UNPRUNE_SYNTHETICS)
    else ()
)

# Poda multianual 5 años en sintéticos e índices US: activos con WR <= 50 % bajo estrategia y criterio humano.
ICT_5Y_SYNTH_PRUNED = (
    (
        "Crash 1000 Index",             # WR = 44.60 %, -0.129 R/op, -27.5 R
        "Volatility 90 (1s) Index",     # WR = 45.71 %, -0.088 R/op, -9.2 R
        "High Frequency Vol 50 Index",  # WR = 42.39 %, -0.179 R/op, -16.5 R
        "Volatility 100 Index",         # WR con criterio humano = 49.7 % (<= 51.0 %)
        "Boom 500 Index",               # WR con criterio humano = 50.4 % (<= 51.0 %)
        "Crash 900 Index",              # WR con criterio humano = 50.5 % (<= 51.0 %)
    )
    if (ICT_5Y_AUDIT_ENABLED and _UNPRUNE_SYNTHETICS)
    else ()
)

ICT_5Y_MARKETS_PRUNED = (
    ("US SP 500",)
    if (ICT_5Y_AUDIT_ENABLED and _UNPRUNE_SYNTHETICS)
    else ()
)

# Fase 1 (18-oct-2026) + actualización 5 años con 6 mejoras (26-oct-2026):
_BASE_PHASE1_EXCLUDED = ("Step Index", "Jump 25 Index", "Volatility 25 Index", "Wall Street 30", "XAGUSD", "XAGUSDmicro", "microXAGUSD")
ICT_PHASE1_EXCLUDED = (
    tuple(s for s in _BASE_PHASE1_EXCLUDED if s not in set(ICT_5Y_RESCUED_SYNTHETICS)) + ICT_5Y_MARKETS_PRUNED
)


def _keep(*symbols):
    blocked = (set(ICT_WR45_PRUNED) | set(ICT_PHASE1_EXCLUDED) | set(ICT_5Y_SYNTH_PRUNED) | set(ICT_5Y_MARKETS_PRUNED)) - set(ICT_5Y_RESCUED_SYNTHETICS)
    return tuple(s for s in symbols if s not in blocked)


# Sintéticos ICT por familia de worker (replay fiel 5 años con 6 mejoras y WR > 47 %):
# 34 activos con WR > 47% (+500.1 R acumulados en los 29 con R > 0, WR = 53.43%).
ICT_SYNTHETIC_FAMILIES = {
    "STEP": _keep("Step Index 200", "Step Index", "Step Index 400", "Step Index 500"),
    "JUMP": _keep("Jump 50 Index", "Jump 75 Index", "Jump 10 Index", "Jump 25 Index"),
    "VOLATILITY": _keep(
        "Volatility 25 Index", "VolSwitch High Vol Index", "Volatility 90 Index", "Volatility 100 (1s) Index",
        "Volatility 10 Index", "Volatility 15 Index", "Volatility 5 Index", "Volatility 250 (1s) Index",
        "High Frequency Vol 100 Index", "Volatility 75 (1s) Index", "Volatility 50 (1s) Index",
        "Volatility 50 Index", "Volatility 150 (1s) Index", "Volatility 75 Index",
        "Vol over Boom 550", "Vol over Crash 550", "Volatility Boom 550 Index", "Volatility Crash 550 Index", "Volatility 100 Index",
        "Volatility 90 (1s) Index", "High Frequency Vol 50 Index",
    ),
    "BOOM": _keep("Boom 900 Index", "Boom 600 Index", "Boom 300 Index", "Boom 1000 Index", "Boom 500 Index"),
    "CRASH": _keep("Crash 300 Index", "Crash 500 Index", "Crash 600 Index", "Crash 900 Index", "Crash 1000 Index"),
}

# Universos de Volatility separados en Worker Activo (VOLATILITY_1) y Worker Podado OFF (VOLATILITY_2).
ICT_VOLATILITY_ACTIVE_SYMBOLS = ICT_SYNTHETIC_FAMILIES["VOLATILITY"]
ICT_VOLATILITY_PRUNED_SYMBOLS = (
    "Volatility 90 (1s) Index",
    "High Frequency Vol 50 Index",
    "Volatility 100 Index",
)

# Forex: pares con WR > 47 % y R/op > 0 en el replay fiel de 5 años tras las 6 mejoras operados por FOREX_1;
# el resto queda en FOREX_2 (desactivado por defecto, activable de forma selectiva desde /Instruments).
ICT_FOREX_ACTIVE_BASES = (
    ("GBPUSD", "USDCHF", "EURJPY", "CADCHF", "NZDUSD", "EURGBP", "GBPJPY")
    if ICT_5Y_AUDIT_ENABLED
    else ("EURUSD", "USDJPY", "GBPUSD", "USDCAD", "USDCHF", "GBPCAD", "AUDUSD")
)
ICT_FOREX_ACTIVE = tuple(ICT_FOREX_ACTIVE_BASES) + tuple(f"{base}micro" for base in ICT_FOREX_ACTIVE_BASES)

ICT_FOREX_ALL_BASES = (
    "GBPUSD", "USDCHF", "EURJPY", "CADCHF", "NZDUSD", "EURGBP", "GBPJPY", "GBPCHF", "AUDJPY",
    "EURAUD", "EURUSD", "EURCHF", "USDJPY", "AUDCAD", "AUDNZD", "AUDUSD", "USDCAD", "CHFJPY",
    "GBPCAD", "GBPAUD", "EURCAD",
)
ICT_FOREX_PRUNED_BASES = tuple(b for b in ICT_FOREX_ALL_BASES if b not in set(ICT_FOREX_ACTIVE_BASES))
ICT_FOREX_PRUNED_SYMBOLS = tuple(
    sym for base in ICT_FOREX_PRUNED_BASES for sym in (base, f"{base}micro")
)

# Worker ICT (metales, índices y commodities). En la auditoría de 5 años con 6 mejoras quedan activos:
# US Tech 100 (WR = 75.00 %, +16.0 R), Wall Street 30 (WR = 56.76 %, +4.5 R), XAUUSD (WR = 54.55 %, +2.0 R) y US Oil (WR = 53.33 %, +54.1 R mercado).
# US SP 500 (-3.0 R, WR = 36.36 %) pasa a PODA PREVENTIVA junto con XAGUSD y Cripto.
ICT_MARKETS_ACTIVE = _keep(
    "XAUUSD", "XAUUSDmicro", "microXAUUSD",
    "US Oil", "Wall Street 30", "US Tech 100", "US SP 500",
)


# Malaysian SNR: solo sintéticos (replay fiel 2 años con tope spread/SL 2 %; mercados reales negativos en
# ambos años: -0.157 / -0.079 R/trade) y sin los de acierto <= 45 % en su replay.
MSNR_SYNTHETICS_ONLY = os.getenv("DAEMONBLACKFX_MSNR_SYNTHETICS_ONLY", "1").strip().lower() not in ("0", "false", "off")
MSNR_SYNTHETIC_UNIVERSE = (
    "Boom 1000 Index", "Boom 300 Index", "Boom 500 Index", "Boom 600 Index", "Boom 900 Index",
    "Crash 1000 Index", "Crash 300 Index", "Crash 500 Index", "Crash 600 Index", "Crash 900 Index",
    "High Frequency Vol 100 Index", "High Frequency Vol 50 Index",
    "Jump 10 Index", "Jump 25 Index", "Jump 50 Index", "Jump 75 Index",
    "Step Index", "Step Index 200", "Step Index 400", "Step Index 500",
    "Vol over Boom 550", "Vol over Crash 550", "VolSwitch High Vol Index",
    "Volatility 10 Index", "Volatility 100 (1s) Index", "Volatility 100 Index", "Volatility 15 Index",
    "Volatility 150 (1s) Index", "Volatility 25 Index", "Volatility 250 (1s) Index", "Volatility 5 Index",
    "Volatility 50 (1s) Index", "Volatility 50 Index", "Volatility 75 (1s) Index", "Volatility 75 Index",
    "Volatility 90 (1s) Index", "Volatility 90 Index",
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
    "High Frequency Vol 100 Index",  # 63.3% WR, +10.8 R
    "VolSwitch High Vol Index",      # 62.9% WR, +9.3 R
    "Volatility 5 Index",            # 60.9% WR, +14.7 R
    "Volatility 90 Index",           # 59.4% WR, +7.4 R
    "Jump 75 Index",                 # 58.3% WR, +27.2 R
    "Vol over Boom 550",             # 56.7% WR, +1.6 R
    "High Frequency Vol 50 Index",   # 54.6% WR, +1.9 R
    "Jump 25 Index",                 # 53.7% WR, +8.7 R
    "Boom 500 Index",                # 53.5% WR, +7.4 R
    "Step Index 200",                # 53.4% WR, +8.4 R
    "Volatility 75 Index",           # 53.0% WR, +6.9 R
    "Step Index 500",                # 52.9% WR, +5.9 R
    "Volatility 75 (1s) Index",      # 52.8% WR, +10.3 R
    "Step Index 400",                # 52.7% WR, +9.2 R
    "Jump 10 Index",                 # 52.5% WR, +7.4 R
    "Volatility 250 (1s) Index",     # 52.2% WR, +8.7 R
    "Volatility 15 Index",           # 52.1% WR, +0.2 R
    "Volatility 25 Index",           # 51.2% WR, +0.5 R

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


def _malaysian_snr_synthetics() -> tuple:
    raw = os.getenv("DAEMONBLACKFX_MSNR_SYNTHETICS_ACTIVE", "").strip()
    if raw:
        return tuple(s.strip() for s in raw.split(",") if s.strip())
    if MSNR_ACIERTO47_ENABLED:
        return MSNR_ACIERTO47_SYNTHETICS
    return (*MSNR_ACTIVE, *MSNR_DEMO_TEST_SYMBOLS)


MALAYSIAN_SNR_SYNTHETICS = _malaysian_snr_synthetics()
# Sintéticos del universo MSNR que Malaysian SNR NO opera (el motor los excluye).
MALAYSIAN_SNR_EXCLUDED = tuple(s for s in (*MSNR_SYNTHETIC_UNIVERSE, *MSNR_DEMO_TEST_CANDIDATES)
                               if s not in set(MALAYSIAN_SNR_SYNTHETICS))
MALAYSIAN_SNR_ACTIVE = (*MALAYSIAN_SNR_SYNTHETICS, *MSNR_REAL_MARKET_SYMBOLS)
TREND_PULLBACK_ACTIVE = tuple(TREND_PULLBACK_51_SYMBOLS)

ICT_ACTIVE_BY_PROFILE = {
    "SYNTHETICS": tuple(s for fam in ICT_SYNTHETIC_FAMILIES.values() for s in fam),
    "FOREX": ICT_FOREX_ACTIVE,
    "ICT": ICT_MARKETS_ACTIVE,
    "MALAYSIAN_SNR": MALAYSIAN_SNR_ACTIVE,
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
    if wp == "VOLATILITY_1":
        active_set = set(ICT_VOLATILITY_ACTIVE_SYMBOLS)
        matched = [s for s in ordered if s in active_set]
        return matched or sorted(active_set, key=str.casefold)
    if wp == "VOLATILITY_2":
        active_set = set(ICT_VOLATILITY_ACTIVE_SYMBOLS)
        pruned_all = (set(ordered) - active_set) | set(ICT_VOLATILITY_PRUNED_SYMBOLS)
        return sorted(pruned_all, key=str.casefold)
    if wp in ("VOLATILITY_3", "VOLATILITY_4"):
        return []
    if wp == "FOREX_1":
        active_set = set(ICT_FOREX_ACTIVE)
        matched = [s for s in ordered if s in active_set]
        return matched or sorted(active_set, key=str.casefold)
    if wp == "FOREX_2":
        active_set = set(ICT_FOREX_ACTIVE)
        pruned_all = (set(ordered) - active_set) | set(ICT_FOREX_PRUNED_SYMBOLS)
        return sorted(pruned_all, key=str.casefold)
    if wp in ("FOREX_3", "FOREX_4"):
        return []
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
    if allow_selective and ALLOW_SELECTIVE_INSTRUMENT_ACTIVATION and profile in ICT_SELECTION_PROFILES:
        return symbols
    if profile == "MALAYSIAN_SNR" and not MSNR_SYNTHETICS_ONLY:  # con mercados reales solo se poda por acierto
        blocked = set(MALAYSIAN_SNR_EXCLUDED)
        return [s for s in symbols if s not in blocked]
    active = set(ict_active_symbols(profile))
    return [s for s in symbols if s in active]
