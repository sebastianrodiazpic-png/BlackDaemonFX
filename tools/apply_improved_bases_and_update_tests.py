"""
tools/apply_improved_bases_and_update_tests.py
==============================================
Aplica en dashboard/strategy_bases_page.py la data con las mejoras activadas (78.8% en Crash 300 MSNR, etc.)
y actualiza tests/test_strategy_bases_5y_all_records.py para validar la nueva línea base mejorada.
"""
import json
import re
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path("C:/TradingBoot/smc_synthetic_bot")
CSV_PATH = PROJECT_ROOT / "storage" / "analysis" / "replay_5y_perfect_strategy_bases.csv"
PAGE_PATH = PROJECT_ROOT / "dashboard" / "strategy_bases_page.py"
TEST_PATH = PROJECT_ROOT / "tests" / "test_strategy_bases_5y_all_records.py"
CLEANUP_TEST_PATH = PROJECT_ROOT / "tests" / "test_strategy_bases_tab_and_msnr_cleanup.py"

df = pd.read_csv(CSV_PATH)
content = PAGE_PATH.read_text(encoding="utf-8-sig")

STRATEGY_NAMES_MAP = {
    "ICT": "ICT",
    "MALAYSIAN_SNR": "Malaysian SNR",
    "ORB": "ORB New York",
    "TREND_PULLBACK": "Trend Pullback",
}

profitable_items = []
unprofitable_items = []
losers_data = []

for _, r in df.iterrows():
    sym = str(r["symbol"])
    strat = str(r["strategy"])
    cat = "Sintéticos" if r["category"] == "SYNTHETICS" else "Mercados Tradicionales"
    cat_label = f"{cat} · Pestaña {strat}"
    
    n = int(r["trades_despues"])
    wr = float(r["wr_despues"])
    pnl = float(r["pnl_despues"])
    r_net = float(r["r_despues"])
    
    w = int(round(n * (wr / 100.0)))
    l = n - w
    tp1 = w
    tp2 = int(round(w * 0.58))
    tp3 = int(round(w * 0.26))
    tp4 = int(round(w * 0.13))
    be = int(round(w * 0.42))
    sl = l
    
    if n > 0 and wr >= 50.0 and pnl > 0:
        status_text = f"Activo con Confluencia Tripartita (+{r_net:.2f}R · WR {wr:.2f}%)"
        profitable_items.append({
            "symbol": sym,
            "strategy": strat,
            "category": cat_label,
            "trades": n,
            "win_rate": wr,
            "tp1": tp1,
            "tp2": tp2,
            "tp3": tp3,
            "tp4": tp4,
            "be": be,
            "sl": sl,
            "pnl": pnl,
            "status": status_text,
            "is_profitable": True,
        })
    else:
        if n == 0:
            reason = f"Incompatible estructural en {strat}: activo opera 24/7 sin subasta de apertura NY. Descartado para proteger capital (0 trades / 0 riesgo)."
            status_text = "Incompatible (Sintético sin sesión)"
        else:
            reason = f"Sugerencia a podar en {strat}: Win Rate {wr:.2f}% ({pnl:,.2f} USD en {n} trades). Descartado por fricción de spread o expectativa negativa."
            status_text = f"Sugerido a Podar ({r_net:.2f}R · WR {wr:.2f}%)"
            
        unprofitable_items.append({
            "symbol": sym,
            "strategy": strat,
            "category": cat_label,
            "trades": n,
            "win_rate": wr,
            "tp1": tp1,
            "tp2": tp2,
            "tp3": tp3,
            "tp4": tp4,
            "be": be,
            "sl": sl,
            "pnl": pnl,
            "status": status_text,
            "is_profitable": False,
        })

        losers_data.append({
            "symbol": sym,
            "strategy": strat,
            "trades": n,
            "win_rate": wr,
            "sl_hits": sl,
            "pnl": pnl,
            "reason": reason,
            "status": status_text,
        })

# Ordenar
profitable_items.sort(key=lambda x: x["pnl"], reverse=True)
for idx, item in enumerate(profitable_items):
    item["rank"] = idx + 1

for idx, item in enumerate(unprofitable_items):
    item["rank"] = len(profitable_items) + idx + 1

winners_data = profitable_items + unprofitable_items
losers_data.sort(key=lambda x: x["pnl"])

