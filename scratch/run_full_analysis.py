import os
import sys
import time
import json
import sqlite3
import pandas as pd
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, os.path.abspath("."))

from backtesting.historical_multibot_analysis import (
    HistoricalEngine,
    simulate_dual_leg_trade,
    compute_performance_metrics,
    save_trades_to_storage,
    SPREADS,
    ORB_SYMBOLS
)
from strategy.orb.new_york_orb import ORBConfig

def main():
    print("==========================================================================")
    print("  ANÁLISIS HISTÓRICO MULTI-BOT: GOLD (CUARTOS) Y ORB (NUEVA YORK)")
    print("  Gestión Dual: Riesgo 1.0% (2 trades x 0.5%) | TP1 + Corredora TP2 con BE")
    print("==========================================================================")
    
    engine = HistoricalEngine(data_dir="data/historical")
    
    # --------------------------------------------------------------------------
    # 1. ESCANEO / CARGA DE SEÑALES CACHEADAS
    # --------------------------------------------------------------------------
    import pickle
    cache_path = Path("storage/analysis/signals_cache.pkl")
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    
    if cache_path.exists():
        print(f"[CACHE] Cargando señales pre-escaneadas desde {cache_path}...")
        with open(cache_path, "rb") as f:
            cached_data = pickle.load(f)
        gq_signals_strict = cached_data["gq_signals_strict"]
        gq_signals_adaptive = cached_data["gq_signals_adaptive"]
        orb_signals_standard = cached_data["orb_signals_standard"]
        orb_signals_optimized = cached_data["orb_signals_optimized"]
        print(f"[CACHE] Cargadas {len(gq_signals_strict)} GQ strict, {len(gq_signals_adaptive)} GQ adaptive.")
    else:
        t_start = time.time()
        # A) GOLD Cuartos (Strict 2.0 tolerance, min_rr 1.5)
        gq_signals_strict = engine.scan_gold_quarters_signals(tolerance=2.0, min_rr=1.5, adaptive_tolerance=False)
        # B) GOLD Cuartos (Adaptive ATR tolerance para optimización)
        gq_signals_adaptive = engine.scan_gold_quarters_signals(tolerance=2.0, min_rr=1.5, adaptive_tolerance=True)
        
        # C) ORB (Standard Config)
        cfg_orb_standard = ORBConfig(
            retest_max_candles=3,
            momentum_enabled=True,
            require_breakout_volume_confirmation=True,
            target_rr=2.0
        )
        
        # D) ORB (Optimized Config: 5 velas de retest, volumen adaptativo)
        cfg_orb_optimized = ORBConfig(
            retest_max_candles=5,
            momentum_enabled=True,
            require_breakout_volume_confirmation=False,  # bypass cuando no hay feed de volumen real en índices
            target_rr=2.0
        )
        
        orb_signals_standard = {}
        orb_signals_optimized = {}
        for sym in ORB_SYMBOLS:
            orb_signals_standard[sym] = engine.scan_orb_signals(sym, config=cfg_orb_standard)
            orb_signals_optimized[sym] = engine.scan_orb_signals(sym, config=cfg_orb_optimized)
            
        print(f"\n[OK] Escaneo de señales completado en {time.time() - t_start:.2f}s")
        with open(cache_path, "wb") as f:
            pickle.dump({
                "gq_signals_strict": gq_signals_strict,
                "gq_signals_adaptive": gq_signals_adaptive,
                "orb_signals_standard": orb_signals_standard,
                "orb_signals_optimized": orb_signals_optimized,
            }, f)
        print(f"[CACHE] Señales guardadas en caché: {cache_path}")
    
    # --------------------------------------------------------------------------
    # 2. SIMULACIÓN DE TRADES DUAL-LEG: COMPARATIVA DE CONFIGURACIONES
    # --------------------------------------------------------------------------
    # Evaluamos 4 configuraciones de salida para responder a la petición del usuario:
    configs = [
        {"name": "Config_1_RR_1.5_2.5", "rr_tp1": 1.5, "rr_tp2": 2.5, "structural": False},
        {"name": "Config_2_RR_1.0_2.0", "rr_tp1": 1.0, "rr_tp2": 2.0, "structural": False},
        {"name": "Config_3_RR_2.0_3.5", "rr_tp1": 2.0, "rr_tp2": 3.5, "structural": False},
        {"name": "Config_4_Estructural", "rr_tp1": 1.5, "rr_tp2": 3.0, "structural": True},
    ]
    
    all_experiments = {}
    
    # A) Baseline: GOLD Cuartos Strict + ORB Standard
    for cfg in configs:
        trades = []
        # GOLD Cuartos
        m5_gold = engine.loaded_data["XAUUSD"]["m5"]
        spread_gold = SPREADS["XAUUSD"]
        for sig in gq_signals_strict:
            tr = simulate_dual_leg_trade(
                sig, m5_gold, spread_gold,
                rr_tp1=cfg["rr_tp1"], rr_tp2=cfg["rr_tp2"],
                use_structural_targets=cfg["structural"]
            )
            if tr: trades.append(tr)
            
        # ORB Standard
        for sym in ORB_SYMBOLS:
            m5_sym = engine.loaded_data[sym]["m5"]
            spr = SPREADS.get(sym, 0.5)
            for sig in orb_signals_standard[sym]:
                tr = simulate_dual_leg_trade(
                    sig, m5_sym, spr,
                    rr_tp1=cfg["rr_tp1"], rr_tp2=cfg["rr_tp2"],
                    use_structural_targets=cfg["structural"]
                )
                if tr: trades.append(tr)
                
        metrics = compute_performance_metrics(trades)
        all_experiments[f"Baseline_{cfg['name']}"] = {
            "metrics": metrics,
            "trades": trades
        }

    # B) Optimización (Aumento de Trades + Rentabilidad):
    # GOLD Cuartos Adaptive ATR + ORB Optimized (5 retest candles, flexible volume)
    for cfg in configs:
        trades_opt = []
        # GOLD Cuartos Adaptive
        m5_gold = engine.loaded_data["XAUUSD"]["m5"]
        spread_gold = SPREADS["XAUUSD"]
        for sig in gq_signals_adaptive:
            tr = simulate_dual_leg_trade(
                sig, m5_gold, spread_gold,
                rr_tp1=cfg["rr_tp1"], rr_tp2=cfg["rr_tp2"],
                use_structural_targets=cfg["structural"]
            )
            if tr: trades_opt.append(tr)
            
        # ORB Optimized
        for sym in ORB_SYMBOLS:
            m5_sym = engine.loaded_data[sym]["m5"]
            spr = SPREADS.get(sym, 0.5)
            for sig in orb_signals_optimized[sym]:
                tr = simulate_dual_leg_trade(
                    sig, m5_sym, spr,
                    rr_tp1=cfg["rr_tp1"], rr_tp2=cfg["rr_tp2"],
                    use_structural_targets=cfg["structural"]
                )
                if tr: trades_opt.append(tr)
                
        metrics_opt = compute_performance_metrics(trades_opt)
        all_experiments[f"Optimized_{cfg['name']}"] = {
            "metrics": metrics_opt,
            "trades": trades_opt
        }

    # --------------------------------------------------------------------------
    # 3. DETALLE POR INSTRUMENTO Y ESTRATEGIA (En la mejor configuración)
    # --------------------------------------------------------------------------
    best_config_name = "Config_1_RR_1.5_2.5"
    primary_trades = all_experiments[f"Baseline_{best_config_name}"]["trades"]
    optimized_trades = all_experiments[f"Optimized_{best_config_name}"]["trades"]
    
    # Desglose por símbolo
    breakdown_by_symbol_base = {}
    for sym in set(ORB_SYMBOLS) | {"GOLD_CUARTOS"}:
        if sym == "GOLD_CUARTOS":
            sub = [t for t in primary_trades if t["strategy"] == "GOLD_QUARTERS"]
        else:
            sub = [t for t in primary_trades if t["symbol"] == sym and t["strategy"] == "ORB_NEW_YORK"]
        breakdown_by_symbol_base[sym] = compute_performance_metrics(sub)

    breakdown_by_symbol_opt = {}
    for sym in set(ORB_SYMBOLS) | {"GOLD_CUARTOS"}:
        if sym == "GOLD_CUARTOS":
            sub = [t for t in optimized_trades if t["strategy"] == "GOLD_QUARTERS"]
        else:
            sub = [t for t in optimized_trades if t["symbol"] == sym and t["strategy"] == "ORB_NEW_YORK"]
        breakdown_by_symbol_opt[sym] = compute_performance_metrics(sub)

    # --------------------------------------------------------------------------
    # 4. GUARDAR TODAS LAS OPERACIONES Y METADATA
    # --------------------------------------------------------------------------
    save_trades_to_storage(
        primary_trades,
        db_path="storage/analysis/historical_analysis.db",
        csv_path="storage/analysis/historical_trades_baseline.csv"
    )
    save_trades_to_storage(
        optimized_trades,
        db_path="storage/analysis/historical_analysis.db",
        csv_path="storage/analysis/historical_trades_optimized.csv"
    )
    
    # Guardar resumen comparativo
    summary_rows = []
    for exp_name, data in all_experiments.items():
        m = data["metrics"]
        summary_rows.append({
            "Experiment": exp_name,
            "Trades": m.get("total_trades", 0),
            "WinRate%": m.get("win_rate_pct", 0),
            "Leg1_WR%": m.get("leg1_win_rate_pct", 0),
            "Leg2_WR%": m.get("leg2_win_rate_pct", 0),
            "Leg2_BE%": m.get("leg2_break_even_rate_pct", 0),
            "ProfitFactor": m.get("profit_factor", 0),
            "NetReturn%": m.get("net_return_pct", 0),
            "MaxDD%": m.get("max_drawdown_pct", 0),
            "Sharpe": m.get("sharpe_ratio", 0),
            "Expectancy_R": m.get("expectancy_r", 0),
            "Trades_Month": m.get("trades_per_month", 0),
        })
    df_summary = pd.DataFrame(summary_rows)
    df_summary.to_csv("storage/analysis/experiments_summary.csv", index=False)
    
    # Guardar desglose por activo
    asset_rows = []
    for sym, m in breakdown_by_symbol_base.items():
        asset_rows.append({
            "Symbol": sym,
            "Mode": "Baseline",
            "Trades": m.get("total_trades", 0),
            "WinRate%": m.get("win_rate_pct", 0),
            "ProfitFactor": m.get("profit_factor", 0),
            "NetPnL_USD": m.get("net_pnl_usd", 0),
            "NetReturn%": m.get("net_return_pct", 0),
            "MaxDD%": m.get("max_drawdown_pct", 0),
            "Expectancy_R": m.get("expectancy_r", 0),
        })
    for sym, m in breakdown_by_symbol_opt.items():
        asset_rows.append({
            "Symbol": sym,
            "Mode": "Optimized",
            "Trades": m.get("total_trades", 0),
            "WinRate%": m.get("win_rate_pct", 0),
            "ProfitFactor": m.get("profit_factor", 0),
            "NetPnL_USD": m.get("net_pnl_usd", 0),
            "NetReturn%": m.get("net_return_pct", 0),
            "MaxDD%": m.get("max_drawdown_pct", 0),
            "Expectancy_R": m.get("expectancy_r", 0),
        })
    df_assets = pd.DataFrame(asset_rows)
    df_assets.to_csv("storage/analysis/breakdown_by_symbol.csv", index=False)
    
    print("\n==========================================================================")
    print("                       RESUMEN DE EXPERIMENTOS")
    print("==========================================================================")
    print(df_summary.to_string(index=False))
    
    print("\n==========================================================================")
    print("                     DESGLOSE POR ACTIVO / WORKER")
    print("==========================================================================")
    print(df_assets.to_string(index=False))

if __name__ == "__main__":
    main()
