"""Replay Histórico Aumentado para GOLD_QUARTERS con soporte de TP1 + TP2 y Break-Even.

Extrae velas históricas de MT5 en M5 y H1, detecta todos los setups de rechazo
de cuartos con los filtros optimizados, simula la gestión dual TP1 (+25) y TP2 (+50)
con activación de Break-Even a +1.0R, extrae características para IA y entrena el modelo.
"""

import sys
import os
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import json
import math
import numpy as np
import pandas as pd
from datetime import datetime, timezone

from strategy.gold_quarters import GoldQuarterStrategy
from strategy.ai.feature_extraction import (
    FEATURE_NAMES, extract_meta_features
)
from strategy.ai.model import (
    LogisticRegressionModel, ProbabilityCalibrator, CalibratedLogisticModel
)


def fetch_mt5_candles(symbol="XAUUSD", count=15000):
    try:
        import MetaTrader5 as mt5
    except ImportError:
        print("MetaTrader5 no disponible en este entorno.")
        return None, None

    if not mt5.initialize():
        print("No se pudo inicializar MT5:", mt5.last_error())
        return None, None

    target_symbol = symbol
    info = mt5.symbol_info(target_symbol)
    if info is None:
        target_symbol = f"{symbol}micro"
        info = mt5.symbol_info(target_symbol)
    if info is None:
        target_symbol = "GOLD"
        info = mt5.symbol_info(target_symbol)
    if info is None:
        print(f"Símbolo {symbol} no encontrado en MT5.")
        mt5.shutdown()
        return None, None

    print(f"Descargando {count} velas M5 e H1 para {target_symbol} desde MT5...")
    m5_rates = mt5.copy_rates_from_pos(target_symbol, mt5.TIMEFRAME_M5, 0, count)
    h1_rates = mt5.copy_rates_from_pos(target_symbol, mt5.TIMEFRAME_H1, 0, max(1500, count // 12))
    mt5.shutdown()

    if m5_rates is None or len(m5_rates) < 100 or h1_rates is None or len(h1_rates) < 50:
        print("Datos insuficientes recibidos de MT5.")
        return None, None

    df_m5 = pd.DataFrame(m5_rates)
    df_m5['time'] = pd.to_datetime(df_m5['time'], unit='s', utc=True)
    df_m5 = df_m5[['time', 'open', 'high', 'low', 'close', 'tick_volume']].sort_values('time').reset_index(drop=True)

    df_h1 = pd.DataFrame(h1_rates)
    df_h1['time'] = pd.to_datetime(df_h1['time'], unit='s', utc=True)
    df_h1 = df_h1[['time', 'open', 'high', 'low', 'close', 'tick_volume']].sort_values('time').reset_index(drop=True)

    print(f"Descargadas {len(df_m5)} velas M5 ({df_m5.time.iloc[0]} a {df_m5.time.iloc[-1]})")
    print(f"Descargadas {len(df_h1)} velas H1 ({df_h1.time.iloc[0]} a {df_h1.time.iloc[-1]})")
    return df_m5, df_h1


class HistoricalCandleProvider:
    def __init__(self, m5_df, h1_df):
        self.m5_df = m5_df
        self.h1_df = h1_df

    def get_candles(self, symbol, timeframe, count=100):
        if timeframe == 'H1':
            return self.h1_df.tail(count).copy()
        return self.m5_df.tail(count).copy()


def run_historical_replay(df_m5, df_h1, increment=25.0, tolerance=2.0, min_rr=2.0):
    print("\nIniciando simulación histórica de rechazos de cuartos (Gestión TP1 + TP2 y BE a +1R)...")
    strategy = GoldQuarterStrategy(provider=None, increment=increment, tolerance=tolerance, min_rr=min_rr)
    
    start_idx = 100
    total_bars = len(df_m5)
    candidates = []

    for i in range(start_idx, total_bars - 50):
        current_time = df_m5['time'].iloc[i]
        
        m5_slice = df_m5.iloc[max(0, i - 40): i + 1].copy()
        h1_slice = df_h1[df_h1['time'] + pd.Timedelta(hours=1) <= current_time].tail(100).copy()
        
        if len(m5_slice) < 16 or len(h1_slice) < 20:
            continue

        provider = HistoricalCandleProvider(m5_slice, h1_slice)
        strategy.provider = provider

        analysis = strategy.analyze_symbol("XAUUSD", now_utc=current_time)
        if not analysis.get("valid"):
            continue

        sig = analysis["signal"]
        direction = sig["direction"]
        entry_price = sig["entry_price"]
        stop_loss = sig["stop_loss"]
        level = sig["quarter_level"]
        
        # TP1 = primer cuarto (+25 pts) | TP2 = segundo cuarto (+50 pts)
        tp1 = level + increment if direction == "BUY" else level - increment
        tp2 = level + (2.0 * increment) if direction == "BUY" else level - (2.0 * increment)

        risk = abs(entry_price - stop_loss)
        if risk <= 0:
            continue

        # Simular gestión con dos piernas (50% en TP1 y 50% en TP2 con Break-Even a +1.0R)
        future_slice = df_m5.iloc[i + 1: min(total_bars, i + 72)]  # hasta 6 horas
        if future_slice.empty:
            continue

        be_activated = False
        tp1_reached = False
        tp2_reached = False
        sl_hit = False

        leg1_rr = -1.0
        leg2_rr = -1.0
        max_favorable_price = entry_price

        for _, bar in future_slice.iterrows():
            high = bar["high"]
            low = bar["low"]

            if direction == "BUY":
                if high > max_favorable_price:
                    max_favorable_price = high
                favorable_r = (high - entry_price) / risk

                # Regla 1: Activar Break-Even al alcanzar +1.0R
                if favorable_r >= 1.0 and not be_activated:
                    be_activated = True

                # Regla 2: Cobrar TP1 al alcanzar el primer cuarto
                if high >= tp1 and not tp1_reached:
                    tp1_reached = True
                    leg1_rr = (tp1 - entry_price) / risk
                    be_activated = True  # Asegura BE para Leg 2

                # Regla 3: Cobrar TP2 al alcanzar el segundo cuarto
                if high >= tp2 and not tp2_reached:
                    tp2_reached = True
                    leg2_rr = (tp2 - entry_price) / risk
                    break  # Trade completado con éxito total

                # Regla 4: Verificar Stop Loss
                effective_sl = (entry_price + 0.30) if be_activated else stop_loss
                if low <= effective_sl:
                    sl_hit = True
                    if not tp1_reached:
                        leg1_rr = 0.0 if be_activated else -1.0
                    leg2_rr = 0.0 if be_activated else -1.0
                    break

            else:  # SELL
                if low < max_favorable_price:
                    max_favorable_price = low
                favorable_r = (entry_price - low) / risk

                if favorable_r >= 1.0 and not be_activated:
                    be_activated = True

                if low <= tp1 and not tp1_reached:
                    tp1_reached = True
                    leg1_rr = (entry_price - tp1) / risk
                    be_activated = True

                if low <= tp2 and not tp2_reached:
                    tp2_reached = True
                    leg2_rr = (entry_price - tp2) / risk
                    break

                effective_sl = (entry_price - 0.30) if be_activated else stop_loss
                if high >= effective_sl:
                    sl_hit = True
                    if not tp1_reached:
                        leg1_rr = 0.0 if be_activated else -1.0
                    leg2_rr = 0.0 if be_activated else -1.0
                    break

        # Si llegó al final del tiempo sin tocar SL ni TP2
        if not sl_hit and not tp2_reached:
            last_close = future_slice.iloc[-1]["close"]
            current_r = (last_close - entry_price) / risk if direction == "BUY" else (entry_price - last_close) / risk
            if not tp1_reached:
                leg1_rr = current_r if current_r > 0 else (0.0 if be_activated else -1.0)
            leg2_rr = current_r if current_r > 0 else (0.0 if be_activated else -1.0)

        # Rendimiento combinado 50/50 de la operación completa
        blended_rr = (0.50 * leg1_rr) + (0.50 * leg2_rr)
        mfe_r = abs(max_favorable_price - entry_price) / risk

        if tp2_reached:
            outcome = "TP2_WIN"
        elif tp1_reached:
            outcome = "TP1_WIN"
        elif be_activated and blended_rr >= 0:
            outcome = "BE"
        else:
            outcome = "SL_LOSS"

        # Características IA
        market_mock = {"atr": sig.get("atr", 2.0), "entry_price": entry_price, "spread": 0.30}
        feats = extract_meta_features(signal=sig, analysis=analysis, market=market_mock, evaluated_at=current_time)

        # Etiqueta: 1 si el trade produjo beneficio neto significativo (> +0.5R), 0 si terminó en pérdida
        label = 1 if blended_rr >= 0.50 else (0 if blended_rr < -0.20 else None)

        candidate = {
            "time": current_time.isoformat(),
            "direction": direction,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "tp1": tp1,
            "tp2": tp2,
            "outcome": outcome,
            "tp1_reached": tp1_reached,
            "tp2_reached": tp2_reached,
            "be_activated": be_activated,
            "blended_rr": round(blended_rr, 3),
            "leg1_rr": round(leg1_rr, 3),
            "leg2_rr": round(leg2_rr, 3),
            "mfe_r": round(mfe_r, 3),
            "label": label,
            "features": feats,
            "h1_trend": sig.get("h1_trend"),
            "quarter_level": level
        }
        candidates.append(candidate)

    print(f"Total candidatos de Cuartos evaluados: {len(candidates)}")
    return candidates


def train_meta_model(candidates, output_path=None):
    labeled = [c for c in candidates if c["label"] is not None]
    if len(labeled) < 15:
        print(f"Muestras etiquetadas insuficientes ({len(labeled)} < 15). No se puede entrenar.")
        return None

    wins = sum(1 for c in labeled if c["label"] == 1)
    losses = sum(1 for c in labeled if c["label"] == 0)
    print(f"Muestras de entrenamiento: {len(labeled)} (Wins: {wins}, Losses: {losses})")
    if wins == 0 or losses == 0:
        print("No hay representación de ambas clases.")
        return None

    X = np.array([[float(c["features"].get(name, 0.0)) for name in FEATURE_NAMES] for c in labeled], dtype=np.float64)
    y = np.array([int(c["label"]) for c in labeled], dtype=np.int64)

    # Entrenar modelo base
    base_model = LogisticRegressionModel(feature_names=FEATURE_NAMES)
    base_model.fit(X, y, epochs=800, learning_rate=0.08)

    # Entrenar calibrador de probabilidad
    calibrator = ProbabilityCalibrator()
    raw_probs = base_model.predict_proba(X)
    calibrator.fit(raw_probs, y)

    # Validar accuracy
    calibrated_probs = np.array([calibrator.calibrate(p) for p in raw_probs])
    preds = (calibrated_probs >= 0.50).astype(int)
    accuracy = float(np.mean(preds == y))
    
    calibrated_model = CalibratedLogisticModel(
        worker="GOLD",
        strategy_name="GOLD_QUARTERS",
        model=base_model,
        calibrator=calibrator,
        trained_at=datetime.now(timezone.utc).isoformat(),
        average_win_rr=float(np.mean([c["blended_rr"] for c in labeled if c["label"] == 1])),
        average_loss_rr=float(abs(np.mean([c["blended_rr"] for c in labeled if c["label"] == 0])))
    )

    print(f"Modelo de IA entrenado con éxito. Accuracy: {accuracy * 100:.2f}% | Win Rate base: {wins / len(labeled) * 100:.1f}%")

    if not output_path:
        output_path = PROJECT_ROOT / "storage" / "ai_models" / "metalabel_GOLD_QUARTERS.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    weights_dict = {name: float(w) for name, w in zip(FEATURE_NAMES, base_model.weights)}
    model_payload = {
        "worker": "GOLD",
        "strategy_name": "GOLD_QUARTERS",
        "feature_schema": "meta-features-v5",
        "feature_names": list(FEATURE_NAMES),
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "trained": True,
        "samples": len(labeled),
        "positive_samples": wins,
        "negative_samples": losses,
        "average_win_rr": round(calibrated_model.average_win_rr, 3),
        "average_loss_rr": round(calibrated_model.average_loss_rr, 3),
        "metrics": {
            "accuracy": round(accuracy, 4),
            "win_rate": round(wins / len(labeled), 4)
        },
        "model": {
            "weights": [float(w) for w in base_model.weights],
            "bias": float(base_model.bias),
            "mean": [float(m) for m in base_model.mean],
            "scale": [float(s) for s in base_model.scale],
            "feature_weights": weights_dict,
            "trained": True
        },
        "calibrator": {
            "bin_edges": [float(e) for e in calibrator.bin_edges],
            "bin_values": [float(v) for v in calibrator.bin_values],
            "trained": bool(calibrator.trained)
        }
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(model_payload, f, indent=2, ensure_ascii=False)
    print(f"Modelo guardado exitosamente en: {output_path}")

    # También actualizar el modelo global de GOLD
    global_gold_path = PROJECT_ROOT / "storage" / "ai_models" / "metalabel_GOLD_ALL.json"
    with open(global_gold_path, "w", encoding="utf-8") as f:
        json.dump(model_payload, f, indent=2, ensure_ascii=False)
    print(f"Modelo global de Gold sincronizado en: {global_gold_path}")

    return model_payload


if __name__ == "__main__":
    df_m5, df_h1 = fetch_mt5_candles("XAUUSD", count=15000)
    if df_m5 is not None and not df_m5.empty:
        candidates = run_historical_replay(df_m5, df_h1)
        
        replay_path = PROJECT_ROOT / "storage" / "runtime" / "smc_trial" / "replay" / "GOLD_QUARTERS.json"
        replay_path.parent.mkdir(parents=True, exist_ok=True)
        with open(replay_path, "w", encoding="utf-8") as f:
            json.dump({
                "worker": "GOLD",
                "strategy": "GOLD_QUARTERS",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "total_candidates": len(candidates),
                "candidates": candidates
            }, f, indent=2, ensure_ascii=False)
        print(f"Replay guardado en {replay_path}")

        # Entrenar modelo
        model_info = train_meta_model(candidates)
        if model_info:
            print("Entrenamiento de IA completado con éxito.")
    else:
        print("No se pudieron obtener velas históricas de MT5.")
