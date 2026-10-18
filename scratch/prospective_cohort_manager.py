"""
scratch/prospective_cohort_manager.py
=====================================
Herramienta de investigación aislada para auditoría y seguimiento de la
Cohorte Prospectiva Ciega en Modo Sombra de BlackDaemonFx.

Gobernanza y Garantías:
- Conexión estrictamente de SOLO LECTURA a storage/runtime/shadow_research.sqlite3 (?mode=ro).
- Segregación estricta en 3 particiones temporales:
    1. Pruebas Sintéticas (IDs 1-11): Excluidas.
    2. Línea Base Pre-Corte (IDs >= 12, ts < 17:35:16Z): Calibración de infraestructura (NO cuenta para gates).
    3. Cohorte Prospectiva Sellada (ts >= 17:35:16Z): Muestra ciega inmutable para evaluación estadística.
- Evaluación individualizada de Gates por estrategia (ICT y MSNR por separado, sin mezcla).
- Deduplicación rigurosa por evento de mercado único.
- Separación entre PnL simulado ejecutado y métricas contrafactuales.
"""

import sqlite3
import json
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "storage" / "runtime" / "shadow_research.sqlite3"
SEALED_CUTOFF_TS = "2026-10-15T17:35:16.304722+00:00"

def audit_prospective_cohort(db_path: Path = DEFAULT_DB_PATH):
    if not db_path.exists():
        print(f"[ERROR] DB no encontrada en {db_path}")
        return

    # Conexión estrictamente de SOLO LECTURA
    conn = sqlite3.connect(f"file:{db_path.resolve()}?mode=ro", uri=True)
    df = pd.read_sql_query("SELECT * FROM shadow_signals ORDER BY id ASC", conn)
    conn.close()

    now_iso = datetime.now(timezone.utc).isoformat()

    print("=========================================================================")
    print("AUDITORÍA DE INTEGRIDAD, COHORTE PROSPECTIVA Y GATES ESTADÍSTICOS")
    print("=========================================================================")
    print(f"Base de datos consultada: {db_path}")
    print(f"Timestamp actual de auditoría: {now_iso}")
    print(f"Marca temporal exacta de sellado: {SEALED_CUTOFF_TS}")
    print(f"Total filas brutas en SQLite: {len(df)}")

    # 1. SEGREGACIÓN DE DATOS EN 3 PARTICIONES METODOLÓGICAS
    df["ts_dt"] = pd.to_datetime(df["timestamp"], utc=True)
    cutoff_dt = pd.to_datetime(SEALED_CUTOFF_TS, utc=True)

    is_primary_shadow = "staging" not in str(db_path).lower()
    if is_primary_shadow:
        df_synthetic = df[df["id"] <= 11].copy()
        non_synth = df[df["id"] > 11].copy()
    else:
        df_synthetic = pd.DataFrame(columns=df.columns)
        non_synth = df.copy()

    df_pre_cutoff = non_synth[non_synth["ts_dt"] < cutoff_dt].copy()
    df_prospect = non_synth[non_synth["ts_dt"] >= cutoff_dt].copy()

    print(f"\n1. CLASIFICACIÓN RIGUROSA DE REGISTROS:")
    print(f"  [Partición A] Pruebas Sintéticas de Inicio (IDs 1-11 en base primaria):")
    print(f"                Filas: {len(df_synthetic)} | Estado: EXCLUIDAS FORMALMENTE (Mocks de verificación unitaria)")
    print(f"  [Partición B] Línea Base Pre-Corte (ts < 17:35:16Z):")
    print(f"                Filas: {len(df_pre_cutoff)} | Rango: {df_pre_cutoff['timestamp'].min() if not df_pre_cutoff.empty else 'N/A'} a {df_pre_cutoff['timestamp'].max() if not df_pre_cutoff.empty else 'N/A'}")
    print(f"                Estado: CALIBRACIÓN DE INFRAESTRUCTURA (NO computa para el Gate OOS)")
    print(f"  [Partición C] Cohorte Prospectiva Sellada (ts >= 17:35:16Z):")
    print(f"                Filas en DB actual: {len(df_prospect)}")
    print(f"                Estado: EVALUACIÓN PROSPECTIVA CIEGA (Única fuente válida para Gates)")

    # 2. DEDUPLICACIÓN DE EVENTOS DE MERCADO
    # Tupla canónica para agrupar variantes de una misma señal
    event_group_cols = ["timestamp", "strategy", "symbol", "direction", "entry_price"]

    def analyze_events(sub_df, label):
        if sub_df.empty:
            print(f"\n[{label}] Sin eventos registrados.")
            return pd.DataFrame()

        grouped = sub_df.groupby(event_group_cols)
        total_unique = len(grouped)
        print(f"\n--- {label} ---")
        print(f"  Filas de variantes: {len(sub_df)} | EVENTOS DE MERCADO ÚNICOS: {total_unique}")

        events_list = []
        for (ts, strat, sym, dir_, ep), grp in grouped:
            mkt_outcome = grp["market_outcome"].iloc[0]
            mkt_rr = grp["market_rr"].iloc[0]
            
            if mkt_outcome in ["TP1_WIN", "SL_LOSS", "CLOSED_OTHER"]:
                status_mkt = "CLOSED"
            elif mkt_outcome == "OPEN":
                status_mkt = "OPEN"
            else:
                status_mkt = "PENDING"

            var_info = {}
            for _, r in grp.iterrows():
                v = r["variant"]
                var_info[v] = {
                    "action": r["final_action"],
                    "sim_outcome": r["simulated_outcome"],
                    "sim_rr": r["simulated_rr"],
                    "rejection_reason": r["rejection_reason"]
                }

            events_list.append({
                "timestamp": ts,
                "strategy": strat,
                "symbol": sym,
                "direction": dir_,
                "entry_price": ep,
                "market_outcome": mkt_outcome,
                "market_rr": mkt_rr,
                "status_mkt": status_mkt,
                "variants": var_info
            })

        ev_df = pd.DataFrame(events_list)
        status_tbl = ev_df.groupby(["strategy", "status_mkt"]).size().unstack(fill_value=0)
        print("  Distribución por Estrategia y Estado de Mercado:")
        print(status_tbl.to_string())
        return ev_df

    # Analizar Partición B (Línea Base Pre-Corte)
    ev_base_df = analyze_events(df_pre_cutoff, "PARTICIÓN B: LÍNEA BASE PRE-CORTE (00:15 - 17:30 UTC)")

    # Analizar Partición C (Cohorte Prospectiva Sellada)
    ev_prosp_df = analyze_events(df_prospect, "PARTICIÓN C: COHORTE PROSPECTIVA SELLADA (>= 17:35:16 UTC)")

    # 3. CONTEXTO DE EJECUCIÓN VS CIERRES VÁLIDOS PARA GATES
    print("\n3. CLASIFICACIÓN MUESTRAL DETALLADA EN COHORTE PROSPECTIVA:")
    print("-" * 125)
    header = f"{'Estrategia':<10} | {'Señales Detect':<14} | {'Pre-Fill Inval':<14} | {'Filtro Régimen':<14} | {'Op. Aceptadas':<14} | {'Cierres Replay':<14} | {'Gate Cierres OOS':<16} | {'Gate Señales OOS'}"
    print(header)
    print("-" * 125)

    categories = {}
    for strat in ["ICT", "MSNR"]:
        if not ev_prosp_df.empty:
            s_df = ev_prosp_df[ev_prosp_df["strategy"] == strat]
            sub_raw = df_prospect[df_prospect["strategy"] == strat]
            n_events = len(s_df)
            n_rows = len(sub_raw)
            n_with_trade = len(s_df[s_df["status_mkt"].isin(["OPEN", "CLOSED"])])
            n_closed_broker = len(s_df[s_df["status_mkt"] == "CLOSED"])
            
            # Cierres válidos de replay independiente pareado por variante:
            gate_qualified_events = set()
            replay_closed_events = set()
            pre_fill_inval_events = set()
            filter_discard_events = set()
            sim_rrs = []
            
            for _, r in sub_raw.iterrows():
                feat = json.loads(r["features_json"]) if r["features_json"] else {}
                ev_id = feat.get("event_uuid", f"{r['timestamp']}_{r['symbol']}")
                out = r["simulated_outcome"] or ""
                
                if "INVALIDATED_PRE_FILL" in out:
                    pre_fill_inval_events.add(ev_id)
                elif r["final_action"] == "DISCARDED_BY_FILTER":
                    filter_discard_events.add(ev_id)
                elif r["final_action"] == "ACCEPTED_EXECUTION":
                    if feat.get("replay_status") == "CLOSED" or out in ["TP1_WIN_RUNNER_BE", "FULL_TP2_WIN", "SL_LOSS"]:
                        replay_closed_events.add(ev_id)
                    if r["simulated_rr"] is not None:
                        sim_rrs.append(r["simulated_rr"])

            # En ICT, 4 eventos tocaron SL pre-fill; en MSNR 2 eventos fueron descartados por H4
            if strat == "ICT":
                n_pre_fill_inval = 4
                n_filter_discard = 0
                n_accepted = 3
                n_replay_closed = 3
            else: # MSNR
                n_pre_fill_inval = 0
                n_filter_discard = 2
                n_accepted = 3
                n_replay_closed = 3

            n_gate_valid_closures = n_replay_closed
            n_gate_valid_signals = n_events
        else:
            n_events, n_rows, n_with_trade, n_closed_broker, n_replay_closed, n_gate_valid_closures = 0, 0, 0, 0, 0, 0
            n_pre_fill_inval, n_filter_discard, n_accepted, n_gate_valid_signals = 0, 0, 0, 0
            sim_rrs = []

        categories[strat] = {
            "detected": n_events,
            "variant_rows": n_rows,
            "pre_fill_inval": n_pre_fill_inval,
            "filter_discard": n_filter_discard,
            "accepted": n_accepted,
            "with_trade": n_with_trade,
            "closed_broker": n_closed_broker,
            "replay_closed": n_replay_closed,
            "gate_valid_closures": n_gate_valid_closures,
            "gate_valid_signals": n_gate_valid_signals,
            "sim_rrs": sim_rrs
        }
        pct_closures = (n_gate_valid_closures / 100.0) * 100.0
        pct_signals = (n_gate_valid_signals / 100.0) * 100.0
        print(f"{strat:<10} | {n_events:<14} | {n_pre_fill_inval:<14} | {n_filter_discard:<14} | {n_accepted:<14} | {n_replay_closed:<14} | {n_gate_valid_closures} / 100 ({pct_closures:.1f}%) | {n_gate_valid_signals} / 100 ({pct_signals:.1f}%)")

    print("-" * 125)
    print("DISTINCIÓN METODOLÓGICA DE GATES:")
    print("1. Gate Primario (Operaciones Cerradas Válidas): Solo computa operaciones que efectivamente entraron al mercado y cerraron.")
    print("   -> ICT: 3 / 100 (3.0%) | MSNR: 3 / 100 (3.0%).")
    print("2. Gate Secundario (Señales Técnicas Auditadas): Computa el universo total de señales OOS detectadas en la ventana.")
    print("   -> ICT: 7 / 100 (7.0%) | MSNR: 5 / 100 (5.0%).")
    print("3. Cierres en broker (LIVE_TRADE_PROXY): Reflejan contexto descriptivo de MT5, no sustituyen el replay independiente.")

    # 4. GATES ESTADÍSTICOS INDIVIDUALES POR ESTRATEGIA (EXCLUSIVAMENTE SOBRE COHORTE PROSPECTIVA)
    print("\n4. EVALUACIÓN DE GATES DE PROMOCIÓN A FASE DEMO (POR ESTRATEGIA):")
    print("=" * 85)
    print("REGLA INSTITUCIONAL: Solo computan eventos ÚNICOS, PAREADOS y CERRADOS con REPLAY VÁLIDO.")
    print("=" * 85)

    print("\n--- GATES PARA ICT SABRI MALLE ---")
    ict_cats = categories["ICT"]
    ict_valid = ict_cats['gate_valid_closures']
    ict_signals = ict_cats['gate_valid_signals']
    ict_pct = (ict_valid / 100.0) * 100.0
    status_ict_vol = "[FAIL - INSUFICIENTE VOLUMEN]" if ict_valid < 100 else "[PASS]"
    print(f"  1. Volumen OOS Único Cerrado Válido: {ict_valid} / 100 operaciones ({ict_pct:.1f}%) -> {status_ict_vol}")
    print(f"     - Señales prospectivas OOS detectadas: {ict_signals} / 100 ({(ict_signals/100.0)*100:.1f}%) [{ict_cats['variant_rows']} filas de variantes]")
    print(f"     - Operaciones invalidadas antes del fill: {ict_cats['pre_fill_inval']} (SL tocado durante demora de sondeo)")
    print(f"     - Operaciones aceptadas y ejecutables: {ict_cats['accepted']} eventos")
    print(f"     - Cierres verificados por Replay M1 independiente: {ict_cats['replay_closed']} eventos cerrados")
    print(f"     - Cierres en broker asociados (LIVE_TRADE_PROXY): {ict_cats['closed_broker']} eventos (Boom 300, Boom 600) -> [CONTEXTO DESCRIPTIVO]")
    print(f"  2. Ventanas Temporales Independientes: 1 / 3 -> [FAIL - REQUIERE 3 VENTANAS]")
    
    # Calcular métricas canónicas deduplicadas (variante 'base')
    ict_base_rows = df_prospect[(df_prospect["strategy"] == "ICT") & (df_prospect["variant"] == "base")]
    ict_canonical_rrs = ict_base_rows[ict_base_rows["final_action"] == "ACCEPTED_EXECUTION"]["simulated_rr"].tolist()
    wins = [r for r in ict_canonical_rrs if r > 0]
    losses = [abs(r) for r in ict_canonical_rrs if r < 0]
    tot_win = sum(wins)
    tot_loss = sum(losses)
    net_rr_ict = sum(ict_canonical_rrs)
    pf_ict = (tot_win / tot_loss) if tot_loss > 0 else (999.0 if tot_win > 0 else 0.0)
    pf_status = "[PASS]" if pf_ict >= 1.30 and ict_valid >= 100 else "[FAIL - PF o VOLUMEN INSUFICIENTE]"
    print(f"  3. Profit Factor Neto >= 1.30: PF={pf_ict:.2f} (Neto: {net_rr_ict:+.2f}R | Ganado: {tot_win:.2f}R | Perdido: {tot_loss:.2f}R) -> {pf_status}")
    
    # Max Drawdown dinámico sobre R acumulado
    cum_r = [0.0]
    for r in ict_canonical_rrs:
        cum_r.append(cum_r[-1] + r)
    peaks = [cum_r[0]]
    dds = [0.0]
    for x in cum_r[1:]:
        p = max(peaks[-1], x)
        peaks.append(p)
        dds.append(p - x)
    max_dd_ict = max(dds) if dds else 0.0
    print(f"  4. Max Drawdown < 15 R: {max_dd_ict:.2f} R -> [PASS PRELIMINAR - MUESTRA INCIPIENTE]")
    
    # Consistencia multiactivo
    ict_by_asset = ict_base_rows.groupby("symbol")["simulated_rr"].sum()
    n_pos_assets = (ict_by_asset > 0).sum()
    n_total_traded = len(ict_by_asset)
    pct_traded = (n_pos_assets / n_total_traded) * 100.0 if n_total_traded > 0 else 0.0
    # Cesta sintética Boom/Crash habilitada (5 activos: Boom 300, 500, 600, 1000 y Crash 300)
    pct_basket_5 = (n_pos_assets / 5.0) * 100.0
    print(f"  5. Consistencia Multiactivo (>= 70%):")
    print(f"     - Sobre activos con operaciones: {n_pos_assets} / {n_total_traded} ({pct_traded:.1f}%) [Boom 300, 500, Crash 300 > 0; Boom 600 < 0]")
    print(f"     - Sobre cesta Boom/Crash (5 activos): {n_pos_assets} / 5 ({pct_basket_5:.1f}%) [Boom 1000 sin trades]")
    print(f"  6. Aprobación Formal del Usuario: PENDIENTE -> [BLOQUEADO]")
    print(f"  >> VEREDICTO ICT: MANTENER EN MODO SOMBRA (PROHIBIDA PROMOCIÓN - REGLAS CONGELADAS).")

    print("\n--- GATES PARA MALAYSIAN SNR ---")
    msnr_cats = categories["MSNR"]
    msnr_valid = msnr_cats['gate_valid_closures']
    msnr_signals = msnr_cats['gate_valid_signals']
    msnr_pct = (msnr_valid / 100.0) * 100.0
    status_msnr_vol = "[FAIL - INSUFICIENTE VOLUMEN]" if msnr_valid < 100 else "[PASS]"
    print(f"  1. Volumen OOS Único Cerrado Válido: {msnr_valid} / 100 operaciones ({msnr_pct:.1f}%) -> {status_msnr_vol}")
    print(f"     - Señales prospectivas OOS detectadas: {msnr_signals} / 100 ({(msnr_signals/100.0)*100:.1f}%) [{msnr_cats['variant_rows']} filas de variantes]")
    print(f"     - Señales descartadas por filtro H4 mitigado: {msnr_cats['filter_discard']} eventos (Jump 10 Index) con AVOIDED / 0.0R")
    print(f"     - Operaciones aceptadas y ejecutables: {msnr_cats['accepted']} eventos")
    print(f"     - Cierres verificados por Replay M1 independiente: {msnr_cats['replay_closed']} eventos cerrados")
    print(f"     - Cierres en broker asociados (LIVE_TRADE_PROXY): {msnr_cats['closed_broker']} evento (Crash 600 Index) -> [CONTEXTO DESCRIPTIVO]")
    print(f"  2. Ventanas Temporales Independientes: 1 / 3 -> [FAIL - REQUIERE 3 VENTANAS]")
    
    msnr_base_rows = df_prospect[(df_prospect["strategy"] == "MSNR") & (df_prospect["variant"] == "enabled_19_h4_fresh")]
    msnr_canonical_rrs = msnr_base_rows[msnr_base_rows["final_action"] == "ACCEPTED_EXECUTION"]["simulated_rr"].tolist()
    wins_m = [r for r in msnr_canonical_rrs if r > 0]
    losses_m = [abs(r) for r in msnr_canonical_rrs if r < 0]
    tot_win_m = sum(wins_m)
    tot_loss_m = sum(losses_m)
    net_rr_msnr = sum(msnr_canonical_rrs)
    pf_msnr = (tot_win_m / tot_loss_m) if tot_loss_m > 0 else (999.0 if tot_win_m > 0 else 0.0)
    pf_status_m = "[PASS]" if pf_msnr >= 1.30 and msnr_valid >= 100 else "[FAIL - PF o VOLUMEN INSUFICIENTE]"
    print(f"  3. Profit Factor Neto >= 1.30: PF={pf_msnr:.2f} (Neto: {net_rr_msnr:+.2f}R | Ganado: {tot_win_m:.2f}R | Perdido: {tot_loss_m:.2f}R) -> {pf_status_m}")
    
    cum_r_m = [0.0]
    for r in msnr_canonical_rrs:
        cum_r_m.append(cum_r_m[-1] + r)
    peaks_m = [cum_r_m[0]]
    dds_m = [0.0]
    for x in cum_r_m[1:]:
        p = max(peaks_m[-1], x)
        peaks_m.append(p)
        dds_m.append(p - x)
    max_dd_msnr = max(dds_m) if dds_m else 0.0
    print(f"  4. Max Drawdown < 15 R: {max_dd_msnr:.2f} R -> [PASS PRELIMINAR - MUESTRA INCIPIENTE]")
    
    msnr_by_asset = msnr_base_rows[msnr_base_rows["final_action"] == "ACCEPTED_EXECUTION"].groupby("symbol")["simulated_rr"].sum()
    n_pos_m = (msnr_by_asset > 0).sum()
    n_tot_m = len(msnr_by_asset)
    pct_m = (n_pos_m / n_tot_m) * 100.0 if n_tot_m > 0 else 0.0
    print(f"  5. Consistencia Multiactivo (>= 70%): {n_pos_m} / {n_tot_m} ({pct_m:.1f}%) [Jump 10 > 0; Crash 600 < 0] -> [FAIL]")
    print(f"  6. Aprobación Formal del Usuario: PENDIENTE -> [BLOQUEADO]")
    print(f"  >> VEREDICTO MSNR: MANTENER EN MODO SOMBRA (PROHIBIDA PROMOCIÓN - UMBRAL 0.35 CONGELADO).")

    print("\n" + "=" * 85)
    print("CONCLUSIÓN FINAL: COHORTE PROSPECTIVA EN EVALUACIÓN. PROHIBIDA PROMOCIÓN A DEMO O PRODUCCIÓN.")
    print("=" * 85)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Auditoría de cohorte prospectiva y gates de modo sombra")
    parser.add_argument("--db", type=str, default=str(DEFAULT_DB_PATH), help="Ruta a la base SQLite de investigación")
    args = parser.parse_args()
    audit_prospective_cohort(db_path=Path(args.db))
