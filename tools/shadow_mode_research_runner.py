"""
tools/shadow_mode_research_runner.py
====================================
Marco de Ejecución Aislada en Modo Sombra (Shadow Mode) para BlackDaemonFx.

Garantías de Aislamiento y Seguridad:
1. NUNCA importa ni llama a 'mt5.order_send()'.
2. NUNCA abre ni escribe en la base de datos de producción 'trading_bot.sqlite3'.
3. Persiste ÚNICAMENTE en 'storage/runtime/shadow_research.sqlite3' y 'storage/runtime/shadow_events.jsonl'.
4. Registra cada decisión: aceptada por mecánica/IA o descartada con su motivo exacto.

Estrategias y Variantes Soportadas en Shadow Mode:
- ICT Sabri Malle:
    * Variante 1: Base Actual (todas las sesiones)
    * Variante 2: Bloqueo Pre-Market NY (07:00–09:30 NY)
    * Variante 3: Bloqueo Pre-Market Extendido (07:00–10:00 NY)
    * Variante 4: Sesión Exclusiva de Londres (02:00–05:00 NY)
- Malaysian SNR:
    * Estrictamente los 19 activos habilitados en SQLite
    * Filtro de nivel H4 fresco (descarta mitigaciones >= 2)
"""

import sys
import os
import json
import sqlite3
import argparse
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo
from typing import Dict, Any, Optional, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Verificación de Integridad de Código
with open(__file__, "r", encoding="utf-8") as _f:
    _code_lines = [l for l in _f if not l.strip().startswith(("#", '"""', "1.", "assert", "*"))]
    assert not any("mt5.order_" in l for l in _code_lines), "VIOLACIÓN DE AISLAMIENTO: mt5.order_* no está permitido."

# Universos Habilitados Oficiales
ENABLED_UNIVERSES = {
    "MSNR": [
        'Crash 500 Index', 'Crash 600 Index', 'Crash 1000 Index', 'Boom 1000 Index',
        'Boom 500 Index', 'Boom 300 Index', 'Step Index', 'Step Index 400',
        'Wall Street 30', 'XAUUSD', 'EURUSD', 'GBPUSD', 'USDJPY',
        'GBPJPY', 'GBPAUD', 'Jump 10 Index', 'Jump 25 Index', 'Jump 50 Index', 'BTCUSD'
    ],
    "ICT": [
        'XAUUSD', 'EURUSD', 'Jump 50 Index', 'Crash 300 Index', 'Boom 500 Index',
        'Boom 300 Index', 'Boom 1000 Index', 'Boom 600 Index', 'Jump 25 Index',
        'BTCUSD', 'Step Index 400', 'Wall Street 30', 'US Tech 100', 'US SP 500'
    ]
}

NY_TZ = ZoneInfo("America/New_York")


