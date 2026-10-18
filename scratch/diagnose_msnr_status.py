import sqlite3
import json
import time
from datetime import datetime
from pathlib import Path
import sys

PROJECT_ROOT = Path("C:/TradingBoot/smc_synthetic_bot")
sys.path.insert(0, str(PROJECT_ROOT))

DB_PATH = Path("C:/Users/sebas/AppData/Local/BlackDaemonFx/trading_bot.sqlite3")

def run_diagnostics():
    print(f"===========================================================")
    print(f"=== DIAGNÓSTICO EN TIEMPO REAL TRAS MODIFICACIONES MSNR ===")
    print(f"===========================================================")
    print(f"Hora del sistema: {datetime.now().isoformat()}")
    print(f"Base de datos: {DB_PATH}\n")

    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    # 1. Configuración activa en la BD
    cur.execute("SELECT settings_json FROM strategy_runtime_preferences WHERE id = 20")
    row = cur.fetchone()
    if row:
        s = json.loads(row[0])
        print("--- 1. Parámetros de Runtime en Base de Datos ---")
        print(f"  • retest_window_minutes: {s.get('retest_window_minutes')} min (esperado: 360)")
        print(f"  • recovery_window_minutes: {s.get('recovery_window_minutes')} min (esperado: 90)")
        print(f"  • confirmation_tolerance_bars: {s.get('confirmation_tolerance_bars')} barras (esperado: 2)")
        print(f"  • confirmation_tolerance_max_atr: {s.get('confirmation_tolerance_max_atr')} ATR (esperado: 0.35)")
        print(f"  • m5_confirmation_mode: {s.get('m5_confirmation_mode')}")
        
        asset_modes = s.get("asset_modes", {})
        star_assets = ['Crash 500 Index', 'Crash 600 Index', 'Step Index', 'Wall Street 30', 'XAUUSD', 'EURUSD', 'GBPUSD']
        toxic_assets = ['Step Index 500', 'Volatility 10 Index', 'Volatility 25 Index', 'Volatility 75 Index', 'Crash 300 Index', 'Boom 600 Index']
        
        print("\n  • Estado de Activos Estrella:")
        for a in star_assets:
            print(f"    - {a:<18}: {asset_modes.get(a, 'N/D')}")
            
        print("\n  • Estado de Activos Tóxicos:")
        for a in toxic_assets:
            print(f"    - {a:<22}: {asset_modes.get(a, 'N/D')}")

    # 2. Símbolos activos en instrument_selection_profile_preferences
    cur.execute("SELECT selected_symbols_json FROM instrument_selection_profile_preferences WHERE selection_profile = 'MALAYSIAN_SNR'")
    row = cur.fetchone()
    if row:
        symbols = json.loads(row[0])
        print(f"\n--- 2. Cartera de Instrumentos Filtrados ({len(symbols)} activos) ---")
        print(f"  {symbols}")

    # 3. Candidatos recientes en msnr_candidates
    cur.execute("""
        SELECT candidate_key, symbol, variant, state, first_reason, last_reason, first_seen, last_seen, evaluations, executed, capture_json 
        FROM msnr_candidates 
        WHERE last_seen >= '2026-10-14 10:20:00' OR last_seen >= '2026-10-14T10:20:00'
        ORDER BY last_seen DESC
    """)
    candidates_after_restart = cur.fetchall()
    print(f"\n--- 3. Actividad de Candidatos MSNR Post-Modificaciones (desde 10:20) ---")
    print(f"Total candidatos evaluados post-reinicio: {len(candidates_after_restart)}")
    
    if candidates_after_restart:
        for c in candidates_after_restart[:15]:
            ckey, sym, var, st, fr, lr, fs, ls, ev, ex, cap_json = c
            cap = json.loads(cap_json) if cap_json else {}
            dist_atr = cap.get("distance_atr", cap.get("dist_atr", "N/A"))
            print(f"  [{ls[:19]}] {sym:<16} | Var: {var:<12} | State: {st:<10} | Razon: {str(lr):<28} | Evals: {ev:<3} | Exec: {ex}")
    else:
        cur.execute("""
            SELECT candidate_key, symbol, variant, state, first_reason, last_reason, first_seen, last_seen, evaluations, executed 
            FROM msnr_candidates 
            ORDER BY last_seen DESC LIMIT 10
        """)
        print("Últimos candidatos registrados globalmente:")
        for c in cur.fetchall():
            ckey, sym, var, st, fr, lr, fs, ls, ev, ex = c
            print(f"  [{ls[:19]}] {sym:<16} | Var: {var:<12} | State: {st:<10} | Razon: {str(lr):<28} | Evals: {ev}")

    # 4. Desglose de estados recientes
    cur.execute("""
        SELECT state, COALESCE(last_reason, 'NONE'), count(*) 
        FROM msnr_candidates 
        WHERE last_seen >= '2026-10-14'
        GROUP BY state, last_reason
        ORDER BY count(*) DESC
    """)
    print("\n--- 4. Distribución de Estados de Candidatos en el Día de Hoy ---")
    for st, rej, count in cur.fetchall():
        print(f"  • Estado: {st:<12} | Razón: {rej:<35} | Cantidad: {count}")

    # 5. Órdenes y Trades ejecutados hoy
    cur.execute("""
        SELECT count(*) FROM trades WHERE entry_time >= '2026-10-14' OR exit_time >= '2026-10-14' OR created_at >= '2026-10-14'
    """)
    trades_today = cur.fetchone()[0]
    print(f"\n--- 5. Trades y Posiciones Hoy ---")
    print(f"  Trades totales hoy: {trades_today}")
    
    cur.execute("""
        SELECT id, instrument, direction, entry_time, exit_time, net_pnl, status, result 
        FROM trades 
        WHERE entry_time >= '2026-10-14' OR created_at >= '2026-10-14'
        ORDER BY id DESC LIMIT 5
    """)
    rows = cur.fetchall()
    if rows:
        for t in rows:
            print(f"  Trade #{t[0]}: {t[1]} {t[2]} | Entry: {t[3]} | PnL: {t[5]} | Estado: {t[6]} | Result: {t[7]}")
    else:
        print("  (Sin operaciones cerradas aún hoy en el broker)")

    # 6. Estado del Modelo IA Live
    from database.repository import TradingRepository
    from strategy.malaysian_snr.ai_policy import active_model_status
    repo = TradingRepository(db_path=str(DB_PATH))
    status = active_model_status(s, model_directory=str(PROJECT_ROOT / "storage/ai_models"))
    print(f"\n--- 6. Estado de Compatibilidad IA Live ---")
    print(f"  {json.dumps(status, indent=2)}")

    # 7. Prueba sintética de inferencia IA con características reales
    from strategy.ai import MetaLabelingConfig, MetaLabelingEngine
    engine = MetaLabelingEngine(
        MetaLabelingConfig(
            enabled=True,
            model_directory=str(PROJECT_ROOT / "storage/ai_models"),
            min_training_samples=15,
            model_type="LIGHTGBM",
        ),
        worker="MALAYSIAN_SNR",
    )
    model = engine.load_model("MALAYSIAN_SNR")
    if model:
        print(f"\n--- 7. Inferencia del Modelo GBDT Recalibrado ---")
        print(f"  Modelo cargado correctamente: {type(model).__name__}")
        print(f"  Firma del modelo: {model.provenance.get('settings_signature')}")
        
        from strategy.ai.feature_extraction import feature_vector
        # Test setup 1: Setup A+ (Crash 500 Sell con confluencia y ADX fuerte)
        features_a = {
            "confirmation_percentage": 0.85,
            "trade_score": 85.0,
            "adx": 32.0,
            "adx_normalized": 0.64,
            "direction_buy": 0.0,
            "confirmations_ratio": 0.85,
            "is_crash": 1.0,
            "is_boom": 0.0,
        }
        vec_a = feature_vector(features_a)
        pred_a = model.probability(vec_a)
        print(f"  • Setup A+ (Crash 500 SELL, ADX 32, conf 85%): Probabilidad = {pred_a:.4f} -> {'APROBADO (>0.55)' if pred_a >= 0.55 else 'FILTRADO'}")

        # Test setup 2: Setup Débil (ADX bajo, sin confluencia)
        features_b = {
            "confirmation_percentage": 0.30,
            "trade_score": 40.0,
            "adx": 12.0,
            "adx_normalized": 0.24,
            "direction_buy": 1.0,
            "confirmations_ratio": 0.40,
            "is_crash": 0.0,
            "is_boom": 0.0,
        }
        vec_b = feature_vector(features_b)
        pred_b = model.probability(vec_b)
        print(f"  • Setup C- (Setup Débil, ADX 12, conf 30%): Probabilidad = {pred_b:.4f} -> {'APROBADO' if pred_b >= 0.55 else 'FILTRADO (<0.55, Protege WR)'}")

    # 8. Verificación de logs recientes del worker malaysian-snr-daemon
    print(f"\n--- 8. Verificación de Logs del Worker MSNR ---")
    log_dir = PROJECT_ROOT / "logs"
    if log_dir.exists():
        msnr_logs = sorted(list(log_dir.glob("*malaysian*")), key=lambda p: p.stat().st_mtime, reverse=True)
        if msnr_logs:
            latest_log = msnr_logs[0]
            print(f"  Archivo de log más reciente: {latest_log.name}")
            with open(latest_log, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            print(f"  Total líneas: {len(lines)}. Últimas 10 líneas:")
            for l in lines[-10:]:
                print(f"    {l.strip()}")
        else:
            print("  No se encontraron archivos de log específicos con nombre *malaysian*")

if __name__ == "__main__":
    run_diagnostics()
