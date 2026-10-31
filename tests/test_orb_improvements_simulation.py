"""Unit tests verifying the quantitative improvements and integrity of ORB NY simulation."""
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[1]
RESULTS_PATH = ROOT / "storage" / "analysis" / "orb_improvements_simulation_results.json"
REPORT_PATH = ROOT / "storage" / "analysis" / "orb_improvements_simulation_report.md"


def test_orb_simulation_artifacts_exist():
    assert RESULTS_PATH.exists(), "orb_improvements_simulation_results.json must exist"
    assert REPORT_PATH.exists(), "orb_improvements_simulation_report.md must exist"


def test_orb_simulation_elite_model_outperforms_baseline():
    data = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    
    baseline = data["M1_BASELINE_ACTUAL"]["global_metrics"]
    elite = data["M3_MODELO_ELITE_5_CORE"]["global_metrics"]
    
    # 1. Total R must be strictly higher in the Elite Model
    assert elite["total_r"] > baseline["total_r"], "Elite model must generate higher net R than baseline"
    assert elite["total_r"] >= 50.0, f"Expected >= 50 R, got {elite['total_r']}"
    
    # 2. Trade count must be significantly higher (unblocking valid setups)
    assert elite["n"] > baseline["n"] * 1.5, "Trade frequency must increase by at least 50%"
    
    # 3. Win rate must remain high (> 50%)
    assert elite["win_rate"] >= 53.0, f"Expected WR >= 53%, got {elite['win_rate']}%"
    
    # 4. Consistency in both halves (H1 and H2 strictly positive)
    assert elite["h1_r"] > 0, "Half 1 must be positive"
    assert elite["h2_r"] > 0, "Half 2 must be positive"


def test_orb_simulation_toxic_assets_isolated():
    data = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    m2_breakdown = data["M2_DESCUBRIMIENTO_PLENO_TODOS"]["asset_breakdown"]
    
    # US Oil and USDCHF are toxic in unconstrained sweep
    assert m2_breakdown["US Oil"]["total_r"] < 0, "US Oil must be negative in pure sweep"
    assert m2_breakdown["USDCHF"]["total_r"] < 0, "USDCHF must be negative in pure sweep"
    
    # The 5 Core assets in M3 must all be profitable
    m3_breakdown = data["M3_MODELO_ELITE_5_CORE"]["asset_breakdown"]
    for asset in ["BTCUSD", "XAUUSD", "USDCAD", "GBPUSD", "AUDUSD"]:
        assert m3_breakdown[asset]["total_r"] > 0, f"{asset} must have positive net R in elite model"
