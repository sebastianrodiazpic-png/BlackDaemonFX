import json
import csv
from pathlib import Path
from collections import defaultdict

def normalize_sym(s: str) -> str:
    s = s.strip()
    s = s.replace(" (ORB)", "").replace(" (Oro ORB)", "").replace(" (Plata ORB)", "")
    s = s.replace(" (Plata Cuartos)", "").replace(" (Oro Cuartos)", "")
    s = s.replace(" (Plata ICT)", "").replace(" (Oro ICT)", "").replace(" (ICT)", "").replace(" (ICT Forex)", "")
    s = s.replace(" (Petróleo WTI)", "").replace(" (Plata M15)", "")
    # Replace internal underscores if it matches known symbols
    mapping = {
        "Boom_1000_Index": "Boom 1000 Index",
        "Crash_1000_Index": "Crash 1000 Index",
        "Jump_50_Index": "Jump 50 Index",
        "Step_Index": "Step Index",
        "US_Oil": "US Oil",
        "US_SP_500": "US SP 500",
        "US_Tech_100": "US Tech 100",
        "Volatility_100_Index": "Volatility 100 Index",
        "Volatility_75_Index": "Volatility 75 Index",
        "Wall_Street_30": "Wall Street 30",
    }
    return mapping.get(s, s)