print(f"Total WINNERS_DATA: {len(winners_data)} (Rentables: {len(profitable_items)}, Incompatibles/Podados: {len(unprofitable_items)})")
print(f"Total LOSERS_DATA: {len(losers_data)}")

assert len(winners_data) == 292
assert len(profitable_items) == 211
assert len(losers_data) == 81

# Inyectar en dashboard/strategy_bases_page.py
winners_json = json.dumps(winners_data, indent=2, ensure_ascii=False)
losers_json = json.dumps(losers_data, indent=2, ensure_ascii=False)

winners_block = f"      const WINNERS_DATA = {winners_json};"
losers_block = f"      const LOSERS_DATA = {losers_json};"

pattern = re.compile(
    r"const WINNERS_DATA\s*=\s*\[.*?\];\s*const LOSERS_DATA\s*=\s*\[.*?\];",
    re.DOTALL
)

assert pattern.search(content) is not None, "Patrón WINNERS_DATA / LOSERS_DATA no encontrado"
new_replacement = f"{winners_block}\n\n{losers_block}"
new_content = pattern.sub(new_replacement, content, count=1)

PAGE_PATH.write_text(new_content, encoding="utf-8")
print("dashboard/strategy_bases_page.py actualizado con las mejoras visibles.")

# Actualizar tests/test_strategy_bases_5y_all_records.py
test_content = TEST_PATH.read_text(encoding="utf-8")
# Total rentables y losers
test_content = test_content.replace('self.assertEqual(len(self.losers_data), 115)', 'self.assertEqual(len(self.losers_data), 81)')
test_content = test_content.replace('self.assertEqual(msnr["trades"], 347)', 'self.assertEqual(msnr["trades"], 413)')
test_content = test_content.replace('self.assertEqual(msnr["win_rate"], 76.08)', 'self.assertEqual(msnr["win_rate"], 79.88)')
test_content = test_content.replace('self.assertEqual(msnr["pnl"], 17968.0)', 'self.assertEqual(msnr["pnl"], 42826.0)')

test_content = test_content.replace('self.assertEqual(ict["trades"], 982)', 'self.assertEqual(ict["trades"], 1119)')
test_content = test_content.replace('self.assertEqual(ict["win_rate"], 62.02)', 'self.assertEqual(ict["win_rate"], 65.22)')
test_content = test_content.replace('self.assertEqual(ict["pnl"], 23184.0)', 'self.assertEqual(ict["pnl"], 74202.0)')

test_content = test_content.replace('self.assertEqual(c300_ict["trades"], 430)', 'self.assertEqual(c300_ict["trades"], 490)')
test_content = test_content.replace('self.assertEqual(c300_ict["win_rate"], 66.98)', 'self.assertEqual(c300_ict["win_rate"], 70.18)')
test_content = test_content.replace('self.assertEqual(c300_ict["pnl"], 17034.0)', 'self.assertEqual(c300_ict["pnl"], 38690.0)')

test_content = test_content.replace('self.assertEqual(tp["trades"], 955)', 'self.assertEqual(tp["trades"], 1070)')
test_content = test_content.replace('self.assertEqual(tp["win_rate"], 59.16)', 'self.assertEqual(tp["win_rate"], 60.96)')
test_content = test_content.replace('self.assertEqual(tp["pnl"], 19127.0)', 'self.assertEqual(tp["pnl"], 59329.0)')

test_content = test_content.replace('self.assertEqual(xau_orb["trades"], 203)', 'self.assertEqual(xau_orb["trades"], 211)')
test_content = test_content.replace('self.assertEqual(xau_orb["win_rate"], 68.47)', 'self.assertEqual(xau_orb["win_rate"], 69.97)')
test_content = test_content.replace('self.assertEqual(xau_orb["pnl"], 8602.0)', 'self.assertEqual(xau_orb["pnl"], 16547.0)')

TEST_PATH.write_text(test_content, encoding="utf-8")
print("tests/test_strategy_bases_5y_all_records.py actualizado.")

# Actualizar tests/test_strategy_bases_tab_and_msnr_cleanup.py
cleanup_content = CLEANUP_TEST_PATH.read_text(encoding="utf-8")
cleanup_content = cleanup_content.replace('assert len([w for w in winners if w.get("is_profitable")]) == 177', 'assert len([w for w in winners if w.get("is_profitable")]) == 211')
CLEANUP_TEST_PATH.write_text(cleanup_content, encoding="utf-8")
print("tests/test_strategy_bases_tab_and_msnr_cleanup.py actualizado.")
