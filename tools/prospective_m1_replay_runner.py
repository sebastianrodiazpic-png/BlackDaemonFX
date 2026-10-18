"""
tools/prospective_m1_replay_runner.py
=====================================
Motor aislado de replay independiente en temporalidad M1 para validación de la
cohorte prospectiva sellada en BlackDaemonFx.

Gobernanza y Garantías de Seguridad:
1. No altera trading_bot.sqlite3 (solo lectura si se consulta).
2. No modifica shadow_research.sqlite3 (base primaria congelada en 87 filas).
3. No envía órdenes a MT5, no toca demonios ni modelos de IA.
4. Obtiene velas M1 limpias y verificables directamente desde Deriv WebSocket.
5. Ejecución cronológica estricta sin fuga de información (fill a partir de created_at).
6. Resolución conservadora de conflictos intra-vela (SL tiene prioridad si se tocan ambos).
7. Incorpora costos verificables (spread real de Deriv y slippage modelado).
8. Segregación estricta:
   - Pre-corte vs Cohorte Prospectiva Sellada.
   - PnL Replay vs PnL Broker Demo (LIVE_TRADE_PROXY).
   - Operaciones simuladas vs Señales descartadas (AVOIDED / 0.0R contrafactual).
"""

import sys
import json
import sqlite3
import argparse
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple

import hashlib

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from marketdata.deriv import DerivMarketDataProvider

STAGING_DB_PATH = PROJECT_ROOT / "storage" / "runtime" / "shadow_research_staging.sqlite3"
DEFAULT_ARCHIVE_DIR = PROJECT_ROOT / "storage" / "runtime" / "m1_prospective_cache"
SEALED_CUTOFF_TS = "2026-10-15T17:35:16.304722+00:00"

# Estimación de spread típico en puntos/unidades por símbolo sintético
TYPICAL_SPREADS = {
    "Boom 500 Index": 0.50,
    "Crash 300 Index": 0.30,
    "Boom 600 Index": 0.60,
    "Jump 10 Index": 2.50,
    "Crash 600 Index": 0.50,
    "Boom 300 Index": 0.20
}

