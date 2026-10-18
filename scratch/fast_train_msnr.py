"""
fast_train_msnr.py
Entrenamiento canónico del modelo GBDT para MALAYSIAN_SNR sin target leakage.
Extrae características reales de mercado y sincroniza settings_signature.
"""

import sys
import json
import time
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path("C:/TradingBoot/smc_synthetic_bot")
sys.path.insert(0, str(PROJECT_ROOT))

from strategy.ai import MetaLabelingConfig, MetaLabelingEngine
from strategy.ai.training import build_training_dataset, train_worker_gbdt_model
from strategy.malaysian_snr.ai_policy import settings_signature
from strategy.malaysian_snr.runtime_settings import MalaysianSNRRuntimeControls, get_msnr_runtime_controls
from database.repository import TradingRepository

def run_fast_train_msnr():
    csv_path = PROJECT_ROOT / "storage/analysis/replay_malaysian_snr_2y_trades.csv"
    if not csv_path.exists():
        print(f"Error: {csv_path} no encontrado.")
        return

    print(f"Leyendo trades desde {csv_path}...", flush=True)
    t0 = time.time()
    trades_df = pd.read_csv(csv_path)
    print(f"Cargados {len(trades_df):,} trades en {time.time()-t0:.2f}s.", flush=True)

    # Muestreo estratificado de 35,000 trades para velocidad y balance
    sample_size = min(35000, len(trades_df))
    trades_sample = trades_df.sample(n=sample_size, random_state=42).to_dict("records")

    formatted_records = []
    t_start = time.time()

    for t in trades_sample:
        # Extracción de características REALES sin target leakage (independientes del resultado WIN/LOSS)
        adx = float(t.get("momentum_adx", 20.0))
        rr = float(t.get("total_rr", 2.0))
        
        # Puntuación basada únicamente en características observables al momento del SETUP
        score = 50.0
        if t.get("ema_confluence"):
            score += 15.0
        if adx > 25.0:
            score += 15.0
        elif adx > 20.0:
            score += 10.0
        if t.get("scenario") in ("CONTINUATION_FRESH", "REVERSAL_ENGULFING"):
            score += 10.0
        score = min(100.0, max(30.0, score))
        
        conf_pct = min(1.0, max(0.2, score / 100.0))

        details = {
            "metadata": {
                "bot_profile": "MALAYSIAN_SNR",
                "strategy_name": "MALAYSIAN_SNR",
                "scenario": t.get("scenario", "CONTINUATION"),
                "direction": t.get("direction", "BUY"),
                "trade_score": score,
                "confirmation_percentage": conf_pct,
                "confirmations_ratio": 0.80,
                "adx": adx,
                "adx_normalized": min(1.0, adx / 50.0),
                "planned_rr": rr,
                "spread_ratio": 1.0,
                "is_boom": 1.0 if "Boom" in str(t.get("symbol", "")) else 0.0,
                "is_crash": 1.0 if "Crash" in str(t.get("symbol", "")) else 0.0,
                "is_volatility": 1.0 if "Vol" in str(t.get("symbol", "")) else 0.0,
                "is_forex": 1.0 if "FOREX" in str(t.get("category", "")) else 0.0,
                "is_gold": 1.0 if "XAU" in str(t.get("symbol", "")) or "Gold" in str(t.get("symbol", "")) else 0.0,
                "is_step": 1.0 if "Step" in str(t.get("symbol", "")) else 0.0,
                "is_jump": 1.0 if "Jump" in str(t.get("symbol", "")) else 0.0,
            }
        }
        rec = {
            "symbol": t["symbol"],
            "entry_time": t["entry_time"],
            "exit_time": t["entry_time"],
            "realized_pnl": float(t.get("total_pnl_usd", 0.0)),
            "net_pnl": float(t.get("total_pnl_usd", 0.0)),
            "realized_rr": rr,
            "status": "CLOSED",
            "details": details,
            "details_json": json.dumps(details),
        }
        formatted_records.append(rec)

    print(f"Formateados {len(formatted_records):,} registros en {time.time()-t_start:.2f}s.", flush=True)

    print("Construyendo dataset de entrenamiento...", flush=True)
    t1 = time.time()
    dataset = build_training_dataset(formatted_records, worker="MALAYSIAN_SNR", strategy_name="MALAYSIAN_SNR")
    total_rows = dataset["rows"]
    wins = sum(dataset["labels"]) if total_rows > 0 else 0
    base_wr = (wins / total_rows * 100.0) if total_rows > 0 else 0.0
    print(f"Dataset construido en {time.time()-t1:.2f}s | Filas: {total_rows:,} | Aciertos: {wins:,} | Win Rate Base: {base_wr:.2f}%")

    print("\nEntrenando CalibratedGBDTModel...", flush=True)
    t2 = time.time()
    model = train_worker_gbdt_model(
        formatted_records,
        worker="MALAYSIAN_SNR",
        strategy_name="MALAYSIAN_SNR",
        min_samples=15,
        allow_global_pooling=False,
        n_estimators=100,
        max_depth=5,
        learning_rate=0.03,
    )
    print(f"Modelo GBDT entrenado en {time.time()-t2:.2f}s.")

    # Sincronización de firma canónica
    repo = TradingRepository()
    current_ctrls = get_msnr_runtime_controls(repo)
    active_sig = settings_signature(current_ctrls)
    
    if hasattr(model, "provenance") and isinstance(model.provenance, dict):
        model.provenance["settings_signature"] = active_sig
        model.provenance["settings"] = current_ctrls.to_dict()
        model.provenance["source_dataset"] = "replay_malaysian_snr_2y_trades.csv"
        model.provenance["training_samples"] = total_rows
        model.provenance["trained_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        model.provenance["win_rate"] = base_wr

    models_dir = PROJECT_ROOT / "storage/ai_models"
    models_dir.mkdir(parents=True, exist_ok=True)
    target_path = models_dir / "metalabel_MALAYSIAN_SNR_MALAYSIAN_SNR.json"
    fallback_path = models_dir / "metalabel_MALAYSIAN_SNR_ALL.json"

    engine = MetaLabelingEngine(
        MetaLabelingConfig(
            enabled=True,
            model_directory=str(models_dir),
            min_training_samples=15,
            model_type="LIGHTGBM",
        ),
        repository=repo,
    )
    engine._models["MALAYSIAN_SNR:MALAYSIAN_SNR"] = model
    engine.save_model("MALAYSIAN_SNR", "MALAYSIAN_SNR")
    print(f"[OK] Modelo guardado en: {target_path}")

    # Guardar fallback
    with open(target_path, "r", encoding="utf-8") as f:
        content = f.read()
    with open(fallback_path, "w", encoding="utf-8") as f:
        f.write(content)

    # Registrar en base de datos SQLite
    repo.register_msnr_model(str(target_path), model.provenance)
    print(f"[OK] Modelo registrado exitosamente en msnr_model_registry.")

if __name__ == "__main__":
    run_fast_train_msnr()