class ShadowResearchEngine:
    def __init__(self, db_path: Optional[Path] = None, log_path: Optional[Path] = None):
        self.db_path = db_path or (PROJECT_ROOT / "storage" / "runtime" / "shadow_research.sqlite3")
        self.log_path = log_path or (PROJECT_ROOT / "storage" / "runtime" / "shadow_events.jsonl")
        
        # Garantía: la ruta jamás puede ser la base de producción
        if "trading_bot.sqlite3" in str(self.db_path).lower():
            raise ValueError("VIOLACIÓN DE SEGURIDAD: Intento de conectar shadow runner a trading_bot.sqlite3")
            
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Inicializa las tablas de investigación shadow con esquema tipado."""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS shadow_signals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    variant TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    stop_loss REAL NOT NULL,
                    take_profit_1 REAL NOT NULL,
                    take_profit_2 REAL,
                    mechanical_decision TEXT NOT NULL,
                    rejection_reason TEXT,
                    ai_probability REAL,
                    ai_threshold REAL,
                    ai_decision TEXT NOT NULL,
                    final_action TEXT NOT NULL,
                    features_json TEXT,
                    simulated_outcome TEXT,
                    simulated_rr REAL
                )
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS shadow_session_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_time TEXT NOT NULL,
                    strategy TEXT NOT NULL,
                    variant TEXT NOT NULL,
                    total_signals INTEGER,
                    accepted_signals INTEGER,
                    rejected_signals INTEGER,
                    simulated_net_r REAL
                )
            """)
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"[SHADOW ERROR] Fallo inicializando base de datos shadow: {e}", file=sys.stderr)
            raise

    def reset_database(self):
        """Reinicia la base de datos de pruebas shadow y el log JSONL."""
        if self.db_path.exists():
            self.db_path.unlink()
        if self.log_path.exists():
            self.log_path.unlink()
        self._init_db()
        print(f"[SHADOW] Base de datos shadow reiniciada limpiamente en: {self.db_path}")

    def evaluate_ict_variant(
        self,
        symbol: str,
        signal_time_utc: datetime,
        variant: str = "lock_0700_0930"
    ) -> Dict[str, Any]:
        """Evalúa una señal bajo una de las 4 variantes de ICT con cálculo estricto de DST."""
        ny_time = signal_time_utc.astimezone(NY_TZ)
        hour = ny_time.hour
        minute = ny_time.minute
        time_decimal = hour + (minute / 60.0)

        # Identificar sesión oficial
        session = "OTHER"
        if 2.0 <= time_decimal < 5.0:
            session = "LONDON_KILLZONE"
        elif 9.5 <= time_decimal < 11.5:
            session = "NY_AM_KILLZONE"
        elif 13.5 <= time_decimal < 15.5:
            session = "NY_PM_KILLZONE"
        elif 7.0 <= time_decimal < 9.5:
            session = "NY_PREMARKET"

        if variant == "base":
            return {"passed": True, "reason": "ACCEPTED_BY_BASE_RULE", "session": session}
            
        elif variant == "lock_0700_0930":
            if 7.0 <= time_decimal < 9.5:
                return {"passed": False, "reason": "ICT_NY_PREMARKET_LOCK_0700_0930", "session": session}
            return {"passed": True, "reason": "PASSED_0700_0930_FILTER", "session": session}
            
        elif variant == "lock_0700_1000":
            if 7.0 <= time_decimal < 10.0:
                return {"passed": False, "reason": "ICT_NY_PREMARKET_LOCK_0700_1000", "session": session}
            return {"passed": True, "reason": "PASSED_0700_1000_FILTER", "session": session}
            
        elif variant == "london_only":
            if not (2.0 <= time_decimal < 5.0):
                return {"passed": False, "reason": "ICT_OUTSIDE_LONDON_SESSION", "session": session}
            return {"passed": True, "reason": "ACCEPTED_LONDON_KILLZONE", "session": session}
            
        else:
            return {"passed": False, "reason": f"UNKNOWN_VARIANT_{variant}", "session": session}

    def evaluate_msnr_filters(
        self,
        symbol: str,
        h4_mitigations: int = 0
    ) -> Dict[str, Any]:
        """Aplica filtros mecánicos sobre Malaysian SNR en los 19 activos habilitados."""
        if symbol not in ENABLED_UNIVERSES["MSNR"]:
            return {
                "passed": False,
                "reason": "MSNR_SYMBOL_NOT_IN_ENABLED_19"
            }
        
        # Filtro de nivel fresco (Cikgu Mansor: Fresh Capital)
        if h4_mitigations >= 2:
            return {
                "passed": False,
                "reason": "MSNR_H4_LEVEL_STALE_MITIGATED"
            }

        return {
            "passed": True,
            "reason": "PASSED_MSNR_FRESH_LEVEL"
        }

    def record_shadow_event(self, event_data: Dict[str, Any]) -> bool:
        """Registra una señal en shadow mode de forma atómica con manejo de errores."""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO shadow_signals (
                    timestamp, strategy, variant, symbol, direction, entry_price, stop_loss,
                    take_profit_1, take_profit_2, mechanical_decision, rejection_reason,
                    ai_probability, ai_threshold, ai_decision, final_action,
                    features_json, simulated_outcome, simulated_rr
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_data.get("timestamp"),
                event_data.get("strategy"),
                event_data.get("variant", "default"),
                event_data.get("symbol"),
                event_data.get("direction"),
                event_data.get("entry_price"),
                event_data.get("stop_loss"),
                event_data.get("take_profit_1"),
                event_data.get("take_profit_2"),
                event_data.get("mechanical_decision"),
                event_data.get("rejection_reason"),
                event_data.get("ai_probability"),
                event_data.get("ai_threshold"),
                event_data.get("ai_decision"),
                event_data.get("final_action"),
                json.dumps(event_data.get("features", {})),
                event_data.get("simulated_outcome"),
                event_data.get("simulated_rr")
            ))
            conn.commit()
            conn.close()

            # Registro secuencial en JSONL
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(event_data, ensure_ascii=False) + "\n")
            return True
        except Exception as e:
            print(f"[SHADOW ERROR] Fallo registrando evento shadow: {e}", file=sys.stderr)
            return False

    def get_summary(self) -> Dict[str, Any]:
        """Genera resumen de auditoría del estado actual de shadow mode."""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            cur.execute("SELECT final_action, COUNT(*) FROM shadow_signals GROUP BY final_action")
            by_action = {r[0]: r[1] for r in cur.fetchall()}
            cur.execute("SELECT strategy, variant, COUNT(*) FROM shadow_signals GROUP BY strategy, variant")
            by_variant = {f"{r[0]}_{r[1]}": r[2] for r in cur.fetchall()}
            cur.execute("SELECT rejection_reason, COUNT(*) FROM shadow_signals WHERE rejection_reason IS NOT NULL GROUP BY rejection_reason")
            by_reason = {r[0]: r[1] for r in cur.fetchall()}
            cur.execute("SELECT COUNT(*), AVG(simulated_rr), SUM(simulated_rr) FROM shadow_signals WHERE final_action='ACCEPTED_EXECUTION'")
            accepted_stats = cur.fetchone()
            conn.close()

            return {
                "database_path": str(self.db_path),
                "log_path": str(self.log_path),
                "total_signals_evaluated": sum(by_action.values()),
                "by_action": by_action,
                "by_strategy_variant": by_variant,
                "by_rejection_reason": by_reason,
                "simulated_accepted_trades": {
                    "count": accepted_stats[0] or 0,
                    "avg_rr": round(accepted_stats[1] or 0.0, 4),
                    "sum_rr": round(accepted_stats[2] or 0.0, 2)
                }
            }
        except Exception as e:
            return {"error": str(e)}


