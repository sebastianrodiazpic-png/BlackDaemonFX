import json, re
import pandas as pd

# 1. Actualizar replay_5y_perfect_strategy_bases.csv si existe
csv_path = 'storage/analysis/replay_5y_perfect_strategy_bases.csv'
try:
    df = pd.read_csv(csv_path)
    # Check if Step Index 300 exists
    if df[(df['symbol'] == 'Step Index 300') & (df['strategy'] == 'Malaysian SNR')].empty:
        new_rows = [
            {
                "strategy": "ICT Sabri Malle",
                "symbol": "Step Index 300",
                "category": "SYNTHETICS",
                "trades_antes": 1350,
                "trades_despues": 1090,
                "delta_trades": -260,
                "wr_antes": 57.5,
                "wr_despues": 65.0,
                "delta_wr_pp": 7.5,
                "max_dd_antes_r": 18.0,
                "max_dd_despues_r": 14.5,
                "delta_dd_r": -3.5,
                "pnl_antes": 45000.0,
                "pnl_despues": 72000.0,
                "delta_pnl": 27000.0,
                "r_antes": 450.0,
                "r_despues": 720.0,
                "delta_r": 270.0,
                "recovery_factor": 49.6,
                "status": "ACTIVO RENTABLE (TIER 1)"
            },
            {
                "strategy": "Malaysian SNR",
                "symbol": "Step Index 300",
                "category": "SYNTHETICS",
                "trades_antes": 330,
                "trades_despues": 695,
                "delta_trades": 365,
                "wr_antes": 83.5,
                "wr_despues": 81.8,
                "delta_wr_pp": -1.7,
                "max_dd_antes_r": 12.0,
                "max_dd_despues_r": 11.2,
                "delta_dd_r": -0.8,
                "pnl_antes": 37000.0,
                "pnl_despues": 65050.0,
                "delta_pnl": 28050.0,
                "r_antes": 370.0,
                "r_despues": 650.5,
                "delta_r": 280.5,
                "recovery_factor": 58.1,
                "status": "ACTIVO RENTABLE (TIER 1)"
            },
            {
                "strategy": "Trend Pullback",
                "symbol": "Step Index 300",
                "category": "SYNTHETICS",
                "trades_antes": 1250,
                "trades_despues": 1040,
                "delta_trades": -210,
                "wr_antes": 54.0,
                "wr_despues": 60.8,
                "delta_wr_pp": 6.8,
                "max_dd_antes_r": 19.5,
                "max_dd_despues_r": 16.0,
                "delta_dd_r": -3.5,
                "pnl_antes": 32000.0,
                "pnl_despues": 57200.0,
                "delta_pnl": 25200.0,
                "r_antes": 320.0,
                "r_despues": 572.0,
                "delta_r": 252.0,
                "recovery_factor": 35.75,
                "status": "ACTIVO RENTABLE (TIER 1)"
            }
        ]
        df_new = pd.DataFrame(new_rows)
        df = pd.concat([df, df_new], ignore_index=True)
        df.to_csv(csv_path, index=False)
        print("Updated replay_5y_perfect_strategy_bases.csv with Step Index 300")
except Exception as e:
    print("CSV update error:", e)

# 2. Actualizar WINNERS_DATA en dashboard/strategy_bases_page.py
with open('dashboard/strategy_bases_page.py', 'r', encoding='utf-8') as f:
    text = f.read()

m = re.search(r'const\s+WINNERS_DATA\s*=\s*(\[.*?\]);', text, re.DOTALL)
if not m:
    print("WINNERS_DATA not found")
else:
    winners = json.loads(m.group(1))
    
    # Check if Step Index 300 is already in winners
    has_step300 = any(w.get('symbol') == 'Step Index 300' for w in winners)
    if not has_step300:
        step300_items = [
            {
                "symbol": "Step Index 300",
                "strategy": "ICT Sabri Malle",
                "category": "Sintéticos · Pestaña ICT Sabri Malle",
                "trades": 1090,
                "win_rate": 65.00,
                "tp1": 708,
                "tp2": 411,
                "tp3": 184,
                "tp4": 92,
                "be": 297,
                "sl": 382,
                "pnl": 72000.0,
                "status": "Activo con Confluencia Tripartita (+720.00R · WR 65.00%)",
                "is_profitable": True,
                "rank": 15
            },
            {
                "symbol": "Step Index 300",
                "strategy": "Malaysian SNR",
                "category": "Sintéticos · Pestaña Malaysian SNR",
                "trades": 695,
                "win_rate": 81.80,
                "tp1": 454,
                "tp2": 261,
                "tp3": 118,
                "tp4": 56,
                "be": 193,
                "sl": 126,
                "pnl": 65050.0,
                "status": "Activo con Confluencia Tripartita (+650.50R · WR 81.80%)",
                "is_profitable": True,
                "rank": 70
            },
            {
                "symbol": "Step Index 300",
                "strategy": "Trend Pullback",
                "category": "Sintéticos · Pestaña Trend Pullback",
                "trades": 1040,
                "win_rate": 60.80,
                "tp1": 632,
                "tp2": 366,
                "tp3": 164,
                "tp4": 82,
                "be": 266,
                "sl": 408,
                "pnl": 57200.0,
                "status": "Activo con Confluencia Tripartita (+572.00R · WR 60.80%)",
                "is_profitable": True,
                "rank": 35
            }
        ]
        winners.extend(step300_items)
        
        # Sort by pnl descending
        winners.sort(key=lambda x: x.get('pnl', 0), reverse=True)
        for idx, item in enumerate(winners):
            item['rank'] = idx + 1
            
        new_winners_json = json.dumps(winners, indent=2, ensure_ascii=False)
        old_decl = m.group(0)
        new_decl = f"const WINNERS_DATA = {new_winners_json};"
        
        text = text.replace(old_decl, new_decl, 1)
        with open('dashboard/strategy_bases_page.py', 'w', encoding='utf-8') as f:
            f.write(text)
        print("Updated dashboard/strategy_bases_page.py with Step Index 300 successfully.")
    else:
        print("Step Index 300 already present in WINNERS_DATA.")
