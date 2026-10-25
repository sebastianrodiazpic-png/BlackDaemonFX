"""Política única de instrumentos de /Instruments para ICT y Malaysian SNR (20-oct-2026).

Fuente de verdad compartida por los workers (STEP, JUMP, VOLATILITY_1-4, BOOM, CRASH, FOREX_1-4, ICT y
MALAYSIAN_SNR), el motor (listas permitidas por familia) y el dashboard (/Instruments, pestañas Sintéticos,
Forex, ICT y Malaysian SNR).

- ACTIVO: el instrumento lo puede operar su worker; queda marcado en /Instruments y la selección persistida
  decide en cada ciclo si se escanea (desmarcarlo lo apaga sin reiniciar).
- PODA PREVENTIVA: el motor lo bloquea (exclusiones Fase 1, acierto <= 45 %, cripto desactivado, pares sin
  evidencia...). Aparece desmarcado y bloqueado en /Instruments para que nunca quede "activo con poda".

Variables de entorno (se leen al importar):
- DAEMONBLACKFX_ICT_UNPRUNE_SYNTHETICS=0 vuelve a las listas de sintéticos anteriores a la liberación.
- DAEMONBLACKFX_SYNTH_WR45_PRUNE=0 desactiva la poda por acierto <= 45 % (config/synth_wr45.py).
- DAEMONBLACKFX_MSNR_SYNTHETICS_ONLY=0 deja de podar los mercados reales en Malaysian SNR (como el motor).
"""
from __future__ import annotations

import os

from config.synth_wr45 import ICT_WR45_PRUNED, MSNR_WR45_PRUNED, REAL_SPREAD_PRUNED

PREVENTIVE_PRUNE_LABEL = "PODA PREVENTIVA"
ICT_SELECTION_PROFILES = ("SYNTHETICS", "FOREX", "ICT")
# Pestañas de /Instruments gobernadas por esta política (ICT + Malaysian SNR).
POLICY_SELECTION_PROFILES = (*ICT_SELECTION_PROFILES, "MALAYSIAN_SNR", "MSNR")

_UNPRUNE_SYNTHETICS = os.getenv("DAEMONBLACKFX_ICT_UNPRUNE_SYNTHETICS", "1").strip().lower() not in ("0", "false", "off")

# Fase 1 (18-oct-2026): expectativa negativa en ambas mitades del replay fiel 365d (ICTSabriMalleConfig.excluded_symbols).
ICT_PHASE1_EXCLUDED = ("Step Index", "Jump 25 Index", "Volatility 25 Index", "XAGUSD", "XAGUSDmicro", "microXAGUSD")


def _keep(*symbols):
    blocked = set(ICT_WR45_PRUNED) | set(ICT_PHASE1_EXCLUDED)
    return tuple(s for s in symbols if s not in blocked)


# Sintéticos ICT por familia de worker (replay fiel con entrada limitada + tope spread/SL 2 %).
ICT_SYNTHETIC_FAMILIES = {
    "STEP": _keep("Step Index 400", "Step Index 500", *(("Step Index 200",) if _UNPRUNE_SYNTHETICS else ())),
    "JUMP": _keep("Jump 75 Index", "Jump 10 Index", "Jump 50 Index"),
    "VOLATILITY": _keep(
        "Volatility 50 (1s) Index", "Volatility 150 (1s) Index", "Volatility 75 Index", "Volatility 75 (1s) Index",
        "VolSwitch High Vol Index", "Volatility 15 Index", "High Frequency Vol 50 Index", "Volatility 250 (1s) Index",
        "Volatility 90 Index", "Volatility 5 Index", "High Frequency Vol 100 Index", "Vol over Boom 550",
        "Volatility 90 (1s) Index", "Vol over Crash 550",
        *(("Volatility 10 Index", "Volatility 100 Index", "Volatility 100 (1s) Index") if _UNPRUNE_SYNTHETICS else ()),
    ),
    "BOOM": _keep("Boom 1000 Index", "Boom 900 Index", "Boom 300 Index",
                  *(("Boom 500 Index", "Boom 600 Index") if _UNPRUNE_SYNTHETICS else ())),
    "CRASH": _keep("Crash 1000 Index", "Crash 900 Index", "Crash 500 Index",
                   *(("Crash 300 Index",) if _UNPRUNE_SYNTHETICS else ())),
}

# Forex: pares que los workers FOREX_1-4 realmente operan (tope spread/SL 5 %, killzones Londres/NY).
ICT_FOREX_ACTIVE = (
    "EURUSD", "USDJPY", "GBPUSD", "USDCAD", "USDCHF", "GBPCAD", "AUDUSD",
    "EURUSDmicro", "USDJPYmicro", "GBPUSDmicro", "USDCADmicro", "USDCHFmicro", "GBPCADmicro", "AUDUSDmicro",
)