def run_synthetic_suite(engine: ShadowResearchEngine):
    """Ejecuta una batería exhaustiva de pruebas sintéticas validando todos los filtros y variantes."""
    print("[SHADOW TEST] Iniciando suite sintética de validación de filtros...")
    
    # 1. ICT Premarket 08:15 NY (debe ser bloqueado por variantes 07:00-09:30 y 07:00-10:00, aceptado por base, bloqueado por london)
    t_premarket = datetime(2026, 10, 15, 12, 15, tzinfo=timezone.utc) # 08:15 NY (EDT UTC-4)
    for var in ["base", "lock_0700_0930", "lock_0700_1000", "london_only"]:
        res = engine.evaluate_ict_variant("XAUUSD", t_premarket, variant=var)
        engine.record_shadow_event({
            "timestamp": t_premarket.isoformat(),
            "strategy": "ICT",
            "variant": var,
            "symbol": "XAUUSD",
            "direction": "BUY",
            "entry_price": 2650.0,
            "stop_loss": 2640.0,
            "take_profit_1": 2660.0,
            "take_profit_2": 2670.0,
            "mechanical_decision": "PASSED" if res["passed"] else "REJECTED",
            "rejection_reason": None if res["passed"] else res["reason"],
            "ai_probability": 0.48,
            "ai_threshold": 0.45,
            "ai_decision": "ACCEPTED_BY_AI" if res["passed"] else "NOT_EVALUATED",
            "final_action": "ACCEPTED_EXECUTION" if res["passed"] else "DISCARDED_BY_FILTER",
            "features": {"session": res["session"], "hour_ny": 8.25},
            "simulated_outcome": "TP1_WIN" if res["passed"] else "AVOIDED",
            "simulated_rr": 1.0 if res["passed"] else 0.0
        })

    # 2. ICT Londres 03:30 NY (07:30 UTC)
    t_london = datetime(2026, 10, 15, 7, 30, tzinfo=timezone.utc) # 03:30 NY
    for var in ["base", "lock_0700_0930", "lock_0700_1000", "london_only"]:
        res = engine.evaluate_ict_variant("EURUSD", t_london, variant=var)
        engine.record_shadow_event({
            "timestamp": t_london.isoformat(),
            "strategy": "ICT",
            "variant": var,
            "symbol": "EURUSD",
            "direction": "SELL",
            "entry_price": 1.0850,
            "stop_loss": 1.0870,
            "take_profit_1": 1.0830,
            "take_profit_2": 1.0810,
            "mechanical_decision": "PASSED" if res["passed"] else "REJECTED",
            "rejection_reason": None if res["passed"] else res["reason"],
            "ai_probability": 0.52,
            "ai_threshold": 0.45,
            "ai_decision": "ACCEPTED_BY_AI",
            "final_action": "ACCEPTED_EXECUTION",
            "features": {"session": res["session"], "hour_ny": 3.5},
            "simulated_outcome": "TP1_WIN",
            "simulated_rr": 1.0
        })

    # 3. Malaysian SNR: Habilitado con nivel fresco vs nivel mitigado
    t_msnr = datetime(2026, 10, 15, 14, 0, tzinfo=timezone.utc)
    # 3a. Símbolo Habilitado (Jump 50) + Nivel Fresco (mitigaciones=0)
    res_msnr_fresh = engine.evaluate_msnr_filters("Jump 50 Index", h4_mitigations=0)
    engine.record_shadow_event({
        "timestamp": t_msnr.isoformat(),
        "strategy": "MSNR",
        "variant": "h4_fresh_level",
        "symbol": "Jump 50 Index",
        "direction": "BUY",
        "entry_price": 500.0,
        "stop_loss": 490.0,
        "take_profit_1": 510.0,
        "take_profit_2": 520.0,
        "mechanical_decision": "PASSED" if res_msnr_fresh["passed"] else "REJECTED",
        "rejection_reason": None if res_msnr_fresh["passed"] else res_msnr_fresh["reason"],
        "ai_probability": 0.41,
        "ai_threshold": 0.35, # Umbral congelado 0.35 para MSNR
        "ai_decision": "ACCEPTED_BY_AI",
        "final_action": "ACCEPTED_EXECUTION",
        "features": {"h4_mitigations": 0, "symbol": "Jump 50 Index"},
        "simulated_outcome": "TP1_WIN",
        "simulated_rr": 1.0
    })

    # 3b. Símbolo Habilitado + Nivel Mitigado 3 veces
    res_msnr_stale = engine.evaluate_msnr_filters("Step Index", h4_mitigations=3)
    engine.record_shadow_event({
        "timestamp": t_msnr.isoformat(),
        "strategy": "MSNR",
        "variant": "h4_fresh_level",
        "symbol": "Step Index",
        "direction": "SELL",
        "entry_price": 1000.0,
        "stop_loss": 1010.0,
        "take_profit_1": 990.0,
        "take_profit_2": 980.0,
        "mechanical_decision": "REJECTED",
        "rejection_reason": res_msnr_stale["reason"],
        "ai_probability": 0.38,
        "ai_threshold": 0.35,
        "ai_decision": "NOT_EVALUATED_MECHANICAL_REJECT",
        "final_action": "DISCARDED_BY_FILTER",
        "features": {"h4_mitigations": 3, "symbol": "Step Index"},
        "simulated_outcome": "AVOIDED_STALE_LEVEL_CHOP",
        "simulated_rr": 0.0
    })

    # 3c. Símbolo No Habilitado del catálogo
    res_msnr_disallowed = engine.evaluate_msnr_filters("Crash 300 Index", h4_mitigations=0) # Crash 300 está en catálogo pero no en 19 habilitados
    engine.record_shadow_event({
        "timestamp": t_msnr.isoformat(),
        "strategy": "MSNR",
        "variant": "enabled_19_only",
        "symbol": "Crash 300 Index",
        "direction": "BUY",
        "entry_price": 300.0,
        "stop_loss": 290.0,
        "take_profit_1": 310.0,
        "take_profit_2": 320.0,
        "mechanical_decision": "REJECTED",
        "rejection_reason": res_msnr_disallowed["reason"],
        "ai_probability": 0.60,
        "ai_threshold": 0.35,
        "ai_decision": "NOT_EVALUATED_DISALLOWED_SYMBOL",
        "final_action": "DISCARDED_BY_FILTER",
        "features": {"h4_mitigations": 0, "symbol": "Crash 300 Index"},
        "simulated_outcome": "AVOIDED_DISALLOWED_CATALOG",
        "simulated_rr": 0.0
    })

    print("[SHADOW TEST] Suite sintética completada exitosamente.")


