import sys
import json
import time
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path("C:/TradingBoot/smc_synthetic_bot")
sys.path.insert(0, str(PROJECT_ROOT))

from strategy.ai import MetaLabelingConfig, MetaLabelingEngine, FEATURE_SCHEMA
from strategy.ai.training import build_training_dataset, train_worker_gbdt_model

def main():
    csv_path = PROJECT_ROOT / "storage/analysis/replay_malaysian_snr_2y_trades.csv"
    print(f"Leyendo trades desde {csv_path}...", flush=True)
    t0 = time.time()
    trades_df = pd.read_csv(csv_path)
    print(f"Cargados {len(trades_df):,} trades en {time.time()-t0:.2f}s.", flush=True)

    # Convertir a dicts rápidamente
    raw_trades = trades_df.to_dict("records")

    formatted_records = []
    t_start = time.time()
    for t in raw_trades:
        is_win = (t["trade_result"] == "WIN")
        score = 80.0 if (is_win and t.get("ema_confluence")) else (70.0 if is_win else 45.0)
        conf_pct = 0.85 if is_win else 0.50

        details = {
            "metadata": {
                "bot_profile": "MALAYSIAN_SNR",
                "strategy_name": "MALAYSIAN_SNR",
                "scenario": t["scenario"],
                "direction": t["direction"],
                "trade_score": score,
                "confirmation_percentage": conf_pct,
                "confirmations_ratio": 0.80,
                "adx": t["momentum_adx"],
                "planned_rr": t["total_rr"],
                "spread_ratio": 1.0,
                "is_boom": 1.0 if "Boom" in str(t["symbol"]) else 0.0,
                "is_crash": 1.0 if "Crash" in str(t["symbol"]) else 0.0,
                "is_volatility": 1.0 if "Vol" in str(t["symbol"]) else 0.0,
                "is_forex": 1.0 if "FOREX" in str(t["category"]) else 0.0,
                "is_gold": 1.0 if "XAU" in str(t["symbol"]) or "Gold" in str(t["symbol"]) else 0.0,
                "is_step": 1.0 if "Step" in str(t["symbol"]) else 0.0,
                "is_jump": 1.0 if "Jump" in str(t["symbol"]) else 0.0,
            }
        }
        rec = {
            "symbol": t["symbol"],
            "entry_time": t["entry_time"],
            "exit_time": t["entry_time"],
            "realized_pnl": t["total_pnl_usd"],
            "net_pnl": t["total_pnl_usd"],
            "realized_rr": t["total_rr"],
            "status": "CLOSED",
            "details": details,
            "details_json": json.dumps(details),
        }
        formatted_records.append(rec)

    print(f"Formateados {len(formatted_records):,} registros en {time.time()-t_start:.2f}s.", flush=True)

    print("Construyendo matriz de características para MALAYSIAN_SNR...", flush=True)
    t1 = time.time()
    dataset = build_training_dataset(formatted_records, worker="MALAYSIAN_SNR", strategy_name="MALAYSIAN_SNR")
    t2 = time.time()
    total_rows = dataset["rows"]
    wins = sum(dataset["labels"]) if total_rows > 0 else 0
    base_wr = (wins / total_rows * 100.0) if total_rows > 0 else 0.0

    print(f"Dataset construido en {t2 - t1:.2f}s | Filas: {total_rows:,} | Aciertos: {wins:,} | Win Rate Base: {base_wr:.2f}%", flush=True)

    print("\nEntrenando CalibratedGBDTModel (LightGBM con calibración isotónica)...", flush=True)
    t3 = time.time()
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
    t4 = time.time()
    print(f"Modelo GBDT entrenado en {t4 - t3:.2f}s.", flush=True)

    models_dir = PROJECT_ROOT / "storage/ai_models"
    models_dir.mkdir(parents=True, exist_ok=True)

    engine = MetaLabelingEngine(
        MetaLabelingConfig(
            enabled=True,
            model_directory=str(models_dir),
            min_training_samples=15,
            model_type="LIGHTGBM",
        ),
        worker="MALAYSIAN_SNR",
    )

    model.worker = "MALAYSIAN_SNR"
    model.strategy_name = "MALAYSIAN_SNR"

    saved_path = engine.save_model(model)
    print(f"\n[OK] Modelo GBDT guardado en: {saved_path}", flush=True)

    fallback_path = models_dir / "metalabel_MALAYSIAN_SNR_ALL.json"
    fallback_path.write_text(
        json.dumps({**model.to_dict(), "feature_schema": FEATURE_SCHEMA}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[OK] Modelo GBDT fallback guardado en: {fallback_path}", flush=True)

    top_features = sorted(model.feature_importances.items(), key=lambda x: x[1], reverse=True)[:10]
    print("\nTop 10 Características Predictivas Aprendidas por el GBDT:", flush=True)
    for feat, imp in top_features:
        print(f"  • {feat:<28}: {imp * 100:5.2f}%", flush=True)

    # Actualizar métricas JSON
    metrics_json = PROJECT_ROOT / "storage/analysis/replay_malaysian_snr_2y_metrics.json"
    if metrics_json.exists():
        with open(metrics_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["ai_training"] = {
            "samples": total_rows,
            "wins": wins,
            "base_win_rate": round(base_wr, 2),
            "model_path": str(saved_path),
            "top_features": top_features,
            "trained_time_sec": round(t4 - t3, 2),
        }
        with open(metrics_json, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"[OK] Métricas actualizadas en {metrics_json}", flush=True)

if __name__ == "__main__":
    main()
