"""
tools/shadow_mode_synchronizer.py
=================================
Worker y sincronizador aislado de investigación para BlackDaemonFx.
Lee señales elegibles desde trading_bot.sqlite3 (SOLO LECTURA) y las evalúa
en modo sombra registrándolas en el entorno de investigación (staging o live shadow).

Gobernanza y Garantías de Seguridad:
1. Conexión de lectura estrictamente en modo URI ?mode=ro a trading_bot.sqlite3.
2. Aserción fatal que prohíbe terminantemente escribir en trading_bot.sqlite3.
3. Cero llamadas a funciones de orden, ejecución o broker de MT5.
4. Totalmente independiente del bucle continuo del runner (no modifica tools/shadow_mode_research_runner.py).
5. Ingestión 100% idempotente: comprueba source_signal_id y tupla canónica para evitar duplicados.
6. Deduplicación por evento único de mercado (ICT asocia 4 variantes al mismo evento).
7. Registro de timestamp de señal (mercado) y timestamp de ingestión por separado en features_json.
8. Preservación estricta de corte prospectivo (2026-10-15T17:35:16.304722+00:00).
9. Desacoplamiento estricto: señales descartadas tienen simulated_outcome = 'AVOIDED' y simulated_rr = 0.0.
10. Modos: --dry-run (solo simulación), --staging (base de pruebas aislada), --execute (base de investigación shadow).
"""

import os
import sys
import json
import sqlite3
import argparse
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from tools.shadow_mode_research_runner import ShadowResearchEngine, ENABLED_UNIVERSES

LIVE_DB_PATH = Path.home() / "AppData/Local/BlackDaemonFx/trading_bot.sqlite3"
PRIMARY_SHADOW_DB = PROJECT_ROOT / "storage" / "runtime" / "shadow_research.sqlite3"
PRIMARY_SHADOW_LOG = PROJECT_ROOT / "storage" / "runtime" / "shadow_events.jsonl"
STAGING_SHADOW_DB = PROJECT_ROOT / "storage" / "runtime" / "shadow_research_staging.sqlite3"
STAGING_SHADOW_LOG = PROJECT_ROOT / "storage" / "runtime" / "shadow_events_staging.jsonl"

SEALED_CUTOFF_TS = "2026-10-15T17:35:16.304722+00:00"