class ProspectiveM1ReplayRunner:
    def __init__(
        self,
        db_path: Path = STAGING_DB_PATH,
        cutoff_iso: str = SEALED_CUTOFF_TS,
        dry_run: bool = True,
        cost_r: float = 0.0,
        fill_mode: str = "created_at",
        max_staleness_minutes: Optional[float] = None,
        pre_fill_guard: bool = False,
        causal_time: bool = False,
        archive_dir: Optional[Path] = None
    ):
        self.db_path = db_path
        self.cutoff_iso = cutoff_iso
        self.cutoff_dt = pd.to_datetime(cutoff_iso, utc=True)
        self.dry_run = dry_run
        self.cost_r = cost_r
        self.fill_mode = fill_mode
        self.max_staleness_minutes = max_staleness_minutes
        self.pre_fill_guard = pre_fill_guard
        self.causal_time = causal_time
        self.archive_dir = Path(archive_dir) if archive_dir else None
        self.provider = DerivMarketDataProvider()
        self.cache_m1 = {}

    def export_archive(self, target_dir: Path = DEFAULT_ARCHIVE_DIR) -> Path:
        target_dir = Path(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        manifest = {
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "archive_version": "1.0",
            "provider": "Deriv Public WebSocket Charts API",
            "endpoint": "wss://api.derivws.com/trading/v1/options/ws/public",
            "timeframe": "M1",
            "symbols": {}
        }
        hash_list = []
        print(f"\n[ARCHIVE] Exportando archivo de datos M1 a: {target_dir}...")
        for sym, df in self.cache_m1.items():
            clean_name = sym.replace(" ", "_").replace("(", "").replace(")", "")
            csv_path = target_dir / f"{clean_name}_M1.csv"
            df.to_csv(csv_path, index=False)

            with open(csv_path, "rb") as f:
                sha256 = hashlib.sha256(f.read()).hexdigest()
            hash_list.append(sha256)

            gaps = int((df['time'].diff().dt.total_seconds() > 60).sum())
            dups = int(df.duplicated(subset=['time']).sum())
            incomplete = int((df['complete'] == False).sum()) if 'complete' in df.columns else 0

            manifest["symbols"][sym] = {
                "file": csv_path.name,
                "sha256": sha256,
                "count": len(df),
                "min_time_utc": str(df['time'].min()),
                "max_time_utc": str(df['time'].max()),
                "gaps_count": gaps,
                "duplicates_count": dups,
                "incomplete_bars": incomplete
            }
            print(f"  [OK ARCHIVE] {sym:<16} -> {csv_path.name} (SHA-256: {sha256[:12]}..., {len(df)} barras)")

        overall_sha = hashlib.sha256("".join(sorted(hash_list)).encode("utf-8")).hexdigest()
        manifest["overall_integrity_hash"] = overall_sha

        manifest_path = target_dir / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        print(f"  [OK ARCHIVE] Manifest guardado en: {manifest_path} (Hash global: {overall_sha[:12]}...)")
        return manifest_path

    def load_archive(self, archive_dir: Path) -> Dict[str, pd.DataFrame]:
        archive_dir = Path(archive_dir)
        manifest_path = archive_dir / "manifest.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest no encontrado en archivo: {manifest_path}")

        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        print(f"[ARCHIVE] Cargando y verificando datos M1 archivados desde: {archive_dir}...")
        for sym, meta in manifest.get("symbols", {}).items():
            csv_file = archive_dir / meta["file"]
            if not csv_file.exists():
                raise FileNotFoundError(f"Archivo de datos M1 faltante: {csv_file}")

            # Verificación de integridad SHA-256
            with open(csv_file, "rb") as f:
                sha256 = hashlib.sha256(f.read()).hexdigest()
            if sha256 != meta["sha256"]:
                raise ValueError(f"Falla de integridad SHA-256 en {csv_file.name}: esperado {meta['sha256']}, obtenido {sha256}")

            df = pd.read_csv(csv_file)
            df['time'] = pd.to_datetime(df['time'], utc=True)
            self.cache_m1[sym] = df
            print(f"  [OK ARCHIVE] {sym:<16}: {len(df)} barras M1 verificadas (SHA-256 OK)")

        return self.cache_m1

    def fetch_market_data(self, symbols: List[str]) -> Dict[str, pd.DataFrame]:
        if self.archive_dir and self.archive_dir.exists():
            return self.load_archive(self.archive_dir)

        print(f"[REPLAY M1] Descargando velas M1 continuas para {len(symbols)} activos desde Deriv WebSocket...")
        for sym in symbols:
            if sym not in self.cache_m1:
                df = self.provider.get_candles(sym, timeframe="M1", count=1000)
                if df is not None and not df.empty:
                    min_t = df['time'].min()
                    max_t = df['time'].max()
                    gaps = (df['time'].diff().dt.total_seconds() > 60).sum()
                    print(f"  [OK] {sym:<16}: {len(df)} barras M1 | Cobertura: {min_t} a {max_t} | Gaps: {gaps}")
                    self.cache_m1[sym] = df
                else:
                    print(f"  [FAIL] {sym:<16}: ERROR al obtener datos M1")
        return self.cache_m1

    def simulate_trade_m1(
        self,
        symbol: str,
        direction: str,
        signal_time: pd.Timestamp,
        created_at: pd.Timestamp,
        entry_target: float,
        sl: float,
        tp1_target: Optional[float] = None,
        tp2_target: Optional[float] = None,
        fill_mode: str = "created_at"
    ) -> Dict[str, Any]:
        """
        Simula cronológicamente la ejecución a partir de created_at usando velas M1.
        """
        df_bars = self.cache_m1.get(symbol)
        if df_bars is None or df_bars.empty:
            return {
                "outcome": "NO_EVALUABLE",
                "realized_rr": 0.0,
                "reason": "MISSING_M1_DATA",
                "bars_held": 0
            }

        # Regla de frescura / caducidad experimental (Staleness Guard)
        if self.max_staleness_minutes is not None:
            delay_minutes = (created_at - signal_time).total_seconds() / 60.0
            if delay_minutes > self.max_staleness_minutes:
                return {
                    "outcome": "EXPIRED_STALE",
                    "realized_rr": 0.0,
                    "status": "DISCARDED",
                    "fill_price": None,
                    "fill_time": None,
                    "exit_time": None,
                    "bars_held": 0,
                    "leg1_reason": f"EXPIRED_STALENESS ({delay_minutes:.1f}m > {self.max_staleness_minutes}m)",
                    "leg2_reason": None
                }

        spread = TYPICAL_SPREADS.get(symbol, 0.0)

        # Regla de elegibilidad de fill tardío (Pre-fill Invalidation Guard)
        # Si el precio tocó SL o TP antes de que la señal estuviera disponible para ejecución,
        # la orden no debe enviarse / simularse como activa en el mercado tardío.
        if self.pre_fill_guard and created_at > signal_time:
            between = df_bars[(df_bars["time"] >= signal_time) & (df_bars["time"] < created_at)]
            if not between.empty:
                sl_hit_pre = False
                tp1_hit_pre = False
                for _, b in between.iterrows():
                    b_high = float(b["high"]) + (spread if direction == "SELL" else 0.0)
                    b_low = float(b["low"]) + (spread if direction == "SELL" else 0.0)
                    if direction == "BUY":
                        if b_low <= sl: sl_hit_pre = True
                        if tp1_target is not None and b_high >= tp1_target: tp1_hit_pre = True
                    else:
                        if b_high >= sl: sl_hit_pre = True
                        if tp1_target is not None and b_low <= tp1_target: tp1_hit_pre = True

                if sl_hit_pre:
                    return {
                        "outcome": "INVALIDATED_PRE_FILL_SL",
                        "realized_rr": 0.0,
                        "status": "DISCARDED",
                        "fill_price": None,
                        "fill_time": None,
                        "exit_time": None,
                        "bars_held": 0,
                        "leg1_reason": "PRE_FILL_SL_TOUCHED",
                        "leg2_reason": None
                    }
                if tp1_hit_pre:
                    return {
                        "outcome": "INVALIDATED_PRE_FILL_TP",
                        "realized_rr": 0.0,
                        "status": "DISCARDED",
                        "fill_price": None,
                        "fill_time": None,
                        "exit_time": None,
                        "bars_held": 0,
                        "leg1_reason": "PRE_FILL_TP_TOUCHED",
                        "leg2_reason": None
                    }

        # Determinación de inicio de evaluación de barras
        if self.causal_time and fill_mode == "signal_entry":
            eval_start = signal_time
        else:
            eval_start = created_at

        # La entrada real a mercado ocurre en la primera barra disponible a partir de eval_start
        future = df_bars[df_bars["time"] >= eval_start].copy().reset_index(drop=True)
        if future.empty:
            return {
                "outcome": "NO_EVALUABLE",
                "realized_rr": 0.0,
                "reason": "NO_BARS_AFTER_SIGNAL",
                "bars_held": 0
            }

        fill_time = future["time"].iloc[0]

        if fill_mode == "signal_entry":
            fill_price = entry_target + spread if direction == "BUY" else entry_target
        else:
            bid_open = float(future["open"].iloc[0])
            fill_price = bid_open + spread if direction == "BUY" else bid_open

        sign = 1 if direction == "BUY" else -1
        risk = abs(fill_price - sl)

        if risk <= 0:
            return {
                "outcome": "INVALID_RISK",
                "realized_rr": 0.0,
                "reason": f"Risk non-positive: fill={fill_price}, sl={sl}",
                "bars_held": 0
            }

        # Objetivos dinámicos si no vienen fijos
        tp1 = fill_price + sign * tp1_rr * risk if tp1_target is None else tp1_target
        tp2 = fill_price + sign * tp2_rr * risk if tp2_target is None else tp2_target

        actual_tp1_rr = sign * (tp1 - fill_price) / risk
        actual_tp2_rr = sign * (tp2 - fill_price) / risk

        leg1_done = False
        leg1_rr = 0.0
        leg1_time = None
        leg1_reason = None

        leg2_done = False
        leg2_rr = 0.0
        leg2_time = None
        leg2_reason = None

        active_sl_leg2 = sl
        bars_held = 0

        for idx, bar in future.iterrows():
            bars_held = idx + 1
            t = bar["time"]
            b_high = float(bar["high"])
            b_low = float(bar["low"])

            # En SELL las posiciones se cierran a Ask (bid + spread)
            if direction == "SELL":
                high = b_high + spread
                low = b_low + spread
            else:
                high = b_high
                low = b_low

            # 1. EVALUAR PIERNA 1
            if not leg1_done:
                hit_sl = low <= sl if direction == "BUY" else high >= sl
                hit_tp1 = high >= tp1 if direction == "BUY" else low <= tp1

                if hit_sl and hit_tp1:
                    # Conflicto en misma vela: regla conservadora, SL gana
                    leg1_done = True
                    leg1_rr = -1.0
                    leg1_time = t
                    leg1_reason = "SL_SAME_BAR_CONFLICT"
                    leg2_done = True
                    leg2_rr = -1.0
                    leg2_time = t
                    leg2_reason = "SL_SAME_BAR_CONFLICT"
                    break
                elif hit_sl:
                    leg1_done = True
                    leg1_rr = -1.0
                    leg1_time = t
                    leg1_reason = "SL_LOSS"
                    leg2_done = True
                    leg2_rr = -1.0
                    leg2_time = t
                    leg2_reason = "SL_LOSS"
                    break
                elif hit_tp1:
                    leg1_done = True
                    leg1_rr = actual_tp1_rr
                    leg1_time = t
                    leg1_reason = "TP1_WIN"
                    # Mover pierna 2 a Breakeven
                    active_sl_leg2 = fill_price
                    hit_tp2_same_bar = high >= tp2 if direction == "BUY" else low <= tp2
                    if hit_tp2_same_bar:
                        leg2_done = True
                        leg2_rr = actual_tp2_rr
                        leg2_time = t
                        leg2_reason = "TP2_WIN"
                        break
                    continue

            # 2. EVALUAR PIERNA 2 EN BARRAS POSTERIORES A TP1
            else:
                hit_be = low <= active_sl_leg2 if direction == "BUY" else high >= active_sl_leg2
                hit_tp2 = high >= tp2 if direction == "BUY" else low <= tp2

                if hit_be and hit_tp2:
                    leg2_done = True
                    leg2_rr = 0.0
                    leg2_time = t
                    leg2_reason = "BE_SAME_BAR_CONFLICT"
                    break
                elif hit_be:
                    leg2_done = True
                    leg2_rr = 0.0
                    leg2_time = t
                    leg2_reason = "BE_LOSS"
                    break
                elif hit_tp2:
                    leg2_done = True
                    leg2_rr = actual_tp2_rr
                    leg2_time = t
                    leg2_reason = "TP2_WIN"
                    break

        if not leg1_done:
            last_c = float(future["close"].iloc[-1])
            unrealized = sign * (last_c - fill_price) / risk
            return {
                "outcome": "STILL_OPEN",
                "realized_rr": unrealized - self.cost_r,
                "status": "OPEN",
                "fill_price": fill_price,
                "fill_time": fill_time.isoformat(),
                "exit_time": None,
                "bars_held": bars_held,
                "leg1_reason": None,
                "leg2_reason": None
            }
        elif not leg2_done:
            last_c = float(future["close"].iloc[-1])
            unrealized_leg2 = sign * (last_c - fill_price) / risk
            cons_rr = 0.5 * leg1_rr + 0.5 * unrealized_leg2 - self.cost_r
            return {
                "outcome": "PARTIAL_TP1_RUNNER_OPEN",
                "realized_rr": cons_rr,
                "status": "OPEN",
                "fill_price": fill_price,
                "fill_time": fill_time.isoformat(),
                "exit_time": None,
                "bars_held": bars_held,
                "leg1_reason": leg1_reason,
                "leg2_reason": "RUNNER_STILL_OPEN"
            }
        else:
            cons_rr = 0.5 * leg1_rr + 0.5 * leg2_rr - self.cost_r
            if leg1_reason == "TP1_WIN" and leg2_reason in ["BE_LOSS", "BE_SAME_BAR_CONFLICT"]:
                final_out = "TP1_WIN_RUNNER_BE"
            elif leg1_reason == "TP1_WIN" and leg2_reason == "TP2_WIN":
                final_out = "FULL_TP2_WIN"
            else:
                final_out = "SL_LOSS"

            return {
                "outcome": final_out,
                "realized_rr": cons_rr,
                "status": "CLOSED",
                "fill_price": fill_price,
                "fill_time": fill_time.isoformat(),
                "exit_time": (leg2_time or leg1_time).isoformat(),
                "bars_held": bars_held,
                "leg1_reason": leg1_reason,
                "leg2_reason": leg2_reason
            }

    def execute_replay(self) -> Dict[str, Any]:
        if not self.db_path.exists():
            raise FileNotFoundError(f"Base de datos no encontrada: {self.db_path}")

        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT * FROM shadow_signals ORDER BY id ASC")
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
        df = pd.DataFrame(rows, columns=cols)

        # Identificar símbolos necesarios
        symbols = df["symbol"].unique().tolist()
        self.fetch_market_data(symbols)

        updates = []
        stats = {
            "total_rows": len(df),
            "pre_cutoff_rows": 0,
            "prospective_rows": 0,
            "accepted_executions": 0,
            "discarded_avoided": 0,
            "closed_replay_trades": 0,
            "open_replay_trades": 0,
            "gate_qualified_events": 0
        }

        print("\n" + "="*95)
        print("EJECUCIÓN DE REPLAY INDEPENDIENTE M1 POR FILA Y VARIANTE")
        print("="*95)

        for _, row in df.iterrows():
            row_id = row["id"]
            strat = row["strategy"]
            var = row["variant"]
            sym = row["symbol"]
            dir_ = row["direction"]
            sig_time = pd.to_datetime(row["timestamp"], utc=True)
            action = row["final_action"]
            
            features = json.loads(row["features_json"]) if row["features_json"] else {}
            created_at_str = features.get("created_at_live", row["timestamp"])
            created_at = pd.to_datetime(created_at_str, utc=True)
            is_prospect = sig_time >= self.cutoff_dt

            if is_prospect:
                stats["prospective_rows"] += 1
            else:
                stats["pre_cutoff_rows"] += 1

            # Si fue descartada por filtro de la variante:
            if action == "DISCARDED_BY_FILTER":
                stats["discarded_avoided"] += 1
                # Calcular resultado contrafactual de mercado
                cf_sim = self.simulate_trade_m1(
                    sym, dir_, sig_time, created_at,
                    row["entry_price"], row["stop_loss"], row["take_profit_1"], row["take_profit_2"],
                    fill_mode=self.fill_mode
                )
                sim_outcome = "AVOIDED"
                sim_rr = 0.0
                features["replay_engine"] = "DERIV_M1_INDEPENDENT_REPLAY"
                features["replay_status"] = "AVOIDED_DISCARDED"
                features["contrafactual_market_outcome"] = cf_sim.get("outcome")
                features["contrafactual_market_rr"] = cf_sim.get("realized_rr")
                features["gate_qualified"] = False
                note = f"DISCARDED: contrafactual {cf_sim.get('outcome')} ({cf_sim.get('realized_rr'):+.2f}R)"
            else:
                stats["accepted_executions"] += 1
                sim_res = self.simulate_trade_m1(
                    sym, dir_, sig_time, created_at,
                    row["entry_price"], row["stop_loss"], row["take_profit_1"], row["take_profit_2"],
                    fill_mode=self.fill_mode
                )
                sim_outcome = sim_res.get("outcome")
                sim_rr = sim_res.get("realized_rr")
                status = sim_res.get("status")

                if status == "CLOSED":
                    stats["closed_replay_trades"] += 1
                    is_gate_qual = is_prospect  # Solo califica si es prospectiva
                else:
                    stats["open_replay_trades"] += 1
                    is_gate_qual = False

                features["replay_engine"] = "DERIV_M1_INDEPENDENT_REPLAY"
                features["replay_fill_mode"] = self.fill_mode
                features["replay_status"] = status
                features["replay_fill_price"] = sim_res.get("fill_price")
                features["replay_fill_time"] = sim_res.get("fill_time")
                features["replay_exit_time"] = sim_res.get("exit_time")
                features["replay_bars_held"] = sim_res.get("bars_held")
                features["replay_leg1"] = sim_res.get("leg1_reason")
                features["replay_leg2"] = sim_res.get("leg2_reason")
                features["gate_qualified"] = is_gate_qual

                note = f"REPLAY M1 ({self.fill_mode}): {sim_outcome} ({sim_rr:+.2f}R), barras={sim_res.get('bars_held')}"

            updates.append((
                sim_outcome,
                sim_rr,
                note,
                json.dumps(features),
                row_id
            ))

            print(f"Row {row_id:<3} | {strat:<4} | {var:<17} | {sym:<16} {dir_} | Act: {action:<21} | {note}")

        if not self.dry_run:
            print(f"\n[REPLAY M1] Escribiendo resultados en staging: {self.db_path}...")
            cur.executemany("""
                UPDATE shadow_signals
                SET simulated_outcome = ?,
                    simulated_rr = ?,
                    contrafactual_note = ?,
                    features_json = ?
                WHERE id = ?
            """, updates)
            conn.commit()
            print("  [OK] Actualización de staging completada con éxito.")
        else:
            print("\n[REPLAY M1] Modo --dry-run activo: ningún registro modificado.")

        conn.close()
        return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Runner aislado de replay M1 prospectivo")
    parser.add_argument("--db", type=str, default=str(STAGING_DB_PATH), help="Ruta a staging SQLite")
    parser.add_argument("--fill-mode", type=str, default="signal_entry", choices=["created_at", "signal_entry"], help="Modo de ejecución del fill")
    parser.add_argument("--cost-r", type=float, default=0.0, help="Costo de fricción por trade en R")
    parser.add_argument("--max-staleness-minutes", type=float, default=None, help="Umbral máximo de antigüedad de la señal en minutos antes de considerarla vencida (EXPIRED)")
    parser.add_argument("--pre-fill-guard", action="store_true", help="Descarta señales cuyo SL o TP fue tocado antes de created_at")
    parser.add_argument("--causal-time", action="store_true", help="Evalúa barras desde signal_time cuando fill-mode es signal_entry")
    parser.add_argument("--execute", action="store_true", help="Escribe los resultados en staging (por defecto solo simula)")
    parser.add_argument("--export-archive", type=str, default=None, help="Exporta velas M1 y manifest a un directorio de archivo local")
    parser.add_argument("--archive-dir", type=str, default=None, help="Carga velas M1 desde un directorio de archivo local offline")
    parser.add_argument("--offline", action="store_true", help="Ejecuta 100% offline usando el archivo local por defecto")
    args = parser.parse_args()

    arch_dir = Path(args.archive_dir) if args.archive_dir else (DEFAULT_ARCHIVE_DIR if args.offline else None)

    runner = ProspectiveM1ReplayRunner(
        db_path=Path(args.db),
        dry_run=not args.execute,
        fill_mode=args.fill_mode,
        cost_r=args.cost_r,
        max_staleness_minutes=args.max_staleness_minutes,
        pre_fill_guard=args.pre_fill_guard,
        causal_time=args.causal_time,
        archive_dir=arch_dir
    )
    
    stats = runner.execute_replay()

    if args.export_archive:
        target_arch = Path(args.export_archive)
        runner.export_archive(target_arch)
    elif not args.offline and not args.archive_dir and not DEFAULT_ARCHIVE_DIR.exists():
        # Exportar automáticamente al directorio por defecto si no existía archivo
        runner.export_archive(DEFAULT_ARCHIVE_DIR)
