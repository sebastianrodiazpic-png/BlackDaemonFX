import sys
sys.path.insert(0, ".")
from strategy.ai.model_inventory import scan_trained_models_catalog

catalog = scan_trained_models_catalog()
print("Total modelos en el catálogo:", len(catalog))
for m in catalog:
    w = m.get("worker")
    strat = m.get("strategy_name")
    tr = m.get("trained")
    samp = m.get("samples")
    pr = m.get("positive_rate", 0) * 100
    win_rr = m.get("average_win_rr", 0)
    print(f"  Worker: {w:12} | Strategy: {strat:6} | Entrenado: {str(tr):5} | Muestras: {samp:4} | WinRate: {pr:5.1f}% | Win RR: {win_rr:.2f}R")