# Worker ICT (metales, índices y commodities). Cripto queda en poda preventiva (ict_crypto_enabled=False)
# y la plata por Fase 1; los sintéticos los operan sus workers de familia (pestaña Sintéticos) y EURUSD los
# workers Forex (pestaña Forex), para que ningún instrumento se controle desde dos pestañas.
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
MALAYSIAN_SNR_ACTIVE = (*MSNR_ACTIVE, *MSNR_DEMO_TEST_SYMBOLS)

ICT_ACTIVE_BY_PROFILE = {
    "SYNTHETICS": tuple(s for fam in ICT_SYNTHETIC_FAMILIES.values() for s in fam),
    "FOREX": ICT_FOREX_ACTIVE,
    "ICT": ICT_MARKETS_ACTIVE,
    "MALAYSIAN_SNR": MALAYSIAN_SNR_ACTIVE,
    # Worker MSNR (estrategia de los vídeos): mismos instrumentos que la pestaña Malaysian SNR.
    "MSNR": MSNR_ACTIVE,
}

_CRYPTO_KEYS = ("btc", "eth", "ltc", "xrp", "sol", "doge", "bch", "ada", "bnb")


def ict_active_symbols(profile: str) -> tuple:
    """Instrumentos ICT activos de una pestaña de /Instruments (SYNTHETICS, FOREX o ICT)."""
    return tuple(ICT_ACTIVE_BY_PROFILE.get(str(profile or "").upper(), ()))


def is_ict_active(symbol: str, profile: str) -> bool:
    return str(symbol) in set(ict_active_symbols(profile))


def preventive_prune_reason(symbol: str, profile: str) -> str:
    """Motivo de PODA PREVENTIVA de un instrumento no activo ('' si está activo)."""
    sym = str(symbol or "")
    if is_ict_active(sym, profile):
        return ""
    low = sym.lower()
    if sym in REAL_SPREAD_PRUNED:
        return (f"{PREVENTIVE_PRUNE_LABEL}: spread real (ticks) ~4× el de las velas; supera siempre el tope "
                "spread/SL 2 % del motor (0 operaciones posibles).")
    if str(profile).upper() in ("MALAYSIAN_SNR", "MSNR"):
        if sym in MSNR_DEMO_TEST_CANDIDATES:
            why = ("sintético en prueba demo solo para Malaysian SNR." if str(profile).upper() == "MSNR"
                   else "prueba demo desactivada (DAEMONBLACKFX_MSNR_DEMO_TEST_SYMBOLS=off).")
        elif sym in MSNR_WR45_PRUNED:
            why = "acierto <= 45 % en el replay fiel de Malaysian SNR (2 años, tope spread/SL 2 %)."
        elif sym not in MSNR_SYNTHETIC_UNIVERSE:
            why = "Malaysian SNR solo opera sintéticos: mercados reales negativos en ambos años del replay fiel."
        else:
            why = "sin evidencia positiva en el replay fiel de Malaysian SNR."
        return f"{PREVENTIVE_PRUNE_LABEL}: {why}"
    if sym in ICT_PHASE1_EXCLUDED:
        why = "Fase 1: expectativa negativa en ambas mitades del replay fiel 365d."
    elif sym in ("Volatility 50 Index", "Crash 600 Index"):
        why = "R negativo en el replay fiel ICT; se mantuvo fuera al liberar los sintéticos podados."
    elif sym in ICT_WR45_PRUNED:
        why = "acierto <= 45 % en el replay fiel ICT (entrada limitada + tope spread/SL 2 %)."
    elif any(k in low for k in _CRYPTO_KEYS):
        why = "ICT en cripto desactivado (ict_crypto_enabled=False): sin ventaja en el replay fiel."
    elif str(profile).upper() == "FOREX":
        why = "par sin ventaja demostrada en el replay fiel ICT; el worker Forex no lo opera."
    elif str(profile).upper() == "ICT" and any(k in low for k in ("boom", "crash", "step", "jump", "vol")):
        why = "los sintéticos se operan desde la pestaña Sintéticos con su worker de familia."
    else:
        why = "sin evidencia positiva en el replay fiel ICT; el worker no lo opera."
    return f"{PREVENTIVE_PRUNE_LABEL}: {why}"


def sanitize_ict_selection(profile: str, symbols) -> list:
    """Quita de una selección los instrumentos en PODA PREVENTIVA (perfiles fuera de la política pasan intactos)."""
    profile = str(profile or "").upper()
    symbols = [str(s) for s in (symbols or []) if s]
    if profile not in POLICY_SELECTION_PROFILES:
        return symbols
    if profile in ("MALAYSIAN_SNR", "MSNR") and not MSNR_SYNTHETICS_ONLY:  # con mercados reales solo se poda por acierto
        return [s for s in symbols if s not in set(MSNR_WR45_PRUNED)]
    active = set(ict_active_symbols(profile))
    return [s for s in symbols if s in active]