def run():
    print("=====================================================================")
    print("GENERANDO MATRIZ COMPARATIVA MULTI-ESTRATEGIA POR INSTRUMENTO")
    print("=====================================================================")
    
    asset_strat_matrix = defaultdict(dict)
    
    # -------------------------------------------------------------
    # 1. ORB NEW YORK
    # -------------------------------------------------------------
    orb_file = Path("storage/analysis/replay_orb_nunez_results.json")
    if orb_file.exists():
        with open(orb_file, "r", encoding="utf-8") as f:
            orb_data = json.load(f)
        for sym, res in orb_data.get("by_symbol", {}).items():
            clean = normalize_sym(sym)
            trades = res.get("trades", 0)
            wr = res.get("win_rate", 0)
            pnl = res.get("profit_net", 0)
            r_mult = res.get("r_multiple", 0)
            status = "Rentable" if pnl > 0 else "Podado"
            asset_strat_matrix[clean]["ORB"] = {
                "strategy_name": "ORB New York",
                "trades": trades,
                "win_rate": wr,
                "pnl_usd": round(pnl, 2),
                "r_mult": round(r_mult, 1),
                "status": status,
                "tp1_rate": round(res.get("tp1_only", 0) / trades * 100, 1) if trades else 0,
                "tp2_rate": round(res.get("full_wins", 0) / trades * 100, 1) if trades else 0,
                "notes": f"Opening Range M5 (Midpoint 50%) · Return: {res.get('return_pct', 0)}%"
            }

    # -------------------------------------------------------------
    # 2. MALAYSIAN SNR (2 Años - 60 Activos)
    # -------------------------------------------------------------
    msnr_file = Path("storage/analysis/replay_malaysian_snr_2y_summary.csv")
    if msnr_file.exists():
        with open(msnr_file, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                clean = normalize_sym(r.get("symbol", ""))
                if not clean: continue
                trades = int(r.get("trades", 0) or 0)
                wr = float(r.get("win_rate", 0) or 0)
                pnl = float(r.get("net_pnl_usd", 0) or 0)
                total_r = float(r.get("total_r", 0) or 0)
                status = "Rentable" if pnl > 0 and wr >= 35.0 else "Podado"
                tp1_hits = int(r.get("wins", 0) or 0) + int(r.get("tp1_only_be", 0) or 0)
                tp2_hits = int(r.get("tp2_hits", 0) or 0)
                asset_strat_matrix[clean]["MALAYSIAN_SNR"] = {
                    "strategy_name": "Malaysian SNR (H1 Break / M15 Retest)",
                    "trades": trades,
                    "win_rate": wr,
                    "pnl_usd": round(pnl, 2),
                    "r_mult": round(total_r, 1),
                    "status": status,
                    "tp1_rate": round(tp1_hits / trades * 100, 1) if trades else 0,
                    "tp2_rate": round(tp2_hits / trades * 100, 1) if trades else 0,
                    "notes": f"Fresh Levels & Fractal Retests · PnL: ${round(pnl, 2):,}"
                }

    # -------------------------------------------------------------
    # 3. ICT SABRI MALLE (2 Años - 19 Activos)
    # -------------------------------------------------------------
    ict_file = Path("storage/meta_labeling_ict_sabri_malle_trades.csv")
    if ict_file.exists():
        ict_trades = defaultdict(lambda: {"trades": 0, "wins": 0, "tp1": 0, "tp2": 0, "r_sum": 0.0, "pnl": 0.0})
        with open(ict_file, "r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                clean = normalize_sym(row.get("symbol", ""))
                if not clean: continue
                r_net = float(row.get("r_net_rr4", 0) or 0)
                pnl_u = float(row.get("pnl_usd_rr4", 0) or 0)
                is_tp1 = row.get("outcome_tp1", "") == "TP1"
                is_tp2 = row.get("outcome_tp2_rr4", "") == "TP2"
                is_win = r_net > 0
                
                ict_trades[clean]["trades"] += 1
                if is_win: ict_trades[clean]["wins"] += 1
                if is_tp1: ict_trades[clean]["tp1"] += 1
                if is_tp2: ict_trades[clean]["tp2"] += 1
                ict_trades[clean]["r_sum"] += r_net
                ict_trades[clean]["pnl"] += pnl_u
                
        for clean, d in ict_trades.items():
            trades = d["trades"]
            wr = round(d["wins"] / trades * 100, 1) if trades else 0
            pnl = d["pnl"]
            r_sum = d["r_sum"]
            status = "Rentable" if r_sum > 0 else "Podado"
            asset_strat_matrix[clean]["ICT"] = {
                "strategy_name": "ICT Sabri Malle (AMD & FVG)",
                "trades": trades,
                "win_rate": wr,
                "pnl_usd": round(pnl, 2),
                "r_mult": round(r_sum, 1),
                "status": status,
                "tp1_rate": round(d["tp1"] / trades * 100, 1) if trades else 0,
                "tp2_rate": round(d["tp2"] / trades * 100, 1) if trades else 0,
                "notes": f"AMD + Judas Swing + FVG (1:2.0 / 1:4.0 RR) · Net: {round(r_sum, 1)}R"
            }

    # -------------------------------------------------------------
    # 4. GOLD QUARTERS (XAUUSD & XAGUSD)
    # -------------------------------------------------------------
    asset_strat_matrix["XAUUSD"]["GOLD_QUARTERS"] = {
        "strategy_name": "Gold Quarters (Niveles Psicológicos 25/50)",
        "trades": 656,
        "win_rate": 41.3,
        "pnl_usd": 252.76,
        "r_mult": 2.5,
        "status": "Rentable",
        "tp1_rate": 41.3,
        "tp2_rate": 19.9,
        "notes": "Cuartos psicológicos 000/250/500/750 con tolerancia adaptativa ATR M5"
    }
    asset_strat_matrix["XAGUSD"]["GOLD_QUARTERS"] = {
        "strategy_name": "Gold Quarters (Niveles Psicológicos 25/50)",
        "trades": 170,
        "win_rate": 41.8,
        "pnl_usd": 986.12,
        "r_mult": 9.9,
        "status": "Rentable",
        "tp1_rate": 41.8,
        "tp2_rate": 20.0,
        "notes": "Cuartos psicológicos aplicados a Plata M5"
    }

    # -------------------------------------------------------------
    # DETERMINACIÓN DE LA ESTRATEGIA GANADORA POR ACTIVO
    # -------------------------------------------------------------
    classification = {
        "METALES": ["XAUUSD", "XAGUSD"],
        "CRIPTO": ["BTCUSD", "ETHUSD"],
        "INDICES": ["US Tech 100", "US SP 500", "Wall Street 30"],
        "FOREX_CORE": ["EURUSD", "GBPUSD", "USDJPY", "USDCAD", "USDCHF", "AUDUSD"],
        "COMMODITIES": ["US Oil", "UK Brent Oil"],
        "SINTETICOS_STEP": ["Step Index", "Step Index 200", "Step Index 500", "Step Index 300", "Step Index 400"],
        "SINTETICOS_JUMP": ["Jump 10 Index", "Jump 25 Index", "Jump 50 Index", "Jump 75 Index", "Jump 100 Index"],
        "SINTETICOS_VOL": ["Volatility 10 Index", "Volatility 25 Index", "Volatility 50 Index", "Volatility 75 Index", "Volatility 100 Index", "Volatility 250 (1s) Index"],
        "SINTETICOS_CRASH_BOOM": ["Boom 1000 Index", "Boom 500 Index", "Boom 600 Index", "Boom 300 Index", "Boom 900 Index", "Crash 1000 Index", "Crash 500 Index", "Crash 600 Index", "Crash 300 Index", "Crash 900 Index"]
    }
    
    comparative_results = []
    
    for sym, strats in asset_strat_matrix.items():
        # Evaluar cuál es la mejor estrategia para este símbolo
        # Criterio institucional:
        # 1. Estrategias Rentables tienen prioridad absoluta sobre Podadas.
        # 2. Si hay varias rentables, se prioriza por Expectativa Matemática (R-Multiple y Win Rate).
        # 3. Considerar la microestructura del activo (ej: XAGUSD en ICT genera +38.1R vs -106k en Malaysian M15).
        
        strat_ranks = []
        for s_code, s_info in strats.items():
            score = 0
            if s_info["status"] == "Rentable":
                score += 1000
                score += s_info["win_rate"] * 5
                score += min(s_info["r_mult"] * 2, 500)
            else:
                score -= 1000
                score += s_info["win_rate"]
                score += s_info["r_mult"]
            strat_ranks.append((score, s_code, s_info))
            
        strat_ranks.sort(key=lambda x: x[0], reverse=True)
        best_tuple = strat_ranks[0]
        best_code = best_tuple[1]
        best_info = best_tuple[2]
        
        # Categoría
        cat = "OTROS"
        for c_name, c_list in classification.items():
            if sym in c_list:
                cat = c_name
                break
                
        comparative_results.append({
            "symbol": sym,
            "category": cat,
            "best_strategy_code": best_code,
            "best_strategy_name": best_info["strategy_name"],
            "status": best_info["status"],
            "win_rate": best_info["win_rate"],
            "trades": best_info["trades"],
            "r_mult": best_info["r_mult"],
            "pnl_usd": best_info["pnl_usd"],
            "all_strategies": strats
        })

    # Guardar matriz final
    with open("storage/analysis/asset_strategy_matrix_full.json", "w", encoding="utf-8") as f:
        json.dump(comparative_results, f, indent=2, ensure_ascii=False)

    print(f"Total activos procesados: {len(comparative_results)}")
    
    # Imprimir resumen de los activos más relevantes
    print("\n" + "="*105)
    print(f"{'INSTRUMENTO':<24} | {'CATEGORÍA':<15} | {'MEJOR ESTRATEGIA':<28} | {'WR%':<6} | {'R-MULT':<8} | {'ESTADO'}")
    print("="*105)
    
    # Ordenar por categoría y luego por rentabilidad
    for item in sorted(comparative_results, key=lambda x: (x["category"], -x["win_rate"])):
        print(f"{item['symbol']:<24} | {item['category']:<15} | {item['best_strategy_name']:<28} | {item['win_rate']:>5.1f}% | {item['r_mult']:>6.1f}R | {item['status']}")

if __name__ == "__main__":
    run()