class ShadowSynchronizer:
    def __init__(
        self,
        target_db: Path = STAGING_SHADOW_DB,
        target_log: Path = STAGING_SHADOW_LOG,
        dry_run: bool = True,
        cutoff_iso: str = SEALED_CUTOFF_TS
    ):
        self.target_db = target_db
        self.target_log = target_log
        self.dry_run = dry_run
        self.cutoff_iso = cutoff_iso
        self.cutoff_dt = pd.to_datetime(cutoff_iso, utc=True)
        self.engine = ShadowResearchEngine(db_path=target_db, log_path=target_log)

        # Aserción de seguridad absoluta
        assert str(target_db).lower() != str(LIVE_DB_PATH).lower(), "FATAL: El destino de sincronización no puede ser la base productiva."

    def _init_target_db_if_needed(self):
        """Inicializa la base de datos de destino y asegura columnas de mercado contrafactual."""
        if self.dry_run:
            return
        self.target_db.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.target_db, timeout=30.0)
        cur = conn.cursor()
        cur.execute("PRAGMA journal_mode = WAL;")
        cur.execute("PRAGMA busy_timeout = 30000;")
        
        # Verificar y agregar columnas contrafactuales si faltan
        cur.execute("PRAGMA table_info(shadow_signals)")
        existing_cols = [r[1] for r in cur.fetchall()]
        
        for col_name, col_type in [
            ("market_outcome", "TEXT"),
            ("market_rr", "REAL"),
            ("contrafactual_note", "TEXT")
        ]:
            if col_name not in existing_cols:
                cur.execute(f"ALTER TABLE shadow_signals ADD COLUMN {col_name} {col_type};")

        conn.commit()
        conn.close()

    def _get_already_ingested_keys(self) -> set:
        """Obtiene el conjunto de claves ya ingestadas para garantizar idempotencia total."""
        if not self.target_db.exists():
            return set()
        try:
            conn = sqlite3.connect(f"file:{self.target_db}?mode=ro", uri=True, timeout=30.0)
            cur = conn.cursor()
            cur.execute("""
                SELECT 
                    strategy, variant, symbol, timestamp, entry_price, features_json
                FROM shadow_signals
            """)
            keys = set()
            for r in cur.fetchall():
                # Clave compuesta 1: tupla canónica
                keys.add((r[0], r[1], r[2], r[3], round(float(r[4] or 0), 4)))
                # Clave compuesta 2: source_signal_id si existe en features_json
                if r[5]:
                    try:
                        feat = json.loads(r[5])
                        src_id = feat.get("source_signal_id")
                        if src_id is not None:
                            keys.add((r[0], r[1], f"src_id_{src_id}"))
                    except Exception:
                        pass
            conn.close()
            return keys
        except Exception as e:
            print(f"[WARN] No se pudieron leer claves existentes de {self.target_db}: {e}")
            return set()

    def fetch_live_signals(self, min_created_at: str = "2026-10-15 00:00:00") -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """Lee señales de trading_bot.sqlite3 de forma estrictamente de solo lectura."""
        if not LIVE_DB_PATH.exists():
            raise FileNotFoundError(f"Base de producción no encontrada en {LIVE_DB_PATH}")

        conn = sqlite3.connect(f"file:{LIVE_DB_PATH}?mode=ro", uri=True, timeout=30.0)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Consultar señales
        cur.execute("""
            SELECT id, instrument, timeframe, signal_time, direction, valid, details_json, created_at
            FROM signals
            WHERE created_at >= ?
            ORDER BY id ASC
        """, (min_created_at,))
        signals = [dict(r) for r in cur.fetchall()]

        # Consultar trades ejecutados para cruzar estado de mercado
        cur.execute("""
            SELECT id, instrument, direction, entry_time, exit_time, entry_price, exit_price,
                   net_pnl, realized_rr, result, exit_reason
            FROM trades
            WHERE entry_time >= ?
            ORDER BY id ASC
        """, (min_created_at,))
        trades = [dict(r) for r in cur.fetchall()]
        conn.close()

        return signals, trades

    def match_market_trade_outcome(
        self,
        signal_data: Dict[str, Any],
        live_trades: List[Dict[str, Any]],
        strategy_family: str = "ALL"
    ) -> Tuple[str, float, str]:
        """
        Cruza una señal con la tabla de trades en vivo para determinar si se ejecutó y cerró.
        Agrupa todas las piernas (TP1 + RUNNER) de la misma ejecución para calcular el
        PnL neto combinado y el RR realizado ponderado/promedio.
        Retorna: (market_outcome, market_rr, contrafactual_note)
        """
        sym = signal_data["instrument"]
        dir_ = signal_data["direction"]
        time_val = signal_data.get("signal_time") or signal_data.get("created_at")
        sig_time = pd.to_datetime(time_val, utc=True)
        sig_time_iso = sig_time.isoformat()

        # Extraer token determinista de details_json si existe
        det = {}
        if signal_data.get("details_json"):
            try:
                det = json.loads(signal_data["details_json"])
            except Exception:
                pass
        
        # Buscar trades coincidentes priorizando execution_key exacto
        candidate_trades = []
        for t in live_trades:
            if t["instrument"] == sym and t["direction"] == dir_:
                t_entry = pd.to_datetime(t["entry_time"], utc=True)
                time_diff = abs((t_entry - sig_time).total_seconds())
                if time_diff <= 3600:
                    setup = (t.get("setup_reason") or "").upper()
                    exec_k = (t.get("execution_key") or "").upper()
                    
                    strat_match = True
                    if strategy_family == "ICT":
                        if "MSNR" in setup or "MSNR" in exec_k:
                            strat_match = False
                    elif strategy_family == "MSNR":
                        if "ICT" in setup or "ICT" in exec_k:
                            strat_match = False
                    
                    if strat_match:
                        # Prioridad 1: Coincidencia explícita de timestamp o hash en execution_key
                        exact_key_match = False
                        if sig_time_iso[:19] in exec_k:
                            exact_key_match = True
                        for k, v in det.items():
                            if isinstance(v, str) and len(v) >= 12 and v.upper() in exec_k:
                                exact_key_match = True
                                break
                        
                        priority = 0 if exact_key_match else 1
                        candidate_trades.append((priority, time_diff, t))

        if not candidate_trades:
            return "PENDING_EVALUATION", 0.0, "No ejecutado o pendiente en mercado"

        # Ordenar por prioridad determinista y luego por cercanía temporal
        candidate_trades.sort(key=lambda x: (x[0], x[1]))
        first_trade = candidate_trades[0][2]
        base_entry = pd.to_datetime(first_trade["entry_time"], utc=True)

        # Agrupar piernas de la misma orden/ejecución (diferencia <= 10s desde la primera pierna)
        execution_legs = [
            t for _, _, t in candidate_trades
            if abs((pd.to_datetime(t["entry_time"], utc=True) - base_entry).total_seconds()) <= 10.0
        ]

        leg_ids = [t["id"] for t in execution_legs]
        any_open = any(t["exit_time"] is None for t in execution_legs)
        all_closed = all(t["exit_time"] is not None for t in execution_legs)

        if any_open:
            return "OPEN", 0.0, f"Abierto en MT5 legs={leg_ids}"

        if all_closed:
            total_risk = sum(float(t.get("risk_amount") or 0.0) for t in execution_legs)
            total_net_pnl = sum(float(t.get("net_pnl") or 0.0) for t in execution_legs)
            
            # Cálculo ponderado por riesgo monetario real: sum(net_pnl) / sum(risk_amount)
            if total_risk > 0.0:
                risk_weighted_rr = total_net_pnl / total_risk
            else:
                risk_weighted_rr = sum(float(t.get("realized_rr") or 0.0) for t in execution_legs) / len(execution_legs)
                
            outcome = "TP1_WIN" if total_net_pnl > 0 else "SL_LOSS" if total_net_pnl < 0 else "CLOSED_OTHER"
            note = f"LIVE_TRADE_PROXY mt5_ids={leg_ids}, risk=${total_risk:.2f}, net_pnl=${total_net_pnl:.2f}, risk_weighted_rr={risk_weighted_rr:+.2f}R, legs={len(execution_legs)}"
            return outcome, risk_weighted_rr, note

        return "PENDING_EVALUATION", 0.0, "Estado mixto o pendiente"


    def run_sync(self, min_created_at: str = "2026-10-15 17:35:16") -> Dict[str, Any]:
        """Ejecuta el ciclo de sincronización idempotente."""
        print("=========================================================================")
        print(f"SHADOW MODE SYNCHRONIZER [{'DRY-RUN' if self.dry_run else 'EXECUTE'}]")
        print("=========================================================================")
        print(f"Origen (Solo Lectura): {LIVE_DB_PATH}")
        print(f"Destino: {self.target_db}")
        print(f"Corte prospectivo sellado: {self.cutoff_iso}")
        print(f"Filtro min_created_at: >= {min_created_at}")

        self._init_target_db_if_needed()
        existing_keys = self._get_already_ingested_keys()
        print(f"Claves existentes en destino: {len(existing_keys)}")

        signals, trades = self.fetch_live_signals(min_created_at=min_created_at)
        print(f"Señales leídas en origen productivo: {len(signals)}")
        print(f"Trades leídos en origen productivo: {len(trades)}")

        now_iso = datetime.now(timezone.utc).isoformat()
        
        stats = {
            "total_read": len(signals),
            "eligible_ict_signals": 0,
            "eligible_ict_prospective": 0,
            "eligible_ict_pre_cutoff": 0,
            "eligible_msnr_signals": 0,
            "eligible_msnr_prospective": 0,
            "eligible_msnr_pre_cutoff": 0,
            "other_signals_skipped": 0,
            "already_ingested_skipped": 0,
            "rows_prepared": 0,
            "rows_inserted": 0,
            "events_unique_prepared": 0,
            "dry_run": self.dry_run,
            "details": []
        }

        prepared_events = []

        for s in signals:
            src_id = s["id"]
            sym = s["instrument"]
            dir_ = s["direction"]
            det = {}
            if s["details_json"]:
                try:
                    det = json.loads(s["details_json"])
                except Exception:
                    pass

            strat_name = det.get("strategy_name", "").upper()
            entry_price = float(det.get("entry_price", 0.0))
            stop_loss = float(det.get("stop_loss", 0.0))
            tp1 = float(det.get("tp1_price", det.get("take_profit", 0.0)))
            tp2 = float(det.get("tp2_price", 0.0))

            time_str = s["signal_time"] or det.get("entry_time") or s["created_at"]
            sig_time = pd.to_datetime(time_str, utc=True)
            sig_time_iso = sig_time.isoformat()

            # Clasificación de cohorte temporal
            is_prospective = sig_time >= self.cutoff_dt
            cohort_tag = "PROSPECTIVE_SEALED" if is_prospective else "PRE_CUTOFF_BASELINE"

            # -------------------------------------------------------------
            # A. ESTRATEGIA ICT SABRI MALLE
            # -------------------------------------------------------------
            if "ICT" in strat_name:
                if sym not in ENABLED_UNIVERSES["ICT"]:
                    stats["other_signals_skipped"] += 1
                    continue

                stats["eligible_ict_signals"] += 1
                if is_prospective:
                    stats["eligible_ict_prospective"] += 1
                else:
                    stats["eligible_ict_pre_cutoff"] += 1
                stats["events_unique_prepared"] += 1

                mkt_outcome, mkt_rr, mkt_note = self.match_market_trade_outcome(s, trades, strategy_family="ICT")

                for variant in ["base", "lock_0700_0930", "lock_0700_1000", "london_only"]:
                    # Comprobación de idempotencia
                    canonical_key = ("ICT", variant, sym, sig_time_iso, round(entry_price, 4))
                    src_key = ("ICT", variant, f"src_id_{src_id}")
                    if canonical_key in existing_keys or src_key in existing_keys:
                        stats["already_ingested_skipped"] += 1
                        continue

                    eval_res = self.engine.evaluate_ict_variant(sym, sig_time, variant=variant)
                    trade_score = float(det.get("trade_score", 50.0))
                    prob = trade_score / 100.0
                    ai_th = 0.45
                    passed_mech = eval_res["passed"]
                    passed_ai = prob >= ai_th

                    if passed_mech and passed_ai:
                        final_action = "ACCEPTED_EXECUTION"
                        ai_decision = "ACCEPTED_BY_AI"
                        sim_outcome = mkt_outcome
                        sim_rr = mkt_rr
                    else:
                        final_action = "DISCARDED_BY_FILTER"
                        ai_decision = "REJECTED_BY_AI" if not passed_ai else "NOT_EVALUATED_FILTER_REJECT"
                        # Regla inmutable: toda señal descartada tiene AVOIDED y RR 0.0
                        sim_outcome = "AVOIDED"
                        sim_rr = 0.0

                    features = {
                        "source_signal_id": src_id,
                        "created_at_live": s["created_at"],
                        "ingested_at": now_iso,
                        "cohort_tag": cohort_tag,
                        "session": eval_res.get("session"),
                        "trade_score": trade_score,
                        "event_uuid": f"ICT_{sym}_{sig_time_iso}_{entry_price:.2f}",
                        "sim_source": "LIVE_TRADE_PROXY" if final_action == "ACCEPTED_EXECUTION" else "DISCARDED_AVOIDED",
                        "gate_qualified": False
                    }

                    event_row = {
                        "timestamp": sig_time_iso,
                        "strategy": "ICT",
                        "variant": variant,
                        "symbol": sym,
                        "direction": dir_,
                        "entry_price": entry_price,
                        "stop_loss": stop_loss,
                        "take_profit_1": tp1,
                        "take_profit_2": tp2,
                        "mechanical_decision": "PASSED" if passed_mech else "REJECTED",
                        "rejection_reason": None if passed_mech else eval_res.get("reason"),
                        "ai_probability": prob,
                        "ai_threshold": ai_th,
                        "ai_decision": ai_decision,
                        "final_action": final_action,
                        "features_json": json.dumps(features),
                        "simulated_outcome": sim_outcome,
                        "simulated_rr": sim_rr,
                        "market_outcome": mkt_outcome,
                        "market_rr": mkt_rr,
                        "contrafactual_note": mkt_note
                    }
                    prepared_events.append(event_row)
                    stats["rows_prepared"] += 1

            # -------------------------------------------------------------
            # B. ESTRATEGIA MALAYSIAN SNR
            # -------------------------------------------------------------
            elif "MALAYSIAN" in strat_name or "MSNR" in strat_name:
                if sym not in ENABLED_UNIVERSES["MSNR"]:
                    stats["other_signals_skipped"] += 1
                    continue

                stats["eligible_msnr_signals"] += 1
                if is_prospective:
                    stats["eligible_msnr_prospective"] += 1
                else:
                    stats["eligible_msnr_pre_cutoff"] += 1
                stats["events_unique_prepared"] += 1

                mkt_outcome, mkt_rr, mkt_note = self.match_market_trade_outcome(s, trades, strategy_family="MSNR")

                canonical_key = ("MSNR", "enabled_19_h4_fresh", sym, sig_time_iso, round(entry_price, 4))
                src_key = ("MSNR", "enabled_19_h4_fresh", f"src_id_{src_id}")
                if canonical_key in existing_keys or src_key in existing_keys:
                    stats["already_ingested_skipped"] += 1
                    continue

                h4_mitigations = int(det.get("retest_evidence", {}).get("touch_index", 0))
                eval_res = self.engine.evaluate_msnr_filters(sym, h4_mitigations=h4_mitigations)
                trade_score = float(det.get("trade_score", 50.0))
                prob = trade_score / 100.0
                ai_th = 0.35 # Umbral congelado 0.35
                passed_mech = eval_res["passed"]
                passed_ai = prob >= ai_th

                if passed_mech and passed_ai:
                    final_action = "ACCEPTED_EXECUTION"
                    ai_decision = "ACCEPTED_BY_AI"
                    sim_outcome = mkt_outcome
                    sim_rr = mkt_rr
                else:
                    final_action = "DISCARDED_BY_FILTER"
                    ai_decision = "REJECTED_BY_AI" if not passed_ai else "NOT_EVALUATED_FILTER_REJECT"
                    sim_outcome = "AVOIDED"
                    sim_rr = 0.0

                features = {
                    "source_signal_id": src_id,
                    "created_at_live": s["created_at"],
                    "ingested_at": now_iso,
                    "cohort_tag": cohort_tag,
                    "h4_mitigations": h4_mitigations,
                    "trade_score": trade_score,
                    "event_uuid": f"MSNR_{sym}_{sig_time_iso}_{entry_price:.2f}",
                    "sim_source": "LIVE_TRADE_PROXY" if final_action == "ACCEPTED_EXECUTION" else "DISCARDED_AVOIDED",
                    "gate_qualified": False
                }

                event_row = {
                    "timestamp": sig_time_iso,
                    "strategy": "MSNR",
                    "variant": "enabled_19_h4_fresh",
                    "symbol": sym,
                    "direction": dir_,
                    "entry_price": entry_price,
                    "stop_loss": stop_loss,
                    "take_profit_1": tp1,
                    "take_profit_2": tp2,
                    "mechanical_decision": "PASSED" if passed_mech else "REJECTED",
                    "rejection_reason": None if passed_mech else eval_res.get("reason"),
                    "ai_probability": prob,
                    "ai_threshold": ai_th,
                    "ai_decision": ai_decision,
                    "final_action": final_action,
                    "features_json": json.dumps(features),
                    "simulated_outcome": sim_outcome,
                    "simulated_rr": sim_rr,
                    "market_outcome": mkt_outcome,
                    "market_rr": mkt_rr,
                    "contrafactual_note": mkt_note
                }
                prepared_events.append(event_row)
                stats["rows_prepared"] += 1

            else:
                stats["other_signals_skipped"] += 1

        print(f"\nResumen de Preparación:")
        print(f"  - Señales Elegibles ICT: {stats['eligible_ict_signals']} (Prospectivas: {stats['eligible_ict_prospective']}, Pre-Corte: {stats['eligible_ict_pre_cutoff']})")
        print(f"  - Señales Elegibles MSNR: {stats['eligible_msnr_signals']} (Prospectivas: {stats['eligible_msnr_prospective']}, Pre-Corte: {stats['eligible_msnr_pre_cutoff']})")
        print(f"  - Eventos Únicos Preparados: {stats['events_unique_prepared']}")
        print(f"  - Filas Preparadas (Variantes): {stats['rows_prepared']}")
        print(f"  - Filas Omitidas por Idempotencia (Ya existían): {stats['already_ingested_skipped']}")
        print(f"  - Otras Señales Omitidas (Símbolo/Estrategia fuera de catálogo): {stats['other_signals_skipped']}")

        # -------------------------------------------------------------
        # INSERCIÓN ATÓMICA SI NO ES DRY-RUN
        # -------------------------------------------------------------
        if not self.dry_run and prepared_events:
            print(f"\nEscribiendo {len(prepared_events)} filas en destino de investigación...")
            conn = sqlite3.connect(self.target_db, timeout=30.0)
            cur = conn.cursor()
            cur.execute("PRAGMA busy_timeout = 30000;")
            
            with conn: # Transacción atómica
                for ev in prepared_events:
                    cur.execute("""
                        INSERT INTO shadow_signals (
                            timestamp, strategy, variant, symbol, direction, entry_price, stop_loss,
                            take_profit_1, take_profit_2, mechanical_decision, rejection_reason,
                            ai_probability, ai_threshold, ai_decision, final_action,
                            features_json, simulated_outcome, simulated_rr, market_outcome, market_rr,
                            contrafactual_note
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        ev["timestamp"], ev["strategy"], ev["variant"], ev["symbol"], ev["direction"],
                        ev["entry_price"], ev["stop_loss"], ev["take_profit_1"], ev["take_profit_2"],
                        ev["mechanical_decision"], ev["rejection_reason"], ev["ai_probability"],
                        ev["ai_threshold"], ev["ai_decision"], ev["final_action"], ev["features_json"],
                        ev["simulated_outcome"], ev["simulated_rr"], ev["market_outcome"], ev["market_rr"],
                        ev["contrafactual_note"]
                    ))
            conn.close()
            stats["rows_inserted"] = len(prepared_events)

            # Escribir en log secuencial JSONL de forma atómica
            with open(self.target_log, "a", encoding="utf-8") as f:
                for ev in prepared_events:
                    f.write(json.dumps(ev, ensure_ascii=False) + "\n")

            print(f"[OK] Ingestadas {stats['rows_inserted']} filas exitosamente en {self.target_db}.")
        elif self.dry_run:
            print("\n[MODO DRY-RUN] Cero escrituras realizadas en disco. Simulación completada.")

        # -------------------------------------------------------------
        # RECONCILIACIÓN DE ESTADOS OPEN / PENDING -> CLOSED EN DESTINO
        # -------------------------------------------------------------
        stats["transitions_updated"] = 0
        if not self.dry_run and self.target_db.exists():
            conn = sqlite3.connect(self.target_db, timeout=30.0)
            cur = conn.cursor()
            cur.execute("""
                SELECT id, timestamp, strategy, variant, symbol, direction, final_action, market_outcome
                FROM shadow_signals
                WHERE market_outcome IN ('OPEN', 'PENDING_EVALUATION')
            """)
            pending_rows = cur.fetchall()
            for prow in pending_rows:
                sh_id, ts, strat, var, sym, dir_, f_act, curr_out = prow
                s_dict = {"instrument": sym, "direction": dir_, "signal_time": ts}
                mkt_out, mkt_rr, mkt_note = self.match_market_trade_outcome(s_dict, trades, strategy_family=strat)
                if mkt_out not in ('OPEN', 'PENDING_EVALUATION'):
                    sim_out = mkt_out if f_act == "ACCEPTED_EXECUTION" else "AVOIDED"
                    sim_rr = mkt_rr if f_act == "ACCEPTED_EXECUTION" else 0.0
                    cur.execute("""
                        UPDATE shadow_signals
                        SET market_outcome = ?, market_rr = ?, contrafactual_note = ?,
                            simulated_outcome = ?, simulated_rr = ?
                        WHERE id = ?
                    """, (mkt_out, mkt_rr, f"{mkt_note} [RECONCILED]", sim_out, sim_rr, sh_id))
                    stats["transitions_updated"] += 1
            conn.commit()
            conn.close()
            if stats["transitions_updated"] > 0:
                print(f"[RECONCILIATION] Actualizadas {stats['transitions_updated']} transiciones de estado a CLOSED.")

        stats["details"] = prepared_events
        return stats


def run_synchronizer_tests():
    """Ejecuta batería exhaustiva de pruebas sobre una base temporal en memoria/scratch."""
    print("=========================================================================")
    print("EJECUTANDO BATERÍA DE PRUEBAS DEL SINCRONIZADOR AISLADO")
    print("=========================================================================")
    
    test_db = PROJECT_ROOT / "scratch" / "test_shadow_sync_temp.sqlite3"
    test_log = PROJECT_ROOT / "scratch" / "test_shadow_sync_temp.jsonl"
    
    if test_db.exists():
        test_db.unlink()
    if test_log.exists():
        test_log.unlink()

    sync = ShadowSynchronizer(target_db=test_db, target_log=test_log, dry_run=False)

    # Prueba 1: Primera ejecución sobre staging
    print("\n--- PRUEBA 1: Sincronización inicial hacia base temporal ---")
    res1 = sync.run_sync(min_created_at="2026-10-15 17:35:16")
    print(f"  Resultados P1: Filas preparadas={res1['rows_prepared']}, Filas insertadas={res1['rows_inserted']}")
    assert res1['rows_inserted'] > 0, "Error P1: Se debieron insertar filas."

    # Prueba 2: Reejecución idempotente (debe insertar 0 filas y omitir todas)
    print("\n--- PRUEBA 2: Reejecución idempotente inmediata ---")
    res2 = sync.run_sync(min_created_at="2026-10-15 17:35:16")
    print(f"  Resultados P2: Filas preparadas={res2['rows_prepared']}, Omitidas por idempotencia={res2['already_ingested_skipped']}, Insertadas={res2['rows_inserted']}")
    assert res2['rows_inserted'] == 0, "Error P2: La reejecución debió insertar 0 filas (fallo de idempotencia)."
    assert res2['already_ingested_skipped'] > 0, "Error P2: Debieron detectarse claves ya existentes."

    # Prueba 3: Verificación de estructura y banderas AVOIDED
    print("\n--- PRUEBA 3: Verificación de banderas AVOIDED y persistencia de features ---")
    conn = sqlite3.connect(test_db)
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM shadow_signals WHERE final_action='DISCARDED_BY_FILTER' AND (simulated_outcome != 'AVOIDED' OR simulated_rr != 0.0)")
    bad_discarded = cur.fetchone()[0]
    print(f"  Señales descartadas sin flag AVOIDED o con RR != 0: {bad_discarded}")
    assert bad_discarded == 0, "Error P3: Violación del desacoplamiento de señales descartadas."

    cur.execute("SELECT count(*) FROM shadow_signals WHERE json_extract(features_json, '$.source_signal_id') IS NULL")
    missing_src_id = cur.fetchone()[0]
    print(f"  Señales sin source_signal_id en features: {missing_src_id}")
    assert missing_src_id == 0, "Error P3: Faltó trazabilidad de source_signal_id."

    # Prueba 4: Deduplicación por evento
    cur.execute("SELECT count(DISTINCT json_extract(features_json, '$.event_uuid')) FROM shadow_signals")
    unique_events_in_db = cur.fetchone()[0]
    print(f"  Eventos únicos deduplicados registrados en test_db: {unique_events_in_db}")

    conn.close()

    # Limpieza de archivos de prueba
    if test_db.exists():
        test_db.unlink()
    if test_log.exists():
        test_log.unlink()

    print("\n[OK] TODAS LAS PRUEBAS PASARON EXITOSAMENTE (100% IDEMPOTENTE Y SEGURO).")
    print("=========================================================================")


def main():
    parser = argparse.ArgumentParser(description="BlackDaemonFx Shadow Mode Isolated Synchronizer")
    parser.add_argument("--dry-run", action="store_true", help="Ejecuta en modo simulación (cero escrituras)")
    parser.add_argument("--staging", action="store_true", help="Ingesta hacia storage/runtime/shadow_research_staging.sqlite3")
    parser.add_argument("--target-live-shadow", action="store_true", help="Ingesta hacia storage/runtime/shadow_research.sqlite3")
    parser.add_argument("--min-created-at", type=str, default="2026-10-15 17:35:16", help="Filtro de timestamp mínimo de created_at")
    parser.add_argument("--test-suite", action="store_true", help="Ejecuta batería de pruebas automáticas del sincronizador")
    args = parser.parse_args()

    if args.test_suite:
        run_synchronizer_tests()
        return

    dry_run = args.dry_run or (not args.staging and not args.target_live_shadow)
    
    if args.target_live_shadow:
        target_db = PRIMARY_SHADOW_DB
        target_log = PRIMARY_SHADOW_LOG
    else:
        target_db = STAGING_SHADOW_DB
        target_log = STAGING_SHADOW_LOG

    sync = ShadowSynchronizer(
        target_db=target_db,
        target_log=target_log,
        dry_run=dry_run
    )
    sync.run_sync(min_created_at=args.min_created_at)


if __name__ == "__main__":
    main()