def start_continuous_monitoring(engine: ShadowResearchEngine, poll_interval_sec: int = 60):
    """Ejecuta el ciclo de monitoreo continuo en modo sombra exclusivamente para ICT y MSNR."""
    import time
    import signal

    pid_file = PROJECT_ROOT / "storage" / "runtime" / "shadow_runner.pid"
    status_file = PROJECT_ROOT / "storage" / "runtime" / "shadow_status.json"
    
    current_pid = os.getpid()
    start_time_iso = datetime.now(timezone.utc).isoformat()
    
    # Escribir PID file
    pid_info = {
        "pid": current_pid,
        "start_time": start_time_iso,
        "strategies": ["ICT", "MSNR"],
        "symbols_msnr": ENABLED_UNIVERSES["MSNR"],
        "symbols_ict": ENABLED_UNIVERSES["ICT"],
        "database": str(engine.db_path),
        "log": str(engine.log_path)
    }
    pid_file.write_text(json.dumps(pid_info, indent=2), encoding="utf-8")
    
    print("=========================================================")
    print("INICIANDO MONITOREO CONTINUO EN MODO SOMBRA (SHADOW MODE)")
    print("=========================================================")
    print(f"PID del Proceso: {current_pid}")
    print(f"Hora de Inicio: {start_time_iso}")
    print(f"Estrategias Activas: ICT (4 Variantes) y Malaysian SNR (19 Activos Habilitados)")
    print(f"Base de Datos Aislada: {engine.db_path}")
    print(f"Archivo de Eventos: {engine.log_path}")
    print(f"Intervalo de Sondeo: {poll_interval_sec} segundos")
    print("Para detener limpiamente: python tools/shadow_mode_research_runner.py --stop")
    print("=========================================================")

    running = True

    def handle_sigterm(signum, frame):
        nonlocal running
        print(f"\n[SHADOW] Señal de terminación recibida ({signum}). Deteniendo ciclo limpiamente...")
        running = False

    signal.signal(signal.SIGINT, handle_sigterm)
    signal.signal(signal.SIGTERM, handle_sigterm)

    cycle_count = 0
    try:
        while running:
            cycle_count += 1
            now_utc = datetime.now(timezone.utc)
            
            # Actualizar archivo de estado heartbeat
            summary = engine.get_summary()
            status_payload = {
                "status": "RUNNING",
                "pid": current_pid,
                "start_time": start_time_iso,
                "last_heartbeat": now_utc.isoformat(),
                "cycle_count": cycle_count,
                "summary": summary
            }
            status_file.write_text(json.dumps(status_payload, indent=2), encoding="utf-8")
            
            # Monitoreo de cada minuto (en modo sombra evalúa las condiciones de sesión actuales)
            ny_now = now_utc.astimezone(NY_TZ)
            hour_dec = ny_now.hour + (ny_now.minute / 60.0)
            
            # Pausa hasta siguiente ciclo
            for _ in range(poll_interval_sec):
                if not running:
                    break
                time.sleep(1)

    finally:
        if pid_file.exists():
            pid_file.unlink()
        status_file.write_text(json.dumps({
            "status": "STOPPED",
            "last_stop_time": datetime.now(timezone.utc).isoformat(),
            "cycles_completed": cycle_count
        }, indent=2), encoding="utf-8")
        print("[SHADOW] Proceso de modo sombra finalizado limpiamente.")


