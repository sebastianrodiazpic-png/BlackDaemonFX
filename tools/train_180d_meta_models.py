"""Re-entrenamiento de Meta-Modelos de IA con Dataset de Replay 180 Días.

Incorpora:
1. Registros históricos del repositorio SQLite (DEMO).
2. Operaciones históricas del replay 180 días (STEP, VOLATILITY, JUMP).
3. 44 Variables predictivas clave:
   - adx_regime (ADX >= 20)
   - signal_age_penalty
   - spread_to_sl_ratio
   - session_killzone_active
   - is_boom, is_crash, is_volatility, is_forex, is_gold, is_step, is_jump
4. Estabilización numérica: gradient clipping y regularización L2.
5. Calibración isotónica walk-forward out-of-sample.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone
import json
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Windows UTF-8 configuration
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from database.repository import TradingRepository
from strategy.ai.training import (
    build_training_dataset,
    train_worker_model,
    temporal_validation,
)
from strategy.ai.meta_labeling import MetaLabelingEngine, MetaLabelingConfig


def build_unified_trade_records():
    """Unifica operaciones del journal SQLite y del replay histórico 180 días."""
    repo = TradingRepository()
    db_df = repo.trades_dataframe(source="DEMO")
    db_records = db_df.to_dict("records") if db_df is not None and not db_df.empty else []
    print(f"Operaciones cargadas de SQLite DEMO: {len(db_records)}")

    replay_files = [
        (PROJECT_ROOT / "storage" / "analysis" / "replay_step_vol_jump_180d_trades.csv", 200000),
        (PROJECT_ROOT / "storage" / "analysis" / "replay_boom_crash_forex_gold_180d_trades.csv", 300000),
        (PROJECT_ROOT / "storage" / "analysis" / "replay_orb_12m_trades.csv", 400000),
    ]
    replay_records = []
    for replay_path, base_id in replay_files:
        if not replay_path.exists():
            continue
        replay_df = pd.read_csv(replay_path)
        print(f"Operaciones cargadas de {replay_path.name}: {len(replay_df)}")

        for idx, row in replay_df.iterrows():
            if str(row.get("be_result") or "").upper() == "OPEN":
                continue

            family = str(row["family"]).upper()
            if family == "VOLATILITY" and (PROJECT_ROOT / "storage" / "analysis" / "volatility_workers_2y_smc_trades.csv").exists():
                continue
            if family in {"STEP", "JUMP"} and (PROJECT_ROOT / "storage" / "analysis" / "step_jump_workers_2y_smc_trades.csv").exists():
                continue
            if family in {"ORB", "GOLD"} and (PROJECT_ROOT / "storage" / "analysis" / "historical_trades_optimized.csv").exists():
                continue
            direction = str(row["direction"]).upper()
            symbol = str(row["symbol"])
            entry_time = str(row["entry_time"])
            exit_time = str(row.get("direct_exit_time") or entry_time)
            adx = float(row.get("adx") or 20.0)
            atr = float(row.get("atr") or 1.0)
            entry_price = float(row.get("entry_price") or 0.0)
            stop_loss = float(row.get("stop_loss") or 0.0)
            take_profit = float(row.get("take_profit") or 0.0)

            # Asymmetric double leg for Boom 300 / Crash 500, dynamic BE for others
            if symbol in {"Boom 300 Index", "Crash 500 Index"} and pd.notna(row.get("asym_realized_rr")):
                realized_rr = float(row.get("asym_realized_rr"))
            else:
                realized_rr = float(
                    row.get("be_realized_rr")
                    if pd.notna(row.get("be_realized_rr"))
                    else row.get("direct_realized_rr") or 0.0
                )
            result = "WIN" if realized_rr > 0 else "LOSS"

            if family == "ORB":
                strategy_name = "ORB_NEW_YORK"
                meta = {
                    "bot_profile": "ORB",
                    "worker": "ORB",
                    "strategy_name": "ORB_NEW_YORK",
                    "symbol": symbol,
                    "direction": direction,
                    "entry_price": entry_price,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "adx": adx,
                    "atr": atr,
                    "trade_score": 85.0 if realized_rr > 0 else 70.0,
                    "confirmation_percentage": 85.0 if realized_rr > 0 else 70.0,
                    "confirmations": {
                        "vwap_alignment": bool(row.get("vwap_alignment", True)),
                        "poc_alignment": bool(row.get("poc_alignment", True)),
                        "breakout_volume_confirmed": bool(row.get("breakout_volume_confirmed", True)),
                    },
                    "opening_range_atr_ratio": float(row.get("opening_range_atr_ratio") or 1.2),
                    "breakout_volume_ratio": float(row.get("breakout_volume_ratio") or 1.0),
                    "operation_risk_percent": 1.0,
                }
            else:
                strategy_name = "GOLD_QUARTERS" if family == "GOLD" else "SMC"
                meta = {
                    "bot_profile": family,
                    "strategy_name": strategy_name,
                    "symbol": symbol,
                    "direction": direction,
                    "entry_price": entry_price,
                    "stop_loss": stop_loss,
                    "take_profit": take_profit,
                    "adx": adx,
                    "atr": atr,
                    "trade_score": 85.0 if realized_rr > 0 else 70.0,
                    "confirmation_percentage": 80.0 if realized_rr > 0 else 65.0,
                    "confirmations": {"fvg": True, "bos": True},
                    "m15_structure_break_type": "BOS_BULLISH" if direction == "BUY" else "BOS_BEARISH",
                    "structure_break": "BOS_BULLISH" if direction == "BUY" else "BOS_BEARISH",
                    "operation_risk_percent": 1.0,
                }

            replay_records.append({
                "id": base_id + idx,
                "execution_key": f"REPLAY_{family}_{base_id}_{idx}",
                "instrument": symbol,
                "direction": direction,
                "status": "CLOSED",
                "result": result,
                "entry_time": entry_time,
                "exit_time": exit_time,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "realized_rr": realized_rr,
                "net_pnl": realized_rr * 10.0,
                "planned_rr": 2.5,
                "risk_percent": 1.0,
                "details": {"metadata": meta},
            })

    vol_2y_path = PROJECT_ROOT / "storage" / "analysis" / "volatility_workers_2y_smc_trades.csv"
    if vol_2y_path.exists():
        vol_df = pd.read_csv(vol_2y_path)
        print(f"Operaciones cargadas de {vol_2y_path.name}: {len(vol_df)}")
        for idx, row in vol_df.iterrows():
            if str(row.get("trade1_result") or "").upper() == "OPEN":
                continue
            worker_name = str(row.get("worker") or "VOLATILITY_1")
            direction = str(row["direction"]).upper()
            symbol = str(row["symbol"])
            entry_time = str(row["entry_time"])
            exit_time = str(row.get("trade1_exit_time") or entry_time)
            adx = float(row.get("adx") or 20.0)
            atr = float(row.get("atr") or 1.0)
            entry_price = float(row.get("entry_price") or 0.0)
            stop_loss = float(row.get("stop_loss") or 0.0)
            take_profit = float(row.get("tp2_3r_price") or row.get("tp1_price") or 0.0)
            smc_score = float(row.get("smc_score") or 80.0)
            realized_rr = float(
                row.get("combined_3r_pct")
                if pd.notna(row.get("combined_3r_pct"))
                else (row.get("trade1_realized_r") or 0.0)
            )
            result = "WIN" if realized_rr > 0 else "LOSS"
            meta = {
                "bot_profile": worker_name,
                "worker": worker_name,
                "strategy_name": "SMC",
                "symbol": symbol,
                "direction": direction,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "adx": adx,
                "atr": atr,
                "trade_score": smc_score,
                "confirmation_percentage": smc_score,
                "confirmations": {"fvg": True, "bos": True, "liquidity": True},
                "m15_structure_break_type": "BOS_BULLISH" if direction == "BUY" else "BOS_BEARISH",
                "structure_break": "BOS_BULLISH" if direction == "BUY" else "BOS_BEARISH",
                "operation_risk_percent": 1.0,
            }
            replay_records.append({
                "id": 500000 + idx,
                "execution_key": f"REPLAY_VOL2Y_{worker_name}_{idx}",
                "instrument": symbol,
                "direction": direction,
                "status": "CLOSED",
                "result": result,
                "entry_time": entry_time,
                "exit_time": exit_time,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "realized_rr": realized_rr,
                "net_pnl": realized_rr * 10.0,
                "planned_rr": 2.5,
                "risk_percent": 1.0,
                "details": {"metadata": meta},
            })

    step_jump_2y_path = PROJECT_ROOT / "storage" / "analysis" / "step_jump_workers_2y_smc_trades.csv"
    if step_jump_2y_path.exists():
        sj_df = pd.read_csv(step_jump_2y_path)
        print(f"Operaciones cargadas de {step_jump_2y_path.name}: {len(sj_df)}")
        for idx, row in sj_df.iterrows():
            if str(row.get("trade1_result") or "").upper() == "OPEN":
                continue
            worker_name = str(row.get("worker") or "STEP")
            direction = str(row["direction"]).upper()
            symbol = str(row["symbol"])
            entry_time = str(row["entry_time"])
            exit_time = str(row.get("trade1_exit_time") or entry_time)
            adx = float(row.get("adx") or 20.0)
            atr = float(row.get("atr") or 1.0)
            entry_price = float(row.get("entry_price") or 0.0)
            stop_loss = float(row.get("stop_loss") or 0.0)
            take_profit = float(row.get("tp2_3r_price") or row.get("tp1_price") or 0.0)
            smc_score = float(row.get("smc_score") or 80.0)
            raw_score = float(row.get("raw_trade_score") or smc_score)
            conf_pct = float(row.get("confirmation_percentage") or smc_score)
            structure_break = str(row.get("structure_break_type") or ("BOS_BULLISH" if direction == "BUY" else "BOS_BEARISH"))
            realized_rr = float(
                row.get("combined_3r_pct")
                if pd.notna(row.get("combined_3r_pct"))
                else (row.get("trade1_realized_r") or 0.0)
            )
            result = "WIN" if realized_rr > 0 else "LOSS"
            meta = {
                "bot_profile": worker_name,
                "worker": worker_name,
                "strategy_name": "SMC",
                "symbol": symbol,
                "direction": direction,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "adx": adx,
                "atr": atr,
                "trade_score": raw_score,
                "confirmation_percentage": conf_pct,
                "confirmations": {
                    "fvg": bool(row.get("fvg_confirmed", 1)),
                    "bos": "bos" in structure_break.lower(),
                    "choch": "choch" in structure_break.lower(),
                    "volume": bool(row.get("volume_confirmed", 1)),
                },
                "m15_structure_break_type": structure_break,
                "structure_break": structure_break,
                "operation_risk_percent": 1.0,
            }
            replay_records.append({
                "id": 600000 + idx,
                "execution_key": f"REPLAY_STEPJUMP2Y_{worker_name}_{idx}",
                "instrument": symbol,
                "direction": direction,
                "status": "CLOSED",
                "result": result,
                "entry_time": entry_time,
                "exit_time": exit_time,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "realized_rr": realized_rr,
                "net_pnl": realized_rr * 10.0,
                "planned_rr": 2.5,
                "risk_percent": 1.0,
                "details": {"metadata": meta},
            })

    gold_orb_2y_path = PROJECT_ROOT / "storage" / "analysis" / "historical_trades_optimized.csv"
    if gold_orb_2y_path.exists():
        go_df = pd.read_csv(gold_orb_2y_path)
        print(f"Operaciones cargadas de {gold_orb_2y_path.name}: {len(go_df)}")
        for idx, row in go_df.iterrows():
            strat = str(row.get("strategy") or "ORB_NEW_YORK")
            worker_name = "GOLD" if strat == "GOLD_QUARTERS" else "ORB"
            direction = str(row["direction"]).upper()
            symbol = str(row["symbol"])
            entry_time = str(row["entry_time"])
            exit_time = str(row.get("leg2_exit_time") or row.get("leg1_exit_time") or entry_time)
            entry_price = float(row.get("entry_price") or 0.0)
            stop_loss = float(row.get("stop_loss") or 0.0)
            take_profit = float(row.get("tp2_target") or row.get("tp1_target") or 0.0)
            realized_rr = float(row.get("combined_rr") or 0.0)
            total_pnl = float(row.get("total_pnl_usd") or (realized_rr * 10.0))
            is_win = bool(row.get("is_win", False))
            result = "WIN" if is_win or realized_rr > 0 else "LOSS"
            meta = {
                "bot_profile": worker_name,
                "worker": worker_name,
                "strategy_name": strat,
                "symbol": symbol,
                "direction": direction,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "spread": float(row.get("spread") or 0.0),
                "risk_distance": float(row.get("risk_distance") or abs(entry_price - stop_loss)),
                "trade_score": 85.0 if result == "WIN" else 70.0,
                "confirmation_percentage": 85.0 if result == "WIN" else 70.0,
                "confirmations": {"quarter_rejection": True, "m5_confirmation": True} if strat == "GOLD_QUARTERS" else {"breakout_volume_confirmed": True, "vwap_alignment": True},
                "structure_break": "BOS_BULLISH" if direction == "BUY" else "BOS_BEARISH",
                "operation_risk_percent": 1.0,
            }
            replay_records.append({
                "id": 700000 + idx,
                "execution_key": f"REPLAY_GOLD_ORB_2Y_{worker_name}_{idx}",
                "instrument": symbol,
                "direction": direction,
                "status": "CLOSED",
                "result": result,
                "entry_time": entry_time,
                "exit_time": exit_time,
                "entry_price": entry_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "realized_rr": realized_rr,
                "net_pnl": total_pnl,
                "planned_rr": float(row.get("target_rr_2") or 2.5),
                "risk_percent": 1.0,
                "details": {"metadata": meta},
            })

    all_records = db_records + replay_records
    print(f"Total registros consolidados para entrenamiento: {len(all_records)}")
    return all_records


def train_and_sync_all_models():
    """Entrena y sincroniza modelos de IA en storage/ai_models/."""
    all_records = build_unified_trade_records()
    models_dir = PROJECT_ROOT / "storage" / "ai_models"
    models_dir.mkdir(parents=True, exist_ok=True)

    workers = [
        "GLOBAL",
        "STEP",
        "JUMP",
        "VOLATILITY",
        "BOOM",
        "CRASH",
        "FOREX",
        "GOLD",
        "ORB",
    ]

    summary_rows = []

    print("\n" + "=" * 95)
    print("INICIANDO ENTRENAMIENTO DE META-MODELOS DE IA (SMC META-LABELING)")
    print("=" * 95)

    for worker in workers:
        engine = MetaLabelingEngine(
            MetaLabelingConfig(
                enabled=True,
                model_directory=str(models_dir),
                min_training_samples=15,
            ),
            worker=worker,
        )

        dataset = build_training_dataset(all_records, worker=worker)
        total_rows = dataset["rows"]
        wins = sum(dataset["labels"]) if total_rows > 0 else 0
        losses = total_rows - wins
        win_rate = round(wins / total_rows * 100, 1) if total_rows > 0 else 0.0

        model = train_worker_model(
            all_records,
            worker=worker,
            min_samples=15,
            allow_global_pooling=True,
        )
        model.worker = worker
        model.strategy_name = "ALL"

        saved_path = engine.save_model(model)

        val = temporal_validation(all_records, worker=worker)

        summary_rows.append({
            "worker": worker,
            "samples": model.model.samples,
            "dataset_rows": total_rows,
            "wins": wins,
            "losses": losses,
            "win_rate": win_rate,
            "trained": model.trained,
            "val_accuracy": round(val.accuracy * 100, 1) if val.samples_evaluated > 0 else 0.0,
            "val_brier": round(val.brier_score, 3) if val.samples_evaluated > 0 else 1.0,
            "val_lift": round(val.lift, 3) if val.samples_evaluated > 0 else 0.0,
            "avg_win_rr": round(model.average_win_rr, 2),
            "avg_loss_rr": round(model.average_loss_rr, 2),
            "bias": round(model.model.bias, 4),
            "saved_path": saved_path,
        })

    # Imprimir Tabla Resumen
    print(f"{'WORKER':<12} | {'MUESTRAS':<8} | {'WIN RATE':<9} | {'ESTADO':<10} | {'ACCURACY':<9} | {'BRIER':<6} | {'AVG WIN/LOSS RR'}")
    print("-" * 95)
    for r in summary_rows:
        estado = "ENTRENADO" if r["trained"] else "INSUFICIENTE"
        wr_str = f"{r['win_rate']:.1f}%"
        acc_str = f"{r['val_accuracy']:.1f}%" if r["val_accuracy"] > 0 else "N/A"
        brier_str = f"{r['val_brier']:.3f}"
        win_loss_str = f"+{r['avg_win_rr']}R / -{r['avg_loss_rr']}R"
        print(f"{r['worker']:<12} | {r['samples']:<8} | {wr_str:<9} | {estado:<10} | {acc_str:<9} | {brier_str:<6} | {win_loss_str}")
    print("=" * 95)

    return summary_rows


if __name__ == "__main__":
    train_and_sync_all_models()
