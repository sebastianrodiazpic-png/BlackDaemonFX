import math
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import numpy as np
import pandas as pd
from datetime import datetime, timezone

from strategy.malaysian_snr.config import MalaysianSNRConfig
from strategy.malaysian_snr.malaysian_snr_strategy import MalaysianSNRStrategy, compute_atr, compute_adx
from strategy.ai.meta_labeling import MetaLabelingEngine, MetaLabelingConfig
from strategy.ai.model_inventory import scan_trained_models_catalog
from dashboard.account_metrics import build_account_payload
from database.repository import TradingRepository

print("=" * 60)
print("AUDITORÍA DE COMPORTAMIENTO Y CONSISTENCIA: MALAYSIAN SNR & AI")
print("=" * 60)

# 1. Test MalaysianSNRConfig integrity
cfg = MalaysianSNRConfig()
print(f"1. MalaysianSNRConfig:")
print(f"   - Allowed symbols count: {len(cfg.allowed_symbols)}")
print(f"   - TP1 Min RR: {cfg.tp1_min_rr}")
print(f"   - TP2 Runner RR: {cfg.tp2_runner_rr}")
print(f"   - Storyline D1 enabled: {cfg.enable_d1_storyline_levels}")
print(f"   - CRT Sweep trigger enabled: {cfg.enable_crt_sweep_rejection}")
print(f"   - Obstacle awareness: {cfg.enable_obstacle_awareness} (Min RR: {cfg.min_obstacle_rr})")

assert len(cfg.allowed_symbols) == 23, f"Expected 23 allowed symbols, got {len(cfg.allowed_symbols)}"
assert cfg.tp1_min_rr >= 2.0, "TP1 min RR should be >= 2.0"
assert cfg.tp2_runner_rr >= 2.5, "TP2 runner RR should be >= 2.5"

# 2. Test AI Model Inventory and Catalog
print("\n2. Catálogo de Modelos de IA:")
catalog = scan_trained_models_catalog()
msnr_catalog = [m for m in catalog if m["worker"] == "MALAYSIAN_SNR" and m["strategy_name"] == "MALAYSIAN_SNR"]

assert len(msnr_catalog) == 1, f"Expected 1 entry for MALAYSIAN_SNR · MALAYSIAN_SNR, found {len(msnr_catalog)}"
item = msnr_catalog[0]
print(f"   - Filename: {item['filename']}")
print(f"   - Worker: {item['worker']}")
print(f"   - Strategy: {item['strategy_name']}")
print(f"   - Family: {item['family']}")
print(f"   - Trained: {item['trained']}")
print(f"   - Samples: {item['samples']}")
print(f"   - Win Rate Base (positive_rate): {item['positive_rate'] * 100:.1f}%")
print(f"   - Win RR / Loss RR: +{item['average_win_rr']}R / -{item['average_loss_rr']}R")
print(f"   - Accuracy: {item['accuracy'] * 100:.1f}%")
print(f"   - Status: {item['status']}")

assert item["trained"] is True
assert item["samples"] >= 200000
assert item["positive_rate"] >= 0.40
assert item["accuracy"] >= 0.70

# 3. Test MetaLabelingEngine live scoring behavior for MALAYSIAN_SNR
print("\n3. Comportamiento del Motor de Meta-Etiquetado en Vivo:")
engine = MetaLabelingEngine(MetaLabelingConfig(mode="FILTER"), worker="MALAYSIAN_SNR")
model = engine.load_model("MALAYSIAN_SNR")
assert model.trained, "Model must be trained!"

# Test scoring on active symbol (e.g., Step Index 400)
active_sig = {
    "direction": "BUY",
    "risk_reward_ratio": 2.5,
    "entry_price": 1000.0,
    "stop_loss": 995.0,
    "trade_score": 90.0,
    "confirmation_percentage": 90.0,
    "body_ratio": 0.65,
    "adx": 30.0,
    "confirmations": {"rejection": True, "micro_structure": True, "displacement": True, "strong_close": True},
    "structure_aligned": 1.0,
    "chart_pattern_strength": 0.85
}
active_analysis = {
    "strategy_name": "MALAYSIAN_SNR",
    "context_policy": "MALAYSIAN_SNR_NATIVE",
    "adx": 30.0,
    "atr": 5.0
}
active_market = {
    "planned_rr": 2.5,
    "risk_percent": 1.0,
    "spread_ratio": 0.0001
}

decision_active = engine.score_signal(
    symbol="Step Index 400",
    signal=active_sig,
    analysis=active_analysis,
    market=active_market,
    strategy_name="MALAYSIAN_SNR"
)

