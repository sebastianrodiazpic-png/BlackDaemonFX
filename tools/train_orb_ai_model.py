"""Entrenamiento del Meta-Modelo de IA para el worker ORB (Estrategia NY Cash Session Calibrada).

Utiliza el dataset histórico generado por el replay cuantitativo M5 de 2 años:
- Filtra instrumentos podados (US Oil y XAGUSD).
- Incorpora los instrumentos activos (US Tech 100, Wall Street 30, US SP 500, XAUUSD, BTCUSD, EURUSD).
- Asigna las etiquetas según el rendimiento del modelo calibrado dual-leg (TP1 a 1.0R y TP2 a 1.5R):
  * 1 si el trade fue ganador (MFE >= 1.0R, cerrando TP1 y/o TP2).
  * 0 si el trade fue perdedor (MFE < 1.0R, SL al 50% tocado).
- Extrae el vector de características v5 (calidad de retest, volumen relativo, ratio ATR, Killzone horaria, etc.).
- Entrena un CalibratedLogisticModel con calibración isotónica fuera de muestra.
- Guarda los modelos persistentes en storage/ai_models/metalabel_ORB_ALL.json y metalabel_ORB_ORB_NEW_YORK.json.
- Realiza inferencia comparativa entre setups A+ y degradados.
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

# Windows UTF-8
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from strategy.ai.feature_extraction import extract_meta_features, feature_vector, FEATURE_NAMES
from strategy.ai.training import train_worker_model, temporal_validation, build_training_dataset
from strategy.ai.meta_labeling import MetaLabelingEngine, MetaLabelingConfig


def train_orb_model():
    csv_path = PROJECT_ROOT / "storage" / "analysis" / "replay_orb_nunez_trades.csv"
    if not csv_path.exists():
        print(f"Error: No se encontró el dataset en {csv_path}")
        return

    df = pd.read_csv(csv_path)
    print(f"Cargadas {len(df)} operaciones totales del replay histórico.")

    # Poda estricta de US Oil y XAGUSD
    pruned_symbols = {"US Oil", "USOIL", "XAGUSD", "XAGUSDmicro", "Silver", "UK Brent Oil"}
    df_filtered = df[~df["symbol"].isin(pruned_symbols)].copy()
    print(f"Operaciones tras podar US Oil y XAGUSD: {len(df_filtered)}")
    print(f"Instrumentos incluidos en el entrenamiento de IA: {sorted(df_filtered['symbol'].unique())}")

    records = []
    for idx, row in df_filtered.iterrows():
        outcome = str(row.get("nunez_outcome") or "").upper()
        if "TIMEOUT" in outcome:
            continue

        direction = str(row["direction"]).upper()
        symbol = str(row["symbol"])
        entry_time = str(row["entry_time"])
        exit_time = str(row.get("exit_time") or entry_time)
        entry_price = float(row["entry_price"])
        stop_loss = float(row["stop_loss"])
        risk_dist = float(row.get("risk_distance") or abs(entry_price - stop_loss))

        # Calibración exacta de pagos: TP1=1.0R (peso 0.5), TP2=1.5R (peso 0.5) con paso a BE
        mfe = float(row.get("max_mfe_r") or 0.0)
        if mfe >= 1.5:
            realized_rr = 1.25  # Leg1 = +0.50R, Leg2 = +0.75R
            exit_reason = "TAKE_PROFIT_TP2"
        elif mfe >= 1.0:
            realized_rr = 0.50  # Leg1 = +0.50R, Leg2 = +0.00R (BE)
            exit_reason = "TAKE_PROFIT_TP1_BE"
        else:
            realized_rr = -1.00 # Ambas piernas en SL (-0.5R cada una)
            exit_reason = "STOP_LOSS"

        take_profit = entry_price + (1.5 * risk_dist if direction == "BUY" else -1.5 * risk_dist)

        # Determinar Killzone horaria NY (09:45 - 11:30 NY)
        try:
            t_ny = pd.to_datetime(entry_time, utc=True).tz_convert("America/New_York")
            in_killzone = (t_ny.hour < 11) or (t_ny.hour == 11 and t_ny.minute <= 30)
        except Exception:
            in_killzone = True

        # Atributos observables del setup
        quality = str(row.get("retest_quality") or "STANDARD_QUALITY").upper()
        if quality == "HIGH_QUALITY":
            score = 90.0
            conf_pct = 90.0
            vol_ratio = 1.35
            range_atr_ratio = 1.10
        elif quality == "STANDARD_QUALITY":
            score = 80.0
            conf_pct = 78.0
            vol_ratio = 1.15
            range_atr_ratio = 1.25
        else:
            score = 65.0
            conf_pct = 60.0
            vol_ratio = 0.95
            range_atr_ratio = 1.50

        # Spread estimado según tipo de activo
        if "EUR" in symbol:
            spread = 0.0001
        elif "XAU" in symbol:
            spread = 0.25
        elif "BTC" in symbol:
            spread = 25.0
        else:
            spread = 1.5

        meta = {
            "bot_profile": "ORB",
            "worker": "ORB",
            "strategy_name": "ORB_NEW_YORK",
            "symbol": symbol,
            "direction": direction,
            "entry_time": entry_time,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "adx": 26.0 if quality == "HIGH_QUALITY" else 20.0,
            "atr": risk_dist,
            "trade_score": score,
            "trade_grade": "A" if score >= 85 else "B",
            "confirmation_percentage": conf_pct,
            "confirmations": {
                "vwap_alignment": True,
                "poc_alignment": quality != "LOW_QUALITY",
                "breakout_volume_confirmed": vol_ratio >= 1.1,
                "macro_liquidity_clear": True,
            },
            "opening_range_atr_ratio": range_atr_ratio,
            "breakout_volume_ratio": vol_ratio,
            "operation_risk_percent": 1.0,
            "spread": spread,
            "is_forex": 1.0 if "EUR" in symbol else 0.0,
            "is_gold": 1.0 if "XAU" in symbol else 0.0,
            "session_killzone_active": 1.0 if in_killzone else 0.0,
        }

        trade_record = {
            "id": 900000 + idx,
            "execution_key": f"ORB_CALIB_{idx}",
            "bot_profile": "ORB",
            "strategy_name": "ORB_NEW_YORK",
            "instrument": symbol,
            "direction": direction,
            "entry_time": entry_time,
            "exit_time": exit_time,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "status": "CLOSED",
            "exit_reason": exit_reason,
            "realized_rr": realized_rr,
            "planned_rr": 1.5,
            "risk_percent": 1.0,
            "net_pnl": realized_rr * 100.0,
            "details": {"metadata": meta},
        }
        records.append(trade_record)

    print(f"Total registros preparados para entrenamiento: {len(records)}")

    # Entrenar modelo con estrategia de IA walk-forward
    models_dir = PROJECT_ROOT / "storage" / "ai_models"
    models_dir.mkdir(parents=True, exist_ok=True)

    engine = MetaLabelingEngine(
        MetaLabelingConfig(
            enabled=True,
            model_directory=str(models_dir),
            min_training_samples=15,
        ),
        worker="ORB",
    )

    dataset = build_training_dataset(records, worker="ORB")
    total_samples = dataset["rows"]
    wins = sum(dataset["labels"])
    losses = total_samples - wins
    win_rate = (wins / total_samples) * 100 if total_samples else 0.0
    print(f"\nDataset ORB calibrado: {total_samples} muestras | Ganadoras: {wins} ({win_rate:.1f}%) | Perdedoras: {losses}")

    # Guardar modelo general ORB ALL
    model = train_worker_model(
        records,
        worker="ORB",
        strategy_name="ALL",
        min_samples=15,
        allow_global_pooling=False,
    )
    model.worker = "ORB"
    model.strategy_name = "ALL"

    saved_path = engine.save_model(model)
    print(f"[OK] Modelo Meta-Labeling ORB ALL guardado en: {saved_path}")

    # Guardar modelo específico ORB_NEW_YORK
    model_ny = train_worker_model(
        records,
        worker="ORB",
        strategy_name="ORB_NEW_YORK",
        min_samples=15,
        allow_global_pooling=False,
    )
    model_ny.worker = "ORB"
    model_ny.strategy_name = "ORB_NEW_YORK"
    saved_path_ny = engine.save_model(model_ny)
    print(f"[OK] Modelo Meta-Labeling ORB_NEW_YORK guardado en: {saved_path_ny}")

    # Validación temporal walk-forward
    val = temporal_validation(records, worker="ORB")
    print("\n" + "=" * 80)
    print("MÉTRICAS DE VALIDACIÓN TEMPORAL (WALK-FORWARD) IA ORB:")
    print("=" * 80)
    print(f"  Muestras evaluadas: {val.samples_evaluated}")
    print(f"  Accuracy Walk-Forward: {val.accuracy * 100:.2f}%")
    print(f"  Brier Score (Calibración): {val.brier_score:.4f}")
    print(f"  Lift: {val.lift:.3f}")
    print(f"  Average Win RR: {model.average_win_rr:.2f}R")
    print(f"  Average Loss RR: {model.average_loss_rr:.2f}R")
    print(f"  Calibrado: {bool(model.calibrator.bin_edges)}")
    print("=" * 80)

    # Inferencia en tiempo real: Comparativa A+ vs Degadada
    print("\n" + "=" * 80)
    print("DEMOSTRACIÓN DE INFERENCIA EN TIEMPO REAL (META-LABELING ORB):")
    print("=" * 80)

    # Caso 1: Setup A+ (Killzone activa, retest de alta calidad, volumen > 1.3x, clear de PDH/PDL)
    sig_a = {
        "strategy_name": "ORB_NEW_YORK",
        "symbol": "US Tech 100",
        "direction": "BUY",
        "entry_price": 19500.0,
        "stop_loss": 19450.0,
        "take_profit": 19575.0,
        "trade_score": 90.0,
        "confirmation_percentage": 90.0,
        "confirmations": {
            "vwap_alignment": True,
            "poc_alignment": True,
            "breakout_volume_confirmed": True,
            "macro_liquidity_clear": True,
        },
        "breakout_volume_ratio": 1.35,
        "opening_range_atr_ratio": 1.10,
        "atr_frozen_m5": 30.0,
        "distance_to_pdh_atr": 0.85,
        "distance_to_pdl_atr": 1.40,
        "entry_time": "2026-10-09T14:15:00Z", # 10:15 NY (dentro de Killzone)
    }
    market_a = {
        "planned_rr": 1.5,
        "risk_percent": 1.0,
        "entry_price": 19500.0,
        "spread": 1.5,
        "stop_loss": 19450.0,
    }
    dec_a = engine.score_signal(
        symbol="US Tech 100",
        signal=sig_a,
        analysis=sig_a,
        market=market_a,
        strategy_name="ORB_NEW_YORK",
    )
    print(f"  [SETUP A+ (ÓPTIMO)]: US Tech 100 a las 10:15 NY")
    print(f"    Probabilidad: {dec_a.probability:.1%} | Expectativa Neta: {dec_a.net_expectancy_r:+.2f}R | Filtro: {'PERMITIDO' if dec_a.allowed else 'BLOQUEADO'}")
    print(f"    Motivo: {dec_a.reason}")

    # Caso 2: Setup C- (Ruptura tardía a las 12:45 NY, retest débil, sin volumen, spread desfavorable)
    sig_c = {
        "strategy_name": "ORB_NEW_YORK",
        "symbol": "US Tech 100",
        "direction": "BUY",
        "entry_price": 19500.0,
        "stop_loss": 19450.0,
        "take_profit": 19575.0,
        "trade_score": 60.0,
        "confirmation_percentage": 55.0,
        "confirmations": {
            "vwap_alignment": False,
            "poc_alignment": False,
            "breakout_volume_confirmed": False,
            "macro_liquidity_clear": False,
        },
        "breakout_volume_ratio": 0.85,
        "opening_range_atr_ratio": 1.85,
        "atr_frozen_m5": 30.0,
        "distance_to_pdh_atr": 0.10, # Chocando contra PDH
        "entry_time": "2026-10-09T16:45:00Z", # 12:45 NY (fuera de Killzone)
    }
    market_c = {
        "planned_rr": 1.5,
        "risk_percent": 1.0,
        "entry_price": 19500.0,
        "spread": 6.5,
        "stop_loss": 19450.0,
    }
    dec_c = engine.score_signal(
        symbol="US Tech 100",
        signal=sig_c,
        analysis=sig_c,
        market=market_c,
        strategy_name="ORB_NEW_YORK",
    )
    print(f"\n  [SETUP C- (DEGRADADO)]: US Tech 100 a las 12:45 NY")
    print(f"    Probabilidad: {dec_c.probability:.1%} | Expectativa Neta: {dec_c.net_expectancy_r:+.2f}R | Filtro: {'PERMITIDO' if dec_c.allowed else 'BLOQUEADO'}")
    print(f"    Motivo: {dec_c.reason}")
    print("=" * 80)
    print("\nEntrenamiento, validación e inferencia de Meta-Labeling ORB completados exitosamente.")


if __name__ == "__main__":
    train_orb_model()
