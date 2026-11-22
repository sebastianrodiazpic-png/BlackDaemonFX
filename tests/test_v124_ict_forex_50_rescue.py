"""11-nov-2026: cruces Forex podados por defecto y opcionalmente rescatables con DAEMONBLACKFX_ICT_FOREX_50_RESCUE=1."""
import subprocess
import sys
import os

from config.ict_instrument_policy import (
    ICT_ACTIVE_BY_PROFILE,
    ICT_FOREX_ACTIVE,
    ICT_FOREX_PRUNED_SYMBOLS,
    ICT_FOREX_50_RESCUED_BASES,
    preventive_prune_reason,
    PREVENTIVE_PRUNE_LABEL,
)
from strategy.confluence.tripartite_confluence_gate import (
    STRICT_PRUNED_ASSETS_BY_STRATEGY,
    TripartiteConfluenceGate,
)

PRUNED_REQUESTED = (
    "AUDCHF", "AUDCHFmicro", "AUDJPY", "AUDJPYmicro", "AUDNZD", "AUDNZDmicro", "CADJPY", "CADJPYmicro",
    "CHFJPY", "EURAUD", "EURAUDmicro", "EURCAD", "EURCADmicro", "EURGBP", "EURGBPmicro", "EURNZD",
    "EURNZDmicro", "GBPAUD", "GBPCAD", "GBPCHF", "GBPCHFmicro", "GBPNZD",
    "USDJPY", "USDJPYmicro", "AUDCAD", "AUDCADmicro", "CADCHF", "CADCHFmicro",
)


def test_pruned_requested_pairs_in_forex_tab():
    """Por defecto (DAEMONBLACKFX_ICT_FOREX_50_RESCUE=0), todos los cruces y USDJPY están en PODA PREVENTIVA."""
    for sym in PRUNED_REQUESTED:
        assert sym not in ICT_FOREX_ACTIVE, f"{sym} no debe estar activo"
        assert sym not in ICT_ACTIVE_BY_PROFILE["FOREX"], f"{sym} no debe estar en activos de FOREX"
        assert preventive_prune_reason(sym, "FOREX").startswith(PREVENTIVE_PRUNE_LABEL), f"{sym} debe tener motivo de poda"
        assert sym in ICT_FOREX_PRUNED_SYMBOLS, f"{sym} debe estar en podados"


def test_default_rescued_bases_empty():
    """Por defecto no hay rescate activo; las bases rescatadas son vacías."""
    assert len(ICT_FOREX_50_RESCUED_BASES) == 0


def test_tripartite_gate_vetoes_pruned_pairs():
    strict = STRICT_PRUNED_ASSETS_BY_STRATEGY["ICT"]
    assert "AUDCAD" in strict
    gate = TripartiteConfluenceGate()
    dec = gate.evaluate_confluence(symbol="AUDCAD", strategy_name="ICT", direction="SELL", signal={"sl": 100, "tp": 200})
    assert dec.action == "VETO_STRICT_PRUNING"


def test_switch_on_enables_rescue_mode():
    code = (
        "import os;"
        "from config.ict_instrument_policy import ICT_FOREX_50_RESCUED_BASES;"
        "assert len(ICT_FOREX_50_RESCUED_BASES) == 13"
    )
    env = dict(os.environ, DAEMONBLACKFX_ICT_FOREX_50_RESCUE="1")
    assert subprocess.run([sys.executable, "-c", code], env=env).returncode == 0