print(f"   [Activo Validado: Step Index 400]")
print(f"   - Probabilidad calculada: {decision_active.probability:.4f}")
print(f"   - Expectativa Neta (R): {decision_active.net_expectancy_r:+.4f} R")
print(f"   - Autorizado por IA: {decision_active.allowed}")
print(f"   - Razón de decisión: {decision_active.reason}")

assert 0.0 <= decision_active.probability <= 1.0
assert math.isfinite(decision_active.net_expectancy_r)
assert decision_active.allowed is True, "Step Index 400 with high score should be allowed"

# Test scoring on pruned symbol (e.g., Volatility 50 Index)
pruned_sig = {
    "direction": "BUY",
    "risk_reward_ratio": 2.0,
    "entry_price": 500.0,
    "stop_loss": 490.0,
    "trade_score": 60.0,
    "confirmation_percentage": 50.0,
    "body_ratio": 0.40,
    "adx": 18.0,
    "confirmations": {},
    "structure_aligned": 0.0,
    "chart_pattern_strength": 0.20
}
pruned_analysis = {
    "strategy_name": "MALAYSIAN_SNR",
    "context_policy": "MALAYSIAN_SNR_NATIVE",
    "adx": 18.0,
    "atr": 15.0
}
pruned_market = {
    "planned_rr": 2.0,
    "risk_percent": 1.0,
    "spread_ratio": 0.005
}

decision_pruned = engine.score_signal(
    symbol="Volatility 50 Index",
    signal=pruned_sig,
    analysis=pruned_analysis,
    market=pruned_market,
    strategy_name="MALAYSIAN_SNR"
)

print(f"\n   [Activo Podado: Volatility 50 Index (Baja Calidad)]")
print(f"   - Probabilidad calculada: {decision_pruned.probability:.4f}")
print(f"   - Expectativa Neta (R): {decision_pruned.net_expectancy_r:+.4f} R")
print(f"   - Autorizado por IA: {decision_pruned.allowed}")
print(f"   - Razón de decisión: {decision_pruned.reason}")

assert 0.0 <= decision_pruned.probability <= 1.0
assert decision_pruned.allowed is False, "Volatility 50 with weak score must be rejected"

# 4. Robustness against degenerate inputs (Vulnerability check)
print("\n4. Pruebas de Estrés y Vulnerabilidades (Degenerate Inputs):")

# Test 4.1: Missing signal fields
deg_sig = {}
decision_deg = engine.score_signal(
    symbol="EURUSD",
    signal=deg_sig,
    analysis={},
    market={},
    strategy_name="MALAYSIAN_SNR"
)
assert math.isfinite(decision_deg.probability)
assert math.isfinite(decision_deg.net_expectancy_r)
print("   [OK] Señal vacía manejada sin crash ni excepción no controlada.")

# Test 4.2: Extreme values (NaN, Inf, Overflow)
deg_extreme = {
    "entry_price": float("nan"),
    "risk_reward_ratio": float("inf"),
    "adx": -999.0
}
decision_extreme = engine.score_signal(
    symbol="EURUSD",
    signal=deg_extreme,
    analysis={"atr": float("nan")},
    market={"planned_rr": float("nan")},
    strategy_name="MALAYSIAN_SNR"
)
assert math.isfinite(decision_extreme.probability)
assert math.isfinite(decision_extreme.net_expectancy_r)
print("   [OK] Valores extremos/NaN manejados sin propagar excepciones numéricas.")

# 5. Check dashboard account payload integration
print("\n5. Integración con Dashboard Account Payload:")
repo = TradingRepository()
payload = build_account_payload(repo, source="DEMO")
by_worker = payload.get("meta_labeling", {}).get("by_worker", [])
msnr_worker = next((w for w in by_worker if w.get("worker") == "MALAYSIAN_SNR"), None)

assert msnr_worker is not None, "MALAYSIAN_SNR worker missing in account payload"
print(f"   - Worker: {msnr_worker.get('worker')}")
print(f"   - Model Strategy: {msnr_worker.get('model_strategy')}")
print(f"   - Model Samples: {msnr_worker.get('model_samples')}")
print(f"   - Positive Rate: {msnr_worker.get('model_positive_rate')}")
print(f"   - Family: {msnr_worker.get('family')}")
print(f"   - In Disk: {msnr_worker.get('in_disk')}")
print(f"   - Trained: {msnr_worker.get('trained')}")

assert msnr_worker.get("model_strategy") == "MALAYSIAN_SNR"
assert msnr_worker.get("trained") is True
assert msnr_worker.get("in_disk") is True

print("\n" + "=" * 60)
print("TODAS LAS PRUEBAS DE VULNERABILIDAD Y CONSISTENCIA PASARON AL 100%")
print("=" * 60)