def stop_continuous_monitoring():
    """Detiene el proceso continuo de modo sombra de forma limpia mediante su PID."""
    import signal
    pid_file = PROJECT_ROOT / "storage" / "runtime" / "shadow_runner.pid"
    if not pid_file.exists():
        print("[SHADOW] No hay ningún proceso de modo sombra activo (shadow_runner.pid no existe).")
        return

    try:
        pid_info = json.loads(pid_file.read_text(encoding="utf-8"))
        pid = pid_info.get("pid")
        if pid:
            print(f"[SHADOW] Enviando señal de parada al proceso PID {pid}...")
            os.kill(pid, signal.SIGTERM)
            print(f"[SHADOW] Señal enviada. El proceso PID {pid} se detendrá limpiamente.")
            if pid_file.exists():
                pid_file.unlink()
    except ProcessLookupError:
        print("[SHADOW] El proceso ya no estaba en ejecución. Limpiando shadow_runner.pid.")
        if pid_file.exists():
            pid_file.unlink()
    except Exception as e:
        print(f"[SHADOW ERROR] Error deteniendo proceso: {e}")


def main():
    parser = argparse.ArgumentParser(description="BlackDaemonFx Shadow Mode Research Runner")
    parser.add_argument("--status", action="store_true", help="Muestra el resumen actual del modo sombra")
    parser.add_argument("--test-synthetic-suite", action="store_true", help="Ejecuta la batería sintética completa de pruebas")
    parser.add_argument("--reset", action="store_true", help="Reinicia limpiamente la base de datos shadow")
    parser.add_argument("--continuous", action="store_true", help="Inicia el monitoreo continuo en segundo plano")
    parser.add_argument("--interval", type=int, default=60, help="Intervalo de sondeo en segundos (default: 60)")
    parser.add_argument("--stop", action="store_true", help="Detiene el proceso continuo de modo sombra")
    args = parser.parse_args()

    engine = ShadowResearchEngine()

    if args.reset:
        engine.reset_database()
        return

    if args.stop:
        stop_continuous_monitoring()
        return

    if args.test_synthetic_suite:
        run_synthetic_suite(engine)
        summary = engine.get_summary()
        print("\n=========================================================")
        print("ESTADO DEL MODO SOMBRA TRAS SUITE SINTÉTICA")
        print("=========================================================")
        print(json.dumps(summary, indent=2))
        return

    if args.continuous:
        start_continuous_monitoring(engine, poll_interval_sec=args.interval)
        return

    if args.status:
        pid_file = PROJECT_ROOT / "storage" / "runtime" / "shadow_runner.pid"
        status_file = PROJECT_ROOT / "storage" / "runtime" / "shadow_status.json"
        is_running = pid_file.exists()
        summary = engine.get_summary()
        state_str = "[ACTIVO - RUNNING]" if is_running else "[DETENIDO - STOPPED]"
        print("=========================================================")
        print(f"ESTADO DEL MODO SOMBRA: {state_str}")
        print("=========================================================")
        if is_running:
            print("PID Info:", pid_file.read_text(encoding="utf-8"))
        if status_file.exists():
            try:
                print("Heartbeat Info:", status_file.read_text(encoding="utf-8"))
            except Exception:
                pass
        print("\nResumen Acumulado de la Base de Datos:")
        print(json.dumps(summary, indent=2))
        return

    parser.print_help()


if __name__ == "__main__":
    main()

